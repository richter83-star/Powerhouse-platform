"""
Tests for Meta-Learning System (Phase 4)

Tests meta-learner initialization, strategy prediction, and transfer learning.
"""

import pytest
import numpy as np
from datetime import datetime

from core.learning.meta_learning import MetaLearner


@pytest.mark.unit
class TestMetaLearner:
    """Test meta-learner."""
    
    def test_initialization(self):
        """Test task memory setup and strategy registry."""
        learner = MetaLearner()
        
        assert learner is not None
        assert learner.model_id is not None
        assert len(learner.strategies) > 0
        assert learner.task_memory == {}
    
    def test_learn_from_task(self):
        """Test learn_from_task() with various task types."""
        learner = MetaLearner()
        
        task_id = learner.learn_from_task(
            task_type="reasoning",
            task_description="Solve complex math problem",
            domain="mathematics",
            learning_curve=[0.5, 0.7, 0.85, 0.92],
            final_performance=0.92,
            hyperparameters={"learning_rate": 0.001, "batch_size": 32}
        )
        
        assert task_id is not None
        assert task_id in learner.task_memory
    
    def test_task_embedding_generation(self):
        """Test task embedding generation."""
        learner = MetaLearner()
        
        # Learn from task
        task_id = learner.learn_from_task(
            task_type="reasoning",
            task_description="Test task",
            domain="test",
            learning_curve=[0.5, 0.7],
            final_performance=0.7,
            hyperparameters={}
        )
        
        # Should have task in memory
        assert task_id in learner.task_memory
        
        # Features should be extractable
        task_meta = learner.task_memory[task_id]
        features = learner._extract_task_features(task_meta)
        assert len(features) > 0
    
    def test_sample_efficiency_calculation(self):
        """Test sample efficiency calculation."""
        learner = MetaLearner()
        
        # Test with different learning curves
        curve1 = [0.5, 0.7, 0.85, 0.92]  # Good efficiency
        efficiency1 = learner._calculate_sample_efficiency(curve1)
        
        curve2 = [0.1, 0.2, 0.3, 0.92]  # Poor efficiency until end
        efficiency2 = learner._calculate_sample_efficiency(curve2)
        
        assert 0.0 <= efficiency1 <= 1.0
        assert 0.0 <= efficiency2 <= 1.0
        # First curve should be more efficient
        assert efficiency1 > efficiency2
    
    def test_predict_strategy_for_new_task(self):
        """Test predict_strategy() for new tasks."""
        learner = MetaLearner()
        
        # Learn from a few tasks first
        learner.learn_from_task(
            task_type="reasoning",
            task_description="Math problem",
            domain="mathematics",
            learning_curve=[0.6, 0.8, 0.9],
            final_performance=0.9,
            hyperparameters={"learning_rate": 0.001}
        )
        
        # Predict strategy for similar task
        strategy, confidence, hyperparams = learner.predict_strategy(
            task_description="Another math problem",
            domain="mathematics"
        )
        
        assert strategy is not None
        assert 0.0 <= confidence <= 1.0
        assert isinstance(hyperparams, dict)
    
    def test_similarity_matching(self):
        """Test similarity matching to past tasks."""
        learner = MetaLearner()
        
        # Add several tasks
        task_ids = []
        for i in range(5):
            task_id = learner.learn_from_task(
                task_type="reasoning",
                task_description=f"Task {i}",
                domain="test",
                learning_curve=[0.5 + i * 0.1],
                final_performance=0.5 + i * 0.1,
                hyperparameters={}
            )
            task_ids.append(task_id)
        
        # Find similar tasks
        similar = learner._find_similar_tasks(
            task_description="Task 2",
            domain="test",
            top_k=3
        )
        
        assert len(similar) > 0
        assert len(similar) <= 3
    
    def test_hyperparameter_recommendations(self):
        """Test hyperparameter recommendations."""
        learner = MetaLearner()
        
        # Learn from tasks with different hyperparameters
        learner.learn_from_task(
            task_type="reasoning",
            task_description="Task 1",
            domain="test",
            learning_curve=[0.8, 0.9],
            final_performance=0.9,
            hyperparameters={"learning_rate": 0.001, "batch_size": 32}
        )
        
        learner.learn_from_task(
            task_type="reasoning",
            task_description="Task 2",
            domain="test",
            learning_curve=[0.7, 0.85],
            final_performance=0.85,
            hyperparameters={"learning_rate": 0.0005, "batch_size": 64}
        )
        
        # Predict hyperparameters
        _, _, hyperparams = learner.predict_strategy(
            task_description="Similar task",
            domain="test"
        )
        
        assert isinstance(hyperparams, dict)
        assert len(hyperparams) > 0
    
    def test_transfer_learning(self):
        """Test knowledge transfer between domains."""
        learner = MetaLearner()
        
        # Learn from source domain
        learner.learn_from_task(
            task_type="reasoning",
            task_description="Source task",
            domain="source",
            learning_curve=[0.8, 0.9],
            final_performance=0.9,
            hyperparameters={"learning_rate": 0.001}
        )
        
        # Transfer to target domain
        transfer_config = learner.transfer_knowledge(
            source_domain="source",
            target_domain="target",
            source_model=None  # Would be actual model in production
        )
        
        assert transfer_config is not None
        assert isinstance(transfer_config, dict)
    
    def test_strategy_selection_accuracy(self):
        """Test strategy selection accuracy."""
        learner = MetaLearner()
        
        # Learn from tasks using different strategies
        for strategy in ["few_shot", "transfer", "maml"]:
            learner.learn_from_task(
                task_type="reasoning",
                task_description=f"Task with {strategy}",
                domain="test",
                learning_curve=[0.6, 0.8],
                final_performance=0.8,
                hyperparameters={"strategy": strategy}
            )
        
        # Predict strategy
        strategy, confidence, _ = learner.predict_strategy(
            task_description="New reasoning task",
            domain="test"
        )
        
        assert strategy in learner.strategies
        assert confidence >= 0.0

