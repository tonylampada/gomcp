# MCP Tools Availability Progress

## Goal
Make the MCP server tools available to Claude.ai after successful OAuth authentication.

## Current Status

### ✅ Completed
1. **Server Infrastructure**
   - MCP server running on port 9090
   - GitHub OAuth authentication working
   - Server accessible at https://mcp.evolutio.io
   - OAuth flow completes successfully with proper `claudeai` scope

2. **Authentication Flow**
   - Claude.ai can connect and authenticate
   - OAuth callback works correctly
   - Access tokens are issued with correct scope

### ❌ Current Issue
- **Tools not visible**: After successful authentication, Claude.ai reports "no tools available"
- The server has one tool registered: `get_user_profile`
- Authentication shows as successful in logs: `Root endpoint accessed. Authenticated: True`

## Investigation Notes

### What We Know
1. The OAuth scope was initially misconfigured (was "user", now "claudeai")
2. Server logs show successful authentication but no MCP protocol connections
3. The root endpoint (`/`) returns tool list but Claude.ai might need different endpoints
4. Expected MCP endpoints:
   - `/mcp` - StreamableHTTP endpoint
   - `/sse` - Server-sent events endpoint  
   - `/messages/` - Messages endpoint

### Next Steps to Investigate

1. **Check MCP Protocol Communication**
   - Monitor server logs for MCP-specific requests after auth
   - Verify Claude.ai is hitting the correct MCP endpoints
   - Check if tools are properly exposed via MCP protocol

2. **Tool Registration Verification**
   - Confirm `get_user_profile` tool is registered in FastMCP
   - Check if tools require specific transport (SSE vs StreamableHTTP)
   - Verify tool metadata is correct

3. **Debug MCP Handshake**
   - Add logging to MCP protocol endpoints
   - Check if Claude.ai sends ListToolsRequest
   - Verify server responds with tool list

4. **Authentication Context**
   - Ensure authenticated context is passed to MCP handlers
   - Check if tools are filtered by authentication status
   - Verify GitHub token mapping works correctly

## Server Details
- **URL**: https://mcp.evolutio.io
- **Port**: 9090
- **Transport**: streamable-http
- **Auth**: GitHub OAuth with `claudeai` scope
- **Tool Count**: 1 (`get_user_profile`)

## Logs to Monitor
```bash
# Watch server logs for MCP requests
tail -f server_output.log | grep -E "(ListToolsRequest|CallToolRequest|mcp|tools)"
```

## Scripts Created
1. **`start_server.sh`** - Start MCP server with timestamped logging
2. **`stop_server.sh`** - Stop all MCP server processes  
3. **`monitor_mcp.sh`** - Monitor server logs for MCP protocol activity

## Usage
```bash
# Start server
./start_server.sh

# Monitor MCP protocol requests
./monitor_mcp.sh

# Stop server
./stop_server.sh
```

## Next Action Items
- [ ] Start server and monitor MCP protocol requests
- [ ] Add debug logging to MCP endpoints
- [ ] Test tool discovery manually via curl
- [ ] Check FastMCP tool registration process
- [ ] Verify authentication context in tool handlers