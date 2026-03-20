"""
Toolformer Agent — dynamic tool selection and invocation.

Inspects the available tool registry, decides which tool(s) to call based on
the task, executes them, and incorporates the results into a final answer.
Mirrors the Toolformer paper (Schick et al., 2023) pattern of learning when
tool calls add value.
"""

from typing import Dict, Any, List
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)


class Agent:
    CAPABILITIES = ["tool_use", "reasoning", "execution"]

    def __init__(self):
        self.llm = LLMConfig.get_llm_provider("toolformer")
        self.tool_registry = None
        try:
            from core.tools import get_tool_registry
            self.tool_registry = get_tool_registry()
        except Exception as exc:
            logger.debug("ToolformerAgent: tool registry unavailable: %s", exc)

    def _invoke(self, prompt: str, max_tokens: int = 500) -> str:
        try:
            result = self.llm.invoke(prompt=prompt, max_tokens=max_tokens)
            return result.strip() if isinstance(result, str) else str(result).strip()
        except Exception as exc:
            logger.warning("ToolformerAgent LLM call failed: %s", exc)
            return ""

    def run(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        if not task:
            return "Error: no task provided to ToolformerAgent"

        # Build tool catalogue
        tool_descriptions: List[str] = []
        if self.tool_registry:
            try:
                tools = self.tool_registry.list_tools()
                tool_descriptions = [
                    f"- {name}: {getattr(t, 'description', 'no description')}"
                    for name, t in (tools.items() if isinstance(tools, dict) else
                                    [(t.name, t) for t in tools])
                ]
            except Exception as exc:
                logger.debug("ToolformerAgent: could not list tools: %s", exc)

        if not tool_descriptions:
            # No tools available — fall back to pure reasoning
            return self._invoke(
                f"No external tools are available. Answer this task using only reasoning:\n\n{task}\n\nAnswer:"
            ) or f"ToolformerAgent: could not answer '{task}' (no tools, LLM unavailable)"

        catalogue = "\n".join(tool_descriptions)

        # Decide which tool to call
        decision = self._invoke(
            f"Available tools:\n{catalogue}\n\n"
            f"Task: {task}\n\n"
            "Which tool (if any) would help answer this task? "
            "Reply with ONLY the tool name, or 'none' if no tool is needed.\n\nTool:",
            max_tokens=50,
        )
        chosen_tool = decision.strip().lower().split()[0] if decision else "none"
        logger.info("ToolformerAgent selected tool: %s", chosen_tool)

        tool_result = ""
        if chosen_tool != "none" and self.tool_registry:
            try:
                tool = (
                    self.tool_registry.get_tool(chosen_tool)
                    if hasattr(self.tool_registry, "get_tool")
                    else None
                )
                if tool and callable(getattr(tool, "execute", None)):
                    tool_result = str(tool.execute({"task": task}))
                elif tool and callable(tool):
                    tool_result = str(tool(task))
            except Exception as exc:
                tool_result = f"Tool error: {exc}"
                logger.warning("ToolformerAgent tool '%s' failed: %s", chosen_tool, exc)

        # Synthesise final answer
        answer = self._invoke(
            f"Task: {task}\n"
            + (f"Tool used: {chosen_tool}\nTool output: {tool_result[:400]}\n" if tool_result else "")
            + "\nProvide a final, complete answer incorporating all available information:\n\nAnswer:"
        )
        return answer or f"ToolformerAgent: processed '{task}' with tool '{chosen_tool}'"

    def reflect(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        status = context.get("status", "success")
        lesson = "Use tool calls only when they add clear value; verify tool output before trusting it."
        return f"Reflection: ToolformerAgent {status} on '{task}'. Lesson: {lesson}"
