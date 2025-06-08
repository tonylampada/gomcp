# Server Startup Debug Plan

## Problem
The server appears to exit immediately when started via the startup script, but runs correctly when tested interactively.

## Diagnosis Steps

1. **Environment Variables**
   - Check if .env file is being loaded
   - Verify MCP_GITHUB_GITHUB_CLIENT_ID and MCP_GITHUB_GITHUB_CLIENT_SECRET are available

2. **Process Lifecycle**
   - Track exact moment when process exits
   - Check if UV is spawning subprocesses
   - Verify PID tracking is correct

3. **Network Binding**
   - Check if port 9090 gets bound
   - Test if server responds to requests
   - Verify https://mcp.evolutio.io connectivity

4. **Error Capture**
   - Ensure all stderr output is captured
   - Check for silent failures
   - Add debug output at each stage

## Fix Strategy

1. Update start_server.sh with:
   - Environment variable validation
   - Process existence checks
   - Network connectivity tests
   - Better error reporting

2. Add health check endpoint test
3. Use curl to verify server is responding
4. Add retry logic if server takes time to start