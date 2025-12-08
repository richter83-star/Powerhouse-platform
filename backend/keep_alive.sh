
#!/bin/bash

# Backend Keep-Alive Watchdog Script
# This script monitors the backend and restarts it if it goes down
# Run this in the background to ensure continuous operation

BACKEND_DIR="/home/ubuntu/powerhouse_b2b_platform/backend"
LOG_FILE="/tmp/simple_backend.log"
WATCHDOG_LOG="/tmp/backend_watchdog.log"
PORT=8001
CHECK_INTERVAL=10  # Check every 10 seconds

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$WATCHDOG_LOG"
}

is_backend_healthy() {
    # Check if port is listening
    if ! lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 1
    fi
    
    # Check if endpoint responds
    if ! curl -s -f http://localhost:$PORT/health > /dev/null 2>&1; then
        return 1
    fi
    
    return 0
}

start_backend() {
    log_message "Starting backend..."
    cd "$BACKEND_DIR"
    nohup python simple_api.py > "$LOG_FILE" 2>&1 &
    sleep 5
    
    if is_backend_healthy; then
        PID=$(lsof -ti:$PORT)
        log_message "✓ Backend started successfully (PID: $PID)"
        return 0
    else
        log_message "❌ Failed to start backend"
        return 1
    fi
}

log_message "Backend watchdog started"
log_message "Monitoring port $PORT with $CHECK_INTERVAL second intervals"

while true; do
    if is_backend_healthy; then
        # Backend is healthy, do nothing
        sleep $CHECK_INTERVAL
    else
        log_message "⚠️  Backend is down! Attempting restart..."
        
        # Kill any zombie processes on the port
        if lsof -ti:$PORT > /dev/null 2>&1; then
            PID=$(lsof -ti:$PORT)
            log_message "Killing stale process $PID"
            kill -9 $PID 2>/dev/null
            sleep 2
        fi
        
        # Start the backend
        start_backend
        
        if [ $? -eq 0 ]; then
            log_message "✓ Backend recovered successfully"
        else
            log_message "❌ Failed to recover backend. Will retry in $CHECK_INTERVAL seconds"
        fi
    fi
done
