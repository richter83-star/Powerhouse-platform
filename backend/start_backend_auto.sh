
#!/bin/bash

# Automated Backend Startup Script
# This script ensures the backend is always running with the correct configuration

BACKEND_DIR="/home/ubuntu/powerhouse_b2b_platform/backend"
PORT=8001

cd "$BACKEND_DIR"

echo "================================================"
echo "Powerhouse Backend - Auto Start"
echo "================================================"
echo ""

# Function to check if backend is healthy
is_backend_healthy() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 && \
       curl -s -f http://localhost:$PORT/health > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Check if backend is already running and healthy
if is_backend_healthy; then
    PID=$(lsof -ti:$PORT)
    echo "✓ Backend is already running and healthy (PID: $PID)"
    echo ""
    echo "Backend URL: http://localhost:$PORT"
    echo "Agents API: http://localhost:$PORT/api/v1/agents"
    echo "Logs: tail -f /tmp/simple_backend.log"
    echo ""
    echo "To restart: kill $PID && $0"
    echo "================================================"
    exit 0
fi

# Kill any stale processes on the port
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo "⚠️  Cleaning up stale process on port $PORT..."
    kill -9 $(lsof -ti:$PORT) 2>/dev/null
    sleep 2
fi

# Start the backend
echo "Starting backend with simple_api.py..."
nohup python simple_api.py > /tmp/simple_backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..15}; do
    if is_backend_healthy; then
        echo ""
        echo "✓ Backend started successfully!"
        echo ""
        echo "Backend Information:"
        echo "  PID: $BACKEND_PID"
        echo "  Port: $PORT"
        echo "  URL: http://localhost:$PORT"
        echo "  Health: http://localhost:$PORT/health"
        echo "  Agents API: http://localhost:$PORT/api/v1/agents"
        echo "  Logs: tail -f /tmp/simple_backend.log"
        echo ""
        
        # Show agent count
        AGENT_COUNT=$(curl -s http://localhost:$PORT/api/v1/agents 2>/dev/null | grep -o '"total_count":[0-9]*' | grep -o '[0-9]*')
        if [ ! -z "$AGENT_COUNT" ]; then
            echo "✓ Loaded $AGENT_COUNT agents"
        fi
        
        echo ""
        echo "================================================"
        exit 0
    fi
    echo "  Waiting... ($i/15)"
    sleep 2
done

echo ""
echo "❌ Backend failed to start. Check logs:"
echo "    tail -f /tmp/simple_backend.log"
echo "================================================"
exit 1
