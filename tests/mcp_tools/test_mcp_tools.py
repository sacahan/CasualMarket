#!/usr/bin/env python3
"""
測試 MCP 工具註冊腳本。

這個腳本會啟動 MCP 服務器並列出所有可用的工具。
"""

import asyncio

from src.server import mcp


async def test_mcp_tools():
    """測試 MCP 工具註冊。"""
    print("🔧 測試 MCP 工具註冊...")

    try:
        # 獲取工具列表
        tools = mcp.get_tool_definitions()
        print(f"📊 總共找到 {len(tools)} 個工具:")

        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool.name} - {tool.description}")

        # 檢查是否有交易工具
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "get_taiwan_stock_price",
            "buy_taiwan_stock",
            "sell_taiwan_stock",
        ]

        print("\n🔍 檢查預期工具:")
        for tool_name in expected_tools:
            if tool_name in tool_names:
                print(f"  ✅ {tool_name}")
            else:
                print(f"  ❌ {tool_name} - 未找到")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
