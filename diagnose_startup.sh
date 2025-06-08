#!/bin/bash

# Comprehensive Startup Diagnostics Script

echo "=== MCP Server Startup Diagnostics ==="
echo "Date: $(date)"
echo ""

# Stop any existing servers
echo "1. Stopping existing servers..."
pkill -f "mcp_simple_auth.server" 2>/dev/null || true
sleep 2

# Check environment
echo ""
echo "2. Environment Check:"
echo "   Python version: $(python --version 2>&1)"
echo "   UV version: $(uv --version 2>&1)"
echo "   Working directory: $(pwd)"

# Check .env file
echo ""
echo "3. Environment Variables:"
if [ -f ".env" ]; then
    echo "   .env file exists"
    export $(cat .env | grep -v '^#' | xargs)
    echo "   MCP_GITHUB_GITHUB_CLIENT_ID: ${MCP_GITHUB_GITHUB_CLIENT_ID:0:5}... (${#MCP_GITHUB_GITHUB_CLIENT_ID} chars)"
    echo "   MCP_GITHUB_GITHUB_CLIENT_SECRET: ${MCP_GITHUB_GITHUB_CLIENT_SECRET:0:5}... (${#MCP_GITHUB_GITHUB_CLIENT_SECRET} chars)"
else
    echo "   ERROR: No .env file found!"
fi

# Test module import
echo ""
echo "4. Testing Module Import:"
uv run python -c "
try:
    import mcp_simple_auth.server
    print('   ✅ Module import successful')
except Exception as e:
    print(f'   ❌ Import failed: {e}')
" 2>&1

# Test click help
echo ""
echo "5. Testing Click CLI:"
echo "   Running: uv run python -m mcp_simple_auth.server --help"
timeout 5 uv run python -m mcp_simple_auth.server --help 2>&1 | head -20 || echo "   Timeout or error"

# Test server startup with explicit output
echo ""
echo "6. Testing Server Startup (10 second timeout):"
mkdir -p logs
LOG_FILE="logs/diagnose_$(date +%Y%m%d_%H%M%S).log"

echo "   Starting server..."
timeout 10 uv run python -m mcp_simple_auth.server --transport streamable-http --port 9090 --host 0.0.0.0 > "$LOG_FILE" 2>&1 &
TIMEOUT_PID=$!

# Wait a bit
sleep 3

# Check processes
echo ""
echo "7. Process Check:"
echo "   UV processes:"
pgrep -af "uv.*mcp_simple_auth" || echo "   None found"
echo ""
echo "   Python processes:"
pgrep -af "python.*mcp_simple_auth" || echo "   None found"

# Check port
echo ""
echo "8. Port Check:"
if lsof -i:9090 2>/dev/null | grep LISTEN; then
    echo "   ✅ Port 9090 is bound"
else
    echo "   ❌ Port 9090 is not bound"
fi

# Check log file
echo ""
echo "9. Log File Contents (first 30 lines):"
if [ -f "$LOG_FILE" ]; then
    head -30 "$LOG_FILE"
else
    echo "   Log file not created"
fi

# Wait for timeout to complete
wait $TIMEOUT_PID 2>/dev/null

# Test direct Python execution
echo ""
echo "10. Testing Direct Python Execution:"
cat > test_direct.py << 'EOF'
import sys
import os

print("Direct execution test:")
print(f"  Python: {sys.version}")
print(f"  CWD: {os.getcwd()}")

# Set up environment
os.environ.setdefault('MCP_GITHUB_GITHUB_CLIENT_ID', 'test')
os.environ.setdefault('MCP_GITHUB_GITHUB_CLIENT_SECRET', 'test')

try:
    from mcp_simple_auth.server import main
    print("  Import successful")
    
    # Simulate command line args
    sys.argv = ['server.py', '--transport', 'streamable-http', '--port', '9091', '--host', '0.0.0.0']
    print("  Calling main() with port 9091...")
    
    # This will block if successful
    exit_code = main()
    print(f"  Main returned: {exit_code}")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()
EOF

timeout 5 uv run python test_direct.py 2>&1

# Cleanup
echo ""
echo "11. Cleanup:"
pkill -f "mcp_simple_auth.server" 2>/dev/null || true
rm -f test_direct.py
echo "   Done"

echo ""
echo "=== Diagnostics Complete ==="