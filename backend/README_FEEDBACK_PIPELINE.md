
# Real-Time Feedback Pipeline

## Overview

The Real-Time Feedback Pipeline provides comprehensive outcome tracking for agent actions in the B2B multi-agent platform. It captures structured events including performance metrics, errors, and business outcomes, publishing them to Kafka for real-time monitoring and analysis.

## Architecture

```
┌─────────────┐
│   Agent     │
│  Execution  │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ ActionDispatcher    │
│  - Wraps execution  │
│  - Tracks metrics   │
│  - Captures errors  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Feedback Pipeline   │
│  - Event creation   │
│  - Buffering        │
│  - Publishing       │
└──────┬──────────────┘
       │
       ├──────────────┐
       │              │
       ▼              ▼
┌────────────┐  ┌────────┐
│   Kafka    │  │  Logs  │
│  (Primary) │  │(Backup)│
└────────────┘  └────────┘
```

## Components

### 1. OutcomeEvent

Structured event capturing complete action context:

```python
@dataclass
class OutcomeEvent:
    # Identification
    event_id: str
    run_id: str
    agent_name: str
    action_type: str
    
    # Timing
    timestamp: str
    duration_ms: float
    latency_ms: float
    
    # Outcome
    status: OutcomeStatus  # SUCCESS, FAILURE, PARTIAL, TIMEOUT
    severity: EventSeverity  # INFO, WARNING, ERROR, CRITICAL
    
    # Performance
    llm_latency_ms: Optional[float]
    tokens_used: Optional[int]
    
    # Results & Errors
    output: Optional[Dict]
    error_message: Optional[str]
    error_type: Optional[str]
    stack_trace: Optional[str]
    
    # Context
    correlation_id: Optional[str]
    workflow_id: Optional[str]
    tags: Optional[List[str]]
```

### 2. FeedbackPipeline

Central pipeline for collecting and publishing events:

```python
# Initialize pipeline
pipeline = FeedbackPipeline(
    kafka_servers="localhost:9092",
    kafka_topic="agent-outcomes",
    enable_kafka=True,
    enable_logging=True
)

# Record an outcome
await pipeline.record_outcome(event)

# Query recent events
recent = pipeline.get_recent_events(count=10)
failed = pipeline.get_recent_events(status=OutcomeStatus.FAILURE)
```

### 3. ActionDispatcher

Dispatcher that wraps agent execution with outcome tracking:

```python
# Create dispatcher
dispatcher = ActionDispatcher(feedback_pipeline=pipeline)

# Dispatch an action
result = await dispatcher.dispatch(
    agent=my_agent,
    action_type="process_task",
    input_data={"task": "Analyze data"},
    context={"workflow": "analysis"},
    tags=["analysis", "priority-high"]
)

# Result includes outcome metadata
# {
#   "status": "success",
#   "output": {...},
#   "event_id": "...",
#   "run_id": "...",
#   "duration_ms": 250.5
# }
```

### 4. OrchestrationDispatcher

Enhanced orchestrator for multi-agent workflows:

```python
# Create orchestrator
orchestrator = OrchestrationDispatcher()

# Execute workflow
result = await orchestrator.execute_workflow(
    agents=[agent1, agent2, agent3],
    task="Process compliance report",
    tags=["compliance", "reporting"]
)

# Result includes outcomes for all agents
# {
#   "workflow_id": "...",
#   "outputs": [
#     {"agent": "agent1", "status": "success", "event_id": "..."},
#     {"agent": "agent2", "status": "success", "event_id": "..."},
#     ...
#   ]
# }
```

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Kafka Configuration
ENABLE_KAFKA=true
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_OUTCOME_TOPIC=agent-outcomes
KAFKA_METRICS_TOPIC=agent-metrics
KAFKA_BATCH_SIZE=100
KAFKA_LINGER_MS=100
KAFKA_COMPRESSION=gzip
KAFKA_MAX_RETRIES=3

# Feedback Pipeline
ENABLE_OUTCOME_LOGGING=true
```

### Kafka Setup

#### Option 1: Local Development (Docker)

```bash
# Start Kafka with Docker Compose
docker-compose up -d kafka
```

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    ports:
      - "2181:2181"
  
  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

#### Option 2: Managed Kafka (Production)

Use a managed Kafka service:
- **Confluent Cloud**: https://confluent.cloud
- **AWS MSK**: Amazon Managed Streaming for Apache Kafka
- **Azure Event Hubs**: Kafka-compatible event streaming

Update `KAFKA_BOOTSTRAP_SERVERS` with the managed endpoint.

### Without Kafka

The pipeline works without Kafka by falling back to logging:

```bash
# Disable Kafka in .env
ENABLE_KAFKA=false
ENABLE_OUTCOME_LOGGING=true
```

Events will be logged but not published to Kafka.

## Usage Examples

### Example 1: Basic Agent Dispatch

```python
import asyncio
from core.action_dispatcher import create_dispatcher
from agents.react import ReactAgent

