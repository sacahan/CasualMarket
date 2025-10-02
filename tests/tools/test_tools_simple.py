"""
簡單的工具測試腳本。
"""

import asyncio

from src.server import mcp


async def test_tools():
    """測試工具定義。"""
    print("🔧 測試工具定義...")

    all_tools = [tool for tool in mcp._tools.values()]

    print(f"📊 總共找到 {len(all_tools)} 個工具:")
    for tool in all_tools:
        print(f"  - {tool.name}: {tool.description}")

    print("\n🔍 所有工具名稱:")
    for i, tool in enumerate(all_tools, 1):
        print(f"  {i}. {tool.name}")

    # Basic assertions to ensure some tools are found
    assert len(all_tools) > 0
    assert any(tool.name == "get_taiwan_stock_price" for tool in all_tools)
    assert any(tool.name == "buy_taiwan_stock" for tool in all_tools)


if __name__ == "__main__":
    asyncio.run(test_tools())