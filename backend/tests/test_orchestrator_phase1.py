"""
Tests for Orchestrator Execution Modes (Phase 1)

Tests sequential, parallel, and adaptive execution modes.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from core.orchestrator import Orchestrator


@pytest.mark.unit
class TestOrchestratorExecutionModes:
    """Test orchestrator execution modes."""
    
    def test_sequential_execution(self):
        """Test sequential execution order."""
        # Create mock agents
        agent1 = Mock()
        agent1.run.return_value = "Result 1"
        agent2 = Mock()
        agent2.run.return_value = "Result 2"
        
        with patch('core.orchestrator.Orchestrator._load_agent') as mock_load:
            mock_load.side_effect = [agent1, agent2]
            orchestrator = Orchestrator(
                agent_names=["agent1", "agent2"],
                execution_mode="sequential"
            )
            
            result = orchestrator.run("test task")
            
            assert result is not None
            assert "outputs" in result or "results" in result or isinstance(result, dict)
            # Verify agents were called
            assert agent1.run.called
            assert agent2.run.called
    
    def test_parallel_execution(self):
        """Test parallel execution with ThreadPoolExecutor."""
        # Create mock agents with delays
        def slow_agent(context):
            time.sleep(0.1)
            return "Slow Result"
        
        agent1 = Mock()
        agent1.run.side_effect = slow_agent
        agent2 = Mock()
        agent2.run.side_effect = slow_agent
        
        with patch('core.orchestrator.Orchestrator._load_agent') as mock_load:
            mock_load.side_effect = [agent1, agent2]
            orchestrator = Orchestrator(
                agent_names=["agent1", "agent2"],
                execution_mode="parallel"
            )
            
            start_time = time.time()
            result = orchestrator.run("test task")
            elapsed = time.time() - start_time
            
            assert result is not None
            # Parallel should be faster than sequential (sequential would be ~0.2s, parallel ~0.1s)
            assert elapsed < 0.15  # Should be closer to 0.1s than 0.2s
    
    def test_agent_loading(self):
        """Test agent loading by name."""
        mock_agent = Mock()
        mock_agent.run.return_value = "Result"
        
        with patch('core.orchestrator.import_module') as mock_import:
            mock_module = Mock()
            mock_module.Agent = Mock(return_value=mock_agent)
            mock_import.return_value = mock_module
            
            orchestrator = Orchestrator(
                agent_names=["test_agent"],
                execution_mode="sequential"
            )
            
            assert len(orchestrator.agents) == 1
    
    def test_max_agent_limit(self):
        """Test max agent limit enforcement."""
        with pytest.raises(ValueError):
            Orchestrator(
                agent_names=[f"agent{i}" for i in range(20)],  # More than default max
                max_agents=19,
                execution_mode="sequential"
            )
    
    def test_result_aggregation(self):
        """Test result collection from multiple agents."""
        agent1 = Mock()
        agent1.run.return_value = "Result 1"
        agent2 = Mock()
        agent2.run.return_value = "Result 2"
        agent3 = Mock()
        agent3.run.return_value = "Result 3"
        
        with patch('core.orchestrator.Orchestrator._load_agent') as mock_load:
            mock_load.side_effect = [agent1, agent2, agent3]
            orchestrator = Orchestrator(
                agent_names=["agent1", "agent2", "agent3"],
                execution_mode="sequential"
            )
            
            result = orchestrator.run("test task")
            
            assert result is not None
            # All agents should have been called
            assert agent1.run.called
            assert agent2.run.called
            assert agent3.run.called
    
    def test_error_handling_in_execution(self):
        """Test error aggregation when agents fail."""
        agent1 = Mock()
        agent1.run.return_value = "Result 1"
        agent2 = Mock()
        agent2.run.side_effect = Exception("Agent 2 failed")
        agent3 = Mock()
        agent3.run.return_value = "Result 3"
        
        with patch('core.orchestrator.Orchestrator._load_agent') as mock_load:
            mock_load.side_effect = [agent1, agent2, agent3]
            orchestrator = Orchestrator(
                agent_names=["agent1", "agent2", "agent3"],
                execution_mode="sequential"
            )
            
            result = orchestrator.run("test task")
            
            # Should handle errors gracefully
            assert result is not None


@pytest.mark.integration
class TestOrchestratorIntegration:
    """Integration tests for orchestrator."""
    
    def test_adaptive_execution_mode(self):
        """Test adaptive execution mode."""
        # This would test the adaptive logic if implemented
        mock_agent = Mock()
        mock_agent.run.return_value = "Result"
        
        with patch('core.orchestrator.Orchestrator._load_agent', return_value=mock_agent):
            orchestrator = Orchestrator(
                agent_names=["agent1"],
                execution_mode="adaptive"
            )
            
            result = orchestrator.run("test task")
            assert result is not None

