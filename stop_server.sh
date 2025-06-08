#!/bin/bash

# MCP Server Stop Script

echo "Stopping MCP server..."

# Find and kill all MCP server processes
PIDS=$(pgrep -f "mcp_simple_auth.server")

if [ -z "$PIDS" ]; then
    echo "No MCP server processes found."
else
    echo "Found MCP server processes: $PIDS"
    kill $PIDS
    sleep 2
    
    # Check if processes are still running
    if pgrep -f "mcp_simple_auth.server" > /dev/null; then
        echo "Some processes didn't stop gracefully. Force killing..."
        pkill -9 -f "mcp_simple_auth.server"
    fi
    
    echo "✅ MCP server stopped."
fi