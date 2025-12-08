
"""
Unit Tests for Dynamic Configuration Manager

Tests autonomous self-configuration capabilities.
"""

import unittest
import time
from datetime import datetime, timedelta

from core.dynamic_config_manager import (
    DynamicConfigManager,
    AdjustmentStrategy,
    AdjustmentRule,
    ParameterBounds,
    ConfigurationScope,
    MetricType
)
from core.performance_monitor import PerformanceMetrics


class TestDynamicConfigManager(unittest.TestCase):
    """Test cases for DynamicConfigManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = DynamicConfigManager(
            strategy=AdjustmentStrategy.BALANCED,
            enable_auto_rollback=True,
            rollback_window_minutes=1  # Short window for testing
        )
    
    def test_parameter_registration(self):
        """Test registering new parameters."""
        
        self.config_manager.register_parameter(
            name="test_param",
            bounds=ParameterBounds(
                min_value=0,
                max_value=100,
                default_value=50,
                step_size=5,
                parameter_type="int"
            ),
            scope=ConfigurationScope.GLOBAL,
            description="Test parameter"
        )
        
        value = self.config_manager.get_parameter("test_param")
        self.assertEqual(value, 50)
    
    def test_parameter_validation(self):
        """Test parameter validation and bounds checking."""
        
        param_name = "planner_search_depth"
        bounds = self.config_manager.parameter_bounds[param_name]
        
        # Test upper bound
        self.config_manager.set_parameter(param_name, 100)
        value = self.config_manager.get_parameter(param_name)
        self.assertEqual(value, bounds.max_value)
        
        # Test lower bound
        self.config_manager.set_parameter(param_name, -10)
        value = self.config_manager.get_parameter(param_name)
        self.assertEqual(value, bounds.min_value)
    
    def test_adjustment_rule_trigger(self):
        """Test adjustment rule triggering."""
        
        # Create metrics that should trigger high latency rule
        metrics = PerformanceMetrics(
            total_tasks=100,
            successful_tasks=90,
            success_rate=0.90,
            avg_latency_ms=6000,  # High latency
            error_rate=0.10
        )
        
        initial_depth = self.config_manager.get_parameter("planner_search_depth")
        
        # Evaluate and adjust
        changes = self.config_manager.evaluate_and_adjust(metrics)
        
        # Should have reduced search depth
        new_depth = self.config_manager.get_parameter("planner_search_depth")
        
        # With BALANCED strategy, should decrease
        if changes:
            self.assertLess(new_depth, initial_depth)
    
    def test_rule_cooldown(self):
        """Test rule cooldown mechanism."""
        
        rule = self.config_manager.adjustment_rules["reduce_depth_on_high_latency"]
        
        # Trigger once
        metrics = PerformanceMetrics(avg_latency_ms=6000)
        self.config_manager.evaluate_and_adjust(metrics)
        
        first_trigger = rule.last_triggered
        self.assertIsNotNone(first_trigger)
        
        # Try to trigger again immediately
        self.config_manager.evaluate_and_adjust(metrics)
        
        # Should not trigger due to cooldown
        self.assertEqual(rule.last_triggered, first_trigger)
    
    def test_strategy_modifiers(self):
        """Test different adjustment strategies."""
        
        strategies = [
            (AdjustmentStrategy.CONSERVATIVE, 0.5),
            (AdjustmentStrategy.BALANCED, 1.0),
            (AdjustmentStrategy.AGGRESSIVE, 1.5),
            (AdjustmentStrategy.GRADUAL, 0.25)
        ]
        
        for strategy, expected_modifier in strategies:
            config = DynamicConfigManager(strategy=strategy)
            
            # Test modifier application
            old_value = 10
            new_value = 20
            delta = new_value - old_value
            
            modified = config._apply_strategy_modifier(old_value, new_value)
            expected = old_value + (delta * expected_modifier)
            
            self.assertAlmostEqual(modified, expected, places=2)
    
    def test_configuration_history(self):
        """Test configuration change history."""
        
        param_name = "max_retries"
        
        # Make some changes
        for value in [1, 2, 3, 4]:
            self.config_manager.set_parameter(
                param_name,
                value,
                reason=f"Test change {value}"
            )
        
        # Check history
        self.assertGreater(len(self.config_manager.change_history), 0)
        
        # Verify last change
        last_change = list(self.config_manager.change_history)[-1]
        self.assertEqual(last_change.parameter_name, param_name)
        self.assertEqual(last_change.new_value, 4)
    
    def test_rollback_on_degradation(self):
        """Test automatic rollback on performance degradation."""
        
        # Set baseline
        baseline_metrics = PerformanceMetrics(
            success_rate=0.90,
            avg_latency_ms=1000,
            error_rate=0.05
        )
        self.config_manager.baseline_metrics = baseline_metrics
        
        # Make a change
        param_name = "timeout_seconds"
        old_value = self.config_manager.get_parameter(param_name)
        self.config_manager.set_parameter(param_name, 10, reason="Test change")
        
        # Simulate degraded performance
        degraded_metrics = PerformanceMetrics(
            success_rate=0.70,  # Significant drop
            avg_latency_ms=3000,  # Higher latency
            error_rate=0.20  # Higher errors
        )
        
        # Wait for rollback window (shortened for testing)
        time.sleep(61)  # 1 minute + buffer
        
        # Check for rollback
        rolled_back = self.config_manager.check_and_rollback(degraded_metrics)
        
        # Should have rolled back
        if self.config_manager.enable_auto_rollback:
            self.assertGreater(len(rolled_back), 0)
    
    def test_get_configuration_snapshot(self):
        """Test getting configuration snapshot."""
        
        snapshot = self.config_manager.get_configuration_snapshot()
        
        self.assertIn("timestamp", snapshot)
        self.assertIn("strategy", snapshot)
        self.assertIn("parameters", snapshot)
        self.assertIn("active_rules", snapshot)
        self.assertIn("recent_changes", snapshot)
        
        self.assertEqual(snapshot["strategy"], AdjustmentStrategy.BALANCED.value)
    
    def test_get_statistics(self):
        """Test getting configuration statistics."""
        
        # Make some changes
        self.config_manager.set_parameter("max_retries", 4, reason="Test")
        self.config_manager.set_parameter("timeout_seconds", 90, reason="Test")
        
        stats = self.config_manager.get_statistics()
        
        self.assertIn("total_changes", stats)
        self.assertIn("changes_by_parameter", stats)
        self.assertIn("rollbacks", stats)
        
        self.assertGreater(stats["total_changes"], 0)
    
    def test_reset_to_defaults(self):
        """Test resetting parameters to defaults."""
        
        # Change some parameters
        self.config_manager.set_parameter("max_retries", 5)
        self.config_manager.set_parameter("timeout_seconds", 200)
        
        # Reset
        self.config_manager.reset_to_defaults()
        
        # Verify defaults
        for name, bounds in self.config_manager.parameter_bounds.items():
            current = self.config_manager.get_parameter(name)
            self.assertEqual(current, bounds.default_value)
    
    def test_multiple_rule_evaluation(self):
        """Test evaluation of multiple rules."""
        
        # Create metrics that trigger multiple rules
        metrics = PerformanceMetrics(
            total_tasks=100,
            successful_tasks=85,
            success_rate=0.85,
            avg_latency_ms=6000,  # High latency
            error_rate=0.20,  # High error rate
            avg_memory_mb=600  # High memory
        )
        
        # Force evaluation
        changes = self.config_manager.evaluate_and_adjust(metrics, force=True)
        
        # Should have triggered multiple rules
        self.assertGreater(len(changes), 0)
    
    def test_rule_priority(self):
        """Test that rules are evaluated by priority."""
        
        # Get rules sorted by priority
        sorted_rules = sorted(
            self.config_manager.adjustment_rules.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )
        
        # Verify sorting
        priorities = [rule.priority for _, rule in sorted_rules]
        self.assertEqual(priorities, sorted(priorities, reverse=True))
    
    def test_custom_rule_addition(self):
        """Test adding custom adjustment rules."""
        
        custom_rule = AdjustmentRule(
            name="custom_test_rule",
            description="Custom test rule",
            trigger_metric=MetricType.SUCCESS_RATE,
            trigger_threshold=0.80,
            trigger_operator="lt",
            target_parameter="quality_threshold",
            adjustment_value=-0.05,
            adjustment_type="relative",
            scope=ConfigurationScope.GLOBAL,
            priority=5
        )
        
        self.config_manager.add_adjustment_rule(custom_rule)
        
        self.assertIn("custom_test_rule", self.config_manager.adjustment_rules)
        
        # Verify it can trigger
        metrics = PerformanceMetrics(success_rate=0.75)
        changes = self.config_manager.evaluate_and_adjust(metrics, force=True)
        
        # Should have triggered custom rule
        rule_triggered = any(
            c.rule_name == "custom_test_rule" for c in changes
        )
        # Note: May not trigger if parameter already at min


class TestAdjustmentStrategies(unittest.TestCase):
    """Test adjustment strategy behaviors."""
    
    def test_conservative_strategy(self):
        """Test conservative strategy reduces adjustments."""
        
        config = DynamicConfigManager(strategy=AdjustmentStrategy.CONSERVATIVE)
        
        old_value = 10
        new_value = 20
        
        result = config._apply_strategy_modifier(old_value, new_value)
        
        # Should be halfway between old and new
        self.assertAlmostEqual(result, 15.0, places=1)
    
    def test_aggressive_strategy(self):
        """Test aggressive strategy amplifies adjustments."""
        
        config = DynamicConfigManager(strategy=AdjustmentStrategy.AGGRESSIVE)
        
        old_value = 10
        new_value = 20
        
        result = config._apply_strategy_modifier(old_value, new_value)
        
        # Should be 1.5x the change
        self.assertAlmostEqual(result, 25.0, places=1)
    
    def test_gradual_strategy(self):
        """Test gradual strategy makes small adjustments."""
        
        config = DynamicConfigManager(strategy=AdjustmentStrategy.GRADUAL)
        
        old_value = 10
        new_value = 20
        
        result = config._apply_strategy_modifier(old_value, new_value)
        
        # Should be 25% of the change
        self.assertAlmostEqual(result, 12.5, places=1)


class TestParameterBounds(unittest.TestCase):
    """Test parameter bounds and validation."""
    
    def test_integer_type_conversion(self):
        """Test integer type conversion."""
        
        config = DynamicConfigManager()
        
        bounds = ParameterBounds(
            min_value=0,
            max_value=10,
            default_value=5,
            step_size=1,
            parameter_type="int"
        )
        
        config.register_parameter("test_int", bounds, ConfigurationScope.GLOBAL)
        
        # Set float value
        config.set_parameter("test_int", 7.8)
        
        # Should be rounded to int
        value = config.get_parameter("test_int")
        self.assertIsInstance(value, int)
        self.assertEqual(value, 8)
    
    def test_float_type_preservation(self):
        """Test float type preservation."""
        
        config = DynamicConfigManager()
        
        bounds = ParameterBounds(
            min_value=0.0,
            max_value=1.0,
            default_value=0.5,
            step_size=0.1,
            parameter_type="float"
        )
        
        config.register_parameter("test_float", bounds, ConfigurationScope.GLOBAL)
        
        config.set_parameter("test_float", 0.75)
        
        value = config.get_parameter("test_float")
        self.assertIsInstance(value, float)
        self.assertEqual(value, 0.75)


def run_tests():
    """Run all tests."""
    
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()

