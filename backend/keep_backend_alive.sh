
#!/bin/bash

# Backend Watchdog Script
# Ensures the backend is always running and restarts it if it fails

BACKEND_DIR="/home/ubuntu/powerhouse_b2b_platform/backend"
PORT=8001
CHECK_INTERVAL=30  # Check every 30 seconds
LOG_FILE="/tmp/backend_watchdog.log"

cd "$BACKEND_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

is_backend_healthy() {
    # Check if port is listening AND health endpoint responds
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        if curl -s -f http://localhost:$PORT/health >/dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

start_backend() {
    log "Starting backend..."
    
    # Kill any stale processes
    if lsof -ti:$PORT >/dev/null 2>&1; then
        log "Killing stale process on port $PORT"
        kill -9 $(lsof -ti:$PORT) 2>/dev/null
        sleep 2
    fi
    
    # Start backend
    nohup python3 simple_api.py > /tmp/simple_backend.log 2>&1 &
    BACKEND_PID=$!
    
    # Wait for it to be healthy
    for i in {1..15}; do
        sleep 2
        if is_backend_healthy; then
            log "✓ Backend started successfully (PID: $BACKEND_PID)"
            return 0
        fi
    done
    
    log "❌ Backend failed to start"
    return 1
}

log "=== Backend Watchdog Started ==="
log "Check interval: ${CHECK_INTERVAL}s"
log "Port: $PORT"

# Initial start
if is_backend_healthy; then
    PID=$(lsof -ti:$PORT)
    log "✓ Backend already running (PID: $PID)"
else
    start_backend
fi

# Monitoring loop
while true; do
    sleep "$CHECK_INTERVAL"
    
    if ! is_backend_healthy; then
        log "⚠️  Backend is down! Attempting restart..."
        start_backend
        
        if is_backend_healthy; then
            log "✓ Backend recovered successfully"
        else
            log "❌ Backend restart failed. Will retry in ${CHECK_INTERVAL}s"
        fi
    fi
done
