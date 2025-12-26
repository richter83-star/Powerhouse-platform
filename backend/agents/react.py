"""
ReAct Agent - Reasoning and Acting agent that interleaves reasoning and actions.
"""

import re
from typing import Dict, Any, Optional
from config.llm_config import LLMConfig
from core.tools import get_tool_registry
from utils.logging import get_logger

logger = get_logger(__name__)


class Agent:
    """ReAct (Reasoning + Acting) agent."""
    
    def __init__(self):
        """Initialize ReAct agent."""
        self.llm = LLMConfig.get_llm_provider("react")
        self.tool_registry = get_tool_registry()
        # Register default tools if registry is empty
        if not self.tool_registry.list_tools():
            from core.tools.builtin_tools import get_default_tools
            self.tool_registry.register_multiple(get_default_tools())
    
    def run(self, context: Dict[str, Any]) -> str:
        """
        Execute ReAct reasoning loop.
        
        ReAct pattern:
        1. Think: Reason about what to do next
        2. Act: Execute an action/tool
        3. Observe: See the result
        4. Repeat until task is complete
        
        Args:
            context: Execution context with 'task' key
            
        Returns:
            Final answer or result
        """
        task = context.get('task', '')
        if not task:
            return "Error: No task provided"
        
        logger.info(f"ReAct agent starting task: {task[:100]}...")
        
        max_iterations = context.get('max_iterations', 10)
        history = []
        observation = ""
        
        for iteration in range(max_iterations):
            # Step 1: Think - Reason about what to do next
            reasoning_prompt = self._build_reasoning_prompt(task, history, observation)
            
            try:
                response = self.llm.invoke(
                    prompt=reasoning_prompt,
                    temperature=0.7,
                    max_tokens=500
                )
                thought = response.content
            except Exception as e:
                logger.error(f"LLM invocation failed: {e}")
                return f"Error: Failed to get reasoning from LLM: {str(e)}"
            
            # Parse thought and action
            action = self._parse_action(thought)
            
            history.append({
                "iteration": iteration + 1,
                "thought": thought,
                "action": action
            })
            
            # Check if we have a final answer
            if self._has_final_answer(thought):
                logger.info(f"ReAct completed in {iteration + 1} iterations")
                return self._extract_final_answer(thought)
            
            # Step 2: Act - Execute action if present
            if action:
                observation = self._execute_action(action)
                history[-1]["observation"] = observation
            else:
                observation = "No action specified in thought"
            
            # Step 3: Observe - The observation is already captured above
            # Check if we should continue
            if observation and "error" in observation.lower() and iteration > 2:
                logger.warning("Multiple errors encountered, stopping")
                break
        
        # Return best answer from history
        return self._synthesize_answer(task, history)
    
    def _build_reasoning_prompt(self, task: str, history: list, observation: str) -> str:
        """Build reasoning prompt for LLM."""
        available_tools = self.tool_registry.list_tools()
        
        prompt = f"""You are a ReAct agent. Your task is: {task}

Available tools: {', '.join(available_tools) if available_tools else 'None'}

Previous observations:
{observation if observation else "None (first iteration)"}

History:
{self._format_history(history) if history else "None"}

Think step-by-step:
1. What information do I currently have?
2. What do I need to find out to complete the task?
3. What action should I take next? (Use a tool or provide final answer)

Format your response as:
Thought: [Your reasoning]
Action: [tool_name(parameters)] or FINAL_ANSWER
Action Input: [parameters if using tool]

If you have enough information to answer, respond with:
Thought: [Your reasoning]
Action: FINAL_ANSWER
Action Input: [Your final answer to the task]
"""
        return prompt
    
    def _parse_action(self, thought: str) -> Optional[Dict[str, Any]]:
        """Parse action from thought text."""
        # Look for Action: tool_name(...) pattern
        action_match = re.search(r'Action:\s*(\w+)(?:\(([^)]+)\))?', thought, re.IGNORECASE)
        if not action_match:
            return None
        
        tool_name = action_match.group(1)
        if tool_name.upper() == "FINAL_ANSWER":
            return {"type": "final_answer"}
        
        # Parse parameters
        params_str = action_match.group(2) if action_match.group(2) else ""
        params = self._parse_parameters(params_str)
        
        return {
            "type": "tool",
            "tool_name": tool_name,
            "parameters": params
        }
    
    def _parse_parameters(self, params_str: str) -> Dict[str, Any]:
        """Parse parameters from string."""
        params = {}
        if not params_str:
            return params
        
        # Simple parsing: key=value pairs
        pairs = re.findall(r'(\w+)=([^,\s]+)', params_str)
        for key, value in pairs:
            # Try to convert to appropriate type
            try:
                if value.startswith('"') or value.startswith("'"):
                    params[key] = value.strip('"\'')
                elif value.lower() in ('true', 'false'):
                    params[key] = value.lower() == 'true'
                elif '.' in value:
                    params[key] = float(value)
                else:
                    params[key] = int(value)
            except:
                params[key] = value
        
        return params
    
    def _execute_action(self, action: Dict[str, Any]) -> str:
        """Execute an action."""
        if action["type"] == "final_answer":
            return "Action executed: Providing final answer"
        
        tool_name = action.get("tool_name")
        parameters = action.get("parameters", {})
        
        if not tool_name:
            return "Error: No tool name specified"
        
        result = self.tool_registry.execute_tool(tool_name, **parameters)
        
        if result is None:
            return f"Error: Tool '{tool_name}' execution failed or returned None"
        
        return f"Tool '{tool_name}' result: {result}"
    
    def _has_final_answer(self, thought: str) -> bool:
        """Check if thought contains a final answer."""
        return "FINAL_ANSWER" in thought.upper() or "final answer" in thought.lower()
    
    def _extract_final_answer(self, thought: str) -> str:
        """Extract final answer from thought."""
        # Look for Action Input or Final Answer markers
        match = re.search(r'Action Input:\s*(.+?)(?:\n|$)', thought, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Fallback: look for explicit answer markers
        match = re.search(r'(?:final answer|answer):\s*(.+?)(?:\n|$)', thought, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Last resort: return the thought itself
        return thought

    def reflect(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        outcome = context.get("status", "success")
        lesson = "Balance tool usage with direct reasoning to reduce latency."
        return f"Reflection: ReAct {outcome} on '{task}'. Lesson learned: {lesson}"
    
    def _synthesize_answer(self, task: str, history: list) -> str:
        """Synthesize answer from history when max iterations reached."""
        if not history:
            return f"Unable to complete task: {task}"
        
        # Get the last observation
        last_obs = history[-1].get("observation", "")
        last_thought = history[-1].get("thought", "")
        
        # Try to extract any answer-like content
        if last_obs and "result" in last_obs.lower():
            return f"Based on observations: {last_obs}"
        
        return f"Completed reasoning process. Final thought: {last_thought[:200]}..."
    
    def _format_history(self, history: list) -> str:
        """Format history for prompt."""
        formatted = []
        for entry in history:
            step = f"Step {entry['iteration']}:\n"
            step += f"Thought: {entry.get('thought', '')}\n"
            if entry.get('action'):
                step += f"Action: {entry['action']}\n"
            if entry.get('observation'):
                step += f"Observation: {entry['observation']}\n"
            formatted.append(step)
        return "\n".join(formatted)
