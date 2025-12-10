"""
Adversarial Training: Trains models to be robust against adversarial attacks.

Uses adversarial examples during training to improve robustness.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from core.robustness.adversarial_generator import AdversarialGenerator
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AdversarialTrainingConfig:
    """Configuration for adversarial training."""
    epsilon: float = 0.1
    alpha: float = 0.5  # Mix of clean and adversarial examples
    attack_method: str = "fgsm"
    epochs: int = 10
    learning_rate: float = 0.001


class AdversarialTrainer:
    """
    Trains models to be robust against adversarial attacks.
    
    Alternates between clean and adversarial examples during training.
    """
    
    def __init__(self, config: Optional[AdversarialTrainingConfig] = None):
        """Initialize adversarial trainer."""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for adversarial training")
        
        self.config = config or AdversarialTrainingConfig()
        self.generator = AdversarialGenerator(
            epsilon=self.config.epsilon,
            method=self.config.attack_method
        )
        self.logger = get_logger(__name__)
    
    def train(
        self,
        model: nn.Module,
        train_data: Any,  # Dataset or DataLoader
        loss_function: Optional[nn.Module] = None
    ) -> Dict[str, Any]:
        """
        Train model with adversarial examples.
        
        Args:
            model: Model to train
            train_data: Training data
            loss_function: Loss function (uses CrossEntropyLoss if None)
            
        Returns:
            Training statistics
        """
        model.train()
        device = next(model.parameters()).device
        
        if loss_function is None:
            loss_function = nn.CrossEntropyLoss()
        
        optimizer = optim.Adam(model.parameters(), lr=self.config.learning_rate)
        
        history = []
        
        for epoch in range(self.config.epochs):
            epoch_loss = 0.0
            num_batches = 0
            
            for batch in train_data:
                if isinstance(batch, (list, tuple)):
                    inputs, labels = batch[0], batch[1]
                else:
                    inputs = batch
                    labels = None
                
                inputs = inputs.to(device)
                if labels is not None:
                    labels = labels.to(device)
                
                # Mix clean and adversarial examples
                if np.random.random() < self.config.alpha:
                    # Use adversarial examples
                    inputs_np = inputs.detach().cpu().numpy()
                    adversarial_inputs = []
                    
                    for i in range(inputs_np.shape[0]):
                        example = self.generator.generate(
                            model=model,
                            input_data=inputs_np[i],
                            target=labels[i].item() if labels is not None else None
                        )
                        adversarial_inputs.append(example.adversarial_input)
                    
                    inputs = torch.FloatTensor(np.array(adversarial_inputs)).to(device)
                
                # Forward pass
                outputs = model(inputs)
                
                # Compute loss
                if labels is not None:
                    loss = loss_function(outputs, labels)
                else:
                    loss = outputs.mean()  # Fallback
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                num_batches += 1
            
            avg_loss = epoch_loss / num_batches if num_batches > 0 else 0.0
            history.append({"epoch": epoch + 1, "loss": avg_loss})
            
            self.logger.info(f"Adversarial training epoch {epoch+1}/{self.config.epochs}: "
                           f"Loss: {avg_loss:.4f}")
        
        return {"history": history, "final_loss": history[-1]["loss"]}

