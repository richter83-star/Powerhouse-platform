"""
Hierarchical Agents — parent–child task delegation.

The parent agent decomposes the task into subtasks, delegates each to an LLM
call acting as a specialist child, then aggregates and synthesises the results.
This mirrors the "Hierarchical Task Network" pattern.
"""

from typing import Dict, Any, List
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)

_MAX_SUBTASKS = 5


class Agent:
    CAPABILITIES = ["planning", "orchestration", "decomposition", "synthesis"]

    def __init__(self):
        self.llm = LLMConfig.get_llm_provider("hierarchical_agents")

    def _invoke(self, prompt: str, max_tokens: int = 500) -> str:
        try:
            result = self.llm.invoke(prompt=prompt, max_tokens=max_tokens)
            return result.strip() if isinstance(result, str) else str(result).strip()
        except Exception as exc:
            logger.warning("HierarchicalAgent LLM call failed: %s", exc)
            return ""

    def run(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        if not task:
            return "Error: no task provided to HierarchicalAgentsAgent"

        # Parent: decompose task into subtasks
        decomposition = self._invoke(
            f"Break the following task into at most {_MAX_SUBTASKS} independent subtasks. "
            "Return ONLY a numbered list, one subtask per line, no explanations.\n\n"
            f"Task: {task}\n\nSubtasks:",
            max_tokens=300,
        )

        subtasks: List[str] = []
        for line in decomposition.splitlines():
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                # Strip leading "1. " or "- "
                cleaned = line.lstrip("0123456789.-) ").strip()
                if cleaned:
                    subtasks.append(cleaned)

        if not subtasks:
            subtasks = [task]  # fallback: treat whole task as single subtask

        logger.info("HierarchicalAgent decomposed into %d subtasks", len(subtasks))

        # Child agents: execute each subtask
        child_results: List[str] = []
        for i, subtask in enumerate(subtasks[:_MAX_SUBTASKS], 1):
            child_output = self._invoke(
                f"You are a specialist child agent. Your sole task is:\n\n{subtask}\n\n"
                f"Parent task context: {task[:200]}\n\n"
                "Provide a complete, focused answer for your specific subtask only.\n\nAnswer:",
            )
            if child_output:
                child_results.append(f"Subtask {i} ({subtask[:60]}):\n{child_output}")
            else:
                child_results.append(f"Subtask {i}: (no output)")

        # Parent: synthesise child results
        combined = "\n\n".join(child_results)
        synthesis = self._invoke(
            f"You are a senior coordinator. Your team of child agents completed the following "
            f"subtasks for the parent task: '{task}'.\n\n{combined}\n\n"
            "Synthesise their outputs into a single, cohesive final answer:\n\nFinal answer:",
            max_tokens=700,
        )

        if not synthesis:
            synthesis = combined  # fallback: return raw child results

        return synthesis

    def reflect(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        lesson = "Propagate constraints from parent to child clearly; synthesis step is critical."
        return f"Reflection: HierarchicalAgentsAgent handled '{task}'. Lesson: {lesson}"
