
"""
Tests for Autonomous Goal-Driven Agent System
"""

import unittest
import time
from datetime import datetime, timedelta

from core.goal_driven_agent import GoalDrivenAgent
from core.autonomous_goal_executor import AutonomousGoalExecutor, ExecutionStrategy
from core.proactive_goal_setter import Goal, GoalType, GoalPriority, GoalStatus


class TestAutonomousGoalExecutor(unittest.TestCase):
    """Test the autonomous goal executor."""
    
    def setUp(self):
        """Set up test executor."""
        self.executor = AutonomousGoalExecutor({
            "execution_interval_seconds": 1,
            "max_concurrent_goals": 2,
            "enable_learning": True
        })
    
    def tearDown(self):
        """Clean up."""
        if self.executor.running:
            self.executor.stop()
    
    def test_executor_initialization(self):
        """Test executor initializes correctly."""
        self.assertIsNotNone(self.executor)
        self.assertFalse(self.executor.running)
        self.assertEqual(len(self.executor.execution_plans), 0)
    
    def test_executor_start_stop(self):
        """Test executor can start and stop."""
        self.executor.start()
        self.assertTrue(self.executor.running)
        time.sleep(0.5)
        self.executor.stop()
        self.assertFalse(self.executor.running)
    
    def test_action_handler_registration(self):
        """Test registering action handlers."""
        def test_handler(params, goal_id):
            return {"success": True}
        
        self.executor.register_action_handler("test_action", test_handler)
        self.assertIn("test_action", self.executor.action_handlers)
    
    def test_create_execution_plan(self):
        """Test creating execution plan."""
        goal = Goal(
            goal_id="test_goal_1",
            goal_type=GoalType.PERFORMANCE_TARGET,
            priority=GoalPriority.HIGH,
            description="Test goal",
            target_metric="latency",
            current_value=200.0,
            target_value=150.0,
            deadline=datetime.now() + timedelta(hours=24),
            actions=["action1", "action2"]
        )
        
        plan = self.executor.create_execution_plan(goal)
        
        self.assertEqual(plan.goal_id, "test_goal_1")
        self.assertIsInstance(plan.strategy, ExecutionStrategy)
        self.assertEqual(len(plan.actions), 2)
        self.assertGreater(plan.priority_score, 0)
    
    def test_priority_calculation(self):
        """Test priority score calculation."""
        high_priority_goal = Goal(
            goal_id="high_priority",
            goal_type=GoalType.BOTTLENECK_PREVENTION,
            priority=GoalPriority.CRITICAL,
            description="Critical goal",
            target_metric="cpu",
            current_value=90.0,
            target_value=70.0,
            deadline=datetime.now() + timedelta(hours=1),  # Urgent
            actions=[]
        )
        
        low_priority_goal = Goal(
            goal_id="low_priority",
            goal_type=GoalType.COST_REDUCTION,
            priority=GoalPriority.LOW,
            description="Low priority goal",
            target_metric="cost",
            current_value=100.0,
            target_value=90.0,
            deadline=datetime.now() + timedelta(days=30),
            actions=[]
        )
        
        high_score = self.executor._calculate_priority_score(high_priority_goal)
        low_score = self.executor._calculate_priority_score(low_priority_goal)
        
        self.assertGreater(high_score, low_score)
    
    def test_get_statistics(self):
        """Test getting statistics."""
        stats = self.executor.get_statistics()
        
        self.assertIn("total_executions", stats)
        self.assertIn("successful_executions", stats)
        self.assertIn("active_executions", stats)
        self.assertIn("scheduled_plans", stats)


