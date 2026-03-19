"""
Knowledge Distillation: Transfer knowledge from teacher to student models.

Implements teacher-student learning for model compression and knowledge transfer.
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

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DistillationConfig:
    """Configuration for knowledge distillation."""
    temperature: float = 3.0  # Softmax temperature
    alpha: float = 0.7  # Weight for soft target loss
    beta: float = 0.3  # Weight for hard target loss
    learning_rate: float = 0.001
    epochs: int = 10


class KnowledgeDistiller:
    """
    Distills knowledge from teacher model to student model.

    Transfers soft predictions (probabilities) from teacher to student
    for better knowledge transfer.  When PyTorch is unavailable the
    distiller operates in *no-op mode*: ``distill()`` returns an empty
    history so callers don't need conditional logic.
    """

    def __init__(self, config: Optional[DistillationConfig] = None):
        """Initialize knowledge distiller."""
        self.logger = get_logger(__name__)
        if not TORCH_AVAILABLE:
            logger.warning(
                "PyTorch unavailable – KnowledgeDistiller running in no-op mode. "
                "distill() will return an empty history."
            )
            self._noop = True
            self.config = config or DistillationConfig()
            return
        self._noop = False
        self.config = config or DistillationConfig()
    
    def distill(
        self,
        teacher_model: Any,
        student_model: Any,
        train_data: Any,
        validation_data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Distill knowledge from teacher to student.
        
        Args:
            teacher_model: Pre-trained teacher model
            student_model: Student model to train
            train_data: Training data
            validation_data: Optional validation data
            
        Returns:
            Training metrics and statistics
        """
        if self._noop:
            logger.warning("KnowledgeDistiller no-op: PyTorch unavailable, returning empty history")
            return {"history": [], "final_train_loss": None, "final_val_loss": None}

        teacher_model.eval()  # Teacher in eval mode
        student_model.train()  # Student in train mode
        
        # Setup optimizer
        optimizer = torch.optim.Adam(student_model.parameters(), lr=self.config.learning_rate)
        
        device = next(teacher_model.parameters()).device
        student_model.to(device)
        
        history = []
        
        for epoch in range(self.config.epochs):
            epoch_loss = 0.0
            num_batches = 0
            
            # Training loop
            for batch in train_data:
                if isinstance(batch, (list, tuple)):
                    inputs, hard_targets = batch[0], batch[1]
                else:
                    inputs = batch
                    hard_targets = None
                
                inputs = inputs.to(device)
                
                # Get teacher predictions (soft targets)
                with torch.no_grad():
                    teacher_outputs = teacher_model(inputs)
                    teacher_probs = F.softmax(teacher_outputs / self.config.temperature, dim=1)
                
                # Get student predictions
                student_outputs = student_model(inputs)
                
                # Compute distillation loss
                loss = self._compute_distillation_loss(
                    student_outputs,
                    teacher_probs,
                    hard_targets
                )
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                num_batches += 1
            
            avg_loss = epoch_loss / num_batches if num_batches > 0 else 0.0
            
            # Validation
            val_loss = None
            if validation_data:
                val_loss = self._validate(student_model, teacher_model, validation_data, device)
            
            history.append({
                "epoch": epoch + 1,
                "train_loss": avg_loss,
                "val_loss": val_loss
            })
            
            self.logger.info(f"Epoch {epoch+1}/{self.config.epochs}: "
                           f"Train Loss: {avg_loss:.4f}, "
                           f"Val Loss: {val_loss:.4f if val_loss else 'N/A'}")
        
        return {
            "history": history,
            "final_train_loss": history[-1]["train_loss"],
            "final_val_loss": history[-1].get("val_loss")
        }
    
    def _compute_distillation_loss(
        self,
        student_outputs: torch.Tensor,
        teacher_probs: torch.Tensor,
        hard_targets: Optional[torch.Tensor]
    ) -> torch.Tensor:
        """
        Compute combined distillation loss.
        
        Loss = alpha * soft_loss + beta * hard_loss
        """
        # Soft target loss (KL divergence)
        student_log_probs = F.log_softmax(student_outputs / self.config.temperature, dim=1)
        soft_loss = F.kl_div(student_log_probs, teacher_probs, reduction='batchmean')
        soft_loss = soft_loss * (self.config.temperature ** 2)
        
        # Hard target loss (if available)
        if hard_targets is not None:
            hard_targets = hard_targets.to(student_outputs.device)
            hard_loss = F.cross_entropy(student_outputs, hard_targets)
        else:
            hard_loss = torch.tensor(0.0).to(student_outputs.device)
        
        # Combined loss
        total_loss = self.config.alpha * soft_loss + self.config.beta * hard_loss
        
        return total_loss
    
    def _validate(
        self,
        student_model: nn.Module,
        teacher_model: nn.Module,
        validation_data: Any,
        device: torch.device
    ) -> float:
        """Validate student model."""
        student_model.eval()
        total_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for batch in validation_data:
                if isinstance(batch, (list, tuple)):
                    inputs, _ = batch[0], batch[1]
                else:
                    inputs = batch
                
                inputs = inputs.to(device)
                
                teacher_outputs = teacher_model(inputs)
                teacher_probs = F.softmax(teacher_outputs / self.config.temperature, dim=1)
                
                student_outputs = student_model(inputs)
                
                student_log_probs = F.log_softmax(student_outputs / self.config.temperature, dim=1)
                loss = F.kl_div(student_log_probs, teacher_probs, reduction='batchmean')
                loss = loss * (self.config.temperature ** 2)
                
                total_loss += loss.item()
                num_batches += 1
        
        student_model.train()
        return total_loss / num_batches if num_batches > 0 else 0.0


