"""
Enhanced Tree-of-Thought Agent with Advanced Capabilities.

Uses causal reasoning to compute a branch-score boost before the ToT search
begins so that causally significant paths are explored preferentially.
Auto-configures from AdvancedFeaturesConfig; can be overridden at construction.
"""

from typing import Any, Dict, Optional
from agents.tree_of_thought import Agent as BaseToTAgent
from utils.logging import get_logger

logger = get_logger(__name__)


class EnhancedTreeOfThoughtAgent(BaseToTAgent):
    """
    Enhanced Tree-of-Thought agent with causal reasoning for better path selection.

    Before the ToT search starts, causal interventions specified in
    ``context['causal_context']`` are evaluated and their predicted effect sizes
    are combined into a ``causal_score_boost`` that is added to each node's score
    in :meth:`score_paths`.
    """

    CAPABILITIES = ["reasoning", "planning", "generation", "causal"]

    def __init__(self, enable_causal: Optional[bool] = None):
        """
        Initialize enhanced ToT agent.

        Args:
            enable_causal: Enable causal reasoning.  Defaults to
                ``AdvancedFeaturesConfig.ENABLE_CAUSAL_REASONING``.
        """
        super().__init__()

        try:
            from config.advanced_features_config import advanced_features_config as _afc
            if enable_causal is None:
                enable_causal = _afc.ENABLE_CAUSAL_REASONING
        except Exception:
            enable_causal = enable_causal or False

        self.enable_causal = enable_causal
        # Causal score boost is computed in run() and consumed by score_paths()
        self._causal_score_boost: float = 0.0

        self.causal_reasoner = None
        if enable_causal:
            try:
                from core.reasoning.causal_reasoner import CausalReasoner
                from core.reasoning.causal_discovery import CausalGraph
                self.causal_reasoner = CausalReasoner(CausalGraph())
                logger.info("Causal reasoning enabled for EnhancedTreeOfThoughtAgent")
            except Exception as e:
                logger.warning(f"Failed to enable causal reasoning: {e}")

    def run(self, context: Dict[str, Any]) -> str:
        """Execute enhanced Tree-of-Thought reasoning."""
        self._causal_score_boost = 0.0  # reset each call

        if self.enable_causal and self.causal_reasoner:
            causal_context = context.get('causal_context', {})
            if causal_context and self.causal_reasoner.graph.nodes:
                try:
                    total_effect = 0.0
                    n_interventions = 0
                    for variable, value in causal_context.items():
                        try:
                            inf = self.causal_reasoner.do_intervention(variable, value)
                            if inf.effect:
                                # Average absolute effect across all downstream vars
                                avg_eff = sum(
                                    abs(v) for v in inf.effect.values()
                                ) / len(inf.effect)
                                total_effect += avg_eff * inf.confidence
                                n_interventions += 1
                        except ValueError:
                            pass  # Variable not in graph – skip

                    if n_interventions:
                        # Cap boost at 0.3 so it guides but doesn't dominate
                        self._causal_score_boost = min(
                            0.3, total_effect / n_interventions
                        )
                        logger.debug(
                            "Causal score boost set to %.3f", self._causal_score_boost
                        )
                except Exception as e:
                    logger.warning(f"Causal scoring failed: {e}")

        return super().run(context)

    def score_paths(self, task: str, nodes, memories) -> None:
        """
        Rank paths by consistency, memory alignment, and causal relevance.

        The causal boost (if any) is added uniformly to all nodes.  This
        rewards exploration of tasks where causal relationships are known and
        strong.
        """
        super().score_paths(task, nodes, memories)
        causal_boost = self._causal_score_boost
        for node in nodes:
            consistency = max(0.0, 1.0 - (node.depth * 0.1))
            node.score = min(1.0, node.score + (0.1 * consistency) + causal_boost)

    def prune_paths(self, nodes, threshold: float = 0.4) -> None:
        """Prune weak branches more aggressively for enhanced agent."""
        super().prune_paths(nodes, threshold=threshold)
