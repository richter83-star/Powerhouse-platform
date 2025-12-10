"""
Neurosymbolic Integration: Combines neural and symbolic reasoning.

Main interface for hybrid neural-symbolic AI systems.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from core.reasoning.knowledge_graph import KnowledgeGraph, Entity, Relationship
from core.reasoning.logical_reasoner import LogicalReasoner, Fact, Rule
from core.reasoning.neural_symbolic_bridge import NeuralSymbolicBridge, HybridInference
from utils.logging import get_logger

logger = get_logger(__name__)


class NeurosymbolicReasoner:
    """
    Main interface for neurosymbolic reasoning.
    
    Combines:
    - Neural networks for pattern recognition and learning
    - Knowledge graphs for explicit knowledge
    - Logical reasoning for constraint satisfaction
    - Bridge for seamless integration
    """
    
    def __init__(self, embedding_dim: int = 128):
        """
        Initialize neurosymbolic reasoner.
        
        Args:
            embedding_dim: Dimension for neural embeddings
        """
        self.kg = KnowledgeGraph()
        self.logical_reasoner = LogicalReasoner()
        self.bridge = NeuralSymbolicBridge(self.kg, self.logical_reasoner, embedding_dim)
        self.logger = get_logger(__name__)
    
    def add_knowledge(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        rules: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Add knowledge to the system.
        
        Args:
            entities: List of entity dicts with 'id', 'type', 'properties'
            relationships: List of relationship dicts with 'source', 'target', 'type'
            rules: Optional list of rule dicts
        """
        # Add entities
        for ent_data in entities:
            entity = Entity(
                id=ent_data["id"],
                type=ent_data.get("type", "entity"),
                properties=ent_data.get("properties", {})
            )
            if "embedding" in ent_data:
                entity.embedding = ent_data["embedding"]
            self.kg.add_entity(entity)
        
        # Add relationships
        for rel_data in relationships:
            rel = Relationship(
                source_id=rel_data["source"],
                target_id=rel_data["target"],
                relation_type=rel_data["type"],
                properties=rel_data.get("properties", {}),
                confidence=rel_data.get("confidence", 1.0)
            )
            self.kg.add_relationship(rel)
        
        # Add rules
        if rules:
            for rule_data in rules:
                head = Fact(
                    predicate=rule_data["head"]["predicate"],
                    arguments=rule_data["head"]["arguments"]
                )
                body = [
                    Fact(
                        predicate=premise["predicate"],
                        arguments=premise["arguments"]
                    )
                    for premise in rule_data["body"]
                ]
                rule = Rule(
                    head=head,
                    body=body,
                    name=rule_data.get("name"),
                    priority=rule_data.get("priority", 1.0)
                )
                self.logical_reasoner.add_rule(rule)
        
        self.logger.info(f"Added {len(entities)} entities, {len(relationships)} relationships, "
                        f"{len(rules) if rules else 0} rules")
    
    def reason(
        self,
        neural_inputs: Optional[Dict[str, Any]] = None,
        symbolic_query: Optional[str] = None,
        apply_constraints: bool = True
    ) -> HybridInference:
        """
        Perform hybrid neural-symbolic reasoning.
        
        Args:
            neural_inputs: Optional neural network inputs/predictions
            symbolic_query: Optional symbolic query string
            apply_constraints: Whether to apply symbolic constraints
            
        Returns:
            HybridInference result
        """
        # If neural inputs provided, use hybrid inference
        if neural_inputs:
            neural_preds = neural_inputs if isinstance(neural_inputs, dict) else {}
            return self.bridge.hybrid_inference(neural_preds, symbolic_query)
        
        # If only symbolic query, use logical reasoning
        if symbolic_query:
            # Parse and answer query symbolically
            # Simplified - would have proper query parser
            pass
        
        # Default: return empty inference
        return HybridInference(
            neural_prediction={},
            symbolic_constraint={},
            combined_result={},
            confidence=0.0,
            reasoning="No inputs provided"
        )
    
    def query_kg(self, query: str, **kwargs) -> List[Entity]:
        """
        Query knowledge graph (symbolic search).
        
        Args:
            query: Query string (simplified format)
            **kwargs: Additional filters
            
        Returns:
            List of matching entities
        """
        # Simplified query parsing
        # In practice, would have proper query language
        filters = {}
        if "type" in kwargs:
            filters["type"] = kwargs["type"]
        if "properties" in kwargs:
            filters["properties"] = kwargs["properties"]
        
        return self.kg.query_entities(filters)
    
    def search_by_embedding(
        self,
        embedding: Any,  # np.ndarray or similar
        entity_type: Optional[str] = None,
        top_k: int = 10
    ) -> List[tuple]:
        """
        Search knowledge graph using neural embedding (neural search).
        
        Args:
            embedding: Embedding vector
            entity_type: Optional filter by entity type
            top_k: Number of results
            
        Returns:
            List of (entity, similarity) tuples
        """
        if not isinstance(embedding, np.ndarray):
            import numpy as np
            embedding = np.array(embedding)
        
        return self.kg.get_entities_by_similarity(embedding, entity_type, top_k)
    
    def infer_logical_consequences(self) -> None:
        """Run forward chaining to infer new facts."""
        self.logical_reasoner.forward_chain()
    
    def check_consistency(self, context: Dict[str, Any]) -> Dict[str, bool]:
        """
        Check logical consistency of context.
        
        Args:
            context: Context to check
            
        Returns:
            Dict mapping constraint descriptions to satisfaction status
        """
        results = self.logical_reasoner.check_constraints(context)
        return {constraint.description: satisfied for constraint, satisfied in results}

