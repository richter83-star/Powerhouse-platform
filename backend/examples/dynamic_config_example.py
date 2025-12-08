
"""
Dynamic Self-Configuration Example

Demonstrates how the agent system autonomously adjusts its runtime
parameters based on performance metrics.
"""

import time
import random
from typing import Dict, Any

from core.adaptive_orchestrator import AdaptiveOrchestrator
from core.dynamic_config_manager import get_config_manager, AdjustmentStrategy
from core.performance_monitor_with_config import get_adaptive_monitor
from utils.logging import get_logger

logger = get_logger(__name__)


def simulate_workload(
    orchestrator: AdaptiveOrchestrator,
    num_tasks: int = 50,
    introduce_latency: bool = False,
    introduce_errors: bool = False
):
    """
    Simulate a workload to trigger configuration adjustments.
    
    Args:
        orchestrator: Adaptive orchestrator instance
        num_tasks: Number of tasks to run
        introduce_latency: Simulate high latency
        introduce_errors: Simulate errors
    """
    logger.info(f"Starting workload simulation: {num_tasks} tasks")
    logger.info(f"  Latency mode: {introduce_latency}")
    logger.info(f"  Error mode: {introduce_errors}")
    
    results = []
    
    for i in range(num_tasks):
        task = f"Task {i+1}: Process data batch"
        
        # Add artificial delays/errors for testing
        if introduce_latency and random.random() > 0.3:
            time.sleep(random.uniform(0.5, 2.0))
        
        if introduce_errors and random.random() > 0.85:
            # Simulate error
            logger.warning(f"Simulated error on {task}")
            results.append({"task": task, "status": "error"})
            continue
        
        try:
            result = orchestrator.run(task)
            results.append({"task": task, "status": "success", "result": result})
        except Exception as e:
            logger.error(f"Task failed: {e}")
            results.append({"task": task, "status": "error", "error": str(e)})
        
        # Brief pause between tasks
        time.sleep(0.1)
    
    # Print results summary
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")
    
    logger.info(f"Workload complete: {success_count} success, {error_count} errors")
    
    return results


def print_configuration_status(config_manager):
    """Print current configuration status."""
    
    snapshot = config_manager.get_configuration_snapshot()
    stats = config_manager.get_statistics()
    
    print("\n" + "="*70)
    print("CONFIGURATION STATUS")
    print("="*70)
    
    print(f"\nStrategy: {snapshot['strategy']}")
    print(f"Timestamp: {snapshot['timestamp']}")
    
    print("\nCurrent Parameters:")
    for name, value in snapshot['parameters'].items():
        bounds = config_manager.parameter_bounds.get(name)
        if bounds:
            print(f"  {name}: {value} (range: {bounds.min_value}-{bounds.max_value})")
    
    print("\nActive Rules:")
    for name, info in snapshot['active_rules'].items():
        status = "✓ enabled" if info['enabled'] else "✗ disabled"
        triggered = f", triggered {info['trigger_count']} times" if info['trigger_count'] > 0 else ""
        print(f"  {name}: {status}{triggered}")
    
    if snapshot['recent_changes']:
        print("\nRecent Changes:")
        for change in snapshot['recent_changes'][-5:]:
            print(f"  [{change['timestamp']}] {change['parameter']}: "
                  f"{change['old_value']} → {change['new_value']}")
            print(f"    Reason: {change['reason']}")
    
    print("\nStatistics:")
    print(f"  Total changes: {stats['total_changes']}")
    print(f"  Rollbacks: {stats['rollbacks']}")
    print(f"  Avg changes/hour: {stats['avg_changes_per_hour']:.2f}")
    
    print("="*70 + "\n")