async def main():
    # Create dispatcher
    dispatcher = create_dispatcher(
        kafka_servers="localhost:9092",
        enable_metrics=True
    )
    
    # Create agent
    agent = ReactAgent()
    
    # Dispatch action
    result = await dispatcher.dispatch(
        agent=agent,
        action_type="reasoning",
        input_data={"query": "What is the weather?"},
        context={},
        tags=["reasoning", "weather"]
    )
    
    print(f"Status: {result['status']}")
    print(f"Duration: {result['duration_ms']:.2f}ms")
    print(f"Event ID: {result['event_id']}")

asyncio.run(main())
```

### Example 2: Workflow with Multiple Agents

```python
from core.action_dispatcher import OrchestrationDispatcher
from agents.react import ReactAgent
from agents.evaluator import EvaluatorAgent

async def main():
    orchestrator = OrchestrationDispatcher()
    
    result = await orchestrator.execute_workflow(
        agents=[ReactAgent(), EvaluatorAgent()],
        task="Analyze customer sentiment",
        tags=["customer", "sentiment"]
    )
    
    for output in result['outputs']:
        print(f"{output['agent']}: {output['status']}")

asyncio.run(main())
```

### Example 3: Custom Hooks for Monitoring

```python
dispatcher = create_dispatcher()

# Pre-execution hook
async def log_start(agent, input_data, context):
    print(f"Starting {agent.name}")

# Post-execution hook
async def log_completion(agent, result, event):
    print(f"Completed {agent.name} in {event.duration_ms:.2f}ms")

dispatcher.add_pre_hook(log_start)
dispatcher.add_post_hook(log_completion)
```

### Example 4: Query Recent Events

```python
from core.feedback_pipeline import get_feedback_pipeline, OutcomeStatus

pipeline = get_feedback_pipeline()

# Get recent events
recent = pipeline.get_recent_events(count=10)

# Get only failures
failures = pipeline.get_recent_events(
    count=20,
    status=OutcomeStatus.FAILURE
)

# Get events for specific agent
agent_events = pipeline.get_recent_events(
    count=10,
    agent_name="react_agent"
)
```

## Event Schema

### Success Event Example

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "run_id": "660e8400-e29b-41d4-a716-446655440000",
  "agent_name": "react_agent",
  "agent_type": "reasoning",
  "action_type": "process_query",
  "timestamp": "2025-10-09T12:34:56.789Z",
  "start_time": "2025-10-09T12:34:56.500Z",
  "end_time": "2025-10-09T12:34:56.789Z",
  "duration_ms": 289.5,
  "status": "success",
  "severity": "info",
  "latency_ms": 289.5,
  "llm_latency_ms": 250.3,
  "tokens_used": 150,
  "output": {
    "result": "Analysis complete",
    "confidence": 0.95
  },
  "correlation_id": "workflow-123",
  "workflow_id": "compliance-report",
  "tags": ["reasoning", "analysis"],
  "metadata": {
    "model": "gpt-4",
    "provider": "openai"
  }
}
```

### Failure Event Example

```json
{
  "event_id": "770e8400-e29b-41d4-a716-446655440000",
  "run_id": "880e8400-e29b-41d4-a716-446655440000",
  "agent_name": "data_processor",
  "agent_type": "processing",
  "action_type": "transform_data",
  "timestamp": "2025-10-09T12:35:10.123Z",
  "start_time": "2025-10-09T12:35:09.000Z",
  "end_time": "2025-10-09T12:35:10.123Z",
  "duration_ms": 1123.4,
  "status": "failure",
  "severity": "error",
  "latency_ms": 1123.4,
  "error_message": "Invalid data format",
  "error_type": "ValueError",
  "stack_trace": "Traceback (most recent call last):\n  ...",
  "retry_count": 2,
  "tags": ["data", "processing", "error"],
  "metadata": {
    "input_size": 1024,
    "validation_failed": true
  }
}
```

## Monitoring & Analytics

### Real-Time Dashboards

Use the Kafka events to build real-time dashboards:

- **Success rate** by agent type
- **Average latency** over time
- **Error rate** and error types
- **Token usage** and costs
- **Workflow completion times**

### Alerting

Set up alerts based on event patterns:

