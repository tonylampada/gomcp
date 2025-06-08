#!/usr/bin/env python3
"""Test click command execution"""

import subprocess
import sys
import time

print("Testing different ways to run the server...\n")

# Test 1: Direct module execution
print("1. Testing: python -m mcp_simple_auth.server --help")
result = subprocess.run(
    [sys.executable, "-m", "mcp_simple_auth.server", "--help"],
    capture_output=True,
    text=True,
    timeout=5
)
print(f"   Return code: {result.returncode}")
print(f"   Stdout: {result.stdout[:100]}...")
print(f"   Stderr: {result.stderr[:100]}...")

# Test 2: Direct import and call
print("\n2. Testing direct import:")
try:
    from mcp_simple_auth.server import main
    print("   Import successful")
    print(f"   main is: {main}")
    print(f"   main.__name__: {main.__name__}")
    # Check if it's a click command
    if hasattr(main, 'callback'):
        print(f"   main.callback: {main.callback}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Run with arguments
print("\n3. Testing server startup (5 second run):")
proc = subprocess.Popen(
    [sys.executable, "-m", "mcp_simple_auth.server", 
     "--transport", "streamable-http", 
     "--port", "9092", 
     "--host", "0.0.0.0"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait a bit
time.sleep(2)

# Check if it's still running
if proc.poll() is None:
    print("   ✅ Server is running!")
    print("   Checking port...")
    port_check = subprocess.run(["lsof", "-i:9092"], capture_output=True, text=True)
    if port_check.returncode == 0:
        print("   ✅ Port 9092 is bound")
    else:
        print("   ❌ Port 9092 is not bound")
    
    # Kill it
    proc.terminate()
    proc.wait()
else:
    print(f"   ❌ Server exited with code: {proc.returncode}")
    stdout, stderr = proc.communicate()
    print(f"   Stdout: {stdout[:200]}")
    print(f"   Stderr: {stderr[:200]}")

print("\nDone")