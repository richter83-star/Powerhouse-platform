
#!/bin/bash

# Powerhouse Backend Startup Script
# Ensures the backend API server is running

BACKEND_DIR="/home/ubuntu/powerhouse_b2b_platform/backend"
PID_FILE="$BACKEND_DIR/backend.pid"
LOG_FILE="$BACKEND_DIR/backend.log"

cd "$BACKEND_DIR"

# Function to check if backend is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Function to start backend
start_backend() {
    echo "Starting Powerhouse backend..."
    nohup python simple_api.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2
    
    if is_running; then
        echo "✅ Backend started successfully on port 8001"
        echo "PID: $(cat $PID_FILE)"
    else
        echo "❌ Failed to start backend"
        cat "$LOG_FILE"
        exit 1
    fi
}

# Function to stop backend
stop_backend() {
    if is_running; then
        echo "Stopping backend..."
        PID=$(cat "$PID_FILE")
        kill "$PID"
        rm -f "$PID_FILE"
        echo "✅ Backend stopped"
    else
        echo "Backend is not running"
    fi
}

# Main logic
case "${1:-start}" in
    start)
        if is_running; then
            echo "Backend is already running (PID: $(cat $PID_FILE))"
        else
            start_backend
        fi
        ;;
    stop)
        stop_backend
        ;;
    restart)
        stop_backend
        sleep 1
        start_backend
        ;;
    status)
        if is_running; then
            echo "Backend is running (PID: $(cat $PID_FILE))"
            curl -s http://localhost:8001/health | python3 -m json.tool
        else
            echo "Backend is not running"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
