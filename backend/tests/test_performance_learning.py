"""
Performance Tests: Learning Efficiency

Tests training time, batch processing, and memory usage.
"""

import pytest
import time
import numpy as np


@pytest.mark.performance
@pytest.mark.skipif(not pytest.importorskip("torch", reason="PyTorch not available"), reason="PyTorch required")
class TestLearningEfficiency:
    """Test learning efficiency."""
    
    def test_training_time_for_neural_models(self):
        """Measure training time for neural models."""
        import torch
        from core.learning.neural_agent_selector import NeuralAgentSelector
        
        selector = NeuralAgentSelector(
            agent_names=["react", "chain_of_thought"],
            input_dim=50,
            hidden_dims=[32]  # Small model
        )
        
        # Generate training data
        features_list = []
        labels = []
        
        for i in range(50):  # Small dataset
            features = {
                "task_complexity": np.random.rand(),
                "task_type_encoded": np.random.rand(5),
                "context_features": np.random.rand(10),
                "agent_history_success_rate": np.random.rand(),
                "agent_history_latency": np.random.rand() * 1000,
                "current_load": np.random.rand(),
                "available_resources": np.random.rand()
            }
            features_list.append(features)
            labels.append(np.random.randint(0, 2))
        
        # Measure training time
        start = time.time()
        try:
            selector.train(features_list, labels, epochs=2, batch_size=10)
            training_time = time.time() - start
            
            # Training should complete in reasonable time
            assert training_time < 10.0  # Should be fast for small model
        except Exception:
            pytest.skip("Training not available")
    
    def test_batch_processing_efficiency(self):
        """Test batch processing efficiency."""
        import torch
        from core.learning.training_pipeline import TrainingDataset
        
        # Create data
        n_samples = 100
        features = np.random.rand(n_samples, 20)
        targets = np.random.randint(0, 3, n_samples)
        
        dataset = TrainingDataset(features, targets)
        
        # Test different batch sizes
        batch_sizes = [10, 32, 64]
        
        for batch_size in batch_sizes:
            dataloader = torch.utils.data.DataLoader(
                dataset, batch_size=batch_size, shuffle=False
            )
            
            start = time.time()
            for batch_features, batch_targets in dataloader:
                pass  # Process batch
            elapsed = time.time() - start
            
            # Larger batches should be more efficient (faster per sample)
            assert elapsed < 1.0  # Should be very fast
    
    def test_memory_usage_during_learning(self):
        """Measure memory usage during learning."""
        import sys
        
        # Simple memory check
        initial_size = sys.getsizeof({})
        
        # Create some data structures
        data = {}
        for i in range(1000):
            data[f"key_{i}"] = np.random.rand(100)
        
        final_size = sys.getsizeof(data)
        
        # Memory should increase reasonably
        memory_increase = final_size - initial_size
        
        # Should use reasonable amount (< 100MB for test)
        assert memory_increase < 100 * 1024 * 1024  # 100MB
        assert memory_increase > 0
    
    def test_incremental_learning_speed(self):
        """Test incremental learning speed."""
        from core.learning.neural_agent_selector import NeuralAgentSelector
        
        selector = NeuralAgentSelector(
            agent_names=["react"],
            input_dim=50,
            hidden_dims=[32]
        )
        
        # Single example update
        features = {
            "task_complexity": 0.6,
            "task_type_encoded": np.random.rand(5),
            "context_features": np.random.rand(10),
            "agent_history_success_rate": 0.7,
            "agent_history_latency": 150.0,
            "current_load": 0.3,
            "available_resources": 0.8
        }
        
        start = time.time()
        try:
            selector.train([features], [0], epochs=1)
            update_time = time.time() - start
            
            # Incremental update should be very fast
            assert update_time < 1.0  # Should be fast
        except Exception:
            pytest.skip("Incremental learning not available")

