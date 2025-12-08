
# Internal Performance Monitor

A comprehensive monitoring service that tracks core metrics across the agent architecture, providing real-time insights into task success rates, resource costs, and model accuracy against real-world outcomes.

## Overview

The Performance Monitor is a dedicated service within the agent architecture that continuously tracks, analyzes, and reports on system performance. It provides actionable insights through real-time metrics, trend analysis, and intelligent alerting.

## Key Features

### 1. Task Success Rate Tracking
- **Real-time success/failure monitoring** across all agents
- **Per-agent success rates** with historical trends
- **Error classification** and pattern detection
- **Retry and timeout tracking**

### 2. Resource Cost Monitoring
- **Token usage tracking** for LLM API calls
- **Cost estimation** per task and agent
- **API call counting** and rate analysis
- **Memory and CPU utilization** metrics

### 3. Model Accuracy Measurement
- **Real-world outcome validation** against predictions
- **Flexible accuracy scoring** for different data types
- **Feedback integration** from users and automated systems
- **Accuracy trends** over time

### 4. Performance Alerting
- **Automatic threshold monitoring** for critical metrics
- **Multi-level alerts** (INFO, WARNING, CRITICAL)
- **Actionable recommendations** with each alert
- **Historical alert tracking**

### 5. Trend Analysis
- **Performance trend detection** (improving, stable, degrading)
- **Predictive insights** based on historical data
- **Comparative analysis** across time windows
- **Anomaly detection**

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Performance Monitor                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Event      │  │   Metrics    │  │   Alerting   │     │
│  │   Recording  │  │  Calculation │  │    Engine    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
│              ┌─────────────▼─────────────┐                 │
│              │   In-Memory Buffer        │                 │
│              │   (Rolling 24h window)    │                 │
│              └─────────────┬─────────────┘                 │
│                            │                                │
│              ┌─────────────▼─────────────┐                 │
│              │   Database Integration    │                 │
│              │   (Historical data)       │                 │
│              └───────────────────────────┘                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
    ┌─────▼─────┐     ┌────▼────┐     ┌─────▼─────┐
    │   REST    │     │  Python │     │  Dashboard│
    │    API    │     │   API   │     │    UI     │
    └───────────┘     └─────────┘     └───────────┘
```

## Installation & Setup

### 1. Dependencies

The Performance Monitor is included in the core platform. Ensure all dependencies are installed:

```bash
cd /home/ubuntu/powerhouse_b2b_platform/backend
pip install -r requirements.txt
```

### 2. Initialize the Monitor

#### Option A: In Your Application Code

```python
from core.performance_monitor import init_performance_monitor

# Initialize with custom settings
monitor = init_performance_monitor(
    window_size_minutes=60,           # Rolling time window
    alert_thresholds={
        "success_rate_min": 0.80,     # Alert if below 80%
        "error_rate_max": 0.15,        # Alert if above 15%
        "latency_p95_max_ms": 5000,    # Alert if p95 > 5s
        "cost_per_task_max": 1.0,      # Alert if > $1 per task
        "accuracy_min": 0.70,          # Alert if accuracy < 70%
    },
    enable_auto_alerts=True,
    enable_trend_analysis=True
)

# Start background monitoring
monitor.start()
```

#### Option B: Using the Startup Script

```bash
python scripts/start_with_monitoring.py
```

This starts the FastAPI server with monitoring automatically enabled.

## Usage

### Recording Agent Performance

#### Manual Recording

```python
from core.performance_monitor import get_performance_monitor

monitor = get_performance_monitor()

# Record an agent execution
monitor.record_agent_run(
    run_id="run_123",
    agent_name="react_agent",
    agent_type="react",
    status="success",              # or "failure", "partial"
    duration_ms=1250.5,
    tokens_used=350,
    cost=0.07,
    memory_mb=128.5,
    cpu_ms=1100,
    quality_score=0.85,           # Optional: 0-1
    confidence=0.92,              # Optional: 0-1
    error_type=None,              # Optional: error classification
    metadata={"custom": "data"}
)
```

#### Automatic Recording (via Orchestrator)

```python
from core.orchestrator_with_monitoring import MonitoredOrchestrator

# Use the monitored orchestrator for automatic tracking
orchestrator = MonitoredOrchestrator(
    agent_types=["react", "evaluator"],
    enable_monitoring=True
)

# All agent runs are automatically tracked
results = orchestrator.run(
    task="Analyze compliance requirements",
    project_id="project_123"
)

# Get performance summary
summary = orchestrator.get_performance_summary()
print(f"Health Score: {summary['health_score']}/100")
```

### Recording Accuracy Measurements

```python
# Record accuracy against real-world outcomes
monitor.record_accuracy(
    agent_name="react_agent",
    task_id="task_456",
    predicted_outcome={
        "recommendation": "approve",
        "confidence": 0.85,
        "estimated_value": 100000
    },
    actual_outcome={
        "result": "approved",
        "actual_value": 95000
    },
    feedback_source="user",        # or "automated", "system"
    metadata={"reviewer": "user_123"}
)
```

### Retrieving Metrics

#### System-Wide Metrics

```python
# Get system-wide performance
metrics = monitor.get_system_metrics(time_window_minutes=60)

