"""
新架構的 MCP Server - 完全重構版本
使用統一的工具模組架構和 Python 3.12+ 語法
"""

from fastmcp import FastMCP

# 新架構工具導入
from .tools.trading import StockPriceTool, StockTradingTool, DailyTradingTool
from .tools.financial import (
    FinancialStatementsTool,
    CompanyProfileTool,
    DividendTool,
    RevenueTool,
    ValuationTool,
)

# API 客戶端導入
from .api.twse_client import create_client

# 設置日誌
from .utils.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

# 創建 FastMCP 實例
mcp = FastMCP(name="casual-market-mcp")

# 創建工具實例
stock_price_tool = StockPriceTool()
stock_trading_tool = StockTradingTool()
daily_trading_tool = DailyTradingTool()
financial_statements_tool = FinancialStatementsTool()
company_profile_tool = CompanyProfileTool()
dividend_tool = DividendTool()
revenue_tool = RevenueTool()
valuation_tool = ValuationTool()

# 創建 API 客戶端實例
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


# === 市場資訊工具 ===


@mcp.tool
async def get_margin_trading_info():
    """取得融資融券資訊。"""
    try:
        logger.info("查詢融資融券資訊")
        data = await api_client.get_data("/exchangeReport/MI_MARGN")

        if not data:
            return {
                "success": False,
                "error": "No margin trading data available",
                "data": None,
            }

        # 限制前10筆避免資料過多
        top_10 = data[:10] if len(data) > 10 else data

        result = {
            "success": True,
            "data": {
                "margin_data": top_10,
                "total_count": len(data),
                "displayed_count": len(top_10),
            },
            "source": "TWSE Margin Trading Report",
        }

        logger.info(f"成功取得融資融券資料: {len(top_10)} 筆")
        return result

    except Exception as e:
        logger.error(f"查詢融資融券資料失敗: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool
async def get_real_time_trading_stats():
    """取得即時交易統計資訊（5分鐘資料）。"""
    try:
        logger.info("查詢即時交易統計")
        data = await api_client.get_latest_market_data(
            "/exchangeReport/MI_5MINS", count=10
        )

        if not data:
            return {
                "success": False,
                "error": "No real-time trading stats available",
                "data": None,
            }

        result = {
            "success": True,
            "data": {
                "trading_stats": data,
                "count": len(data),
                "frequency": "5_minutes",
            },
            "source": "TWSE Real-time Trading Statistics",
        }

        logger.info(f"成功取得即時交易統計: {len(data)} 筆")
        return result

    except Exception as e:
        logger.error(f"查詢即時交易統計失敗: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool
async def get_dividend_rights_schedule(symbol: str = ""):
    """取得除權息行事曆。"""
    try:
        logger.info(f"查詢除權息行事曆: {symbol or '全部'}")

        endpoint = "/exchangeReport/TWT48U_ALL"
        if symbol:
            # 查詢特定公司
            data = await api_client.get_company_data(endpoint, symbol)
            if not data:
                return {
                    "success": False,
                    "error": f"No dividend schedule found for {symbol}",
                    "data": None,
                }
            result_data = [data] if isinstance(data, dict) else data
        else:
            # 查詢全部
            data = await api_client.get_data(endpoint)
            if not data:
                return {
                    "success": False,
                    "error": "No dividend schedule data available",
                    "data": None,
                }
            # 限制前20筆避免資料過多
            result_data = data[:20] if len(data) > 20 else data

        result = {
            "success": True,
            "data": {
                "dividend_schedule": result_data,
                "query_symbol": symbol or "all",
                "total_count": len(data) if not symbol else 1,
                "displayed_count": len(result_data),
            },
            "source": "TWSE Exchange Report",
        }

        logger.info(f"成功取得除權息資料: {len(result_data)} 筆")
        return result

    except Exception as e:
        logger.error(f"查詢除權息資料失敗: {e}")
        return {"success": False, "error": str(e)}


# === 交易統計工具 ===


@mcp.tool
async def get_stock_monthly_trading(symbol: str):
    """取得股票月交易資訊。"""
    try:
        logger.info(f"查詢股票月交易資訊: {symbol}")
        endpoint = "/exchangeReport/FMSRFK_ALL"
        data = await api_client.get_company_data(endpoint, symbol)

        if not data:
            return {
                "success": False,
                "error": f"No monthly trading data found for {symbol}",
                "data": None,
            }

        result = {
            "success": True,
            "company_code": symbol,
            "data": data,
            "source": "TWSE Exchange Report",
        }

        logger.info(f"成功取得 {symbol} 月交易資料")
        return result

    except Exception as e:
        logger.error(f"查詢月交易資料失敗: {e}")
        return {"success": False, "error": str(e), "company_code": symbol}


@mcp.tool
async def get_stock_yearly_trading(symbol: str):
    """取得股票年交易資訊。"""
    try:
        logger.info(f"查詢股票年交易資訊: {symbol}")
        endpoint = "/exchangeReport/FMNPTK_ALL"
        data = await api_client.get_company_data(endpoint, symbol)

        if not data:
            return {
                "success": False,
                "error": f"No yearly trading data found for {symbol}",
                "data": None,
            }

        result = {
            "success": True,
            "company_code": symbol,
            "data": data,
            "source": "TWSE Exchange Report",
        }

        logger.info(f"成功取得 {symbol} 年交易資料")
        return result

    except Exception as e:
        logger.error(f"查詢年交易資料失敗: {e}")
        return {"success": False, "error": str(e), "company_code": symbol}


@mcp.tool
async def get_stock_monthly_average(symbol: str):
    """取得股票月平均價格。"""
    try:
        logger.info(f"查詢股票月平均價格: {symbol}")
        endpoint = "/exchangeReport/FMSRFK_ALL"
        data = await api_client.get_company_data(endpoint, symbol)

        if not data:
            return {
                "success": False,
                "error": f"No monthly average data found for {symbol}",
                "data": None,
            }

        result = {
            "success": True,
            "company_code": symbol,
            "data": data,
            "source": "TWSE Exchange Report",
        }

        logger.info(f"成功取得 {symbol} 月平均價格")
        return result

    except Exception as e:
        logger.error(f"查詢月平均價格失敗: {e}")
        return {"success": False, "error": str(e), "company_code": symbol}


# === 外資工具 ===


@mcp.tool
async def get_foreign_investment_by_industry():
    """取得外資持股(按產業別)。"""
    try:
        logger.info("查詢外資持股(按產業別)")
        endpoint = "/fund/MI_QFIIS_cat"
        data = await api_client.get_data(endpoint)

        if not data:
            return {
                "success": False,
                "error": "No foreign investment data by industry available",
                "data": None,
            }

        result = {
            "success": True,
            "data": {
                "industry_foreign_investment": data,
                "total_industries": len(data),
            },
            "source": "TWSE Fund Report",
        }

        logger.info(f"成功取得外資持股產業資料: {len(data)} 個產業")
        return result

    except Exception as e:
        logger.error(f"查詢外資持股產業資料失敗: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool
async def get_top_foreign_holdings():
    """取得外資持股前20名。"""
    try:
        logger.info("查詢外資持股前20名")
        endpoint = "/fund/MI_QFIIS_sort_20"
        data = await api_client.get_data(endpoint)

        if not data:
            return {
                "success": False,
                "error": "No top foreign holdings data available",
                "data": None,
            }

        result = {
            "success": True,
            "data": {
                "top_foreign_holdings": data,
                "count": len(data),
            },
            "source": "TWSE Fund Report",
        }

        logger.info(f"成功取得外資持股前20名: {len(data)} 筆")
        return result

    except Exception as e:
        logger.error(f"查詢外資持股前20名失敗: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool
async def get_market_historical_index():
    """取得歷史指數資料。"""
    try:
        logger.info("查詢歷史指數資料")
        endpoint = "/exchangeReport/MI_INDEX"
        data = await api_client.get_latest_market_data(endpoint)

        if not data:
            return {
                "success": False,
                "error": "No historical index data available",
                "data": None,
            }

        result = {
            "success": True,
            "data": {
                "historical_indices": data,
                "count": len(data),
            },
            "source": "TWSE Exchange Report",
        }

        logger.info(f"成功取得歷史指數資料: {len(data)} 筆")
        return result

    except Exception as e:
        logger.error(f"查詢歷史指數資料失敗: {e}")
        return {"success": False, "error": str(e)}


# === 其他市場工具 ===


@mcp.tool
async def get_etf_regular_investment_ranking():
    """取得ETF定期定額排名資訊（前10名）。"""
    try:
        logger.info("查詢ETF定期定額排名")
        data = await api_client.get_data("/ETFReport/ETFRank")

        if not data:
            return {
                "success": False,
                "error": "No ETF ranking data available",
                "data": None,
            }

        top_10 = data[:10] if len(data) > 10 else data

        return {
            "success": True,
            "data": {
                "ranking_date": None,
                "rankings": top_10,
                "total_count": len(data),
                "displayed_count": len(top_10),
            },
            "source": "TWSE ETF Report",
        }
    except Exception as e:
        logger.error(f"查詢ETF排名失敗: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool
async def get_market_index_info(
    category: str = "major", count: int = 20, format: str = "detailed"
):
    """取得市場指數資訊。"""
    try:
        logger.info(
            f"查詢市場指數: category={category}, count={count}, format={format}"
        )

        data = await api_client.get_latest_market_data("/exchangeReport/MI_INDEX")

        if not data:
            return {
                "success": False,
                "error": "No market index data available",
                "data": None,
            }

        # 根據類別篩選指數
        if category == "major":
            filtered_data = [
                item
                for item in data
                if not any(
                    pattern in item.get("指數", "")
                    for pattern in ["類指數", "報酬指數", "兩倍", "反向", "槓桿"]
                )
                and any(
                    pattern in item.get("指數", "")
                    for pattern in ["發行量加權", "寶島", "臺灣50", "中型", "小型"]
                )
            ]
        elif category == "sector":
            filtered_data = [
                item
                for item in data
                if "類指數" in item.get("指數", "")
                and "報酬指數" not in item.get("指數", "")
            ]
        else:
            filtered_data = data

        result_data = filtered_data[:count] if count > 0 else filtered_data

        return {
            "success": True,
            "data": {
                "category": category,
                "count": len(result_data),
                "format": format,
                "indices": result_data,
            },
            "source": "TWSE Market Index Report",
        }
    except Exception as e:
        logger.error(f"查詢市場指數失敗: {e}")
        return {"success": False, "error": str(e)}


def main():
    """主程式入口點"""
    logger.info("啟動新架構 Market MCP Server (FastMCP 模式)")
    mcp.run()


if __name__ == "__main__":
    main()
