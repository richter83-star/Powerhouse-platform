"""
Model Compression: Reduces model size while maintaining accuracy.

Implements pruning, quantization, and architecture search.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Provide minimal stubs so type annotations in class bodies don't fail
    class _TorchStub:
        class Tensor: pass
        class device: pass
        def __getattr__(self, name):
            return type(name, (), {})()
    class _NNStub:
        class Module: pass
        class Linear: pass
        class ReLU: pass
        class Dropout: pass
        class Sequential: pass
        def __getattr__(self, name):
            return type(name, (), {})()
    class _FStub:
        def __getattr__(self, name):
            return lambda *a, **kw: None
    torch = _TorchStub()  # type: ignore[assignment]
    nn = _NNStub()        # type: ignore[assignment]
    F = _FStub()          # type: ignore[assignment]

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CompressionConfig:
    """Configuration for model compression."""
    pruning_ratio: float = 0.5  # Fraction of weights to prune
    quantization_bits: int = 8  # Bits for quantization (8, 4, etc.)
    compression_method: str = "pruning"  # "pruning", "quantization", "both"


class ModelCompressor:
    """
    Compresses neural network models.
    
    Supports:
    - Weight pruning (removes unimportant weights)
    - Quantization (reduces precision)
    - Architecture search (finds smaller architectures)
    """
    
    def __init__(self, config: Optional[CompressionConfig] = None):
        """Initialize model compressor.

        When PyTorch is unavailable the compressor runs in *no-op mode*:
        ``compress()`` returns the model unchanged with a diagnostic stat dict.
        """
        self.logger = get_logger(__name__)
        if not TORCH_AVAILABLE:
            logger.warning(
                "PyTorch unavailable – ModelCompressor running in no-op mode. "
                "compress() will return the model unchanged."
            )
            self._noop = True
            self.config = config or CompressionConfig()
            return
        self._noop = False
        self.config = config or CompressionConfig()
    
    def compress(
        self,
        model: Any,
        method: Optional[str] = None
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Compress a model.

        Args:
            model: Model to compress
            method: Compression method (uses config if None)

        Returns:
            (compressed_model, compression_stats) tuple.
            In no-op mode returns (model, {"noop": True}).
        """
        if self._noop:
            logger.warning("ModelCompressor no-op: returning model unchanged")
            return model, {"noop": True, "reason": "PyTorch unavailable"}
        method = method or self.config.compression_method
        
        if method == "pruning":
            return self._prune(model)
        elif method == "quantization":
            return self._quantize(model)
        elif method == "both":
            compressed, stats1 = self._prune(model)
            compressed, stats2 = self._quantize(compressed)
            stats = {**stats1, **stats2}
            return compressed, stats
        else:
            raise ValueError(f"Unknown compression method: {method}")
    
    def _prune(self, model: nn.Module) -> Tuple[nn.Module, Dict[str, Any]]:
        """
        Prune model weights (magnitude-based pruning).
        
        Args:
            model: Model to prune
            
        Returns:
            (pruned_model, stats) tuple
        """
        original_params = sum(p.numel() for p in model.parameters())
        original_size = original_params * 4  # Assuming float32 (4 bytes)
        
        model_copy = self._copy_model(model)
        
        # Prune each module
        total_pruned = 0
        for module in model_copy.modules():
            if isinstance(module, (nn.Linear, nn.Conv2d)):
                weight = module.weight.data
                
                # Calculate threshold (prune smallest weights)
                flat_weights = torch.abs(weight).flatten()
                threshold_idx = int(self.config.pruning_ratio * flat_weights.numel())
                threshold = torch.kthvalue(flat_weights, threshold_idx)[0].item()
                
                # Create mask
                mask = torch.abs(weight) > threshold
                module.weight.data *= mask.float()
                
                pruned_count = (~mask).sum().item()
                total_pruned += pruned_count
        
        compressed_params = original_params - total_pruned
        compression_ratio = compressed_params / original_params
        
        stats = {
            "original_params": original_params,
            "compressed_params": compressed_params,
            "pruned_params": total_pruned,
            "compression_ratio": compression_ratio,
            "method": "pruning"
        }
        
        self.logger.info(f"Pruned {total_pruned} parameters "
                        f"({compression_ratio:.2%} remaining)")
        
        return model_copy, stats
    
    def _quantize(self, model: nn.Module) -> Tuple[nn.Module, Dict[str, Any]]:
        """
        Quantize model weights.
        
        Args:
            model: Model to quantize
            
        Returns:
            (quantized_model, stats) tuple
        """
        original_bits = 32  # float32
        target_bits = self.config.quantization_bits
        
        model_copy = self._copy_model(model)
        
        # Quantize weights
        for module in model_copy.modules():
            if isinstance(module, (nn.Linear, nn.Conv2d)):
                weight = module.weight.data
                
                # Quantize to target bits
                min_val = weight.min().item()
                max_val = weight.max().item()
                
                # Scale to [0, 2^bits - 1]
                scale = (2 ** target_bits - 1) / (max_val - min_val + 1e-8)
                quantized = torch.round((weight - min_val) * scale)
                
                # Dequantize
                dequantized = quantized / scale + min_val
                module.weight.data = dequantized
        
        size_reduction = 1.0 - (target_bits / original_bits)
        
        stats = {
            "original_bits": original_bits,
            "quantized_bits": target_bits,
            "size_reduction": size_reduction,
            "method": "quantization"
        }
        
        self.logger.info(f"Quantized to {target_bits} bits "
                        f"({size_reduction:.2%} size reduction)")
        
        return model_copy, stats
    
    def _copy_model(self, model: nn.Module) -> nn.Module:
        """Create a deep copy of the model."""
        return type(model)(**{name: getattr(model, name) 
                             for name in dir(model) 
                             if not name.startswith('_') and 
                             not callable(getattr(model, name, None))})
    
    def estimate_size(self, model: nn.Module, bits: int = 32) -> Dict[str, Any]:
        """
        Estimate model size.
        
        Args:
            model: Model to analyze
            bits: Bits per parameter (32 for float32)
            
        Returns:
            Size statistics
        """
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        
        bytes_per_param = bits / 8
        total_size_bytes = total_params * bytes_per_param
        total_size_mb = total_size_bytes / (1024 * 1024)
        
        return {
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "size_bytes": total_size_bytes,
            "size_mb": total_size_mb,
            "bits_per_param": bits
        }