def print_performance_summary(orchestrator: AdaptiveOrchestrator):
    """Print performance summary."""
    
    summary = orchestrator.get_performance_summary()
    
    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    
    print(f"\nAdaptive Mode: {'ENABLED' if summary['adaptive_mode'] else 'DISABLED'}")
    print(f"Health Score: {summary.get('health_score', 'N/A')}/100")
    
    perf = summary.get('performance', {})
    if perf:
        print("\nPerformance Metrics:")
        print(f"  Success Rate: {perf.get('success_rate', 0)*100:.1f}%")
        print(f"  Avg Latency: {perf.get('avg_latency_ms', 0):.0f}ms")
        print(f"  Error Rate: {perf.get('error_rate', 0)*100:.1f}%")
        print(f"  Total Cost: ${perf.get('total_cost', 0):.2f}")
        print(f"  Avg Memory: {perf.get('avg_memory_mb', 0):.0f}MB")
    
    print("="*70 + "\n")


def example_1_basic_adaptation():
    """Example 1: Basic dynamic configuration adaptation."""
    
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Dynamic Configuration")
    print("="*70 + "\n")
    
    # Create adaptive orchestrator
    orchestrator = AdaptiveOrchestrator(
        agent_names=["planning", "react", "chain_of_thought"],
        enable_adaptation=True
    )
    
    config_manager = get_config_manager()
    
    # Print initial configuration
    print("Initial configuration:")
    print_configuration_status(config_manager)
    
    # Run some tasks
    print("\nRunning initial workload (normal conditions)...")
    simulate_workload(orchestrator, num_tasks=20)
    
    # Check configuration
    print("\nConfiguration after normal workload:")
    print_configuration_status(config_manager)
    
    # Print performance
    print_performance_summary(orchestrator)


def example_2_high_latency_adaptation():
    """Example 2: Adaptation to high latency."""
    
    print("\n" + "="*70)
    print("EXAMPLE 2: High Latency Adaptation")
    print("="*70 + "\n")
    
    orchestrator = AdaptiveOrchestrator(
        agent_names=["planning", "react"],
        enable_adaptation=True
    )
    
    config_manager = get_config_manager()
    
    # Check initial planner depth
    initial_depth = config_manager.get_parameter("planner_search_depth")
    print(f"Initial planner search depth: {initial_depth}")
    
    # Simulate high latency workload
    print("\nSimulating high latency workload...")
    simulate_workload(orchestrator, num_tasks=30, introduce_latency=True)
    
    # Check if depth was reduced
    new_depth = config_manager.get_parameter("planner_search_depth")
    print(f"\nPlanner search depth after high latency: {new_depth}")
    
    if new_depth < initial_depth:
        print("✓ System successfully adapted to high latency by reducing search depth!")
    else:
        print("ℹ No adaptation needed or threshold not reached")
    
    print_configuration_status(config_manager)


def example_3_error_handling_adaptation():
    """Example 3: Adaptation to high error rates."""
    
    print("\n" + "="*70)
    print("EXAMPLE 3: Error Rate Adaptation")
    print("="*70 + "\n")
    
    orchestrator = AdaptiveOrchestrator(
        agent_names=["react", "reflection"],
        enable_adaptation=True
    )
    
    config_manager = get_config_manager()
    
    # Check initial retry count
    initial_retries = config_manager.get_parameter("max_retries")
    print(f"Initial max retries: {initial_retries}")
    
    # Simulate errors
    print("\nSimulating workload with errors...")
    simulate_workload(orchestrator, num_tasks=30, introduce_errors=True)
    
    # Check if retries increased
    new_retries = config_manager.get_parameter("max_retries")
    print(f"\nMax retries after error workload: {new_retries}")
    
    if new_retries > initial_retries:
        print("✓ System increased retry attempts in response to errors!")
    else:
        print("ℹ No adaptation needed or threshold not reached")
    
    print_configuration_status(config_manager)


