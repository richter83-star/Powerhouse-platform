
"""
Tests for Exponential Learning System

Tests:
1. Learning data plugins
2. Agent learning coordinator
3. Integration with existing systems
4. Learning loop execution
5. Performance measurement
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.learning_data_plugins import (
    LearningDataOrchestrator,
    CustomerSupportDataPlugin,
    SalesResearchDataPlugin,
    BenchmarkDatasetPlugin
)
from core.agent_learning_coordinator import AgentLearningCoordinator
from core.adaptive_orchestrator import AdaptiveOrchestrator
from core.goal_driven_agent import GoalDrivenAgent


class TestLearningDataPlugins(unittest.TestCase):
    """Test learning data plugin system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = LearningDataOrchestrator()
    
    def test_plugin_registration(self):
        """Test plugin registration."""
        plugin = CustomerSupportDataPlugin()
        self.orchestrator.register_plugin(plugin)
        
        plugins = self.orchestrator.list_plugins()
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0]['name'], 'customer_support')
    
    def test_customer_support_plugin(self):
        """Test customer support plugin."""
        plugin = CustomerSupportDataPlugin()
        
        # Test single task generation
        task = plugin.generate_task()
        self.assertIn('id', task)
        self.assertIn('type', task)
        self.assertEqual(task['type'], 'customer_support')
        self.assertIn('description', task)
        
        # Test batch generation
        batch = plugin.generate_batch(5)
        self.assertEqual(len(batch), 5)
        
        # Test validation
        result = "Here is the documentation for our product"
        validation = plugin.validate_result(task, result)
        self.assertIsInstance(validation, bool)
    
    def test_sales_research_plugin(self):
        """Test sales research plugin."""
        plugin = SalesResearchDataPlugin()
        
        task = plugin.generate_task()
        self.assertEqual(task['type'], 'sales_research')
        self.assertIn('description', task)
        
        batch = plugin.generate_batch(3)
        self.assertEqual(len(batch), 3)
    
    def test_benchmark_plugin(self):
        """Test benchmark dataset plugin."""
        plugin = BenchmarkDatasetPlugin()
        
        task = plugin.generate_task()
        self.assertEqual(task['type'], 'benchmark')
        self.assertIn('expected_answer', task)
        
        # Test validation with correct answer
        correct_result = task['expected_answer']
        self.assertTrue(plugin.validate_result(task, correct_result))
        
        # Test validation with incorrect answer
        self.assertFalse(plugin.validate_result(task, "wrong answer"))
    
    def test_orchestrator_task_generation(self):
        """Test orchestrator task generation."""
        self.orchestrator.register_plugin(CustomerSupportDataPlugin())
        self.orchestrator.register_plugin(BenchmarkDatasetPlugin())
        
        # Test single task generation
        task = self.orchestrator.generate_task()
        self.assertIn('id', task)
        self.assertIn('type', task)
        
        # Test specific plugin
        task = self.orchestrator.generate_task('customer_support')
        self.assertEqual(task['type'], 'customer_support')
        
        # Test batch generation
        batch = self.orchestrator.generate_training_batch(10)
        self.assertEqual(len(batch), 10)
    
    def test_orchestrator_validation(self):
        """Test result validation through orchestrator."""
        plugin = BenchmarkDatasetPlugin()
        self.orchestrator.register_plugin(plugin)
        
        task = plugin.generate_task()
        result = task['expected_answer']
        
        validation = self.orchestrator.validate_result(task, result)
        self.assertIn('valid', validation)
        self.assertTrue(validation['valid'])
    
    def test_stats_tracking(self):
        """Test statistics tracking."""
        self.orchestrator.register_plugin(CustomerSupportDataPlugin())
        
        # Generate tasks
        for _ in range(5):
            self.orchestrator.generate_task()
        
        stats = self.orchestrator.get_stats()
        self.assertEqual(stats['total_tasks_generated'], 5)
        self.assertEqual(stats['plugin_count'], 1)