print(f"Success Rate: {metrics.success_rate:.1%}")
print(f"Avg Latency: {metrics.avg_latency_ms:.0f}ms")
print(f"Total Cost: ${metrics.total_cost:.2f}")
print(f"Avg Accuracy: {metrics.avg_accuracy:.2f}")
```

#### Per-Agent Metrics

```python
# Get metrics for a specific agent
agent_perf = monitor.get_agent_metrics("react_agent")

print(f"Agent: {agent_perf.agent_name}")
print(f"Reliability: {agent_perf.reliability_score:.2f}")
print(f"Efficiency: {agent_perf.efficiency_score:.2f}")
print(f"Specialization: {agent_perf.specialization_score:.2f}")
```

### Checking Alerts

```python
# Get recent alerts
alerts = monitor.get_alerts(
    level=AlertLevel.WARNING,      # Filter by level
    agent_name="react_agent",      # Filter by agent
    limit=10
)

for alert in alerts:
    print(f"[{alert.level}] {alert.message}")
    print(f"  Current: {alert.current_value}")
    print(f"  Threshold: {alert.threshold}")
    print(f"  Recommendation: {alert.recommendation}")
```

### Generating Reports

```python
# Generate comprehensive performance report
report = monitor.generate_report(
    include_agents=True,
    time_window_minutes=60
)

print(f"Health Score: {report['health_score']}/100")
print(f"\nRecommendations:")
for rec in report['recommendations']:
    print(f"  - {rec}")
```

## REST API

### Endpoints

#### Health Status

```bash
GET /api/performance/health
```

Returns overall system health status.

**Response:**
```json
{
  "status": "healthy",
  "health_score": 87.5,
  "timestamp": "2025-10-09T12:00:00Z"
}
```

#### System Metrics

```bash
GET /api/performance/metrics/system?time_window_minutes=60
```

Returns system-wide performance metrics.

**Response:**
```json
{
  "metrics": {
    "total_tasks": 150,
    "successful_tasks": 135,
    "failed_tasks": 15,
    "success_rate": 0.90,
    "avg_latency_ms": 1250.5,
    "p95_latency_ms": 2800.0,
    "total_tokens": 45000,
    "total_cost": 9.50,
    "avg_quality_score": 0.85,
    "avg_accuracy": 0.88,
    "error_rate": 0.10
  },
  "generated_at": "2025-10-09T12:00:00Z"
}
```

#### Agent Metrics

```bash
GET /api/performance/metrics/agent/react_agent?time_window_minutes=60
```

Returns metrics for a specific agent.

**Response:**
```json
{
  "agent_name": "react_agent",
  "agent_type": "react",
  "status": "active",
  "last_run": "2025-10-09T11:55:00Z",
  "metrics": {
    "total_tasks": 50,
    "success_rate": 0.92,
    "avg_latency_ms": 1150.0
  },
  "scores": {
    "specialization": 0.88,
    "reliability": 0.92,
    "efficiency": 0.85
  }
}
```

#### All Agent Metrics

```bash
GET /api/performance/metrics/agents?time_window_minutes=60
```

Returns metrics for all tracked agents.

#### Performance Alerts

```bash
GET /api/performance/alerts?level=warning&limit=20
```

Returns recent performance alerts.

**Response:**
```json
{
  "alerts": [
    {
      "alert_id": "alert_123",
      "level": "warning",
      "metric_type": "latency",
      "message": "High latency detected for react_agent",
      "current_value": 5200,
      "threshold": 5000,
      "agent_name": "react_agent",
      "timestamp": "2025-10-09T11:50:00Z",
      "recommendation": "Check agent workload and LLM performance"
    }
  ],
  "total_count": 1
}
```

#### Comprehensive Report

```bash
GET /api/performance/report?include_agents=true&time_window_minutes=60
```

Generates a comprehensive performance report.

#### Record Accuracy

```bash
POST /api/performance/accuracy
Content-Type: application/json

