from typing import List, Dict, Any
from importlib import import_module

class Orchestrator:
    def __init__(self, agent_names: List[str], max_agents: int = 19):
        if len(agent_names) > max_agents:
            raise ValueError(f"Too many agents: {len(agent_names)} > {max_agents}")
        self.agent_names = agent_names
        self.agents = [self._load_agent(n) for n in agent_names]

    def _load_agent(self, name: str):
        module = import_module(f"agents.{name}")
        agent_class_name = name.title().replace('_', '') + 'Agent'
        return module.Agent() if hasattr(module, 'Agent') else module.__dict__[agent_class_name]()

    def run(self, task: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = {"task": task, "outputs": [], "state": {}}
        gov = next((a for a in self.agents if a.__class__.__name__ == "GovernorAgent"), None)
        if gov:
            ok, msg = gov.preflight(task)
            if not ok:
                return {"error": f"Governor blocked task: {msg}"}

        mem = next((a for a in self.agents if a.__class__.__name__ == "AdaptiveMemoryAgent"), None)
        if mem:
            context["state"]["memory"] = mem.load()

        for agent in self.agents:
            if hasattr(agent, "skip_in_main") and getattr(agent, "skip_in_main"):
                continue
            out = agent.run(context)
            context["outputs"].append({"agent": agent.__class__.__name__, "output": out})
            if mem:
                mem.update(context, out)

        evalr = next((a for a in self.agents if a.__class__.__name__ == "EvaluatorAgent"), None)
        if evalr:
            context["evaluation"] = evalr.evaluate(context)

        meta = next((a for a in self.agents if a.__class__.__name__ == "MetaEvolverAgent"), None)
        if meta:
            meta.evolve(self.agents, context)

        return context
