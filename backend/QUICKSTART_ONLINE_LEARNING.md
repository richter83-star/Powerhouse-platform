
# Online Learning Module - Quick Start Guide

Get the online learning module up and running in 5 minutes.

## Prerequisites

- Python 3.11+
- Kafka running (or Docker to run Kafka)
- Backend dependencies installed

## Step 1: Start Kafka (if not running)

```bash
# Option 1: Using Docker
docker run -d \
  --name kafka \
  -p 9092:9092 \
  -e KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092 \
  confluentinc/cp-kafka:latest

# Option 2: Local Kafka
# Follow Kafka installation instructions
```

## Step 2: Install Dependencies

```bash
cd backend
pip install kafka-python numpy
```

## Step 3: Configure Environment

```bash
# Create or update .env file
cat > .env << EOF
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_OUTCOME_TOPIC=agent-outcomes
ENABLE_KAFKA=true

# Learning Configuration  
MODEL_BATCH_SIZE=10
MODEL_BATCH_TIMEOUT=30
MODEL_STORAGE_PATH=./models
MODEL_SAVE_INTERVAL=300

# Database (if not already configured)
DATABASE_URL=postgresql://user:password@localhost/powerhouse
EOF
```

## Step 4: Start the Service

```bash
# Option 1: Using the startup script
chmod +x scripts/start_online_learning.sh
./scripts/start_online_learning.sh

# Option 2: Direct start
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Step 5: Verify Installation

```bash
# Check service status
curl http://localhost:8000/api/learning/status

# Expected output:
# {
#   "status": "running",
#   "running": true,
#   "kafka_topic": "agent-outcomes",
#   "batch_size": 10,
#   "models_loaded": ["agent_selection"]
# }
```

## Step 6: Run Tests

```bash
# Option 1: Using test script
chmod +x scripts/test_online_learning.sh
./scripts/test_online_learning.sh

# Option 2: Direct pytest
pytest tests/test_online_learning.py -v
```

## Quick API Examples

### Get Learning Metrics

```bash
curl http://localhost:8000/api/learning/metrics
```

### Get Agent Performance

```bash
curl http://localhost:8000/api/learning/agents/performance
```

### Predict Best Agent

```bash
curl -X POST http://localhost:8000/api/learning/predict/agent-selection \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "analysis",
    "top_k": 3
  }'
```

## Troubleshooting

### Can't connect to Kafka

```bash
# Check if Kafka is running
docker ps | grep kafka

# Check Kafka logs
docker logs kafka

# Test connection
nc -zv localhost 9092
```

### Model updater not starting

```bash
# Check environment variables
echo $ENABLE_KAFKA
echo $KAFKA_BOOTSTRAP_SERVERS

# Check API logs
tail -f logs/app.log | grep "model updater"
```

### No predictions available

```bash
# Verify events are being published
curl http://localhost:8000/api/learning/metrics

# Check samples_processed value (should be > 0)
```

## Next Steps

1. **Explore the API:** Visit `http://localhost:8000/docs`
2. **Read Full Documentation:** See `docs/ONLINE_LEARNING.md`
3. **Review Delivery Summary:** See `docs/ONLINE_LEARNING_DELIVERY.md`
4. **Integrate with Workflows:** Use predictions in your orchestrator

## Example Integration

```python
from core.online_learning import get_model_updater, ModelType

# Get the model updater
updater = get_model_updater()

# Get agent recommendations for a task
predictions = updater.predict(
    ModelType.AGENT_SELECTION,
    task_type="compliance_analysis",
    context={"complexity": "high"},
    top_k=3
)

# Use the top recommendation
best_agent = predictions[0][0]
print(f"Best agent for this task: {best_agent}")
```

## Support

- **Documentation:** `docs/ONLINE_LEARNING.md`
- **API Reference:** `http://localhost:8000/docs`
- **Architecture Diagram:** `docs/architecture/online_learning.png`

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** October 9, 2025
