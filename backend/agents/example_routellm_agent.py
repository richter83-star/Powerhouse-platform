
"""
Example agent implementation using RouteLLM.

This demonstrates how to integrate RouteLLM with your agent architectures.
"""

from typing import Dict, Any, Optional, List
from config.llm_config import llm_config
from utils.logging import get_logger

logger = get_logger(__name__)


class ChainOfThoughtAgentWithRouteLLM:
    """
    Chain of Thought agent powered by RouteLLM.
    
    This agent breaks down complex problems into sequential reasoning steps,
    with RouteLLM automatically selecting the best model for each step.
    """
    
    def __init__(self, agent_name: str = "chain_of_thought"):
        """
        Initialize agent with RouteLLM.
        
        Args:
            agent_name: Name of the agent (for routing strategy lookup)
        """
        self.agent_name = agent_name
        
        # Get LLM provider with agent-specific routing strategy
        self.llm = llm_config.get_llm_provider(agent_name)
        
        logger.info(
            f"Initialized {agent_name} with RouteLLM "
            f"(strategy: {self.llm.routing_strategy})"
        )
    
    def execute(self, task: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute task using Chain of Thought reasoning.
        
        Args:
            task: Task description
            context: Optional context information
            
        Returns:
            Dict with result, reasoning steps, and metadata
        """
        logger.info(f"Executing task: {task[:100]}...")
        
        # Step 1: Break down the problem
        breakdown_prompt = f"""
        Task: {task}
        {f"Context: {context}" if context else ""}
        
        Break this task into 3-5 logical steps.
        List each step clearly.
        """
        
        breakdown_response = self.llm.invoke(
            prompt=breakdown_prompt,
            temperature=0.7,
            max_tokens=300
        )
        
        steps = breakdown_response.content
        logger.info(f"Broke down task into steps (model: {breakdown_response.model})")
        
        # Step 2: Solve each step sequentially
        solution_prompt = f"""
        Task: {task}
        Steps identified:
        {steps}
        
        Now, solve each step systematically and provide the final answer.
        """
        
        solution_response = self.llm.invoke(
            prompt=solution_prompt,
            temperature=0.7,
            max_tokens=500
        )
        
        logger.info(f"Generated solution (model: {solution_response.model})")
        
        # Return result with metadata
        return {
            "status": "success",
            "task": task,
            "reasoning_steps": steps,
            "solution": solution_response.content,
            "metadata": {
                "agent": self.agent_name,
                "routing_strategy": self.llm.routing_strategy,
                "models_used": {
                    "breakdown": breakdown_response.model,
                    "solution": solution_response.model
                },
                "total_tokens": (
                    breakdown_response.usage.get("total_tokens", 0) +
                    solution_response.usage.get("total_tokens", 0)
                )
            }
        }


class TreeOfThoughtAgentWithRouteLLM:
    """
    Tree of Thought agent powered by RouteLLM.
    
    This agent explores multiple reasoning paths in parallel,
    with RouteLLM intelligently routing to powerful models (GPT-4, Claude-3)
    for complex evaluation tasks.
    """
    
    def __init__(self, agent_name: str = "tree_of_thought"):
        """Initialize with RouteLLM."""
        self.agent_name = agent_name
        self.llm = llm_config.get_llm_provider(agent_name)
        
        # Tree of Thought typically needs quality-first routing
        logger.info(
            f"Initialized {agent_name} with RouteLLM "
            f"(strategy: {self.llm.routing_strategy})"
        )
    
    def execute(
        self,
        task: str,
        num_branches: int = 3,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Execute task using Tree of Thought reasoning.
        
        Args:
            task: Task description
            num_branches: Number of thought branches to explore
            max_depth: Maximum depth of thought tree
            
        Returns:
            Dict with best solution and exploration tree
        """
        logger.info(f"Executing Tree of Thought for: {task[:100]}...")
        
        # Generate multiple initial thoughts
        thoughts = []
        for i in range(num_branches):
            prompt = f"""
            Task: {task}
            
            Generate thought #{i+1} - a unique approach or perspective
            for solving this task.
            """
            
            response = self.llm.invoke(
                prompt=prompt,
                temperature=0.8,  # Higher temp for diversity
                max_tokens=200
            )
            
            thoughts.append({
                "thought": response.content,
                "model": response.model,
                "score": None  # Will be evaluated
            })
        
        logger.info(f"Generated {len(thoughts)} initial thoughts")
        
        # Evaluate all thoughts
        evaluation_prompt = f"""
        Task: {task}
        
        Evaluate these {len(thoughts)} approaches:
        
        {chr(10).join([f"{i+1}. {t['thought']}" for i, t in enumerate(thoughts)])}
        
        Score each approach (1-10) and explain why.
        Return as JSON: {{"scores": [score1, score2, ...], "reasoning": "..."}}
        """
        
        eval_response = self.llm.invoke(
            prompt=evaluation_prompt,
            json_mode=True,
            temperature=0.3
        )
        
        logger.info(f"Evaluated thoughts (model: {eval_response.model})")
        
        # Select best thought and expand
        best_thought = thoughts[0]  # Simplified selection
        
        final_prompt = f"""
        Task: {task}
        Best approach: {best_thought['thought']}
        
        Develop this approach into a complete solution.
        """
        
        final_response = self.llm.invoke(
            prompt=final_prompt,
            temperature=0.7,
            max_tokens=600
        )
        
        return {
            "status": "success",
            "task": task,
            "explored_thoughts": thoughts,
            "evaluation": eval_response.content,
            "final_solution": final_response.content,
            "metadata": {
                "agent": self.agent_name,
                "routing_strategy": self.llm.routing_strategy,
                "num_branches": num_branches,
                "models_used": list(set([
                    t["model"] for t in thoughts
                ] + [eval_response.model, final_response.model]))
            }
        }


class ReActAgentWithRouteLLM:
    """
    ReAct (Reasoning + Acting) agent powered by RouteLLM.
    
    This agent alternates between reasoning and actions,
    with RouteLLM adapting to the complexity of each step.
    """
    
    def __init__(self, agent_name: str = "react"):
        """Initialize with RouteLLM."""
        self.agent_name = agent_name
        self.llm = llm_config.get_llm_provider(agent_name)
        
        # Available tools (mock for demonstration)
        self.tools = {
            "search": self._mock_search,
            "calculate": self._mock_calculate,
            "lookup": self._mock_lookup
        }
        
        logger.info(f"Initialized {agent_name} with {len(self.tools)} tools")
    
    def _mock_search(self, query: str) -> str:
        """Mock search tool."""
        return f"Search results for '{query}': [Mock data]"
    
    def _mock_calculate(self, expression: str) -> str:
        """Mock calculator tool."""
        try:
            result = eval(expression)
            return f"Calculation: {expression} = {result}"
        except:
            return f"Invalid expression: {expression}"
    
    def _mock_lookup(self, key: str) -> str:
        """Mock lookup tool."""
        return f"Lookup result for '{key}': [Mock data]"
    
    def execute(
        self,
        task: str,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Execute task using ReAct pattern.
        
        Args:
            task: Task description
            max_iterations: Maximum reasoning-action cycles
            
        Returns:
            Dict with solution and execution trace
        """
        logger.info(f"Executing ReAct for: {task[:100]}...")
        
        history = []
        observation = ""
        
        for i in range(max_iterations):
            # Reasoning step
            reasoning_prompt = f"""
            Task: {task}
            Iteration: {i+1}/{max_iterations}
            
            Previous observations:
            {observation if observation else "None"}
            
            Available tools: {', '.join(self.tools.keys())}
            
            Think step-by-step:
            1. What do I know?
            2. What do I need to find out?
            3. Which tool should I use next?
            
            Respond with: Thought: ... | Action: tool_name(args)
            """
            
            response = self.llm.invoke(
                prompt=reasoning_prompt,
                temperature=0.7,
                max_tokens=200
            )
            
            thought_and_action = response.content
            history.append({
                "iteration": i + 1,
                "thought": thought_and_action,
                "model": response.model
            })
            
            # Check if task is complete
            if "FINAL ANSWER" in thought_and_action.upper():
                logger.info("Task completed")
                break
            
            # Execute action (simplified)
            observation = "[Action executed: mock result]"
            history[-1]["observation"] = observation
        
        # Generate final answer
        final_prompt = f"""
        Task: {task}
        
        Based on this reasoning trace:
        {chr(10).join([f"{h['thought']}" for h in history])}
        
        Provide the final answer.
        """
        
        final_response = self.llm.invoke(
            prompt=final_prompt,
            temperature=0.5,
            max_tokens=300
        )
        
        return {
            "status": "success",
            "task": task,
            "execution_trace": history,
            "final_answer": final_response.content,
            "metadata": {
                "agent": self.agent_name,
                "routing_strategy": self.llm.routing_strategy,
                "iterations": len(history),
                "models_used": list(set([h["model"] for h in history] + [final_response.model]))
            }
        }


# Export example agents
__all__ = [
    "ChainOfThoughtAgentWithRouteLLM",
    "TreeOfThoughtAgentWithRouteLLM",
    "ReActAgentWithRouteLLM"
]

