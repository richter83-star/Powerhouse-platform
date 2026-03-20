"""
Auto-Loop Agent — iterative self-improvement loop.

Repeatedly refines a response until either:
- The delta between iterations falls below a convergence threshold, or
- The maximum number of iterations is reached.

This mimics the "self-refine" pattern from the literature.
"""

from typing import Dict, Any
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)

_MAX_ITERATIONS = 4
_CONVERGENCE_RATIO = 0.05   # < 5 % change in length → converged


class Agent:
    CAPABILITIES = ["reasoning", "planning", "iterative_refinement"]

    def __init__(self):
        self.llm = LLMConfig.get_llm_provider("auto_loop_agent")

    def _invoke(self, prompt: str) -> str:
        try:
            result = self.llm.invoke(prompt=prompt, max_tokens=600)
            return result.strip() if isinstance(result, str) else str(result).strip()
        except Exception as exc:
            logger.warning("AutoLoopAgent LLM call failed: %s", exc)
            return ""

    def run(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        if not task:
            return "Error: no task provided to AutoLoopAgent"

        max_iters = int(context.get("max_iterations", _MAX_ITERATIONS))

        # Initial draft
        current = self._invoke(
            f"Provide an initial answer to the following task:\n\n{task}\n\nAnswer:"
        )
        if not current:
            return f"AutoLoopAgent: could not generate initial answer for '{task}'"

        for i in range(1, max_iters):
            refined = self._invoke(
                f"Task: {task}\n\n"
                f"Current answer (iteration {i}):\n{current}\n\n"
                "Critique this answer: identify any gaps, errors, or improvements needed. "
                "Then provide a better, more complete answer.\n\nImproved answer:"
            )
            if not refined:
                break

            # Convergence check: compare normalised lengths
            prev_len = len(current)
            new_len = len(refined)
            delta = abs(new_len - prev_len) / max(prev_len, 1)
            logger.debug("AutoLoopAgent iter=%d delta=%.3f", i + 1, delta)

            current = refined
            if delta < _CONVERGENCE_RATIO:
                logger.info("AutoLoopAgent converged at iteration %d", i + 1)
                break

        return current

    def reflect(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        lesson = "Avoid unnecessary loops; exit early when delta is small; set iteration budgets."
        return f"Reflection: AutoLoopAgent handled '{task}'. Lesson: {lesson}"
