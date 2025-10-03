"""
台灣證券交易所 API 的整合式流量限制與快取服務。
將所有快取元件整合為統一的高階介面。
"""

import logging
import os
import time
from typing import Any

from .cache_manager import CacheManager
from .rate_limiter import RateLimiter
from .request_tracker import RequestTracker

logger = logging.getLogger(__name__)


class RateLimitedCacheService:
    """
    整合流量限制、快取與統計追蹤的高階服務。
    提供受保護 API 存取與智慧型快取的主要介面。
    """

    def __init__(self):
        # 從環境變數讀取配置，提供合理的預設值
        self.rate_limiter = RateLimiter(
            per_stock_interval=float(
                os.getenv("MARKET_MCP_RATE_LIMIT_INTERVAL", "30.0")
            ),
            global_limit_per_minute=int(
                os.getenv("MARKET_MCP_RATE_LIMIT_GLOBAL_PER_MINUTE", "20")
            ),
            per_second_limit=int(os.getenv("MARKET_MCP_RATE_LIMIT_PER_SECOND", "2")),
        )

        self.cache_manager = CacheManager(
            ttl_seconds=int(os.getenv("MARKET_MCP_CACHE_TTL", "30")),
            max_size=int(os.getenv("MARKET_MCP_CACHE_MAX_SIZE", "1000")),
            max_memory_mb=float(os.getenv("MARKET_MCP_CACHE_MAX_MEMORY_MB", "200.0")),
        )

        self.request_tracker = RequestTracker(
            stats_retention_hours=int(
                os.getenv("MARKET_MCP_MONITORING_STATS_RETENTION_HOURS", "24")
            )
        )

        self._is_enabled = True

    def _is_rate_limiting_enabled(self) -> bool:
        """檢查是否啟用限速功能"""
        return os.getenv("MARKET_MCP_RATE_LIMITING_ENABLED", "true").lower() == "true"

    def _is_caching_enabled(self) -> bool:
        """檢查是否啟用快取功能"""
        return os.getenv("MARKET_MCP_CACHING_ENABLED", "true").lower() == "true"

    def _get_rate_limiting_config(self) -> dict[str, Any]:
        """取得限速配置"""
        return {
            "per_stock_interval_seconds": float(
                os.getenv("MARKET_MCP_RATE_LIMIT_INTERVAL", "30.0")
            ),
            "global_limit_per_minute": int(
                os.getenv("MARKET_MCP_RATE_LIMIT_GLOBAL_PER_MINUTE", "20")
            ),
            "per_second_limit": int(os.getenv("MARKET_MCP_RATE_LIMIT_PER_SECOND", "2")),
            "enabled": self._is_rate_limiting_enabled(),
        }

    def _get_caching_config(self) -> dict[str, Any]:
        """取得快取配置"""
        return {
            "ttl_seconds": int(os.getenv("MARKET_MCP_CACHE_TTL", "30")),
            "max_size": int(os.getenv("MARKET_MCP_CACHE_MAX_SIZE", "1000")),
            "max_memory_mb": float(
                os.getenv("MARKET_MCP_CACHE_MAX_MEMORY_MB", "200.0")
            ),
            "enabled": self._is_caching_enabled(),
        }

    async def can_make_request(
        self, symbol: str, request_type: str = "quote"
    ) -> tuple[bool, str, float]:
        """
        檢查指定股票是否可發送請求。
        回傳 (允許, 原因, 等待秒數)。
        """
        if not self._is_rate_limiting_enabled():
            return True, "rate_limiting_disabled", 0.0

        return await self.rate_limiter.can_request(symbol)

    async def get_cached_or_wait(
        self, symbol: str, request_type: str = "quote"
    ) -> tuple[dict | None, bool, str]:
        """
        智慧型快取取得，並考量流量限制。
        回傳 (資料, 是否來自快取, 訊息)。

        邏輯：
        1. 先檢查快取
        2. 若快取未命中，檢查流量限制
        3. 若流量受限則回傳快取資料
        4. 若無快取且流量受限則回傳 None
        """
        # Always try cache first
        cached_data = None
        if self._is_caching_enabled():
            cached_data = await self.cache_manager.get_cached_data(symbol, request_type)

        # Check rate limits
        can_request, reason, wait_time = await self.can_make_request(
            symbol, request_type
        )

        if can_request:
            if cached_data:
                return cached_data, True, "cache_hit_but_can_make_new_request"
            else:
                return None, False, "cache_miss_can_make_request"
        else:
            # Rate limited - return cached data if available
            if cached_data:
                await self.request_tracker.record_rate_limit_hit(
                    symbol, reason, wait_time, request_type
                )
                return cached_data, True, f"rate_limited_returned_cache_{reason}"
            else:
                await self.request_tracker.record_rate_limit_hit(
                    symbol, reason, wait_time, request_type
                )
                return None, False, f"rate_limited_no_cache_{reason}"

    async def record_successful_request(
        self,
        symbol: str,
        response_data: dict,
        response_time_ms: float,
        request_type: str = "quote",
    ) -> bool:
        """
        記錄成功的 API 請求並快取回應。
        全部記錄成功則回傳 True。
        """
        try:
            # Record the request with rate limiter
            await self.rate_limiter.record_request(symbol)

            # Cache the response data
            cache_success = True
            if self._is_caching_enabled():
                cache_success = await self.cache_manager.set_cached_data(
                    symbol, response_data, request_type
                )

            # Track the request for statistics
            request_id = await self.request_tracker.record_request_start(
                symbol, request_type
            )
            await self.request_tracker.record_request_complete(
                request_id, symbol, True, response_time_ms, False, request_type
            )

            logger.debug(
                f"Recorded successful request for {symbol}: "
                f"{response_time_ms:.2f}ms, cached: {cache_success}"
            )

            return cache_success

        except Exception as e:
            logger.error(f"記錄股票 {symbol} 成功請求時發生錯誤: {e}")
            return False

    async def record_failed_request(
        self, symbol: str, response_time_ms: float, request_type: str = "quote"
    ) -> None:
        """
        記錄失敗的 API 請求以供統計。
        """
        try:
            request_id = await self.request_tracker.record_request_start(
                symbol, request_type
            )
            await self.request_tracker.record_request_complete(
                request_id, symbol, False, response_time_ms, False, request_type
            )

            logger.debug(
                f"Recorded failed request for {symbol}: {response_time_ms:.2f}ms"
            )

        except Exception as e:
            logger.error(f"記錄股票 {symbol} 失敗請求時發生錯誤: {e}")

    async def record_cached_response(
        self, symbol: str, request_type: str = "quote"
    ) -> None:
        """
        記錄回傳快取資料的事件。
        """
        try:
            request_id = await self.request_tracker.record_request_start(
                symbol, request_type
            )
            await self.request_tracker.record_request_complete(
                request_id,
                symbol,
                True,
                0.0,  # 0ms for cached response
                True,
                request_type,
            )

            logger.debug(f"已記錄股票 {symbol} 的快取回應")

        except Exception as e:
            logger.error(f"記錄股票 {symbol} 快取回應時發生錯誤: {e}")

    def get_comprehensive_stats(self) -> dict[str, Any]:
        """
        取得所有元件的綜合統計資料。
        """
        try:
            return {
                "service_status": {
                    "enabled": self._is_enabled,
                    "rate_limiting_enabled": self._is_rate_limiting_enabled(),
                    "caching_enabled": self._is_caching_enabled(),
                },
                "rate_limiter": self.rate_limiter.get_stats(),
                "cache_manager": self.cache_manager.get_cache_stats(),
                "request_tracker": {
                    "global": self.request_tracker.get_global_stats(),
                    "rate_limits": self.request_tracker.get_rate_limit_summary(),
                    "top_symbols": self.request_tracker.get_top_symbols(5),
                },
                "cache_health": {
                    "is_healthy": self.cache_manager.is_cache_healthy()[0],
                    "issues": self.cache_manager.is_cache_healthy()[1],
                },
                "configuration": {
                    "rate_limiting": self._get_rate_limiting_config(),
                    "caching": self._get_caching_config(),
                },
            }
        except Exception as e:
            logger.error(f"取得綜合統計資料時發生錯誤: {e}")
            return {"error": str(e)}

    async def health_check(self) -> dict[str, Any]:
        """
        執行所有元件的綜合健康檢查。
        """
        health_status = {
            "overall_healthy": True,
            "timestamp": time.time(),
            "components": {},
            "issues": [],
            "recommendations": [],
        }

        try:
            # Check cache health
            cache_healthy, cache_issues = self.cache_manager.is_cache_healthy()
            health_status["components"]["cache"] = {
                "healthy": cache_healthy,
                "issues": cache_issues,
            }

            if not cache_healthy:
                health_status["overall_healthy"] = False
                health_status["issues"].extend(
                    [f"Cache: {issue}" for issue in cache_issues]
                )

            # Check rate limiter stats
            rate_stats = self.rate_limiter.get_stats()
            rate_healthy = True
            rate_issues = []

            # Check if global rate limit is being hit frequently
            if (
                rate_stats["global_requests_last_minute"]
                > rate_stats["global_limit_per_minute"] * 0.9
            ):
                rate_healthy = False
                rate_issues.append("Approaching global rate limit")

            health_status["components"]["rate_limiter"] = {
                "healthy": rate_healthy,
                "issues": rate_issues,
            }

            if not rate_healthy:
                health_status["overall_healthy"] = False
                health_status["issues"].extend(
                    [f"Rate Limiter: {issue}" for issue in rate_issues]
                )

            # Check request tracker stats
            global_stats = self.request_tracker.get_global_stats()
            tracker_healthy = True
            tracker_issues = []

            # Check success rate
            if (
                global_stats["success_rate_percent"] < 90.0
                and global_stats["total_requests"] > 10
            ):
                tracker_healthy = False
                tracker_issues.append(
                    f"Low success rate: {global_stats['success_rate_percent']}%"
                )

            # Check cache hit rate
            target_hit_rate = float(
                os.getenv("MARKET_MCP_MONITORING_CACHE_HIT_RATE_TARGET", "80.0")
            )
            if (
                global_stats["cache_hit_rate_percent"] < target_hit_rate
                and global_stats["total_requests"] > 10
            ):
                tracker_healthy = False
                tracker_issues.append(
                    f"Low cache hit rate: {global_stats['cache_hit_rate_percent']}% "
                    f"(target: {target_hit_rate}%)"
                )

            health_status["components"]["request_tracker"] = {
                "healthy": tracker_healthy,
                "issues": tracker_issues,
            }

            if not tracker_healthy:
                health_status["overall_healthy"] = False
                health_status["issues"].extend(
                    [f"Request Tracker: {issue}" for issue in tracker_issues]
                )

            # Generate recommendations
            if not cache_healthy:
                health_status["recommendations"].append(
                    "Consider increasing cache size or memory limit"
                )

            if not rate_healthy:
                health_status["recommendations"].append(
                    "Consider adjusting rate limits or request patterns"
                )

            if global_stats["cache_hit_rate_percent"] < target_hit_rate:
                health_status["recommendations"].append(
                    "Optimize cache TTL or request patterns to improve hit rate"
                )

        except Exception as e:
            health_status["overall_healthy"] = False
            health_status["issues"].append(f"Health check error: {str(e)}")
            logger.error(f"健康檢查時發生錯誤: {e}")

        return health_status

    async def invalidate_symbol_cache(
        self, symbol: str, request_type: str = "quote"
    ) -> bool:
        """
        手動使指定股票的快取失效。
        """
        if self._is_caching_enabled():
            return await self.cache_manager.invalidate(symbol, request_type)
        return True

    async def clear_all_cache(self) -> None:
        """
        清除所有快取資料。
        """
        if self._is_caching_enabled():
            await self.cache_manager.clear_all()

    async def reset_rate_limits(self) -> None:
        """
        重設所有流量限制計數器。
        """
        self.rate_limiter.reset_limits()

    async def reset_all_stats(self) -> None:
        """
        重設所有統計資料並清除快取。
        """
        await self.clear_all_cache()
        self.rate_limiter.reset_limits()
        await self.request_tracker.reset_stats()
        logger.info("所有統計資料和快取已重置")

    def enable_service(self) -> None:
        """
        啟用流量限制與快取服務。
        """
        self._is_enabled = True
        logger.info("流量限制快取服務已啟用")

    def disable_service(self) -> None:
        """
        停用流量限制與快取服務。
        """
        self._is_enabled = False
        logger.info("流量限制快取服務已停用")

    def is_enabled(self) -> bool:
        """
        檢查服務是否已啟用。
        """
        return self._is_enabled
