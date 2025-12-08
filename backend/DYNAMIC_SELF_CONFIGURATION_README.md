
# Dynamic Self-Configuration System

## Overview

The Dynamic Self-Configuration System enables the agent architecture to **autonomously adjust its runtime parameters** based on real-time performance metrics from the PerformanceMonitor. This creates a self-optimizing system that continuously adapts to changing conditions, workload patterns, and performance requirements.

### Key Capabilities

- **Automatic Parameter Tuning**: Adjusts runtime parameters based on performance metrics
- **Multiple Adjustment Strategies**: Conservative, Balanced, Aggressive, and Gradual approaches
- **Safe Boundaries**: All parameters have validated min/max bounds
- **Automatic Rollback**: Reverts changes if performance degrades
- **Audit Trail**: Complete history of all configuration changes
- **Rule-Based System**: Configurable rules for different scenarios
- **Multi-Scope Configuration**: Global, agent-type, and instance-level parameters

---

## Architecture

### Components

1. **DynamicConfigManager** (`core/dynamic_config_manager.py`)
   - Manages all configurable parameters
   - Enforces parameter bounds and validation
   - Applies adjustment rules
   - Tracks configuration history
   - Handles automatic rollback

2. **AdaptivePerformanceMonitor** (`core/performance_monitor_with_config.py`)
   - Extends PerformanceMonitor with configuration integration
   - Automatically triggers parameter adjustments
   - Monitors for performance degradation
   - Creates alerts for configuration changes

3. **AdaptiveOrchestrator** (`core/adaptive_orchestrator.py`)
   - Orchestrator that uses dynamic configuration
   - Injects runtime parameters into agent execution
   - Records metrics for configuration decisions
   - Provides configuration management API

4. **Configuration API** (`api/config_routes.py`)
   - RESTful endpoints for configuration management
   - View current parameters and rules
   - Manual parameter overrides
   - Configuration statistics and health checks

---

## Configurable Parameters

### Core Parameters

| Parameter | Description | Default | Range | Type |
|-----------|-------------|---------|-------|------|
| `planner_search_depth` | Search depth for planning algorithms | 5 | 1-10 | int |
| `max_retries` | Maximum retry attempts | 3 | 0-5 | int |
| `timeout_seconds` | Operation timeout | 60 | 5-300 | int |
| `batch_size` | Batch size for parallel processing | 10 | 1-100 | int |
| `memory_cache_size_mb` | Memory cache size | 100 | 10-1000 | int |
| `quality_threshold` | Minimum quality threshold | 0.7 | 0.0-1.0 | float |

### Adding Custom Parameters

```python
from core.dynamic_config_manager import get_config_manager, ParameterBounds, ConfigurationScope

config_manager = get_config_manager()

config_manager.register_parameter(
    name="custom_parameter",
    bounds=ParameterBounds(
        min_value=1,
        max_value=100,
        default_value=50,
        step_size=5,
        parameter_type="int"
    ),
    scope=ConfigurationScope.GLOBAL,
    description="My custom parameter"
)
```

---

## Adjustment Rules

### Default Rules

1. **Reduce Depth on High Latency**
   - **Trigger**: Average latency > 5000ms
   - **Action**: Decrease `planner_search_depth` by 1
   - **Priority**: 8/10
   - **Rationale**: Reduces computational complexity to improve response time

2. **Increase Retries on High Error Rate**
   - **Trigger**: Error rate > 15%
   - **Action**: Increase `max_retries` by 1
   - **Priority**: 7/10
   - **Rationale**: More retries may overcome transient failures

3. **Increase Timeout on Timeouts**
   - **Trigger**: Average latency > 50000ms
   - **Action**: Multiply `timeout_seconds` by 1.2
   - **Priority**: 6/10
   - **Rationale**: Prevents premature timeouts on slow operations

4. **Reduce Batch Size on High Memory**
   - **Trigger**: Average memory usage > 500MB
   - **Action**: Decrease `batch_size` by 2
   - **Priority**: 7/10
   - **Rationale**: Reduces memory footprint

5. **Increase Depth on Good Performance**
   - **Trigger**: Success rate > 95%
   - **Action**: Increase `planner_search_depth` by 1
   - **Priority**: 4/10
   - **Rationale**: Use spare capacity for better quality

