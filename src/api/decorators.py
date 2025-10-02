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


def with_cache_and_rate_limit(
    cache_key_prefix: str = "default",
    enable_cache: bool = True,
    enable_rate_limit: bool = True,
):
    """Decorator to add caching and rate limiting to async functions."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            symbol = None
            force_refresh = kwargs.pop("force_refresh", False)

            if args and len(args) > 1:
                symbol = args[1]
            elif "symbol" in kwargs:
                symbol = kwargs["symbol"]

            if not symbol:
                return await func(*args, **kwargs)

            cache_service = _get_cache_service()
            start_time = time.time()

            try:
                if enable_cache:
                    if force_refresh:
                        await cache_service.invalidate_symbol_cache(
                            symbol, cache_key_prefix
                        )

                    if enable_rate_limit:
                        (
                            cached_data,
                            _,
                            message,
                        ) = await cache_service.get_cached_or_wait(
                            symbol, cache_key_prefix
                        )

                        if cached_data:
                            response_time = (time.time() - start_time) * 1000
                            await cache_service.record_cached_response(
                                symbol, cache_key_prefix
                            )
                            return _parse_cached_response(cached_data["data"])

                        if "cache_miss_can_make_request" not in message:
                            raise APIError(f"股票 {symbol} 受流量限制: {message}")

                    else:
                        cached_data = await cache_service.cache_manager.get_cached_data(
                            symbol, cache_key_prefix
                        )
                        if cached_data and not force_refresh:
                            return _parse_cached_response(cached_data["data"])

                result = await func(*args, **kwargs)
                response_time = (time.time() - start_time) * 1000

                if enable_cache:
                    result_dict = _prepare_for_cache(result)
                    if result_dict:
                        await cache_service.record_successful_request(
                            symbol, result_dict, response_time, cache_key_prefix
                        )

                return result

            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                if enable_cache and enable_rate_limit:
                    await cache_service.record_failed_request(
                        symbol, response_time, cache_key_prefix
                    )
                raise APIError(
                    f"股票 {symbol} 的 {func.__name__} 操作失敗: {str(e)}"
                ) from e

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


def with_cache(cache_key_prefix: str = "default", enable_rate_limit: bool = True):
    """
    通用快取裝飾器。

    Args:
        cache_key_prefix: 快取鍵值前綴，用於區分不同類型的資料
        enable_rate_limit: 是否啟用速率限制

    Examples:
        >>> @with_cache("quote", enable_rate_limit=True)
        >>> async def get_stock_quote(self, symbol: str):
        >>>     # 股票報價，需要速率限制
        >>>     pass

        >>> @with_cache("financial", enable_rate_limit=False)
        >>> async def get_financial_data(self, symbol: str):
        >>>     # 財務資料，不需要速率限制（因為資料來源已有限制）
        >>>     pass
    """
    return with_cache_and_rate_limit(
        cache_key_prefix=cache_key_prefix,
        enable_cache=True,
        enable_rate_limit=enable_rate_limit,
    )


def with_endpoint_cache(cache_key_prefix: str = "api", enable_rate_limit: bool = False):
    """
    多參數快取裝飾器，適用於需要基於多個參數生成唯一快取鍵的函數。
    特別適用於 get_company_data(endpoint, symbol) 這類函數。

    Args:
        cache_key_prefix: 快取鍵值前綴
        enable_rate_limit: 是否啟用速率限制

    Examples:
        >>> @with_endpoint_cache("company_data", enable_rate_limit=False)
        >>> async def get_company_data(self, endpoint: str, symbol: str):
        >>>     # Cache key: "company_data_{endpoint_hash}_{symbol}"
        >>>     pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 提取 endpoint 和 symbol
            endpoint = None
            symbol = None
            force_refresh = kwargs.pop("force_refresh", False)

            # 從位置參數提取
            if len(args) >= 3:  # self, endpoint, symbol
                endpoint = args[1]
                symbol = args[2]
            # 從關鍵字參數提取
            if "endpoint" in kwargs:
                endpoint = kwargs["endpoint"]
            if "symbol" in kwargs:
                symbol = kwargs["symbol"]

            if not endpoint or not symbol:
                # 如果無法提取必要參數，直接執行函數
                return await func(*args, **kwargs)

            # 生成包含 endpoint 資訊的快取鍵
            import hashlib

            endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()[:8]
            cache_key_suffix = f"{endpoint_hash}_{symbol}"

            cache_service = _get_cache_service()
            start_time = time.time()

            try:
                if force_refresh:
                    await cache_service.invalidate_symbol_cache(
                        cache_key_suffix, cache_key_prefix
                    )

                if enable_rate_limit:
                    (
                        cached_data,
                        _,
                        message,
                    ) = await cache_service.get_cached_or_wait(
                        cache_key_suffix, cache_key_prefix
                    )

                    if cached_data:
                        response_time = (time.time() - start_time) * 1000
                        await cache_service.record_cached_response(
                            cache_key_suffix, cache_key_prefix
                        )
                        return _parse_cached_response(cached_data["data"])

                    if "cache_miss_can_make_request" not in message:
                        raise APIError(
                            f"API 呼叫 {endpoint} (symbol: {symbol}) 受流量限制: {message}"
                        )

                else:
                    cached_data = await cache_service.cache_manager.get_cached_data(
                        cache_key_suffix, cache_key_prefix
                    )
                    if cached_data and not force_refresh:
                        return _parse_cached_response(cached_data["data"])

                result = await func(*args, **kwargs)
                response_time = (time.time() - start_time) * 1000

                if result is not None:
                    result_dict = _prepare_for_cache(result)
                    if result_dict:
                        await cache_service.record_successful_request(
                            cache_key_suffix,
                            result_dict,
                            response_time,
                            cache_key_prefix,
                        )

                return result

            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                if enable_rate_limit:
                    await cache_service.record_failed_request(
                        cache_key_suffix, response_time, cache_key_prefix
                    )
                raise APIError(
                    f"API 呼叫 {endpoint} (symbol: {symbol}) 失敗: {str(e)}"
                ) from e

        return wrapper

    return decorator


