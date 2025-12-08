
"""
Tests for the online learning module.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import json

from core.online_learning import (
    AgentPerformanceModel,
    RealTimeModelUpdater,
    ModelType,
    UpdateStrategy,
    get_model_updater
)
from core.feedback_pipeline import OutcomeEvent, OutcomeStatus, EventSeverity


@pytest.fixture
def sample_outcome_event():
    """Create a sample outcome event."""
    return OutcomeEvent(
        event_id="evt_123",
        run_id="run_456",
        agent_name="ReActAgent",
        agent_type="react",
        action_type="analysis",
        timestamp=datetime.utcnow().isoformat(),
        start_time=datetime.utcnow().isoformat(),
        end_time=datetime.utcnow().isoformat(),
        duration_ms=1500.0,
        status=OutcomeStatus.SUCCESS,
        severity=EventSeverity.INFO,
        latency_ms=1200.0,
        quality_score=0.85,
        confidence_score=0.9
    )


@pytest.fixture
def agent_model():
    """Create an agent performance model."""
    return AgentPerformanceModel()


class TestAgentPerformanceModel:
    """Tests for AgentPerformanceModel."""
    
    def test_initialization(self, agent_model):
        """Test model initialization."""
        assert agent_model.model_id == "agent_perf_v1"
        assert agent_model.update_count == 0
        assert len(agent_model.agent_stats) == 0
    
    def test_update_with_success(self, agent_model, sample_outcome_event):
        """Test updating model with successful outcome."""
        agent_model.update(sample_outcome_event)
        
        stats = agent_model.agent_stats["ReActAgent"]
        assert stats['successes'] == 1
        assert stats['failures'] == 0
        assert len(stats['latencies']) == 1
        assert agent_model.update_count == 1
    
    def test_update_with_failure(self, agent_model, sample_outcome_event):
        """Test updating model with failed outcome."""
        sample_outcome_event.status = OutcomeStatus.FAILURE
        agent_model.update(sample_outcome_event)
        
        stats = agent_model.agent_stats["ReActAgent"]
        assert stats['successes'] == 0
        assert stats['failures'] == 1
    
    def test_success_rate_calculation(self, agent_model, sample_outcome_event):
        """Test success rate calculation."""
        # Add 3 successes
        for _ in range(3):
            sample_outcome_event.status = OutcomeStatus.SUCCESS
            agent_model.update(sample_outcome_event)
        
        # Add 1 failure
        sample_outcome_event.status = OutcomeStatus.FAILURE
        agent_model.update(sample_outcome_event)
        
        success_rate = agent_model.get_success_rate("ReActAgent")
        assert success_rate == 0.75  # 3/4
    
    def test_avg_latency_calculation(self, agent_model, sample_outcome_event):
        """Test average latency calculation."""
        latencies = [100.0, 200.0, 300.0]
        
        for latency in latencies:
            sample_outcome_event.latency_ms = latency
            agent_model.update(sample_outcome_event)
        
        avg_latency = agent_model.get_avg_latency("ReActAgent")
        assert avg_latency == 200.0
    
    def test_predict_best_agent(self, agent_model, sample_outcome_event):
        """Test agent prediction."""
        # Add data for multiple agents
        agents = ["ReActAgent", "DebateAgent", "GovernorAgent"]
        
        for agent in agents:
            sample_outcome_event.agent_name = agent
            for _ in range(5):
                agent_model.update(sample_outcome_event)
        
        predictions = agent_model.predict_best_agent(top_k=2)
        
        assert len(predictions) == 2
        assert all(isinstance(p, tuple) for p in predictions)
        assert all(len(p) == 2 for p in predictions)
    
    def test_task_specific_patterns(self, agent_model, sample_outcome_event):
        """Test task-specific pattern learning."""
        sample_outcome_event.action_type = "analysis"
        agent_model.update(sample_outcome_event)
        
        assert "analysis" in agent_model.task_patterns
        assert "ReActAgent" in agent_model.task_patterns["analysis"]
    
    def test_to_dict(self, agent_model, sample_outcome_event):
        """Test model serialization."""
        agent_model.update(sample_outcome_event)
        
        data = agent_model.to_dict()
        
        assert 'model_id' in data
        assert 'agent_stats' in data
        assert 'update_count' in data
        assert data['update_count'] == 1


@pytest.mark.skipif(
    not hasattr(pytest, 'kafka_available') or not pytest.kafka_available,
    reason="Kafka not available"
)
class TestRealTimeModelUpdater:
    """Tests for RealTimeModelUpdater."""
    
    @pytest.fixture
    def updater(self, tmp_path):
        """Create a model updater instance."""
        with patch('core.online_learning.KafkaConsumer'):
            updater = RealTimeModelUpdater(
                kafka_servers="localhost:9092",
                batch_size=5,
                batch_timeout_seconds=10,
                model_storage_path=str(tmp_path / "models")
            )
            return updater
    
    def test_initialization(self, updater):
        """Test updater initialization."""
        assert updater.batch_size == 5
        assert updater.batch_timeout_seconds == 10
        assert ModelType.AGENT_SELECTION in updater.models
        assert not updater.running
    
    def test_model_persistence(self, updater, sample_outcome_event):
        """Test model saving and loading."""
        # Update model
        model = updater.get_model(ModelType.AGENT_SELECTION)
        model.update(sample_outcome_event)
        
        # Save
        updater._save_models()
        
        # Create new updater and load
        with patch('core.online_learning.KafkaConsumer'):
            new_updater = RealTimeModelUpdater(
                kafka_servers="localhost:9092",
                model_storage_path=str(updater.model_storage_path)
            )
        
        loaded_model = new_updater.get_model(ModelType.AGENT_SELECTION)
        assert loaded_model.update_count == 1
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, updater, sample_outcome_event):
        """Test batch processing of events."""
        events = [sample_outcome_event for _ in range(3)]
        
        await updater._process_batch(events)
        
        assert updater.metrics.total_updates == 1
        assert updater.metrics.samples_processed == 3
    
    def test_get_metrics(self, updater, sample_outcome_event):
        """Test metrics retrieval."""
        model = updater.get_model(ModelType.AGENT_SELECTION)
        model.update(sample_outcome_event)
        
        metrics = updater.get_metrics()
        
        assert 'total_updates' in metrics
        assert 'samples_processed' in metrics
        assert 'model_agent_selection' in metrics
    
    def test_prediction(self, updater, sample_outcome_event):
        """Test making predictions."""
        model = updater.get_model(ModelType.AGENT_SELECTION)
        
        # Add some data
        for _ in range(5):
            model.update(sample_outcome_event)
        
        predictions = updater.predict(
            ModelType.AGENT_SELECTION,
            task_type="analysis",
            top_k=1
        )
        
        assert len(predictions) == 1
        assert predictions[0][0] == "ReActAgent"


def test_get_model_updater_singleton():
    """Test singleton pattern for model updater."""
    with patch('core.online_learning.KAFKA_AVAILABLE', True):
        with patch('core.online_learning.KafkaConsumer'):
            updater1 = get_model_updater(
                kafka_servers="localhost:9092",
                force_new=True
            )
            updater2 = get_model_updater(kafka_servers="localhost:9092")
            
            assert updater1 is updater2


def test_get_model_updater_without_kafka():
    """Test model updater when Kafka is not available."""
    with patch('core.online_learning.KAFKA_AVAILABLE', False):
        updater = get_model_updater()
        assert updater is None