class TestAgentLearningCoordinator(unittest.TestCase):
    """Test agent learning coordinator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create minimal orchestrator
        self.orchestrator = AdaptiveOrchestrator(
            agent_names=["react"],
            enable_adaptation=False
        )
        
        # Create goal agent
        self.goal_agent = GoalDrivenAgent(
            agent_config={"autonomous_mode": False}
        )
        
        # Create learning data
        self.learning_data = LearningDataOrchestrator()
        self.learning_data.register_plugin(BenchmarkDatasetPlugin())
        
        # Create coordinator
        self.coordinator = AgentLearningCoordinator(
            orchestrator=self.orchestrator,
            goal_driven_agent=self.goal_agent,
            learning_data_orchestrator=self.learning_data
        )
    
    def test_coordinator_initialization(self):
        """Test coordinator initialization."""
        self.assertIsNotNone(self.coordinator.orchestrator)
        self.assertIsNotNone(self.coordinator.goal_agent)
        self.assertIsNotNone(self.coordinator.learning_data)
        self.assertEqual(self.coordinator.learning_stats['tasks_executed'], 0)
    
    def test_training_batch_generation(self):
        """Test training batch generation."""
        tasks = self.coordinator._generate_training_batch(5)
        self.assertIsInstance(tasks, list)
        self.assertLessEqual(len(tasks), 5)
    
    def test_performance_measurement(self):
        """Test performance measurement."""
        # Create mock results
        results = [
            {'success': True, 'latency_ms': 100},
            {'success': True, 'latency_ms': 150},
            {'success': False, 'latency_ms': 200},
        ]
        
        performance = self.coordinator._measure_performance(results)
        self.assertIn('success_rate', performance)
        self.assertIn('avg_latency', performance)
        self.assertAlmostEqual(performance['success_rate'], 2/3)
    
    def test_multiplier_calculation(self):
        """Test performance multiplier calculation."""
        baseline = {'success_rate': 0.5, 'avg_latency': 1000}
        current = {'success_rate': 0.8, 'avg_latency': 500}
        
        multiplier = self.coordinator._calculate_multiplier(baseline, current)
        self.assertGreater(multiplier, 1.0)  # Should show improvement
    
    def test_mini_learning_loop(self):
        """Test mini learning loop (3 iterations)."""
        report = self.coordinator.start_exponential_learning_loop(
            iterations=3,
            batch_size=2,
            report_every=1
        )
        
        self.assertIn('status', report)
        self.assertIn('performance', report)
        self.assertIn('learning', report)
        self.assertEqual(report['summary']['iterations_completed'], 3)
        self.assertGreater(report['summary']['total_tasks_executed'], 0)
    
    def test_get_current_stats(self):
        """Test getting current statistics."""
        stats = self.coordinator.get_current_stats()
        self.assertIn('iterations_completed', stats)
        self.assertIn('tasks_executed', stats)
        self.assertIn('strategies_learned', stats)


class TestIntegration(unittest.TestCase):
    """Test integration with existing systems."""
    
    def test_full_system_integration(self):
        """Test full system integration."""
        # Create all components
        orchestrator = AdaptiveOrchestrator(
            agent_names=["react", "planning"],
            enable_adaptation=True
        )
        
        goal_agent = GoalDrivenAgent(
            agent_config={"autonomous_mode": False}
        )
        
        learning_data = LearningDataOrchestrator()
        learning_data.register_plugin(CustomerSupportDataPlugin())
        learning_data.register_plugin(BenchmarkDatasetPlugin())
        
        coordinator = AgentLearningCoordinator(
            orchestrator=orchestrator,
            goal_driven_agent=goal_agent,
            learning_data_orchestrator=learning_data
        )
        
        # Run mini learning loop
        report = coordinator.start_exponential_learning_loop(
            iterations=2,
            batch_size=3
        )
        
        self.assertEqual(report['status'], 'success')
        self.assertGreater(report['summary']['total_tasks_executed'], 0)
    
    def test_with_all_plugins(self):
        """Test with all learning plugins."""
        orchestrator = AdaptiveOrchestrator(agent_names=["react"])
        goal_agent = GoalDrivenAgent(agent_config={"autonomous_mode": False})
        
        learning_data = LearningDataOrchestrator()
        learning_data.register_plugin(CustomerSupportDataPlugin())
        learning_data.register_plugin(SalesResearchDataPlugin())
        learning_data.register_plugin(BenchmarkDatasetPlugin())
        
        coordinator = AgentLearningCoordinator(
            orchestrator=orchestrator,
            goal_driven_agent=goal_agent,
            learning_data_orchestrator=learning_data
        )
        
        # Verify all plugins available
        plugins = learning_data.list_plugins()
        self.assertEqual(len(plugins), 3)
        
        # Run learning
        report = coordinator.start_exponential_learning_loop(
            iterations=2,
            batch_size=6  # 2 tasks per plugin
        )
        
        self.assertGreater(report['summary']['total_tasks_executed'], 0)


def run_tests():
    """Run all tests."""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add tests
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestLearningDataPlugins))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAgentLearningCoordinator))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    result = run_tests()
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)
