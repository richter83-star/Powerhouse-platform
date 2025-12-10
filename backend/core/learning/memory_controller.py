"""
Memory Controller: Neural network that controls memory read/write operations.

Implements read/write heads with attention mechanisms for MANN.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from core.learning.external_memory import ExternalMemoryBank
from utils.logging import get_logger

logger = get_logger(__name__)


if TORCH_AVAILABLE:
    class MemoryController(nn.Module):
        """
        Neural network controller for memory operations.
        
        Takes input state and generates:
        - Read keys (for reading from memory)
        - Write keys, values, erase, add vectors (for writing)
        """
        
        def __init__(
            self,
            input_dim: int,
            memory_key_dim: int,
            memory_value_dim: int,
            controller_hidden_dim: int = 256,
            num_read_heads: int = 1,
            num_write_heads: int = 1
        ):
            """
            Initialize memory controller.
            
            Args:
                input_dim: Dimension of input state
                memory_key_dim: Dimension of memory keys
                memory_value_dim: Dimension of memory values
                controller_hidden_dim: Hidden layer dimension
                num_read_heads: Number of read heads
                num_write_heads: Number of write heads
            """
            super().__init__()
            
            self.input_dim = input_dim
            self.memory_key_dim = memory_key_dim
            self.memory_value_dim = memory_value_dim
            self.num_read_heads = num_read_heads
            self.num_write_heads = num_write_heads
            
            # Controller network
            self.controller = nn.Sequential(
                nn.Linear(input_dim, controller_hidden_dim),
                nn.ReLU(),
                nn.Linear(controller_hidden_dim, controller_hidden_dim),
                nn.ReLU()
            )
            
            # Read heads: generate read keys
            self.read_keys = nn.ModuleList([
                nn.Linear(controller_hidden_dim, memory_key_dim)
                for _ in range(num_read_heads)
            ])
            
            # Write heads: generate write keys, values, erase, add vectors
            self.write_keys = nn.ModuleList([
                nn.Linear(controller_hidden_dim, memory_key_dim)
                for _ in range(num_write_heads)
            ])
            self.write_values = nn.ModuleList([
                nn.Linear(controller_hidden_dim, memory_value_dim)
                for _ in range(num_write_heads)
            ])
            self.erase_vectors = nn.ModuleList([
                nn.Sequential(
                    nn.Linear(controller_hidden_dim, memory_value_dim),
                    nn.Sigmoid()  # Erase is 0-1
                )
                for _ in range(num_write_heads)
            ])
            self.add_vectors = nn.ModuleList([
                nn.Linear(controller_hidden_dim, memory_value_dim)
                for _ in range(num_write_heads)
            ])
            self.write_strengths = nn.ModuleList([
                nn.Sequential(
                    nn.Linear(controller_hidden_dim, 1),
                    nn.Sigmoid()  # Strength is 0-1
                )
                for _ in range(num_write_heads)
            ])
        
        def forward(self, input_state: torch.Tensor) -> Dict[str, torch.Tensor]:
            """
            Generate memory control signals from input state.
            
            Args:
                input_state: Input state tensor [batch_size, input_dim]
                
            Returns:
                Dictionary with read/write signals
            """
            # Pass through controller
            hidden = self.controller(input_state)
            
            # Generate read signals
            read_keys = torch.stack([
                read_head(hidden) for read_head in self.read_keys
            ], dim=1)  # [batch, num_read_heads, key_dim]
            
            # Generate write signals
            write_keys = torch.stack([
                write_head(hidden) for write_head in self.write_keys
            ], dim=1)  # [batch, num_write_heads, key_dim]
            
            write_values = torch.stack([
                write_head(hidden) for write_head in self.write_values
            ], dim=1)  # [batch, num_write_heads, value_dim]
            
            erase_vectors = torch.stack([
                erase_head(hidden) for erase_head in self.erase_vectors
            ], dim=1)  # [batch, num_write_heads, value_dim]
            
            add_vectors = torch.stack([
                add_head(hidden) for add_head in self.add_vectors
            ], dim=1)  # [batch, num_write_heads, value_dim]
            
            write_strengths = torch.stack([
                strength_head(hidden) for strength_head in self.write_strengths
            ], dim=1).squeeze(-1)  # [batch, num_write_heads]
            
            return {
                "read_keys": read_keys,
                "write_keys": write_keys,
                "write_values": write_values,
                "erase_vectors": erase_vectors,
                "add_vectors": add_vectors,
                "write_strengths": write_strengths
            }
else:
    # Dummy class when PyTorch not available
    class MemoryController:
        def __init__(self, *args, **kwargs):
            pass
        def forward(self, *args, **kwargs):
            return {}


class MemoryReadWrite:
    """
    Helper class for performing differentiable memory operations.
    """
    
    @staticmethod
    def read(
        memory: ExternalMemoryBank,
        query_keys: np.ndarray,
        num_slots: int = 1,
        temperature: float = 1.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Read from memory (batched).
        
        Args:
            memory: Memory bank
            query_keys: Query keys [num_queries, key_dim]
            num_slots: Number of slots to read
            temperature: Attention temperature
            
        Returns:
            (read_values, attention_weights)
        """
        if query_keys.ndim == 1:
            query_keys = query_keys.reshape(1, -1)
        
        read_values = []
        attentions = []
        
        for query_key in query_keys:
            values, attention = memory.read(query_key, num_slots, temperature)
            read_values.append(values)
            attentions.append(attention)
        
        return np.array(read_values), np.array(attentions)
    
    @staticmethod
    def write(
        memory: ExternalMemoryBank,
        write_key: np.ndarray,
        write_value: np.ndarray,
        erase_vector: Optional[np.ndarray] = None,
        add_vector: Optional[np.ndarray] = None,
        write_strength: float = 1.0
    ) -> np.ndarray:
        """
        Write to memory.
        
        Args:
            memory: Memory bank
            write_key: Write key
            write_value: Write value
            erase_vector: Optional erase vector
            add_vector: Optional add vector
            write_strength: Write strength
            
        Returns:
            Write attention weights
        """
        return memory.write(
            write_key,
            write_value,
            erase_vector,
            add_vector,
            write_strength
        )

