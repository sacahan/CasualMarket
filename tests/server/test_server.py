"""
Tests for the CasualTrader MCP Server basic functionality with FastMCP.

This module contains basic tests for the FastMCP server architecture
and tool registration.
"""

import pytest
from unittest.mock import patch, AsyncMock

# Import the mcp instance and the tool functions directly from src.server
from src.server import mcp, get_taiwan_stock_price, buy_taiwan_stock, sell_taiwan_stock


class TestFastMCPServer:
    """Test FastMCP Server basic functionality and tool registration."""

    @pytest.fixture(autouse=True)
    def mock_tool_dependencies(self):
        """Mock external dependencies for tools."""
        with (
            patch(
                "src.api.twse_client.create_client", return_value=AsyncMock()
            ) as mock_create_client,
            patch("src.securities_db.SecuritiesDatabase") as mock_securities_db,
        ):
            # Mock the stock_client for StockPriceTool and StockTradingTool
            mock_stock_client = AsyncMock()
            mock_stock_client.get_stock_quote.return_value = AsyncMock(
                symbol="2330",
                company_name="台積電",
                current_price=500.0,
                change=10.0,
                change_percent=0.02,
                volume=1000000,
                open_price=490.0,
                high_price=505.0,
                low_price=485.0,
                previous_close=490.0,
                upper_limit=539.0,
                lower_limit=441.0,
                bid_prices=[499.5, 499.0, 498.5, 498.0, 497.5],
                bid_volumes=[100, 200, 150, 300, 250],
                ask_prices=[500.0, 500.5, 501.0, 501.5, 502.0],
                ask_volumes=[150, 100, 200, 180, 220],
                update_time="2024-01-01T10:30:00",
                last_trade_time="10:30:00",
            )
            mock_create_client.return_value = mock_stock_client

            # Mock SecuritiesDatabase for company name resolution
            mock_db_instance = mock_securities_db.return_value
            mock_db_instance.find_by_company_name.return_value = [
                AsyncMock(stock_code="2330", company_name="台積電")
            ]
            mock_db_instance.find_by_stock_code.return_value = AsyncMock(
                stock_code="2330", company_name="台積電"
            )

            yield

    def test_mcp_instance_exists(self):
        """Test that the FastMCP instance 'mcp' exists."""
        assert mcp is not None
        assert mcp.name == "casual-market-mcp"

    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that expected tools are registered."""
        registered_tool_names = {tool for tool in await mcp.get_tools()}

        expected_tools = {
            "get_taiwan_stock_price",
            "buy_taiwan_stock",
            "sell_taiwan_stock",
            "get_stock_daily_trading",
            "get_company_income_statement",
            "get_company_balance_sheet",
            "get_company_profile",
            "get_company_dividend",
            "get_company_monthly_revenue",
            "get_stock_valuation_ratios",
            "get_dividend_rights_schedule",
            "get_stock_monthly_trading",
            "get_stock_yearly_trading",
            "get_stock_monthly_average",
            "get_margin_trading_info",
            "get_real_time_trading_stats",
            "get_etf_regular_investment_ranking",
            "get_market_index_info",
            "get_market_historical_index",
            "get_foreign_investment_by_industry",
            "get_top_foreign_holdings",
        }

        # Check if all expected tools are present
        missing_tools = expected_tools - registered_tool_names
        extra_tools = registered_tool_names - expected_tools

        assert not missing_tools, f"Missing expected tools: {missing_tools}"
        assert not extra_tools, f"Unexpected extra tools: {extra_tools}"

    @pytest.mark.asyncio
    async def test_get_taiwan_stock_price_functionality(self):
        """Test the functionality of get_taiwan_stock_price tool."""
        result = await get_taiwan_stock_price(symbol="2330")
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["type"] == "text"
        assert "台積電" in result[0]["text"]
        assert "500.0" in result[0]["text"]

    @pytest.mark.asyncio
    async def test_buy_taiwan_stock_functionality(self):
        """Test the functionality of buy_taiwan_stock tool."""
        # Assuming a successful buy scenario with price matching ask_prices
        result = await buy_taiwan_stock(symbol="2330", quantity=1000, price=500.0)
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["type"] == "text"
        assert "交易成功" in result[0]["text"]
        assert "500.0" in result[0]["text"]

    @pytest.mark.asyncio
    async def test_sell_taiwan_stock_functionality(self):
        """Test the functionality of sell_taiwan_stock tool."""
        # Assuming a successful sell scenario with price matching bid_prices
        result = await sell_taiwan_stock(symbol="2330", quantity=1000, price=499.5)
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["type"] == "text"
        assert "交易成功" in result[0]["text"]
        assert "499.5" in result[0]["text"]
