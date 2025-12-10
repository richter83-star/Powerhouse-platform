"""
Causal Discovery: Learning causal structure from data.

Implements algorithms for discovering causal relationships from
observational and interventional data.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

try:
    from pgmpy.models import BayesianNetwork
    from pgmpy.estimators import PC, HillClimbSearch, BicScore
    PGMPY_AVAILABLE = True
except ImportError:
    PGMPY_AVAILABLE = False

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CausalGraph:
    """
    Represents a causal directed acyclic graph (DAG).
    
    Nodes represent variables, edges represent causal relationships.
    """
    nodes: Set[str] = field(default_factory=set)
    edges: Set[Tuple[str, str]] = field(default_factory=set)  # (parent, child)
    edge_weights: Dict[Tuple[str, str], float] = field(default_factory=dict)
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize networkx graph if available."""
        if NETWORKX_AVAILABLE:
            self.graph = nx.DiGraph()
            self.graph.add_nodes_from(self.nodes)
            self.graph.add_edges_from(self.edges)
        else:
            self.graph = None
    
    def add_edge(self, parent: str, child: str, weight: float = 1.0):
        """Add a causal edge from parent to child."""
        if parent not in self.nodes:
            self.nodes.add(parent)
        if child not in self.nodes:
            self.nodes.add(child)
        
        self.edges.add((parent, child))
        self.edge_weights[(parent, child)] = weight
        
        if self.graph is not None:
            self.graph.add_edge(parent, child, weight=weight)
    
    def get_parents(self, node: str) -> Set[str]:
        """Get all parent nodes (direct causes) of a node."""
        return {parent for parent, child in self.edges if child == node}
    
    def get_children(self, node: str) -> Set[str]:
        """Get all child nodes (direct effects) of a node."""
        return {child for parent, child in self.edges if parent == node}
    
    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """Check if ancestor is an ancestor of descendant."""
        if not self.graph:
            # Simple BFS if networkx not available
            visited = set()
            queue = [ancestor]
            while queue:
                node = queue.pop(0)
                if node == descendant:
                    return True
                if node not in visited:
                    visited.add(node)
                    queue.extend(self.get_children(node))
            return False
        
        try:
            return nx.has_path(self.graph, ancestor, descendant)
        except Exception:
            return False
    
    def to_dict(self) -> Dict:
        """Convert graph to dictionary representation."""
        return {
            "nodes": list(self.nodes),
            "edges": [{"parent": p, "child": c, "weight": self.edge_weights.get((p, c), 1.0)} 
                     for p, c in self.edges],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CausalGraph':
        """Create graph from dictionary representation."""
        graph = cls()
        graph.nodes = set(data.get("nodes", []))
        for edge in data.get("edges", []):
            graph.add_edge(edge["parent"], edge["child"], edge.get("weight", 1.0))
        graph.metadata = data.get("metadata", {})
        return graph


class CausalDiscovery:
    """
    Discovers causal structure from data using various algorithms.
    
    Supports:
    - PC algorithm (constraint-based)
    - GES (score-based)
    - Custom heuristics
    """
    
    def __init__(self, method: str = "pc", alpha: float = 0.05):
        """
        Initialize causal discovery.
        
        Args:
            method: Discovery method ("pc", "ges", "heuristic")
            alpha: Significance level for independence tests
        """
        self.method = method
        self.alpha = alpha
        self.logger = get_logger(__name__)
        
        if method == "pc" and not PGMPY_AVAILABLE:
            self.logger.warning("pgmpy not available, falling back to heuristic method")
            self.method = "heuristic"
    
    def discover(self, data: Dict[str, np.ndarray], variable_names: Optional[List[str]] = None) -> CausalGraph:
        """
        Discover causal graph from observational data.
        
        Args:
            data: Dictionary mapping variable names to numpy arrays
            variable_names: Optional list of variable names (if not provided, use dict keys)
            
        Returns:
            CausalGraph representing discovered causal structure
        """
        if variable_names is None:
            variable_names = list(data.keys())
        
        if len(variable_names) < 2:
            raise ValueError("Need at least 2 variables for causal discovery")
        
        if self.method == "pc" and PGMPY_AVAILABLE:
            return self._discover_pc(data, variable_names)
        elif self.method == "ges" and PGMPY_AVAILABLE:
            return self._discover_ges(data, variable_names)
        else:
            return self._discover_heuristic(data, variable_names)
    
    def _discover_pc(self, data: Dict[str, np.ndarray], variable_names: List[str]) -> CausalGraph:
        """Discover using PC algorithm (constraint-based)."""
        try:
            # Convert to pandas DataFrame for pgmpy
            import pandas as pd
            df = pd.DataFrame({var: data[var] for var in variable_names})
            
            # Run PC algorithm
            model = PC(df)
            estimated_model = model.estimate(return_type="dag")
            
            # Convert to CausalGraph
            graph = CausalGraph()
            graph.nodes = set(estimated_model.nodes())
            
            for edge in estimated_model.edges():
                graph.add_edge(edge[0], edge[1])
            
            graph.metadata = {
                "method": "pc",
                "alpha": self.alpha,
                "discovered_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"PC algorithm discovered {len(graph.edges)} edges")
            return graph
            
        except Exception as e:
            self.logger.warning(f"PC algorithm failed: {e}, falling back to heuristic")
            return self._discover_heuristic(data, variable_names)
    
    def _discover_ges(self, data: Dict[str, np.ndarray], variable_names: List[str]) -> CausalGraph:
        """Discover using GES algorithm (score-based)."""
        try:
            import pandas as pd
            df = pd.DataFrame({var: data[var] for var in variable_names})
            
            # Run GES (Greedy Equivalence Search)
            hc = HillClimbSearch(df)
            estimated_model = hc.estimate(scoring_method=BicScore(df))
            
            # Convert to CausalGraph
            graph = CausalGraph()
            graph.nodes = set(estimated_model.nodes())
            
            for edge in estimated_model.edges():
                graph.add_edge(edge[0], edge[1])
            
            graph.metadata = {
                "method": "ges",
                "discovered_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"GES algorithm discovered {len(graph.edges)} edges")
            return graph
            
        except Exception as e:
            self.logger.warning(f"GES algorithm failed: {e}, falling back to heuristic")
            return self._discover_heuristic(data, variable_names)
    
    def _discover_heuristic(self, data: Dict[str, np.ndarray], variable_names: List[str]) -> CausalGraph:
        """
        Heuristic causal discovery using correlation and partial correlation.
        
        This is a simplified method that doesn't require pgmpy.
        """
        graph = CausalGraph()
        graph.nodes = set(variable_names)
        
        # Compute correlation matrix
        n_vars = len(variable_names)
        correlations = np.zeros((n_vars, n_vars))
        
        for i, var1 in enumerate(variable_names):
            for j, var2 in enumerate(variable_names):
                if i != j:
                    corr = np.corrcoef(data[var1], data[var2])[0, 1]
                    correlations[i, j] = corr
        
        # Heuristic: if |correlation| > threshold and var1 has lower variance,
        # var1 might cause var2 (simplified assumption)
        threshold = 0.3  # Configurable threshold
        
        for i, var1 in enumerate(variable_names):
            for j, var2 in enumerate(variable_names):
                if i != j:
                    corr = abs(correlations[i, j])
                    if corr > threshold:
                        # Check variance (lower variance might indicate cause)
                        var1_var = np.var(data[var1])
                        var2_var = np.var(data[var2])
                        
                        if var1_var < var2_var * 1.2:  # Slight preference
                            graph.add_edge(var1, var2, weight=corr)
        
        graph.metadata = {
            "method": "heuristic",
            "threshold": threshold,
            "discovered_at": datetime.now().isoformat()
        }
        
        self.logger.info(f"Heuristic method discovered {len(graph.edges)} edges")
        return graph
    
    def discover_from_interventions(
        self,
        observational_data: Dict[str, np.ndarray],
        interventional_data: List[Tuple[str, Dict[str, np.ndarray]]],  # List of (intervened_var, data)
        variable_names: Optional[List[str]] = None
    ) -> CausalGraph:
        """
        Discover causal structure using both observational and interventional data.
        
        Args:
            observational_data: Data from observational studies
            interventional_data: List of (intervened_variable, data) tuples
            variable_names: Optional variable names
            
        Returns:
            CausalGraph with improved structure from interventions
        """
        # Start with observational discovery
        graph = self.discover(observational_data, variable_names)
        
        # Refine using interventional data
        # If intervening on X changes Y's distribution, X causes Y
        for intervened_var, intervention_data in interventional_data:
            if intervened_var not in graph.nodes:
                continue
            
            for var in graph.nodes:
                if var == intervened_var:
                    continue
                
                # Compare distributions
                obs_dist = observational_data.get(var)
                int_dist = intervention_data.get(var)
                
                if obs_dist is not None and int_dist is not None:
                    # Statistical test (simplified - could use Kolmogorov-Smirnov)
                    obs_mean = np.mean(obs_dist)
                    int_mean = np.mean(int_dist)
                    
                    if abs(obs_mean - int_mean) > np.std(obs_dist) * 0.5:
                        # Intervention had effect, add edge if not present
                        if not graph.is_ancestor(intervened_var, var):
                            graph.add_edge(intervened_var, var)
        
        graph.metadata["refined_with_interventions"] = True
        return graph

