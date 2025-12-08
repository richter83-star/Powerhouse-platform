
#!/bin/bash

# Setup script for Kafka with Docker

echo "================================================"
echo "Kafka Setup for Real-Time Feedback Pipeline"
echo "================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed"
    echo "Please install docker-compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Create docker-compose.yml for Kafka
echo "Creating docker-compose.yml..."

cat > docker-compose.kafka.yml << 'EOF'
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    hostname: zookeeper
    container_name: zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data
      - zookeeper-logs:/var/lib/zookeeper/log

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    hostname: kafka
    container_name: kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: 'zookeeper:2181'
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'
      KAFKA_LOG_RETENTION_HOURS: 168
      KAFKA_LOG_SEGMENT_BYTES: 1073741824
    volumes:
      - kafka-data:/var/lib/kafka/data

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: kafka-ui
    depends_on:
      - kafka
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:29092
      KAFKA_CLUSTERS_0_ZOOKEEPER: zookeeper:2181

volumes:
  zookeeper-data:
  zookeeper-logs:
  kafka-data:
EOF

echo "✓ docker-compose.kafka.yml created"

# Start Kafka
echo ""
echo "Starting Kafka..."
docker-compose -f docker-compose.kafka.yml up -d

# Wait for Kafka to be ready
echo ""
echo "Waiting for Kafka to be ready..."
sleep 10

# Check Kafka status
echo ""
echo "Checking Kafka status..."
docker ps | grep kafka

# Create topics
echo ""
echo "Creating Kafka topics..."

docker exec -it kafka kafka-topics --create \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 3 \
    --topic agent-outcomes \
    --if-not-exists

docker exec -it kafka kafka-topics --create \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 1 \
    --topic agent-metrics \
    --if-not-exists

docker exec -it kafka kafka-topics --create \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 1 \
    --topic agent-alerts \
    --if-not-exists

# List topics
echo ""
echo "Listing Kafka topics..."
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

echo ""
echo "================================================"
echo "Kafka Setup Complete!"
echo "================================================"
echo ""
echo "Services:"
echo "  - Kafka: localhost:9092"
echo "  - Zookeeper: localhost:2181"
echo "  - Kafka UI: http://localhost:8080"
echo ""
echo "Topics created:"
echo "  - agent-outcomes (3 partitions)"
echo "  - agent-metrics (1 partition)"
echo "  - agent-alerts (1 partition)"
echo ""
echo "Management commands:"
echo "  - Stop: docker-compose -f docker-compose.kafka.yml down"
echo "  - Start: docker-compose -f docker-compose.kafka.yml up -d"
echo "  - Logs: docker-compose -f docker-compose.kafka.yml logs -f"
echo "  - Remove: docker-compose -f docker-compose.kafka.yml down -v"
echo ""
echo "Update your .env file:"
echo "  ENABLE_KAFKA=true"
echo "  KAFKA_BOOTSTRAP_SERVERS=localhost:9092"
echo ""
