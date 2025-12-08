
"""
Autonomous Retraining Integration Example

This example demonstrates how to set up and use the PerformanceMonitor
with autonomous retraining triggers that automatically update the 
RealTimeModelUpdater when performance degrades.
"""

import asyncio
import time
from datetime import datetime

# Import core components
from core.performance_monitor import (
    PerformanceMonitor,
    init_performance_monitor
)
from core.online_learning import (
    RealTimeModelUpdater,
    ModelType,
    OutcomeEvent,
    OutcomeStatus
)

# Import Kafka for model updater
try:
    from kafka import KafkaProducer
    import json
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    print("Warning: kafka-python not available. Install with: pip install kafka-python")


def setup_integrated_monitoring():
    """
    Set up PerformanceMonitor and RealTimeModelUpdater with integration.
    
    This creates a monitoring system where:
    1. PerformanceMonitor tracks agent performance
    2. When accuracy drops below threshold, it automatically triggers
    3. RealTimeModelUpdater to retrain the model
    """
    
    print("=" * 80)
    print("Setting up Autonomous Retraining System")
    print("=" * 80)
    
    # Step 1: Create the RealTimeModelUpdater (if Kafka is available)
    model_updater = None
    
    if KAFKA_AVAILABLE:
        try:
            model_updater = RealTimeModelUpdater(
                kafka_servers="localhost:9092",
                kafka_topic="agent-outcomes",
                batch_size=10,
                model_storage_path="./models",
                enable_auto_save=True
            )
            
            # Start the model updater
            model_updater.start()
            print("✅ RealTimeModelUpdater initialized and started")
            
        except Exception as e:
            print(f"⚠️  Could not connect to Kafka: {e}")
            print("   Continuing without model updater (retraining will be disabled)")
    else:
        print("⚠️  Kafka not available - retraining features will be disabled")
    
    # Step 2: Create PerformanceMonitor with auto-retraining enabled
    monitor = PerformanceMonitor(
        window_size_minutes=60,
        enable_auto_alerts=True,
        enable_trend_analysis=True,
        enable_auto_retraining=True,  # Enable autonomous retraining
        model_updater=model_updater,  # Connect to model updater
        alert_thresholds={
            "accuracy_min": 0.70,  # Trigger retraining if accuracy < 70%
            "success_rate_min": 0.80,
            "error_rate_max": 0.15
        }
    )
    
    # Start the monitor
    monitor.start()
    print("✅ PerformanceMonitor initialized with autonomous retraining")
    
    return monitor, model_updater


def simulate_performance_degradation(monitor: PerformanceMonitor):
    """
    Simulate agent runs with degrading accuracy to trigger autonomous retraining.
    """
    print("\n" + "=" * 80)
    print("Simulating Agent Performance with Degrading Accuracy")
    print("=" * 80)
    
    # Phase 1: Good performance (accuracy ~90%)
    print("\n📊 Phase 1: Good Performance (90% accuracy)")
    for i in range(10):
        monitor.record_agent_run(
            run_id=f"run_good_{i}",
            agent_name="TestAgent",
            agent_type="general",
            status="success",
            duration_ms=500 + (i * 10),
            tokens_used=1000,
            cost=0.02,
            quality_score=0.9
        )
        
        # Record accuracy
        monitor.record_accuracy(
            agent_name="TestAgent",
            task_id=f"task_good_{i}",
            predicted_outcome={"result": "success"},
            actual_outcome={"result": "success"},
            feedback_source="automated"
        )
    
    print(f"   ✓ Recorded 10 runs with 90% accuracy")
    time.sleep(2)
    
    # Check metrics
    metrics = monitor.get_system_metrics()
    print(f"   Current accuracy: {metrics.avg_accuracy:.1%}")
    
    # Phase 2: Degrading performance (accuracy ~65%)
    print("\n📉 Phase 2: Degrading Performance (65% accuracy)")
    print("   This should trigger autonomous retraining...")
    
    for i in range(20):
        # Mix of successes and failures
        status = "success" if i % 3 != 0 else "failure"
        
        monitor.record_agent_run(
            run_id=f"run_bad_{i}",
            agent_name="TestAgent",
            agent_type="general",
            status=status,
            duration_ms=800 + (i * 20),
            tokens_used=1200,
            cost=0.03,
            quality_score=0.6
        )
        
        # Record poor accuracy
        predicted = {"result": "success"}
        actual = {"result": "success" if i % 3 != 0 else "failure"}
        
        monitor.record_accuracy(
            agent_name="TestAgent",
            task_id=f"task_bad_{i}",
            predicted_outcome=predicted,
            actual_outcome=actual,
            feedback_source="automated"
        )
    
    print(f"   ✓ Recorded 20 runs with degraded performance")
    time.sleep(3)
    
    # Check metrics and alerts
    metrics = monitor.get_system_metrics()
    print(f"\n   📊 Current Metrics:")
    print(f"      - Accuracy: {metrics.avg_accuracy:.1%}")
    print(f"      - Success Rate: {metrics.success_rate:.1%}")
    print(f"      - Avg Latency: {metrics.avg_latency_ms:.0f}ms")
    
    # Get alerts
    alerts = monitor.get_alerts(limit=10)
    print(f"\n   🚨 Recent Alerts ({len(alerts)} total):")
    for alert in alerts[-5:]:
        print(f"      [{alert.level.upper()}] {alert.message}")
        if alert.recommendation:
            print(f"         → {alert.recommendation}")


