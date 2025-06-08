#!/bin/bash

# MCP Server Startup Script with Debug

echo "=== MCP Server Startup Debug ==="
echo "Date: $(date)"
echo ""

# Function to print debug info
debug() {
    echo "[DEBUG $(date +%H:%M:%S)] $1"
}

# Kill any existing server processes
debug "Stopping any existing MCP server processes..."
pkill -f "mcp_simple_auth.server" 2>/dev/null || true
sleep 2

# Check for .env file
if [ -f ".env" ]; then
    debug "Found .env file"
    # Source the .env file to load variables
    export $(cat .env | grep -v '^#' | xargs)
else
    debug "WARNING: No .env file found"
fi

# Verify environment variables
debug "Checking environment variables..."
if [ -z "$MCP_GITHUB_GITHUB_CLIENT_ID" ]; then
    echo "ERROR: MCP_GITHUB_GITHUB_CLIENT_ID not set"
    exit 1
else
    debug "MCP_GITHUB_GITHUB_CLIENT_ID is set (length: ${#MCP_GITHUB_GITHUB_CLIENT_ID})"
fi

if [ -z "$MCP_GITHUB_GITHUB_CLIENT_SECRET" ]; then
    echo "ERROR: MCP_GITHUB_GITHUB_CLIENT_SECRET not set"
    exit 1
else
    debug "MCP_GITHUB_GITHUB_CLIENT_SECRET is set (length: ${#MCP_GITHUB_GITHUB_CLIENT_SECRET})"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Set log file with timestamp
LOG_FILE="logs/mcp_server_$(date +%Y%m%d_%H%M%S).log"

debug "Starting MCP server..."
debug "Log file: $LOG_FILE"
debug "Server URL: https://mcp.evolutio.io"
debug "Local port: 9090"

# Check if port is already in use
if lsof -i:9090 >/dev/null 2>&1; then
    echo "ERROR: Port 9090 is already in use!"
    lsof -i:9090
    exit 1
fi

# Run server with UV using the entry point
debug "Executing: uv run mcp-simple-auth --transport sse --port 9090 --host 0.0.0.0"
uv run mcp-simple-auth \
    --transport sse \
    --port 9090 \
    --host 0.0.0.0 \
    > "$LOG_FILE" 2>&1 &

# Get the PID
UV_PID=$!
debug "Started UV process with PID: $UV_PID"

# Wait a moment for server to start
debug "Waiting for server to initialize..."
sleep 5

# UV spawns a child Python process - find it
PYTHON_PID=$(pgrep -P $UV_PID -f "mcp-simple-auth" | head -1)
if [ -z "$PYTHON_PID" ]; then
    # Sometimes the python process is not a direct child
    PYTHON_PID=$(pgrep -f "mcp-simple-auth" | grep -v $UV_PID | head -1)
fi

if [ -z "$PYTHON_PID" ]; then
    echo "❌ Server process not found (UV PID $UV_PID exists but no Python subprocess)"
    echo "Running processes:"
    pgrep -af "mcp_simple_auth"
    echo ""
    echo "Last 20 lines of log:"
    tail -20 "$LOG_FILE"
    exit 1
fi

debug "Found Python server process with PID: $PYTHON_PID"
SERVER_PID=$PYTHON_PID

# Check if port is now bound
debug "Checking if port 9090 is bound..."
if ! lsof -i:9090 >/dev/null 2>&1; then
    echo "❌ Server process is running but port 9090 is not bound"
    echo "Process info:"
    ps -p $SERVER_PID -f
    echo ""
    echo "Last 20 lines of log:"
    tail -20 "$LOG_FILE"
    exit 1
fi

# Test local connectivity
debug "Testing local connectivity..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/ 2>/dev/null || echo "FAIL")
if [ "$RESPONSE" != "200" ]; then
    echo "❌ Server not responding on localhost:9090 (HTTP status: $RESPONSE)"
    echo ""
    echo "Last 20 lines of log:"
    tail -20 "$LOG_FILE"
    exit 1
fi

debug "Local connectivity test passed (HTTP 200)"

# Test remote connectivity
debug "Testing remote connectivity to https://mcp.evolutio.io..."
REMOTE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://mcp.evolutio.io/ 2>/dev/null || echo "FAIL")
debug "Remote response: $REMOTE_RESPONSE"

if [ "$REMOTE_RESPONSE" == "200" ]; then
    echo "✅ Server started successfully and accessible remotely!"
else
    echo "✅ Server started successfully (PID: $SERVER_PID)"
    echo "⚠️  Remote access returned: $REMOTE_RESPONSE (may need time to propagate)"
fi

echo ""
echo "Server details:"
echo "  PID: $SERVER_PID"
echo "  Local URL: http://localhost:9090"
echo "  Remote URL: https://mcp.evolutio.io"
echo "  Log file: $LOG_FILE"
echo ""
echo "Monitor logs with:"
echo "  tail -f $LOG_FILE"
echo ""
echo "Stop server with:"
echo "  kill $SERVER_PID"