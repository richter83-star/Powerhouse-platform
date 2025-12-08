
"""
Autonomous Goal-Driven Agent - Usage Example

Demonstrates:
1. Starting the autonomous agent
2. Recording metrics and events
3. Monitoring autonomous behavior
4. Viewing goals and predictions
5. Manual interventions
"""

import time
import random
from datetime import datetime

from core.goal_driven_agent import GoalDrivenAgent


def simulate_system_metrics(agent: GoalDrivenAgent, duration_seconds: int = 300):
    """Simulate system metrics for demonstration."""
    print(f"\n{'='*80}")
    print("Simulating System Metrics")
    print(f"{'='*80}\n")
    
    metrics = ["cpu_usage", "memory_usage", "latency", "throughput", "error_rate"]
    events = ["user_login", "api_request", "database_query", "cache_hit", "model_inference"]
    
    start_time = time.time()
    iteration = 0
    
    while (time.time() - start_time) < duration_seconds:
        iteration += 1
        
        # Record metrics
        for metric in metrics:
            if metric == "latency":
                value = random.uniform(100, 300)  # ms
            elif metric == "throughput":
                value = random.uniform(800, 1200)  # req/s
            elif metric == "error_rate":
                value = random.uniform(0.001, 0.02)  # 0.1% to 2%
            else:
                value = random.uniform(40, 80)  # percentage
            
            agent.record_metric(metric, value)
        
        # Record random events
        if random.random() < 0.3:  # 30% chance
            event = random.choice(events)
            agent.record_event(event, metadata={"iteration": iteration})
        
        # Print status every 30 seconds
        if iteration % 6 == 0:
            status = agent.get_agent_status()
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Agent Status:")
            print(f"  Active Goals: {status['active_goals']}")
            print(f"  Goals Created: {status['statistics']['goals_created']}")
            print(f"  Goals Executed: {status['statistics']['goals_executed']}")
            print(f"  Goals Achieved: {status['statistics']['goals_achieved']}")
            print(f"  Uptime: {status['uptime_seconds']:.0f}s")
        
        time.sleep(5)  # Record every 5 seconds