def example_4_manual_parameter_control():
    """Example 4: Manual parameter control."""
    
    print("\n" + "="*70)
    print("EXAMPLE 4: Manual Parameter Control")
    print("="*70 + "\n")
    
    orchestrator = AdaptiveOrchestrator(
        agent_names=["planning"],
        enable_adaptation=True
    )
    
    config_manager = get_config_manager()
    
    # Manually set parameters
    print("Setting custom parameters:")
    
    params = {
        "planner_search_depth": 8,
        "max_retries": 5,
        "timeout_seconds": 120,
        "quality_threshold": 0.85
    }
    
    for param, value in params.items():
        success = orchestrator.set_parameter(param, value, reason="Manual tuning for test")
        if success:
            print(f"  ✓ Set {param} = {value}")
        else:
            print(f"  ✗ Failed to set {param}")
    
    # Verify settings
    print("\nVerifying parameter values:")
    for param in params.keys():
        current = orchestrator.get_current_parameter(param)
        print(f"  {param}: {current}")
    
    # Run workload with custom parameters
    print("\nRunning workload with custom parameters...")
    simulate_workload(orchestrator, num_tasks=15)
    
    print_configuration_status(config_manager)


def example_5_rollback_on_degradation():
    """Example 5: Automatic rollback on performance degradation."""
    
    print("\n" + "="*70)
    print("EXAMPLE 5: Automatic Rollback")
    print("="*70 + "\n")
    
    orchestrator = AdaptiveOrchestrator(
        agent_names=["react"],
        enable_adaptation=True
    )
    
    monitor = get_adaptive_monitor()
    config_manager = get_config_manager()
    
    # Run baseline workload
    print("Establishing baseline performance...")
    simulate_workload(orchestrator, num_tasks=20)
    
    baseline_health = orchestrator.get_performance_summary().get('health_score')
    print(f"Baseline health score: {baseline_health}")
    
    # Manually set a bad parameter
    print("\nSetting potentially problematic parameter...")
    config_manager.set_parameter(
        "timeout_seconds",
        5,  # Very low timeout
        reason="Testing rollback"
    )
    
    # Run workload that may trigger issues
    print("\nRunning workload with low timeout...")
    simulate_workload(orchestrator, num_tasks=20, introduce_latency=True)
    
    # Check for rollback
    time.sleep(monitor.rollback_window_minutes * 60 + 1)  # Wait for rollback window
    
    current_timeout = config_manager.get_parameter("timeout_seconds")
    print(f"\nTimeout after rollback check: {current_timeout}")
    
    print_configuration_status(config_manager)


def example_6_strategy_comparison():
    """Example 6: Compare different adjustment strategies."""
    
    print("\n" + "="*70)
    print("EXAMPLE 6: Strategy Comparison")
    print("="*70 + "\n")
    
    strategies = [
        AdjustmentStrategy.CONSERVATIVE,
        AdjustmentStrategy.BALANCED,
        AdjustmentStrategy.AGGRESSIVE
    ]
    
    for strategy in strategies:
        print(f"\n--- Testing {strategy.value.upper()} strategy ---\n")
        
        # Create orchestrator with specific strategy
        orchestrator = AdaptiveOrchestrator(
            agent_names=["planning"],
            enable_adaptation=True
        )
        
        # Note: Strategy is set at config_manager initialization
        # For this example, we're using the same manager
        # In production, you might create separate managers
        
        # Run workload
        print(f"Running workload with {strategy.value} strategy...")
        simulate_workload(orchestrator, num_tasks=15, introduce_latency=True)
        
        # Show results
        print_configuration_status(get_config_manager())
        print_performance_summary(orchestrator)


def main():
    """Run all examples."""
    
    print("\n" + "="*70)
    print("DYNAMIC SELF-CONFIGURATION EXAMPLES")
    print("="*70)
    
    examples = [
        ("Basic Adaptation", example_1_basic_adaptation),
        ("High Latency Adaptation", example_2_high_latency_adaptation),
        ("Error Handling Adaptation", example_3_error_handling_adaptation),
        ("Manual Parameter Control", example_4_manual_parameter_control),
        ("Automatic Rollback", example_5_rollback_on_degradation),
        ("Strategy Comparison", example_6_strategy_comparison)
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRunning Example 1 (Basic Adaptation)...")
    example_1_basic_adaptation()
    
    print("\nTo run other examples, call them directly:")
    print("  example_2_high_latency_adaptation()")
    print("  example_3_error_handling_adaptation()")
    print("  etc.")


if __name__ == "__main__":
    main()

