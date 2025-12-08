
"""
Startup Script with Dynamic Self-Configuration

Starts the agent system with dynamic configuration enabled.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from core.adaptive_orchestrator import AdaptiveOrchestrator
from core.performance_monitor_with_config import get_adaptive_monitor
from core.dynamic_config_manager import get_config_manager, AdjustmentStrategy
from utils.logging import get_logger

logger = get_logger(__name__)


def initialize_system(
    agent_names: list = None,
    adjustment_strategy: AdjustmentStrategy = AdjustmentStrategy.BALANCED,
    enable_adaptation: bool = True
):
    """
    Initialize the agent system with dynamic configuration.
    
    Args:
        agent_names: List of agent names to load
        adjustment_strategy: Strategy for parameter adjustments
        enable_adaptation: Enable dynamic configuration
        
    Returns:
        Initialized orchestrator
    """
    
    if agent_names is None:
        agent_names = [
            "planning",
            "react",
            "chain_of_thought",
            "reflection",
            "evaluator",
            "governor"
        ]
    
    logger.info("="*70)
    logger.info("INITIALIZING AGENT SYSTEM WITH DYNAMIC SELF-CONFIGURATION")
    logger.info("="*70)
    
    # Initialize configuration manager
    config_manager = get_config_manager(strategy=adjustment_strategy)
    logger.info(f"Configuration Manager: {adjustment_strategy.value} strategy")
    
    # Initialize adaptive monitor
    monitor = get_adaptive_monitor(
        enable_dynamic_config=enable_adaptation,
        adjustment_strategy=adjustment_strategy,
        adjustment_interval_seconds=60
    )
    logger.info(f"Performance Monitor: Dynamic config {'ENABLED' if enable_adaptation else 'DISABLED'}")
    
    # Create adaptive orchestrator
    orchestrator = AdaptiveOrchestrator(
        agent_names=agent_names,
        enable_adaptation=enable_adaptation
    )
    logger.info(f"Orchestrator: Loaded {len(agent_names)} agents")
    
    # Print initial configuration
    snapshot = config_manager.get_configuration_snapshot()
    logger.info("\nInitial Configuration:")
    for param, value in snapshot['parameters'].items():
        logger.info(f"  {param}: {value}")
    
    logger.info("\nActive Adjustment Rules:")
    for name, info in snapshot['active_rules'].items():
        status = "✓" if info['enabled'] else "✗"
        logger.info(f"  {status} {name}")
    
    logger.info("\n" + "="*70)
    logger.info("SYSTEM READY")
    logger.info("="*70 + "\n")
    
    return orchestrator


def main():
    """Main entry point."""
    
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Start agent system with dynamic self-configuration"
    )
    
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["conservative", "balanced", "aggressive", "gradual"],
        default="balanced",
        help="Adjustment strategy"
    )
    
    parser.add_argument(
        "--disable-adaptation",
        action="store_true",
        help="Disable dynamic configuration"
    )
    
    parser.add_argument(
        "--agents",
        type=str,
        nargs="+",
        help="Agent names to load"
    )
    
    args = parser.parse_args()
    
    # Map strategy string to enum
    strategy_map = {
        "conservative": AdjustmentStrategy.CONSERVATIVE,
        "balanced": AdjustmentStrategy.BALANCED,
        "aggressive": AdjustmentStrategy.AGGRESSIVE,
        "gradual": AdjustmentStrategy.GRADUAL
    }
    
    strategy = strategy_map[args.strategy]
    
    # Initialize system
    orchestrator = initialize_system(
        agent_names=args.agents,
        adjustment_strategy=strategy,
        enable_adaptation=not args.disable_adaptation
    )
    
    # Example: Run some tasks
    print("\nRunning example tasks...")
    
    tasks = [
        "Analyze the current market trends",
        "Generate a summary of recent events",
        "Plan a project timeline",
        "Evaluate the quality of the output"
    ]
    
    for task in tasks:
        print(f"\nTask: {task}")
        try:
            result = orchestrator.run(task)
            print(f"Status: {'✓ Success' if 'error' not in result else '✗ Error'}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Print performance summary
    print("\n" + "="*70)
    summary = orchestrator.get_performance_summary()
    print("PERFORMANCE SUMMARY")
    print("="*70)
    print(f"Health Score: {summary.get('health_score', 'N/A')}/100")
    
    if summary.get('performance'):
        perf = summary['performance']
        print(f"Success Rate: {perf.get('success_rate', 0)*100:.1f}%")
        print(f"Avg Latency: {perf.get('avg_latency_ms', 0):.0f}ms")
        print(f"Error Rate: {perf.get('error_rate', 0)*100:.1f}%")
    
    if summary.get('configuration'):
        config = summary['configuration']
        stats = config.get('statistics', {})
        print(f"\nConfiguration Changes: {stats.get('total_changes', 0)}")
        print(f"Rollbacks: {stats.get('rollbacks', 0)}")
    
    print("="*70)


if __name__ == "__main__":
    main()

