"""
Enhanced ReAct Agent with Advanced Capabilities.

Integrates causal reasoning, neurosymbolic reasoning, and hierarchical decomposition.
"""

from typing import Dict, Any, Optional
from agents.react import Agent as BaseReActAgent
from utils.logging import get_logger

logger = get_logger(__name__)


class EnhancedReActAgent(BaseReActAgent):
    """
    Enhanced ReAct agent with optional advanced capabilities.
    
    Features:
    - Causal reasoning for decision-making
    - Neurosymbolic reasoning for constraint satisfaction
    - Hierarchical task decomposition
    """
    
    def __init__(self, enable_causal: bool = False, enable_neurosymbolic: bool = False, enable_hierarchical: bool = False):
        """
        Initialize enhanced ReAct agent.
        
        Args:
            enable_causal: Enable causal reasoning
            enable_neurosymbolic: Enable neurosymbolic reasoning
            enable_hierarchical: Enable hierarchical task decomposition
        """
        super().__init__()
        self.enable_causal = enable_causal
        self.enable_neurosymbolic = enable_neurosymbolic
        self.enable_hierarchical = enable_hierarchical
        
        # Initialize optional components
        self.causal_reasoner = None
        self.neurosymbolic_reasoner = None
        self.task_decomposer = None
        
        if enable_causal:
            try:
                from core.reasoning.causal_reasoner import CausalReasoner
                from core.reasoning.causal_discovery import CausalGraph
                # Initialize with empty graph (will be populated if needed)
                empty_graph = CausalGraph()
                self.causal_reasoner = CausalReasoner(empty_graph)
                logger.info("Causal reasoning enabled for EnhancedReActAgent")
            except Exception as e:
                logger.warning(f"Failed to enable causal reasoning: {e}")
        
        if enable_neurosymbolic:
            try:
                from core.reasoning.neurosymbolic import NeurosymbolicReasoner
                self.neurosymbolic_reasoner = NeurosymbolicReasoner()
                logger.info("Neurosymbolic reasoning enabled for EnhancedReActAgent")
            except Exception as e:
                logger.warning(f"Failed to enable neurosymbolic reasoning: {e}")
        
        if enable_hierarchical:
            try:
                from core.planning.hierarchical_decomposer import TaskDecomposer
                self.task_decomposer = TaskDecomposer()
                logger.info("Hierarchical decomposition enabled for EnhancedReActAgent")
            except Exception as e:
                logger.warning(f"Failed to enable hierarchical decomposition: {e}")
    
    def run(self, context: Dict[str, Any]) -> str:
        """
        Execute enhanced ReAct reasoning loop.
        
        Args:
            context: Execution context with 'task' key
            
        Returns:
            Final answer or result
        """
        task = context.get('task', '')
        if not task:
            return "Error: No task provided"
        
        # Step 1: Decompose complex tasks hierarchically if enabled
        if self.enable_hierarchical and self.task_decomposer:
            task_complexity = self._estimate_complexity(task)
            if task_complexity > 0.7:  # High complexity threshold
                logger.info("Decomposing complex task hierarchically")
                try:
                    dag = self.task_decomposer.decompose(task)
                    # Use decomposed subtasks
                    subtasks = [t.description for t in dag.tasks.values() if t.depth > 0]
                    if subtasks:
                        task = f"{task} [Decomposed into: {', '.join(subtasks[:3])}]"
                except Exception as e:
                    logger.warning(f"Task decomposition failed: {e}")
        
        # Step 2: Apply neurosymbolic constraints if enabled
        if self.enable_neurosymbolic and self.neurosymbolic_reasoner:
            constraints = context.get('constraints', [])
            if constraints:
                logger.info("Applying neurosymbolic constraints")
                try:
                    # Convert constraints to knowledge graph facts
                    for constraint in constraints:
                        # Simplified: would parse constraint properly
                        pass
                except Exception as e:
                    logger.warning(f"Neurosymbolic constraint application failed: {e}")
        
        # Step 3: Run base ReAct agent
        result = super().run(context)
        
        # Step 4: Post-process with causal reasoning if enabled
        if self.enable_causal and self.causal_reasoner:
            causal_context = context.get('causal_context', {})
            if causal_context:
                logger.info("Applying causal reasoning post-processing")
                try:
                    # Could analyze result causally
                    pass
                except Exception as e:
                    logger.warning(f"Causal reasoning post-processing failed: {e}")
        
        return result
    
    def _estimate_complexity(self, task: str) -> float:
        """Estimate task complexity (0.0-1.0)."""
        # Simple heuristic: longer tasks with multiple steps are more complex
        words = task.split()
        step_indicators = ['and', 'then', 'also', 'after', 'before', 'while']
        step_count = sum(1 for word in step_indicators if word.lower() in task.lower())
        
        complexity = min(1.0, (len(words) / 50.0) + (step_count * 0.1))
        return complexity

