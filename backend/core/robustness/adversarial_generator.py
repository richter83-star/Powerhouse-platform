"""
Adversarial Generator: Creates adversarial examples that fool models.

Implements FGSM, PGD, and other adversarial attack methods.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AdversarialExample:
    """Represents an adversarial example."""
    original_input: np.ndarray
    adversarial_input: np.ndarray
    perturbation: np.ndarray
    perturbation_norm: float
    original_prediction: Any
    adversarial_prediction: Any
    attack_success: bool


class AdversarialGenerator:
    """
    Generates adversarial examples to test model robustness.
    
    Supports:
    - FGSM (Fast Gradient Sign Method)
    - PGD (Projected Gradient Descent)
    - Custom attacks
    """
    
    def __init__(self, epsilon: float = 0.1, method: str = "fgsm"):
        """
        Initialize adversarial generator.
        
        Args:
            epsilon: Perturbation magnitude
            method: Attack method ("fgsm", "pgd")
        """
        self.epsilon = epsilon
        self.method = method
        self.logger = get_logger(__name__)
    
    def generate(
        self,
        model: Any,  # nn.Module or callable
        input_data: np.ndarray,
        target: Optional[Any] = None,
        bounds: Optional[Tuple[float, float]] = None
    ) -> AdversarialExample:
        """
        Generate adversarial example.
        
        Args:
            model: Model to attack
            input_data: Original input
            target: Optional target (for targeted attack)
            bounds: Optional input bounds (min, max)
            
        Returns:
            AdversarialExample
        """
        if self.method == "fgsm":
            return self._fgsm_attack(model, input_data, target, bounds)
        elif self.method == "pgd":
            return self._pgd_attack(model, input_data, target, bounds)
        else:
            raise ValueError(f"Unknown attack method: {self.method}")
    
    def _fgsm_attack(
        self,
        model: Any,
        input_data: np.ndarray,
        target: Optional[Any],
        bounds: Optional[Tuple[float, float]]
    ) -> AdversarialExample:
        """
        Fast Gradient Sign Method attack.
        
        Creates adversarial example by adding epsilon * sign(gradient).
        """
        if not TORCH_AVAILABLE:
            # Fallback: random perturbation
            perturbation = np.random.randn(*input_data.shape) * self.epsilon
            adversarial = input_data + perturbation
        else:
            # Convert to tensor
            input_tensor = torch.FloatTensor(input_data).requires_grad_(True)
            
            # Forward pass
            if isinstance(model, nn.Module):
                output = model(input_tensor)
                loss = self._compute_loss(output, target, input_data, model)
            else:
                # Assume callable
                output = model(input_tensor.detach().numpy())
                loss = torch.FloatTensor([np.mean((output - target) ** 2) if target is not None else 0.0])
            
            # Backward pass
            loss.backward()
            
            # Get gradient
            gradient = input_tensor.grad.data
            
            # Create perturbation
            perturbation = self.epsilon * torch.sign(gradient)
            adversarial_tensor = input_tensor + perturbation
            
            # Apply bounds if provided
            if bounds:
                adversarial_tensor = torch.clamp(adversarial_tensor, bounds[0], bounds[1])
            
            perturbation = perturbation.detach().numpy()
            adversarial = adversarial_tensor.detach().numpy()
        
        # Get predictions
        original_pred = self._predict(model, input_data)
        adversarial_pred = self._predict(model, adversarial)
        
        attack_success = not np.array_equal(original_pred, adversarial_pred)
        
        return AdversarialExample(
            original_input=input_data,
            adversarial_input=adversarial,
            perturbation=perturbation,
            perturbation_norm=np.linalg.norm(perturbation),
            original_prediction=original_pred,
            adversarial_prediction=adversarial_pred,
            attack_success=attack_success
        )
    
    def _pgd_attack(
        self,
        model: Any,
        input_data: np.ndarray,
        target: Optional[Any],
        bounds: Optional[Tuple[float, float]],
        num_iterations: int = 10,
        step_size: Optional[float] = None
    ) -> AdversarialExample:
        """
        Projected Gradient Descent attack (iterative FGSM).
        
        More powerful than FGSM but slower.
        """
        step_size = step_size or (self.epsilon / num_iterations)
        adversarial = input_data.copy()
        
        if TORCH_AVAILABLE:
            adversarial_tensor = torch.FloatTensor(adversarial).requires_grad_(True)
            
            for _ in range(num_iterations):
                # Forward and backward
                if isinstance(model, nn.Module):
                    output = model(adversarial_tensor)
                    loss = self._compute_loss(output, target, input_data, model)
                else:
                    output_np = model(adversarial_tensor.detach().numpy())
                    loss = torch.FloatTensor([np.mean((output_np - target) ** 2) if target is not None else 0.0])
                
                loss.backward()
                gradient = adversarial_tensor.grad.data
                
                # Update adversarial example
                adversarial_tensor = adversarial_tensor + step_size * torch.sign(gradient)
                
                # Project back to epsilon ball
                perturbation = adversarial_tensor - torch.FloatTensor(input_data)
                perturbation = torch.clamp(perturbation, -self.epsilon, self.epsilon)
                adversarial_tensor = torch.FloatTensor(input_data) + perturbation
                
                # Apply bounds
                if bounds:
                    adversarial_tensor = torch.clamp(adversarial_tensor, bounds[0], bounds[1])
                
                adversarial_tensor = adversarial_tensor.detach().requires_grad_(True)
            
            adversarial = adversarial_tensor.detach().numpy()
            perturbation = adversarial - input_data
        else:
            # Fallback: random iterative perturbation
            perturbation = np.zeros_like(input_data)
            for _ in range(num_iterations):
                step = np.random.randn(*input_data.shape) * step_size
                perturbation += step
                perturbation = np.clip(perturbation, -self.epsilon, self.epsilon)
            
            adversarial = input_data + perturbation
        
        original_pred = self._predict(model, input_data)
        adversarial_pred = self._predict(model, adversarial)
        
        return AdversarialExample(
            original_input=input_data,
            adversarial_input=adversarial,
            perturbation=perturbation,
            perturbation_norm=np.linalg.norm(perturbation),
            original_prediction=original_pred,
            adversarial_prediction=adversarial_pred,
            attack_success=not np.array_equal(original_pred, adversarial_pred)
        )
    
    def _compute_loss(self, output: torch.Tensor, target: Any, input_data: np.ndarray, model: Any) -> torch.Tensor:
        """Compute loss for adversarial generation."""
        if target is not None:
            if isinstance(target, torch.Tensor):
                if output.dim() > 1:
                    return nn.functional.cross_entropy(output, target)
                else:
                    return nn.functional.mse_loss(output, target)
            else:
                target_tensor = torch.FloatTensor([target])
                return nn.functional.mse_loss(output, target_tensor)
        else:
            # Untargeted: maximize loss
            return -output.sum()
    
    def _predict(self, model: Any, input_data: np.ndarray) -> Any:
        """Get model prediction."""
        if TORCH_AVAILABLE and isinstance(model, nn.Module):
            with torch.no_grad():
                input_tensor = torch.FloatTensor(input_data)
                output = model(input_tensor)
                if output.dim() > 1:
                    return torch.argmax(output, dim=1).numpy()
                else:
                    return output.numpy()
        else:
            # Assume callable
            output = model(input_data)
            if isinstance(output, np.ndarray) and output.ndim > 0:
                return np.argmax(output) if output.size > 1 else output[0]
            return output

