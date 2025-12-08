
# Autonomous Retraining System

## Overview

The **Autonomous Retraining System** enables the PerformanceMonitor to automatically trigger model retraining when it detects performance degradation below predefined thresholds. This creates a self-improving system that continuously adapts to changing conditions without manual intervention.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Performance Monitor                           │
│                                                                    │
│  • Tracks task success rates                                      │
│  • Monitors resource costs                                        │
│  • Measures model accuracy vs real outcomes                       │
│  • Detects performance degradation                                │
│                                                                    │
│         ↓ (When accuracy < threshold)                             │
│         ↓                                                          │
│  [AUTONOMOUS TRIGGER]                                             │
│         ↓                                                          │
└─────────┼──────────────────────────────────────────────────────────┘
          │
          ↓
┌─────────┴──────────────────────────────────────────────────────────┐
│              RealTimeModelUpdater                                   │
│                                                                     │
│  • Receives retraining trigger                                     │
│  • Performs incremental or full retrain                            │
│  • Updates agent selection model                                   │
│  • Saves improved model                                            │
│  • Reports results back                                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

### 1. **Automatic Degradation Detection**
The PerformanceMonitor continuously analyzes:
- **Model accuracy** against real-world outcomes
- **Success rates** across agents
- **Error patterns** and trends
- **Quality scores** over time

### 2. **Autonomous Retraining Triggers**
When performance degrades below thresholds:
```python
# Default threshold: 70% accuracy
if avg_accuracy < 0.70:
    trigger_retraining(
        reason="Accuracy dropped to X%",
        force_full_retrain=False  # Start with incremental
    )
```

### 3. **Two Retraining Modes**

#### Incremental Retraining (Default)
- Processes recent events with higher learning weight
- Fast (typically <100ms)
- Preserves existing knowledge
- Used for minor corrections

#### Full Retraining (Aggressive)
- Resets model completely
- Replays all buffered events
- Slower but thorough
- Used for major degradation

### 4. **Configurable Thresholds**
```python
alert_thresholds = {
    "accuracy_min": 0.70,         # Trigger if accuracy < 70%
    "success_rate_min": 0.80,     # Trigger if success < 80%
    "error_rate_max": 0.15,       # Trigger if errors > 15%
}
```

## Setup

### 1. Install Dependencies

```bash
# Install Kafka (required for RealTimeModelUpdater)
pip install kafka-python

# Or use Docker for Kafka
docker run -d --name kafka \
  -p 9092:9092 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  confluentinc/cp-kafka:latest
```

### 2. Initialize Components

```python
from core.performance_monitor import PerformanceMonitor
from core.online_learning import RealTimeModelUpdater

# Create model updater
model_updater = RealTimeModelUpdater(
    kafka_servers="localhost:9092",
    kafka_topic="agent-outcomes",
    batch_size=10,
    model_storage_path="./models",
    enable_auto_save=True
)
model_updater.start()

# Create monitor with auto-retraining
monitor = PerformanceMonitor(
    window_size_minutes=60,
    enable_auto_retraining=True,     # Enable autonomous retraining
    model_updater=model_updater,     # Connect to model updater
    alert_thresholds={
        "accuracy_min": 0.70          # Trigger at 70%
    }
)
monitor.start()
```

### 3. Record Performance Data

```python
# Record agent runs
monitor.record_agent_run(
    run_id="run_123",
    agent_name="DataAgent",
    agent_type="data_processor",
    status="success",
    duration_ms=450,
    tokens_used=1000,
    cost=0.02
)

# Record accuracy against real outcomes
monitor.record_accuracy(
    agent_name="DataAgent",
    task_id="task_456",
    predicted_outcome={"sales": 10000},
    actual_outcome={"sales": 9500},
    feedback_source="user"
)
```

## Usage

### Automatic Retraining
The system automatically triggers retraining when thresholds are breached:

```python
# The monitor continuously checks in background
# When accuracy drops below 70%:
# 🚨 Accuracy degraded to 65% (threshold: 70%) - Triggering autonomous retraining...
# 🔄 RETRAINING TRIGGERED: agent_selection - Reason: Accuracy dropped to 65%
# ✅ Autonomous retraining completed: 100 events processed
```

