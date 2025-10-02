"""
TWSE OpenAPI Client with integrated caching and rate limiting.
Extends the existing enhanced architecture for comprehensive TWSE data access.
"""

from typing import Any

import httpx

from ..cache.rate_limited_cache_service import RateLimitedCacheService
from ..utils.logging import get_logger

logger = get_logger(__name__)


class OpenAPIClient:
    """
    TWSE OpenAPI client with integrated caching and rate limiting.
    Works with the enhanced TWStockAPIClient architecture.
    """

    BASE_URL = "https://openapi.twse.com.tw/v1"
    USER_AGENT = "CasualTrader-MCP/2.0"

    def __init__(self, cache_service: RateLimitedCacheService | None = None):
        """
        Initialize OpenAPI client with cache service.

        Args:
            cache_service: Optional cache service for rate limiting and caching
        """
        logger.debug("初始化 OpenAPIClient")

        self.cache_service = cache_service or RateLimitedCacheService()
        self.session = httpx.Client(
            headers={"User-Agent": self.USER_AGENT, "Accept": "application/json"},
            timeout=30.0,
            verify=False,  # SSL verification bypass for TWSE compatibility
        )

        logger.info(f"OpenAPIClient 初始化完成，基礎 URL: {self.BASE_URL}")
        logger.debug(
            f"HTTP Client 設定: User-Agent={self.USER_AGENT}, timeout=30.0s, verify=False"
        )

    async def get_data(self, endpoint: str) -> list[dict[str, Any]]:
        """
        Fetch data from TWSE OpenAPI endpoint with caching and rate limiting.

        Args:
            endpoint: API endpoint path (e.g., "/opendata/t187ap03_L")

        Returns:
            List of dictionaries containing API response data
        """
        cache_key = f"openapi:{endpoint}"
        logger.info(f"開始請求 OpenAPI 資料: {endpoint}")

        # Use integrated cache service if available
        if self.cache_service:
            logger.debug("使用快取服務處理請求")
            try:

                async def fetch_func():
                    url = f"{self.BASE_URL}{endpoint}"
                    logger.debug(f"從 OpenAPI 取得資料: {url}")

                    response = self.session.get(url)
                    response.raise_for_status()

                    # Ensure UTF-8 encoding
                    response.encoding = "utf-8"
                    data = response.json()

                    logger.debug(f"OpenAPI 回應成功，資料類型: {type(data)}")
                    # Normalize response format
                    result = data if isinstance(data, list) else [data] if data else []
                    logger.debug(f"正規化後資料數量: {len(result)}")
                    return result

                # Use the integrated cache and rate limiting service
                result = await self.cache_service.get_cached_or_wait(
                    symbol=cache_key, fetch_func=fetch_func
                )
                logger.info(f"OpenAPI 請求完成: {endpoint}，取得 {len(result)} 筆資料")
                return result

            except Exception as e:
                logger.error(f"快取服務錯誤: {e}")
                logger.warning("回退到直接請求模式")
                # Fall back to direct fetch
                pass

        # Direct fetch without cache (fallback)
        url = f"{self.BASE_URL}{endpoint}"
        logger.info(f"直接請求 OpenAPI 資料: {url} (無快取)")

        try:
            response = self.session.get(url)
            response.raise_for_status()

            # Ensure UTF-8 encoding
            response.encoding = "utf-8"
            data = response.json()

            logger.debug(f"直接請求成功，狀態碼: {response.status_code}")
            # Normalize response format
            result = data if isinstance(data, list) else [data] if data else []
            logger.info(f"OpenAPI 直接請求完成: {endpoint}，取得 {len(result)} 筆資料")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 狀態錯誤: {url} - {e.response.status_code}: {e}")
            raise Exception(f"API request failed: {e}") from e
        except Exception as e:
            logger.error(f"請求失敗: {url} - {type(e).__name__}: {e}")
            raise Exception(f"Failed to fetch data: {e}") from e

    async def get_company_data(self, endpoint: str, code: str) -> dict[str, Any] | None:
        """
        Fetch company-specific data from TWSE OpenAPI.

        Args:
            endpoint: API endpoint path
            code: Company stock code

        Returns:
            Dictionary containing company data or None if not found
        """
        try:
            data = await self.get_data(endpoint)

            # Filter data by company code
            filtered_data = [
                item
                for item in data
                if isinstance(item, dict)
                and (
                    item.get("公司代號") == code
                    or item.get("Code") == code
                    or item.get("證券代號") == code
                )
            ]

            result = filtered_data[0] if filtered_data else None
            logger.debug(
                f"Company data for {code}: {'found' if result else 'not found'}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to fetch company data for {code}: {e}")
            return None

    async def get_latest_market_data(
        self, endpoint: str, count: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Fetch latest market data from TWSE OpenAPI.

        Args:
            endpoint: API endpoint path
            count: Number of latest records to return. If None, returns all records.

        Returns:
            List of latest market data records
        """
        try:
            data = await self.get_data(endpoint)

            # Return latest records or all data if count is None
            result = data[-count:] if data and count is not None else data
            logger.debug(f"Market data from {endpoint}: {len(result)} records")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch latest market data: {e}")
            return []

    async def get_industry_api_suffix(self, code: str) -> str:
        """
        Get the appropriate API suffix based on company industry.

        Args:
            code: Company stock code

        Returns:
            API suffix for the company's industry
        """
        try:
            profile_data = await self.get_company_data("/opendata/t187ap03_L", code)

            if not profile_data:
                return "_ci"  # Default to general industry

            industry = profile_data.get("產業別", "")

            # Map industry to API suffix
            industry_mapping = {
                "金融業": "_basi",
                "證券期貨業": "_bd",
                "金控業": "_fh",
                "保險業": "_ins",
                "異業": "_mim",
                "一般業": "_ci",
            }

            # Check if industry exactly matches or contains any of the key terms
            for industry_key, suffix in industry_mapping.items():
                if industry_key in industry or industry == industry_key:
                    return suffix

            return "_ci"  # Default to general industry if no match

        except Exception as e:
            logger.error(f"Error determining industry for {code}: {e}")
            return "_ci"  # Default to general industry on error

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
