"""
Multi-Agent Agent — delegates subtasks to a small set of specialist agents and
merges their outputs into a coherent final answer.

Spawns an inner Orchestrator with a curated subset of agents
(chain_of_thought, planning, reflection) so it benefits from all three
reasoning styles without recursion risk.
"""

from typing import Dict, Any
from utils.logging import get_logger

logger = get_logger(__name__)

_DELEGATE_AGENTS = ["chain_of_thought", "planning", "reflection"]


class Agent:
    CAPABILITIES = ["planning", "orchestration", "delegation", "synthesis"]

    def __init__(self):
        self._inner: Any = None  # lazy to avoid circular import

    def _get_inner(self):
        if self._inner is None:
            try:
                from core.orchestrator import Orchestrator
                self._inner = Orchestrator(
                    agent_names=_DELEGATE_AGENTS,
                    max_agents=len(_DELEGATE_AGENTS),
                    execution_mode="sequential",
                )
            except Exception as exc:
                logger.warning("MultiAgentAgent: could not build inner orchestrator: %s", exc)
        return self._inner

    def run(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        if not task:
            return "Error: no task provided to MultiAgentAgent"

        inner = self._get_inner()
        if inner is None:
            return f"MultiAgentAgent: inner orchestrator unavailable for '{task}'"

        try:
            result = inner.run(task, context={"task": task, "outputs": [], "state": {}})
            outputs = result.get("outputs", [])
            parts = []
            for o in outputs:
                if o.get("status") == "success" and o.get("output"):
                    parts.append(f"[{o['agent']}]\n{str(o['output'])[:600]}")
            if not parts:
                return f"MultiAgentAgent: all sub-agents returned errors for '{task}'"
            merged = "\n\n---\n\n".join(parts)
            logger.info("MultiAgentAgent merged %d sub-agent outputs", len(parts))
            return merged
        except Exception as exc:
            logger.error("MultiAgentAgent inner run failed: %s", exc)
            return f"MultiAgentAgent error: {exc}"

    def reflect(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        lesson = "Coordinate roles early to reduce duplication; select specialist agents intentionally."
        return f"Reflection: MultiAgentAgent processed '{task}'. Lesson: {lesson}"
