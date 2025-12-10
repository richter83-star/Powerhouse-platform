"""
Knowledge Graph: Symbolic knowledge representation and storage.

Stores entities, relationships, and rules in graph form for symbolic reasoning.
"""

import numpy as np
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Entity:
    """Represents an entity in the knowledge graph."""
    id: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None


@dataclass
class Relationship:
    """Represents a relationship between entities."""
    source_id: str
    target_id: str
    relation_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


class KnowledgeGraph:
    """
    Knowledge graph for storing symbolic knowledge.
    
    Stores entities (nodes) and relationships (edges) with types,
    properties, and optional embeddings for neural integration.
    """
    
    def __init__(self):
        """Initialize empty knowledge graph."""
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
        self.entity_types: Dict[str, Set[str]] = defaultdict(set)  # type -> set of entity IDs
        self.relation_types: Dict[str, List[int]] = defaultdict(list)  # relation_type -> list of relationship indices
        
        if NETWORKX_AVAILABLE:
            self.graph = nx.MultiDiGraph()
        else:
            self.graph = None
        
        self.logger = get_logger(__name__)
    
    def add_entity(self, entity: Entity) -> None:
        """Add or update an entity."""
        self.entities[entity.id] = entity
        self.entity_types[entity.type].add(entity.id)
        
        if self.graph is not None:
            self.graph.add_node(entity.id, **entity.properties, type=entity.type)
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self.entities.get(entity_id)
    
    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship between entities."""
        # Validate entities exist
        if relationship.source_id not in self.entities:
            raise ValueError(f"Source entity {relationship.source_id} not found")
        if relationship.target_id not in self.entities:
            raise ValueError(f"Target entity {relationship.target_id} not found")
        
        self.relationships.append(relationship)
        rel_index = len(self.relationships) - 1
        self.relation_types[relationship.relation_type].append(rel_index)
        
        if self.graph is not None:
            self.graph.add_edge(
                relationship.source_id,
                relationship.target_id,
                relation_type=relationship.relation_type,
                **relationship.properties,
                confidence=relationship.confidence
            )
    
    def query_entities(self, filters: Dict[str, Any]) -> List[Entity]:
        """
        Query entities matching filters.
        
        Args:
            filters: Dict with keys like "type", "property_name", etc.
            
        Returns:
            List of matching entities
        """
        results = []
        
        for entity in self.entities.values():
            match = True
            
            if "type" in filters and entity.type != filters["type"]:
                match = False
            
            if "properties" in filters:
                for prop_name, prop_value in filters["properties"].items():
                    if entity.properties.get(prop_name) != prop_value:
                        match = False
                        break
            
            if match:
                results.append(entity)
        
        return results
    
    def find_relationships(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[str] = None
    ) -> List[Relationship]:
        """
        Find relationships matching criteria.
        
        Args:
            source_id: Optional source entity ID
            target_id: Optional target entity ID
            relation_type: Optional relation type
            
        Returns:
            List of matching relationships
        """
        results = []
        
        for rel in self.relationships:
            match = True
            
            if source_id is not None and rel.source_id != source_id:
                match = False
            if target_id is not None and rel.target_id != target_id:
                match = False
            if relation_type is not None and rel.relation_type != relation_type:
                match = False
            
            if match:
                results.append(rel)
        
        return results
    
    def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[str] = None,
        direction: str = "outgoing"  # "outgoing", "incoming", "both"
    ) -> List[Tuple[Entity, Relationship]]:
        """
        Get neighboring entities and relationships.
        
        Args:
            entity_id: Entity ID
            relation_type: Optional filter by relation type
            direction: "outgoing", "incoming", or "both"
            
        Returns:
            List of (neighbor_entity, relationship) tuples
        """
        neighbors = []
        
        if direction in ("outgoing", "both"):
            for rel in self.relationships:
                if rel.source_id == entity_id:
                    if relation_type is None or rel.relation_type == relation_type:
                        target = self.get_entity(rel.target_id)
                        if target:
                            neighbors.append((target, rel))
        
        if direction in ("incoming", "both"):
            for rel in self.relationships:
                if rel.target_id == entity_id:
                    if relation_type is None or rel.relation_type == relation_type:
                        source = self.get_entity(rel.source_id)
                        if source:
                            neighbors.append((source, rel))
        
        return neighbors
    
    def infer_path(
        self,
        source_id: str,
        target_id: str,
        max_length: int = 3
    ) -> Optional[List[Relationship]]:
        """
        Find path between two entities (symbolic reasoning).
        
        Args:
            source_id: Source entity
            target_id: Target entity
            max_length: Maximum path length
            
        Returns:
            List of relationships forming path, or None if no path found
        """
        if self.graph is not None:
            try:
                # Use networkx shortest path if available
                path = nx.shortest_path(self.graph, source_id, target_id)
                if len(path) - 1 > max_length:
                    return None
                
                # Convert path to relationships
                relationships = []
                for i in range(len(path) - 1):
                    source = path[i]
                    target = path[i + 1]
                    edges = self.graph[source][target]
                    
                    # Get first relationship
                    for edge_key, edge_data in edges.items():
                        rel_type = edge_data.get("relation_type")
                        relationships.append(Relationship(
                            source_id=source,
                            target_id=target,
                            relation_type=rel_type,
                            properties=edge_data
                        ))
                        break  # Take first edge
                
                return relationships if len(relationships) == len(path) - 1 else None
                
            except (nx.NetworkXNoPath, KeyError):
                return None
        
        # Fallback: BFS search
        return self._bfs_path(source_id, target_id, max_length)
    
    def _bfs_path(self, source_id: str, target_id: str, max_length: int) -> Optional[List[Relationship]]:
        """BFS to find path between entities."""
        from collections import deque
        
        queue = deque([(source_id, [])])
        visited = {source_id}
        
        while queue:
            current, path = queue.popleft()
            
            if len(path) >= max_length:
                continue
            
            if current == target_id:
                return path
            
            # Explore outgoing relationships
            for rel in self.relationships:
                if rel.source_id == current and rel.target_id not in visited:
                    visited.add(rel.target_id)
                    queue.append((rel.target_id, path + [rel]))
        
        return None
    
    def set_entity_embedding(self, entity_id: str, embedding: np.ndarray) -> None:
        """Set neural embedding for an entity (for neural-symbolic bridge)."""
        if entity_id in self.entities:
            self.entities[entity_id].embedding = embedding
    
    def get_entities_by_similarity(
        self,
        query_embedding: np.ndarray,
        entity_type: Optional[str] = None,
        top_k: int = 10
    ) -> List[Tuple[Entity, float]]:
        """
        Find entities similar to query embedding (neural search).
        
        Args:
            query_embedding: Query vector
            entity_type: Optional filter by entity type
            top_k: Number of results to return
            
        Returns:
            List of (entity, similarity_score) tuples
        """
        candidates = list(self.entities.values())
        
        if entity_type:
            candidates = [e for e in candidates if e.type == entity_type]
        
        # Calculate similarities
        similarities = []
        for entity in candidates:
            if entity.embedding is not None:
                similarity = np.dot(query_embedding, entity.embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(entity.embedding) + 1e-8
                )
                similarities.append((entity, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def to_dict(self) -> Dict:
        """Export knowledge graph to dictionary."""
        return {
            "entities": [
                {
                    "id": e.id,
                    "type": e.type,
                    "properties": e.properties,
                    "has_embedding": e.embedding is not None
                }
                for e in self.entities.values()
            ],
            "relationships": [
                {
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "relation_type": r.relation_type,
                    "properties": r.properties,
                    "confidence": r.confidence
                }
                for r in self.relationships
            ]
        }

