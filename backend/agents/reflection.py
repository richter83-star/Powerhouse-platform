"""
Reflection Agent — metacognitive critique and improvement of prior agent outputs.

Reads the accumulated outputs from earlier agents in the pipeline, identifies
weaknesses or gaps, and returns an improved synthesis or concrete suggestions.
"""

from typing import Dict, Any
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are a critical thinking assistant. You will be shown a task and the outputs "
    "produced so far by other agents. Your job is to:\n"
    "1. Identify what is missing, incorrect, or could be improved.\n"
    "2. Provide a concise, improved synthesis or corrective suggestions.\n"
    "Be specific and constructive. Do not repeat what was already said well."
)


class Agent:
    CAPABILITIES = ["reasoning", "analysis", "critique", "refinement"]

    def __init__(self):
        self.llm = LLMConfig.get_llm_provider("reflection")

    def run(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        outputs = context.get("outputs", [])

        if not outputs:
            return (
                "No prior outputs to reflect on. "
                "ReflectionAgent recommends ensuring earlier agents run first."
            )

        prior_text = "\n\n".join(
            f"[{o['agent']}]:\n{str(o.get('output', ''))[:400]}"
            for o in outputs
            if o.get("status") == "success"
        )
        if not prior_text:
            return "All prior agents encountered errors; no content available for reflection."

        prompt = (
            f"{_SYSTEM_PROMPT}\n\n"
            f"Task: {task}\n\n"
            f"Prior agent outputs:\n{prior_text}\n\n"
            "Reflection and improvements:"
        )

        try:
            result = self.llm.invoke(prompt=prompt, max_tokens=500)
            reflection = result.strip() if isinstance(result, str) else str(result).strip()
            logger.info("ReflectionAgent produced %d-char critique", len(reflection))
            return reflection
        except Exception as exc:
            logger.warning("ReflectionAgent LLM call failed: %s", exc)
            return (
                f"Reflection (fallback): The outputs address '{task}' but may benefit from "
                "additional detail, edge-case handling, and explicit validation of assumptions."
            )

    def reflect(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        lesson = "Ensure reflection captures both wins and misses; avoid repeating prior content."
        return f"Reflection: ReflectionAgent processed '{task}'. Lesson: {lesson}"
