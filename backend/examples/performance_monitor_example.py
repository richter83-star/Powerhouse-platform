
"""
Example usage of the Performance Monitor service.

This script demonstrates how to integrate and use the Performance Monitor
to track agent performance, record accuracy, and generate reports.
"""

import time
import random
from datetime import datetime

from core.performance_monitor import (
    get_performance_monitor,
    init_performance_monitor,
    AlertLevel
)
from utils.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def simulate_agent_runs(monitor, num_runs=50):
    """Simulate agent run events for demonstration."""
    agent_types = ["react", "evaluator", "debate", "governor"]
    statuses = ["success", "success", "success", "failure"]  # 75% success rate
    
    logger.info(f"Simulating {num_runs} agent runs...")
    
    for i in range(num_runs):
        agent_name = f"agent_{random.choice(agent_types)}"
        agent_type = random.choice(agent_types)
        status = random.choice(statuses)
        
        # Simulate realistic metrics
        duration_ms = random.gauss(1500, 500) if status == "success" else random.gauss(3000, 1000)
        duration_ms = max(100, duration_ms)
        
        tokens_used = random.randint(150, 350) if status == "success" else random.randint(400, 600)
        cost = tokens_used * 0.0002  # ~$0.02 per 100 tokens
        
        quality_score = random.gauss(0.85, 0.1) if status == "success" else random.gauss(0.5, 0.15)
        quality_score = max(0.0, min(1.0, quality_score))
        
        confidence = random.gauss(0.8, 0.12) if status == "success" else random.gauss(0.4, 0.15)
        confidence = max(0.0, min(1.0, confidence))
        
        # Record the run
        monitor.record_agent_run(
            run_id=f"run_{i}_{int(time.time()*1000)}",
            agent_name=agent_name,
            agent_type=agent_type,
            status=status,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            cost=cost,
            quality_score=quality_score,
            confidence=confidence,
            error_type="timeout" if status == "failure" and random.random() > 0.5 else None
        )
        
        # Small delay to simulate real execution
        time.sleep(0.05)
    
    logger.info("Agent run simulation completed")


def simulate_accuracy_measurements(monitor, num_measurements=20):
    """Simulate accuracy measurements for demonstration."""
    logger.info(f"Simulating {num_measurements} accuracy measurements...")
    
    agent_names = ["agent_react", "agent_evaluator", "agent_debate"]
    
    for i in range(num_measurements):
        agent_name = random.choice(agent_names)
        
        # Simulate predicted vs actual outcomes
        predicted_value = random.randint(80, 120)
        actual_value = predicted_value + random.randint(-15, 15)
        
        monitor.record_accuracy(
            agent_name=agent_name,
            task_id=f"task_{i}",
            predicted_outcome={"value": predicted_value, "confidence": 0.8},
            actual_outcome={"value": actual_value},
            feedback_source="automated" if random.random() > 0.3 else "user",
            metadata={"task_type": "prediction"}
        )
        
        time.sleep(0.03)
    
    logger.info("Accuracy measurement simulation completed")


