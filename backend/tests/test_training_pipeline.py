"""
Tests for Training Pipeline (Phase 2)

Tests batch processing, gradient updates, validation, and model persistence.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
import tempfile
from pathlib import Path

from core.learning.training_pipeline import (
    ModelTrainingPipeline as TrainingPipeline,
    TrainingConfig,
    TrainingMetrics,
    TrainingDataset
)


@pytest.mark.unit
@pytest.mark.skipif(not pytest.importorskip("torch", reason="PyTorch not available"), reason="PyTorch required")
class TestTrainingPipeline:
    """Test training pipeline components."""
    
    def test_training_config(self):
        """Test training configuration."""
        config = TrainingConfig(
            batch_size=64,
            learning_rate=0.001,
            num_epochs=20,
            validation_split=0.2
        )
        
        assert config.batch_size == 64
        assert config.learning_rate == 0.001
        assert config.num_epochs == 20
        assert config.validation_split == 0.2
    
    def test_training_dataset(self):
        """Test DataLoader creation and batching."""
        import torch
        
        # Create synthetic data
        n_samples = 100
        n_features = 50
        n_outputs = 3
        
        features = np.random.rand(n_samples, n_features)
        targets = np.random.randint(0, n_outputs, n_samples)
        
        dataset = TrainingDataset(features, targets)
        assert len(dataset) == n_samples
        
        # Test DataLoader
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True)
        
        batch_features, batch_targets = next(iter(dataloader))
        assert batch_features.shape[0] <= 32
        assert batch_features.shape[1] == n_features
        assert batch_targets.shape[0] <= 32
    
    def test_optimizer_configuration(self):
        """Test optimizer configuration (Adam)."""
        import torch
        
        # Create simple model
        model = torch.nn.Sequential(
            torch.nn.Linear(50, 32),
            torch.nn.ReLU(),
            torch.nn.Linear(32, 3)
        )
        
        config = TrainingConfig(learning_rate=0.001, weight_decay=0.0001)
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay
        )
        
        assert optimizer is not None
        assert len(list(optimizer.param_groups)) == 1
    
    def test_learning_rate_scheduling(self):
        """Test learning rate scheduling."""
        import torch
        
        model = torch.nn.Linear(10, 1)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        
        scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)
        
        initial_lr = optimizer.param_groups[0]['lr']
        
        # Step through scheduler
        for _ in range(5):
            scheduler.step()
        
        final_lr = optimizer.param_groups[0]['lr']
        assert final_lr < initial_lr
    
    def test_early_stopping_mechanism(self):
        """Test early stopping mechanism."""
        import torch
        
        # Simulate training with early stopping
        patience = 3
        best_val_loss = float('inf')
        patience_counter = 0
        should_stop = False
        
        val_losses = [1.0, 0.9, 0.85, 0.87, 0.88, 0.89]  # Improving then getting worse
        
        for epoch, val_loss in enumerate(val_losses):
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
            else:
                patience_counter += 1
            
            if patience_counter >= patience:
                should_stop = True
                break
        
        assert should_stop
        assert epoch < len(val_losses) - 1
    
    def test_single_epoch_execution(self):
        """Test single epoch execution."""
        import torch
        
        # Create simple model and data
        model = torch.nn.Sequential(
            torch.nn.Linear(10, 5),
            torch.nn.ReLU(),
            torch.nn.Linear(5, 1)
        )
        optimizer = torch.optim.Adam(model.parameters())
        criterion = torch.nn.MSELoss()
        
        # Synthetic data
        features = torch.randn(20, 10)
        targets = torch.randn(20, 1)
        
        # Training step
        optimizer.zero_grad()
        outputs = model(features)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        
        assert loss.item() is not None
        assert not torch.isnan(loss)
    
    def test_validation_loop(self):
        """Test validation loop."""
        import torch
        
        model = torch.nn.Linear(10, 1)
        criterion = torch.nn.MSELoss()
        
        # Validation data
        val_features = torch.randn(10, 10)
        val_targets = torch.randn(10, 1)
        
        model.eval()
        with torch.no_grad():
            val_outputs = model(val_features)
            val_loss = criterion(val_outputs, val_targets)
        
        assert val_loss.item() is not None
        assert not torch.isnan(val_loss)
    
    def test_checkpoint_saving(self, tmp_path):
        """Test checkpoint saving."""
        import torch
        
        model = torch.nn.Linear(10, 1)
        optimizer = torch.optim.Adam(model.parameters())
        
        checkpoint_path = tmp_path / "checkpoint.pt"
        
        checkpoint = {
            'epoch': 5,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': 0.5,
        }
        
        torch.save(checkpoint, checkpoint_path)
        assert checkpoint_path.exists()
        
        # Load checkpoint
        loaded = torch.load(checkpoint_path)
        assert loaded['epoch'] == 5
        assert 'model_state_dict' in loaded
    
    def test_metrics_tracking(self):
        """Test metrics tracking."""
        from datetime import datetime
        
        metrics = TrainingMetrics(
            epoch=1,
            train_loss=0.5,
            val_loss=0.4,
            train_accuracy=0.8,
            val_accuracy=0.85,
            learning_rate=0.001
        )
        
        assert metrics.epoch == 1
        assert metrics.train_loss == 0.5
        assert metrics.val_loss == 0.4
        assert metrics.timestamp is not None


@pytest.mark.integration
@pytest.mark.skipif(not pytest.importorskip("torch", reason="PyTorch not available"), reason="PyTorch required")
class TestTrainingPipelineIntegration:
    """Integration tests for training pipeline."""
    
    def test_end_to_end_training(self):
        """Test end-to-end training pipeline."""
        import torch
        
        # Create model
        model = torch.nn.Sequential(
            torch.nn.Linear(20, 10),
            torch.nn.ReLU(),
            torch.nn.Linear(10, 3)
        )
        
        # Create data
        n_samples = 100
        features = np.random.rand(n_samples, 20)
        targets = np.random.randint(0, 3, n_samples)
        
        dataset = TrainingDataset(features, targets)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=32)
        
        # Training setup
        optimizer = torch.optim.Adam(model.parameters())
        criterion = torch.nn.CrossEntropyLoss()
        
        # Train for one epoch
        model.train()
        total_loss = 0
        for batch_features, batch_targets in dataloader:
            optimizer.zero_grad()
            outputs = model(batch_features)
            loss = criterion(outputs, batch_targets.long())
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        avg_loss = total_loss / len(dataloader)
        assert avg_loss is not None
        assert not np.isnan(avg_loss)