def test_manual_retraining(monitor: PerformanceMonitor):
    """
    Test manual retraining trigger.
    """
    print("\n" + "=" * 80)
    print("Testing Manual Retraining Trigger")
    print("=" * 80)
    
    print("\n🔄 Triggering manual retraining...")
    
    result = monitor.trigger_retraining(
        reason="Manual test of retraining functionality",
        force_full_retrain=False
    )
    
    if result.get('success'):
        print(f"\n✅ Retraining Successful!")
        print(f"   - Model Type: {result.get('model_type')}")
        print(f"   - Retrain Type: {result.get('retrain_type')}")
        print(f"   - Events Processed: {result.get('events_processed', 0)}")
        print(f"   - Duration: {result.get('duration_ms', 0):.0f}ms")
    else:
        print(f"\n❌ Retraining Failed: {result.get('error')}")


def test_full_retraining(monitor: PerformanceMonitor):
    """
    Test full retraining (resets model completely).
    """
    print("\n" + "=" * 80)
    print("Testing Full Retraining")
    print("=" * 80)
    
    print("\n🔄 Triggering FULL retraining (model reset)...")
    
    result = monitor.trigger_retraining(
        reason="Full model reset for testing",
        force_full_retrain=True
    )
    
    if result.get('success'):
        print(f"\n✅ Full Retraining Successful!")
        print(f"   - Model completely reset and retrained")
        print(f"   - Events Replayed: {result.get('events_processed', 0)}")
        print(f"   - Agents Tracked: {result.get('agents_tracked', 0)}")
        print(f"   - Duration: {result.get('duration_ms', 0):.0f}ms")
    else:
        print(f"\n❌ Full Retraining Failed: {result.get('error')}")


def display_final_stats(monitor: PerformanceMonitor):
    """
    Display final statistics and configuration.
    """
    print("\n" + "=" * 80)
    print("Final System Statistics")
    print("=" * 80)
    
    stats = monitor.get_stats()
    
    print(f"\n📊 Monitor Stats:")
    print(f"   - Events Buffered: {stats['events_buffered']}")
    print(f"   - Agents Tracked: {stats['agents_tracked']}")
    print(f"   - Accuracy Measurements: {stats['accuracy_measurements']}")
    print(f"   - Active Alerts: {stats['active_alerts']}")
    print(f"   - Monitoring Active: {stats['monitoring_active']}")
    print(f"   - Auto-Retraining Enabled: {stats['auto_retraining_enabled']}")
    print(f"   - Model Updater Connected: {stats['model_updater_connected']}")
    
    # Generate comprehensive report
    print(f"\n📄 Generating Performance Report...")
    report = monitor.generate_report(include_agents=True)
    
    print(f"\n   Health Score: {report['health_score']:.1f}/100")
    print(f"\n   Recommendations:")
    for rec in report['recommendations']:
        print(f"      • {rec}")


def main():
    """
    Main execution function.
    """
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "AUTONOMOUS RETRAINING DEMO" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    # Setup
    monitor, model_updater = setup_integrated_monitoring()
    
    try:
        # Wait for initialization
        time.sleep(2)
        
        # Simulate performance degradation (this should trigger auto-retraining)
        simulate_performance_degradation(monitor)
        
        # Wait for background processing
        print("\n⏳ Waiting for background processing...")
        time.sleep(5)
        
        # Test manual retraining
        if monitor.model_updater:
            test_manual_retraining(monitor)
            time.sleep(2)
            
            test_full_retraining(monitor)
            time.sleep(2)
        
        # Display final stats
        display_final_stats(monitor)
        
        print("\n" + "=" * 80)
        print("✅ Autonomous Retraining Demo Completed Successfully!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        monitor.stop()
        
        if model_updater:
            model_updater.stop()
        
        print("✅ Cleanup complete\n")


if __name__ == "__main__":
    main()
