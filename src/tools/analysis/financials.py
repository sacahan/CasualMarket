"""
財務分析工具，整合台灣證券交易所（TWSE）OpenAPI。
與現有 CasualTrader 架構整合，提供完整的財務分析。
"""

from typing import Any

from ...api.openapi_client import OpenAPIClient
from ...utils.logging import get_logger

logger = get_logger(__name__)


class FinancialAnalysisTool:
    """
    財務分析工具，使用 OpenAPIClient 內建的快取與速率限制。
    提供完整的綜合損益表與資產負債表分析。
    """

    def __init__(self):
        """
        初始化財務分析工具。

        使用 OpenAPIClient 的內建快取與速率限制功能。
        """
        self.api_client = OpenAPIClient()

    async def get_income_statement(self, symbol: str) -> dict[str, Any]:
        """
        取得上市公司完整綜合損益表。
        自動偵測公司所屬產業並使用相應格式。

        參數：
            symbol: 公司股票代碼

        回傳：
            包含格式化損益表資料的字典
        """
        try:
            # Get industry-specific API suffix
            suffix = await self.api_client.get_industry_api_suffix(symbol)
            endpoint = f"/opendata/t187ap06_L{suffix}"

            logger.info(f"Fetching income statement for {symbol} using {suffix} format")

            # Fetch data using integrated cache and rate limiting
            data = await self.api_client.get_company_data(endpoint, symbol)

            if not data:
                return {
                    "success": False,
                    "error": f"No income statement data found for {symbol}",
                    "data": None,
                }

            # Format response for MCP tool compatibility
            formatted_data = self._format_financial_data(data, "income_statement")

            return {
                "success": True,
                "company_code": symbol,
                "statement_type": "綜合損益表",
                "industry_format": suffix,
                "data": formatted_data,
                "source": "TWSE OpenAPI",
            }

        except Exception as e:
            logger.error(f"Error fetching income statement for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e),
                "company_code": symbol,
                "statement_type": "綜合損益表",
            }

    async def get_balance_sheet(self, symbol: str) -> dict[str, Any]:
        """
        取得上市公司資產負債表。
        自動偵測公司所屬產業並使用相應格式。

        參數：
            symbol: 公司股票代碼

        回傳：
            包含格式化資產負債表資料的字典
        """
        try:
            # Get industry-specific API suffix
            suffix = await self.api_client.get_industry_api_suffix(symbol)
            endpoint = f"/opendata/t187ap07_L{suffix}"

            logger.info(f"Fetching balance sheet for {symbol} using {suffix} format")

            # Fetch data using integrated cache and rate limiting
            data = await self.api_client.get_company_data(endpoint, symbol)

            if not data:
                return {
                    "success": False,
                    "error": f"No balance sheet data found for {symbol}",
                    "data": None,
                }

            # Format response for MCP tool compatibility
            formatted_data = self._format_financial_data(data, "balance_sheet")

            return {
                "success": True,
                "company_code": symbol,
                "statement_type": "資產負債表",
                "industry_format": suffix,
                "data": formatted_data,
                "source": "TWSE OpenAPI",
            }

        except Exception as e:
            logger.error(f"Error fetching balance sheet for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e),
                "company_code": symbol,
                "statement_type": "資產負債表",
            }

    async def get_company_profile(self, symbol: str) -> dict[str, Any]:
        """
        取得公司基本資料。

        參數：
            symbol: 公司股票代碼

        回傳：
            包含公司基本資料的字典
        """
        try:
            endpoint = "/opendata/t187ap03_L"
            data = await self.api_client.get_company_data(endpoint, symbol)

            if not data:
                return {
                    "success": False,
                    "error": f"No company profile found for {symbol}",
                    "data": None,
                }

            return {
                "success": True,
                "company_code": symbol,
                "data": data,
                "source": "TWSE OpenAPI",
            }

        except Exception as e:
            logger.error(f"Error fetching company profile for {symbol}: {e}")
            return {"success": False, "error": str(e), "company_code": symbol}

    async def get_company_dividend(self, symbol: str) -> dict[str, Any]:
        """
        取得公司股利分配資訊。

        參數：
            symbol: 公司股票代碼

        回傳：
            包含股利分配資訊的字典
        """
        try:
            endpoint = "/opendata/t187ap45_L"
            data = await self.api_client.get_company_data(endpoint, symbol)

            if not data:
                return {
                    "success": False,
                    "error": f"No dividend data found for {symbol}",
                    "data": None,
                }

            return {
                "success": True,
                "company_code": symbol,
                "data": data,
                "source": "TWSE OpenAPI",
            }

        except Exception as e:
            logger.error(f"Error fetching dividend info for {symbol}: {e}")
            return {"success": False, "error": str(e), "company_code": symbol}

    async def get_company_monthly_revenue(self, symbol: str) -> dict[str, Any]:
        """
        取得公司月營收資訊。

        參數：
            symbol: 公司股票代碼

        回傳：
            包含月營收資訊的字典
        """
        try:
            endpoint = "/opendata/t187ap05_L"
            data = await self.api_client.get_company_data(endpoint, symbol)

            if not data:
                return {
                    "success": False,
                    "error": f"No monthly revenue data found for {symbol}",
                    "data": None,
                }

            return {
                "success": True,
                "company_code": symbol,
                "data": data,
                "source": "TWSE OpenAPI",
            }

        except Exception as e:
            logger.error(f"Error fetching monthly revenue for {symbol}: {e}")
            return {"success": False, "error": str(e), "company_code": symbol}

    async def get_stock_valuation_ratios(self, symbol: str) -> dict[str, Any]:
        """
        取得股票估值比率 (P/E, P/B, 殖利率)。

        參數：
            symbol: 股票代碼

        回傳：
            包含估值比率資訊的字典
        """
        try:
            endpoint = "/exchangeReport/BWIBBU_ALL"
            data = await self.api_client.get_company_data(endpoint, symbol)

            if not data:
                return {
                    "success": False,
                    "error": f"No valuation ratios found for {symbol}",
                    "data": None,
                }

            return {
                "success": True,
                "company_code": symbol,
                "data": data,
                "source": "TWSE Exchange Report",
            }

        except Exception as e:
            logger.error(f"Error fetching valuation ratios for {symbol}: {e}")
            return {"success": False, "error": str(e), "company_code": symbol}

    def _format_financial_data(
        self, data: dict[str, Any], statement_type: str
    ) -> dict[str, Any]:
        """
        格式化財務資料，統一輸出格式。

        參數：
            data: 從 API 取得的原始財務資料
            statement_type: 財務報表類型

        回傳：
            格式化後的財務資料
        """
        try:
            # Extract key financial metrics based on statement type
            if statement_type == "income_statement":
                return self._extract_income_statement_metrics(data)
            elif statement_type == "balance_sheet":
                return self._extract_balance_sheet_metrics(data)
            else:
                return data

        except Exception as e:
            logger.warning(f"Error formatting financial data: {e}")
            return data

    def _extract_income_statement_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        從綜合損益表資料中擷取主要指標。
        """
        return {
            "raw_data": data,
            "key_metrics": {
                "revenue": data.get("營業收入", "N/A"),
                "operating_income": data.get("營業利益", "N/A"),
                "net_income": data.get("本期淨利", "N/A"),
                "earnings_per_share": data.get("基本每股盈餘", "N/A"),
            },
        }

    def _extract_balance_sheet_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        從資產負債表資料中擷取主要指標。
        """
        return {
            "raw_data": data,
            "key_metrics": {
                "total_assets": data.get("資產總額", "N/A"),
                "total_liabilities": data.get("負債總額", "N/A"),
                "stockholders_equity": data.get("股東權益總額", "N/A"),
                "book_value_per_share": data.get("每股淨值", "N/A"),
            },
        }

    def close(self):
        """
        關閉 API client。
        """
        self.api_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
