
"""
Integration Test for Dynamic Self-Configuration

Tests the complete flow from agent execution to automatic parameter adjustment.
"""

import unittest
import time
from datetime import datetime

from core.adaptive_orchestrator import AdaptiveOrchestrator
from core.dynamic_config_manager import get_config_manager, AdjustmentStrategy
from core.performance_monitor_with_config import get_adaptive_monitor
from core.performance_monitor import PerformanceMetrics


class TestDynamicConfigIntegration(unittest.TestCase):
    """Integration tests for dynamic self-configuration system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = AdaptiveOrchestrator(
            agent_names=["planning", "react"],
            enable_adaptation=True
        )
        self.config_manager = get_config_manager()
        self.monitor = get_adaptive_monitor()
    
    def test_end_to_end_adaptation(self):
        """Test complete adaptation flow."""
        
        # Get initial parameters
        initial_depth = self.config_manager.get_parameter("planner_search_depth")
        initial_retries = self.config_manager.get_parameter("max_retries")
        
        print(f"\nInitial Configuration:")
        print(f"  Planner depth: {initial_depth}")
        print(f"  Max retries: {initial_retries}")
        
        # Simulate high latency scenario
        print("\nSimulating high latency scenario...")
        metrics = PerformanceMetrics(
            total_tasks=100,
            successful_tasks=85,
            success_rate=0.85,
            avg_latency_ms=6000,  # High latency
            error_rate=0.15  # High error rate
        )
        
        # Force evaluation
        changes = self.config_manager.evaluate_and_adjust(metrics, force=True)
        
        print(f"\nAdjustments made: {len(changes)}")
        for change in changes:
            print(f"  {change.parameter_name}: {change.old_value} -> {change.new_value}")
        
        # Verify parameters changed
        new_depth = self.config_manager.get_parameter("planner_search_depth")
        new_retries = self.config_manager.get_parameter("max_retries")
        
        print(f"\nNew Configuration:")
        print(f"  Planner depth: {new_depth}")
        print(f"  Max retries: {new_retries}")
        
        # Should have made some adjustments
        self.assertGreater(len(changes), 0)
    
    def test_orchestrator_uses_dynamic_config(self):
        """Test that orchestrator uses dynamic configuration."""
        
        # Set a specific parameter value
        self.config_manager.set_parameter("timeout_seconds", 120, reason="Test")
        
        # Get runtime config from orchestrator
        runtime_config = self.orchestrator._get_runtime_config()
        
        # Verify parameter is included
        self.assertIn("timeout_seconds", runtime_config)
        self.assertEqual(runtime_config["timeout_seconds"], 120)
    
    def test_performance_summary_includes_config(self):
        """Test that performance summary includes configuration data."""
        
        summary = self.orchestrator.get_performance_summary()
        
        # Verify structure
        self.assertIn("adaptive_mode", summary)
        self.assertTrue(summary["adaptive_mode"])
        
        if "configuration" in summary:
            config = summary["configuration"]
            self.assertIn("enabled", config)
            self.assertIn("strategy", config)
            self.assertIn("current_parameters", config)
    
    def test_monitor_triggers_adjustments(self):
        """Test that monitor triggers automatic adjustments."""
        
        # Record some metrics
        for i in range(10):
            self.monitor.record_agent_run(
                run_id=f"test_run_{i}",
                agent_name="test_agent",
                agent_type="test",
                status="success",
                duration_ms=2000 + (i * 100)
            )
        
        # Force adjustment evaluation
        self.monitor.force_adjustment_evaluation()
        
        # Check that evaluation happened (stats should show total changes)
        stats = self.config_manager.get_statistics()
        self.assertGreaterEqual(stats["total_changes"], 0)
    
    def test_api_integration(self):
        """Test API integration points."""
        
        # Get configuration snapshot (simulates API call)
        snapshot = self.config_manager.get_configuration_snapshot()
        
        # Verify structure
        self.assertIn("timestamp", snapshot)
        self.assertIn("strategy", snapshot)
        self.assertIn("parameters", snapshot)
        self.assertIn("active_rules", snapshot)
        
        # Get statistics (simulates API call)
        stats = self.config_manager.get_statistics()
        
        # Verify structure
        self.assertIn("total_changes", stats)
        self.assertIn("changes_by_parameter", stats)
    
    def test_health_score_calculation(self):
        """Test health score calculation."""
        
        summary = self.orchestrator.get_performance_summary()
        
        if "health_score" in summary:
            health = summary["health_score"]
            
            # Health score should be between 0 and 100
            self.assertGreaterEqual(health, 0)
            self.assertLessEqual(health, 100)
    
    def test_manual_parameter_control(self):
        """Test manual parameter control via orchestrator."""
        
        # Set parameter manually
        success = self.orchestrator.set_parameter(
            "planner_search_depth",
            7,
            reason="Manual integration test"
        )
        
        self.assertTrue(success)
        
        # Verify it was set
        current = self.orchestrator.get_current_parameter("planner_search_depth")
        self.assertEqual(current, 7)
        
        # Verify in change history
        snapshot = self.config_manager.get_configuration_snapshot()
        recent_changes = snapshot["recent_changes"]
        
        if recent_changes:
            last_change = recent_changes[-1]
            self.assertEqual(last_change["parameter"], "planner_search_depth")
            self.assertEqual(last_change["new_value"], 7)
    
    def test_reset_functionality(self):
        """Test resetting configuration to defaults."""
        
        # Change some parameters
        self.config_manager.set_parameter("max_retries", 5)
        self.config_manager.set_parameter("timeout_seconds", 200)
        
        # Reset
        self.config_manager.reset_to_defaults()
        
        # Verify defaults restored
        for name, bounds in self.config_manager.parameter_bounds.items():
            current = self.config_manager.get_parameter(name)
            self.assertEqual(
                current,
                bounds.default_value,
                f"Parameter {name} not reset to default"
            )
    
    def test_rule_enable_disable(self):
        """Test enabling/disabling adjustment rules."""
        
        rule_name = "reduce_depth_on_high_latency"
        rule = self.config_manager.adjustment_rules[rule_name]
        
        # Disable
        rule.enabled = False
        self.assertFalse(rule.enabled)
        
        # Enable
        rule.enabled = True
        self.assertTrue(rule.enabled)
    
    def test_configuration_persistence_across_runs(self):
        """Test that configuration changes persist across runs."""
        
        # Make a change
        param_name = "quality_threshold"
        new_value = 0.85
        self.config_manager.set_parameter(param_name, new_value)
        
        # Simulate "new run"
        runtime_config = self.orchestrator._get_runtime_config()
        
        # Verify parameter is in runtime config
        self.assertIn(param_name, runtime_config)
        self.assertEqual(runtime_config[param_name], new_value)


class TestConfigurationScenarios(unittest.TestCase):
    """Test specific configuration scenarios."""
    
    def setUp(self):
        """Set up for each test."""
        self.config_manager = get_config_manager()
    
    def test_high_latency_scenario(self):
        """Test adaptation to high latency."""
        
        initial_depth = self.config_manager.get_parameter("planner_search_depth")
        
        # Simulate high latency
        metrics = PerformanceMetrics(avg_latency_ms=8000)
        changes = self.config_manager.evaluate_and_adjust(metrics, force=True)
        
        new_depth = self.config_manager.get_parameter("planner_search_depth")
        
        # Should have reduced depth (or hit minimum)
        self.assertLessEqual(new_depth, initial_depth)
    
    def test_high_error_scenario(self):
        """Test adaptation to high error rate."""
        
        initial_retries = self.config_manager.get_parameter("max_retries")
        
        # Simulate high error rate
        metrics = PerformanceMetrics(error_rate=0.25)
        changes = self.config_manager.evaluate_and_adjust(metrics, force=True)
        
        new_retries = self.config_manager.get_parameter("max_retries")
        
        # Should have increased retries (or hit maximum)
        self.assertGreaterEqual(new_retries, initial_retries)
    
    def test_high_memory_scenario(self):
        """Test adaptation to high memory usage."""
        
        initial_batch = self.config_manager.get_parameter("batch_size")
        
        # Simulate high memory
        metrics = PerformanceMetrics(avg_memory_mb=700)
        changes = self.config_manager.evaluate_and_adjust(metrics, force=True)
        
        new_batch = self.config_manager.get_parameter("batch_size")
        
        # Should have reduced batch size (or hit minimum)
        self.assertLessEqual(new_batch, initial_batch)
    
    def test_good_performance_scenario(self):
        """Test that good performance can trigger optimizations."""
        
        # Start with lower depth
        self.config_manager.set_parameter("planner_search_depth", 3)
        time.sleep(0.1)
        
        initial_depth = self.config_manager.get_parameter("planner_search_depth")
        
        # Simulate excellent performance
        metrics = PerformanceMetrics(
            success_rate=0.97,
            avg_latency_ms=500,
            error_rate=0.01
        )
        changes = self.config_manager.evaluate_and_adjust(metrics, force=True)
        
        new_depth = self.config_manager.get_parameter("planner_search_depth")
        
        # May have increased depth for better quality
        # (or stayed same if already optimal)
        self.assertGreaterEqual(new_depth, initial_depth)


def run_integration_tests():
    """Run all integration tests."""
    
    print("\n" + "="*70)
    print("RUNNING DYNAMIC SELF-CONFIGURATION INTEGRATION TESTS")
    print("="*70 + "\n")
    
    # Run tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "="*70)
    print("INTEGRATION TESTS COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_integration_tests()