### Manual Retraining
You can also trigger retraining manually:

```python
# Incremental retraining
result = monitor.trigger_retraining(
    reason="Manual improvement",
    force_full_retrain=False
)

# Full retraining (reset model)
result = monitor.trigger_retraining(
    reason="Major architecture change",
    force_full_retrain=True
)

# Check result
if result['success']:
    print(f"Retraining completed: {result['events_processed']} events")
```

### Via API

```bash
# Trigger incremental retraining
curl -X POST http://localhost:8000/api/performance/trigger-retraining \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Manual trigger via API",
    "force_full_retrain": false
  }'

# Trigger full retraining
curl -X POST http://localhost:8000/api/performance/trigger-retraining \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Complete model reset",
    "force_full_retrain": true
  }'
```

## Configuration

### Retraining Thresholds

```python
monitor = PerformanceMonitor(
    enable_auto_retraining=True,
    alert_thresholds={
        # Accuracy threshold
        "accuracy_min": 0.70,         # Default: 70%
        
        # Other thresholds (optional)
        "success_rate_min": 0.80,     # Default: 80%
        "error_rate_max": 0.15,       # Default: 15%
        "latency_p95_max_ms": 5000,   # Default: 5 seconds
    }
)
```

### Model Updater Configuration

```python
model_updater = RealTimeModelUpdater(
    kafka_servers="localhost:9092",
    kafka_topic="agent-outcomes",
    
    # Batch processing
    batch_size=10,                    # Events per batch
    batch_timeout_seconds=30,         # Max wait for batch
    
    # Model storage
    model_storage_path="./models",
    enable_auto_save=True,
    save_interval_seconds=300,        # Save every 5 minutes
    
    # Update strategy
    update_strategy=UpdateStrategy.EXPONENTIAL
)
```

## Monitoring Retraining

### Check System Stats

```python
stats = monitor.get_stats()

print(f"Auto-Retraining Enabled: {stats['auto_retraining_enabled']}")
print(f"Model Updater Connected: {stats['model_updater_connected']}")
```

### Review Alerts

```python
alerts = monitor.get_alerts(limit=10)

for alert in alerts:
    if "retrain" in alert.message.lower():
        print(f"[{alert.level}] {alert.message}")
        print(f"Details: {alert.details}")
```

### Generate Report

```python
report = monitor.generate_report(include_agents=True)

print(f"Health Score: {report['health_score']:.1f}/100")
print(f"\nRecommendations:")
for rec in report['recommendations']:
    print(f"  • {rec}")
```

## Examples

### Example 1: Basic Integration

```python
from core.performance_monitor import init_performance_monitor
from core.online_learning import RealTimeModelUpdater

# Setup model updater
model_updater = RealTimeModelUpdater(
    kafka_servers="localhost:9092",
    kafka_topic="agent-outcomes"
)
model_updater.start()

# Setup monitor with auto-retraining
monitor = init_performance_monitor(
    enable_auto_retraining=True,
    model_updater=model_updater
)

# The system now runs autonomously!
```

### Example 2: Custom Thresholds

```python
monitor = PerformanceMonitor(
    enable_auto_retraining=True,
    model_updater=model_updater,
    alert_thresholds={
        "accuracy_min": 0.75,       # More aggressive: retrain at 75%
        "success_rate_min": 0.85    # Higher success requirement
    }
)
```

### Example 3: Simulation Test

```bash
# Run the complete demo
cd /home/ubuntu/powerhouse_b2b_platform/backend
python examples/autonomous_retraining_example.py
```

This will:
1. Set up integrated monitoring
2. Simulate good performance (90% accuracy)
3. Simulate degradation (65% accuracy)
4. Trigger autonomous retraining
5. Test manual retraining
6. Display comprehensive results

## Best Practices

### 1. **Set Appropriate Thresholds**
- Too low: Models won't improve quickly enough
- Too high: Unnecessary retraining overhead
- Recommended: 70-75% accuracy threshold

