from fastapi import FastAPI
from pydantic import BaseModel
import json
from core.orchestrator import Orchestrator

with open("config/default.json") as f:
    DEFAULT = json.load(f)

app = FastAPI()

class TaskRequest(BaseModel):
    task: str
    agents: list[str] | None = None
    config: dict | None = None

@app.post("/task")
def run_task(req: TaskRequest):
    names = req.agents or DEFAULT["enabled_agents"]
    orch = Orchestrator(names, max_agents=DEFAULT["max_agents"])
    return {"result": orch.run(req.task, req.config or {})}

@app.get("/health")
def health():
    return {"ok": True}