def with_args_cache(
    cache_key_prefix: str = "api",
    enable_rate_limit: bool = False,
    include_args: list[int] | None = None,
    include_kwargs: list[str] | None = None,
):
    """
    多參數快取裝飾器，基於指定的參數生成唯一快取鍵。

    Args:
        cache_key_prefix: 快取鍵值前綴
        enable_rate_limit: 是否啟用速率限制
        include_args: 要包含在 cache key 中的位置參數索引（不包含 self）
        include_kwargs: 要包含在 cache key 中的關鍵字參數名稱

    Examples:
        >>> @with_args_cache("company_data", include_args=[0, 1])  # endpoint, symbol
        >>> async def get_company_data(self, endpoint: str, symbol: str):
        >>>     # Cache key: "company_data_{args_hash}"
        >>>     pass

        >>> @with_args_cache("market", include_kwargs=["category", "count"])
        >>> async def get_market_info(self, category: str = "major", count: int = 20):
        >>>     # Cache key: "market_{kwargs_hash}"
        >>>     pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            force_refresh = kwargs.pop("force_refresh", False)

            # 收集要用於 cache key 的參數
            cache_params = []

            # 包含指定的位置參數（跳過 self，所以索引從 1 開始）
            if include_args:
                for arg_idx in include_args:
                    if arg_idx + 1 < len(args):  # +1 因為跳過 self
                        cache_params.append(str(args[arg_idx + 1]))

            # 包含指定的關鍵字參數
            if include_kwargs:
                for kwarg_name in include_kwargs:
                    if kwarg_name in kwargs:
                        cache_params.append(f"{kwarg_name}:{kwargs[kwarg_name]}")

            # 如果沒有指定參數或無法提取參數，直接執行函數
            if not cache_params:
                return await func(*args, **kwargs)

            # 生成基於所有相關參數的快取鍵
            import hashlib

            params_str = "|".join(cache_params)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:12]
            cache_key_suffix = params_hash

            cache_service = _get_cache_service()
            start_time = time.time()

            try:
                if force_refresh:
                    await cache_service.invalidate_symbol_cache(
                        cache_key_suffix, cache_key_prefix
                    )

                if enable_rate_limit:
                    (
                        cached_data,
                        _,
                        message,
                    ) = await cache_service.get_cached_or_wait(
                        cache_key_suffix, cache_key_prefix
                    )

                    if cached_data:
                        response_time = (time.time() - start_time) * 1000
                        await cache_service.record_cached_response(
                            cache_key_suffix, cache_key_prefix
                        )
                        return _parse_cached_response(cached_data["data"])

                    if "cache_miss_can_make_request" not in message:
                        raise APIError(
                            f"函數 {func.__name__} 呼叫受流量限制: {message}"
                        )

                else:
                    cached_data = await cache_service.cache_manager.get_cached_data(
                        cache_key_suffix, cache_key_prefix
                    )
                    if cached_data and not force_refresh:
                        return _parse_cached_response(cached_data["data"])

                result = await func(*args, **kwargs)
                response_time = (time.time() - start_time) * 1000

                if result is not None:
                    result_dict = _prepare_for_cache(result)
                    if result_dict:
                        await cache_service.record_successful_request(
                            cache_key_suffix,
                            result_dict,
                            response_time,
                            cache_key_prefix,
                        )

                return result

            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                if enable_rate_limit:
                    await cache_service.record_failed_request(
                        cache_key_suffix, response_time, cache_key_prefix
                    )
                raise APIError(f"函數 {func.__name__} 呼叫失敗: {str(e)}") from e

        return wrapper

    return decorator