### 2. **Use Incremental First**
- Start with incremental retraining
- Only use full retrain for major issues
- Full retrain takes longer and discards knowledge

### 3. **Monitor Retraining Results**
```python
# After retraining, check if it helped
before_accuracy = 0.65
retrain_result = monitor.trigger_retraining(...)

# Wait and measure
time.sleep(300)  # 5 minutes
metrics = monitor.get_system_metrics()
after_accuracy = metrics.avg_accuracy

improvement = after_accuracy - before_accuracy
print(f"Improvement: {improvement:+.1%}")
```

### 4. **Buffer Size Matters**
```python
# Larger buffer = better retraining data
model_updater = RealTimeModelUpdater(
    # ... other params ...
    batch_size=20  # More events per batch
)
# The buffer stores 10x batch_size events
```

### 5. **Periodic Full Retraining**
```python
import schedule

# Schedule full retrain weekly
schedule.every().monday.at("03:00").do(
    lambda: monitor.trigger_retraining(
        reason="Weekly full retrain",
        force_full_retrain=True
    )
)
```

## Troubleshooting

### Issue: Retraining Not Triggering

**Check:**
```python
stats = monitor.get_stats()

# Verify configuration
assert stats['auto_retraining_enabled'] == True
assert stats['model_updater_connected'] == True

# Check threshold
metrics = monitor.get_system_metrics()
print(f"Current accuracy: {metrics.avg_accuracy:.1%}")
print(f"Threshold: {monitor.alert_thresholds['accuracy_min']:.1%}")
```

### Issue: Kafka Connection Failed

```bash
# Verify Kafka is running
nc -zv localhost 9092

# Check Kafka logs
docker logs kafka

# Restart Kafka
docker restart kafka
```

### Issue: Retraining Has No Effect

**Possible causes:**
1. Not enough training data in buffer
2. Model type mismatch
3. Events not being recorded properly

**Solution:**
```python
# Check buffer
stats = model_updater.get_metrics()
print(f"Event buffer size: {stats['event_buffer_size']}")

# Should have at least 50-100 events for effective retraining
```

## API Reference

### PerformanceMonitor.trigger_retraining()

```python
def trigger_retraining(
    reason: str = "Manual trigger",
    force_full_retrain: bool = False
) -> Dict[str, Any]
```

**Returns:**
```python
{
    'success': True,
    'model_type': 'agent_selection',
    'retrain_type': 'incremental',  # or 'full'
    'events_processed': 100,
    'duration_ms': 85.2,
    'reason': 'Accuracy dropped to 65%',
    'timestamp': '2025-10-10T12:00:00Z'
}
```

### API Endpoint: POST /api/performance/trigger-retraining

**Request:**
```json
{
  "reason": "Manual trigger via API",
  "force_full_retrain": false
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Retraining completed successfully",
  "result": {
    "success": true,
    "model_type": "agent_selection",
    "retrain_type": "incremental",
    "events_processed": 100,
    "duration_ms": 85.2
  },
  "timestamp": "2025-10-10T12:00:00Z"
}
```

## Performance Impact

### Incremental Retraining
- **Duration:** 50-200ms
- **CPU:** Low impact
- **Memory:** Minimal (processes 100 recent events)
- **Frequency:** Can run every 1-5 minutes

### Full Retraining
- **Duration:** 500ms - 5 seconds (depends on buffer size)
- **CPU:** Moderate impact
- **Memory:** Moderate (reprocesses entire buffer)
- **Frequency:** Recommended: weekly or after major changes

## Conclusion

The Autonomous Retraining System provides:
- ✅ **Self-improving agents** that adapt to changing conditions
- ✅ **Zero manual intervention** for routine performance issues
- ✅ **Continuous learning** from real-world outcomes
- ✅ **Fast recovery** from accuracy degradation
- ✅ **Configurable** thresholds and behavior

The system is production-ready and requires minimal configuration to start delivering value.

---

**Next Steps:**
1. Run the demo: `python examples/autonomous_retraining_example.py`
2. Integrate into your orchestrator
3. Configure thresholds for your use case
4. Monitor results and adjust as needed
