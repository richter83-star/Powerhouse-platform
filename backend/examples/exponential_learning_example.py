
"""
Exponential Learning System - Usage Examples

Demonstrates how to use the exponential learning system.

Examples:
1. Basic deployment and learning
2. Custom configuration
3. Monitoring progress
4. Analyzing results
5. Working with learning plugins
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from datetime import datetime

from core.adaptive_orchestrator import AdaptiveOrchestrator
from core.goal_driven_agent import GoalDrivenAgent
from core.forecasting_engine import ForecastingEngine
from core.dynamic_config_manager import get_config_manager
from core.learning_data_plugins import (
    LearningDataOrchestrator,
    CustomerSupportDataPlugin,
    SalesResearchDataPlugin,
    BenchmarkDatasetPlugin
)
from core.agent_learning_coordinator import AgentLearningCoordinator


# ============================================================================
# Example 1: Basic Deployment and Learning
# ============================================================================

def example_basic_learning():
    """Basic exponential learning demonstration."""
    print("\n" + "="*70)
    print("Example 1: Basic Exponential Learning")
    print("="*70)
    
    # 1. Create orchestrator
    print("\n1. Creating orchestrator with 3 agents...")
    orchestrator = AdaptiveOrchestrator(
        agent_names=["react", "planning", "evaluator"],
        enable_adaptation=True
    )
    
    # 2. Create goal-driven agent
    print("2. Creating goal-driven agent...")
    goal_agent = GoalDrivenAgent()
    
    # 3. Create learning data orchestrator
    print("3. Setting up learning data plugins...")
    learning_data = LearningDataOrchestrator()
    learning_data.register_plugin(CustomerSupportDataPlugin())
    learning_data.register_plugin(BenchmarkDatasetPlugin())
    
    # 4. Create learning coordinator
    print("4. Creating learning coordinator...")
    coordinator = AgentLearningCoordinator(
        orchestrator=orchestrator,
        goal_driven_agent=goal_agent,
        learning_data_orchestrator=learning_data
    )
    
    # 5. Run learning loop
    print("\n5. Starting learning loop (10 iterations)...")
    report = coordinator.start_exponential_learning_loop(
        iterations=10,
        batch_size=5,
        report_every=5
    )
    
    # 6. Show results
    print("\n6. Learning Results:")
    print(f"   Final Multiplier: {report['performance']['final_multiplier']:.2f}x")
    print(f"   Strategies Learned: {report['learning']['strategies_learned']}")
    print(f"   Exponential Learning: {report['exponential_learning_achieved']}")
    
    return report


# ============================================================================
# Example 2: Custom Configuration
# ============================================================================

def example_custom_config():
    """Learning with custom configuration."""
    print("\n" + "="*70)
    print("Example 2: Custom Configuration")
    print("="*70)
    
    # Custom orchestrator with specific agents
    print("\n1. Creating custom orchestrator...")
    orchestrator = AdaptiveOrchestrator(
        agent_names=[
            "chain_of_thought",  # For reasoning
            "reflection",        # For self-improvement
            "evaluator"          # For assessment
        ],
        enable_adaptation=True
    )
    
    # Custom goal agent config
    print("2. Creating goal agent with custom config...")
    goal_agent = GoalDrivenAgent(
        agent_config={
            "autonomous_mode": True,
            "goal_generation_interval": 30,
            "max_concurrent_goals": 3
        }
    )
    
    # Forecasting engine
    print("3. Creating forecasting engine...")
    forecasting = ForecastingEngine(config={
        "forecaster": {
            "default_method": "exponential_smoothing",
            "horizon": 10
        },
        "pattern_recognizer": {"enabled": True}
    })
    
    # Dynamic config manager
    print("4. Creating dynamic config manager...")
    config_manager = get_config_manager()
    
    # Learning data with all plugins
    print("5. Setting up all learning plugins...")
    learning_data = LearningDataOrchestrator()
    learning_data.register_plugin(CustomerSupportDataPlugin())
    learning_data.register_plugin(SalesResearchDataPlugin())
    learning_data.register_plugin(BenchmarkDatasetPlugin())
    
    # Coordinator with full integration
    print("6. Creating fully integrated coordinator...")
    coordinator = AgentLearningCoordinator(
        orchestrator=orchestrator,
        goal_driven_agent=goal_agent,
        learning_data_orchestrator=learning_data,
        config_manager=config_manager,
        forecasting_engine=forecasting
    )
    
    # Run with custom parameters
    print("\n7. Running learning with custom parameters...")
    report = coordinator.start_exponential_learning_loop(
        iterations=20,
        batch_size=8,
        report_every=5
    )
    
    print(f"\n8. Results:")
    print(f"   Iterations: {report['summary']['iterations_completed']}")
    print(f"   Total Tasks: {report['summary']['total_tasks_executed']}")
    print(f"   Final Performance: {report['performance']['final_multiplier']:.2f}x")
    
    return report


# ============================================================================
# Example 3: Monitoring Progress
# ============================================================================

def example_monitoring():
    """Monitor learning progress in real-time."""
    print("\n" + "="*70)
    print("Example 3: Progress Monitoring")
    print("="*70)
    
    # Setup
    orchestrator = AdaptiveOrchestrator(agent_names=["react", "planning"])
    goal_agent = GoalDrivenAgent()
    learning_data = LearningDataOrchestrator()
    learning_data.register_plugin(BenchmarkDatasetPlugin())
    
    coordinator = AgentLearningCoordinator(
        orchestrator=orchestrator,
        goal_driven_agent=goal_agent,
        learning_data_orchestrator=learning_data
    )
    
    # Run with frequent reporting
    print("\n1. Running learning with frequent progress reports...")
    report = coordinator.start_exponential_learning_loop(
        iterations=15,
        batch_size=5,
        report_every=3  # Report every 3 iterations
    )
    
    # Analyze learning curve
    print("\n2. Analyzing learning curve:")
    curve = report['learning_curve']
    
    for i, perf in enumerate(curve[-5:], 1):  # Last 5 data points
        print(f"   Point {i}:")
        print(f"     Success Rate: {perf['success_rate']*100:.1f}%")
        print(f"     Avg Latency: {perf['avg_latency']:.0f}ms")
    
    # Check current stats
    print("\n3. Current system statistics:")
    stats = coordinator.get_current_stats()
    print(json.dumps(stats, indent=2, default=str))
    
    return report


# ============================================================================
# Example 4: Working with Learning Plugins
# ============================================================================

def example_plugins():
    """Explore learning data plugins."""
    print("\n" + "="*70)
    print("Example 4: Learning Data Plugins")
    print("="*70)
    
    # Create orchestrator
    learning_data = LearningDataOrchestrator()
    
    # Register plugins
    print("\n1. Registering plugins...")
    learning_data.register_plugin(CustomerSupportDataPlugin())
    learning_data.register_plugin(SalesResearchDataPlugin())
    learning_data.register_plugin(BenchmarkDatasetPlugin())
    
    # List plugins
    print("\n2. Available plugins:")
    plugins = learning_data.list_plugins()
    for plugin in plugins:
        print(f"   - {plugin['name']}: {plugin['description']}")
    
    # Generate sample tasks
    print("\n3. Generating sample tasks from each plugin:")
    
    for plugin_info in plugins:
        plugin_name = plugin_info['name']
        print(f"\n   Plugin: {plugin_name}")
        
        # Generate 2 tasks
        tasks = learning_data.generate_training_batch(
            batch_size=2,
            agent_type=plugin_name
        )
        
        for i, task in enumerate(tasks, 1):
            print(f"   Task {i}:")
            print(f"     ID: {task['id']}")
            print(f"     Description: {task.get('description', 'N/A')}")
            print(f"     Type: {task.get('type', 'N/A')}")
    
    # Get stats
    print("\n4. Plugin statistics:")
    stats = learning_data.get_stats()
    print(json.dumps(stats, indent=2))
    
    return learning_data


# ============================================================================
# Example 5: Analyzing Learning Results
# ============================================================================

def example_analysis():
    """Analyze learning results in detail."""
    print("\n" + "="*70)
    print("Example 5: Results Analysis")
    print("="*70)
    
    # Setup and run learning
    orchestrator = AdaptiveOrchestrator(
        agent_names=["react", "chain_of_thought", "evaluator"]
    )
    goal_agent = GoalDrivenAgent()
    learning_data = LearningDataOrchestrator()
    learning_data.register_plugin(CustomerSupportDataPlugin())
    learning_data.register_plugin(BenchmarkDatasetPlugin())
    
    coordinator = AgentLearningCoordinator(
        orchestrator=orchestrator,
        goal_driven_agent=goal_agent,
        learning_data_orchestrator=learning_data
    )
    
    print("\n1. Running learning...")
    report = coordinator.start_exponential_learning_loop(
        iterations=20,
        batch_size=10
    )
    
    # Analyze performance improvements
    print("\n2. Performance Analysis:")
    perf = report['performance']
    print(f"   Initial Success Rate: {perf['initial']['success_rate']*100:.1f}%")
    print(f"   Final Success Rate: {perf['final']['success_rate']*100:.1f}%")
    print(f"   Improvement: {perf['success_rate_improvement_pct']:.1f}%")
    print()
    print(f"   Initial Latency: {perf['initial']['avg_latency']:.0f}ms")
    print(f"   Final Latency: {perf['final']['avg_latency']:.0f}ms")
    print(f"   Improvement: {perf['latency_improvement_pct']:.1f}%")
    print()
    print(f"   Overall Multiplier: {perf['final_multiplier']:.2f}x")
    
    # Analyze learning
    print("\n3. Learning Analysis:")
    learning = report['learning']
    print(f"   Strategies Learned: {learning['strategies_learned']}")
    print(f"   Config Adjustments: {learning['config_adjustments']}")
    print(f"   Goal Adjustments: {learning['goal_adjustments']}")
    
    print("\n4. Strategy Knowledge:")
    for strategy, details in learning['strategy_knowledge'].items():
        print(f"   {strategy}:")
        print(f"     Success Rate: {details['success_rate']*100:.1f}%")
        print(f"     Avg Latency: {details['avg_latency']:.0f}ms")
    
    # Check milestones
    print("\n5. Milestones Achieved:")
    milestones = report['milestones']
    if milestones['doubled_performance']:
        print("   ✅ Performance Doubled!")
    if milestones['5x_performance']:
        print("   ✅ 5x Performance!")
    if milestones['10x_performance']:
        print("   ✅ 10x Performance!")
    if not any(milestones.values()):
        print("   No major milestones yet")
    
    # Best iteration
    print("\n6. Best Iteration:")
    best = report['best_iteration']
    if best:
        print(f"   Iteration: {best['iteration']}")
        print(f"   Multiplier: {best['multiplier']:.2f}x")
        print(f"   Success Rate: {best['performance']['success_rate']*100:.1f}%")
    
    return report


# ============================================================================
# Example 6: Integration with Existing Systems
# ============================================================================

def example_integration():
    """Show integration with existing monitoring and forecasting."""
    print("\n" + "="*70)
    print("Example 6: System Integration")
    print("="*70)
    
    print("\n1. Integrating all existing systems...")
    
    # Full system integration
    from deploy_exponential_learning import deploy_exponential_learning_system
    
    coordinator = deploy_exponential_learning_system(
        enable_forecasting=True,
        enable_dynamic_config=True
    )
    
    print("\n2. Running integrated learning...")
    report = coordinator.start_exponential_learning_loop(
        iterations=15,
        batch_size=8
    )
    
    print("\n3. Integration Benefits:")
    print("   ✅ Performance monitoring active")
    print("   ✅ Forecasting predictions enabled")
    print("   ✅ Dynamic configuration adjustments")
    print("   ✅ Autonomous goal setting")
    print("   ✅ Safe learning data generation")
    
    print(f"\n4. Final Results:")
    print(f"   Exponential Learning: {report['exponential_learning_achieved']}")
    print(f"   Performance Multiplier: {report['performance']['final_multiplier']:.2f}x")
    
    return report


# ============================================================================
# Main - Run All Examples
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Exponential Learning Examples")
    parser.add_argument(
        "--example",
        type=int,
        choices=[1, 2, 3, 4, 5, 6],
        help="Run specific example (1-6)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all examples"
    )
    
    args = parser.parse_args()
    
    examples = {
        1: ("Basic Learning", example_basic_learning),
        2: ("Custom Configuration", example_custom_config),
        3: ("Progress Monitoring", example_monitoring),
        4: ("Learning Plugins", example_plugins),
        5: ("Results Analysis", example_analysis),
        6: ("System Integration", example_integration)
    }
    
    if args.example:
        # Run specific example
        name, func = examples[args.example]
        print(f"\nRunning Example {args.example}: {name}")
        result = func()
        
    elif args.all:
        # Run all examples
        print("\n" + "="*70)
        print("RUNNING ALL EXAMPLES")
        print("="*70)
        
        for num, (name, func) in examples.items():
            try:
                print(f"\n\n{'='*70}")
                print(f"EXAMPLE {num}: {name}")
                print(f"{'='*70}")
                func()
            except Exception as e:
                print(f"\n❌ Example {num} failed: {e}")
        
        print("\n\n" + "="*70)
        print("ALL EXAMPLES COMPLETED")
        print("="*70)
        
    else:
        # Run default example
        print("\nRunning default example (Basic Learning)")
        print("Use --example N or --all to run other examples")
        example_basic_learning()
