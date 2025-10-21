"""
函數裝飾器模組 - 為 API 方法添加快取和速率限制功能。

本模組提供兩個主要裝飾器：
1. @with_rate_limit - 純速率限制裝飾器，適用於需要即時數據的場景
2. @with_cache - 快取裝飾器，支援自動快取和可選的速率限制

設計理念：
- 使用全域單例模式管理快取服務，避免重複初始化
- 支援環境變數配置，提供彈性的參數覆蓋機制
- 自動生成快取鍵，基於函數名稱和參數
- 統一的錯誤處理和請求統計
"""

import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar

from ..cache.rate_limited_cache_service import RateLimitedCacheService
from ..models.stock_data import APIError, TWStockResponse, ValidationError
from ..utils.logging import get_logger

logger = get_logger(__name__)

# 全域快取服務實例，使用延遲初始化模式
_cache_service: RateLimitedCacheService | None = None

# 泛型類型變數，用於保持裝飾器的類型提示
F = TypeVar("F", bound=Callable[..., Any])


def _get_cache_service() -> RateLimitedCacheService:
    """
    取得全域快取服務實例（單例模式）。

    使用延遲初始化（Lazy Initialization）模式，只在第一次呼叫時建立實例。
    這樣可以避免模組載入時就初始化服務，減少啟動時間和資源消耗。

    Returns:
        RateLimitedCacheService: 全域共享的快取服務實例
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = RateLimitedCacheService()
        logger.info("已初始化全域快取服務")
    return _cache_service


def with_rate_limit(
    interval_seconds: float | None = None,
    global_limit_per_minute: int | None = None,
    per_second_limit: int | None = None,
    request_type: str = "api_call",
):
    """
    純限速裝飾器，只提供速率限制功能，不使用快取。
    適用於需要即時數據且不需要快取的情況，如股票即時報價。

    配置優先順序：
    1. 傳入的參數（如果有指定）
    2. 環境變數 (MARKET_MCP_RATE_LIMIT_*)
    3. 預設值 (interval_seconds=30.0, global_limit_per_minute=20, per_second_limit=2)

    Args:
        interval_seconds: 每個symbol的請求間隔秒數（可選，預設由環境變數或30秒）
        global_limit_per_minute: 全域每分鐘請求限制（可選，預設由環境變數或20次）
        per_second_limit: 每秒請求限制（可選，預設由環境變數或2次）
        request_type: 請求類型，用於統計和監控（預設"api_call"）

    Examples:
        >>> @with_rate_limit()  # 使用環境變數配置
        >>> async def get_stock_quote(self, symbol: str):
        >>>     pass

        >>> @with_rate_limit(interval_seconds=10.0)  # 覆蓋特定參數
        >>> async def get_fast_data(self, symbol: str):
        >>>     pass
    """
    import os

    from ..cache.rate_limiter import RateLimiter
    from ..cache.request_tracker import RequestTracker

    # 從環境變數讀取配置，使用統一的預設值
    actual_interval = float(
        os.getenv(
            "MARKET_MCP_RATE_LIMIT_INTERVAL",
            str(interval_seconds) if interval_seconds is not None else "30.0",
        )
    )
    actual_global_limit = int(
        os.getenv(
            "MARKET_MCP_RATE_LIMIT_GLOBAL_PER_MINUTE",
            (
                str(global_limit_per_minute)
                if global_limit_per_minute is not None
                else "20"
            ),
        )
    )
    actual_per_second = int(
        os.getenv(
            "MARKET_MCP_RATE_LIMIT_PER_SECOND",
            str(per_second_limit) if per_second_limit is not None else "2",
        )
    )

    # 創建專用的限速器實例
    rate_limiter = RateLimiter(
        per_stock_interval=actual_interval,
        global_limit_per_minute=actual_global_limit,
        per_second_limit=actual_per_second,
    )

    # 創建請求追蹤器用於統計
    request_tracker = RequestTracker(
        stats_retention_hours=int(
            os.getenv("MARKET_MCP_MONITORING_STATS_RETENTION_HOURS", "24")
        )
    )

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 提取股票代碼作為限速識別碼
            # 假設第一個參數是 self (類實例)，第二個參數是 symbol (股票代碼)
            if len(args) < 2:
                raise APIError(f"函數 {func.__name__} 缺少必要的 symbol 參數")

            symbol = str(args[1])  # args[0] 是 self，args[1] 是 symbol
            start_time = time.time()  # 記錄開始時間，用於計算響應時間

            try:
                # 檢查是否啟用限速功能（透過環境變數控制）
                # 這允許在測試或特殊場景下完全禁用限速
                if (
                    os.getenv("MARKET_MCP_RATE_LIMITING_ENABLED", "true").lower()
                    == "false"
                ):
                    # 如果禁用了限速，直接執行函數，但仍記錄統計數據
                    result = await func(*args, **kwargs)
                    response_time = (time.time() - start_time) * 1000  # 轉換為毫秒

                    # 記錄統計數據（成功，未使用快取）
                    request_id = await request_tracker.record_request_start(
                        symbol, request_type
                    )
                    await request_tracker.record_request_complete(
                        request_id, symbol, True, response_time, False, request_type
                    )
                    return result

                # 檢查是否可以發出請求（限速檢查）
                # 返回：(可否請求, 原因說明, 需等待時間)
                can_request, reason, wait_time = await rate_limiter.can_request(symbol)

                if not can_request:
                    # 超過限速，拋出錯誤並告知等待時間
                    raise APIError(
                        f"函數 {func.__name__} 受流量限制: {reason}，需等待 {wait_time:.1f} 秒"
                    )

                # 通過限速檢查，執行實際的 API 函數
                result = await func(*args, **kwargs)
                response_time = (
                    time.time() - start_time
                ) * 1000  # 計算響應時間（毫秒）

                # 記錄成功的請求到限速器（更新最後請求時間）
                await rate_limiter.record_request(symbol)

                # 記錄統計數據（成功，未使用快取）
                request_id = await request_tracker.record_request_start(
                    symbol, request_type
                )
                await request_tracker.record_request_complete(
                    request_id, symbol, True, response_time, False, request_type
                )

                return result

            except (APIError, ValidationError) as e:
                # 捕捉已知的業務錯誤，記錄統計後重新拋出
                response_time = (time.time() - start_time) * 1000
                request_id = await request_tracker.record_request_start(
                    symbol, request_type
                )
                await request_tracker.record_request_complete(
                    request_id, symbol, False, response_time, False, request_type
                )
                raise e
            except Exception as e:
                # 捕捉未預期的錯誤，包裝成 APIError 後拋出
                response_time = (time.time() - start_time) * 1000
                request_id = await request_tracker.record_request_start(
                    symbol, request_type
                )
                await request_tracker.record_request_complete(
                    request_id, symbol, False, response_time, False, request_type
                )
                raise APIError(f"函數 {func.__name__} 操作失敗: {str(e)}") from e

        return wrapper

    return decorator


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
            # 提取並移除 force_refresh 參數（強制刷新快取）
            force_refresh = kwargs.pop("force_refresh", False)

            # === 自動生成快取鍵 ===
            # 策略：基於函數名稱和所有參數生成唯一識別碼
            cache_params = []

            # 1. 使用自訂前綴或函數名稱作為快取鍵的命名空間
            prefix = cache_key_prefix or func.__name__
            cache_params.append(prefix)

            # 2. 包含所有位置參數（跳過第一個 self 參數）
            if len(args) > 1:  # args[0] 是 self，從 args[1] 開始才是實際參數
                for arg in args[1:]:
                    cache_params.append(str(arg))

            # 3. 包含所有關鍵字參數（force_refresh 已被移除）
            for key, value in kwargs.items():
                if key != "force_refresh":
                    cache_params.append(f"{key}:{value}")

            # 4. 使用 MD5 雜湊生成緊湊的快取鍵（取前16位元組）
            # 格式範例: "get_stock_quote|2330" -> "a1b2c3d4e5f6g7h8"
            import hashlib

            cache_key_str = "|".join(cache_params)
            cache_key = hashlib.md5(cache_key_str.encode()).hexdigest()[:16]

            # 取得快取服務實例
            cache_service = _get_cache_service()
            start_time = time.time()  # 記錄開始時間

            try:
                # 如果要求強制刷新，先清除現有快取
                if force_refresh:
                    await cache_service.invalidate_symbol_cache(cache_key, prefix)

                # === 快取檢查流程 ===
                if enable_rate_limit:
                    # 啟用限速模式：檢查快取並等待限速
                    # 返回值：(快取數據, 是否命中, 訊息)
                    (
                        cached_data,
                        _,
                        message,
                    ) = await cache_service.get_cached_or_wait(cache_key, prefix)

                    if cached_data:
                        # 快取命中！直接返回快取數據，無需呼叫 API
                        logger.info(f"快取命中: {cache_key_str} -> {cache_key}")
                        response_time = (time.time() - start_time) * 1000
                        await cache_service.record_cached_response(cache_key, prefix)
                        return _parse_cached_response(cached_data["data"])

                    # 快取未命中，檢查是否允許發出請求
                    if "cache_miss_can_make_request" not in message:
                        # 被限速阻擋，拋出錯誤
                        raise APIError(f"函數 {func.__name__} 受流量限制: {message}")

                else:
                    # 未啟用限速模式：純快取檢查（不等待）
                    cached_data = await cache_service.cache_manager.get_cached_data(
                        cache_key, prefix
                    )
                    if cached_data and not force_refresh:
                        # 快取命中且未要求強制刷新，直接返回
                        response_time = (time.time() - start_time) * 1000
                        logger.info(
                            f"[快取命中] 函數: {func.__name__}, 快取鍵: {cache_key}, "
                            f"參數: {cache_key_str}, 響應時間: {response_time:.2f}ms"
                        )
                        return _parse_cached_response(cached_data["data"])

                # === 執行實際的 API 呼叫 ===
                result = await func(*args, **kwargs)
                response_time = (
                    time.time() - start_time
                ) * 1000  # 計算響應時間（毫秒）

                # === 儲存結果到快取 ===
                if result is not None:
                    # 將結果轉換為可快取的字典格式
                    result_dict = _prepare_for_cache(result)
                    if result_dict:
                        # 記錄成功請求並儲存快取
                        await cache_service.record_successful_request(
                            cache_key, result_dict, response_time, prefix
                        )
                        logger.info(
                            f"[已快取] 函數: {func.__name__}, 快取鍵: {cache_key}, "
                            f"參數: {cache_key_str}, 響應時間: {response_time:.2f}ms"
                        )

                return result

            except (APIError, ValidationError) as e:
                # 捕捉已知的業務錯誤
                response_time = (time.time() - start_time) * 1000
                if enable_rate_limit:
                    # 記錄失敗請求（用於統計和監控）
                    await cache_service.record_failed_request(
                        cache_key, response_time, prefix
                    )
                raise e
            except Exception as e:
                # 捕捉未預期的錯誤，包裝成 APIError
                response_time = (time.time() - start_time) * 1000
                if enable_rate_limit:
                    await cache_service.record_failed_request(
                        cache_key, response_time, prefix
                    )
                raise APIError(f"函數 {func.__name__} 操作失敗: {str(e)}") from e

        return wrapper

    return decorator


def _prepare_for_cache(result: Any) -> dict | None:
    """
    準備資料以供快取使用，將各種類型的結果轉換為可序列化的字典。

    轉換策略：
    1. TWStockResponse 物件 -> 手動轉換為字典（確保所有欄位都包含）
    2. 已經是字典 -> 直接返回
    3. 其他物件 -> 嘗試使用 __dict__ 屬性
    4. 無法轉換 -> 返回 None（不快取）

    Args:
        result: 要快取的結果資料（可以是任何類型）

    Returns:
        dict | None: 可序列化的字典，或 None（無法快取）
    """
    try:
        if isinstance(result, TWStockResponse):
            # 手動提取 TWStockResponse 的所有欄位
            # 注意：datetime 物件需要轉換為 ISO 格式字串以便序列化
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
                "update_time": result.update_time.isoformat(),  # datetime -> string
                "last_trade_time": result.last_trade_time,
            }
        elif isinstance(result, dict):
            # 已經是字典，直接返回
            return result
        elif isinstance(result, list):
            # 列表類型（如 get_data 返回的資料），直接返回
            return {"data": result, "type": "list"}
        else:
            # 嘗試使用物件的 __dict__ 屬性
            if hasattr(result, "__dict__"):
                return result.__dict__
            # 無法轉換，不快取
            return None
    except Exception:
        # 轉換過程中發生錯誤，安全地返回 None
        return None


def _parse_cached_response(data: dict) -> Any:
    """
    解析快取數據，將字典還原為原始物件類型。

    解析策略：
    1. 檢查是否為 TWStockResponse 的資料（透過特徵欄位判斷）
    2. 如果是，將 ISO 格式的時間字串還原為 datetime 物件
    3. 使用字典解包建立 TWStockResponse 物件
    4. 如果不是，直接返回字典

    Args:
        data: 從快取中讀取的字典資料

    Returns:
        Any: 還原的物件（TWStockResponse 或原始字典）
    """
    try:
        # 檢查是否為列表類型的快取資料
        if "type" in data and data["type"] == "list":
            # 還原列表資料
            return data["data"]
        # 透過特徵欄位判斷是否為 TWStockResponse 資料
        elif "company_name" in data and "current_price" in data:
            # 將時間字串還原為 datetime 物件
            if isinstance(data.get("update_time"), str):
                from datetime import datetime

                data["update_time"] = datetime.fromisoformat(data["update_time"])
            # 使用字典解包建立 TWStockResponse 物件
            return TWStockResponse(**data)
        else:
            # 不是 TWStockResponse，直接返回字典
            return data
    except Exception:
        # 解析失敗，安全地返回原始字典
        return data
        return data
