"""
簡化的 MCP Server 實作 - 使用 FastMCP 框架
使用 @mcp.tool() 裝飾器模式，大幅簡化架構
"""

from typing import Any

from fastmcp import FastMCP

from .api.twse_client import create_client
from .tools.analysis.financials import FinancialAnalysisTool
from .utils.logging import get_logger, setup_logging

# 設置日誌
setup_logging()
logger = get_logger(__name__)

# 創建 FastMCP 實例
mcp = FastMCP(name="casual-market-mcp")

# 全域 API 客戶端 (帶有速率限制和快取)
api_client = create_client()

# 創建財務分析工具實例（使用 OpenAPIClient 內建快取）
financial_tool = FinancialAnalysisTool()


@mcp.tool
async def get_taiwan_stock_price(symbol: str) -> dict[str, Any]:
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
    try:
        logger.info(f"查詢股票價格: {symbol}")

        # 呼叫 API 取得股票資料
        stock_data = await api_client.get_stock_quote(symbol)

        # 格式化回應
        result = {
            "status": "success",
            "data": {
                "symbol": stock_data.symbol,
                "name": stock_data.company_name,
                "price": stock_data.current_price,
                "change": stock_data.change,
                "change_percent": stock_data.change_percent,
                "volume": stock_data.volume,
                "high": stock_data.high_price,
                "low": stock_data.low_price,
                "open": stock_data.open_price,
                "previous_close": stock_data.previous_close,
                "last_update": (
                    stock_data.update_time.isoformat()
                    if stock_data.update_time
                    else None
                ),
            },
        }

        logger.info(f"成功取得 {symbol} 股票資料")
        return result

    except Exception as e:
        logger.error(f"查詢股票 {symbol} 失敗: {e}")
        return {"status": "error", "error": str(e), "symbol": symbol}


@mcp.tool
async def buy_taiwan_stock(
    symbol: str, quantity: int, price: float | None = None
) -> dict[str, Any]:
    """
    模擬台灣股票買入操作。

    Args:
        symbol: 股票代碼
        quantity: 購買股數 (台股最小單位為1000股)
        price: 指定價格 (可選，不指定則為市價)

    Returns:
        交易結果資訊
    """
    try:
        logger.info(f"模擬買入: {symbol} x {quantity} 股")

        # 驗證股數 (台股最小單位1000股)
        if quantity % 1000 != 0:
            return {"status": "error", "error": "台股交易最小單位為1000股"}

        # 取得目前股價作為參考
        stock_data = await api_client.get_stock_quote(symbol)
        current_price = stock_data.current_price

        # 如果未指定價格，使用當前價格（市價單）
        if price is None:
            # 市價單：立即以當前價格成交
            order_price = current_price
            total_amount = order_price * quantity
            order_type = "market"
            executed = True
            execution_message = "市價單立即成交"
        else:
            # 限價單：檢查是否符合成交條件
            order_price = price
            total_amount = order_price * quantity
            order_type = "limit"

            # 買入限價單：出價必須 >= 當前賣價才能成交
            if order_price >= current_price:
                executed = True
                execution_message = (
                    f"限價買單成交（出價 {order_price} >= 市價 {current_price}）"
                )
            else:
                executed = False
                execution_message = (
                    f"限價買單無法成交（出價 {order_price} < 市價 {current_price}）"
                )

        if executed:
            result = {
                "status": "success",
                "order": {
                    "action": "buy",
                    "symbol": symbol,
                    "name": stock_data.company_name,
                    "quantity": quantity,
                    "price": order_price,
                    "total_amount": total_amount,
                    "current_price": current_price,
                    "order_type": order_type,
                    "executed": True,
                    "message": execution_message,
                    "timestamp": (
                        stock_data.update_time.isoformat()
                        if stock_data.update_time
                        else None
                    ),
                },
            }
            logger.info(f"買入交易成功: {symbol} x {quantity} @ {order_price}")
        else:
            result = {
                "status": "failed",
                "order": {
                    "action": "buy",
                    "symbol": symbol,
                    "name": stock_data.company_name,
                    "quantity": quantity,
                    "price": order_price,
                    "current_price": current_price,
                    "order_type": order_type,
                    "executed": False,
                    "message": execution_message,
                    "reason": "出價低於市價，無法立即成交",
                },
            }
            logger.info(f"買入交易失敗: {symbol} - {execution_message}")

        return result

    except Exception as e:
        logger.error(f"買入操作失敗: {e}")
        return {"status": "error", "error": str(e), "symbol": symbol}


