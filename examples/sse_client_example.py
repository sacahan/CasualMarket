#!/usr/bin/env python3
"""
Example client for CasualMarket MCP Server SSE endpoint.

This script demonstrates how to interact with the MCP server
running in Docker via the SSE HTTP interface.
"""

import json
import requests


class MCPSSEClient:
    """Simple client for MCP server SSE endpoint"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.sse_url = f"{base_url}/sse"
        self.request_id = 0
    
    def _next_id(self) -> int:
        """Generate next request ID"""
        self.request_id += 1
        return self.request_id
    
    def list_tools(self) -> dict:
        """List all available tools"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {}
        }
        
        response = requests.post(
            self.sse_url,
            json=request,
            headers={"Content-Type": "application/json"}
        )
        
        # Parse SSE response
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                return json.loads(line[6:])
        
        return {}
    
    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a specific tool with arguments"""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = requests.post(
            self.sse_url,
            json=request,
            headers={"Content-Type": "application/json"}
        )
        
        # Parse SSE response
        for line in response.text.split('\n'):
            if line.startswith('data: '):
                return json.loads(line[6:])
        
        return {}
    
    def health_check(self) -> dict:
        """Check server health"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()


def main():
    """Example usage of MCP SSE client"""
    
    # Create client
    client = MCPSSEClient()
    
    print("🏥 Health Check")
    print("=" * 50)
    health = client.health_check()
    print(json.dumps(health, indent=2, ensure_ascii=False))
    print()
    
    print("🔧 List Available Tools")
    print("=" * 50)
    tools_response = client.list_tools()
    
    if "result" in tools_response:
        tools = tools_response["result"].get("tools", [])
        print(f"Found {len(tools)} tools:")
        for tool in tools[:5]:  # Show first 5 tools
            print(f"  - {tool.get('name')}: {tool.get('description', '')[:60]}...")
    print()
    
    print("📊 Get Stock Price (台積電 2330)")
    print("=" * 50)
    result = client.call_tool(
        "get_taiwan_stock_price",
        {"symbol": "2330"}
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()
    
    print("📈 Get Stock Price (鴻海 2317)")
    print("=" * 50)
    result = client.call_tool(
        "get_taiwan_stock_price",
        {"symbol": "2317"}
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()
    
    print("💰 Buy Stock Simulation")
    print("=" * 50)
    result = client.call_tool(
        "buy_taiwan_stock",
        {
            "symbol": "2330",
            "quantity": 1000,
            "price": None  # Market price
        }
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to MCP server at http://localhost:8000")
        print("Please ensure the Docker container is running:")
        print("  docker-compose up -d")
    except Exception as e:
        print(f"❌ Error: {e}")
