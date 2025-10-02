"""
Function decorators for adding caching and rate limiting to API methods.
"""

import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar

from ..cache.rate_limited_cache_service import RateLimitedCacheService
from ..models.stock_data import APIError, TWStockResponse
from ..utils.config_manager import ConfigManager
from ..utils.logging import get_logger

logger = get_logger(__name__)

_cache_service: RateLimitedCacheService | None = None
_config_manager: ConfigManager | None = None

F = TypeVar("F", bound=Callable[..., Any])


def _get_cache_service() -> RateLimitedCacheService:
    """Get global cache service instance."""
    global _cache_service, _config_manager
    if _cache_service is None:
        _config_manager = ConfigManager()
        _cache_service = RateLimitedCacheService(_config_manager)
        logger.info("已初始化全域快取服務")
    return _cache_service


def with_cache(
    enable_rate_limit: bool = True,
    cache_key_prefix: str | None = None,
):
    """
    統一快取裝飾器，基於函數名稱和所有參數自動生成快取鍵。

    Args:
        enable_rate_limit: 是否啟用速率限制
        cache_key_prefix: 快取鍵值前綴，若未指定則使用函數名稱

    Examples:
        >>> @with_cache(enable_rate_limit=True)
        >>> async def get_stock_quote(self, symbol: str):
        >>>     # Cache key: "get_stock_quote_{symbol}"
        >>>     pass

        >>> @with_cache(enable_rate_limit=False, cache_key_prefix="financial")
        >>> async def get_financial_data(self, endpoint: str, symbol: str):
        >>>     # Cache key: "financial_{endpoint}_{symbol}"
        >>>     pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            force_refresh = kwargs.pop("force_refresh", False)

            # 生成基於函數名稱和所有參數的快取鍵
            cache_params = []

            # 使用函數名稱或指定的前綴
            prefix = cache_key_prefix or func.__name__
            cache_params.append(prefix)

            # 包含所有位置參數（跳過 self）
            if len(args) > 1:  # 跳過 self
                for arg in args[1:]:
                    cache_params.append(str(arg))

            # 包含所有關鍵字參數（排除 force_refresh）
            for key, value in kwargs.items():
                if key != "force_refresh":
                    cache_params.append(f"{key}:{value}")

            # 生成唯一的快取鍵
            import hashlib

            cache_key_str = "|".join(cache_params)
            cache_key = hashlib.md5(cache_key_str.encode()).hexdigest()[:16]

            cache_service = _get_cache_service()
            start_time = time.time()

            try:
                if force_refresh:
                    await cache_service.invalidate_symbol_cache(cache_key, prefix)

                if enable_rate_limit:
                    (
                        cached_data,
                        _,
                        message,
                    ) = await cache_service.get_cached_or_wait(cache_key, prefix)

                    if cached_data:
                        response_time = (time.time() - start_time) * 1000
                        await cache_service.record_cached_response(cache_key, prefix)
                        return _parse_cached_response(cached_data["data"])

                    if "cache_miss_can_make_request" not in message:
                        raise APIError(f"函數 {func.__name__} 受流量限制: {message}")

                else:
                    cached_data = await cache_service.cache_manager.get_cached_data(
                        cache_key, prefix
                    )
                    if cached_data and not force_refresh:
                        return _parse_cached_response(cached_data["data"])

                result = await func(*args, **kwargs)
                response_time = (time.time() - start_time) * 1000

                if result is not None:
                    result_dict = _prepare_for_cache(result)
                    if result_dict:
                        await cache_service.record_successful_request(
                            cache_key, result_dict, response_time, prefix
                        )

                return result

            except (APIError, ValidationError) as e:
                response_time = (time.time() - start_time) * 1000
                if enable_rate_limit:
                    await cache_service.record_failed_request(
                        cache_key, response_time, prefix
                    )
                raise e
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                if enable_rate_limit:
                    await cache_service.record_failed_request(
                        cache_key, response_time, prefix
                    )
                raise APIError(f"函數 {func.__name__} 操作失敗: {str(e)}") from e

        return wrapper

    return decorator


def _prepare_for_cache(result: Any) -> dict | None:
    """Prepare result data for caching."""
    try:
        if isinstance(result, TWStockResponse):
            return {
                "symbol": result.symbol,
                "company_name": result.company_name,
                "current_price": result.current_price,
                "change": result.change,
                "change_percent": result.change_percent,
                "volume": result.volume,
                "open_price": result.open_price,
                "high_price": result.high_price,
                "low_price": result.low_price,
                "previous_close": result.previous_close,
                "upper_limit": result.upper_limit,
                "lower_limit": result.lower_limit,
                "bid_prices": result.bid_prices,
                "bid_volumes": result.bid_volumes,
                "ask_prices": result.ask_prices,
                "ask_volumes": result.ask_volumes,
                "update_time": result.update_time.isoformat(),
                "last_trade_time": result.last_trade_time,
            }
        elif isinstance(result, dict):
            return result
        else:
            if hasattr(result, "__dict__"):
                return result.__dict__
            return None
    except Exception:
        return None


def _parse_cached_response(data: dict) -> Any:
    """Parse cached data."""
    try:
        if "company_name" in data and "current_price" in data:
            if isinstance(data.get("update_time"), str):
                from datetime import datetime

                data["update_time"] = datetime.fromisoformat(data["update_time"])
            return TWStockResponse(**data)
        else:
            return data
    except Exception:
        return data
