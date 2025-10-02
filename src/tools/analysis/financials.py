"""
Financial analysis tools using TWSE OpenAPI integration.
Integrates with existing CasualTrader architecture for comprehensive financial analysis.
"""

from typing import Any

from ...api.openapi_client import OpenAPIClient
from ...cache.rate_limited_cache_service import RateLimitedCacheService
from ...utils.logging import get_logger

logger = get_logger(__name__)


class FinancialAnalysisTool:
    """
    Financial analysis tool with integrated caching and rate limiting.
    Provides comprehensive income statement and balance sheet analysis.
    """

    def __init__(self, cache_service: RateLimitedCacheService | None = None):
        """
        Initialize financial analysis tool.

        Args:
            cache_service: Optional cache service for rate limiting and caching
        """
        self.api_client = OpenAPIClient(cache_service)

    async def get_income_statement(self, code: str) -> dict[str, Any]:
        """
        Get comprehensive income statement for a listed company.
        Automatically detects company industry and uses appropriate format.

        Args:
            code: Company stock code

        Returns:
            Dictionary containing formatted income statement data
        """
        try:
            # Get industry-specific API suffix
            suffix = await self.api_client.get_industry_api_suffix(code)
            endpoint = f"/opendata/t187ap06_L{suffix}"

            logger.info(f"Fetching income statement for {code} using {suffix} format")

            # Fetch data using integrated cache and rate limiting
            data = await self.api_client.get_company_data(endpoint, code)

            if not data:
                return {
                    "success": False,
                    "error": f"No income statement data found for {code}",
                    "data": None,
                }

            # Format response for MCP tool compatibility
            formatted_data = self._format_financial_data(data, "income_statement")

            return {
                "success": True,
                "company_code": code,
                "statement_type": "綜合損益表",
                "industry_format": suffix,
                "data": formatted_data,
                "source": "TWSE OpenAPI",
            }

        except Exception as e:
            logger.error(f"Error fetching income statement for {code}: {e}")
            return {
                "success": False,
                "error": str(e),
                "company_code": code,
                "statement_type": "綜合損益表",
            }

    async def get_balance_sheet(self, code: str) -> dict[str, Any]:
        """
        Get balance sheet for a listed company.
        Automatically detects company industry and uses appropriate format.

        Args:
            code: Company stock code

        Returns:
            Dictionary containing formatted balance sheet data
        """
        try:
            # Get industry-specific API suffix
            suffix = await self.api_client.get_industry_api_suffix(code)
            endpoint = f"/opendata/t187ap07_L{suffix}"

            logger.info(f"Fetching balance sheet for {code} using {suffix} format")

            # Fetch data using integrated cache and rate limiting
            data = await self.api_client.get_company_data(endpoint, code)

            if not data:
                return {
                    "success": False,
                    "error": f"No balance sheet data found for {code}",
                    "data": None,
                }

            # Format response for MCP tool compatibility
            formatted_data = self._format_financial_data(data, "balance_sheet")

            return {
                "success": True,
                "company_code": code,
                "statement_type": "資產負債表",
                "industry_format": suffix,
                "data": formatted_data,
                "source": "TWSE OpenAPI",
            }

        except Exception as e:
            logger.error(f"Error fetching balance sheet for {code}: {e}")
            return {
                "success": False,
                "error": str(e),
                "company_code": code,
                "statement_type": "資產負債表",
            }

    async def get_company_profile(self, code: str) -> dict[str, Any]:
        """
        Get company basic profile information.

        Args:
            code: Company stock code

        Returns:
            Dictionary containing company profile data
        """
        try:
            endpoint = "/opendata/t187ap03_L"
            data = await self.api_client.get_company_data(endpoint, code)

            if not data:
                return {
                    "success": False,
                    "error": f"No company profile found for {code}",
                    "data": None,
                }

            return {
                "success": True,
                "company_code": code,
                "data": data,
                "source": "TWSE OpenAPI",
            }

        except Exception as e:
            logger.error(f"Error fetching company profile for {code}: {e}")
            return {"success": False, "error": str(e), "company_code": code}

    def _format_financial_data(
        self, data: dict[str, Any], statement_type: str
    ) -> dict[str, Any]:
        """
        Format financial data for consistent output.

        Args:
            data: Raw financial data from API
            statement_type: Type of financial statement

        Returns:
            Formatted financial data
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
        """Extract key metrics from income statement data."""
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
        """Extract key metrics from balance sheet data."""
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
        """Close the API client."""
        self.api_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
