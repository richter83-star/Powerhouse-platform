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
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from api.middleware import RateLimitMiddleware
from core.security.rate_limit_config import security_rate_limits

from core.orchestrator import Orchestrator
from config.settings import get_settings
from utils.logging import get_logger

logger = get_logger(__name__)

# --- Integration bridges ---
from core.learning.swarm_feedback_bridge import (
    SwarmFeedbackBridge,
    SwarmExecutionFeedback,
    swarm_result_to_feedback,
)
from core.human_in_the_loop import (
    build_approval_gate,
)
from core.human_in_the_loop.webhook_handler import build_webhook_handler
from core.reasoning.causal_agent_router import (
    CausalAgentRouter,
    CausalInterventionRecommendation,
)
from core.swarm.swarm_orchestrator import SwarmOrchestrator

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

settings = get_settings()

# ---------------------------------------------------------------------------
# Authentication dependency (Group A)
# ---------------------------------------------------------------------------

def _get_optional_token(request: Request) -> Optional[str]:
    """Extract Bearer token or X-API-Key from request headers."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return request.headers.get("X-API-Key")


def require_api_auth(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency that enforces authentication on protected endpoints.

    Accepts either:
    - ``Authorization: Bearer <JWT>``
    - ``X-API-Key: <key>``

    When ``settings.api_keys`` is empty AND ``settings.secret_key`` is the
    default placeholder the server is assumed to be running in un-keyed dev
    mode and all requests pass through (with a warning logged once).
    """
    _dev_mode = (
        not getattr(settings, "api_keys", [])
        and settings.secret_key == "your-secret-key-change-in-production"
    )
    if _dev_mode:
        return {"user_id": "dev", "tenant_id": "dev", "roles": ["admin"]}

    token = _get_optional_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide 'Authorization: Bearer <token>' or 'X-API-Key: <key>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Try static API key list first
    api_keys = getattr(settings, "api_keys", [])
    if api_keys and token in api_keys:
        return {"user_id": "api_key_user", "tenant_id": "default", "roles": ["user"]}

    # Try JWT verification
    try:
        from core.security import verify_token
        payload = verify_token(token)
        if payload:
            return payload
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ---------------------------------------------------------------------------
# Persistence paths (override via env vars)
# ---------------------------------------------------------------------------
_RL_CHECKPOINT_PATH  = os.environ.get("PH_RL_CHECKPOINT",  "data/rl_bridge.pt")
_HITL_AUDIT_LOG_PATH = os.environ.get("PH_HITL_AUDIT_LOG", "data/hitl_audit.jsonl")


# ---------------------------------------------------------------------------
# Lifespan: load persisted state on startup, save on shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    _swarm_bridge.load(_RL_CHECKPOINT_PATH)

    # Log which advanced features are active
    try:
        from config.advanced_features_config import advanced_features_config as _afc
        enabled = [
            name
            for name, val in _afc.model_dump().items()
            if name.startswith("ENABLE_") and val is True
        ]
        logger.info(
            "Advanced features enabled at startup: %s",
            ", ".join(enabled) if enabled else "none",
        )
    except Exception as _exc:
        logger.warning("Could not read advanced_features_config: %s", _exc)

    # Register alert notification channels if configured (Group E)
    try:
        from core.monitoring.alerting import alert_manager, SlackAlertHandler, EmailAlertHandler, AlertSeverity
        _slack_url = getattr(settings, "alert_slack_webhook_url", None)
        _email_to = getattr(settings, "alert_email_recipient", None)
        _min_sev_str = getattr(settings, "alert_min_severity", "error").lower()
        _sev_map = {
            "info": AlertSeverity.INFO,
            "warning": AlertSeverity.WARNING,
            "error": AlertSeverity.ERROR,
            "critical": AlertSeverity.CRITICAL,
        }
        _min_sev = _sev_map.get(_min_sev_str, AlertSeverity.ERROR)
        if _slack_url:
            alert_manager.register_handler(SlackAlertHandler(_slack_url, min_severity=_min_sev))
            logger.info("Slack alert handler registered (min_severity=%s)", _min_sev_str)
        if _email_to:
            alert_manager.register_handler(EmailAlertHandler(_email_to, min_severity=AlertSeverity.CRITICAL))
            logger.info("Email alert handler registered (recipient=%s)", _email_to)
        # Set operational thresholds
        alert_manager.set_threshold("agent_error_rate", {"warning": 0.3, "error": 0.6, "critical": 0.9})
        alert_manager.set_threshold("circuit_breaker_open_count", {"warning": 1, "error": 3, "critical": 5})
    except Exception as _al_exc:
        logger.warning("Alert handler registration failed: %s", _al_exc)

    # Initialise OpenTelemetry tracing if enabled (Feature 9)
    if getattr(settings, "otel_enabled", False):
        try:
            from core.monitoring.tracing import setup_tracing
            setup_tracing(
                service_name=getattr(settings, "otel_service_name", "powerhouse"),
                otlp_endpoint=getattr(settings, "otel_otlp_endpoint", None),
            )
        except Exception as _otel_exc:
            logger.warning("OpenTelemetry setup failed: %s", _otel_exc)

    yield
    # --- Shutdown ---
    _swarm_bridge.save(_RL_CHECKPOINT_PATH)
    _approval_gate.flush_audit_log()

    # Flush and shut down the tracer so all spans are exported before exit
    try:
        from core.monitoring.tracing import shutdown_tracing
        shutdown_tracing()
    except Exception:
        pass


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Powerhouse Multi-Agent Orchestrator API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def _global_exception_handler(request: Request, exc: Exception) -> Response:
    """Return a structured JSON 500 for any unhandled exception."""
    import traceback
    error_id = str(uuid.uuid4())
    logger.error(
        "Unhandled exception [error_id=%s] %s %s: %s",
        error_id, request.method, request.url.path, exc,
        exc_info=True,
    )
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": error_id,
            "path": request.url.path,
        },
    )

