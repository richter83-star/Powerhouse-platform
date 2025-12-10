"""
Performance Tests: Execution Speed

Tests execution speed comparisons and concurrent task handling.
"""

import pytest
import time
from unittest.mock import Mock, patch


@pytest.mark.performance
class TestExecutionSpeed:
    """Test execution speed."""
    
    def test_parallel_vs_sequential_execution_times(self):
        """Compare sequential vs parallel execution times."""
        import time
        
        # Create agents with delays
        def slow_agent(context):
            time.sleep(0.1)  # 100ms delay
            return "Result"
        
        mock_agent1 = Mock()
        mock_agent1.run.side_effect = slow_agent
        mock_agent2 = Mock()
        mock_agent2.run.side_effect = slow_agent
        mock_agent3 = Mock()
        mock_agent3.run.side_effect = slow_agent
        
        # Sequential execution
        with patch('core.orchestrator.Orchestrator._load_agent') as mock_load:
            mock_load.side_effect = [mock_agent1, mock_agent2, mock_agent3]
            from core.orchestrator import Orchestrator
            
            sequential_orch = Orchestrator(
                agent_names=["agent1", "agent2", "agent3"],
                execution_mode="sequential"
            )
            
            start = time.time()
            sequential_orch.run("task")
            sequential_time = time.time() - start
        
        # Parallel execution
        with patch('core.orchestrator.Orchestrator._load_agent') as mock_load:
            mock_load.side_effect = [mock_agent1, mock_agent2, mock_agent3]
            parallel_orch = Orchestrator(
                agent_names=["agent1", "agent2", "agent3"],
                execution_mode="parallel"
            )
            
            start = time.time()
            parallel_orch.run("task")
            parallel_time = time.time() - start
        
        # Parallel should be faster (should be ~0.1s vs ~0.3s)
        # Allow some overhead
        assert parallel_time < sequential_time * 1.5  # Parallel should be significantly faster
        assert sequential_time >= 0.25  # Sequential: 3 agents * 0.1s
        assert parallel_time <= 0.15  # Parallel: max(0.1s) + overhead
    
    def test_agent_communication_overhead(self):
        """Measure agent communication overhead."""
        try:
            from communication import CommunicationProtocol
            protocol = CommunicationProtocol()
            
            start = time.time()
            
            # Register agents
            protocol.register_agent("agent1", "react", [])
            protocol.register_agent("agent2", "cot", [])
            
            # Send message
            protocol.send_message("agent1", "agent2", "info", {"data": "test"})
            
            # Get messages
            messages = protocol.get_messages("agent2")
            
            overhead = time.time() - start
            
            # Communication should be fast (< 10ms typically)
            assert overhead < 0.1  # Should be very fast
            assert len(messages) > 0
        except ImportError:
            pytest.skip("Communication protocol not available")
    
    def test_concurrent_task_handling(self):
        """Test concurrent task handling."""
        import threading
        import time
        
        results = []
        lock = threading.Lock()
        
        def run_task(task_id):
            # Simulate task execution
            time.sleep(0.05)
            with lock:
                results.append(f"Task {task_id} completed")
        
        # Run tasks concurrently
        threads = []
        start = time.time()
        
        for i in range(5):
            thread = threading.Thread(target=run_task, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all
        for thread in threads:
            thread.join()
        
        concurrent_time = time.time() - start
        
        # Should be faster than sequential (5 * 0.05s = 0.25s sequential)
        assert concurrent_time < 0.15  # Should be closer to 0.05s
        assert len(results) == 5

