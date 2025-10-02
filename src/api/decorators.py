"""
Decorators for enhancing API client with rate limiting and caching.
使用裝飾器模式為 API 客戶端添加快取和速率限制功能，避免侵入原始程式碼。
"""

import asyncio
import time
from typing import Any

from ..cache.rate_limited_cache_service import RateLimitedCacheService
from ..models.stock_data import APIError, TWStockResponse, ValidationError
from ..utils.config_manager import ConfigManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


def with_rate_limiting_and_cache(
    config_file: str | None = None,
):
    """
    Class decorator that adds rate limiting and caching to TWStockAPIClient.

    使用方式:
        from .decorators import with_rate_limiting_and_cache

        # 創建帶有增強功能的客戶端
        client = with_rate_limiting_and_cache()(TWStockAPIClient)()

        # 或使用工廠函式
        from .twse_client import create_client
        client = create_client(enhanced=True)

    Args:
        config_file: 配置檔案路徑
    """

    def decorator(cls):
        """Decorator that wraps the class."""

        class EnhancedClient(cls):
            """Enhanced client with rate limiting and caching."""

            def __init__(self, *args, **kwargs):
                """Initialize enhanced client."""
                super().__init__(*args, **kwargs)

                # 添加增強功能
                self._config = ConfigManager(config_file)
                self._cache_service = RateLimitedCacheService(self._config)

                logger.info("已啟用速率限制和快取功能")
                logger.debug(
                    f"配置: rate_limiting={self._config.is_rate_limiting_enabled()}, "
                    f"caching={self._config.is_caching_enabled()}"
                )

            async def get_stock_quote(
                self,
                symbol: str,
                market: str | None = None,
                force_refresh: bool = False,
            ) -> TWStockResponse:
                """
                Get stock quote with caching and rate limiting.

                Args:
                    symbol: 股票代號
                    market: 市場類型 ('tse' or 'otc')
                    force_refresh: 是否強制刷新快取
                """
                start_time = time.time()
                logger.info(f"開始查詢股票 {symbol}，force_refresh={force_refresh}")

                try:
                    # 強制刷新時清除快取
                    if force_refresh:
                        logger.debug(f"強制刷新，清除 {symbol} 的快取")
                        await self._cache_service.invalidate_symbol_cache(
                            symbol, "quote"
                        )

                    # 檢查快取和速率限制
                    logger.debug(f"檢查 {symbol} 的快取和速率限制")
                    (
                        cached_data,
                        is_from_cache,
                        message,
                    ) = await self._cache_service.get_cached_or_wait(symbol, "quote")

                    if cached_data:
                        # 返回快取資料
                        response_time = (time.time() - start_time) * 1000
                        await self._cache_service.record_cached_response(
                            symbol, "quote"
                        )

                        logger.info(f"從快取返回 {symbol} 資料 ({response_time:.2f}ms)")
                        return self._cached_data_to_response(cached_data["data"])

                    if "cache_miss_can_make_request" in message:
                        # 發送新的 API 請求
                        logger.debug(f"快取未命中，發送 API 請求: {symbol}")
                        try:
                            response = await super().get_stock_quote(symbol, market)
                            response_time = (time.time() - start_time) * 1000

                            # 快取成功的回應
                            response_dict = self._response_to_dict(response)
                            await self._cache_service.record_successful_request(
                                symbol, response_dict, response_time, "quote"
                            )

                            logger.info(
                                f"成功取得 API 新資料: {symbol} ({response.company_name}) = "
                                f"${response.current_price} ({response_time:.2f}ms)"
                            )
                            return response

                        except Exception as e:
                            response_time = (time.time() - start_time) * 1000
                            await self._cache_service.record_failed_request(
                                symbol, response_time, "quote"
                            )
                            logger.error(f"API 請求失敗: {symbol} - {e}")
                            raise APIError(
                                f"API request failed for {symbol}: {str(e)}"
                            ) from e

                    else:
                        # 速率限制且無快取可用
                        logger.warning(f"速率限制且無快取資料: {symbol} - {message}")
                        raise APIError(
                            f"Rate limited for stock {symbol} and no cached data available. "
                            f"Please try again later. (Reason: {message})"
                        )

                except (ValidationError, APIError):
                    raise
                except Exception as e:
                    response_time = (time.time() - start_time) * 1000
                    await self._cache_service.record_failed_request(
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
                """Get multiple stock quotes with rate limiting."""
                logger.info(
                    f"開始批量查詢 {len(symbols)} 支股票，force_refresh={force_refresh}"
                )

                results = []
                failed_symbols = []

                for i, symbol in enumerate(symbols):
                    try:
                        logger.debug(f"處理第 {i + 1}/{len(symbols)} 個查詢: {symbol}")
                        result = await self.get_stock_quote(
                            symbol, force_refresh=force_refresh
                        )
                        results.append(result)
                        logger.debug(f"成功查詢: {symbol} -> {result.company_name}")

                        # 添加延遲以遵守速率限制
                        if i < len(symbols) - 1:
                            await asyncio.sleep(0.1)

                    except Exception as e:
                        failed_symbols.append(symbol)
                        logger.warning(f"查詢失敗: {symbol} - {e}")

                logger.info(f"批量查詢完成 - 成功: {len(results)}/{len(symbols)}")
                if failed_symbols:
                    logger.warning(f"失敗的股票: {failed_symbols}")
                return results

            def _response_to_dict(self, response: TWStockResponse) -> dict:
                """Convert TWStockResponse to dictionary for caching."""
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
                # 確保 update_time 是 datetime 物件
                if isinstance(data.get("update_time"), str):
                    from datetime import datetime

                    data["update_time"] = datetime.fromisoformat(data["update_time"])
                return TWStockResponse(**data)

            # 增強功能的方法

            async def get_system_stats(self) -> dict[str, Any]:
                """Get comprehensive system statistics."""
                return self._cache_service.get_comprehensive_stats()

            async def get_health_status(self) -> dict[str, Any]:
                """Get system health status."""
                return await self._cache_service.health_check()

            async def clear_cache(self) -> None:
                """Clear all cached data."""
                await self._cache_service.clear_all_cache()
                logger.info("Cache cleared")

            async def reset_rate_limits(self) -> None:
                """Reset all rate limiting counters."""
                await self._cache_service.reset_rate_limits()
                logger.info("Rate limits reset")

            async def invalidate_symbol_cache(self, symbol: str) -> bool:
                """Manually invalidate cache for a specific symbol."""
                success = await self._cache_service.invalidate_symbol_cache(
                    symbol, "quote"
                )
                logger.info(f"Cache invalidated for {symbol}: {success}")
                return success

            def get_configuration(self) -> dict[str, Any]:
                """Get current system configuration."""
                return self._cache_service.config.get_all_config()

            def update_rate_limits(
                self,
                per_stock_interval: float | None = None,
                global_limit_per_minute: int | None = None,
                per_second_limit: int | None = None,
                save_to_file: bool = False,
            ) -> bool:
                """Update rate limiting parameters."""
                success = self._config.update_rate_limits(
                    per_stock_interval,
                    global_limit_per_minute,
                    per_second_limit,
                    save_to_file,
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
                success = self._config.update_cache_settings(
                    ttl_seconds, max_size, max_memory_mb, save_to_file
                )
                logger.info(f"Cache settings updated: {success}")
                return success

            def enable_rate_limiting(self, save_to_file: bool = False) -> bool:
                """Enable rate limiting feature."""
                return self._config.enable_feature("rate_limiting", save_to_file)

            def disable_rate_limiting(self, save_to_file: bool = False) -> bool:
                """Disable rate limiting feature."""
                return self._config.disable_feature("rate_limiting", save_to_file)

            def enable_caching(self, save_to_file: bool = False) -> bool:
                """Enable caching feature."""
                return self._config.enable_feature("caching", save_to_file)

            def disable_caching(self, save_to_file: bool = False) -> bool:
                """Disable caching feature."""
                return self._config.disable_feature("caching", save_to_file)

            def is_rate_limiting_enabled(self) -> bool:
                """Check if rate limiting is enabled."""
                return self._config.is_rate_limiting_enabled()

            def is_caching_enabled(self) -> bool:
                """Check if caching is enabled."""
                return self._config.is_caching_enabled()

        # 保留原始類名
        EnhancedClient.__name__ = f"Enhanced{cls.__name__}"
        EnhancedClient.__qualname__ = f"Enhanced{cls.__qualname__}"

        return EnhancedClient

    return decorator
