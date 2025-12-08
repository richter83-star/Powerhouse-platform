
"""
Startup script for agent system with full forecasting capabilities.

Initializes and runs:
- Performance Monitoring
- Dynamic Self-Configuration
- Forecasting Engine with Proactive Goal Setting
- Orchestrator with all features
"""

import asyncio
import signal
import sys
from datetime import datetime

from utils.logging import get_logger
from core.orchestrator_with_forecasting import OrchestratorWithForecasting
from api.routes import forecasting_routes

logger = get_logger(__name__)

# Global orchestrator instance
orchestrator = None


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Shutdown signal received")
    if orchestrator:
        orchestrator.shutdown()
    sys.exit(0)


async def main():
    """Main entry point."""
    global orchestrator
    
    print("=" * 80)
    print("AGENT SYSTEM WITH FORECASTING ENGINE")
    print("=" * 80)
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configuration
    performance_config = {
        "alert_thresholds": {
            "error_rate": 0.05,
            "latency_ms": 1000,
            "token_budget": 900000
        },
        "monitoring_interval": 60,
        "enable_autonomous_retraining": True
    }
    
    dynamic_config = {
        "adjustment_strategy": "balanced",
        "monitoring_interval": 300,
        "enable_auto_rollback": True
    }
    
    forecasting_config = {
        "forecaster": {
            "max_history_size": 1000,
            "min_history_for_forecast": 10,
            "default_horizon": 24
        },
        "pattern_recognizer": {
            "max_history_size": 10000,
            "min_confidence_threshold": 0.7
        },
        "predictive_model": {
            "resource_capacities": {
                "cpu": 100.0,
                "memory": 100.0,
                "api_calls": 10000.0,
                "token_budget": 1000000.0,
                "storage": 1000.0,
                "network": 1000.0
            },
            "thresholds": {
                "optimal": 60.0,
                "healthy": 75.0,
                "degraded": 85.0,
                "critical": 95.0
            }
        },
        "goal_setter": {
            "auto_goal_setting": True,
            "max_active_goals": 10,
            "goal_review_interval_hours": 6
        },
        "auto_analysis_enabled": True,
        "analysis_interval_minutes": 60
    }
    
    # Initialize orchestrator
    logger.info("Initializing orchestrator with forecasting...")
    orchestrator = OrchestratorWithForecasting(
        performance_monitor_config=performance_config,
        config_manager_config=dynamic_config,
        forecasting_config=forecasting_config
    )
    
    print("✓ Orchestrator initialized")
    print("✓ Performance Monitor active")
    print("✓ Dynamic Config Manager active")
    print("✓ Forecasting Engine active")
    print()
    
    # Initialize API forecasting engine reference
    forecasting_routes.initialize_forecasting_engine(forecasting_config)
    print("✓ API endpoints initialized")
    print()
    
    # Print capabilities
    print("CAPABILITIES:")
    print("  • Real-time performance monitoring")
    print("  • Autonomous retraining on degradation")
    print("  • Dynamic parameter self-configuration")
    print("  • Time series forecasting (ARIMA, SARIMA, Ensemble)")
    print("  • Pattern recognition (recurring tasks, spikes, trends)")
    print("  • Predictive state modeling")
    print("  • Proactive goal setting")
    print("  • Bottleneck prevention")
    print("  • Automated optimization")
    print()
    
    # Example: Run some agents with monitoring and forecasting
    print("=" * 80)
    print("RUNNING EXAMPLE WORKFLOW")
    print("=" * 80)
    print()
    
    tasks = [
        ("planning_agent", "Create a strategic plan for product launch"),
        ("research_agent", "Research market trends for Q4 2025"),
        ("reflection_agent", "Review and improve previous planning outputs")
    ]
    
    for agent_name, task_desc in tasks:
        print(f"Executing: {agent_name}")
        print(f"Task: {task_desc}")
        
        try:
            result = await orchestrator.execute_with_forecasting(
                agent_name=agent_name,
                task_description=task_desc,
                context={"priority": "high"}
            )
            
            print(f"✓ Success: {result.get('status', 'completed')}")
            
            if "metrics" in result:
                print(f"  Metrics: {result['metrics']}")
            
            if "forecasting" in result:
                print(f"  Active goals: {result['forecasting']['active_goals']}")
                print(f"  Patterns detected: {result['forecasting']['detected_patterns']}")
            
            print()
            
        except Exception as e:
            logger.error(f"Error executing {agent_name}: {e}")
            print(f"✗ Error: {e}")
            print()
    
    # Get comprehensive report
    print("=" * 80)
    print("FORECASTING REPORT")
    print("=" * 80)
    print()
    
    report = orchestrator.get_forecasting_report()
    
    print(f"Statistics:")
    print(f"  Total forecasts: {report['statistics']['total_forecasts']}")
    print(f"  Patterns detected: {report['statistics']['total_patterns_detected']}")
    print(f"  System predictions: {report['statistics']['total_predictions']}")
    print()
    
    print(f"Goals:")
    print(f"  Active: {report['goals']['active']}")
    print(f"  Total: {report['goals']['total']}")
    print(f"  Achievement rate: {report['goals']['achievement_rate'] * 100:.0f}%")
    print()
    
    if report['goals']['active'] > 0:
        print("Active Goals:")
        for goal in report['goals']['active_goals'][:5]:
            print(f"  • {goal['goal_type']}: {goal['description']}")
            print(f"    Priority: {goal['priority']}, Progress: {goal['progress'] * 100:.0f}%")
        print()
    
    # Predict future state
    print("=" * 80)
    print("SYSTEM STATE PREDICTION")
    print("=" * 80)
    print()
    
    prediction = orchestrator.predict_future_state(horizon_hours=24)
    
    print(f"Current State: {prediction['current_state']}")
    print(f"Predicted State (24h): {prediction['predicted_state']}")
    print(f"Confidence: {prediction['confidence'] * 100:.0f}%")
    print()
    
    if prediction['predicted_bottlenecks']:
        print("Predicted Bottlenecks:")
        for bottleneck in prediction['predicted_bottlenecks'][:3]:
            print(f"  ⚠️  {bottleneck['location']} ({bottleneck['severity']})")
            print(f"     {bottleneck['description']}")
        print()
    
    if prediction['recommendations']:
        print("Recommendations:")
        for rec in prediction['recommendations'][:5]:
            print(f"  💡 {rec}")
        print()
    
    # Keep running
    print("=" * 80)
    print("System is running. Press Ctrl+C to stop.")
    print("=" * 80)
    print()
    print("API Endpoints available at:")
    print("  • GET  /forecasting/health")
    print("  • POST /forecasting/forecast")
    print("  • POST /forecasting/predict")
    print("  • GET  /forecasting/goals")
    print("  • GET  /forecasting/report")
    print()
    
    try:
        # Keep the system running
        while True:
            await asyncio.sleep(60)
            
            # Periodic status update
            stats = orchestrator.forecasting_engine.get_statistics()
            logger.info(
                f"Status: {stats['active_goals']} active goals, "
                f"{stats['detected_patterns']} patterns detected"
            )
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        # Cleanup
        orchestrator.shutdown()
        print("\nSystem shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
