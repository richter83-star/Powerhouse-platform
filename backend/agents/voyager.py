"""
Voyager Agent — open-ended exploration using a hypothesis-test-observe loop.

Inspired by the Voyager paper (Wang et al., 2023): the agent proposes a
hypothesis, tests it via reasoning, observes the result, and iterates to
discover novel strategies or facts about the task space.
"""

from typing import Dict, Any, List
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)

_MAX_EXPLORATION_STEPS = 3


class Agent:
    CAPABILITIES = ["planning", "tool_use", "generation", "exploration", "discovery"]

    def __init__(self):
        self.llm = LLMConfig.get_llm_provider("voyager")
        self.skill_library: List[str] = []  # accumulated reusable skills

    def _invoke(self, prompt: str, max_tokens: int = 500) -> str:
        try:
            result = self.llm.invoke(prompt=prompt, max_tokens=max_tokens)
            return result.strip() if isinstance(result, str) else str(result).strip()
        except Exception as exc:
            logger.warning("VoyagerAgent LLM call failed: %s", exc)
            return ""

    def run(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        if not task:
            return "Error: no task provided to VoyagerAgent"

        observations: List[str] = []
        prior_context = "\n".join(
            f"- {o['agent']}: {str(o.get('output',''))[:150]}"
            for o in context.get("outputs", [])[-3:]
            if o.get("status") == "success"
        )

        for step in range(1, _MAX_EXPLORATION_STEPS + 1):
            obs_text = "\n".join(f"Step {i+1}: {o}" for i, o in enumerate(observations))

            # Propose hypothesis
            hypothesis = self._invoke(
                f"You are an explorer agent. Task: {task}\n"
                f"Prior context: {prior_context or 'none'}\n"
                f"Exploration log so far:\n{obs_text or 'none'}\n\n"
                f"Step {step}: Propose a specific hypothesis or sub-goal to investigate next. "
                "Be concrete and novel (avoid repeating prior steps).\n\nHypothesis:"
            )
            if not hypothesis:
                break

            # Test hypothesis via reasoning
            observation = self._invoke(
                f"Task: {task}\nHypothesis: {hypothesis}\n\n"
                "Reason about whether this hypothesis is correct, partially correct, or incorrect. "
                "What evidence supports or refutes it? What did you discover?\n\nObservation:"
            )
            if not observation:
                break

            skill = self._invoke(
                f"Based on this observation: '{observation[:300]}'\n"
                "Write a one-sentence reusable skill or insight that could apply to similar tasks.",
                max_tokens=100,
            )
            if skill:
                self.skill_library.append(skill)

            observations.append(f"H: {hypothesis[:200]} → O: {observation[:200]}")
            logger.debug("VoyagerAgent step %d complete", step)

        if not observations:
            return f"VoyagerAgent: exploration yielded no observations for '{task}'"

        skills_text = "\n".join(f"• {s}" for s in self.skill_library[-5:])
        exploration_log = "\n\n".join(observations)
        return (
            f"Exploration log ({len(observations)} steps):\n{exploration_log}"
            + (f"\n\nDiscovered skills:\n{skills_text}" if skills_text else "")
        )

    def reflect(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        lesson = "Chart exploration steps before execution; store reusable skills to avoid re-discovery."
        return f"Reflection: VoyagerAgent processed '{task}'. Lesson: {lesson}"
