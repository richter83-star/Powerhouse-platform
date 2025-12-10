"""
External Memory: Differentiable external memory bank for MANN.

Implements key-value memory with attention-based read/write mechanisms.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MemorySlot:
    """Represents a single memory slot."""
    key: np.ndarray  # Key vector
    value: np.ndarray  # Value vector
    usage_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)


class ExternalMemoryBank:
    """
    External differentiable memory bank.
    
    Stores key-value pairs that can be read/written using attention mechanisms.
    """
    
    def __init__(self, memory_size: int = 128, key_dim: int = 64, value_dim: int = 128):
        """
        Initialize memory bank.
        
        Args:
            memory_size: Number of memory slots
            key_dim: Dimension of key vectors
            value_dim: Dimension of value vectors
        """
        self.memory_size = memory_size
        self.key_dim = key_dim
        self.value_dim = value_dim
        
        # Initialize memory slots
        self.slots: List[MemorySlot] = []
        for i in range(memory_size):
            # Random initialization
            key = np.random.randn(key_dim).astype(np.float32)
            key = key / (np.linalg.norm(key) + 1e-8)
            value = np.zeros(value_dim, dtype=np.float32)
            
            self.slots.append(MemorySlot(key=key, value=value))
        
        self.logger = get_logger(__name__)
    
    def read(self, query_key: np.ndarray, num_slots: int = 1, temperature: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Read from memory using content-based addressing.
        
        Args:
            query_key: Query key vector
            num_slots: Number of slots to read from (top-k)
            temperature: Temperature for attention sharpness
            
        Returns:
            (read_values, attention_weights) tuple
        """
        # Compute similarities (cosine similarity)
        similarities = []
        for slot in self.slots:
            sim = np.dot(query_key, slot.key) / (
                np.linalg.norm(query_key) * np.linalg.norm(slot.key) + 1e-8
            )
            similarities.append(sim)
        
        similarities = np.array(similarities)
        
        # Apply temperature
        similarities = similarities / (temperature + 1e-8)
        
        # Softmax attention
        attention = self._softmax(similarities)
        
        # Select top-k slots
        top_k_indices = np.argsort(attention)[-num_slots:][::-1]
        
        # Weighted sum of values
        read_values = np.zeros(self.value_dim, dtype=np.float32)
        for idx in top_k_indices:
            read_values += attention[idx] * self.slots[idx].value
        
        # Update usage statistics
        for idx in top_k_indices:
            self.slots[idx].usage_count += 1
            self.slots[idx].last_accessed = datetime.now()
        
        return read_values, attention
    
    def write(
        self,
        write_key: np.ndarray,
        write_value: np.ndarray,
        erase_vector: Optional[np.ndarray] = None,
        add_vector: Optional[np.ndarray] = None,
        write_strength: float = 1.0
    ) -> np.ndarray:
        """
        Write to memory using content-based addressing.
        
        Args:
            write_key: Key to determine write location
            write_value: Value to write
            erase_vector: Optional erase vector (0-1 per dimension)
            add_vector: Optional add vector (to add to existing value)
            write_strength: Strength of write operation
            
        Returns:
            Write attention weights
        """
        # Find best matching slot
        similarities = []
        for slot in self.slots:
            sim = np.dot(write_key, slot.key) / (
                np.linalg.norm(write_key) * np.linalg.norm(slot.key) + 1e-8
            )
            similarities.append(sim)
        
        similarities = np.array(similarities)
        attention = self._softmax(similarities)
        
        # Update memory slots
        for i, slot in enumerate(self.slots):
            weight = attention[i] * write_strength
            
            # Erase (if provided)
            if erase_vector is not None:
                slot.value = slot.value * (1 - weight * erase_vector)
            
            # Add (if provided, otherwise write)
            if add_vector is not None:
                slot.value = slot.value + weight * add_vector
            else:
                slot.value = slot.value * (1 - weight) + weight * write_value
            
            # Update key (slight update towards write_key)
            slot.key = slot.key * (1 - 0.1 * weight) + 0.1 * weight * write_key
            slot.key = slot.key / (np.linalg.norm(slot.key) + 1e-8)
        
        return attention
    
    def get_all_values(self) -> np.ndarray:
        """Get all memory values as matrix."""
        return np.array([slot.value for slot in self.slots])
    
    def get_least_used_slots(self, num_slots: int = 5) -> List[int]:
        """Get indices of least used memory slots."""
        usage_counts = [slot.usage_count for slot in self.slots]
        return np.argsort(usage_counts)[:num_slots].tolist()
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax function."""
        exp_x = np.exp(x - np.max(x))
        return exp_x / (np.sum(exp_x) + 1e-8)
    
    def to_dict(self) -> Dict:
        """Export memory to dictionary (for persistence)."""
        return {
            "memory_size": self.memory_size,
            "key_dim": self.key_dim,
            "value_dim": self.value_dim,
            "slots": [
                {
                    "key": slot.key.tolist(),
                    "value": slot.value.tolist(),
                    "usage_count": slot.usage_count,
                    "last_accessed": slot.last_accessed.isoformat()
                }
                for slot in self.slots
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ExternalMemoryBank':
        """Load memory from dictionary."""
        memory = cls(
            memory_size=data["memory_size"],
            key_dim=data["key_dim"],
            value_dim=data["value_dim"]
        )
        
        for i, slot_data in enumerate(data["slots"]):
            memory.slots[i].key = np.array(slot_data["key"])
            memory.slots[i].value = np.array(slot_data["value"])
            memory.slots[i].usage_count = slot_data["usage_count"]
            memory.slots[i].last_accessed = datetime.fromisoformat(slot_data["last_accessed"])
        
        return memory

