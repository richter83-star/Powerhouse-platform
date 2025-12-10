"""
Model training pipeline for neural network models.

Provides batch processing, gradient updates, validation, and model persistence.
"""

from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from collections import deque
import pickle
from pathlib import Path

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Create dummy classes if PyTorch not available
    class Dataset:
        pass
    # Create minimal nn module structure
    class _DummyNN:
        class Module:
            pass
        class MSELoss:
            pass
    nn = _DummyNN()
    DataLoader = None
    torch = None

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for model training."""
    batch_size: int = 32
    learning_rate: float = 0.001
    num_epochs: int = 10
    validation_split: float = 0.2
    early_stopping_patience: int = 5
    min_delta: float = 0.001
    save_best_model: bool = True
    save_checkpoints: bool = True
    checkpoint_interval: int = 5  # Save every N epochs
    gradient_clip_norm: Optional[float] = 1.0
    weight_decay: float = 0.0001
    warmup_steps: int = 100


@dataclass
class TrainingMetrics:
    """Metrics tracked during training."""
    epoch: int
    train_loss: float
    val_loss: Optional[float] = None
    train_accuracy: Optional[float] = None
    val_accuracy: Optional[float] = None
    learning_rate: float = 0.001
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


if TORCH_AVAILABLE:
    class TrainingDataset(Dataset):
        """PyTorch dataset for training data."""
        
        def __init__(self, features: np.ndarray, targets: np.ndarray):
            """
            Initialize dataset.
            
            Args:
                features: Feature matrix (n_samples, n_features)
                targets: Target values (n_samples,) or (n_samples, n_outputs)
            """
            self.features = torch.FloatTensor(features)
            self.targets = torch.FloatTensor(targets)
        
        def __len__(self):
            return len(self.features)
        
        def __getitem__(self, idx):
            return self.features[idx], self.targets[idx]
else:
    class TrainingDataset:
        """Dummy dataset class when PyTorch is not available."""
        
        def __init__(self, features: np.ndarray, targets: np.ndarray):
            self.features = features
            self.targets = targets
        
        def __len__(self):
            return len(self.features)
        
        def __getitem__(self, idx):
            return self.features[idx], self.targets[idx]


class ModelTrainingPipeline:
    """
    Training pipeline for neural network models.
    
    Handles:
    - Data preparation and batching
    - Training loops with gradient updates
    - Validation and early stopping
    - Model checkpointing
    - Metrics tracking
    """
    
    def __init__(
        self,
        model: Any,  # nn.Module when PyTorch available
        config: Optional[TrainingConfig] = None,
        device: Optional[str] = None
    ):
        """
        Initialize training pipeline.
        
        Args:
            model: PyTorch model to train
            config: Training configuration
            device: Device to train on ('cpu', 'cuda', or None for auto)
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for ModelTrainingPipeline")
        
        self.model = model
        self.config = config or TrainingConfig()
        
        # Determine device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        self.model.to(self.device)
        
        # Initialize optimizer and loss
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay
        )
        
        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=3,
            verbose=True
        )
        
        self.criterion = nn.MSELoss()
        
        # Training state
        self.training_history: List[TrainingMetrics] = []
        self.best_val_loss: Optional[float] = None
        self.best_model_state: Optional[Dict[str, Any]] = None
        self.epochs_without_improvement = 0
        
        logger.info(f"Initialized training pipeline on device: {self.device}")
    
    def prepare_data(
        self,
        features: np.ndarray,
        targets: np.ndarray,
        shuffle: bool = True
    ) -> Tuple[Any, Optional[Any]]:  # DataLoader when PyTorch available
        """
        Prepare data for training.
        
        Args:
            features: Feature matrix (n_samples, n_features)
            targets: Target values (n_samples,) or (n_samples, n_outputs)
            shuffle: Whether to shuffle training data
            
        Returns:
            Tuple of (train_loader, val_loader)
        """
        # Split data
        n_samples = len(features)
        n_train = int(n_samples * (1 - self.config.validation_split))
        
        indices = np.arange(n_samples)
        if shuffle:
            np.random.shuffle(indices)
        
        train_indices = indices[:n_train]
        val_indices = indices[n_train:]
        
        # Create datasets
        if not TORCH_AVAILABLE or DataLoader is None:
            raise ImportError("PyTorch DataLoader is required for prepare_data")
        
        train_dataset = TrainingDataset(features[train_indices], targets[train_indices])
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=shuffle,
            num_workers=0  # Set to 0 for Windows compatibility
        )
        
        val_loader = None
        if len(val_indices) > 0:
            val_dataset = TrainingDataset(features[val_indices], targets[val_indices])
            val_loader = DataLoader(
                val_dataset,
                batch_size=self.config.batch_size,
                shuffle=False,
                num_workers=0
            )
        
        logger.info(
            f"Prepared data: {len(train_indices)} train samples, "
            f"{len(val_indices)} validation samples"
        )
        
        return train_loader, val_loader
    
    def train_epoch(
        self,
        train_loader: Any,  # DataLoader when PyTorch available
        epoch: int
    ) -> Tuple[float, Optional[float]]:
        """
        Train for one epoch.
        
        Args:
            train_loader: Training data loader
            epoch: Current epoch number
            
        Returns:
            Tuple of (average_loss, average_accuracy)
        """
        self.model.train()
        total_loss = 0.0
        total_correct = 0
        total_samples = 0
        
        for batch_idx, (features, targets) in enumerate(train_loader):
            features = features.to(self.device)
            targets = targets.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(features)
            
            # Handle output shape (flatten if needed)
            if outputs.dim() > targets.dim():
                outputs = outputs.view_as(targets)
            
            loss = self.criterion(outputs, targets)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            if self.config.gradient_clip_norm:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    self.config.gradient_clip_norm
                )
            
            self.optimizer.step()
            
            # Track metrics
            total_loss += loss.item()
            total_samples += len(features)
            
            # Calculate accuracy (for classification tasks)
            # For regression, we skip accuracy
            if targets.dim() == 1 or targets.shape[1] == 1:
                # Regression task - use MAE as "accuracy"
                with torch.no_grad():
                    mae = torch.mean(torch.abs(outputs - targets)).item()
                    # Convert to "accuracy-like" metric (inverse of error)
                    total_correct += (1.0 - min(mae, 1.0)) * len(features)
            
            # Log progress
            if (batch_idx + 1) % max(1, len(train_loader) // 5) == 0:
                logger.debug(
                    f"Epoch {epoch}, Batch {batch_idx+1}/{len(train_loader)}, "
                    f"Loss: {loss.item():.4f}"
                )
        
        avg_loss = total_loss / len(train_loader)
        avg_accuracy = total_correct / total_samples if total_samples > 0 else None
        
        return avg_loss, avg_accuracy
    
    def validate(
        self,
        val_loader: Any  # DataLoader when PyTorch available
    ) -> Tuple[float, Optional[float]]:
        """
        Validate model.
        
        Args:
            val_loader: Validation data loader
            
        Returns:
            Tuple of (average_loss, average_accuracy)
        """
        self.model.eval()
        total_loss = 0.0
        total_correct = 0
        total_samples = 0
        
        with torch.no_grad():
            for features, targets in val_loader:
                features = features.to(self.device)
                targets = targets.to(self.device)
                
                outputs = self.model(features)
                
                # Handle output shape
                if outputs.dim() > targets.dim():
                    outputs = outputs.view_as(targets)
                
                loss = self.criterion(outputs, targets)
                total_loss += loss.item()
                total_samples += len(features)
                
                # Accuracy for regression (similar to training)
                if targets.dim() == 1 or targets.shape[1] == 1:
                    mae = torch.mean(torch.abs(outputs - targets)).item()
                    total_correct += (1.0 - min(mae, 1.0)) * len(features)
        
        avg_loss = total_loss / len(val_loader)
        avg_accuracy = total_correct / total_samples if total_samples > 0 else None
        
        return avg_loss, avg_accuracy
    
    def train(
        self,
        features: np.ndarray,
        targets: np.ndarray,
        callbacks: Optional[List[Callable]] = None
    ) -> List[TrainingMetrics]:
        """
        Train the model.
        
        Args:
            features: Feature matrix (n_samples, n_features)
            targets: Target values (n_samples,) or (n_samples, n_outputs)
            callbacks: Optional list of callback functions (called after each epoch)
            
        Returns:
            List of training metrics for each epoch
        """
        logger.info(f"Starting training pipeline: {self.config.num_epochs} epochs")
        
        # Prepare data
        train_loader, val_loader = self.prepare_data(features, targets)
        
        # Training loop
        for epoch in range(1, self.config.num_epochs + 1):
            # Train
            train_loss, train_acc = self.train_epoch(train_loader, epoch)
            
            # Validate
            val_loss = None
            val_acc = None
            if val_loader:
                val_loss, val_acc = self.validate(val_loader)
                
                # Update learning rate scheduler
                self.scheduler.step(val_loss)
                
                # Early stopping check
                if self.config.early_stopping_patience > 0:
                    if self.best_val_loss is None or val_loss < self.best_val_loss - self.config.min_delta:
                        self.best_val_loss = val_loss
                        self.epochs_without_improvement = 0
                        
                        # Save best model
                        if self.config.save_best_model:
                            self.best_model_state = {
                                'epoch': epoch,
                                'model_state_dict': self.model.state_dict(),
                                'optimizer_state_dict': self.optimizer.state_dict(),
                                'val_loss': val_loss
                            }
                    else:
                        self.epochs_without_improvement += 1
                        
                        if self.epochs_without_improvement >= self.config.early_stopping_patience:
                            logger.info(f"Early stopping at epoch {epoch}")
                            break
            
            # Record metrics
            current_lr = self.optimizer.param_groups[0]['lr']
            metrics = TrainingMetrics(
                epoch=epoch,
                train_loss=train_loss,
                val_loss=val_loss,
                train_accuracy=train_acc,
                val_accuracy=val_acc,
                learning_rate=current_lr
            )
            self.training_history.append(metrics)
            
            # Log progress
            log_msg = (
                f"Epoch {epoch}/{self.config.num_epochs}: "
                f"Train Loss: {train_loss:.4f}"
            )
            if val_loss is not None:
                log_msg += f", Val Loss: {val_loss:.4f}"
            if train_acc is not None:
                log_msg += f", Train Acc: {train_acc:.4f}"
            if val_acc is not None:
                log_msg += f", Val Acc: {val_acc:.4f}"
            log_msg += f", LR: {current_lr:.6f}"
            logger.info(log_msg)
            
            # Save checkpoint
            if self.config.save_checkpoints and epoch % self.config.checkpoint_interval == 0:
                self.save_checkpoint(f"checkpoint_epoch_{epoch}.pt")
            
            # Callbacks
            if callbacks:
                for callback in callbacks:
                    try:
                        callback(epoch, metrics, self.model)
                    except Exception as e:
                        logger.warning(f"Callback failed: {e}")
        
        # Restore best model
        if self.config.save_best_model and self.best_model_state:
            logger.info("Restoring best model")
            self.model.load_state_dict(self.best_model_state['model_state_dict'])
        
        logger.info("Training completed")
        return self.training_history
    
    def save_checkpoint(self, filepath: str) -> None:
        """Save model checkpoint."""
        checkpoint = {
            'epoch': len(self.training_history),
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config,
            'training_history': self.training_history,
            'best_val_loss': self.best_val_loss
        }
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        torch.save(checkpoint, path)
        logger.info(f"Saved checkpoint to {filepath}")
    
    def load_checkpoint(self, filepath: str) -> None:
        """Load model checkpoint."""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.training_history = checkpoint.get('training_history', [])
        self.best_val_loss = checkpoint.get('best_val_loss')
        
        logger.info(f"Loaded checkpoint from {filepath}")
    
    def get_training_summary(self) -> Dict[str, Any]:
        """Get training summary."""
        if not self.training_history:
            return {"status": "not_trained"}
        
        latest = self.training_history[-1]
        
        return {
            "total_epochs": len(self.training_history),
            "final_train_loss": latest.train_loss,
            "final_val_loss": latest.val_loss,
            "best_val_loss": self.best_val_loss,
            "training_complete": True,
            "metrics": [
                {
                    "epoch": m.epoch,
                    "train_loss": m.train_loss,
                    "val_loss": m.val_loss,
                    "learning_rate": m.learning_rate
                }
                for m in self.training_history
            ]
        }

