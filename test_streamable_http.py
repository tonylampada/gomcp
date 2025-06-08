#!/usr/bin/env python3
"""Test the streamable-http MCP server."""

import asyncio
import json
import httpx

async def test_streamable_http():
    """Test the streamable-http MCP protocol."""
    base_url = "https://mcp.evolutio.io"
    
    print("MCP StreamableHTTP Testing")
    print("=" * 50)
    
    # 1. Check root endpoint
    print("\n1. Root endpoint check...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/")
        print(f"Root Status: {response.status_code}")
        print(f"Root Response: {response.text}")
    
    # 2. Test tools/list request to /mcp endpoint
    print("\n2. Sending tools/list request to /mcp...")
    try:
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/mcp",
                json=list_tools_request,
                headers={"Content-Type": "application/json"},
                timeout=10.0
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
                        print(f"\n⚠️  No tools in response: {result}")
                except Exception as e:
                    print(f"⚠️  Parse error: {e}")
            else:
                print(f"\n❌ Failed with status {response.status_code}")
    except Exception as e:
        print(f"ListTools Error: {e}")
    
    # 3. Test initialize request
    print("\n3. Sending initialize request...")
    try:
        init_request = {
            "jsonrpc": "2.0",
            "id": 2,
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
                f"{base_url}/mcp",
                json=init_request,
                headers={"Content-Type": "application/json"},
                timeout=10.0
            )
            print(f"Initialize Status: {response.status_code}")
            print(f"Initialize Response: {response.text}")
    except Exception as e:
        print(f"Initialize Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_streamable_http())