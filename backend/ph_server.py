"""
Powerhouse FastAPI server.

Integration layer wires four architectural bridges into the endpoints:

1. SwarmFeedbackBridge  – captures execution outcomes and feeds them back
                          into the RL Q-network so parameters improve over time.
2. ApprovalGate         – enforces the HITL policy (gate | audit | disabled)
                          before any execution.  Configurable via HITL_MODE.
3. CausalAgentRouter    – optional pathway: caller supplies causal_context
                          (variable → confidence/domain hints) and the router
                          boosts the most-suited agents before dispatch.
4. SwarmOrchestrator    – /run/swarm runs stigmergic multi-agent execution and
                          feeds its outcome into the RL bridge automatically.
"""

import json
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.orchestrator import Orchestrator
from config.settings import get_settings

# --- Integration bridges ---
from core.learning.swarm_feedback_bridge import (
    SwarmFeedbackBridge,
    SwarmExecutionFeedback,
    swarm_result_to_feedback,
)
from core.human_in_the_loop import (
    build_approval_gate,
)
from core.reasoning.causal_agent_router import (
    CausalAgentRouter,
    CausalInterventionRecommendation,
)
from core.swarm.swarm_orchestrator import SwarmOrchestrator

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Powerhouse Multi-Agent Orchestrator API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load orchestrator configuration once at startup
with open("config/default.json", "r", encoding="utf-8") as f:
    _cfg = json.load(f)

_orchestrator = Orchestrator(
    _cfg["enabled_agents"],
    max_agents=_cfg.get("max_agents", settings.max_agents_per_workflow),
)

# --- Swarm ↔ RL bridge (singleton, shared across requests) ---
_swarm_bridge = SwarmFeedbackBridge()

# --- HITL approval gate (reads mode/timeout from settings) ---
_approval_gate = build_approval_gate(
    mode=settings.hitl_mode,
    timeout_seconds=settings.hitl_timeout_seconds,
    auto_approve_on_timeout=settings.hitl_auto_approve_on_timeout,
    trusted_agents=set(settings.hitl_trusted_agents),
)

# --- Causal agent router (no CausalReasoner at server level; callers supply
#     pre-computed causal_context; the router handles boost logic) ---
_causal_router = CausalAgentRouter(
    causal_reasoner=None,   # no live graph at server startup
    agent_selector=None,    # uses NeuralAgentSelector with default settings
)

# --- Swarm orchestrator (lazy agent registration on first /run/swarm call) ---
_swarm_orchestrator = SwarmOrchestrator(base_orchestrator=_orchestrator)
_swarm_agents_registered = False


def _ensure_swarm_agents() -> None:
    """Register orchestrator agents with the swarm orchestrator on first use."""
    global _swarm_agents_registered
    if _swarm_agents_registered:
        return
    for agent_name in _cfg["enabled_agents"]:
        agent_instance = _orchestrator._agents.get(agent_name)
        if agent_instance is not None:
            _swarm_orchestrator.register_agent(
                agent_id=agent_name,
                agent_instance=agent_instance,
                initial_location="default",
            )
    _swarm_agents_registered = True


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None
    task_type: Optional[str] = None
    parameters: Optional[Dict[str, float]] = None
    # Optional causal context: variable name → {confidence, domain, predicted_effect}
    # When provided, agent selection is boosted toward matching specialisations.
    causal_context: Optional[Dict[str, Dict[str, Any]]] = None


class RunResponse(BaseModel):
    task: str
    outputs: List[Dict[str, Any]]
    state: Dict[str, Any]
    run_id: str
    hitl_status: str = "not_checked"
    rl_adjustments: Optional[Dict[str, float]] = None
    selected_agent: Optional[str] = None


class SwarmRunRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None
    task_type: Optional[str] = None
    parameters: Optional[Dict[str, float]] = None
    max_iterations: int = 10
    use_stigmergy: bool = True


class SwarmRunResponse(BaseModel):
    task: str
    run_id: str
    iterations: int
    results: List[Dict[str, Any]]
    emergent_patterns: List[Dict[str, Any]]
    swarm_statistics: Dict[str, Any]
    hitl_status: str = "not_checked"
    rl_ingested: bool = False


class HITLDecisionRequest(BaseModel):
    approved: bool
    resolver: str = "human"
    rejection_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Shared pre-execution pipeline
# ---------------------------------------------------------------------------

