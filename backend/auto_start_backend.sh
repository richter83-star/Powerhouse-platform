
#!/bin/bash

# Auto-start backend script
# This script ensures the backend is always running

BACKEND_DIR="/home/ubuntu/powerhouse_b2b_platform/backend"
LOG_FILE="/tmp/simple_backend.log"
PORT=8001

# Function to check if backend is running
is_running() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0
    else
        return 1
    fi
}

# Function to start backend
start_backend() {
    cd "$BACKEND_DIR"
    nohup python simple_api.py > "$LOG_FILE" 2>&1 &
    sleep 3
    
    if is_running; then
        echo "✓ Backend started successfully"
        return 0
    else
        echo "❌ Failed to start backend"
        return 1
    fi
}

# Main logic
if is_running; then
    echo "✓ Backend is already running on port $PORT"
    PID=$(lsof -ti:$PORT)
    echo "  PID: $PID"
    echo "  Logs: tail -f $LOG_FILE"
else
    echo "Starting backend..."
    start_backend
fi

# Show status
if is_running; then
    PID=$(lsof -ti:$PORT)
    echo ""
    echo "================================================"
    echo "Backend Status: RUNNING"
    echo "PID: $PID"
    echo "Port: $PORT"
    echo "Logs: $LOG_FILE"
    echo "================================================"
    echo ""
    echo "Endpoints:"
    echo "  http://localhost:$PORT/health"
    echo "  http://localhost:$PORT/api/v1/agents"
    echo "  http://localhost:$PORT/docs"
fi
