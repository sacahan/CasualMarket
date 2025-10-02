"""
新架構的 MCP Server - 完全模組化版本
使用統一的工具模組架構和 Python 3.12+ 語法
"""

from fastmcp import FastMCP

# API 客戶端導入
from .api.twse_client import create_client
from .tools.financial import (
    CompanyProfileTool,
    DividendScheduleTool,
    DividendTool,
    FinancialStatementsTool,
    RevenueTool,
    ValuationTool,
)
from .tools.foreign import ForeignInvestmentTool
from .tools.market import (
    ETFRankingTool,
    HistoricalIndexTool,
    IndexInfoTool,
    MarginTradingTool,
    TradingStatsTool,
)

# 新架構工具導入
from .tools.trading import (
    DailyTradingTool,
    StockPriceTool,
    StockTradingTool,
    TradingStatisticsTool,
)

# 設置日誌
from .utils.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

# 創建 FastMCP 實例
mcp = FastMCP(name="casual-market-mcp")

# 創建工具實例 - 交易相關
stock_price_tool = StockPriceTool()
stock_trading_tool = StockTradingTool()
daily_trading_tool = DailyTradingTool()
trading_statistics_tool = TradingStatisticsTool()

# 創建工具實例 - 財務相關
financial_statements_tool = FinancialStatementsTool()
company_profile_tool = CompanyProfileTool()
dividend_tool = DividendTool()
revenue_tool = RevenueTool()
valuation_tool = ValuationTool()
dividend_schedule_tool = DividendScheduleTool()

# 創建工具實例 - 市場相關
margin_trading_tool = MarginTradingTool()
trading_stats_tool = TradingStatsTool()
etf_ranking_tool = ETFRankingTool()
index_info_tool = IndexInfoTool()
historical_index_tool = HistoricalIndexTool()

# 創建工具實例 - 外資相關
foreign_investment_tool = ForeignInvestmentTool()

# 創建 API 客戶端實例（用於剩餘未重構的工具）
api_client = create_client()


# === 交易相關工具 ===


@mcp.tool
async def get_taiwan_stock_price(symbol: str):
    """
    取得台灣股票即時價格資訊。

    支援股票代碼或公司名稱查詢：
    - 股票代碼: 4-6位數字 + 可選字母 (例如: 2330, 0050, 00648R)
    - 公司名稱: 完整或部分公司名稱 (例如: "台積電", "鴻海")

    Args:
        symbol: 台灣股票代號或公司名稱

    Returns:
        包含股票價格資訊的字典
    """
    return await stock_price_tool.safe_execute(symbol=symbol)


@mcp.tool
async def buy_taiwan_stock(symbol: str, quantity: int, price: float | None = None):
    """
    模擬台灣股票買入操作。

    Args:
        symbol: 股票代碼
        quantity: 購買股數 (台股最小單位為1000股)
        price: 指定價格 (可選，不指定則為市價)

    Returns:
        交易結果資訊
    """
    return await stock_trading_tool.buy(symbol=symbol, quantity=quantity, price=price)


@mcp.tool
async def sell_taiwan_stock(symbol: str, quantity: int, price: float | None = None):
    """
    模擬台灣股票賣出操作。

    Args:
        symbol: 股票代碼
        quantity: 賣出股數 (台股最小單位為1000股)
        price: 指定價格 (可選，不指定則為市價)

    Returns:
        交易結果資訊
    """
    return await stock_trading_tool.sell(symbol=symbol, quantity=quantity, price=price)


@mcp.tool
async def get_stock_daily_trading(symbol: str):
    """
    取得股票日交易資訊。

    Args:
        symbol: 股票代碼

    Returns:
        包含日交易資訊的字典
    """
    return await daily_trading_tool.safe_execute(symbol=symbol)


# === 財務分析工具 ===


@mcp.tool
async def get_company_income_statement(symbol: str):
    """
    取得上市公司綜合損益表。

    自動偵測公司所屬行業並使用相應的財務報表格式：
    - 一般業、金融業、證券期貨業、金控業、保險業、異業

    Args:
        symbol: 公司股票代碼

    Returns:
        包含綜合損益表資訊的字典
    """
    return await financial_statements_tool.get_income_statement(symbol)