@mcp.tool
async def sell_taiwan_stock(
    symbol: str, quantity: int, price: float | None = None
) -> dict[str, Any]:
    """
    模擬台灣股票賣出操作。

    Args:
        symbol: 股票代碼
        quantity: 賣出股數 (台股最小單位為1000股)
        price: 指定價格 (可選，不指定則為市價)

    Returns:
        交易結果資訊
    """
    try:
        logger.info(f"模擬賣出: {symbol} x {quantity} 股")

        # 驗證股數 (台股最小單位1000股)
        if quantity % 1000 != 0:
            return {"status": "error", "error": "台股交易最小單位為1000股"}

        # 取得目前股價作為參考
        stock_data = await api_client.get_stock_quote(symbol)
        current_price = stock_data.current_price

        # 如果未指定價格，使用當前價格（市價單）
        if price is None:
            # 市價單：立即以當前價格成交
            order_price = current_price
            total_amount = order_price * quantity
            order_type = "market"
            executed = True
            execution_message = "市價單立即成交"
        else:
            # 限價單：檢查是否符合成交條件
            order_price = price
            total_amount = order_price * quantity
            order_type = "limit"

            # 賣出限價單：售價必須 <= 當前買價才能成交
            if order_price <= current_price:
                executed = True
                execution_message = (
                    f"限價賣單成交（售價 {order_price} <= 市價 {current_price}）"
                )
            else:
                executed = False
                execution_message = (
                    f"限價賣單無法成交（售價 {order_price} > 市價 {current_price}）"
                )

        if executed:
            result = {
                "status": "success",
                "order": {
                    "action": "sell",
                    "symbol": symbol,
                    "name": stock_data.company_name,
                    "quantity": quantity,
                    "price": order_price,
                    "total_amount": total_amount,
                    "current_price": current_price,
                    "order_type": order_type,
                    "executed": True,
                    "message": execution_message,
                    "timestamp": (
                        stock_data.update_time.isoformat()
                        if stock_data.update_time
                        else None
                    ),
                },
            }
            logger.info(f"賣出交易成功: {symbol} x {quantity} @ {order_price}")
        else:
            result = {
                "status": "failed",
                "order": {
                    "action": "sell",
                    "symbol": symbol,
                    "name": stock_data.company_name,
                    "quantity": quantity,
                    "price": order_price,
                    "current_price": current_price,
                    "order_type": order_type,
                    "executed": False,
                    "message": execution_message,
                    "reason": "售價高於市價，無法立即成交",
                },
            }
            logger.info(f"賣出交易失敗: {symbol} - {execution_message}")

        return result

    except Exception as e:
        logger.error(f"賣出操作失敗: {e}")
        return {"status": "error", "error": str(e), "symbol": symbol}


@mcp.tool
async def get_company_income_statement(symbol: str) -> dict[str, Any]:
    """
    取得上市公司綜合損益表。

    自動偵測公司所屬行業並使用相應的財務報表格式：
    - 一般業、金融業、證券期貨業、金控業、保險業、異業

    Args:
        symbol: 公司股票代碼

    Returns:
        包含綜合損益表資訊的字典
    """
    try:
        logger.info(f"查詢公司損益表: {symbol}")

        result = await financial_tool.get_income_statement(symbol)

        if result["success"]:
            logger.info(f"成功取得 {symbol} 損益表資料")
        else:
            logger.warning(
                f"無法取得 {symbol} 損益表: {result.get('error', 'Unknown error')}"
            )

        return result

    except Exception as e:
        logger.error(f"查詢損益表失敗: {e}")
        return {
            "success": False,
            "error": str(e),
            "company_code": symbol,
            "statement_type": "綜合損益表",
        }


@mcp.tool
async def get_company_balance_sheet(symbol: str) -> dict[str, Any]:
    """
    取得上市公司資產負債表。

    自動偵測公司所屬行業並使用相應的財務報表格式：
    - 一般業、金融業、證券期貨業、金控業、保險業、異業

    Args:
        symbol: 公司股票代碼

    Returns:
        包含資產負債表資訊的字典
    """
    try:
        logger.info(f"查詢公司資產負債表: {symbol}")

        result = await financial_tool.get_balance_sheet(symbol)

        if result["success"]:
            logger.info(f"成功取得 {symbol} 資產負債表資料")
        else:
            logger.warning(
                f"無法取得 {symbol} 資產負債表: {result.get('error', 'Unknown error')}"
            )

        return result

    except Exception as e:
        logger.error(f"查詢資產負債表失敗: {e}")
        return {
            "success": False,
            "error": str(e),
            "company_code": symbol,
            "statement_type": "資產負債表",
        }