6. **Lower Quality Threshold on Low Success**
   - **Trigger**: Success rate < 70%
   - **Action**: Decrease `quality_threshold` by 0.05
   - **Priority**: 5/10
   - **Rationale**: Balances quality vs. success rate

### Rule Properties

- **Cooldown**: Minimum time between applications (prevents oscillation)
- **Rate Limit**: Maximum applications per hour
- **Priority**: Determines evaluation order (1-10)
- **Scope**: Which agents/components are affected

### Creating Custom Rules

```python
from core.dynamic_config_manager import get_config_manager, AdjustmentRule, MetricType, ConfigurationScope

config_manager = get_config_manager()

rule = AdjustmentRule(
    name="my_custom_rule",
    description="Custom adjustment rule",
    trigger_metric=MetricType.LATENCY,
    trigger_threshold=3000,
    trigger_operator="gt",  # gt, lt, gte, lte, eq
    target_parameter="planner_search_depth",
    adjustment_value=-1,
    adjustment_type="relative",  # absolute, relative, multiply
    scope=ConfigurationScope.AGENT_TYPE,
    cooldown_seconds=120,
    max_adjustments_per_hour=5,
    priority=7
)

config_manager.add_adjustment_rule(rule)
```

---

## Adjustment Strategies

### Conservative Strategy
- **Modifier**: 50% of calculated adjustment
- **Use Case**: Production systems requiring stability
- **Characteristics**: Slow, safe, minimal risk

### Balanced Strategy (Default)
- **Modifier**: 100% of calculated adjustment
- **Use Case**: General purpose applications
- **Characteristics**: Moderate speed, reasonable risk

### Aggressive Strategy
- **Modifier**: 150% of calculated adjustment
- **Use Case**: Development, experimentation, rapid optimization
- **Characteristics**: Fast adaptation, higher risk

### Gradual Strategy
- **Modifier**: 25% of calculated adjustment
- **Use Case**: Sensitive systems, gradual optimization
- **Characteristics**: Very slow, very safe

---

## Usage Examples

### Example 1: Basic Setup

```python
from core.adaptive_orchestrator import AdaptiveOrchestrator

# Create adaptive orchestrator with default settings
orchestrator = AdaptiveOrchestrator(
    agent_names=["planning", "react", "chain_of_thought"],
    enable_adaptation=True
)

# Run tasks - system will automatically adapt
result = orchestrator.run("Process this task")

# Check performance
summary = orchestrator.get_performance_summary()
print(f"Health Score: {summary['health_score']}/100")
```

### Example 2: Custom Strategy

```python
from core.dynamic_config_manager import get_config_manager, AdjustmentStrategy

# Set aggressive strategy for rapid optimization
config_manager = get_config_manager()
# Note: Strategy is set at initialization
# For runtime changes, you would need to reinitialize

orchestrator = AdaptiveOrchestrator(
    agent_names=["planning"],
    enable_adaptation=True
)
```

### Example 3: Manual Parameter Override

```python
from core.adaptive_orchestrator import AdaptiveOrchestrator

orchestrator = AdaptiveOrchestrator(
    agent_names=["planning"],
    enable_adaptation=True
)

# Manually set a parameter
orchestrator.set_parameter(
    "planner_search_depth",
    8,
    reason="Optimizing for quality over speed"
)

# Get current value
depth = orchestrator.get_current_parameter("planner_search_depth")
print(f"Current search depth: {depth}")
```

### Example 4: Monitor Configuration Changes

```python
from core.dynamic_config_manager import get_config_manager

config_manager = get_config_manager()

# Get configuration snapshot
snapshot = config_manager.get_configuration_snapshot()

print(f"Current parameters: {snapshot['parameters']}")
print(f"Recent changes: {snapshot['recent_changes']}")

# Get statistics
stats = config_manager.get_statistics()
print(f"Total changes: {stats['total_changes']}")
print(f"Rollbacks: {stats['rollbacks']}")
```

### Example 5: Disable Specific Rules