class EnsembleDistiller:
    """
    Distills multiple teacher models into a single student.

    Combines knowledge from multiple expert models.  Operates in no-op mode
    when PyTorch is unavailable.
    """

    def __init__(self, config: Optional[DistillationConfig] = None):
        """Initialize ensemble distiller."""
        self.logger = get_logger(__name__)
        if not TORCH_AVAILABLE:
            logger.warning(
                "PyTorch unavailable – EnsembleDistiller running in no-op mode."
            )
            self._noop = True
            self.config = config or DistillationConfig()
            return
        self._noop = False
        self.config = config or DistillationConfig()
    
    def distill_ensemble(
        self,
        teacher_models: List[Any],
        student_model: Any,
        train_data: Any,
        teacher_weights: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Distill from multiple teachers.
        
        Args:
            teacher_models: List of teacher models
            student_model: Student model
            train_data: Training data
            teacher_weights: Optional weights for each teacher (uniform if None)
            
        Returns:
            Training statistics
        """
        if self._noop:
            logger.warning("EnsembleDistiller no-op: PyTorch unavailable, returning empty history")
            return {"history": []}

        if teacher_weights is None:
            teacher_weights = [1.0 / len(teacher_models)] * len(teacher_models)

        # Set all teachers to eval mode
        for teacher in teacher_models:
            teacher.eval()
        
        student_model.train()
        optimizer = torch.optim.Adam(student_model.parameters(), lr=self.config.learning_rate)
        
        device = next(teacher_models[0].parameters()).device
        student_model.to(device)
        
        history = []
        
        for epoch in range(self.config.epochs):
            epoch_loss = 0.0
            num_batches = 0
            
            for batch in train_data:
                if isinstance(batch, (list, tuple)):
                    inputs, hard_targets = batch[0], batch[1]
                else:
                    inputs = batch
                    hard_targets = None
                
                inputs = inputs.to(device)
                
                # Average teacher predictions
                ensemble_probs = None
                with torch.no_grad():
                    for teacher, weight in zip(teacher_models, teacher_weights):
                        teacher_outputs = teacher(inputs)
                        teacher_probs = F.softmax(teacher_outputs / self.config.temperature, dim=1)
                        
                        if ensemble_probs is None:
                            ensemble_probs = weight * teacher_probs
                        else:
                            ensemble_probs += weight * teacher_probs
                
                # Student predictions
                student_outputs = student_model(inputs)
                
                # Loss
                student_log_probs = F.log_softmax(student_outputs / self.config.temperature, dim=1)
                soft_loss = F.kl_div(student_log_probs, ensemble_probs, reduction='batchmean')
                soft_loss = soft_loss * (self.config.temperature ** 2)
                
                if hard_targets is not None:
                    hard_targets = hard_targets.to(device)
                    hard_loss = F.cross_entropy(student_outputs, hard_targets)
                else:
                    hard_loss = torch.tensor(0.0).to(device)
                
                loss = self.config.alpha * soft_loss + self.config.beta * hard_loss
                
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                num_batches += 1
            
            avg_loss = epoch_loss / num_batches if num_batches > 0 else 0.0
            history.append({"epoch": epoch + 1, "loss": avg_loss})
        
        return {"history": history}

