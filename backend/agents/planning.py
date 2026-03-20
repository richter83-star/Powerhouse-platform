"""
Planning Agent — produces a structured, numbered action plan for a given task.

Uses LLM-backed step decomposition to turn an open-ended task into an ordered
list of concrete steps that downstream agents (or humans) can execute.
"""

from typing import Dict, Any, List
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are an expert project planner. Given a task, produce a clear, numbered "
    "action plan. Each step should be specific, actionable, and ordered logically. "
    "Format: '1. <step>\\n2. <step>\\n...'. Do not add preamble—start directly with step 1."
)


class Agent:
    CAPABILITIES = ["planning", "decomposition", "step_by_step"]

    def __init__(self):
        self.llm = LLMConfig.get_llm_provider("planning")

    def run(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        if not task:
            return "Error: no task provided to PlanningAgent"

        prior_outputs = context.get("outputs", [])
        prior_summary = ""
        if prior_outputs:
            snippets = [
                f"- {o['agent']}: {str(o.get('output', ''))[:200]}"
                for o in prior_outputs[-3:]
                if o.get("status") == "success"
            ]
            if snippets:
                prior_summary = "\n\nPrior agent findings:\n" + "\n".join(snippets)

        prompt = (
            f"{_SYSTEM_PROMPT}\n\nTask: {task}{prior_summary}\n\nAction plan:"
        )

        try:
            result = self.llm.invoke(prompt=prompt, max_tokens=600)
            plan = result.strip() if isinstance(result, str) else str(result).strip()
            logger.info("PlanningAgent produced %d-char plan", len(plan))
            return plan
        except Exception as exc:
            logger.warning("PlanningAgent LLM call failed: %s", exc)
            # Graceful fallback: heuristic decomposition
            words = task.split()
            steps: List[str] = [
                f"1. Clarify the scope and constraints of: {task}",
                f"2. Research background information relevant to {words[0] if words else 'the topic'}",
                "3. Draft an initial solution or approach",
                "4. Review and refine the draft",
                "5. Validate the result against original requirements",
            ]
            return "\n".join(steps)

    def reflect(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        status = context.get("status", "success")
        lesson = (
            "Clarify constraints before expanding the plan; prefer fewer, well-scoped steps."
        )
        return f"Reflection: PlanningAgent {status} on '{task}'. Lesson: {lesson}"