def _pre_execute(
    task: str,
    run_id: str,
    task_type: Optional[str],
    context: Dict[str, Any],
    agent_name: str,
    causal_context: Optional[Dict[str, Any]] = None,
) -> tuple:
    """
    Shared pre-execution steps (RL hints + HITL gate).

    Returns:
        (rl_adjustments, hitl_status)

    Raises:
        HTTPException 403 if HITL gate rejects.
    """
    # RL parameter recommendations
    rl_adjustments = _swarm_bridge.get_recommended_adjustments(
        task=task,
        task_type=task_type,
    )
    if rl_adjustments:
        context.setdefault("rl_adjustments", rl_adjustments)

    # HITL gate
    approval_req = _approval_gate.create_request(
        task=task,
        reasoning_summary=(
            f"Task submitted. Agent: '{agent_name}'. "
            + (f"Causal hints: {list(causal_context.keys())}." if causal_context else "")
        ),
        agent_name=agent_name,
        agent_confidence=1.0,
        estimated_impact="medium",
        causal_context=causal_context,
        run_id=run_id,
    )
    approved = _approval_gate.request_approval(approval_req)

    if not approved:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "HITL gate rejected execution",
                "request_id": approval_req.request_id,
                "reason": approval_req.rejection_reason or "Human rejected",
            },
        )

    return rl_adjustments, approval_req.status.value


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "hitl_mode": settings.hitl_mode,
        "rl_ingestion_count": _swarm_bridge.get_statistics()["ingestion_count"],
    }


@app.post("/run", response_model=RunResponse)
async def run(payload: RunRequest) -> RunResponse:
    """
    Execute a task through the orchestration pipeline.

    Pipeline:
      1. RL parameter recommendations from the swarm bridge.
      2. HITL gate (gate | audit | disabled).
      3a. If ``causal_context`` is supplied → CausalAgentRouter selects the
          best agent and injects causal hints into context.
      3b. Otherwise → plain Orchestrator.run().
      4. Ingest outcome into RL bridge.

    ``causal_context`` format::

        {
          "temperature": {"confidence": 0.85, "domain": "parameter_tuning",
                          "predicted_effect": 0.6}
        }
    """
    run_id = str(uuid.uuid4())
    context = payload.context or {}
    context["run_id"] = run_id

    # Resolve the primary agent name for HITL display
    primary_agent = _cfg["enabled_agents"][0] if _cfg["enabled_agents"] else "unknown"
    selected_agent: Optional[str] = None

    # --- Causal routing (optional) ---
    if payload.causal_context:
        # Build CausalInterventionRecommendation objects from raw dicts
        causal_recs: Dict[str, CausalInterventionRecommendation] = {
            var: CausalInterventionRecommendation(
                variable=var,
                intervention_value=rec.get("intervention_value"),
                predicted_effect=rec.get("predicted_effect", 0.5),
                confidence=rec.get("confidence", 0.0),
                domain=rec.get("domain", "general"),
            )
            for var, rec in payload.causal_context.items()
        }

        # Build agent histories from enabled agents (stub: uniform history)
        agent_histories = {
            name: {"success_rate": 0.5, "avg_latency_ms": 1000.0, "total_runs": 0}
            for name in _cfg["enabled_agents"]
        }

        selected_agent = _causal_router.select_agent(
            task=payload.task,
            causal_context=causal_recs,
            agent_histories=agent_histories,
            task_type=payload.task_type,
            context=context,
        )
        if selected_agent:
            primary_agent = selected_agent
            context["causal_selected_agent"] = selected_agent

    rl_adjustments, hitl_status = _pre_execute(
        task=payload.task,
        run_id=run_id,
        task_type=payload.task_type,
        context=context,
        agent_name=primary_agent,
        causal_context=payload.causal_context,
    )

    # --- Orchestrator execution ---
    start_ms = time.monotonic() * 1000
    result = _orchestrator.run(payload.task, context=context)
    elapsed_ms = time.monotonic() * 1000 - start_ms

    # --- RL ingestion ---
    feedback = SwarmExecutionFeedback(
        run_id=run_id,
        task=payload.task,
        task_type=payload.task_type,
        success=1.0 if not result.get("error") else 0.0,
        quality_score=_estimate_quality(result),
        latency_ms=elapsed_ms,
        parameters_used=payload.parameters or {},
        agent_performance=_extract_agent_perf(result),
        raw_result=result,
    )
    _swarm_bridge.ingest_swarm_outcome(feedback)

    return RunResponse(
        task=result.get("task", payload.task),
        outputs=result.get("outputs", []),
        state=result.get("state", {}),
        run_id=run_id,
        hitl_status=hitl_status,
        rl_adjustments=rl_adjustments or None,
        selected_agent=selected_agent,
    )


