
#!/bin/bash

# Start Online Learning Module
# This script initializes and starts the RealTimeModelUpdater service

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Online Learning Module Startup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Kafka is enabled
if [ "$ENABLE_KAFKA" != "true" ]; then
    echo -e "${YELLOW}⚠️  ENABLE_KAFKA is not set to 'true'${NC}"
    echo -e "${YELLOW}   Online learning will be disabled${NC}"
    echo ""
    echo "To enable, set environment variable:"
    echo "  export ENABLE_KAFKA=true"
    echo ""
    exit 0
fi

# Check Kafka connection
echo "1. Checking Kafka connection..."
if ! nc -z $(echo $KAFKA_BOOTSTRAP_SERVERS | cut -d: -f1) $(echo $KAFKA_BOOTSTRAP_SERVERS | cut -d: -f2) 2>/dev/null; then
    echo -e "${RED}✗ Cannot connect to Kafka at $KAFKA_BOOTSTRAP_SERVERS${NC}"
    echo ""
    echo "Please ensure Kafka is running:"
    echo "  docker run -d --name kafka -p 9092:9092 confluentinc/cp-kafka:latest"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ Kafka connection successful${NC}"
echo ""

# Check Python dependencies
echo "2. Checking Python dependencies..."
python3 -c "import kafka; import numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Missing dependencies${NC}"
    echo ""
    echo "Please install required packages:"
    echo "  pip install kafka-python numpy"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ All dependencies installed${NC}"
echo ""

# Create models directory
echo "3. Creating models directory..."
mkdir -p ./models
echo -e "${GREEN}✓ Models directory ready${NC}"
echo ""

# Display configuration
echo "4. Configuration:"
echo "   - Kafka Servers: $KAFKA_BOOTSTRAP_SERVERS"
echo "   - Kafka Topic: ${KAFKA_OUTCOME_TOPIC:-agent-outcomes}"
echo "   - Batch Size: ${MODEL_BATCH_SIZE:-10}"
echo "   - Batch Timeout: ${MODEL_BATCH_TIMEOUT:-30}s"
echo "   - Model Storage: ${MODEL_STORAGE_PATH:-./models}"
echo ""

# Start the API server (which will start the model updater)
echo "5. Starting API server with online learning..."
echo ""
echo -e "${GREEN}🚀 Server starting...${NC}"
echo ""

python3 -m uvicorn api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info

# Note: The model updater is automatically started in the lifespan event
