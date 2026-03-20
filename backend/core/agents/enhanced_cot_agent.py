"""
Enhanced Chain-of-Thought Agent with Advanced Capabilities.

Auto-configures causal and neurosymbolic features from AdvancedFeaturesConfig.
Both flags can be overridden explicitly at construction time.
"""

from typing import Any, Dict, Optional
from agents.chain_of_thought import Agent as BaseCoTAgent
from utils.logging import get_logger

logger = get_logger(__name__)


class EnhancedChainOfThoughtAgent(BaseCoTAgent):
    """
    Enhanced Chain-of-Thought agent with causal and neurosymbolic reasoning.

    Causal reasoning enriches the context with cause-effect hints before the
    chain-of-thought loop starts.  Neurosymbolic constraints are registered in
    the knowledge graph so they can be applied during each reasoning step.
    """

    CAPABILITIES = ["reasoning", "analysis", "causal", "neurosymbolic"]

    def __init__(
        self,
        enable_causal: Optional[bool] = None,
        enable_neurosymbolic: Optional[bool] = None,
    ):
        """
        Initialize enhanced CoT agent.

        Args:
            enable_causal: Enable causal reasoning.  Defaults to
                ``AdvancedFeaturesConfig.ENABLE_CAUSAL_REASONING``.
            enable_neurosymbolic: Enable neurosymbolic reasoning.  Defaults to
                ``AdvancedFeaturesConfig.ENABLE_NEUROSYMBOLIC``.
        """
        super().__init__()

        # Auto-configure from advanced_features_config when flag not explicit
        try:
            from config.advanced_features_config import advanced_features_config as _afc
            if enable_causal is None:
                enable_causal = _afc.ENABLE_CAUSAL_REASONING
            if enable_neurosymbolic is None:
                enable_neurosymbolic = _afc.ENABLE_NEUROSYMBOLIC
        except Exception:
            enable_causal = enable_causal or False
            enable_neurosymbolic = enable_neurosymbolic or False

        self.enable_causal = enable_causal
        self.enable_neurosymbolic = enable_neurosymbolic

        self.causal_reasoner = None
        self.neurosymbolic_reasoner = None

        if enable_causal:
            try:
                from core.reasoning.causal_reasoner import CausalReasoner
                from core.reasoning.causal_discovery import CausalGraph
                self.causal_reasoner = CausalReasoner(CausalGraph())
                logger.info("Causal reasoning enabled for EnhancedChainOfThoughtAgent")
            except Exception as e:
                logger.warning(f"Failed to enable causal reasoning: {e}")

        if enable_neurosymbolic:
            try:
                from core.reasoning.neurosymbolic import NeurosymbolicReasoner
                self.neurosymbolic_reasoner = NeurosymbolicReasoner()
                logger.info(
                    "Neurosymbolic reasoning enabled for EnhancedChainOfThoughtAgent"
                )
            except Exception as e:
                logger.warning(f"Failed to enable neurosymbolic reasoning: {e}")

    def run(self, context: Dict[str, Any]) -> str:
        """Execute enhanced Chain-of-Thought reasoning."""
        task = context.get('task', '')
        context = dict(context)  # shallow copy so we don't mutate the caller's dict

        # Pre-step A: Enrich context with causal cause-effect hints
        if self.enable_causal and self.causal_reasoner:
            try:
                # Extract candidate variables: capitalised words of length > 3
                words = [
                    w.strip('.,!?;:')
                    for w in task.split()
                    if len(w.strip('.,!?;:')) > 3 and w[0].isupper()
                ]
                if len(words) >= 2 and self.causal_reasoner.graph.nodes:
                    treatment, outcome = words[0], words[-1]
                    try:
                        effect = self.causal_reasoner.estimate_causal_effect(
                            treatment, outcome
                        )
                        if effect.get("confidence", 0) > 0.4:
                            context["causal_hint"] = {
                                "treatment": treatment,
                                "outcome": outcome,
                                "effect": effect,
                            }
                            logger.debug(
                                "Causal hint injected: %s → %s (confidence=%.2f)",
                                treatment,
                                outcome,
                                effect["confidence"],
                            )
                    except (ValueError, KeyError):
                        pass  # Variables not in graph – skip
            except Exception as e:
                logger.warning(f"Causal context enrichment failed: {e}")

        # Pre-step B: Register symbolic constraints so the reasoning respects them
        if self.enable_neurosymbolic and self.neurosymbolic_reasoner:
            constraints = context.get('constraints', [])
            if constraints:
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
                                        "confidence": 1.0,
                                    }],
                                )
                    inference = self.neurosymbolic_reasoner.reason(
                        apply_constraints=True
                    )
                    if inference.confidence > 0:
                        context["constraint_inference"] = inference.reasoning
                        logger.debug(
                            "Neurosymbolic constraints registered, confidence=%.2f",
                            inference.confidence,
                        )
                except Exception as e:
                    logger.warning(f"Neurosymbolic reasoning failed: {e}")

        # Run base CoT with enriched context
        return super().run(context)