def main():
    """Main demonstration function."""
    logger.info("=" * 80)
    logger.info("Performance Monitor Example")
    logger.info("=" * 80)
    
    # Initialize performance monitor with custom settings
    logger.info("\n1. Initializing Performance Monitor...")
    monitor = init_performance_monitor(
        window_size_minutes=60,
        alert_thresholds={
            "success_rate_min": 0.70,  # Trigger alert if below 70%
            "latency_p95_max_ms": 4000,
            "cost_per_task_max": 0.20
        },
        enable_auto_alerts=True,
        enable_trend_analysis=True
    )
    
    logger.info(f"Monitor initialized: {monitor}")
    
    # Simulate agent runs
    logger.info("\n2. Simulating agent runs...")
    simulate_agent_runs(monitor, num_runs=100)
    
    # Simulate accuracy measurements
    logger.info("\n3. Recording accuracy measurements...")
    simulate_accuracy_measurements(monitor, num_measurements=30)
    
    # Get system metrics
    logger.info("\n4. Retrieving system-wide metrics...")
    system_metrics = monitor.get_system_metrics()
    
    logger.info("\nSystem Performance Metrics:")
    logger.info(f"  Total Tasks: {system_metrics.total_tasks}")
    logger.info(f"  Success Rate: {system_metrics.success_rate:.1%}")
    logger.info(f"  Error Rate: {system_metrics.error_rate:.1%}")
    logger.info(f"  Avg Latency: {system_metrics.avg_latency_ms:.0f}ms")
    logger.info(f"  P95 Latency: {system_metrics.p95_latency_ms:.0f}ms")
    logger.info(f"  Total Tokens: {system_metrics.total_tokens:,}")
    logger.info(f"  Total Cost: ${system_metrics.total_cost:.4f}")
    logger.info(f"  Avg Quality: {system_metrics.avg_quality_score:.2f}")
    logger.info(f"  Avg Accuracy: {system_metrics.avg_accuracy:.2f}")
    
    # Get per-agent metrics
    logger.info("\n5. Retrieving per-agent metrics...")
    
    with monitor._lock:
        agent_names = list(monitor._agent_metrics.keys())
    
    for agent_name in agent_names[:3]:  # Show first 3 agents
        agent_perf = monitor.get_agent_metrics(agent_name)
        logger.info(f"\nAgent: {agent_name}")
        logger.info(f"  Type: {agent_perf.agent_type}")
        logger.info(f"  Status: {agent_perf.status}")
        logger.info(f"  Tasks: {agent_perf.metrics.total_tasks}")
        logger.info(f"  Success Rate: {agent_perf.metrics.success_rate:.1%}")
        logger.info(f"  Avg Latency: {agent_perf.metrics.avg_latency_ms:.0f}ms")
        logger.info(f"  Specialization Score: {agent_perf.specialization_score:.2f}")
        logger.info(f"  Reliability Score: {agent_perf.reliability_score:.2f}")
        logger.info(f"  Efficiency Score: {agent_perf.efficiency_score:.2f}")
    
    # Check for alerts
    logger.info("\n6. Checking for alerts...")
    alerts = monitor.get_alerts(limit=10)
    
    if alerts:
        logger.info(f"\nFound {len(alerts)} alerts:")
        for alert in alerts:
            logger.info(f"  [{alert.level.value.upper()}] {alert.message}")
            logger.info(f"    Current: {alert.current_value}, Threshold: {alert.threshold}")
            if alert.recommendation:
                logger.info(f"    Recommendation: {alert.recommendation}")
    else:
        logger.info("No alerts detected - system is performing well!")
    
    # Generate comprehensive report
    logger.info("\n7. Generating comprehensive performance report...")
    report = monitor.generate_report(include_agents=True)
    
    logger.info(f"\nPerformance Report:")
    logger.info(f"  Generated At: {report['generated_at']}")
    logger.info(f"  Time Window: {report['time_window_minutes']} minutes")
    logger.info(f"  Health Score: {report['health_score']:.1f}/100")
    
    logger.info(f"\n  Recommendations:")
    for i, recommendation in enumerate(report['recommendations'], 1):
        logger.info(f"    {i}. {recommendation}")
    
    logger.info(f"\n  Agent Summary:")
    logger.info(f"    Total Agents Tracked: {len(report.get('agent_metrics', {}))}")
    
    # Get monitor statistics
    logger.info("\n8. Monitor Statistics...")
    stats = monitor.get_stats()
    logger.info(f"  Events Buffered: {stats['events_buffered']}")
    logger.info(f"  Agents Tracked: {stats['agents_tracked']}")
    logger.info(f"  Accuracy Measurements: {stats['accuracy_measurements']}")
    logger.info(f"  Active Alerts: {stats['active_alerts']}")
    logger.info(f"  Monitoring Active: {stats['monitoring_active']}")
    
    # Calculate health score
    health_score = monitor._calculate_health_score(system_metrics)
    logger.info(f"\n9. Overall System Health: {health_score:.1f}/100")
    
    if health_score >= 80:
        logger.info("   Status: EXCELLENT ✓")
    elif health_score >= 60:
        logger.info("   Status: GOOD ✓")
    elif health_score >= 40:
        logger.info("   Status: FAIR ⚠")
    else:
        logger.info("   Status: POOR ✗")
    
    logger.info("\n" + "=" * 80)
    logger.info("Example completed successfully!")
    logger.info("=" * 80)
    
    # Cleanup
    monitor.stop()


if __name__ == "__main__":
    main()
