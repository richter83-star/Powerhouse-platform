
#!/bin/bash

# Test Online Learning Module
# This script runs comprehensive tests of the online learning system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="${API_BASE_URL:-http://localhost:8000}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Online Learning Module Tests${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to check if API is running
check_api() {
    echo -n "Checking if API is running... "
    if ! curl -s "${BASE_URL}/health" > /dev/null 2>&1; then
        echo -e "${RED}✗${NC}"
        echo ""
        echo "API is not running at $BASE_URL"
        echo "Please start the API first:"
        echo "  ./scripts/start_online_learning.sh"
        exit 1
    fi
    echo -e "${GREEN}✓${NC}"
}

# Function to make API call and format output
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$description${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Request:"
    echo "  $method $endpoint"
    if [ -n "$data" ]; then
        echo "  Data: $data"
    fi
    echo ""
    echo "Response:"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s "${BASE_URL}${endpoint}")
    else
        response=$(curl -s -X POST "${BASE_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    
    # Check if response is valid JSON
    if echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
        echo -e "\n${GREEN}✓ Test passed${NC}"
        return 0
    else
        echo -e "\n${RED}✗ Test failed${NC}"
        return 1
    fi
}

# Run tests
echo ""
echo "Starting tests..."

check_api

# Test 1: Service Status
api_call "GET" "/api/learning/status" "" "Test 1: Check Service Status"

# Test 2: Learning Metrics
api_call "GET" "/api/learning/metrics" "" "Test 2: Get Learning Metrics"

# Test 3: Agent Performance
api_call "GET" "/api/learning/agents/performance" "" "Test 3: Get Agent Performance"

# Test 4: Model Info
api_call "GET" "/api/learning/models/agent_selection" "" "Test 4: Get Model Information"

# Test 5: Predict Best Agent (Simple)
api_call "POST" "/api/learning/predict/agent-selection" \
    '{"top_k": 3}' \
    "Test 5: Predict Best Agent (Simple)"

# Test 6: Predict Best Agent (With Context)
api_call "POST" "/api/learning/predict/agent-selection" \
    '{"task_type": "compliance_analysis", "context": {"complexity": "high"}, "top_k": 3}' \
    "Test 6: Predict Best Agent (With Context)"

# Test 7: Manual Save
api_call "POST" "/api/learning/models/save" "" "Test 7: Manual Model Save"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Test Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}✓ All tests completed successfully${NC}"
echo ""
echo "Next steps:"
echo "  1. View metrics dashboard"
echo "  2. Monitor model performance"
echo "  3. Integrate predictions into workflows"
echo ""
