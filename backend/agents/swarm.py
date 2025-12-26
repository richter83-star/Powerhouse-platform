from typing import Dict, Any, List
import re

from utils.logging import get_logger
from core.swarm.stigmergy import StigmergicMemory

logger = get_logger(__name__)


class SwarmAgent:
    """
    Swarm agent that collects proposals and selects a consensus answer.
    """

    def __init__(self):
        self.stigmergy = StigmergicMemory()

    def run(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        agents = context.get("agents", [])
        evaluator = context.get("evaluator") or context.get("evaluator_agent")

        if not agents:
            return f"swarm processed: {task}"

        proposals = []
        for agent in agents:
            try:
                if hasattr(agent, "run"):
                    output = agent.run({"task": task})
                else:
                    output = str(agent)
                proposals.append({"agent": agent, "output": output})
            except Exception as exc:
                logger.warning(f"Swarm agent proposal failed: {exc}")

        if not proposals:
            return f"swarm processed: {task}"

        proposal_outputs = [p["output"] for p in proposals]
        scored = self.stigmergy.score_consensus(proposal_outputs, evaluator=evaluator)

        for idx, scored_entry in enumerate(scored):
            output = scored_entry["proposal"]
            score = scored_entry["score"]
            agent = proposals[idx]["agent"] if idx < len(proposals) else f"agent_{idx}"
            self.stigmergy.deposit_trace(
                agent_id=agent.__class__.__name__ if hasattr(agent, "__class__") else f"agent_{idx}",
                location="swarm_consensus",
                trace_type="proposal",
                value=score,
                metadata={"output": output}
            )

        scored.sort(key=lambda s: s["score"], reverse=True)
        best = scored[0]["proposal"]
        logger.info(f"Swarm consensus score: {scored[0]['score']:.2f}")
        return best

    def reflect(self, context: Dict[str, Any]) -> str:
        lesson = "Collect diverse proposals, then converge on shared signals."
        return f"Reflection: Swarm consensus formed. Lesson learned: {lesson}"

    def _consensus_score(self, output: str, others: List[str]) -> float:
        if not others:
            return 0.5
        scores = [self._overlap(output, other) for other in others]
        return sum(scores) / len(scores)

    def _overlap(self, a: str, b: str) -> float:
        tokens_a = set(re.findall(r"[a-zA-Z0-9]+", a.lower()))
        tokens_b = set(re.findall(r"[a-zA-Z0-9]+", b.lower()))
        if not tokens_a or not tokens_b:
            return 0.0
        return len(tokens_a & tokens_b) / max(len(tokens_a | tokens_b), 1)

    def _combine_scores(self, consensus: float, evaluation_score: Any) -> float:
        if evaluation_score is None:
            return consensus
        return (0.6 * consensus) + (0.4 * float(evaluation_score))


Agent = SwarmAgent
