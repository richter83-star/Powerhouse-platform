
"""
Unit tests for the Real-Time Feedback Pipeline.

Tests cover:
- OutcomeEvent creation and serialization
- FeedbackPipeline event recording
- KafkaPublisher (mocked)
- ActionDispatcher execution tracking
- OrchestrationDispatcher workflow tracking
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from core.feedback_pipeline import (
    OutcomeEvent,
    OutcomeStatus,
    EventSeverity,
    FeedbackPipeline,
    KafkaPublisher,
    get_feedback_pipeline
)
from core.action_dispatcher import (
    ActionDispatcher,
    OrchestrationDispatcher,
    create_dispatcher
)
from core.base_agent import BaseAgent


# Test Agent Implementation
class TestAgent(BaseAgent):
    """Simple test agent."""
    
    def __init__(self, name="test_agent", should_fail=False):
        super().__init__(
            name=name,
            agent_type="test",
            capabilities=["testing"]
        )
        self.should_fail = should_fail
        self.execution_count = 0
    
    def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent."""
        self.execution_count += 1
        
        if self.should_fail:
            raise ValueError("Test failure")
        
        return {
            "status": "success",
            "output": f"Processed: {input_data.get('task', 'N/A')}",
            "metadata": {
                "tokens_used": 100,
                "llm_latency_ms": 150.5
            }
        }


# ============================================================================
# OutcomeEvent Tests
# ============================================================================

def test_outcome_event_creation():
    """Test OutcomeEvent creation."""
    event = OutcomeEvent(
        event_id="test-123",
        run_id="run-456",
        agent_name="test_agent",
        agent_type="test",
        action_type="test_action",
        timestamp=datetime.utcnow().isoformat(),
        start_time=datetime.utcnow().isoformat(),
        end_time=datetime.utcnow().isoformat(),
        duration_ms=100.5,
        status=OutcomeStatus.SUCCESS,
        severity=EventSeverity.INFO,
        latency_ms=100.5
    )
    
    assert event.event_id == "test-123"
    assert event.agent_name == "test_agent"
    assert event.status == OutcomeStatus.SUCCESS
    assert event.severity == EventSeverity.INFO


def test_outcome_event_to_dict():
    """Test OutcomeEvent serialization to dict."""
    event = OutcomeEvent(
        event_id="test-123",
        run_id="run-456",
        agent_name="test_agent",
        agent_type="test",
        action_type="test_action",
        timestamp=datetime.utcnow().isoformat(),
        start_time=datetime.utcnow().isoformat(),
        end_time=datetime.utcnow().isoformat(),
        duration_ms=100.5,
        status=OutcomeStatus.SUCCESS,
        severity=EventSeverity.INFO,
        latency_ms=100.5
    )
    
    data = event.to_dict()
    
    assert isinstance(data, dict)
    assert data["event_id"] == "test-123"
    assert data["status"] == "success"
    assert data["severity"] == "info"


def test_outcome_event_to_json():
    """Test OutcomeEvent serialization to JSON."""
    event = OutcomeEvent(
        event_id="test-123",
        run_id="run-456",
        agent_name="test_agent",
        agent_type="test",
        action_type="test_action",
        timestamp=datetime.utcnow().isoformat(),
        start_time=datetime.utcnow().isoformat(),
        end_time=datetime.utcnow().isoformat(),
        duration_ms=100.5,
        status=OutcomeStatus.SUCCESS,
        severity=EventSeverity.INFO,
        latency_ms=100.5
    )
    
    json_str = event.to_json()
    
    assert isinstance(json_str, str)
    assert '"event_id": "test-123"' in json_str
    assert '"status": "success"' in json_str


# ============================================================================
# FeedbackPipeline Tests
# ============================================================================

@pytest.mark.asyncio
async def test_feedback_pipeline_record_outcome():
    """Test recording an outcome to the pipeline."""
    pipeline = FeedbackPipeline(
        kafka_servers=None,  # No Kafka for testing
        enable_kafka=False,
        enable_logging=True
    )
    
    event = OutcomeEvent(
        event_id="test-123",
        run_id="run-456",
        agent_name="test_agent",
        agent_type="test",
        action_type="test_action",
        timestamp=datetime.utcnow().isoformat(),
        start_time=datetime.utcnow().isoformat(),
        end_time=datetime.utcnow().isoformat(),
        duration_ms=100.5,
        status=OutcomeStatus.SUCCESS,
        severity=EventSeverity.INFO,
        latency_ms=100.5
    )
    
    await pipeline.record_outcome(event)
    
    # Check buffer
    recent = pipeline.get_recent_events(count=10)
    assert len(recent) == 1
    assert recent[0].event_id == "test-123"


