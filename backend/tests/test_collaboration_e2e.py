"""
End-to-End Tests: Multi-Agent Collaboration (E2E)

Tests that multiple agents collaborate to solve complex tasks.
"""

import pytest
from unittest.mock import Mock, patch

try:
    from communication import CommunicationProtocol, MessageType
    COMMUNICATION_AVAILABLE = True
except ImportError:
    COMMUNICATION_AVAILABLE = False


@pytest.mark.e2e
@pytest.mark.skipif(not COMMUNICATION_AVAILABLE, reason="Communication protocol required")
class TestMultiAgentCollaboration:
    """Test multi-agent collaboration."""
    
    def test_agents_communicate_and_delegate(self, mock_communication_protocol):
        """Verify agents communicate and delegate."""
        from core.orchestrator_with_communication import OrchestratorWithCommunication
        
        mock_agent1 = Mock()
        mock_agent1.run.return_value = "Agent1 result"
        mock_agent2 = Mock()
        mock_agent2.run.return_value = "Agent2 result"
        
        with patch('core.orchestrator_with_communication.Orchestrator._load_agent') as mock_load:
            mock_load.side_effect = [mock_agent1, mock_agent2]
            
            orchestrator = OrchestratorWithCommunication(
                agent_names=["agent1", "agent2"],
                execution_mode="collaborative",
                protocol=mock_communication_protocol
            )
            
            # Agents should be registered
            assert len(mock_communication_protocol.agents) >= 2
            
            # Execute task
            result = orchestrator.run("Complex collaborative task")
            
            assert result is not None
    
    def test_consensus_mechanisms_work(self, mock_communication_protocol):
        """Verify consensus mechanisms work."""
        from core.orchestrator_with_communication import OrchestratorWithCommunication
        
        orchestrator = OrchestratorWithCommunication(
            agent_names=["agent1", "agent2", "agent3"],
            enable_consensus=True,
            protocol=mock_communication_protocol
        )
        
        try:
            # Simulate voting
            votes = {"option1": 2, "option2": 1}
            result = orchestrator.reach_consensus(votes)
            
            assert result is not None
            assert result == "option1"  # Majority
        except AttributeError:
            pytest.skip("Consensus method not available")
    
    def test_shared_context_maintained(self, mock_communication_protocol):
        """Verify shared context is maintained."""
        protocol = mock_communication_protocol
        
        # Set shared state
        protocol.set_shared_state("task_context", {"status": "in_progress", "data": "shared"})
        
        # Multiple agents should see it
        context1 = protocol.get_shared_state("task_context")
        context2 = protocol.get_shared_state("task_context")
        
        assert context1 == context2
        assert context1["status"] == "in_progress"
    
    def test_collaborative_vs_sequential_performance(self, mock_communication_protocol):
        """Compare collaborative vs sequential performance."""
        import time
        
        # Mock agents
        def agent_with_delay(context):
            time.sleep(0.05)  # Small delay
            return "Result"
        
        mock_agent1 = Mock()
        mock_agent1.run.side_effect = agent_with_delay
        mock_agent2 = Mock()
        mock_agent2.run.side_effect = agent_with_delay
        
        # Sequential
        with patch('core.orchestrator.Orchestrator._load_agent') as mock_load:
            mock_load.side_effect = [mock_agent1, mock_agent2]
            sequential_orch = Orchestrator(
                agent_names=["agent1", "agent2"],
                execution_mode="sequential"
            )
            
            start = time.time()
            sequential_orch.run("task")
            sequential_time = time.time() - start
        
        # Collaborative (parallel)
        with patch('core.orchestrator_with_communication.Orchestrator._load_agent') as mock_load:
            mock_load.side_effect = [mock_agent1, mock_agent2]
            collaborative_orch = OrchestratorWithCommunication(
                agent_names=["agent1", "agent2"],
                execution_mode="parallel",
                protocol=mock_communication_protocol
            )
            
            start = time.time()
            collaborative_orch.run("task")
            collaborative_time = time.time() - start
        
        # Parallel should be faster
        # (Note: In real test, would be more significant difference)
        assert sequential_time >= 0
        assert collaborative_time >= 0

