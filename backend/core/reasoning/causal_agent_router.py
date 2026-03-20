"""
Causal Agent Router: Routes tasks to agents informed by causal inference.

This module bridges the gap between CausalReasoner (do-calculus) and
NeuralAgentSelector so that high-confidence causal recommendations influence
which agent is chosen to execute a task.

Pipeline:
    task → CausalReasoner.do_intervention() → CausalInterventionRecommendation
    → CausalAgentRouter.select_agent() → NeuralAgentSelector (with causal context)
    → best_agent_name

The router can also be used standalone: pass a pre-computed causal context dict
directly to select_agent() if you already have recommendations.

Routing rule:
    If a causal recommendation has confidence >= CONFIDENCE_THRESHOLD (default 0.7)
    the selector receives a context hint that boosts agents matching the
    intervention domain (parameter_tuning, reasoning, analysis, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.learning.neural_agent_selector import NeuralAgentSelector
from core.reasoning.causal_reasoner import CausalInference, CausalReasoner
from utils.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLD = 0.7


@dataclass
class CausalInterventionRecommendation:
    """
    Actionable recommendation derived from a CausalInference result.

    The router uses ``domain`` and ``confidence`` to weight agent selection.
    """

    variable: str                   # Intervened variable (e.g. "temperature")
    intervention_value: Any         # Target value
    predicted_effect: float         # Expected magnitude of effect (0-1)
    confidence: float               # Confidence in the causal estimate (0-1)
    domain: str = "general"         # Closest agent domain (see DOMAIN_KEYWORDS)
    causal_inference: Optional[CausalInference] = None  # Raw result for audit

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence >= CONFIDENCE_THRESHOLD


# Domain → keywords that hint which agents are preferred.
# Extend as new agent specialisations are added.
DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "parameter_tuning": ["parameter", "tuning", "optimizer", "calibrat"],
    "reasoning": ["reason", "logic", "causal", "infer", "deduc"],
    "analysis": ["analys", "evaluat", "assess", "review"],
    "planning": ["plan", "schedul", "strateg", "orchestrat"],
    "generation": ["generat", "synth", "creat", "writ"],
}


def _infer_domain(variable: str, inference: CausalInference) -> str:
    """Map a causal variable name to the closest agent domain."""
    combined = variable.lower() + " " + str(inference.metadata)
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            return domain
    return "general"


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

class CausalAgentRouter:
    """
    Routes tasks to the best agent by combining causal recommendations with
    the neural agent selector's learned scores.

    Usage::

        router = CausalAgentRouter(
            causal_reasoner=my_reasoner,
            agent_selector=my_selector,
        )

        # Full pipeline – reasoner runs automatically:
        agent_name, recs = router.route(
            task="Optimise generation quality",
            intervention_variable="temperature",
            intervention_value=0.9,
            agent_histories={"agent_a": {...}, "agent_b": {...}},
        )

        # Or supply pre-computed causal context:
        agent_name, recs = router.select_agent(
            task="...",
            causal_context={"temperature": my_recommendation},
            agent_histories=...,
        )
    """

    def __init__(
        self,
        causal_reasoner: Optional[CausalReasoner] = None,
        agent_selector: Optional[NeuralAgentSelector] = None,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        causal_boost: float = 0.3,
    ) -> None:
        """
        Args:
            causal_reasoner: CausalReasoner instance.  May be None if you
                always supply a pre-computed causal context.
            agent_selector: NeuralAgentSelector instance.  Created with
                default settings if not provided.
            confidence_threshold: Minimum confidence for a recommendation to
                influence routing.
            causal_boost: Additive score boost applied to agents that match a
                high-confidence causal recommendation.
        """
        self.causal_reasoner = causal_reasoner
        self.agent_selector = agent_selector or NeuralAgentSelector()
        self.confidence_threshold = confidence_threshold
        self.causal_boost = causal_boost

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_recommendation(
        self,
        variable: str,
        value: Any,
        target_variables: Optional[List[str]] = None,
    ) -> CausalInterventionRecommendation:
        """
        Run the causal reasoner and return an actionable recommendation.

        Raises:
            RuntimeError: if no CausalReasoner was provided at construction.
        """
        if self.causal_reasoner is None:
            raise RuntimeError(
                "CausalAgentRouter was created without a CausalReasoner.  "
                "Pass a reasoner at construction or use select_agent() with "
                "a pre-computed causal_context."
            )

        inference: CausalInference = self.causal_reasoner.do_intervention(
            variable=variable,
            value=value,
            target_variables=target_variables,
        )

        # Predicted effect = mean absolute effect across targets
        effects = list(inference.effect.values())
        predicted_effect = sum(abs(e) for e in effects) / len(effects) if effects else 0.0
        domain = _infer_domain(variable, inference)

        return CausalInterventionRecommendation(
            variable=variable,
            intervention_value=value,
            predicted_effect=predicted_effect,
            confidence=inference.confidence,
            domain=domain,
            causal_inference=inference,
        )

    def route(
        self,
        task: str,
        intervention_variable: str,
        intervention_value: Any,
        agent_histories: Optional[Dict[str, Dict[str, Any]]] = None,
        task_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        target_variables: Optional[List[str]] = None,
    ) -> Tuple[Optional[str], Dict[str, CausalInterventionRecommendation]]:
        """
        Full pipeline: causal analysis → agent selection.

        Returns:
            (best_agent_name, causal_context_dict)
        """
        recommendation = self.build_recommendation(
            variable=intervention_variable,
            value=intervention_value,
            target_variables=target_variables,
        )
        causal_context = {intervention_variable: recommendation}

        best_agent = self.select_agent(
            task=task,
            causal_context=causal_context,
            agent_histories=agent_histories,
            task_type=task_type,
            context=context,
        )
        return best_agent, causal_context

    def select_agent(
        self,
        task: str,
        causal_context: Optional[Dict[str, CausalInterventionRecommendation]] = None,
        agent_histories: Optional[Dict[str, Dict[str, Any]]] = None,
        task_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Select the best agent, optionally boosted by causal recommendations.

        If a causal recommendation has confidence >= threshold, agents whose
        name contains a keyword associated with the recommendation's domain
        receive a score boost.

        Args:
            task: Task description.
            causal_context: Map of variable → CausalInterventionRecommendation.
            agent_histories: Per-agent performance history.
            task_type: Optional task type hint for the neural selector.
            context: Execution context forwarded to neural selector.

        Returns:
            Name of the selected agent, or None if no agents are available.
        """
        if not agent_histories:
            logger.warning("No agent histories provided – cannot select agent")
            return None

        # --- Base scores from neural selector ---
        context_enriched = dict(context or {})

        # Inject causal context summary into context dict so NeuralAgentSelector
        # can access it via context.get("causal_hints", {})
        high_conf_recs = {
            var: rec
            for var, rec in (causal_context or {}).items()
            if rec.is_high_confidence
        }
        if high_conf_recs:
            context_enriched["causal_hints"] = {
                var: {
                    "domain": rec.domain,
                    "confidence": rec.confidence,
                    "predicted_effect": rec.predicted_effect,
                }
                for var, rec in high_conf_recs.items()
            }
            logger.debug(
                "Injecting %d high-confidence causal hints into selector context",
                len(high_conf_recs),
            )

        scores: List[Tuple[str, float]] = self.agent_selector.predict_agent_scores(
            task=task,
            task_type=task_type,
            context=context_enriched,
            agent_histories=agent_histories,
        )

        if not scores:
            return None

        # --- Apply causal boost ---
        if high_conf_recs:
            scores = self._apply_causal_boost(scores, high_conf_recs)

        best_agent, best_score = scores[0]
        logger.info(
            "CausalAgentRouter selected '%s' (score=%.3f, causal_hints=%d)",
            best_agent,
            best_score,
            len(high_conf_recs),
        )
        try:
            from core.monitoring.metrics import causal_routing_total
            # Derive a domain label from the winning causal recommendation if any
            domain_label = "none"
            if high_conf_recs:
                domain_label = next(iter(high_conf_recs.values())).domain or "none"
            causal_routing_total.labels(
                domain=domain_label,
                context_used="true" if high_conf_recs else "false",
            ).inc()
        except Exception:
            pass
        return best_agent

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_causal_boost(
        self,
        scores: List[Tuple[str, float]],
        high_conf_recs: Dict[str, CausalInterventionRecommendation],
    ) -> List[Tuple[str, float]]:
        """
        Boost scores for agents whose names match a high-confidence domain.
        """
        domain_keywords_flat: Dict[str, List[str]] = {}
        for rec in high_conf_recs.values():
            domain_keywords_flat[rec.domain] = DOMAIN_KEYWORDS.get(
                rec.domain, []
            )

        boosted: List[Tuple[str, float]] = []
        for agent_name, score in scores:
            bonus = 0.0
            for rec in high_conf_recs.values():
                keywords = DOMAIN_KEYWORDS.get(rec.domain, [])
                if any(kw in agent_name.lower() for kw in keywords):
                    bonus += self.causal_boost * rec.confidence
            boosted.append((agent_name, score + bonus))

        boosted.sort(key=lambda x: x[1], reverse=True)
        return boosted

    def get_statistics(self) -> Dict[str, Any]:
        """Return selector metadata for monitoring."""
        return {
            "confidence_threshold": self.confidence_threshold,
            "causal_boost": self.causal_boost,
            "selector": self.agent_selector.to_dict(),
        }
