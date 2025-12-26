"""
Chain-of-Thought Agent - Step-by-step reasoning agent.
"""

from typing import Dict, Any
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)


class Agent:
    """Chain-of-Thought reasoning agent that breaks down problems into steps."""
    
    def __init__(self):
        """Initialize Chain-of-Thought agent."""
        self.llm = LLMConfig.get_llm_provider("chain_of_thought")
    
    def run(self, context: Dict[str, Any]) -> str:
        """
        Execute Chain-of-Thought reasoning.
        
        CoT pattern:
        1. Break problem into steps
        2. Solve each step sequentially
        3. Combine results into final answer
        
        Args:
            context: Execution context with 'task' key
            
        Returns:
            Final answer with reasoning chain
        """
        task = context.get('task', '')
        if not task:
            return "Error: No task provided"
        
        logger.info(f"Chain-of-Thought agent starting task: {task[:100]}...")
        
        # Step 1: Break down the problem into steps
        decomposition_prompt = f"""Break down the following problem into clear, sequential steps:

Problem: {task}

Provide a numbered list of steps that should be taken to solve this problem. Each step should be clear and actionable.
"""
        
        try:
            response = self.llm.invoke(
                prompt=decomposition_prompt,
                temperature=0.3,  # Lower temperature for more structured output
                max_tokens=500
            )
            steps_text = response.content
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            return f"Error: Failed to decompose problem: {str(e)}"
        
        # Extract steps
        steps = self._extract_steps(steps_text)
        logger.info(f"Decomposed problem into {len(steps)} steps")
        
        # Step 2: Solve each step sequentially
        reasoning_chain = []
        accumulated_context = task
        
        for i, step in enumerate(steps, 1):
            step_prompt = f"""Original Problem: {task}

Steps identified:
{self._format_steps(steps)}

Current Step {i}: {step}

Previous reasoning:
{self._format_reasoning_chain(reasoning_chain) if reasoning_chain else "None (first step)"}

Think through this step carefully and provide:
1. Your reasoning for this step
2. The solution or result for this step
3. How this contributes to solving the overall problem

Be thorough and clear in your reasoning.
"""
            
            try:
                response = self.llm.invoke(
                    prompt=step_prompt,
                    temperature=0.5,
                    max_tokens=800
                )
                step_reasoning = response.content
                
                reasoning_chain.append({
                    "step_number": i,
                    "step_description": step,
                    "reasoning": step_reasoning
                })
                
                # Update accumulated context
                accumulated_context += f"\n\nStep {i} reasoning: {step_reasoning}"
                
            except Exception as e:
                logger.error(f"Failed to solve step {i}: {e}")
                reasoning_chain.append({
                    "step_number": i,
                    "step_description": step,
                    "reasoning": f"Error: {str(e)}"
                })
        
        # Step 3: Synthesize final answer
        synthesis_prompt = f"""Original Problem: {task}

Complete Reasoning Chain:
{self._format_reasoning_chain(reasoning_chain)}

Based on the reasoning chain above, provide a clear, comprehensive final answer to the original problem.
Explain how the steps connect to form the complete solution.
"""
        
        try:
            response = self.llm.invoke(
                prompt=synthesis_prompt,
                temperature=0.4,
                max_tokens=1000
            )
            final_answer = response.content
        except Exception as e:
            logger.error(f"Failed to synthesize answer: {e}")
            # Fallback: use last step's reasoning
            final_answer = reasoning_chain[-1]["reasoning"] if reasoning_chain else "Unable to generate answer"
        
        logger.info("Chain-of-Thought reasoning completed")
        
        # Return formatted answer with reasoning chain
        return self._format_final_output(task, reasoning_chain, final_answer)
    
    def _extract_steps(self, steps_text: str) -> list:
        """Extract numbered steps from text."""
        steps = []
        # Look for numbered list patterns
        import re
        patterns = [
            r'^\d+[\.\)]\s*(.+)$',  # 1. or 1) format
            r'^Step \d+[:]\s*(.+)$',  # Step 1: format
            r'^-\s*(.+)$'  # - format
        ]
        
        for line in steps_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    steps.append(match.group(1).strip())
                    break
        
        # Fallback: split by newlines if no pattern matches
        if not steps:
            steps = [line.strip() for line in steps_text.split('\n') if line.strip()]
        
        return steps[:10]  # Limit to 10 steps max
    
    def _format_steps(self, steps: list) -> str:
        """Format steps for prompt."""
        return '\n'.join([f"{i+1}. {step}" for i, step in enumerate(steps)])
    
    def _format_reasoning_chain(self, reasoning_chain: list) -> str:
        """Format reasoning chain for prompt."""
        formatted = []
        for entry in reasoning_chain:
            formatted.append(
                f"Step {entry['step_number']}: {entry['step_description']}\n"
                f"Reasoning: {entry['reasoning']}\n"
            )
        return '\n'.join(formatted)
    
    def _format_final_output(self, task: str, reasoning_chain: list, final_answer: str) -> str:
        """Format final output with reasoning chain."""
        output = f"Task: {task}\n\n"
        output += "Reasoning Chain:\n"
        output += self._format_reasoning_chain(reasoning_chain)
        output += "\n" + "="*50 + "\n"
        output += f"Final Answer:\n{final_answer}"
        return output

    def reflect(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        outcome = context.get("status", "success")
        lesson = "Use shorter step summaries to keep synthesis focused."
        return f"Reflection: Chain-of-Thought {outcome} on '{task}'. Lesson learned: {lesson}"
