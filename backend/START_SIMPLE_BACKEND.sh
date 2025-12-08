
#!/bin/bash

# Start Simple Backend API Server for Powerhouse Multi-Agent Platform
# This script starts the lightweight FastAPI backend server

echo "================================================"
echo "Powerhouse Multi-Agent Platform"
echo "Starting Simple Backend API Server (Port 8001)"
echo "================================================"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")"

echo "Current directory: $(pwd)"
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "✓ Python version: $(python --version)"
echo ""

# Check if FastAPI and uvicorn are installed
echo "Checking dependencies..."
python -c "import fastapi; import uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: Required packages not installed"
    echo "Installing FastAPI and uvicorn..."
    pip install fastapi uvicorn[standard] pydantic
fi

echo "✓ Dependencies installed"
echo ""

# Check if port 8001 is already in use
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Warning: Port 8001 is already in use"
    echo "Finding process..."
    PID=$(lsof -ti:8001)
    echo "Process ID: $PID"
    read -p "Do you want to kill this process and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill -9 $PID
        echo "✓ Process killed"
        sleep 2
    else
        echo "Exiting..."
        exit 1
    fi
fi

# Start the server
echo "Starting Simple FastAPI server..."
echo ""
echo "Backend API will be available at:"
echo "  ✓ Main API: http://localhost:8001"
echo "  ✓ Health Check: http://localhost:8001/health"
echo "  ✓ Agents API: http://localhost:8001/api/v1/agents"
echo "  ✓ API Docs: http://localhost:8001/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Run in background and log to file
nohup python simple_api.py > /tmp/simple_backend.log 2>&1 &
PID=$!

# Wait a moment and check if it started successfully
sleep 3

if ps -p $PID > /dev/null; then
    echo "✓ Backend started successfully (PID: $PID)"
    echo "✓ Logs: /tmp/simple_backend.log"
    echo ""
    
    # Test the endpoint
    echo "Testing backend..."
    HEALTH_CHECK=$(curl -s http://localhost:8001/health 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "✓ Backend is responding"
        echo "✓ Health check: $HEALTH_CHECK"
        echo ""
        
        # Check agents count
        AGENT_COUNT=$(curl -s http://localhost:8001/api/v1/agents 2>/dev/null | grep -o '"total_count":[0-9]*' | grep -o '[0-9]*')
        if [ ! -z "$AGENT_COUNT" ]; then
            echo "✓ Agents loaded: $AGENT_COUNT agents available"
        fi
    else
        echo "⚠️  Backend started but not responding yet. Check logs:"
        echo "    tail -f /tmp/simple_backend.log"
    fi
    
    echo ""
    echo "================================================"
    echo "Backend is running!"
    echo "View logs: tail -f /tmp/simple_backend.log"
    echo "Stop backend: kill $PID"
    echo "================================================"
else
    echo "❌ Failed to start backend. Check logs:"
    echo "    tail -f /tmp/simple_backend.log"
    exit 1
fi
