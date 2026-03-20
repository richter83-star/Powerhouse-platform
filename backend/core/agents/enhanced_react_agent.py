"""
Enhanced ReAct Agent with Advanced Capabilities.

Integrates causal reasoning, neurosymbolic reasoning, and hierarchical decomposition.
Feature flags are read from AdvancedFeaturesConfig by default; each flag can be
overridden at construction time by passing an explicit True/False value.
"""

from typing import Dict, Any, Optional
from agents.react import Agent as BaseReActAgent
from utils.logging import get_logger

logger = get_logger(__name__)


class EnhancedReActAgent(BaseReActAgent):
    """
    Enhanced ReAct agent with optional advanced capabilities.

    Features:
    - Causal reasoning for post-hoc decision analysis
    - Neurosymbolic reasoning for constraint satisfaction
    - Hierarchical task decomposition for complex tasks
    """

    def __init__(
        self,
        enable_causal: Optional[bool] = None,
        enable_neurosymbolic: Optional[bool] = None,
        enable_hierarchical: Optional[bool] = None,
    ):
        """
        Initialize enhanced ReAct agent.

        Args:
            enable_causal: Enable causal reasoning.  When *None* (default) the
                value is read from ``AdvancedFeaturesConfig.ENABLE_CAUSAL_REASONING``.
            enable_neurosymbolic: Enable neurosymbolic reasoning.  Defaults to
                ``AdvancedFeaturesConfig.ENABLE_NEUROSYMBOLIC``.
            enable_hierarchical: Enable hierarchical task decomposition.  Defaults
                to ``AdvancedFeaturesConfig.ENABLE_HIERARCHICAL_DECOMPOSITION``.
        """
        super().__init__()

        # Auto-configure from advanced_features_config when flag not explicit
        try:
            from config.advanced_features_config import advanced_features_config as _afc
            if enable_causal is None:
                enable_causal = _afc.ENABLE_CAUSAL_REASONING
            if enable_neurosymbolic is None:
                enable_neurosymbolic = _afc.ENABLE_NEUROSYMBOLIC
            if enable_hierarchical is None:
                enable_hierarchical = _afc.ENABLE_HIERARCHICAL_DECOMPOSITION
        except Exception:
            enable_causal = enable_causal or False
            enable_neurosymbolic = enable_neurosymbolic or False
            enable_hierarchical = enable_hierarchical or False

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
                self.causal_reasoner = CausalReasoner(CausalGraph())
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
            if task_complexity > 0.7:
                logger.info("Decomposing complex task hierarchically")
                try:
                    dag = self.task_decomposer.decompose(task)
                    subtasks = [t.description for t in dag.tasks.values() if t.depth > 0]
                    if subtasks:
                        task = f"{task} [Decomposed into: {', '.join(subtasks[:3])}]"
                        context = dict(context)
                        context['task'] = task
                        context['subtasks'] = subtasks
                except Exception as e:
                    logger.warning(f"Task decomposition failed: {e}")

        # Step 2: Apply neurosymbolic constraints before execution
        if self.enable_neurosymbolic and self.neurosymbolic_reasoner:
            constraints = context.get('constraints', [])
            if constraints:
                logger.info("Applying neurosymbolic constraints")
                try:
                    for constraint in constraints:
                        if isinstance(constraint, str):
                            parts = constraint.split()
                            if len(parts) >= 3:
                                subject = parts[0]
                                relation = "_".join(parts[1:-1])
                                obj = parts[-1]
                                self.neurosymbolic_reasoner.add_knowledge(
                                    entities=[
                                        {"id": subject, "type": "constraint_entity"},
                                        {"id": obj, "type": "constraint_entity"},
                                    ],
                                    relationships=[{
                                        "source": subject,
                                        "target": obj,
                                        "type": relation,
                                        "confidence": 0.9,
                                    }],
                                )
                    inference = self.neurosymbolic_reasoner.reason(
                        neural_inputs={"task": task},
                        apply_constraints=True,
                    )
                    if inference.confidence > 0.5:
                        context = dict(context)
                        context["neurosymbolic_inference"] = {
                            "confidence": inference.confidence,
                            "reasoning": inference.reasoning,
                        }
                        logger.debug(
                            "Neurosymbolic inference applied, confidence=%.2f",
                            inference.confidence,
                        )
                except Exception as e:
                    logger.warning(f"Neurosymbolic constraint application failed: {e}")

        # Step 3: Run base ReAct agent
        result = super().run(context)

        # Step 4: Post-process with causal reasoning if causal_context supplied
        if self.enable_causal and self.causal_reasoner:
            causal_context = context.get('causal_context', {})
            if causal_context and self.causal_reasoner.graph.nodes:
                logger.info("Applying causal reasoning post-processing")
                try:
                    causal_analysis: Dict[str, Any] = {}
                    for variable, value in causal_context.items():
                        try:
                            inference = self.causal_reasoner.do_intervention(
                                variable=variable, value=value
                            )
                            if inference.confidence > 0.5:
                                causal_analysis[variable] = {
                                    "effect": inference.effect,
                                    "confidence": inference.confidence,
                                    "method": inference.method,
                                }
                        except ValueError:
                            pass  # Variable not in graph – skip silently
                    if causal_analysis:
                        # Append a concise causal summary to the result
                        summary_parts = [
                            f"{v}: effect_size={max(eff['effect'].values(), default=0.0):.2f}"
                            for v, eff in causal_analysis.items()
                        ]
                        result = f"{result}\n[Causal analysis: {'; '.join(summary_parts)}]"
                except Exception as e:
                    logger.warning(f"Causal reasoning post-processing failed: {e}")

        return result

    def _estimate_complexity(self, task: str) -> float:
        """Estimate task complexity (0.0–1.0)."""
        words = task.split()
        step_indicators = ['and', 'then', 'also', 'after', 'before', 'while']
        step_count = sum(1 for w in step_indicators if w.lower() in task.lower())
        return min(1.0, (len(words) / 50.0) + (step_count * 0.1))
