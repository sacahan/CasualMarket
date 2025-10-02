"""
Multi-layered API rate limiting mechanism for protecting Taiwan Stock Exchange API.
Implements per-stock, global, and per-second rate limiting.
"""

import logging
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Multi-layered rate limiter with the following constraints:
    - Per stock: 1 request per 30 seconds
    - Global: 20 requests per minute
    - Per second: 2 requests maximum
    """

    def __init__(
        self,
        per_stock_interval: float = 30.0,  # 30 seconds per stock
        global_limit_per_minute: int = 20,  # 20 requests per minute
        per_second_limit: int = 2,  # 2 requests per second
    ):
        self.per_stock_interval = per_stock_interval
        self.global_limit_per_minute = global_limit_per_minute
        self.per_second_limit = per_second_limit

        # Per-stock tracking
        self.last_request_time: dict[str, float] = defaultdict(float)
        self.stock_lock = Lock()

        # Global request tracking (sliding window)
        self.global_requests: deque = deque()
        self.global_lock = Lock()

        # Per-second tracking
        self.per_second_requests: deque = deque()
        self.per_second_lock = Lock()

    def _clean_old_requests(self, request_deque: deque, time_window: float) -> None:
        """Remove requests older than time_window seconds."""
        current_time = time.time()
        while request_deque and request_deque[0] <= current_time - time_window:
            request_deque.popleft()

    def can_request_stock(self, symbol: str) -> tuple[bool, float]:
        """
        Check if we can make a request for a specific stock.
        Returns (can_request, wait_time_seconds)
        """
        with self.stock_lock:
            current_time = time.time()
            last_request = self.last_request_time.get(symbol, 0)
            time_since_last = current_time - last_request

            if time_since_last >= self.per_stock_interval:
                return True, 0.0
            else:
                wait_time = self.per_stock_interval - time_since_last
                return False, wait_time

    def can_request_global(self) -> tuple[bool, float]:
        """
        Check global rate limit (20 requests per minute).
        Returns (can_request, wait_time_seconds)
        """
        with self.global_lock:
            current_time = time.time()
            self._clean_old_requests(self.global_requests, 60.0)  # 1 minute window

            if len(self.global_requests) < self.global_limit_per_minute:
                return True, 0.0
            else:
                # Calculate wait time until oldest request expires
                oldest_request = self.global_requests[0]
                wait_time = 60.0 - (current_time - oldest_request)
                return False, max(0, wait_time)

    def can_request_per_second(self) -> tuple[bool, float]:
        """
        檢查每秒的請求限制（每秒最多 2 次請求）。
        返回 (can_request, wait_time_seconds)
        """
        with self.per_second_lock:
            current_time = time.time()
            self._clean_old_requests(self.per_second_requests, 1.0)  # 1 秒的時間窗口

            if len(self.per_second_requests) < self.per_second_limit:
                return True, 0.0
            else:
                # 計算直到最舊請求過期的等待時間
                oldest_request = self.per_second_requests[0]
                wait_time = 1.0 - (current_time - oldest_request)
                return False, max(0, wait_time)

    async def can_request(self, symbol: str) -> tuple[bool, str, float]:
        """
        檢查是否可以對特定股票進行請求，並檢查所有的流量限制。
        返回 (can_request, reason, max_wait_time_seconds)
        """
        # 檢查所有流量限制
        stock_ok, stock_wait = self.can_request_stock(symbol)
        global_ok, global_wait = self.can_request_global()
        per_sec_ok, per_sec_wait = self.can_request_per_second()

        # 找到最嚴格的限制
        max_wait = max(stock_wait, global_wait, per_sec_wait)

        if stock_ok and global_ok and per_sec_ok:
            return True, "allowed", 0.0

        # 確定是哪個限制阻止了請求
        if not stock_ok and stock_wait == max_wait:
            reason = f"stock_limit_exceeded_for_{symbol}"
        elif not global_ok and global_wait == max_wait:
            reason = "global_limit_exceeded"
        else:
            reason = "per_second_limit_exceeded"

        return False, reason, max_wait

    async def record_request(self, symbol: str) -> None:
        """記錄對特定股票的請求。"""
        current_time = time.time()

        # 記錄每支股票的請求
        with self.stock_lock:
            self.last_request_time[symbol] = current_time

        # 記錄全域請求
        with self.global_lock:
            self.global_requests.append(current_time)
            self._clean_old_requests(self.global_requests, 60.0)

        # 記錄每秒請求
        with self.per_second_lock:
            self.per_second_requests.append(current_time)
            self._clean_old_requests(self.per_second_requests, 1.0)

        logger.debug(f"已記錄股票 {symbol} 的 API 請求")

    def get_stats(self) -> dict[str, Any]:
        """獲取當前流量限制器的統計資訊。"""
        current_time = time.time()

        with self.global_lock:
            self._clean_old_requests(self.global_requests, 60.0)
            global_requests_count = len(self.global_requests)

        with self.per_second_lock:
            self._clean_old_requests(self.per_second_requests, 1.0)
            per_second_count = len(self.per_second_requests)

        with self.stock_lock:
            tracked_stocks = len(self.last_request_time)

        return {
            "global_requests_last_minute": global_requests_count,
            "global_limit_per_minute": self.global_limit_per_minute,
            "requests_last_second": per_second_count,
            "per_second_limit": self.per_second_limit,
            "tracked_stocks_count": tracked_stocks,
            "per_stock_interval_seconds": self.per_stock_interval,
        }

    def reset_limits(self) -> None:
        """重置所有流量限制計數器。使用時需謹慎。"""
        with self.stock_lock:
            self.last_request_time.clear()

        with self.global_lock:
            self.global_requests.clear()

        with self.per_second_lock:
            self.per_second_requests.clear()

        logger.info("流量限制計數器已重置")
