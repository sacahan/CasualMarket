"""
Enhanced Taiwan Stock Exchange API client with rate limiting and caching.
Integrates the rate limiting and caching system with the existing TWSE API client.
"""

import asyncio
import time
from typing import Any

from ..cache.rate_limited_cache_service import RateLimitedCacheService
from ..models.stock_data import APIError, TWStockResponse, ValidationError
from ..utils.config_manager import ConfigManager
from ..utils.logging import get_logger
from .twse_client import TWStockAPIClient

# 設置日誌
logger = get_logger(__name__)


class EnhancedTWStockAPIClient:
    """
    Enhanced Taiwan Stock Exchange API client with intelligent rate limiting and caching.

    This client wraps the original TWStockAPIClient and adds:
    - Multi-layered rate limiting (per-stock, global, per-second)
    - Intelligent TTL-based caching
    - Performance monitoring and statistics
    - Automatic fallback to cached data when rate limited
    """

    def __init__(self, config_file: str | None = None):
        """Initialize the enhanced API client."""
        logger.debug(f"初始化 EnhancedTWStockAPIClient，配置檔案: {config_file}")

        self.config = ConfigManager(config_file)
        self.cache_service = RateLimitedCacheService(self.config)
        self.original_client = TWStockAPIClient()

        logger.info("Enhanced TWSE API client 初始化完成，已啟用速率限制和快取功能")
        logger.debug(
            f"配置: rate_limiting={self.is_rate_limiting_enabled()}, caching={self.is_caching_enabled()}"
        )

    async def get_stock_quote(
        self, symbol: str, market: str | None = None, force_refresh: bool = False
    ) -> TWStockResponse:
        """
        Get real-time stock quote with intelligent caching and rate limiting.

        Args:
            symbol: Stock symbol (4-digit code)
            market: Market type ('tse' or 'otc'), auto-detected if None
            force_refresh: If True, bypass cache and make fresh API request

        Returns:
            TWStockResponse: Stock quote data

        Raises:
            ValidationError: Invalid stock symbol format
            APIError: API request failed and no cached data available
        """
        start_time = time.time()
        logger.info(f"開始查詢股票 {symbol}，force_refresh={force_refresh}")

        try:
            # If force refresh requested, invalidate cache first
            if force_refresh:
                logger.debug(f"強制刷新，清除 {symbol} 的快取")
                await self.cache_service.invalidate_symbol_cache(symbol, "quote")

            # Check cache and rate limits
            logger.debug(f"檢查 {symbol} 的快取和速率限制")
            (
                cached_data,
                is_from_cache,
                message,
            ) = await self.cache_service.get_cached_or_wait(symbol, "quote")

            if cached_data:
                # Return cached data
                response_time = (time.time() - start_time) * 1000
                await self.cache_service.record_cached_response(symbol, "quote")

                logger.info(f"從快取返回 {symbol} 資料 ({response_time:.2f}ms)")
                logger.debug(
                    f"快取資料: {cached_data['data']['name']} = ${cached_data['data']['price']}"
                )
                return self._cached_data_to_response(cached_data["data"])

            if "cache_miss_can_make_request" in message:
                # Make fresh API request
                logger.debug(f"快取未命中，發送 API 請求: {symbol}")
                try:
                    response = await self.original_client.get_stock_quote(
                        symbol, market
                    )
                    response_time = (time.time() - start_time) * 1000

                    # Cache the successful response
                    response_dict = self._response_to_dict(response)
                    await self.cache_service.record_successful_request(
                        symbol, response_dict, response_time, "quote"
                    )

                    logger.info(
                        f"成功取得 API 新資料: {symbol} ({response.company_name}) = ${response.current_price} ({response_time:.2f}ms)"
                    )
                    return response

                except Exception as e:
                    response_time = (time.time() - start_time) * 1000
                    await self.cache_service.record_failed_request(
                        symbol, response_time, "quote"
                    )

                    logger.error(f"API 請求失敗: {symbol} - {e}")
                    raise APIError(f"API request failed for {symbol}: {str(e)}") from e

            else:
                # Rate limited and no cache available
                logger.warning(f"速率限制且無快取資料: {symbol} - {message}")
                raise APIError(
                    f"Rate limited for stock {symbol} and no cached data available. "
                    f"Please try again later. (Reason: {message})"
                )

        except (ValidationError, APIError):
            # Re-raise validation and API errors as-is
            logger.debug(f"重新拋出業務錯誤: {symbol}")
            raise
        except Exception as e:
            # Handle unexpected errors
            response_time = (time.time() - start_time) * 1000
            await self.cache_service.record_failed_request(
                symbol, response_time, "quote"
            )

            logger.error(
                f"查詢股票時發生未預期錯誤: {symbol} - {type(e).__name__}: {e}"
            )
            raise APIError(
                f"Unexpected error retrieving data for {symbol}: {str(e)}"
            ) from e

    async def get_multiple_quotes(
        self, symbols: list[str], force_refresh: bool = False
    ) -> list[TWStockResponse]:
        """
        Get real-time quotes for multiple stocks with intelligent batching.

        Args:
            symbols: List of stock symbols
            force_refresh: If True, bypass cache for all symbols

        Returns:
            List of stock quote responses (may be fewer than requested due to rate limits)
        """
        logger.info(
            f"開始批量查詢 {len(symbols)} 支股票，force_refresh={force_refresh}"
        )
        logger.debug(f"股票清單: {symbols}")

        # Create tasks for all symbols
        tasks = []
        for symbol in symbols:
            task = self.get_stock_quote(symbol, force_refresh=force_refresh)
            tasks.append(task)

        # Execute with proper rate limiting
        results = []
        failed_symbols = []
        for i, task in enumerate(tasks):
            try:
                logger.debug(f"處理第 {i + 1}/{len(tasks)} 個查詢: {symbols[i]}")
                result = await task
                results.append(result)
                logger.debug(f"成功查詢: {symbols[i]} -> {result.company_name}")

                # Add small delay between requests to respect rate limits
                if i < len(tasks) - 1:  # Don't delay after last request
                    await asyncio.sleep(0.1)  # 100ms delay

            except Exception as e:
                failed_symbols.append(symbols[i])
                logger.warning(f"查詢失敗: {symbols[i]} - {e}")
                # Continue with other symbols

        logger.info(f"批量查詢完成 - 成功: {len(results)}/{len(symbols)}")
        if failed_symbols:
            logger.warning(f"失敗的股票: {failed_symbols}")
        return results

    def _response_to_dict(self, response: TWStockResponse) -> dict:
        """Convert TWStockResponse to dictionary for caching."""
        logger.debug(f"轉換回應為字典格式: {response.symbol}")
        return {
            "symbol": response.symbol,
            "company_name": response.company_name,
            "current_price": response.current_price,
            "change": response.change,
            "change_percent": response.change_percent,
            "volume": response.volume,
            "open_price": response.open_price,
            "high_price": response.high_price,
            "low_price": response.low_price,
            "previous_close": response.previous_close,
            "upper_limit": response.upper_limit,
            "lower_limit": response.lower_limit,
            "bid_prices": response.bid_prices,
            "bid_volumes": response.bid_volumes,
            "ask_prices": response.ask_prices,
            "ask_volumes": response.ask_volumes,
            "update_time": response.update_time.isoformat(),
            "last_trade_time": response.last_trade_time,
        }

    def _cached_data_to_response(self, data: dict) -> TWStockResponse:
        """Convert cached dictionary data back to TWStockResponse."""
        logger.debug(f"從快取字典轉換為回應物件: {data.get('symbol', 'unknown')}")
        # 確保 update_time 是 datetime 物件
        if isinstance(data.get("update_time"), str):
            from datetime import datetime

            data["update_time"] = datetime.fromisoformat(data["update_time"])
        return TWStockResponse(**data)

    async def get_system_stats(self) -> dict[str, Any]:
        """Get comprehensive system statistics."""
        return self.cache_service.get_comprehensive_stats()

    async def get_health_status(self) -> dict[str, Any]:
        """Get system health status."""
        return await self.cache_service.health_check()

    async def clear_cache(self) -> None:
        """Clear all cached data."""
        await self.cache_service.clear_all_cache()
        logger.info("Cache cleared")

    async def reset_rate_limits(self) -> None:
        """Reset all rate limiting counters."""
        await self.cache_service.reset_rate_limits()
        logger.info("Rate limits reset")

    async def invalidate_symbol_cache(self, symbol: str) -> bool:
        """Manually invalidate cache for a specific symbol."""
        success = await self.cache_service.invalidate_symbol_cache(symbol, "quote")
        logger.info(f"Cache invalidated for {symbol}: {success}")
        return success

    def get_configuration(self) -> dict[str, Any]:
        """Get current system configuration."""
        return self.cache_service.config.get_all_config()

    def update_rate_limits(
        self,
        per_stock_interval: float | None = None,
        global_limit_per_minute: int | None = None,
        per_second_limit: int | None = None,
        save_to_file: bool = False,
    ) -> bool:
        """Update rate limiting parameters."""
        success = self.cache_service.config.update_rate_limits(
            per_stock_interval, global_limit_per_minute, per_second_limit, save_to_file
        )
        logger.info(f"Rate limits updated: {success}")
        return success

    def update_cache_settings(
        self,
        ttl_seconds: int | None = None,
        max_size: int | None = None,
        max_memory_mb: float | None = None,
        save_to_file: bool = False,
    ) -> bool:
        """Update cache configuration."""
        success = self.cache_service.config.update_cache_settings(
            ttl_seconds, max_size, max_memory_mb, save_to_file
        )
        logger.info(f"Cache settings updated: {success}")
        return success

    def enable_rate_limiting(self, save_to_file: bool = False) -> bool:
        """Enable rate limiting feature."""
        return self.cache_service.config.enable_feature("rate_limiting", save_to_file)

    def disable_rate_limiting(self, save_to_file: bool = False) -> bool:
        """Disable rate limiting feature."""
        return self.cache_service.config.disable_feature("rate_limiting", save_to_file)

    def enable_caching(self, save_to_file: bool = False) -> bool:
        """Enable caching feature."""
        return self.cache_service.config.enable_feature("caching", save_to_file)

    def disable_caching(self, save_to_file: bool = False) -> bool:
        """Disable caching feature."""
        return self.cache_service.config.disable_feature("caching", save_to_file)

    def is_rate_limiting_enabled(self) -> bool:
        """Check if rate limiting is enabled."""
        return self.cache_service.config.is_rate_limiting_enabled()

    def is_caching_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.cache_service.config.is_caching_enabled()


# Convenience function to create enhanced client
def create_enhanced_client(config_file: str | None = None) -> EnhancedTWStockAPIClient:
    """Create an enhanced TWSE API client with rate limiting and caching."""
    return EnhancedTWStockAPIClient(config_file)
