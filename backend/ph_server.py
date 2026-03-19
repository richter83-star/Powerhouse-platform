"""
Powerhouse FastAPI server (minimal).

Integration layer wires three architectural bridges into the /run endpoint:

1. SwarmFeedbackBridge  – captures swarm outcomes and feeds them back into
                          the RL Q-network so parameters improve over time.
2. ApprovalGate         – enforces the HITL policy (gate | audit | disabled)
                          before any execution.  Configurable via HITL_MODE.
3. CausalAgentRouter    – (used by callers that need causal routing; the server
                          exposes the /route endpoint as an optional pathway).
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
    ApprovalGate,
    ApprovalRequest,
    HITLMode,
    build_approval_gate,
)

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


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None
    # Optional hints for swarm / RL integration
    task_type: Optional[str] = None
    parameters: Optional[Dict[str, float]] = None


class RunResponse(BaseModel):
    task: str
    outputs: List[Dict[str, Any]]
    state: Dict[str, Any]
    run_id: str
    hitl_status: str = "not_checked"
    rl_adjustments: Optional[Dict[str, float]] = None


class HITLDecisionRequest(BaseModel):
    approved: bool
    resolver: str = "human"
    rejection_reason: Optional[str] = None


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
      1. Get RL-recommended parameter adjustments from the swarm bridge.
      2. Create an HITL approval request and enforce the configured gate mode.
         - gate:    blocks until human approves or timeout
         - audit:   logs and proceeds immediately
         - disabled: no check
      3. Run the orchestrator (sequential mode by default).
      4. Capture the outcome as SwarmExecutionFeedback and ingest into RL.
    """
    run_id = str(uuid.uuid4())
    context = payload.context or {}
    context["run_id"] = run_id

    # --- Step 1: RL parameter recommendations ---
    rl_adjustments = _swarm_bridge.get_recommended_adjustments(
        task=payload.task,
        task_type=payload.task_type,
    )
    if rl_adjustments:
        context.setdefault("rl_adjustments", rl_adjustments)

    # --- Step 2: HITL gate ---
    approval_req = _approval_gate.create_request(
        task=payload.task,
        reasoning_summary=(
            f"Task submitted via /run endpoint. "
            f"Agent selector will choose among {_cfg['enabled_agents']}."
        ),
        agent_name=_cfg["enabled_agents"][0] if _cfg["enabled_agents"] else "unknown",
        agent_confidence=1.0,
        estimated_impact="medium",
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

    hitl_status = approval_req.status.value

    # --- Step 3: Orchestrator execution ---
    start_ms = time.monotonic() * 1000
    result = _orchestrator.run(payload.task, context=context)
    elapsed_ms = time.monotonic() * 1000 - start_ms

    # --- Step 4: Feed outcome back into RL ---
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
    """
    Submit a human decision for a pending HITL approval request.

    Use this from your reviewer UI / webhook handler.
    """
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
    success_count = sum(
        1 for o in outputs if o.get("status") == "success"
    )
    return success_count / len(outputs)


def _extract_agent_perf(result: Dict[str, Any]) -> Dict[str, float]:
    """Build per-agent success-rate snapshot from orchestrator output."""
    perf: Dict[str, float] = {}
    for output in result.get("outputs", []):
        agent = output.get("agent", "unknown")
        perf[agent] = 1.0 if output.get("status") == "success" else 0.0
    return perf