{
  "agent_name": "react_agent",
  "task_id": "task_123",
  "predicted_outcome": {"value": 100},
  "actual_outcome": {"value": 95},
  "feedback_source": "user",
  "metadata": {"reviewer": "user_456"}
}
```

Records accuracy measurement.

#### Sync with Database

```bash
POST /api/performance/sync?lookback_hours=24
```

Syncs performance metrics from database for historical data.

## Performance Scores

The monitor calculates several composite scores:

### Health Score (0-100)

Overall system health combining:
- **Success Rate** (40 points)
- **Latency** (30 points)
- **Error Rate** (20 points)
- **Accuracy** (10 points)

```
90-100: Excellent ✓
70-89:  Good ✓
50-69:  Fair ⚠
0-49:   Poor ✗
```

### Agent-Specific Scores (0-1)

#### Reliability Score
Consistency of successful task completion.

#### Efficiency Score
Balance between speed and quality:
- Lower latency = higher score
- Higher quality = higher score
- Weighted combination

#### Specialization Score
How well an agent performs its specialized tasks:
- Success rate on specialty tasks
- Quality of outputs
- Consistency across runs

## Alert Thresholds

Default alert thresholds (customizable):

| Metric | Threshold | Level |
|--------|-----------|-------|
| Success Rate | < 80% | CRITICAL |
| Error Rate | > 15% | WARNING |
| P95 Latency | > 5000ms | WARNING |
| Cost per Task | > $1.00 | WARNING |
| Accuracy | < 70% | CRITICAL |
| Memory Usage | > 1024 MB | CRITICAL |
| Tokens per Task | > 5000 | WARNING |

## Accuracy Scoring

The monitor uses intelligent accuracy scoring that adapts to different data types:

### Numeric Values
Relative error calculation:
```python
accuracy = 1.0 - abs(predicted - actual) / abs(actual)
```

### Strings
Word overlap similarity:
```python
accuracy = |predicted_words ∩ actual_words| / |actual_words|
```

### Dictionaries
Combined key and value similarity:
```python
accuracy = (key_overlap + value_similarity) / 2
```

### Lists
Element overlap:
```python
accuracy = |predicted ∩ actual| / |actual|
```

## Trend Detection

The monitor analyzes trends by comparing metrics across time windows:

```
Trend = "improving" | "stable" | "degrading"
```

**Criteria:**
- **Stable**: Change within ±5%
- **Improving**: Increase > 5% (or decrease for inverse metrics like latency)
- **Degrading**: Decrease > 5% (or increase for inverse metrics)

## Best Practices

### 1. Regular Syncing
Sync with database periodically to maintain historical context:
```python
monitor.sync_with_database(lookback_hours=24)
```

### 2. Custom Thresholds
Adjust thresholds based on your SLAs:
```python
init_performance_monitor(
    alert_thresholds={
        "success_rate_min": 0.95,  # Stricter for critical systems
        "latency_p95_max_ms": 3000
    }
)
```

### 3. Accuracy Feedback
Regularly provide accuracy feedback:
- Collect user feedback on predictions
- Automate outcome validation where possible
- Use feedback to retrain models

### 4. Monitor Resource Costs
Track costs closely for optimization:
```python
metrics = monitor.get_system_metrics()
cost_per_task = metrics.total_cost / metrics.total_tasks
if cost_per_task > target_cost:
    # Optimize prompts, switch models, or implement caching
```

### 5. Review Recommendations
Act on system recommendations:
```python
report = monitor.generate_report()
for recommendation in report['recommendations']:
    # Review and implement suggested actions
```

## Example: Complete Integration

```python
from core.performance_monitor import init_performance_monitor, get_performance_monitor
from core.orchestrator_with_monitoring import MonitoredOrchestrator

# 1. Initialize monitor
monitor = init_performance_monitor(
    window_size_minutes=60,
    enable_auto_alerts=True
)

# 2. Create monitored orchestrator
orchestrator = MonitoredOrchestrator(
    agent_types=["react", "evaluator"],
    enable_monitoring=True
)

# 3. Execute tasks (automatically monitored)
results = orchestrator.run(
    task="Analyze compliance requirements",
    project_id="project_123"
)

# 4. Record accuracy when outcomes are known
monitor.record_accuracy(
    agent_name="react_agent",
    task_id=results["run_id"],
    predicted_outcome=results["output"],
    actual_outcome=known_outcome,
    feedback_source="user"
)

# 5. Check performance
summary = orchestrator.get_performance_summary()
print(f"Health: {summary['health_score']}/100")

# 6. Review alerts
alerts = monitor.get_alerts(level=AlertLevel.CRITICAL)
for alert in alerts:
    print(f"CRITICAL: {alert.message}")
    # Take action...

# 7. Generate periodic reports
report = monitor.generate_report(include_agents=True)
# Save or email report...
```

## Troubleshooting

### High Memory Usage
- Reduce `window_size_minutes`
- Decrease buffer sizes in monitor initialization
- Run cleanup more frequently

### Missing Metrics
- Ensure agents are properly instrumented
- Check that monitor is started: `monitor.start()`
- Verify database sync: `monitor.sync_with_database()`

### Inaccurate Trends
- Increase time window for more stable trends
- Ensure sufficient sample size (>100 events)
- Check data quality and outlier removal

## Performance Impact

The Performance Monitor is designed for minimal overhead:

- **Memory**: ~50-100 MB for 10k events
- **CPU**: <1% for background monitoring
- **Latency**: <5ms per event recording
- **Storage**: Metrics are stored in-memory with database backup

## Future Enhancements

Planned improvements:
- Machine learning-based anomaly detection
- Predictive performance forecasting
- Integration with external monitoring tools (Prometheus, Grafana)
- Advanced visualization dashboards
- Multi-tenant metric isolation
- Cost optimization recommendations

## Support

For questions or issues:
1. Check the logs in `/logs/performance_monitor.log`
2. Review examples in `/examples/performance_monitor_example.py`
3. Run tests: `pytest tests/test_performance_monitor.py`
4. Contact the platform team

---

**Version**: 1.0.0  
**Last Updated**: October 9, 2025  
**Status**: Production Ready ✓