def test_feedback_pipeline_get_recent_events():
    """Test querying recent events."""
    pipeline = FeedbackPipeline(
        kafka_servers=None,
        enable_kafka=False
    )
    
    # Add events to buffer directly
    for i in range(5):
        event = OutcomeEvent(
            event_id=f"test-{i}",
            run_id="run-456",
            agent_name=f"agent_{i % 2}",  # Alternate agents
            agent_type="test",
            action_type="test_action",
            timestamp=datetime.utcnow().isoformat(),
            start_time=datetime.utcnow().isoformat(),
            end_time=datetime.utcnow().isoformat(),
            duration_ms=100.5,
            status=OutcomeStatus.SUCCESS if i % 2 == 0 else OutcomeStatus.FAILURE,
            severity=EventSeverity.INFO,
            latency_ms=100.5
        )
        pipeline._event_buffer.append(event)
    
    # Get all recent
    recent = pipeline.get_recent_events(count=10)
    assert len(recent) == 5
    
    # Filter by agent
    agent_events = pipeline.get_recent_events(count=10, agent_name="agent_0")
    assert len(agent_events) == 3  # events 0, 2, 4
    
    # Filter by status
    failures = pipeline.get_recent_events(count=10, status=OutcomeStatus.FAILURE)
    assert len(failures) == 2  # events 1, 3


def test_feedback_pipeline_metrics():
    """Test pipeline metrics."""
    pipeline = FeedbackPipeline(
        kafka_servers=None,
        enable_kafka=False
    )
    
    metrics = pipeline.get_metrics()
    
    assert "buffer_size" in metrics
    assert "buffer_max_size" in metrics
    assert metrics["buffer_size"] == 0


# ============================================================================
# ActionDispatcher Tests
# ============================================================================

@pytest.mark.asyncio
async def test_action_dispatcher_success():
    """Test successful action dispatch."""
    pipeline = FeedbackPipeline(kafka_servers=None, enable_kafka=False)
    dispatcher = ActionDispatcher(feedback_pipeline=pipeline)
    
    agent = TestAgent()
    
    result = await dispatcher.dispatch(
        agent=agent,
        action_type="test_action",
        input_data={"task": "test task"},
        context={}
    )
    
    # Check result
    assert result["status"] == "success"
    assert "output" in result
    assert "event_id" in result
    assert "run_id" in result
    assert "duration_ms" in result
    assert result["duration_ms"] > 0
    
    # Check agent was executed
    assert agent.execution_count == 1
    
    # Check event was recorded
    recent = pipeline.get_recent_events(count=10)
    assert len(recent) == 1
    assert recent[0].status == OutcomeStatus.SUCCESS


@pytest.mark.asyncio
async def test_action_dispatcher_failure():
    """Test failed action dispatch."""
    pipeline = FeedbackPipeline(kafka_servers=None, enable_kafka=False)
    dispatcher = ActionDispatcher(feedback_pipeline=pipeline)
    
    agent = TestAgent(should_fail=True)
    
    result = await dispatcher.dispatch(
        agent=agent,
        action_type="test_action",
        input_data={"task": "test task"},
        context={}
    )
    
    # Check result
    assert result["status"] == "failure"
    assert "error" in result
    assert result["error"] == "Test failure"
    
    # Check event was recorded
    recent = pipeline.get_recent_events(count=10)
    assert len(recent) == 1
    assert recent[0].status == OutcomeStatus.FAILURE
    assert recent[0].error_message == "Test failure"
    assert recent[0].error_type == "ValueError"


@pytest.mark.asyncio
async def test_action_dispatcher_with_tags():
    """Test dispatch with tags."""
    pipeline = FeedbackPipeline(kafka_servers=None, enable_kafka=False)
    dispatcher = ActionDispatcher(feedback_pipeline=pipeline)
    
    agent = TestAgent()
    
    result = await dispatcher.dispatch(
        agent=agent,
        action_type="test_action",
        input_data={"task": "test task"},
        context={},
        tags=["tag1", "tag2", "priority-high"]
    )
    
    # Check event has tags
    recent = pipeline.get_recent_events(count=10)
    assert len(recent) == 1
    assert recent[0].tags == ["tag1", "tag2", "priority-high"]