@mcp.tool
async def get_company_balance_sheet(symbol: str):
    """
    取得上市公司資產負債表。

    自動偵測公司所屬行業並使用相應的財務報表格式：
    - 一般業、金融業、證券期貨業、金控業、保險業、異業

    Args:
        symbol: 公司股票代碼

    Returns:
        包含資產負債表資訊的字典
    """
    return await financial_statements_tool.get_balance_sheet(symbol)


@mcp.tool
async def get_company_profile(symbol: str):
    """
    取得上市公司基本資訊。

    Args:
        symbol: 公司股票代碼

    Returns:
        包含公司基本資訊的字典
    """
    return await company_profile_tool.safe_execute(symbol=symbol)


@mcp.tool
async def get_company_dividend(symbol: str):
    """
    取得公司股利分配資訊。

    Args:
        symbol: 公司股票代碼

    Returns:
        包含股利分配資訊的字典
    """
    return await dividend_tool.safe_execute(symbol=symbol)


@mcp.tool
async def get_company_monthly_revenue(symbol: str):
    """
    取得公司月營收資訊。

    Args:
        symbol: 公司股票代碼

    Returns:
        包含月營收資訊的字典
    """
    return await revenue_tool.safe_execute(symbol=symbol)


@mcp.tool
async def get_stock_valuation_ratios(symbol: str):
    """
    取得股票估值比率 (P/E, P/B, 殖利率)。

    Args:
        symbol: 股票代碼

    Returns:
        包含估值比率的字典
    """
    return await valuation_tool.safe_execute(symbol=symbol)


@mcp.tool
async def get_dividend_rights_schedule(symbol: str = ""):
    """
    取得除權息行事曆。

    Args:
        symbol: 股票代碼 (可選，空字串則查詢全部)

    Returns:
        包含除權息行事曆的字典
    """
    return await dividend_schedule_tool.safe_execute(symbol=symbol)


# === 交易統計工具 ===


@mcp.tool
async def get_stock_monthly_trading(symbol: str):
    """
    取得股票月交易資訊。

    Args:
        symbol: 股票代碼

    Returns:
        包含月交易資訊的字典
    """
    return await trading_statistics_tool.get_monthly_trading(symbol)


@mcp.tool
async def get_stock_yearly_trading(symbol: str):
    """
    取得股票年交易資訊。

    Args:
        symbol: 股票代碼

    Returns:
        包含年交易資訊的字典
    """
    return await trading_statistics_tool.get_yearly_trading(symbol)


@mcp.tool
async def get_stock_monthly_average(symbol: str):
    """
    取得股票月平均價格。

    Args:
        symbol: 股票代碼

    Returns:
        包含月平均價格的字典
    """
    return await trading_statistics_tool.get_monthly_average(symbol)


# === 市場資訊工具 ===


@mcp.tool
async def get_margin_trading_info():
    """取得融資融券資訊。"""
    return await margin_trading_tool.safe_execute()


@mcp.tool
async def get_real_time_trading_stats():
    """取得即時交易統計資訊（5分鐘資料）。"""
    return await trading_stats_tool.safe_execute()


@mcp.tool
async def get_etf_regular_investment_ranking():
    """取得ETF定期定額排名資訊（前10名）。"""
    return await etf_ranking_tool.safe_execute()


@mcp.tool
async def get_market_index_info(
    category: str = "major", count: int = 20, format: str = "detailed"
):
    """取得市場指數資訊。"""
    return await index_info_tool.safe_execute(
        category=category, count=count, format=format
    )


@mcp.tool
async def get_market_historical_index():
    """取得歷史指數資料。"""
    return await historical_index_tool.safe_execute()


# === 外資工具 ===


@mcp.tool
async def get_foreign_investment_by_industry():
    """取得外資持股(按產業別)。"""
    return await foreign_investment_tool.get_investment_by_industry()


@mcp.tool
async def get_top_foreign_holdings():
    """取得外資持股前20名。"""
    return await foreign_investment_tool.get_top_holdings()


def main():
    """主程式入口點"""
    logger.info("啟動新架構 Market MCP Server (FastMCP 模式)")
    mcp.run()


if __name__ == "__main__":
    main()