# Rate limiting: workflow endpoints — 10 requests per minute per IP/user
# (matches SecurityRateLimitConfig.workflow_max_requests).
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=security_rate_limits.workflow_max_requests,
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
# audit_log_path set here so records are appended on every resolve and loaded
# at construction.  The lifespan handler calls flush_audit_log() on shutdown
# to capture any in-flight (pending) records as well.
#
# When HITL_WEBHOOK_URL is configured, build a notify-only handler that POSTs
# the approval request payload to that URL so operators are notified in real
# time and can call /hitl/{request_id}/decide without polling.
_webhook_handler = None
if settings.hitl_webhook_url:
    try:
        _server_base = os.environ.get("PH_SERVER_BASE_URL", "http://localhost:8000")
        _webhook_handler = build_webhook_handler(
            url=settings.hitl_webhook_url,
            secret=settings.hitl_webhook_secret,
            server_base_url=_server_base,
        )
        logger.info("HITL webhook handler configured → %s", settings.hitl_webhook_url)
    except Exception as _wh_exc:
        logger.warning("Failed to configure HITL webhook handler: %s", _wh_exc)

_approval_gate = build_approval_gate(
    mode=settings.hitl_mode,
    timeout_seconds=settings.hitl_timeout_seconds,
    auto_approve_on_timeout=settings.hitl_auto_approve_on_timeout,
    trusted_agents=set(settings.hitl_trusted_agents),
    audit_log_path=_HITL_AUDIT_LOG_PATH,
    approval_handler=_webhook_handler,
)

# --- Causal agent router (no CausalReasoner at server level; callers supply
#     pre-computed causal_context; the router handles boost logic) ---
_causal_router = CausalAgentRouter(
    causal_reasoner=None,   # no live graph at server startup
    agent_selector=None,    # uses NeuralAgentSelector with default settings
)

