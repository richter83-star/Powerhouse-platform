from typing import Dict, Any, Optional
import re

from core.base_agent import BaseAgent
from utils.logging import get_logger

logger = get_logger(__name__)


class EvaluatorAgent(BaseAgent):
    """
    Evaluates agent outputs for relevance, efficiency, and completeness.
    """

    def __init__(self):
        super().__init__(
            name="EvaluatorAgent",
            agent_type="evaluator",
            capabilities=["evaluation", "scoring", "feedback"]
        )

    def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        output = input_data.get("output", "")
        evaluation = self.evaluate(output=output, context=context)
        return {"status": "success", "output": evaluation, "metadata": {}}

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.evaluate(output=None, context=context)

    def reflect(self, context: Dict[str, Any]) -> str:
        score = context.get("evaluation", {}).get("overall_score")
        if score is None:
            lesson = "No evaluation score available; capture outputs before scoring."
        elif score >= 0.8:
            lesson = "High-quality output; preserve this reasoning pattern."
        else:
            lesson = "Output quality lagged; tighten relevance and completeness checks."
        return f"Reflection: evaluation completed. Lesson learned: {lesson}"

    def evaluate(self, output: Optional[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        if context is None and isinstance(output, dict):
            context = output
            output = None
        if output is None:
            outputs = context.get("outputs", []) if context else []
            output = " ".join(
                entry.get("output", "") for entry in outputs if entry.get("output")
            )
        task = context.get("task", "") if context else ""
        relevance = self._score_relevance(task, output)
        completeness = self._score_completeness(output)
        efficiency = self._score_efficiency(task, output, context)
        overall = round((relevance + completeness + efficiency) / 3.0, 3)

        evaluation = {
            "relevance": relevance,
            "completeness": completeness,
            "efficiency": efficiency,
            "overall_score": overall
        }
        logger.info(f"Evaluation scores: {evaluation}")
        return evaluation

    def _score_relevance(self, task: str, output: str) -> float:
        if not task or not output:
            return 0.0
        task_tokens = set(re.findall(r"[a-zA-Z0-9]+", task.lower()))
        output_tokens = set(re.findall(r"[a-zA-Z0-9]+", output.lower()))
        if not task_tokens or not output_tokens:
            return 0.0
        overlap = len(task_tokens & output_tokens)
        score = overlap / max(len(task_tokens), 1)
        return round(min(1.0, score), 3)

    def _score_completeness(self, output: str) -> float:
        if not output:
            return 0.0
        length_score = min(len(output) / 500.0, 1.0)
        structure_bonus = 0.1 if "\n" in output or "." in output else 0.0
        return round(min(1.0, length_score + structure_bonus), 3)

    def _score_efficiency(self, task: str, output: str, context: Dict[str, Any]) -> float:
        if not output:
            return 0.0
        max_tokens = context.get("max_tokens", 500) if context else 500
        token_estimate = len(output.split())
        efficiency = 1.0 - min(token_estimate / max_tokens, 1.0)
        return round(max(0.0, efficiency), 3)
