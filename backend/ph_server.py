import json
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.orchestrator import Orchestrator
from config.settings import get_settings


# ------------------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------------------

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Powerhouse Multi-Agent Orchestrator API (minimal)",
)

# CORS: allow frontend on localhost:3000 (and anything else in settings.cors_origins)
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


# ------------------------------------------------------------------------------
# Models
# ------------------------------------------------------------------------------

class RunRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None


class RunResponse(BaseModel):
    task: str
    outputs: List[Dict[str, Any]]
    state: Dict[str, Any]


# ------------------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------------------

@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.post("/run", response_model=RunResponse)
async def run(payload: RunRequest) -> RunResponse:
    """
    Minimal sync endpoint: runs the orchestrator and returns the result.
    """
    context = payload.context or {}
    result = _orchestrator.run(payload.task, context=context)

    return RunResponse(
        task=result.get("task", payload.task),
        outputs=result.get("outputs", []),
        state=result.get("state", {}),
    )