# Wire the RL bridge to the causal router so that after bootstrap_interval
# swarm runs the auto-discovered causal graph is injected into the router.
_swarm_bridge.causal_agent_router = _causal_router

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

    @field_validator("task")
    @classmethod
    def task_must_be_non_empty_and_bounded(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("task must not be empty")
        if len(v) > 10_000:
            raise ValueError("task must not exceed 10 000 characters")
        return v


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
async def run(
    payload: RunRequest,
    _auth: Dict[str, Any] = Depends(require_api_auth),
) -> RunResponse:
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
async def run_swarm(
    payload: SwarmRunRequest,
    _auth: Dict[str, Any] = Depends(require_api_auth),
) -> SwarmRunResponse:
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


@app.get("/metrics")
async def metrics_endpoint() -> Response:
    """
    Expose all Prometheus metrics in OpenMetrics text format.

    Compatible with any Prometheus scrape configuration::

        - job_name: powerhouse
          static_configs:
            - targets: ["localhost:8000"]
          metrics_path: /metrics
    """
    from core.monitoring.metrics import get_metrics, get_metrics_content_type
    return Response(content=get_metrics(), media_type=get_metrics_content_type())


@app.get("/circuit-breakers")
async def circuit_breakers_endpoint() -> Dict[str, Any]:
    """
    Return the current state and statistics of all per-agent circuit breakers.

    Useful for diagnosing which agents are repeatedly failing and when their
    cooldown window expires.
    """
    return {
        name: cb.get_stats()
        for name, cb in _orchestrator._circuit_breakers.items()
    }


@app.get("/agents/capabilities")
async def agent_capabilities() -> Dict[str, Any]:
    """
    Discover all loaded agents and their capability lists.

    Returns two views:
    - ``agents``:       agent class name → capability list
    - ``capabilities``: capability string → list of agent class names
    """
    agents_map: Dict[str, List[str]] = {}
    cap_map: Dict[str, List[str]] = {}
    for agent in _orchestrator.agents:
        name = agent.__class__.__name__
        caps = (
            getattr(type(agent), "CAPABILITIES", None)
            or getattr(agent, "capabilities", None)
            or []
        )
        agents_map[name] = list(caps)
        for cap in caps:
            cap_map.setdefault(cap, []).append(name)
    return {"agents": agents_map, "capabilities": cap_map}


@app.websocket("/ws/run")
async def ws_run(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time bidirectional agent execution.

    The client sends a single JSON message with a ``task`` field and optionally
    a ``context`` dict.  Each agent result is pushed as it completes; a final
    ``{"done": true}`` frame closes the stream.

    Example (JavaScript)::

        const ws = new WebSocket("ws://localhost:8000/ws/run");
        ws.onopen = () => ws.send(JSON.stringify({ task: "analyse the dataset" }));
        ws.onmessage = (e) => console.log(JSON.parse(e.data));
    """
    import asyncio as _aio
    import json as _json

    await websocket.accept()
    try:
        raw = await websocket.receive_text()
        data = _json.loads(raw)
    except Exception as exc:
        await websocket.send_json({"error": f"Invalid payload: {exc}"})
        await websocket.close()
        return

    task = data.get("task", "")
    extra_ctx = data.get("context") or {}
    if not task:
        await websocket.send_json({"error": "task field is required"})
        await websocket.close()
        return

    _queue: _aio.Queue = _aio.Queue()
    _loop = _aio.get_event_loop()

    def _cb(result: Dict[str, Any]) -> None:
        _loop.call_soon_threadsafe(_queue.put_nowait, result)

    fut = _loop.run_in_executor(
        None,
        lambda: _orchestrator.run_streaming(task, extra_ctx, _cb),
    )

    while not fut.done():
        try:
            item = await _aio.wait_for(_queue.get(), timeout=0.1)
            await websocket.send_json(item)
        except _aio.TimeoutError:
            continue
        except Exception:
            break

    # Drain remaining
    while not _queue.empty():
        item = _queue.get_nowait()
        try:
            await websocket.send_json(item)
        except Exception:
            break

    try:
        await websocket.send_json({"done": True})
        await websocket.close()
    except Exception:
        pass


@app.post("/run/stream")
async def run_stream(
    payload: RunRequest,
    _auth: Dict[str, Any] = Depends(require_api_auth),
) -> Response:
    """
    Execute a task and stream each agent's result as a Server-Sent Events (SSE) stream.

    Each agent result is emitted immediately as it finishes::

        data: {"agent": "ReactAgent", "status": "success", "output": "...", "duration_ms": 123}\n\n

    The stream closes with a final ``data: {"done": true}`` event.

    Client example (curl)::

        curl -N -X POST /run/stream \\
             -H 'Content-Type: application/json' \\
             -d '{"task": "analyse the dataset"}'
    """
    import asyncio as _asyncio
    import json as _json

    run_id = str(uuid.uuid4())
    context = payload.context or {}
    context["run_id"] = run_id
    _queue: _asyncio.Queue = _asyncio.Queue()
    _loop = _asyncio.get_event_loop()

    def _cb(result: Dict[str, Any]) -> None:
        _loop.call_soon_threadsafe(_queue.put_nowait, result)

    async def _event_stream():
        fut = _loop.run_in_executor(
            None,
            lambda: _orchestrator.run_streaming(payload.task, payload.context or {}, _cb),
        )
        while not fut.done():
            try:
                item = await _asyncio.wait_for(_queue.get(), timeout=0.1)
                yield f"data: {_json.dumps(item)}\n\n"
            except _asyncio.TimeoutError:
                continue
        # Drain any items that arrived after fut completed
        while not _queue.empty():
            item = _queue.get_nowait()
            yield f"data: {_json.dumps(item)}\n\n"
        yield 'data: {"done": true}\n\n'

    return Response(
        content=_event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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