@mcp.tool
async def get_company_profile(symbol: str) -> dict[str, Any]:
    """
    取得上市公司基本資訊。

    Args:
        symbol: 公司股票代碼

    Returns:
        包含公司基本資訊的字典
    """
    try:
        logger.info(f"查詢公司基本資訊: {symbol}")

        result = await financial_tool.get_company_profile(symbol)

        if result["success"]:
            logger.info(f"成功取得 {symbol} 基本資訊")
        else:
            logger.warning(
                f"無法取得 {symbol} 基本資訊: {result.get('error', 'Unknown error')}"
            )

        return result

    except Exception as e:
        logger.error(f"查詢公司基本資訊失敗: {e}")
        return {"success": False, "error": str(e), "company_code": symbol}


@mcp.tool
async def get_company_dividend(symbol: str) -> dict[str, Any]:
    """
    取得上市公司股利分配資訊。

    Args:
        symbol: 公司股票代碼

    Returns:
        包含股利分配資訊的字典
    """
    try:
        logger.info(f"查詢公司股利資訊: {symbol}")

        result = await financial_tool.get_company_dividend(symbol)

        if result["success"]:
            logger.info(f"成功取得 {symbol} 股利資訊")
        else:
            logger.warning(
                f"無法取得 {symbol} 股利資訊: {result.get('error', 'Unknown error')}"
            )

        return result

    except Exception as e:
        logger.error(f"查詢股利資訊失敗: {e}")
        return {"success": False, "error": str(e), "company_code": symbol}


@mcp.tool
async def get_company_monthly_revenue(symbol: str) -> dict[str, Any]:
    """
    取得上市公司月營收資訊。

    Args:
        symbol: 公司股票代碼

    Returns:
        包含月營收資訊的字典
    """
    try:
        logger.info(f"查詢公司月營收: {symbol}")

        result = await financial_tool.get_company_monthly_revenue(symbol)

        if result["success"]:
            logger.info(f"成功取得 {symbol} 月營收資料")
        else:
            logger.warning(
                f"無法取得 {symbol} 月營收: {result.get('error', 'Unknown error')}"
            )

        return result

    except Exception as e:
        logger.error(f"查詢月營收失敗: {e}")
        return {"success": False, "error": str(e), "company_code": symbol}