```python
# Example: Alert on high failure rate
def check_failure_rate(events):
    failures = sum(1 for e in events if e.status == OutcomeStatus.FAILURE)
    rate = failures / len(events)
    
    if rate > 0.1:  # 10% threshold
        send_alert(f"High failure rate: {rate:.1%}")
```

### Analytics Queries

Example Kafka Streams or KSQL queries:

```sql
-- Average latency by agent
SELECT agent_name, AVG(latency_ms) as avg_latency
FROM agent_outcomes
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY agent_name;

-- Error rate by hour
SELECT 
  WINDOWSTART as hour,
  COUNT_IF(status = 'failure') / COUNT(*) as error_rate
FROM agent_outcomes
WINDOW HOPPING (SIZE 1 HOUR, ADVANCE BY 1 HOUR)
GROUP BY WINDOWSTART;
```

## Testing

Run the example script:

```bash
# Install Kafka Python client
pip install kafka-python

# Run examples
python examples/dispatcher_example.py
```

This will demonstrate:
1. Single agent dispatch with outcome tracking
2. Multi-agent workflow orchestration
3. Querying recent events
4. Custom execution hooks

## Performance Considerations

### Batching

Events are batched before sending to Kafka:

```python
KAFKA_BATCH_SIZE=100      # Batch up to 100 events
KAFKA_LINGER_MS=100       # Wait up to 100ms before sending
```

### Compression

Events are compressed using gzip by default:

```python
KAFKA_COMPRESSION=gzip    # Reduces bandwidth ~70%
```

### Async Publishing

Events are published asynchronously to avoid blocking agent execution:

```python
# Non-blocking publish
await pipeline.record_outcome(event)  # Returns immediately
```

### Buffer Fallback

If Kafka is unavailable, events are buffered locally:

```python
# 1000 events buffered in memory
_buffer_max_size = 1000
```

## Troubleshooting

### Kafka Connection Issues

```python
# Check if Kafka is available
try:
    producer = KafkaProducer(bootstrap_servers='localhost:9092')
    producer.close()
    print("✓ Kafka available")
except:
    print("✗ Kafka unavailable - check connection")
```

### No Events Published

1. Check `ENABLE_KAFKA=true` in `.env`
2. Verify Kafka servers are reachable
3. Check topic exists: `kafka-topics --list --bootstrap-server localhost:9092`
4. Review logs for connection errors

### High Latency

If event publishing adds latency:

1. Increase batch size: `KAFKA_BATCH_SIZE=500`
2. Reduce compression: `KAFKA_COMPRESSION=none`
3. Use async publishing (already default)
4. Consider dedicated Kafka cluster

## Security

### Network Security

```python
# Use SSL for production
KAFKA_BOOTSTRAP_SERVERS=kafka.production.com:9093
KAFKA_SECURITY_PROTOCOL=SSL
KAFKA_SSL_CAFILE=/path/to/ca.pem
```

### Data Privacy

Sensitive data handling:

```python
# Disable input/output capture for sensitive operations
dispatcher = ActionDispatcher(enable_metrics=False)

# Or sanitize data before recording
def sanitize_output(output):
    # Remove sensitive fields
    output.pop('ssn', None)
    output.pop('password', None)
    return output
```

## Integration with Existing Code

### Replace Existing Orchestrator

```python
# Old code
from core.orchestrator import Orchestrator

orchestrator = Orchestrator(agent_names=['react', 'evaluator'])
result = orchestrator.run(task="Analyze data", config={})

# New code with outcome tracking
from core.action_dispatcher import OrchestrationDispatcher

orchestrator = OrchestrationDispatcher()
result = await orchestrator.execute_workflow(
    agents=[ReactAgent(), EvaluatorAgent()],
    task="Analyze data"
)
```

### Wrap Individual Agent Calls

```python
# Old code
result = agent.execute(input_data, context)

# New code with outcome tracking
dispatcher = create_dispatcher()
result = await dispatcher.dispatch(
    agent=agent,
    action_type="execution",
    input_data=input_data,
    context=context
)
```

## Next Steps

1. **Set up Kafka**: Deploy Kafka locally or use managed service
2. **Update Configuration**: Set environment variables
3. **Modify Orchestrator**: Replace with OrchestrationDispatcher
4. **Build Dashboards**: Create real-time monitoring dashboards
5. **Set Up Alerts**: Configure alerting based on event patterns
6. **Optimize**: Tune batching and compression settings

## Resources

- **Kafka Documentation**: https://kafka.apache.org/documentation/
- **Confluent Cloud**: https://docs.confluent.io/cloud/current/
- **kafka-python**: https://kafka-python.readthedocs.io/
- **KSQL**: https://docs.confluent.io/platform/current/ksql/
