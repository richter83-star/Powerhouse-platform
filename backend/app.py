import json
from core.orchestrator import Orchestrator

def main(task: str):
    with open("config/default.json") as f:
        cfg = json.load(f)
    orch = Orchestrator(cfg["enabled_agents"], max_agents=cfg["max_agents"])
    return orch.run(task)

if __name__ == "__main__":
    print(main("demo task: analyze quarterly sales"))