@mcp.tool
async def get_stock_daily_trading(symbol: str) -> dict[str, Any]:
    """
    取得股票日交易資訊。

    Args:
        symbol: 股票代碼

    Returns:
        包含日交易資訊的字典
    """
    try:
        logger.info(f"查詢股票日交易資訊: {symbol}")

        # 使用現有的 API 客戶端但針對日交易資料
        stock_data = await api_client.get_stock_quote(symbol)

        # 格式化日交易資料
        result = {
            "success": True,
            "symbol": symbol,
            "data": {
                "trading_date": (
                    stock_data.update_time.strftime("%Y-%m-%d")
                    if stock_data.update_time
                    else None
                ),
                "open_price": stock_data.open_price,
                "high_price": stock_data.high_price,
                "low_price": stock_data.low_price,
                "close_price": stock_data.current_price,
                "volume": stock_data.volume,
                "change": stock_data.change,
                "change_percent": stock_data.change_percent,
                "previous_close": stock_data.previous_close,
            },
        }

        logger.info(f"成功取得 {symbol} 日交易資料")
        return result

    except Exception as e:
        logger.error(f"查詢日交易資料失敗: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@mcp.tool
async def get_etf_regular_investment_ranking() -> dict[str, Any]:
    """
    取得ETF定期定額排名資訊（前10名）。

    Returns:
        包含ETF定期定額排名的字典
    """
    try:
        logger.info("查詢ETF定期定額排名")

        # 使用 OpenAPI 客戶端取得 ETF 排名資料
        data = await financial_tool.api_client.get_data("/ETFReport/ETFRank")

        if not data:
            return {
                "success": False,
                "error": "No ETF ranking data available",
                "data": None,
            }

        # 限制前10名並格式化資料
        top_10 = data[:10] if len(data) > 10 else data

        result = {
            "success": True,
            "data": {
                "ranking_date": None,  # API 資料中可能包含日期
                "rankings": top_10,
                "total_count": len(data),
                "displayed_count": len(top_10),
            },
            "source": "TWSE ETF Report",
        }

        logger.info("成功取得ETF定期定額排名")
        return result

    except Exception as e:
        logger.error(f"查詢ETF排名失敗: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool
async def get_market_index_info(
    category: str = "major", count: int = 20, format: str = "detailed"
) -> dict[str, Any]:
    """
    取得市場指數資訊。

    Args:
        category: 指數類別 ("major"=主要指數, "sector"=產業指數, "all"=全部)
        count: 返回數量 (預設20筆)
        format: 格式 ("detailed"=詳細, "summary"=摘要, "simple"=簡單)

    Returns:
        包含市場指數資訊的字典
    """
    try:
        logger.info(
            f"查詢市場指數: category={category}, count={count}, format={format}"
        )

        # 使用 OpenAPI 客戶端取得市場指數資料
        data = await financial_tool.api_client.get_latest_market_data(
            "/exchangeReport/MI_INDEX"
        )

        if not data:
            return {
                "success": False,
                "error": "No market index data available",
                "data": None,
            }

        # 根據類別篩選指數
        filtered_data = []
        if category == "major":
            # 主要指數：核心市場基準
            filtered_data = [
                item
                for item in data
                if not any(
                    pattern in item.get("指數", "")
                    for pattern in ["類指數", "報酬指數", "兩倍", "反向", "槓桿"]
                )
                and any(
                    pattern in item.get("指數", "")
                    for pattern in [
                        "發行量加權",
                        "寶島",
                        "臺灣50",
                        "中型",
                        "小型",
                        "未含",
                        "公司治理",
                        "高股息",
                    ]
                )
            ]
        elif category == "sector":
            # 產業指數
            filtered_data = [
                item
                for item in data
                if "類指數" in item.get("指數", "")
                and "報酬指數" not in item.get("指數", "")
            ]
        else:  # category == "all" or other
            filtered_data = data

        # 限制數量
        result_data = filtered_data[:count] if count > 0 else filtered_data

        # 根據格式格式化輸出
        formatted_data = result_data
        if format == "summary":
            formatted_data = [
                {
                    "name": item.get("指數", ""),
                    "close": item.get("收盤指數", ""),
                    "change_percent": item.get("漲跌百分比", ""),
                    "direction": item.get("漲跌", ""),
                }
                for item in result_data
            ]
        elif format == "simple":
            formatted_data = [
                f"{item.get('指數', '')}: {item.get('漲跌', '')}{item.get('漲跌百分比', '')}%"
                for item in result_data
            ]

        result = {
            "success": True,
            "data": {
                "category": category,
                "count": len(formatted_data),
                "format": format,
                "indices": formatted_data,
            },
            "source": "TWSE Market Index Report",
        }

        logger.info(f"成功取得 {len(formatted_data)} 筆市場指數資料")
        return result

    except Exception as e:
        logger.error(f"查詢市場指數失敗: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool
async def get_margin_trading_info() -> dict[str, Any]:
    """
    取得融資融券資訊。

    Returns:
        包含融資融券資訊的字典
    """
    try:
        logger.info("查詢融資融券資訊")

        # 使用 OpenAPI 客戶端取得融資融券資料
        data = await financial_tool.api_client.get_data("/exchangeReport/MI_MARGN")

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
async def get_real_time_trading_stats() -> dict[str, Any]:
    """
    取得即時交易統計資訊（5分鐘資料）。

    Returns:
        包含即時交易統計的字典
    """
    try:
        logger.info("查詢即時交易統計")

        # 使用 OpenAPI 客戶端取得即時交易統計
        data = await financial_tool.api_client.get_latest_market_data(
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
async def get_stock_valuation_ratios(symbol: str) -> dict[str, Any]:
    """
    取得股票估值比率 (P/E, P/B, 殖利率)。

    Args:
        symbol: 股票代碼

    Returns:
        包含估值比率的字典
    """
    try:
        logger.info(f"查詢股票估值比率: {symbol}")

        result = await financial_tool.get_stock_valuation_ratios(symbol)

        if result["success"]:
            logger.info(f"成功取得 {symbol} 估值比率資料")
        else:
            logger.warning(
                f"無法取得 {symbol} 估值比率: {result.get('error', 'Unknown error')}"
            )

        return result

    except Exception as e:
        logger.error(f"查詢估值比率失敗: {e}")
        return {"success": False, "error": str(e), "company_code": symbol}


@mcp.tool
async def get_dividend_rights_schedule(symbol: str = "") -> dict[str, Any]:
    """
    取得除權息行事曆。

    Args:
        symbol: 股票代碼 (可選，空字串則查詢全部)

    Returns:
        包含除權息行事曆的字典
    """
    try:
        logger.info(f"查詢除權息行事曆: {symbol or '全部'}")

        endpoint = "/exchangeReport/TWT48U_ALL"
        if symbol:
            # 查詢特定公司
            data = await financial_tool.api_client.get_company_data(endpoint, symbol)
            if not data:
                return {
                    "success": False,
                    "error": f"No dividend schedule found for {symbol}",
                    "data": None,
                }
            result_data = [data] if isinstance(data, dict) else data
        else:
            # 查詢全部
            data = await financial_tool.api_client.get_data(endpoint)
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
        logger.error(f"查詢除權息行事曆失敗: {e}")
        return {"success": False, "error": str(e), "query_symbol": symbol}


@mcp.tool
async def get_stock_monthly_trading(symbol: str) -> dict[str, Any]:
    """
    取得股票月交易資訊。

    Args:
        symbol: 股票代碼

    Returns:
        包含月交易資訊的字典
    """
    try:
        logger.info(f"查詢股票月交易資訊: {symbol}")

        endpoint = "/exchangeReport/FMSRFK_ALL"
        data = await financial_tool.api_client.get_company_data(endpoint, symbol)

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
async def get_stock_yearly_trading(symbol: str) -> dict[str, Any]:
    """
    取得股票年交易資訊。

    Args:
        symbol: 股票代碼

    Returns:
        包含年交易資訊的字典
    """
    try:
        logger.info(f"查詢股票年交易資訊: {symbol}")

        endpoint = "/exchangeReport/FMNPTK_ALL"
        data = await financial_tool.api_client.get_company_data(endpoint, symbol)

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
async def get_stock_monthly_average(symbol: str) -> dict[str, Any]:
    """
    取得股票月平均價格。

    Args:
        symbol: 股票代碼

    Returns:
        包含月平均價格的字典
    """
    try:
        logger.info(f"查詢股票月平均價格: {symbol}")

        endpoint = "/exchangeReport/STOCK_DAY_AVG_ALL"
        data = await financial_tool.api_client.get_company_data(endpoint, symbol)

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

        logger.info(f"成功取得 {symbol} 月平均價格資料")
        return result

    except Exception as e:
        logger.error(f"查詢月平均價格失敗: {e}")
        return {"success": False, "error": str(e), "company_code": symbol}


@mcp.tool
async def get_foreign_investment_by_industry() -> dict[str, Any]:
    """
    取得外資持股(按產業別)。

    Returns:
        包含各產業外資持股比率統計的字典
    """
    try:
        logger.info("查詢外資持股(按產業別)")

        endpoint = "/fund/MI_QFIIS_cat"
        data = await financial_tool.api_client.get_data(endpoint)

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
async def get_top_foreign_holdings() -> dict[str, Any]:
    """
    取得外資持股前20名。

    Returns:
        包含外資持股排名前20的公司詳細資訊的字典
    """
    try:
        logger.info("查詢外資持股前20名")

        endpoint = "/fund/MI_QFIIS_sort_20"
        data = await financial_tool.api_client.get_data(endpoint)

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
async def get_market_historical_index() -> dict[str, Any]:
    """
    取得歷史指數資料。

    Returns:
        包含TAIEX歷史資料的字典
    """
    try:
        logger.info("查詢歷史指數資料")

        endpoint = "/indicesReport/MI_5MINS_HIST"
        data = await financial_tool.api_client.get_latest_market_data(
            endpoint, count=20
        )

        if not data:
            return {
                "success": False,
                "error": "No historical index data available",
                "data": None,
            }

        result = {
            "success": True,
            "data": {
                "historical_index": data,
                "count": len(data),
            },
            "source": "TWSE Indices Report",
        }

        logger.info(f"成功取得歷史指數資料: {len(data)} 筆")
        return result

    except Exception as e:
        logger.error(f"查詢歷史指數資料失敗: {e}")
        return {"success": False, "error": str(e)}


def main() -> None:
    """主程式入口點"""
    logger.info("啟動 Market MCP Server (FastMCP 模式)")

    # 啟動 FastMCP 伺服器
    mcp.run()


if __name__ == "__main__":
    main()
