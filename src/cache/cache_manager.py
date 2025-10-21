"""
高效能快取管理器，採用 TTL（存活時間）策略。
實作台灣證券交易所 API 回應的智慧型快取。
"""

import logging
import sys
import time
from threading import RLock
from typing import Any

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class CacheManager:
    """
    基於 TTL 的快取管理器，具備記憶體用量控管。
    目標：快取命中率 80%，記憶體用量低於 200MB。
    """

    def __init__(
        self,
        ttl_seconds: int = 30,
        max_size: int = 1000,
        max_memory_mb: float = 200.0,
    ):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.max_memory_mb = max_memory_mb

        # Thread-safe TTL cache
        self.cache = TTLCache(maxsize=max_size, ttl=ttl_seconds)
        self.cache_lock = RLock()

        # Statistics tracking
        self.hit_count = 0
        self.miss_count = 0
        self.stats_lock = RLock()

    def _generate_cache_key(self, symbol: str, request_type: str = "quote") -> str:
        """
        產生此請求的唯一快取鍵。
        """
        return f"{request_type}:{symbol.upper()}"

    def _estimate_memory_usage(self) -> float:
        """
        估算目前記憶體用量（MB）。
        """
        try:
            # Get the size of the cache object
            cache_size = sys.getsizeof(self.cache)

            # Estimate size of cached data
            data_size = 0
            with self.cache_lock:
                # TTLCache uses internal data structure
                for key, value in self.cache.items():
                    data_size += sys.getsizeof(key) + sys.getsizeof(value)

            total_mb = (cache_size + data_size) / (1024 * 1024)
            return total_mb
        except Exception as e:
            logger.warning(f"無法估算記憶體使用量: {e}")
            return 0.0

    async def get_cached_data(
        self, symbol: str, request_type: str = "quote"
    ) -> dict | None:
        """
        取得指定股票代號的快取資料。
        若未找到或已過期則回傳 None。
        """
        cache_key = self._generate_cache_key(symbol, request_type)

        with self.cache_lock:
            try:
                data = self.cache.get(cache_key)
                if data is not None:
                    with self.stats_lock:
                        self.hit_count += 1

                    # 詳細的快取命中日誌
                    cached_at = data.get("cached_at", 0)
                    ttl = data.get("ttl_seconds", self.ttl_seconds)
                    age_seconds = time.time() - cached_at
                    data_size = sys.getsizeof(data.get("data"))

                    logger.info(
                        f"快取命中 [{cache_key}] - "
                        f"年齡: {age_seconds:.1f}s/{ttl}s, "
                        f"大小: {data_size} bytes, "
                        f"命中率: {self.hit_count}/{self.hit_count + self.miss_count}"
                    )
                    logger.debug(f"快取數據詳情: {cache_key} = {data}")
                    return data
                else:
                    with self.stats_lock:
                        self.miss_count += 1

                    logger.info(
                        f"快取未命中 [{cache_key}] - "
                        f"命中率: {self.hit_count}/{self.hit_count + self.miss_count}"
                    )
                    return None
            except Exception as e:
                logger.error(f"取得快取資料時發生錯誤 {cache_key}: {e}", exc_info=True)
                with self.stats_lock:
                    self.miss_count += 1
                return None

    async def set_cached_data(
        self, symbol: str, data: dict, request_type: str = "quote"
    ) -> bool:
        """
        將資料存入快取並設定 TTL。
        快取成功回傳 True，否則回傳 False。
        """
        cache_key = self._generate_cache_key(symbol, request_type)

        # Check memory usage before adding new data
        current_memory = self._estimate_memory_usage()
        if current_memory > self.max_memory_mb:
            logger.warning(
                f"記憶體使用量 ({current_memory:.1f}MB) 超過限制 "
                f"({self.max_memory_mb}MB)。不快取新資料。"
            )
            return False

        with self.cache_lock:
            try:
                # Add metadata to cached data
                enriched_data = {
                    "symbol": symbol.upper(),
                    "request_type": request_type,
                    "cached_at": time.time(),
                    "ttl_seconds": self.ttl_seconds,
                    "data": data,
                }

                self.cache[cache_key] = enriched_data
                logger.debug(f"已快取資料: {cache_key}")
                return True
            except Exception as e:
                logger.error(f"快取資料時發生錯誤 {cache_key}: {e}")
                return False

    async def invalidate(self, symbol: str, request_type: str = "quote") -> bool:
        """
        移除指定資料的快取。
        """
        cache_key = self._generate_cache_key(symbol, request_type)

        with self.cache_lock:
            try:
                if cache_key in self.cache:
                    del self.cache[cache_key]
                    logger.debug(f"已失效快取: {cache_key}")
                    return True
                return False
            except Exception as e:
                logger.error(f"失效快取時發生錯誤 {cache_key}: {e}")
                return False

    async def clear_all(self) -> None:
        """
        清除所有快取資料。
        """
        with self.cache_lock:
            self.cache.clear()

        with self.stats_lock:
            self.hit_count = 0
            self.miss_count = 0

        logger.info("快取已完全清除")

    def get_cache_stats(self) -> dict[str, Any]:
        """
        取得快取詳細統計資訊。
        """
        with self.stats_lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = (
                (self.hit_count / total_requests * 100) if total_requests > 0 else 0.0
            )

        with self.cache_lock:
            cache_size = len(self.cache)
            memory_usage = self._estimate_memory_usage()

        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_entries": cache_size,
            "max_entries": self.max_size,
            "memory_usage_mb": round(memory_usage, 2),
            "memory_limit_mb": self.max_memory_mb,
            "ttl_seconds": self.ttl_seconds,
        }

    def is_cache_healthy(self) -> tuple[bool, list[str]]:
        """
        檢查快取是否在可接受參數範圍內運作。
        回傳 (是否健康, 問題列表)
        """
        issues = []
        stats = self.get_cache_stats()

        # Check hit rate (target: 80%+)
        if stats["total_requests"] > 10 and stats["hit_rate_percent"] < 80.0:
            issues.append(f"命中率偏低: {stats['hit_rate_percent']}% (目標: 80%+)")

        # Check memory usage
        if stats["memory_usage_mb"] > stats["memory_limit_mb"]:
            issues.append(
                f"記憶體使用量超標: {stats['memory_usage_mb']}MB "
                f"(限制: {stats['memory_limit_mb']}MB)"
            )

        # Check cache utilization
        utilization = (stats["cache_entries"] / stats["max_entries"]) * 100
        if utilization > 95.0:
            issues.append(
                f"快取即將滿載: {utilization:.1f}% "
                f"({stats['cache_entries']}/{stats['max_entries']})"
            )

        return len(issues) == 0, issues

    async def get_all_cached_symbols(self) -> list[str]:
        """
        取得目前所有已快取的股票代號列表。
        """
        symbols = set()

        with self.cache_lock:
            for key in self.cache.keys():
                # Extract symbol from cache key format "request_type:SYMBOL"
                if ":" in key:
                    symbol = key.split(":", 1)[1]
                    symbols.add(symbol)

        return sorted(symbols)
