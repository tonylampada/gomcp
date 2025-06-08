#!/usr/bin/env python3
"""Test MCP server directly to see if tools are discoverable."""

import asyncio
import json
import httpx

async def test_mcp_server():
    """Test the MCP server directly."""
    base_url = "https://mcp.evolutio.io"
    
    print("Testing MCP Server Tool Discovery")
    print("=" * 40)
    
    # Test SSE endpoint - establish session
    print("\n1. Testing SSE endpoint...")
    session_id = "test-session-123"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/sse?session_id={session_id}")
            print(f"SSE Status: {response.status_code}")
            print(f"SSE Response: {response.text[:200]}")
    except Exception as e:
        print(f"SSE Error: {e}")
    
    # Test messages endpoint  
    print("\n2. Testing Messages endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/messages/")
            print(f"Messages Status: {response.status_code}")
            print(f"Messages Response: {response.text[:200]}")
    except Exception as e:
        print(f"Messages Error: {e}")
    
    # Test OAuth discovery
    print("\n3. Testing OAuth discovery...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/.well-known/oauth-authorization-server")
            print(f"OAuth Discovery Status: {response.status_code}")
            oauth_config = response.json()
            print(f"Required scopes: {oauth_config.get('scopes_supported', [])}")
    except Exception as e:
        print(f"OAuth Discovery Error: {e}")
    
    # Try to send a ListTools request via POST to messages endpoint with session_id
    print("\n4. Testing MCP ListTools request...")
    try:
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 1,
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
                        print(f"✅ Found {len(tools)} tools!")
                        for tool in tools:
                            print(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                    else:
                        print("⚠️  No tools found in response")
                except:
                    print("⚠️  Could not parse JSON response")
    except Exception as e:
        print(f"ListTools Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())