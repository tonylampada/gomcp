#!/usr/bin/env python3
"""Debug wrapper for MCP server startup"""

import sys
import os
import subprocess

print("=== MCP Server Debug Wrapper ===")
print(f"Python: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Environment vars:")
print(f"  MCP_GITHUB_GITHUB_CLIENT_ID: {'SET' if os.getenv('MCP_GITHUB_GITHUB_CLIENT_ID') else 'NOT SET'}")
print(f"  MCP_GITHUB_GITHUB_CLIENT_SECRET: {'SET' if os.getenv('MCP_GITHUB_GITHUB_CLIENT_SECRET') else 'NOT SET'}")
print("")

try:
    print("Attempting to import mcp_simple_auth.server...")
    from mcp_simple_auth.server import main
    print("✅ Import successful")
    
    print("\nCalling main() with arguments:")
    print("  --transport streamable-http")
    print("  --port 9090") 
    print("  --host 0.0.0.0")
    print("")
    
    # Call main with sys.argv manipulation
    original_argv = sys.argv
    sys.argv = ['server.py', '--transport', 'streamable-http', '--port', '9090', '--host', '0.0.0.0']
    
    exit_code = main()
    print(f"\nMain function returned: {exit_code}")
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)