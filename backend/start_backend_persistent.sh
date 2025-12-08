
#!/bin/bash

# Persistent Backend Startup
# This script ensures the backend stays running using multiple methods

BACKEND_DIR="/home/ubuntu/powerhouse_b2b_platform/backend"
cd "$BACKEND_DIR"

echo "================================================"
echo "Powerhouse Backend - Persistent Startup"
echo "================================================"
echo ""

# Check if watchdog is already running
if ps aux | grep -v grep | grep "keep_backend_alive.sh" > /dev/null; then
    echo "✓ Watchdog is already running"
    WATCHDOG_PID=$(ps aux | grep -v grep | grep "keep_backend_alive.sh" | awk '{print $2}')
    echo "  PID: $WATCHDOG_PID"
else
    echo "Starting watchdog..."
    # Start watchdog in a screen session for persistence
    if command -v screen &> /dev/null; then
        screen -dmS backend-watchdog bash keep_backend_alive.sh
        echo "✓ Watchdog started in screen session 'backend-watchdog'"
        echo "  View: screen -r backend-watchdog"
    else
        # Fallback to nohup if screen not available
        nohup bash keep_backend_alive.sh > /tmp/backend_watchdog.log 2>&1 &
        echo "✓ Watchdog started in background"
    fi
fi

echo ""

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..20}; do
    if curl -s -f http://localhost:8001/health > /dev/null 2>&1; then
        echo ""
        echo "✓ Backend is ready!"
        echo ""
        echo "Backend Information:"
        echo "  URL: http://localhost:8001"
        echo "  Health: http://localhost:8001/health"
        echo "  API Docs: http://localhost:8001/docs"
        echo "  Agents API: http://localhost:8001/api/v1/agents"
        echo ""
        echo "Monitoring:"
        echo "  Backend logs: tail -f /tmp/simple_backend.log"
        echo "  Watchdog logs: tail -f /tmp/backend_watchdog.log"
        echo "  Backend status: curl http://localhost:8001/health"
        echo ""
        echo "Management:"
        if ps aux | grep -v grep | grep "keep_backend_alive.sh" | grep "screen" > /dev/null; then
            echo "  View watchdog: screen -r backend-watchdog"
            echo "  Kill watchdog: screen -X -S backend-watchdog quit"
        else
            WATCHDOG_PID=$(ps aux | grep -v grep | grep "keep_backend_alive.sh" | awk '{print $2}')
            echo "  Stop watchdog: kill $WATCHDOG_PID"
        fi
        echo ""
        echo "✓ Persistent backend with auto-restart is now active!"
        echo "================================================"
        exit 0
    fi
    echo "  Waiting... ($i/20)"
    sleep 2
done

echo ""
echo "⚠️  Backend taking longer than expected to start"
echo "   Check logs: tail -f /tmp/simple_backend.log"
echo "================================================"
exit 1