@pytest.mark.asyncio
async def test_action_dispatcher_hooks():
    """Test pre and post execution hooks."""
    pipeline = FeedbackPipeline(kafka_servers=None, enable_kafka=False)
    dispatcher = ActionDispatcher(feedback_pipeline=pipeline)
    
    # Track hook calls
    pre_called = []
    post_called = []
    
    async def pre_hook(agent, input_data, context):
        pre_called.append(agent.name)
    
    async def post_hook(agent, result, event):
        post_called.append((agent.name, result["status"]))
    
    dispatcher.add_pre_hook(pre_hook)
    dispatcher.add_post_hook(post_hook)
    
    agent = TestAgent()
    
    await dispatcher.dispatch(
        agent=agent,
        action_type="test_action",
        input_data={"task": "test"},
        context={}
    )
    
    # Check hooks were called
    assert len(pre_called) == 1
    assert pre_called[0] == "test_agent"
    assert len(post_called) == 1
    assert post_called[0] == ("test_agent", "success")


# ============================================================================
# OrchestrationDispatcher Tests
# ============================================================================

@pytest.mark.asyncio
async def test_orchestration_dispatcher_workflow():
    """Test multi-agent workflow orchestration."""
    orchestrator = OrchestrationDispatcher()
    
    agents = [
        TestAgent(name="agent1"),
        TestAgent(name="agent2"),
        TestAgent(name="agent3")
    ]
    
    result = await orchestrator.execute_workflow(
        agents=agents,
        task="Test workflow",
        tags=["test", "workflow"]
    )
    
    # Check result structure
    assert "workflow_id" in result
    assert "run_id" in result
    assert "outputs" in result
    assert len(result["outputs"]) == 3
    
    # Check each agent was executed
    for i, output in enumerate(result["outputs"]):
        assert output["agent"] == f"agent{i+1}"
        assert output["status"] == "success"
        assert "event_id" in output


@pytest.mark.asyncio
async def test_orchestration_dispatcher_workflow_failure():
    """Test workflow stops on agent failure."""
    orchestrator = OrchestrationDispatcher()
    
    agents = [
        TestAgent(name="agent1"),
        TestAgent(name="agent2", should_fail=True),
        TestAgent(name="agent3")
    ]
    
    result = await orchestrator.execute_workflow(
        agents=agents,
        task="Test workflow",
        tags=["test", "failure"]
    )
    
    # Check only first 2 agents executed (stops after failure)
    assert len(result["outputs"]) == 2
    assert result["outputs"][0]["status"] == "success"
    assert result["outputs"][1]["status"] == "failure"


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test complete end-to-end workflow."""
    # Create orchestrator
    orchestrator = OrchestrationDispatcher()
    
    # Create agents
    agents = [
        TestAgent(name="analyzer"),
        TestAgent(name="processor"),
        TestAgent(name="reporter")
    ]
    
    # Execute workflow
    result = await orchestrator.execute_workflow(
        agents=agents,
        task="Complete analysis workflow",
        tags=["analysis", "production"]
    )
    
    # Verify workflow completed
    assert result["workflow_id"]
    assert len(result["outputs"]) == 3
    
    # Verify all agents succeeded
    for output in result["outputs"]:
        assert output["status"] == "success"
    
    # Query events
    pipeline = orchestrator.pipeline
    recent = pipeline.get_recent_events(count=10)
    
    # Filter events for this specific workflow
    workflow_events = [e for e in recent if e.workflow_id == result["workflow_id"]]
    
    # Should have 3 events (one per agent)
    assert len(workflow_events) == 3
    
    # Verify event sequence
    agent_names = [e.agent_name for e in workflow_events]
    assert agent_names == ["analyzer", "processor", "reporter"]


@pytest.mark.asyncio
async def test_factory_function():
    """Test create_dispatcher factory function."""
    dispatcher = create_dispatcher(
        kafka_servers=None,
        enable_metrics=True
    )
    
    assert isinstance(dispatcher, ActionDispatcher)
    assert dispatcher.enable_metrics is True
    
    # Test dispatch
    agent = TestAgent()
    result = await dispatcher.dispatch(
        agent=agent,
        action_type="test",
        input_data={"task": "test"},
        context={}
    )
    
    assert result["status"] == "success"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
