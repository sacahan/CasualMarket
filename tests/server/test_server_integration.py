"""
MCP 服務器整合測試。

測試 MCP 服務器是否正確註冊和運行交易工具。
"""

import pytest
import unittest
from unittest.mock import patch

from src.server import mcp


class TestServerIntegration(unittest.TestCase):
    """MCP 服務器整合測試類別。"""

    def setUp(self):
        """設置測試環境。"""
        # No need to instantiate MCPServer, just ensure mcp is available
        pass

    @pytest.mark.asyncio
    async def test_trading_tools_registered(self):
        """測試交易工具是否正確註冊。"""
        # 取得所有工具定義
        all_tool_defs = [tool for tool in await mcp.get_tools()]

        # 過濾出交易工具
        trading_defs = [
            tool_def
            for tool_def in all_tool_defs
            if tool_def.name in ["buy_taiwan_stock", "sell_taiwan_stock"]
        ]

        # 驗證有兩個交易工具
        self.assertEqual(len(trading_defs), 2)

        # 驗證工具名稱
        tool_names = [tool_def.name for tool_def in trading_defs]
        self.assertIn("buy_taiwan_stock", tool_names)
        self.assertIn("sell_taiwan_stock", tool_names)

        # 驗證工具定義格式
        for tool_def in trading_defs:
            self.assertIn("name", tool_def)
            self.assertIn("description", tool_def)
            self.assertIn("inputSchema", tool_def.get_definition())
            self.assertIn("properties", tool_def.get_definition()["inputSchema"])
            self.assertIn("required", tool_def.get_definition()["inputSchema"])

            # 檢查必要參數
            required_fields = tool_def.get_definition()["inputSchema"]["required"]
            self.assertIn("symbol", required_fields)
            self.assertIn("quantity", required_fields) # Changed from price to quantity

    def test_server_initialization(self):
        """測試服務器初始化。"""
        # 驗證 mcp 對象已創建
        self.assertIsNotNone(mcp)
        self.assertEqual(mcp.name, "casual-market-mcp")


if __name__ == "__main__":
    unittest.main()