def demonstrate_autonomous_behavior():
    """Demonstrate autonomous goal-driven behavior."""
    print("\n" + "="*80)
    print("Autonomous Goal-Driven Agent - Demonstration")
    print("="*80 + "\n")
    
    # Configuration
    forecasting_config = {
        "auto_analysis_enabled": True,
        "analysis_interval_minutes": 2,  # Faster for demo
        "goal_setter": {
            "auto_goal_setting": True,
            "max_active_goals": 5
        }
    }
    
    executor_config = {
        "execution_interval_seconds": 30,  # Faster for demo
        "max_concurrent_goals": 2,
        "enable_learning": True
    }
    
    agent_config = {
        "autonomous_mode": True,
        "goal_sync_interval_seconds": 15,  # Faster for demo
        "analysis_interval_minutes": 2
    }
    
    # Initialize agent
    print("1. Initializing Autonomous Agent...")
    agent = GoalDrivenAgent(
        forecasting_config=forecasting_config,
        executor_config=executor_config,
        agent_config=agent_config
    )
    
    # Start agent
    print("2. Starting Autonomous Agent...")
    agent.start()
    print("   ✓ Agent started in AUTONOMOUS mode")
    print("   ✓ Forecasting engine active")
    print("   ✓ Goal executor running")
    print("   ✓ Learning system enabled\n")
    
    time.sleep(2)
    
    # Simulate metrics
    print("3. Simulating System Activity...")
    print("   Recording metrics and events for 2 minutes...\n")
    
    try:
        simulate_system_metrics(agent, duration_seconds=120)
        
        # Get comprehensive status
        print("\n" + "="*80)
        print("4. Agent Status After Simulation")
        print("="*80 + "\n")
        
        status = agent.get_agent_status()
        print(f"Running: {status['running']}")
        print(f"Autonomous Mode: {status['autonomous_mode']}")
        print(f"Uptime: {status['uptime_seconds']:.0f} seconds")
        print(f"\nStatistics:")
        print(f"  Goals Created: {status['statistics']['goals_created']}")
        print(f"  Goals Executed: {status['statistics']['goals_executed']}")
        print(f"  Goals Achieved: {status['statistics']['goals_achieved']}")
        print(f"  Total Actions: {status['statistics']['total_actions']}")
        print(f"  Predictions Made: {status['statistics']['total_predictions']}")
        
        # Show active goals
        print("\n" + "="*80)
        print("5. Active Goals")
        print("="*80 + "\n")
        
        goal_overview = agent.get_goal_overview()
        print(f"Total Active Goals: {goal_overview['total_active_goals']}")
        print(f"\nGoals by Type:")
        for goal_type, count in goal_overview['goals_by_type'].items():
            if count > 0:
                print(f"  {goal_type}: {count}")
        
        print(f"\nGoals by Priority:")
        for priority, count in goal_overview['goals_by_priority'].items():
            if count > 0:
                print(f"  {priority}: {count}")
        
        if goal_overview['goals']:
            print("\nGoal Details:")
            for i, goal in enumerate(goal_overview['goals'][:5], 1):
                print(f"\n  Goal {i}:")
                print(f"    ID: {goal['goal_id']}")
                print(f"    Type: {goal['type']}")
                print(f"    Priority: {goal['priority']}")
                print(f"    Description: {goal['description']}")
                print(f"    Progress: {goal['progress']:.1%}")
                print(f"    Status: {goal['status']}")
                if goal.get('execution_status'):
                    print(f"    Execution: {goal['execution_status']['status']}")
        
        # Show predictions
        print("\n" + "="*80)
        print("6. System Predictions (Next 24 Hours)")
        print("="*80 + "\n")
        
        predictions = agent.get_predictions(horizon_hours=24)
        print(f"Current State: {predictions['current_state']}")
        print(f"Predicted State: {predictions['predicted_state']}")
        print(f"Confidence: {predictions['confidence']:.1%}")
        
        if predictions.get('predicted_bottlenecks'):
            print(f"\nPredicted Bottlenecks: {len(predictions['predicted_bottlenecks'])}")
            for bottleneck in predictions['predicted_bottlenecks'][:3]:
                print(f"  - {bottleneck['description']} (Severity: {bottleneck['severity']})")
        
        # Show learning insights
        print("\n" + "="*80)
        print("7. Learning Insights")
        print("="*80 + "\n")
        
        insights = agent.executor.get_learning_insights()
        if insights['enabled']:
            print("Learning System: ACTIVE")
            
            if insights.get('action_success_rates'):
                print("\nAction Success Rates:")
                for action, data in list(insights['action_success_rates'].items())[:5]:
                    print(f"  {action}: {data['rate']:.1%} ({data['samples']} samples)")
            
            if insights.get('common_failures'):
                print("\nCommon Failures:")
                for failure in insights['common_failures'][:3]:
                    print(f"  {failure['action']}: {failure['count']} times")
        
        # Trigger manual analysis
        print("\n" + "="*80)
        print("8. Manual Analysis Trigger")
        print("="*80 + "\n")
        
        print("Forcing comprehensive analysis...")
        result = agent.force_analysis()
        print(f"✓ Analysis completed at {result['timestamp']}")
        
        time.sleep(2)
        
        # Final report
        print("\n" + "="*80)
        print("9. Final Comprehensive Report")
        print("="*80 + "\n")
        
        report = agent.get_comprehensive_report()
        print(f"Report Generated: {report['forecasting_report']['timestamp']}")
        print(f"Total Patterns Detected: {report['forecasting_report']['patterns']['total']}")
        print(f"Total Goals: {report['goals']['total_active_goals']}")
        print(f"Executor Success Rate: {report['executor_state']['statistics'].get('success_rate', 0):.1%}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        # Cleanup
        print("\n" + "="*80)
        print("10. Shutting Down")
        print("="*80 + "\n")
        
        print("Stopping autonomous agent...")
        agent.stop()
        print("✓ Agent stopped")
        print("✓ All components shut down cleanly")
        
        print("\n" + "="*80)
        print("Demonstration Complete!")
        print("="*80 + "\n")


if __name__ == '__main__':
    demonstrate_autonomous_behavior()

