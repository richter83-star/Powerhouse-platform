"""
Debate Agent — adversarial dual-perspective reasoning.

Generates a PRO argument, then a CON argument, then a neutral judge adjudicates
and delivers a final verdict.  This forces surfacing of counterarguments before
committing to a conclusion, reducing confirmation bias.
"""

from typing import Dict, Any
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)


class Agent:
    CAPABILITIES = ["reasoning", "analysis", "argumentation", "critique"]

    def __init__(self):
        self.llm = LLMConfig.get_llm_provider("debate")

    def _invoke(self, prompt: str, max_tokens: int = 400) -> str:
        try:
            result = self.llm.invoke(prompt=prompt, max_tokens=max_tokens)
            return result.strip() if isinstance(result, str) else str(result).strip()
        except Exception as exc:
            logger.warning("DebateAgent LLM call failed: %s", exc)
            return "(LLM unavailable)"

    def run(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        if not task:
            return "Error: no task provided to DebateAgent"

        # Round 1 — PRO argument
        pro = self._invoke(
            f"You are an advocate. Make the strongest possible argument IN FAVOUR of "
            f"the following position or approach:\n\n\"{task}\"\n\nArgument:"
        )

        # Round 2 — CON argument
        con = self._invoke(
            f"You are a devil's advocate. Make the strongest possible argument AGAINST "
            f"the following position or approach:\n\n\"{task}\"\n\nArgument:"
        )

        # Round 3 — Judge verdict
        verdict = self._invoke(
            f"You are a neutral judge. Given these two arguments about \"{task}\":\n\n"
            f"PRO:\n{pro}\n\nCON:\n{con}\n\n"
            "Weigh both sides and deliver a balanced, evidence-based verdict. "
            "State which considerations are most important and what the best course of action is.\n\nVerdict:",
            max_tokens=500,
        )

        output = (
            f"=== PRO ===\n{pro}\n\n"
            f"=== CON ===\n{con}\n\n"
            f"=== VERDICT ===\n{verdict}"
        )
        logger.info("DebateAgent completed 3-round debate for task: %s", task[:60])
        return output

    def reflect(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        lesson = "Surface counterarguments before committing; strong conclusions survive adversarial scrutiny."
        return f"Reflection: DebateAgent processed '{task}'. Lesson: {lesson}"
