#!/bin/bash

# MCP Server Startup Script

# Kill any existing server processes
echo "Stopping any existing MCP server processes..."
pkill -f "mcp_simple_auth.server" 2>/dev/null || true
sleep 2

# Create logs directory if it doesn't exist
mkdir -p logs

# Set log file with timestamp
LOG_FILE="logs/mcp_server_$(date +%Y%m%d_%H%M%S).log"

# Start the server
echo "Starting MCP server..."
echo "Log file: $LOG_FILE"
echo "Server URL: https://mcp.evolutio.io"
echo "Local port: 9090"
echo ""

# Run server with UV
uv run python -m mcp_simple_auth.server \
    --transport streamable-http \
    --port 9090 \
    --host 0.0.0.0 \
    > "$LOG_FILE" 2>&1 &

# Get the PID
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

# Check if server started successfully
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Server started successfully (PID: $SERVER_PID)"
    echo ""
    echo "Monitor logs with:"
    echo "  tail -f $LOG_FILE"
    echo ""
    echo "Stop server with:"
    echo "  kill $SERVER_PID"
else
    echo "❌ Failed to start server"
    echo "Check logs at: $LOG_FILE"
    exit 1
fi