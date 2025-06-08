#!/bin/bash

# MCP Server Monitoring Script

echo "MCP Server Monitor"
echo "=================="
echo ""

# Check if server is running
if pgrep -f "mcp_simple_auth.server" > /dev/null; then
    echo "✅ Server is running"
    echo ""
    
    # Find latest log file
    LATEST_LOG=$(ls -t logs/mcp_server_*.log 2>/dev/null | head -1)
    
    if [ -n "$LATEST_LOG" ]; then
        echo "Monitoring: $LATEST_LOG"
        echo "Looking for MCP protocol requests..."
        echo ""
        echo "Press Ctrl+C to stop monitoring"
        echo "=================================="
        echo ""
        
        # Monitor for specific MCP-related patterns
        tail -f "$LATEST_LOG" | grep --line-buffered -E "(ListToolsRequest|CallToolRequest|ReadResourceRequest|GET /mcp|POST /mcp|GET /sse|POST /messages|Tool:|Authenticated:|OAuth|ERROR|WARNING)"
    else
        echo "No log files found in logs/ directory"
    fi
else
    echo "❌ Server is not running"
    echo "Start it with: ./start_server.sh"
fi