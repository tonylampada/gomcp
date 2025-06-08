#!/usr/bin/env python3
"""Comprehensive MCP server test to understand the protocol."""

import asyncio
import json
import httpx
import uuid

async def test_mcp_sse_session():
    """Test establishing an SSE session and sending MCP requests."""
    base_url = "https://mcp.evolutio.io"
    session_id = str(uuid.uuid4())
    
    print("MCP Protocol Testing")
    print("=" * 50)
    
    # 1. Check root endpoint
    print("\n1. Root endpoint check...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/")
        print(f"Root Status: {response.status_code}")
        print(f"Root Response: {response.text}")
    
    # 2. Try to establish SSE connection with proper headers
    print(f"\n2. Establishing SSE session...")
    server_session_id = None
    try:
        async with httpx.AsyncClient() as client:
            # SSE requires Accept: text/event-stream
            headers = {
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            }
            
            # Start SSE stream
            async with client.stream('GET', f"{base_url}/sse", headers=headers, timeout=5.0) as response:
                print(f"SSE Status: {response.status_code}")
                
                # Read first few events to get session ID
                async for line in response.aiter_lines():
                    if line.startswith("data: /messages/?session_id="):
                        server_session_id = line.split("session_id=")[1]
                        print(f"Got server session ID: {server_session_id}")
                        break
                    print(f"SSE Event: {line}")
    except Exception as e:
        print(f"SSE Error: {e}")
    
    if not server_session_id:
        print("Failed to get session ID from server")
        return
        
    # Update session_id to use the server-provided one
    session_id = server_session_id
    
    # 3. Send initialize request
    print("\n3. Sending initialize request...")
    try:
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/messages/?session_id={session_id}",
                json=init_request,
                headers={"Content-Type": "application/json"}
            )
            print(f"Initialize Status: {response.status_code}")
            print(f"Initialize Response: {response.text}")
    except Exception as e:
        print(f"Initialize Error: {e}")
    
    # 4. Send tools/list request
    print("\n4. Sending tools/list request...")
    try:
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/messages/?session_id={session_id}",
                json=list_tools_request,
                headers={"Content-Type": "application/json"}
            )
            print(f"ListTools Status: {response.status_code}")
            print(f"ListTools Response: {response.text}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "result" in result and "tools" in result["result"]:
                        tools = result["result"]["tools"]
                        print(f"\n✅ Found {len(tools)} tools!")
                        for tool in tools:
                            print(f"  - {tool.get('name', 'Unknown')}")
                            print(f"    Description: {tool.get('description', 'No description')[:100]}...")
                    else:
                        print("\n⚠️  No tools in response")
                except Exception as e:
                    print(f"⚠️  Parse error: {e}")
    except Exception as e:
        print(f"ListTools Error: {e}")
    
    # 5. Check what transports are available
    print("\n5. Checking available transports...")
    endpoints = ["/sse", "/messages/", "/mcp", "/mcp/"]
    for endpoint in endpoints:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(f"{base_url}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
        except Exception as e:
            print(f"{endpoint}: Error - {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_sse_session())