#!/usr/bin/env python3
"""Final test of the working MCP server."""

import asyncio
import json
import httpx
import uuid

async def test_mcp_working():
    """Test the working MCP server."""
    base_url = "https://mcp.evolutio.io"
    
    print("MCP Final Test")
    print("=" * 50)
    
    # Test initialize and then tools/list
    async with httpx.AsyncClient() as client:
        # Initialize
        print("1. Initialize...")
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
        
        response = await client.post(
            f"{base_url}/mcp/",
            json=init_request,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        )
        print(f"Initialize Status: {response.status_code}")
        print(f"Initialize Response: {response.text}")
        
        # Tools list
        print("\n2. List tools...")
        tools_request = {
            "jsonrpc": "2.0", 
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        response = await client.post(
            f"{base_url}/mcp/",
            json=tools_request,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        )
        print(f"Tools Status: {response.status_code}")
        print(f"Tools Response: {response.text}")
        
        if "get_user_profile" in response.text:
            print("\n✅ SUCCESS! Tools are discoverable!")
        else:
            print("\n❌ Tools not found in response")

if __name__ == "__main__":
    asyncio.run(test_mcp_working())