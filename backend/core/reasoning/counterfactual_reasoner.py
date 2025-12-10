"""
Counterfactual Reasoning: "What if" scenario analysis.

Generates and evaluates counterfactual scenarios - what would have
happened if things were different.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

from core.reasoning.causal_discovery import CausalGraph
from core.reasoning.causal_reasoner import CausalReasoner
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CounterfactualScenario:
    """
    Represents a counterfactual "what if" scenario.
    """
    factual_state: Dict[str, Any]  # What actually happened
    counterfactual_intervention: Dict[str, Any]  # What we change
    predicted_outcome: Dict[str, Any]  # What would have happened
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)


class CounterfactualReasoner:
    """
    Generates and evaluates counterfactual scenarios.
    
    Answers questions like:
    - "What if we had done X instead of Y?"
    - "What would have happened if variable Z was different?"
    """
    
    def __init__(self, causal_graph: CausalGraph, causal_reasoner: Optional[CausalReasoner] = None):
        """
        Initialize counterfactual reasoner.
        
        Args:
            causal_graph: Causal graph for reasoning
            causal_reasoner: Optional causal reasoner instance
        """
        self.graph = causal_graph
        self.causal_reasoner = causal_reasoner or CausalReasoner(causal_graph)
        self.logger = get_logger(__name__)
    
    def generate_counterfactual(
        self,
        factual_state: Dict[str, Any],
        intervention: Dict[str, Any],
        target_variables: Optional[List[str]] = None
    ) -> CounterfactualScenario:
        """
        Generate a counterfactual scenario.
        
        Args:
            factual_state: Observed state (what actually happened)
            intervention: What we change (counterfactual intervention)
            target_variables: Variables to predict (if None, all affected)
            
        Returns:
            CounterfactualScenario with predicted outcome
        """
        # Validate intervention variables are in graph
        for var in intervention.keys():
            if var not in self.graph.nodes:
                raise ValueError(f"Variable {var} not in causal graph")
        
        # Use causal reasoning to predict counterfactual outcome
        predicted_outcome = {}
        
        for intervened_var, intervened_value in intervention.items():
            # Perform do-intervention
            inference = self.causal_reasoner.do_intervention(
                intervened_var,
                intervened_value,
                target_variables
            )
            
            # Update predicted outcome
            for target, effect in inference.effect.items():
                if target not in predicted_outcome:
                    predicted_outcome[target] = {}
                predicted_outcome[target][intervened_var] = effect
        
        # Aggregate effects (simplified)
        aggregated_outcome = {}
        for target in predicted_outcome.keys():
            # Take mean of effects if multiple interventions affect same variable
            effects = list(predicted_outcome[target].values())
            aggregated_outcome[target] = np.mean(effects) if effects else factual_state.get(target, 0.0)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(factual_state, intervention, aggregated_outcome)
        
        # Calculate confidence
        confidence = self._calculate_confidence(intervention, aggregated_outcome)
        
        return CounterfactualScenario(
            factual_state=factual_state,
            counterfactual_intervention=intervention,
            predicted_outcome=aggregated_outcome,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def compare_scenarios(
        self,
        factual_state: Dict[str, Any],
        interventions: List[Dict[str, Any]],
        target_variable: str
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Compare multiple counterfactual scenarios.
        
        Args:
            factual_state: Baseline state
            interventions: List of different interventions to compare
            target_variable: Variable to compare across scenarios
            
        Returns:
            List of (intervention, effect_on_target) tuples, sorted by effect
        """
        results = []
        
        for intervention in interventions:
            scenario = self.generate_counterfactual(
                factual_state,
                intervention,
                target_variables=[target_variable]
            )
            
            effect = scenario.predicted_outcome.get(target_variable, 0.0)
            baseline = factual_state.get(target_variable, 0.0)
            effect_size = effect - baseline
            
            results.append((intervention, effect_size))
        
        # Sort by effect size (largest first)
        results.sort(key=lambda x: abs(x[1]), reverse=True)
        return results
    
    def find_minimal_intervention(
        self,
        factual_state: Dict[str, Any],
        target_variable: str,
        desired_value: float,
        candidate_variables: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find minimal intervention to achieve desired outcome.
        
        Args:
            factual_state: Current state
            target_variable: Variable we want to change
            desired_value: Desired value for target variable
            candidate_variables: Variables we can intervene on (if None, all)
            
        Returns:
            Minimal intervention dict, or None if not achievable
        """
        if candidate_variables is None:
            candidate_variables = [
                node for node in self.graph.nodes
                if self.graph.is_ancestor(node, target_variable)
            ]
        
        if not candidate_variables:
            return None
        
        current_value = factual_state.get(target_variable, 0.0)
        needed_change = desired_value - current_value
        
        # Try interventions on each candidate variable
        best_intervention = None
        best_error = float('inf')
        
        for candidate in candidate_variables:
            # Estimate required intervention value (simplified)
            # In practice, would use optimization or search
            candidate_value = factual_state.get(candidate, 0.0)
            
            # Estimate effect per unit change
            inference = self.causal_reasoner.estimate_causal_effect(candidate, target_variable)
            effect_per_unit = inference.get("effect", 0.0)
            
            if abs(effect_per_unit) < 1e-6:
                continue  # No causal effect
            
            # Estimate required intervention
            required_change = needed_change / effect_per_unit
            intervention_value = candidate_value + required_change
            
            # Generate counterfactual
            intervention = {candidate: intervention_value}
            scenario = self.generate_counterfactual(
                factual_state,
                intervention,
                target_variables=[target_variable]
            )
            
            predicted_value = scenario.predicted_outcome.get(target_variable, current_value)
            error = abs(predicted_value - desired_value)
            
            if error < best_error:
                best_error = error
                best_intervention = intervention
        
        if best_error < abs(needed_change) * 0.1:  # Within 10% of desired
            return best_intervention
        
        return None
    
    def explain_counterfactual(
        self,
        scenario: CounterfactualScenario
    ) -> str:
        """
        Generate human-readable explanation of counterfactual scenario.
        
        Args:
            scenario: Counterfactual scenario to explain
            
        Returns:
            Natural language explanation
        """
        intervention_desc = ", ".join([
            f"{var}={value}" for var, value in scenario.counterfactual_intervention.items()
        ])
        
        outcome_changes = []
        for var, new_value in scenario.predicted_outcome.items():
            old_value = scenario.factual_state.get(var)
            if old_value is not None and abs(new_value - old_value) > 1e-6:
                change = new_value - old_value
                outcome_changes.append(f"{var} would change by {change:.2f}")
        
        explanation = f"""
Counterfactual Analysis:

Factual State: {scenario.factual_state}
Intervention: If we had {intervention_desc} instead,
Predicted Outcome: {scenario.predicted_outcome}

Key Changes: {", ".join(outcome_changes) if outcome_changes else "Minimal changes"}
Confidence: {scenario.confidence:.2%}

Reasoning: {scenario.reasoning}
        """.strip()
        
        return explanation
    
    def _generate_reasoning(
        self,
        factual_state: Dict[str, Any],
        intervention: Dict[str, Any],
        predicted_outcome: Dict[str, Any]
    ) -> str:
        """Generate reasoning explanation for counterfactual."""
        reasoning_parts = []
        
        for intervened_var, intervened_value in intervention.items():
            factual_value = factual_state.get(intervened_var)
            if factual_value is not None:
                reasoning_parts.append(
                    f"Changed {intervened_var} from {factual_value:.2f} to {intervened_value:.2f}"
                )
        
        affected_vars = []
        for var, new_value in predicted_outcome.items():
            old_value = factual_state.get(var)
            if old_value is not None and abs(new_value - old_value) > 1e-6:
                affected_vars.append(var)
        
        if affected_vars:
            reasoning_parts.append(f"This affects: {', '.join(affected_vars)}")
        
        return ". ".join(reasoning_parts) if reasoning_parts else "No significant changes predicted."
    
    def _calculate_confidence(
        self,
        intervention: Dict[str, Any],
        predicted_outcome: Dict[str, Any]
    ) -> float:
        """Calculate confidence in counterfactual prediction."""
        # Simplified confidence calculation
        # In practice, would consider:
        # - Strength of causal relationships
        # - Data quality
        # - Model uncertainty
        
        base_confidence = 0.7
        
        # Adjust based on number of interventions (more = less certain)
        num_interventions = len(intervention)
        if num_interventions > 1:
            base_confidence *= 0.9 ** (num_interventions - 1)
        
        # Adjust based on path strength (if available)
        # Would use actual causal effect estimates
        
        return min(1.0, max(0.0, base_confidence))

