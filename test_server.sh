#!/bin/bash

# Test MCP Server Endpoints

echo "=== MCP Server Test ==="
echo ""

# Function to test endpoint
test_endpoint() {
    local url=$1
    local name=$2
    echo -n "Testing $name... "
    
    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)
    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" == "200" ]; then
        echo "✅ OK (HTTP $http_code)"
        if [ ! -z "$body" ]; then
            echo "  Response: $(echo $body | head -c 100)..."
        fi
    else
        echo "❌ FAIL (HTTP $http_code)"
    fi
    echo ""
}

# Test local endpoints
echo "LOCAL TESTS:"
test_endpoint "http://localhost:9090/" "Root endpoint"
test_endpoint "http://localhost:9090/.well-known/oauth-authorization-server" "OAuth metadata"
test_endpoint "http://localhost:9090/mcp" "MCP endpoint"

# Test remote endpoints
echo ""
echo "REMOTE TESTS:"
test_endpoint "https://mcp.evolutio.io/" "Root endpoint"
test_endpoint "https://mcp.evolutio.io/.well-known/oauth-authorization-server" "OAuth metadata"

# Check if server process is running
echo ""
echo "PROCESS CHECK:"
if pgrep -f "mcp_simple_auth.server" > /dev/null; then
    echo "✅ Server process is running"
    echo "PIDs: $(pgrep -f "mcp_simple_auth.server" | tr '\n' ' ')"
else
    echo "❌ No server process found"
fi

# Check port binding
echo ""
echo "PORT CHECK:"
if lsof -i:9090 > /dev/null 2>&1; then
    echo "✅ Port 9090 is bound"
    lsof -i:9090 | grep LISTEN
else
    echo "❌ Port 9090 is not bound"
fi