```python
from core.dynamic_config_manager import get_config_manager

config_manager = get_config_manager()

# Disable a rule
rule = config_manager.adjustment_rules["reduce_depth_on_high_latency"]
rule.enabled = False

# Re-enable later
rule.enabled = True
```

---

## API Endpoints

### Get Configuration Snapshot
```http
GET /api/v1/config/snapshot
```

Returns current configuration state with all parameters and recent changes.

### Get All Parameters
```http
GET /api/v1/config/parameters
```

Returns all configurable parameters with their values and bounds.

### Get Specific Parameter
```http
GET /api/v1/config/parameters/{parameter_name}
```

Returns specific parameter value and metadata.

### Update Parameter
```http
POST /api/v1/config/parameters/{parameter_name}
Content-Type: application/json

{
  "parameter_name": "planner_search_depth",
  "value": 7,
  "reason": "Manual optimization"
}
```

### Get Adjustment Rules
```http
GET /api/v1/config/rules
```

Returns all adjustment rules and their status.

### Enable/Disable Rule
```http
POST /api/v1/config/rules/{rule_name}/enable
POST /api/v1/config/rules/{rule_name}/disable
```

### Get System Health
```http
GET /api/v1/config/health
```

Returns comprehensive system health with performance and configuration data.

### Force Configuration Evaluation
```http
POST /api/v1/config/force-evaluation
```

Immediately evaluates and applies adjustment rules.

### Reset to Defaults
```http
POST /api/v1/config/reset
```

Resets all parameters to their default values.

---

## Automatic Rollback

### How It Works

1. **Change Tracking**: Every configuration change is tracked with timestamp
2. **Rollback Window**: Changes are monitored for a configurable period (default: 5 minutes)
3. **Performance Comparison**: Current performance is compared to baseline
4. **Degradation Detection**: Multiple indicators are checked:
   - Success rate drop > 5%
   - Latency increase > 30%
   - Error rate increase > 5%
   - Cost increase > 50%
   - Quality drop > 0.1
5. **Automatic Revert**: If degradation score ≥ 3, parameter is rolled back

### Configuration

```python
from core.dynamic_config_manager import DynamicConfigManager

config_manager = DynamicConfigManager(
    enable_auto_rollback=True,
    rollback_window_minutes=5
)
```

### Disabling Rollback

```python
config_manager.enable_auto_rollback = False
```

---

## Best Practices

### 1. Start Conservative

Begin with the **Conservative** strategy and gradually move to Balanced or Aggressive as you understand system behavior.

```python
from core.dynamic_config_manager import AdjustmentStrategy

config_manager = get_config_manager(strategy=AdjustmentStrategy.CONSERVATIVE)
```

### 2. Monitor Configuration Changes

Regularly check configuration changes and their impact:

```python
snapshot = config_manager.get_configuration_snapshot()
for change in snapshot['recent_changes']:
    print(f"{change['parameter']}: {change['old_value']} → {change['new_value']}")
```

### 3. Set Appropriate Bounds

Define parameter bounds that match your system constraints:

```python
bounds = ParameterBounds(
    min_value=1,
    max_value=10,  # Don't allow too high
    default_value=5,
    step_size=1
)
```

### 4. Use Rule Priorities

Set higher priorities for critical rules:

```python
rule = AdjustmentRule(
    name="critical_rule",
    priority=9,  # Higher priority
    # ...
)
```

### 5. Enable Rollback in Production

Always enable automatic rollback in production:

```python
config_manager = DynamicConfigManager(
    enable_auto_rollback=True,
    rollback_window_minutes=10  # Longer window for production
)
```

### 6. Test Configuration Changes

Test parameter changes in development before deploying to production:

```python
# Development: Aggressive strategy for testing
dev_config = get_config_manager(strategy=AdjustmentStrategy.AGGRESSIVE)

# Production: Conservative strategy
prod_config = get_config_manager(strategy=AdjustmentStrategy.CONSERVATIVE)
```

### 7. Log Configuration Events

Monitor logs for configuration changes:

```python
import logging
logging.getLogger("core.dynamic_config_manager").setLevel(logging.INFO)
```

---

## Integration with Performance Monitor

The DynamicConfigManager is tightly integrated with the PerformanceMonitor:

```python
from core.performance_monitor_with_config import get_adaptive_monitor

# Monitor automatically triggers configuration adjustments
monitor = get_adaptive_monitor(
    enable_dynamic_config=True,
    adjustment_interval_seconds=60  # Check every minute
)

# Configuration is evaluated automatically during metric collection
monitor.record_agent_run(
    run_id="run_123",
    agent_name="planner",
    agent_type="planning",
    status="success",
    duration_ms=1500
)

# Force immediate evaluation if needed
monitor.force_adjustment_evaluation()
```

---

## Troubleshooting

### Configuration Not Changing

**Symptom**: Parameters don't adjust despite performance issues

**Solutions**:
1. Check if rules are enabled:
   ```python
   rules = config_manager.adjustment_rules
   for name, rule in rules.items():
       print(f"{name}: {'enabled' if rule.enabled else 'disabled'}")
   ```

2. Verify cooldown hasn't been reached:
   ```python
   rule = config_manager.adjustment_rules["rule_name"]
   print(f"Last triggered: {rule.last_triggered}")
   print(f"Cooldown: {rule.cooldown_seconds}s")
   ```

3. Check if threshold is met:
   ```python
   metrics = monitor.get_system_metrics()
   print(f"Current latency: {metrics.avg_latency_ms}ms")
   print(f"Threshold: {rule.trigger_threshold}ms")
   ```

### Too Many Adjustments

**Symptom**: Parameters changing too frequently

**Solutions**:
1. Increase cooldown:
   ```python
   rule.cooldown_seconds = 300  # 5 minutes
   ```

2. Reduce rate limit:
   ```python
   rule.max_adjustments_per_hour = 3
   ```

3. Use more conservative strategy:
   ```python
   # Reinitialize with conservative strategy
   ```

### Rollback Not Working

**Symptom**: Bad changes not reverted

**Solutions**:
1. Ensure rollback is enabled:
   ```python
   config_manager.enable_auto_rollback = True
   ```

2. Check rollback window:
   ```python
   config_manager.rollback_window_minutes = 5
   ```

3. Verify degradation threshold:
   ```python
   # Check if degradation is significant enough
   baseline = config_manager.baseline_metrics
   current = monitor.get_system_metrics()
   ```

---

## Performance Impact

The Dynamic Self-Configuration system is designed for minimal overhead:

- **Memory**: ~10MB for configuration history
- **CPU**: <1% overhead for evaluation
- **Latency**: <5ms added to metric recording
- **Storage**: Configuration history stored in memory (configurable size)

---

## Future Enhancements

Planned features for future releases:

1. **Machine Learning-Based Adjustments**
   - Use ML models to predict optimal parameters
   - Learn from historical performance data

2. **Multi-Objective Optimization**
   - Balance multiple objectives (latency, cost, quality)
   - Pareto-optimal configuration selection

3. **A/B Testing Support**
   - Test different configurations simultaneously
   - Statistical significance testing

4. **Configuration Templates**
   - Predefined configurations for common scenarios
   - Quick-start templates

5. **Cross-Project Learning**
   - Share configuration insights across projects
   - Collective intelligence

---

## Support and Feedback

For questions, issues, or feedback about the Dynamic Self-Configuration system:

- **Documentation**: See this README
- **Examples**: `examples/dynamic_config_example.py`
- **Tests**: `tests/test_dynamic_config_manager.py`
- **Logs**: Check application logs for configuration events

---

## Summary

The Dynamic Self-Configuration System provides:

✅ **Autonomous Adaptation**: Automatically adjusts parameters based on performance  
✅ **Safe Boundaries**: Validated parameter ranges prevent unsafe values  
✅ **Multiple Strategies**: Choose from Conservative to Aggressive  
✅ **Automatic Rollback**: Reverts changes that degrade performance  
✅ **Complete Audit Trail**: Track all configuration changes  
✅ **RESTful API**: Manage configuration via HTTP endpoints  
✅ **Production-Ready**: Minimal overhead, robust error handling  

**Example Use Case**: If the PerformanceMonitor detects high task latency (>5s), the agent autonomously reduces its GOAP planner's search depth from 5 to 4, prioritizing speed over absolute optimality. This happens automatically without manual intervention!