class TestGoalDrivenAgent(unittest.TestCase):
    """Test the goal-driven agent."""
    
    def setUp(self):
        """Set up test agent."""
        forecasting_config = {
            "auto_analysis_enabled": False,  # Disable for tests
            "goal_setter": {
                "auto_goal_setting": True,
                "max_active_goals": 5
            }
        }
        
        executor_config = {
            "execution_interval_seconds": 1,
            "max_concurrent_goals": 2,
            "enable_learning": True
        }
        
        agent_config = {
            "autonomous_mode": False,  # Start in manual mode
            "goal_sync_interval_seconds": 1
        }
        
        self.agent = GoalDrivenAgent(
            forecasting_config=forecasting_config,
            executor_config=executor_config,
            agent_config=agent_config
        )
    
    def tearDown(self):
        """Clean up."""
        if self.agent.running:
            self.agent.stop()
    
    def test_agent_initialization(self):
        """Test agent initializes correctly."""
        self.assertIsNotNone(self.agent)
        self.assertIsNotNone(self.agent.forecasting_engine)
        self.assertIsNotNone(self.agent.executor)
        self.assertFalse(self.agent.running)
    
    def test_agent_start_stop(self):
        """Test agent can start and stop."""
        self.agent.start()
        self.assertTrue(self.agent.running)
        time.sleep(0.5)
        self.agent.stop()
        self.assertFalse(self.agent.running)
    
    def test_record_metric(self):
        """Test recording metrics."""
        self.agent.record_metric("test_metric", 42.0)
        # Verify metric was recorded (no exception)
        self.assertTrue(True)
    
    def test_record_event(self):
        """Test recording events."""
        self.agent.record_event("test_event", metadata={"key": "value"})
        # Verify event was recorded (no exception)
        self.assertTrue(True)
    
    def test_get_agent_status(self):
        """Test getting agent status."""
        status = self.agent.get_agent_status()
        
        self.assertIn("running", status)
        self.assertIn("autonomous_mode", status)
        self.assertIn("statistics", status)
        self.assertIn("active_goals", status)
        self.assertIn("forecasting", status)
        self.assertIn("executor", status)
    
    def test_get_goal_overview(self):
        """Test getting goal overview."""
        overview = self.agent.get_goal_overview()
        
        self.assertIn("total_active_goals", overview)
        self.assertIn("goals_by_type", overview)
        self.assertIn("goals_by_priority", overview)
        self.assertIn("goals", overview)
    
    def test_get_predictions(self):
        """Test getting predictions."""
        # Add some metric data first
        self.agent.record_metric("cpu_usage", 50.0)
        self.agent.record_metric("memory_usage", 60.0)
        
        predictions = self.agent.get_predictions(horizon_hours=12)
        
        self.assertIn("current_state", predictions)
        self.assertIn("predicted_state", predictions)
        self.assertIn("confidence", predictions)
    
    def test_force_analysis(self):
        """Test forcing analysis."""
        result = self.agent.force_analysis()
        
        self.assertEqual(result["status"], "success")
        self.assertIn("timestamp", result)
    
    def test_set_autonomous_mode(self):
        """Test setting autonomous mode."""
        self.agent.start()
        
        # Start in manual mode
        self.assertFalse(self.agent.autonomous_mode)
        
        # Enable autonomous mode
        self.agent.set_autonomous_mode(True)
        self.assertTrue(self.agent.autonomous_mode)
        
        # Disable autonomous mode
        self.agent.set_autonomous_mode(False)
        self.assertFalse(self.agent.autonomous_mode)
        
        self.agent.stop()
    
    def test_action_handler_registration(self):
        """Test registering custom action handlers."""
        def custom_handler(params, goal_id):
            return {"success": True, "custom": True}
        
        self.agent.register_action_handler("custom_action", custom_handler)
        
        # Verify handler is registered
        self.assertIn("custom_action", self.agent.executor.action_handlers)
    
    def test_comprehensive_report(self):
        """Test getting comprehensive report."""
        report = self.agent.get_comprehensive_report()
        
        self.assertIn("agent_status", report)
        self.assertIn("goals", report)
        self.assertIn("forecasting_report", report)
        self.assertIn("executor_state", report)
        self.assertIn("learning_insights", report)


class TestAutonomousIntegration(unittest.TestCase):
    """Test full integration of autonomous behavior."""
    
    def setUp(self):
        """Set up integrated test."""
        self.agent = GoalDrivenAgent(
            forecasting_config={
                "auto_analysis_enabled": False,
                "goal_setter": {"auto_goal_setting": True}
            },
            executor_config={
                "execution_interval_seconds": 1,
                "enable_learning": True
            },
            agent_config={
                "autonomous_mode": True,
                "goal_sync_interval_seconds": 2
            }
        )
    
    def tearDown(self):
        """Clean up."""
        if self.agent.running:
            self.agent.stop()
    
    def test_end_to_end_autonomous_behavior(self):
        """Test complete autonomous cycle."""
        # Start agent
        self.agent.start()
        self.assertTrue(self.agent.running)
        
        # Simulate metrics
        for i in range(10):
            self.agent.record_metric("cpu_usage", 50.0 + i * 2)
            self.agent.record_metric("memory_usage", 60.0 + i)
            time.sleep(0.2)
        
        # Force analysis to create goals
        self.agent.force_analysis()
        
        # Wait for goal processing
        time.sleep(3)
        
        # Check if goals were created
        overview = self.agent.get_goal_overview()
        # Note: Goals may or may not be created depending on patterns
        self.assertIsNotNone(overview)
        
        # Check statistics
        stats = self.agent.get_agent_status()
        self.assertGreater(stats["uptime_seconds"], 0)
        
        # Stop agent
        self.agent.stop()
        self.assertFalse(self.agent.running)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()

