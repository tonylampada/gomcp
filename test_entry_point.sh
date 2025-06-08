#!/bin/bash

echo "Testing mcp-simple-auth entry point..."

# Test the installed script
echo ""
echo "1. Testing mcp-simple-auth --help:"
timeout 5 uv run mcp-simple-auth --help

echo ""
echo "2. Starting server with mcp-simple-auth:"
timeout 10 uv run mcp-simple-auth --transport streamable-http --port 9090 --host 0.0.0.0 > test_ep.log 2>&1 &
EP_PID=$!

sleep 3

echo "   Checking processes:"
pgrep -af "mcp" | grep -v grep | grep -v "test_entry"

echo ""
echo "   Checking port:"
lsof -i:9090 2>/dev/null | grep LISTEN

echo ""
echo "   Log contents:"
cat test_ep.log

# Cleanup
pkill -f mcp-simple-auth 2>/dev/null
rm -f test_ep.log