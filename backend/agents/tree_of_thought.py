"""
Tree-of-Thought Agent - Explores multiple reasoning paths in a tree structure.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ThoughtNode:
    """Node in the thought tree."""
    thought: str
    depth: int
    score: float = 0.0
    parent: Optional['ThoughtNode'] = None
    children: List['ThoughtNode'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class Agent:
    """Tree-of-Thought agent that explores multiple reasoning paths."""
    
    def __init__(self):
        """Initialize Tree-of-Thought agent."""
        self.llm = LLMConfig.get_llm_provider("tree_of_thought")
        self.max_depth = 3
        self.branching_factor = 3  # Number of thoughts to explore per node
        self.max_nodes = 20  # Maximum total nodes to explore
        self._last_nodes: List[ThoughtNode] = []
    
    def run(self, context: Dict[str, Any]) -> str:
        """
        Execute Tree-of-Thought reasoning.
        
        ToT pattern:
        1. Generate multiple initial thoughts
        2. Evaluate and score each thought
        3. Expand promising thoughts (breadth-first or best-first)
        4. Continue until solution found or max depth reached
        5. Backtrack to find best path
        
        Args:
            context: Execution context with 'task' key
            
        Returns:
            Final answer with reasoning tree
        """
        task = context.get('task', '')
        if not task:
            return "Error: No task provided"
        
        self.max_depth = context.get('max_depth', self.max_depth)
        self.branching_factor = context.get('branching_factor', self.branching_factor)
        
        logger.info(f"Tree-of-Thought agent starting task: {task[:100]}...")
        
        # Step 1: Generate initial thoughts (root level)
        initial_thoughts = self._generate_thoughts(task, None, 0)
        
        if not initial_thoughts:
            return "Error: Failed to generate initial thoughts"
        
        # Build tree
        root_nodes = [ThoughtNode(thought=thought, depth=0) for thought in initial_thoughts]
        all_nodes = list(root_nodes)
        
        # Step 2: Expand tree level by level
        for depth in range(1, self.max_depth + 1):
            if len(all_nodes) >= self.max_nodes:
                break
            
            # Get nodes at current depth
            current_level_nodes = [node for node in all_nodes if node.depth == depth - 1]
            
            if not current_level_nodes:
                break
            
            # Score current level nodes
            for node in current_level_nodes:
                node.score = self._evaluate_thought(task, node)
            
            # Sort by score and expand top nodes
            current_level_nodes.sort(key=lambda n: n.score, reverse=True)
            
            # Expand top nodes (limit to avoid explosion)
            nodes_to_expand = current_level_nodes[:self.branching_factor]
            
            new_nodes_this_level = []
            for parent_node in nodes_to_expand:
                # Generate child thoughts
                child_thoughts = self._generate_thoughts(task, parent_node, depth)
                
                for thought in child_thoughts:
                    if len(all_nodes) >= self.max_nodes:
                        break
                    
                    child_node = ThoughtNode(
                        thought=thought,
                        depth=depth,
                        parent=parent_node
                    )
                    parent_node.children.append(child_node)
                    all_nodes.append(child_node)
                    new_nodes_this_level.append(child_node)
                    
                    # Check if this is a solution
                    if self._is_solution(child_node.thought, task):
                        logger.info(f"Solution found at depth {depth}")
                        return self._extract_solution(child_node, all_nodes)
            
            if not new_nodes_this_level:
                break
        
        # Step 3: Find best path through tree
        logger.info(f"Tree exploration complete. Total nodes: {len(all_nodes)}")
        self._last_nodes = all_nodes

        # Score all leaf nodes
        leaf_nodes = [node for node in all_nodes if not node.children]
        for node in leaf_nodes:
            node.score = self._evaluate_thought(task, node)

        # Memory-guided scoring and pruning
        memories = context.get("memories") or context.get("memory_context") or []
        if memories:
            self.score_paths(task, leaf_nodes, memories)
            self.prune_paths(all_nodes)
        
        # Find best leaf
        if leaf_nodes:
            best_leaf = max(leaf_nodes, key=lambda n: n.score)
            output = self._extract_solution(best_leaf, all_nodes)
            return self._maybe_evaluate_output(output, context)
        
        # Fallback: return best root thought
        if root_nodes:
            root_nodes.sort(key=lambda n: n.score, reverse=True)
            output_attach = f"Best reasoning path:\n{self._format_path(root_nodes[0])}"
            return self._maybe_evaluate_output(output_attach, context)

        return self._maybe_evaluate_output("Unable to generate solution", context)

    def reflect(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        lesson = "Prune low-value branches early to focus depth on promising paths."
        return f"Reflection: Tree-of-Thought completed for '{task}'. Lesson learned: {lesson}"

    def score_paths(
        self,
        task: str,
        nodes: List[ThoughtNode],
        memories: List[Dict[str, Any]]
    ) -> None:
        """Re-score nodes using memory alignment."""
        memory_texts = []
        for memory in memories:
            if isinstance(memory, dict):
                memory_texts.append(memory.get("content", ""))
            else:
                memory_texts.append(str(memory))
        memory_text = " ".join(memory_texts)
        memory_tokens = set(memory_text.lower().split())
        for node in nodes:
            tokens = set(node.thought.lower().split())
            overlap = len(tokens & memory_tokens) / max(len(tokens), 1)
            node.score = min(1.0, max(0.0, node.score + (0.2 * overlap)))

    def prune_paths(self, nodes: List[ThoughtNode], threshold: float = 0.35) -> None:
        """Prune weak branches based on score threshold."""
        for node in nodes:
            if not node.children:
                continue
            node.children = [child for child in node.children if child.score >= threshold]

    def _maybe_evaluate_output(self, output: str, context: Dict[str, Any]) -> str:
        evaluator = context.get("evaluator") or context.get("evaluator_agent")
        if evaluator and hasattr(evaluator, "evaluate"):
            evaluation = evaluator.evaluate(output=output, context=context)
            context["evaluation"] = evaluation
            return f"{output}\n\nEvaluation: {evaluation}"
        return output
    
    def _generate_thoughts(self, task: str, parent_node: Optional[ThoughtNode], depth: int) -> List[str]:
        """Generate multiple thoughts for a given node."""
        context_info = ""
        if parent_node:
            # Include parent thought in context
            path = self._get_path_to_node(parent_node)
            context_info = f"\n\nCurrent reasoning path:\n{path}\n\nParent thought: {parent_node.thought}"
        
        prompt = f"""Task: {task}
{context_info}

