# MCP Tools Availability Progress

## Goal
Make the MCP server tools available to Claude.ai after successful OAuth authentication.

## Current Status (as of 2025-06-08)

### ✅ Completed
1. **Server Infrastructure**
   - MCP server running on port 9090
   - Server accessible at https://mcp.evolutio.io
   - Using SSE (Server-Sent Events) transport
   - OAuth discovery endpoint working correctly

2. **GitHub OAuth Authentication**
   - OAuth flow completes successfully
   - Fixed double-slash issue in authorization URL
   - Fixed missing `scopes` parameter in authorization handler
   - Tokens are issued and stored correctly

3. **MCP Protocol**
   - SSE endpoint (`/sse`) is working
   - Messages endpoint (`/messages/`) is working
   - Server properly handles session creation
   - MCP protocol requests (initialize, tools/list) are received

### ❌ Current Issue
- **Claude.ai doesn't discover tools**: After successful OAuth authentication, Claude.ai:
  - Successfully completes OAuth flow
  - Hits the root endpoint (`GET /`)
  - BUT never attempts to connect to SSE endpoint (`/sse`)
  - Reports "no tools available"

## Debug Process & Commands

### 1. Server Management
```bash
# Start server with SSE transport
./start_server.sh

# Stop server
./stop_server.sh

# Monitor logs in real-time
tail -f logs/mcp_server_$(ls -t logs/ | head -1)

# Check if server is running
ps aux | grep mcp
```

### 2. Testing MCP Protocol
Created test scripts to understand the protocol:
- `test_mcp_direct.py` - Basic endpoint testing
- `test_mcp_complete.py` - Full SSE session testing

Key findings:
- SSE endpoint returns a session ID: `/messages/?session_id=XXX`
- Must use the server-provided session ID, not a client-generated one
- Protocol flow: SSE connection → Initialize → List Tools

### 3. Log Analysis
```bash
# Check for MCP protocol activity
tail -30 logs/mcp_server_*.log | grep -E "(SSE|session|tools|list)"

# Check what happens after OAuth
grep -A10 "POST /token HTTP/1.1" logs/mcp_server_*.log

# Filter out noise from logs
tail -30 logs/mcp_server_*.log | grep -v "multipart" | grep -v "httpcore"
```

## Technical Details Discovered

### 1. Authentication Architecture
- Removed authentication requirement from MCP protocol endpoints
- OAuth is now only required for tool execution, not discovery
- This allows Claude.ai to see tools before authenticating

### 2. Transport Configuration
- Switched from `streamable-http` to `sse` transport (more reliable)
- SSE endpoint properly configured at `/sse`
- Messages endpoint at `/messages/` requires session_id parameter

### 3. URL Issues Fixed
- OAuth discovery was returning URLs with double slashes
- Fixed by using `str(settings.server_url).rstrip('/')`
- Authorization endpoint now correctly at `/authorize` (not `//authorize`)

### 4. Root Endpoint Discovery
Currently returning:
```json
{
  "mcp": {
    "version": "1.0"
  },
  "transport": {
    "type": "sse",
    "endpoint": "/sse"
  }
}
```

## Key Code Changes

### 1. Removed Auth Requirement for Discovery
```python
auth_settings = AuthSettings(
    # ...
    required_scopes=[],  # Don't require auth for discovery
)

app = FastMCP(
    # No auth parameter - allows unauthenticated access
)
```

### 2. Manual OAuth Endpoints
Added OAuth endpoints manually since we removed the auth provider from FastMCP:
- `/.well-known/oauth-authorization-server`
- `/authorize`
- `/token`
- `/github/callback`

### 3. Tool with Conditional Auth
```python
@app.tool()
async def get_user_profile(mcp_token: str = "") -> dict[str, Any]:
    # Tool is visible without auth
    # But returns message that auth is required for actual use
```

## Current Hypothesis

Claude.ai is not recognizing this as a valid MCP server because:
1. The root endpoint discovery format might not match expectations
2. Claude.ai might expect a different protocol version or transport configuration
3. There might be additional headers or metadata required

## Next Steps

1. **Research MCP Discovery Spec**
   - Find official MCP server discovery documentation
   - Compare with working MCP servers

2. **Test Different Discovery Formats**
   - Try different root endpoint responses
   - Test with minimal vs detailed discovery info

3. **Monitor Claude.ai Behavior**
   - Check if Claude.ai makes any other requests we're missing
   - Look for patterns in successful MCP server connections

4. **Alternative Approaches**
   - Try WebSocket transport instead of SSE
   - Test with different MCP protocol versions