@app.post("/run/swarm", response_model=SwarmRunResponse)
async def run_swarm(payload: SwarmRunRequest) -> SwarmRunResponse:
    """
    Execute a task using stigmergic swarm intelligence.

    Pipeline:
      1. RL parameter recommendations + HITL gate.
      2. Register orchestrator agents with SwarmOrchestrator (once).
      3. SwarmOrchestrator.execute_swarm() — agents coordinate via pheromone
         traces; emergent consensus patterns are detected automatically.
      4. Convert raw swarm result → SwarmExecutionFeedback → RL ingestion.

    The swarm is stateful within a server lifetime; pheromone traces from
    previous runs accumulate and guide subsequent executions.
    """
    run_id = str(uuid.uuid4())
    context = payload.context or {}
    context["run_id"] = run_id

    primary_agent = _cfg["enabled_agents"][0] if _cfg["enabled_agents"] else "swarm"

    rl_adjustments, hitl_status = _pre_execute(
        task=payload.task,
        run_id=run_id,
        task_type=payload.task_type,
        context=context,
        agent_name=primary_agent,
    )

    # Ensure agents are registered in the swarm orchestrator
    _ensure_swarm_agents()

    # --- Swarm execution ---
    start_ms = time.monotonic() * 1000
    swarm_result = _swarm_orchestrator.execute_swarm(
        task=payload.task,
        max_iterations=payload.max_iterations,
        use_stigmergy=payload.use_stigmergy,
    )
    elapsed_ms = time.monotonic() * 1000 - start_ms

    # --- RL ingestion ---
    feedback = swarm_result_to_feedback(
        run_id=run_id,
        task=payload.task,
        swarm_result=swarm_result,
        parameters_used=payload.parameters or {},
        task_type=payload.task_type,
    )
    feedback.latency_ms = elapsed_ms
    _swarm_bridge.ingest_swarm_outcome(feedback)

    return SwarmRunResponse(
        task=swarm_result.get("task", payload.task),
        run_id=run_id,
        iterations=swarm_result.get("iterations", 0),
        results=swarm_result.get("results", []),
        emergent_patterns=swarm_result.get("emergent_patterns", []),
        swarm_statistics=swarm_result.get("swarm_statistics", {}),
        hitl_status=hitl_status,
        rl_ingested=True,
    )


@app.get("/hitl/pending")
async def hitl_pending() -> Dict[str, Any]:
    """Return all pending HITL approval requests (for human reviewers)."""
    return {
        "pending": _approval_gate.get_pending_requests(),
        "mode": settings.hitl_mode,
    }


@app.post("/hitl/{request_id}/decide")
async def hitl_decide(
    request_id: str,
    payload: HITLDecisionRequest,
) -> Dict[str, Any]:
    """Submit a human decision for a pending HITL approval request."""
    ok = _approval_gate.submit_decision(
        request_id=request_id,
        approved=payload.approved,
        resolver=payload.resolver,
        rejection_reason=payload.rejection_reason,
    )
    if not ok:
        raise HTTPException(status_code=404, detail=f"Unknown request_id: {request_id}")
    return {"request_id": request_id, "approved": payload.approved}


@app.get("/hitl/audit")
async def hitl_audit(limit: int = 50) -> Dict[str, Any]:
    """Return recent HITL audit trail."""
    return {
        "audit_trail": _approval_gate.get_audit_trail(limit=limit),
        "statistics": _approval_gate.get_statistics(),
    }


@app.get("/rl/statistics")
async def rl_statistics() -> Dict[str, Any]:
    """Return RL bridge statistics (for monitoring / debugging)."""
    return _swarm_bridge.get_statistics()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _estimate_quality(result: Dict[str, Any]) -> float:
    """Heuristic quality score from orchestrator output."""
    if result.get("error"):
        return 0.0
    outputs = result.get("outputs", [])
    if not outputs:
        return 0.5
    success_count = sum(1 for o in outputs if o.get("status") == "success")
    return success_count / len(outputs)


def _extract_agent_perf(result: Dict[str, Any]) -> Dict[str, float]:
    """Build per-agent success-rate snapshot from orchestrator output."""
    perf: Dict[str, float] = {}
    for output in result.get("outputs", []):
        agent = output.get("agent", "unknown")
        perf[agent] = 1.0 if output.get("status") == "success" else 0.0
    return perf