Generate {self.branching_factor} different approaches or reasoning steps to continue solving this task.
Each approach should be distinct and explore a different angle or strategy.

For each approach, provide:
1. A clear thought/step
2. Brief reasoning why this approach might be promising

Format as a numbered list.
"""
        
        try:
            response = self.llm.invoke(
                prompt=prompt,
                temperature=0.8,  # Higher temperature for diversity
                max_tokens=600
            )
            thoughts_text = response.content
            return self._extract_thoughts(thoughts_text)
        except Exception as e:
            logger.error(f"Failed to generate thoughts: {e}")
            return []
    
    def _extract_thoughts(self, thoughts_text: str) -> List[str]:
        """Extract individual thoughts from text."""
        thoughts = []
        import re
        
        # Look for numbered list
        pattern = r'(?:^\d+[\.\)]\s*|^-\s*|^•\s*)(.+?)(?=\n\d+[\.\)]|\n-|\n•|\n\n|$)'
        matches = re.findall(pattern, thoughts_text, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            thought = match.strip()
            if thought and len(thought) > 10:  # Filter out too short thoughts
                thoughts.append(thought)
        
        # Fallback: split by newlines if pattern doesn't match
        if not thoughts:
            lines = [line.strip() for line in thoughts_text.split('\n') if line.strip()]
            thoughts = [line for line in lines if len(line) > 10][:self.branching_factor]
        
        return thoughts[:self.branching_factor]
    
    def _evaluate_thought(self, task: str, node: ThoughtNode) -> float:
        """Evaluate how promising a thought is (0.0 to 1.0)."""
        path = self._get_path_to_node(node)
        
        prompt = f"""Task: {task}

Reasoning path:
{path}

Evaluate how promising this reasoning path is for solving the task.
Consider:
1. How relevant is this path to the task?
2. How likely is this to lead to a solution?
3. How clear and logical is the reasoning?

Provide a score from 0.0 to 1.0, where:
- 1.0 = Excellent path, very likely to solve the task
- 0.7 = Good path, promising but may need refinement
- 0.5 = Moderate path, could work but uncertain
- 0.3 = Weak path, unlikely to lead to solution
- 0.0 = Irrelevant or incorrect path

Respond with just the numerical score (e.g., "0.85").
"""
        
        try:
            response = self.llm.invoke(
                prompt=prompt,
                temperature=0.2,  # Low temperature for consistent evaluation
                max_tokens=50
            )
            score_text = response.content.strip()
            # Extract number
            import re
            match = re.search(r'(\d+\.?\d*)', score_text)
            if match:
                score = float(match.group(1))
                # Normalize to 0-1 range
                if score > 1.0:
                    score = score / 10.0 if score <= 10.0 else 1.0
                return min(1.0, max(0.0, score))
        except Exception as e:
            logger.error(f"Failed to evaluate thought: {e}")
        
        # Default score based on depth (deeper = slightly less promising all else equal)
        return 0.5 - (node.depth * 0.05)
    
    def _is_solution(self, thought: str, task: str) -> bool:
        """Check if a thought represents a complete solution."""
        # Look for indicators of a final answer
        indicators = [
            "final answer",
            "solution is",
            "therefore",
            "in conclusion",
            "the answer is"
        ]
        
        thought_lower = thought.lower()
        return any(indicator in thought_lower for indicator in indicators)
    
    def _extract_solution(self, solution_node: ThoughtNode, all_nodes: List[ThoughtNode]) -> str:
        """Extract and format the solution from the best path."""
        path = self._get_path_to_node(solution_node)
        
        output = "Tree-of-Thought Solution:\n"
        output += "="*50 + "\n"
        output += f"Best Reasoning Path (Score: {solution_node.score:.2f}):\n\n"
        output += path
        output += "\n\n" + "="*50 + "\n"
        output += f"Final Answer:\n{solution_node.thought}"
        
        return output
    
    def _get_path_to_node(self, node: ThoughtNode) -> str:
        """Get the full path from root to a node."""
        path_nodes = []
        current = node
        
        while current:
            path_nodes.append(current)
            current = current.parent
        
        path_nodes.reverse()
        
        path_text = []
        for i, path_node in enumerate(path_nodes):
            indent = "  " * i
            path_text.append(f"{indent}Step {i+1}: {path_node.thought[:200]}...")
        
        return "\n".join(path_text)
    
    def _format_path(self, node: ThoughtNode) -> str:
        """Format a node's path."""
        return self._get_path_to_node(node)
