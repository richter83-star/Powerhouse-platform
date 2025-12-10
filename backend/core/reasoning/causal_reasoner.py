"""
Causal Inference: Performs causal reasoning using discovered causal graphs.

Implements do-calculus, intervention analysis, and causal effect estimation.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
import logging

from core.reasoning.causal_discovery import CausalGraph
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CausalInference:
    """
    Result of a causal inference operation.
    """
    intervention: Dict[str, Any]  # do(X=x)
    effect: Dict[str, float]  # P(Y | do(X=x))
    confidence: float
    method: str
    metadata: Dict[str, Any]


class CausalReasoner:
    """
    Performs causal inference using causal graphs.
    
    Supports:
    - Do-calculus operations (P(Y | do(X=x)))
    - Intervention analysis
    - Causal effect estimation
    - Backdoor/frontdoor adjustment
    """
    
    def __init__(self, causal_graph: CausalGraph):
        """
        Initialize causal reasoner with a causal graph.
        
        Args:
            causal_graph: Discovered or known causal graph
        """
        self.graph = causal_graph
        self.logger = get_logger(__name__)
    
    def do_intervention(
        self,
        variable: str,
        value: Any,
        target_variables: Optional[List[str]] = None
    ) -> CausalInference:
        """
        Perform do-intervention: P(Y | do(X=x)).
        
        Args:
            variable: Variable to intervene on
            value: Value to set (or distribution)
            target_variables: Variables to estimate effect on (if None, all)
            
        Returns:
            CausalInference result
        """
        if variable not in self.graph.nodes:
            raise ValueError(f"Variable {variable} not in causal graph")
        
        if target_variables is None:
            # Default: all descendants of intervened variable
            target_variables = [
                node for node in self.graph.nodes
                if self.graph.is_ancestor(variable, node) or node == variable
            ]
        
        # Simplified effect estimation
        # In practice, this would use more sophisticated methods
        effects = {}
        
        for target in target_variables:
            if target == variable:
                effects[target] = value if isinstance(value, (int, float)) else 1.0
            elif self.graph.is_ancestor(variable, target):
                # Estimate effect (simplified - would use actual data/models)
                path_strength = self._estimate_path_strength(variable, target)
                effects[target] = path_strength
            else:
                effects[target] = 0.0  # No causal effect
        
        return CausalInference(
            intervention={variable: value},
            effect=effects,
            confidence=0.7,  # Simplified
            method="do_calculus",
            metadata={
                "graph_nodes": list(self.graph.nodes),
                "graph_edges": list(self.graph.edges),
                "computed_at": datetime.now().isoformat()
            }
        )
    
    def estimate_causal_effect(
        self,
        treatment: str,
        outcome: str,
        confounders: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Estimate average causal effect: E[Y | do(X=1)] - E[Y | do(X=0)].
        
        Args:
            treatment: Treatment variable X
            outcome: Outcome variable Y
            confounders: Optional confounders to adjust for
            
        Returns:
            Dictionary with effect estimate and confidence
        """
        if treatment not in self.graph.nodes or outcome not in self.graph.nodes:
            raise ValueError("Treatment or outcome not in causal graph")
        
        # Check if there's a causal path
        if not self.graph.is_ancestor(treatment, outcome):
            return {
                "effect": 0.0,
                "confidence": 0.0,
                "interpretation": "No causal path from treatment to outcome"
            }
        
        # Find backdoor paths (confounders)
        if confounders is None:
            confounders = self._find_backdoor_paths(treatment, outcome)
        
        # Estimate effect (simplified)
        # In practice, would use propensity scores, instrumental variables, etc.
        path_strength = self._estimate_path_strength(treatment, outcome)
        
        return {
            "effect": path_strength,
            "confidence": 0.75,
            "confounders": confounders,
            "interpretation": f"Intervening on {treatment} affects {outcome}"
        }
    
    def _estimate_path_strength(self, source: str, target: str) -> float:
        """
        Estimate strength of causal path from source to target.
        
        Simplified implementation - would use actual data in production.
        """
        if source == target:
            return 1.0
        
        # Simple path-based estimation
        paths = self._find_all_paths(source, target)
        if not paths:
            return 0.0
        
        # Weight by edge weights along path
        total_strength = 0.0
        for path in paths:
            path_strength = 1.0
            for i in range(len(path) - 1):
                edge_weight = self.graph.edge_weights.get((path[i], path[i+1]), 1.0)
                path_strength *= edge_weight
            total_strength += path_strength
        
        # Average over paths
        return total_strength / len(paths) if paths else 0.0
    
    def _find_all_paths(self, source: str, target: str, max_length: int = 10) -> List[List[str]]:
        """Find all directed paths from source to target."""
        paths = []
        
        def dfs(current: str, path: List[str], visited: Set[str]):
            if len(path) > max_length:
                return
            
            if current == target and len(path) > 1:
                paths.append(path.copy())
                return
            
            children = self.graph.get_children(current)
            for child in children:
                if child not in visited:
                    visited.add(child)
                    path.append(child)
                    dfs(child, path, visited)
                    path.pop()
                    visited.remove(child)
        
        dfs(source, [source], {source})
        return paths
    
    def _find_backdoor_paths(self, treatment: str, outcome: str) -> List[str]:
        """
        Find confounders (variables that create backdoor paths).
        
        Backdoor path: treatment <- confounder -> outcome
        """
        confounders = []
        
        treatment_parents = self.graph.get_parents(treatment)
        outcome_parents = self.graph.get_parents(outcome)
        
        # Common causes (confounders)
        confounders = list(treatment_parents & outcome_parents)
        
        return confounders
    
    def identify_causal_effect(
        self,
        treatment: str,
        outcome: str
    ) -> Dict[str, Any]:
        """
        Check if causal effect is identifiable using do-calculus rules.
        
        Returns identification strategy (adjustment set, instrumental variable, etc.)
        """
        # Check for backdoor criterion
        backdoor_set = self._find_backdoor_paths(treatment, outcome)
        
        if backdoor_set:
            return {
                "identifiable": True,
                "method": "backdoor_adjustment",
                "adjustment_set": backdoor_set,
                "formula": f"P(Y|do(X)) = Σ_{{z}} P(Y|X,Z) P(Z)"
            }
        
        # Check for frontdoor criterion (simplified)
        frontdoor_set = self._find_frontdoor_set(treatment, outcome)
        if frontdoor_set:
            return {
                "identifiable": True,
                "method": "frontdoor_adjustment",
                "frontdoor_set": frontdoor_set
            }
        
        # Check if direct path exists
        if (treatment, outcome) in self.graph.edges:
            return {
                "identifiable": True,
                "method": "direct_effect",
                "direct": True
            }
        
        return {
            "identifiable": False,
            "reason": "Cannot identify causal effect with available information"
        }
    
    def _find_frontdoor_set(self, treatment: str, outcome: str) -> Optional[List[str]]:
        """
        Find frontdoor set (mediator variables).
        
        Frontdoor path: treatment -> mediator -> outcome
        """
        # Find variables on directed path from treatment to outcome
        mediators = []
        
        children = self.graph.get_children(treatment)
        for child in children:
            if self.graph.is_ancestor(child, outcome):
                mediators.append(child)
        
        return mediators if mediators else None

