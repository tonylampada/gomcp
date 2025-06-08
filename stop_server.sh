#!/bin/bash

# MCP Server Stop Script

echo "Stopping MCP server..."

# Find and kill all MCP server processes
PIDS=$(pgrep -f "mcp-simple-auth")

if [ -z "$PIDS" ]; then
    echo "No MCP server processes found."
else
    echo "Found MCP server processes: $PIDS"
    kill $PIDS
    sleep 2
    
    # Check if processes are still running
    if pgrep -f "mcp-simple-auth" > /dev/null; then
        echo "Some processes didn't stop gracefully. Force killing..."
        pkill -9 -f "mcp-simple-auth"
    fi
    
    echo "✅ MCP server stopped."
fi