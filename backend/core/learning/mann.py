"""
Memory-Augmented Neural Network (MANN): Neural network with external memory.

Implements neural networks that can read from and write to external memory banks.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from core.learning.external_memory import ExternalMemoryBank
from core.learning.memory_controller import MemoryController, MemoryReadWrite
from utils.logging import get_logger

logger = get_logger(__name__)


if TORCH_AVAILABLE:
    class MANNModel(nn.Module):
        """
        Memory-Augmented Neural Network.
        
        Combines a controller network with external memory for long-term storage.
        """
        
        def __init__(
            self,
            input_dim: int,
            output_dim: int,
            memory_size: int = 128,
            memory_key_dim: int = 64,
            memory_value_dim: int = 128,
            controller_hidden_dim: int = 256,
            num_read_heads: int = 1,
            num_write_heads: int = 1
        ):
            """
            Initialize MANN model.
            
            Args:
                input_dim: Input dimension
                output_dim: Output dimension
                memory_size: Number of memory slots
                memory_key_dim: Memory key dimension
                memory_value_dim: Memory value dimension
                controller_hidden_dim: Controller hidden dimension
                num_read_heads: Number of read heads
                num_write_heads: Number of write heads
            """
            super().__init__()
            
            self.input_dim = input_dim
            self.output_dim = output_dim
            self.memory_size = memory_size
            self.memory_key_dim = memory_key_dim
            self.memory_value_dim = memory_value_dim
            
            # Memory bank (will be created per forward pass or managed separately)
            # For differentiable operations, we'd need PyTorch-compatible memory
            
            # Memory controller
            self.controller = MemoryController(
                input_dim=input_dim,
                memory_key_dim=memory_key_dim,
                memory_value_dim=memory_value_dim,
                controller_hidden_dim=controller_hidden_dim,
                num_read_heads=num_read_heads,
                num_write_heads=num_write_heads
            )
            
            # Output network (processes controller output + memory reads)
            read_output_dim = num_read_heads * memory_value_dim
            self.output_network = nn.Sequential(
                nn.Linear(controller_hidden_dim + read_output_dim, controller_hidden_dim),
                nn.ReLU(),
                nn.Linear(controller_hidden_dim, output_dim)
            )
        
        def forward(
            self,
            input_state: torch.Tensor,
            memory: Optional[ExternalMemoryBank] = None
        ) -> Tuple[torch.Tensor, Dict[str, Any]]:
            """
            Forward pass through MANN.
            
            Args:
                input_state: Input state [batch_size, input_dim]
                memory: Optional external memory bank (if None, creates new)
                
            Returns:
                (output, metadata) tuple
            """
            # Generate memory control signals
            control_signals = self.controller(input_state)
            
            # In a fully differentiable implementation, memory operations would
            # be differentiable too. For now, we use a hybrid approach where
            # memory is managed separately but controller learns to use it.
            
            # Process controller hidden state (get it from controller)
            # For simplicity, we'll use a separate forward through controller
            controller_hidden = self.controller.controller(input_state)
            
            # Read from memory (would be differentiable in full implementation)
            if memory is not None:
                # Convert read keys to numpy for memory operations
                read_keys_np = control_signals["read_keys"].detach().cpu().numpy()
                batch_size = read_keys_np.shape[0]
                
                read_values_list = []
                for i in range(batch_size):
                    read_vals = []
                    for head_idx in range(self.controller.num_read_heads):
                        read_key = read_keys_np[i, head_idx]
                        values, _ = memory.read(read_key, num_slots=1)
                        read_vals.append(values)
                    read_values_list.append(np.concatenate(read_vals))
                
                read_values = torch.FloatTensor(np.array(read_values_list)).to(input_state.device)
            else:
                # No memory, use zeros
                read_output_dim = self.controller.num_read_heads * self.memory_value_dim
                read_values = torch.zeros(input_state.shape[0], read_output_dim).to(input_state.device)
            
            # Concatenate controller output with memory reads
            combined = torch.cat([controller_hidden, read_values], dim=1)
            
            # Generate output
            output = self.output_network(combined)
            
            metadata = {
                "control_signals": control_signals,
                "memory_used": memory is not None
            }
            
            return output, metadata
else:
    # Dummy class when PyTorch not available
    class MANNModel:
        def __init__(self, *args, **kwargs):
            pass
        def forward(self, *args, **kwargs):
            return None, {}


class MANNWrapper:
    """
    Wrapper for MANN that manages memory lifecycle.
    
    Provides high-level interface for MANN usage.
    """
    
    def __init__(
        self,
        model: MANNModel,
        memory: Optional[ExternalMemoryBank] = None
    ):
        """
        Initialize MANN wrapper.
        
        Args:
            model: MANN model
            memory: Optional memory bank (creates new if None)
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for MANN")
        
        self.model = model
        self.memory = memory or ExternalMemoryBank(
            memory_size=model.memory_size,
            key_dim=model.memory_key_dim,
            value_dim=model.memory_value_dim
        )
        self.logger = get_logger(__name__)
    
    def predict(self, input_state: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Make prediction with memory operations.
        
        Args:
            input_state: Input state [input_dim] or [batch_size, input_dim]
            
        Returns:
            (prediction, metadata) tuple
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required")
        
        # Convert to tensor
        if input_state.ndim == 1:
            input_state = input_state.reshape(1, -1)
        
        input_tensor = torch.FloatTensor(input_state)
        
        # Forward pass
        with torch.no_grad():
            output, metadata = self.model(input_tensor, self.memory)
            output_np = output.cpu().numpy()
        
        # Perform writes based on control signals
        # (In full implementation, this would be part of forward pass)
        control_signals = metadata["control_signals"]
        
        write_keys = control_signals["write_keys"].cpu().numpy()
        write_values = control_signals["write_values"].cpu().numpy()
        erase_vectors = control_signals["erase_vectors"].cpu().numpy()
        add_vectors = control_signals["add_vectors"].cpu().numpy()
        write_strengths = control_signals["write_strengths"].cpu().numpy()
        
        # Write to memory (for each sample in batch)
        for i in range(input_state.shape[0]):
            for head_idx in range(self.model.controller.num_write_heads):
                write_key = write_keys[i, head_idx]
                write_value = write_values[i, head_idx]
                erase_vector = erase_vectors[i, head_idx]
                add_vector = add_vectors[i, head_idx]
                write_strength = float(write_strengths[i, head_idx])
                
                self.memory.write(
                    write_key,
                    write_value,
                    erase_vector,
                    add_vector,
                    write_strength
                )
        
        if input_state.shape[0] == 1:
            output_np = output_np[0]  # Remove batch dimension
        
        return output_np, metadata
    
    def save_memory(self, filepath: str) -> None:
        """Save memory to file."""
        import json
        memory_dict = self.memory.to_dict()
        with open(filepath, 'w') as f:
            json.dump(memory_dict, f)
        self.logger.info(f"Saved memory to {filepath}")
    
    def load_memory(self, filepath: str) -> None:
        """Load memory from file."""
        import json
        with open(filepath, 'r') as f:
            memory_dict = json.load(f)
        self.memory = ExternalMemoryBank.from_dict(memory_dict)
        self.logger.info(f"Loaded memory from {filepath}")

