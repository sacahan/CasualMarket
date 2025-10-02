"""
台灣證券交易所 API 客戶端。

提供與台灣證交所即時股價 API 的整合功能，包含請求發送、
回應處理、錯誤重試等機制。
"""

from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime
from typing import Any

import httpx

from ..models.stock_data import (
    APIError,
    StockQuoteRequest,
    TWAPIRawResponse,
    TWStockResponse,
    ValidationError,
)
from ..parsers.twse_parser import create_parser
from ..securities_db import get_securities_database
from ..utils.logging import get_logger
from ..utils.validators import determine_market_type, validate_taiwan_stock_symbol
from .decorators import with_cache

# 設置日誌
logger = get_logger(__name__)


class TWStockAPIClient:
    """
    台灣證券交易所 API 客戶端。

    負責處理與證交所 API 的通信，包含請求建構、發送、
    回應解析和錯誤處理。
    """

    def __init__(self, enable_cache: bool = True, enable_rate_limit: bool = True):
        """初始化 API 客戶端。"""
        logger.debug("初始化 TWStockAPIClient")

        self.enable_cache = enable_cache
        self.enable_rate_limit = enable_rate_limit

        # 從環境變數讀取配置，如果沒有則使用默認值
        self.base_url = os.getenv(
            "MARKET_MCP_TWSE_API_URL",
            "https://mis.twse.com.tw/stock/api/getStockInfo.jsp",
        )
        self.timeout = float(os.getenv("MARKET_MCP_API_TIMEOUT", "5.0"))
        self.max_retries = int(os.getenv("MARKET_MCP_API_RETRIES", "3"))
        self.parser = create_parser()

        logger.debug(
            f"API 配置 - URL: {self.base_url}, timeout: {self.timeout}s, max_retries: {self.max_retries}"
        )

        # 設定 HTTP 客戶端標頭
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://mis.twse.com.tw/stock/fibest.jsp",
        }

        logger.debug("TWStockAPIClient 初始化完成")

from .decorators import (
    _get_cache_service,
    _parse_cached_response,
    _prepare_for_cache,
)

# 設置日誌
logger = get_logger(__name__)


class TWStockAPIClient:
    """
    台灣證券交易所 API 客戶端。

    負責處理與證交所 API 的通信，包含請求建構、發送、
    回應解析和錯誤處理。
    """

    def __init__(self, enable_cache: bool = True, enable_rate_limit: bool = True):
        """初始化 API 客戶端。"""
        logger.debug("初始化 TWStockAPIClient")

        self.enable_cache = enable_cache
        self.enable_rate_limit = enable_rate_limit

        # 從環境變數讀取配置，如果沒有則使用默認值
        self.base_url = os.getenv(
            "MARKET_MCP_TWSE_API_URL",
            "https://mis.twse.com.tw/stock/api/getStockInfo.jsp",
        )
        self.timeout = float(os.getenv("MARKET_MCP_API_TIMEOUT", "5.0"))
        self.max_retries = int(os.getenv("MARKET_MCP_API_RETRIES", "3"))
        self.parser = create_parser()

        logger.debug(
            f"API 配置 - URL: {self.base_url}, timeout: {self.timeout}s, max_retries: {self.max_retries}"
        )

        # 設定 HTTP 客戶端標頭
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://mis.twse.com.tw/stock/fibest.jsp",
        }

        logger.debug("TWStockAPIClient 初始化完成")

    async def get_stock_quote(
        self, symbol: str, market: str | None = None, force_refresh: bool = False
    ) -> TWStockResponse:
        """
        取得單一股票即時報價。

        Args:
            symbol: 股票代號或公司名稱
            market: 市場類型 ('tse' 或 'otc')，如果未指定會自動判斷
            force_refresh: 是否強制刷新快取

        Returns:
            TWStockResponse: 股票報價資料

        Raises:
            ValidationError: 股票代號格式不正確或找不到該股票
            APIError: API 請求失敗
        """
        cache_key_prefix = "quote"
        start_time = time.time()

        if self.enable_cache:
            cache_service = _get_cache_service()
            if force_refresh:
                await cache_service.invalidate_symbol_cache(symbol, cache_key_prefix)

            if self.enable_rate_limit:
                cached_data, _, message = await cache_service.get_cached_or_wait(
                    symbol, cache_key_prefix
                )

                if cached_data:
                    response_time = (time.time() - start_time) * 1000
                    await cache_service.record_cached_response(symbol, cache_key_prefix)
                    return _parse_cached_response(cached_data["data"])

                if "cache_miss_can_make_request" not in message:
                    raise APIError(f"股票 {symbol} 受流量限制: {message}")
            else:
                cached_data = await cache_service.cache_manager.get_cached_data(
                    symbol, cache_key_prefix
                )
                if cached_data and not force_refresh:
                    return _parse_cached_response(cached_data["data"])

        logger.info(f"開始查詢股票報價: {symbol}")

        # 嘗試使用資料庫解析股票代碼或公司名稱
        securities_db = get_securities_database()
        resolved_symbol = None

        if securities_db:
            try:
                # 使用資料庫搜尋功能
                results = securities_db.search_securities(symbol)
                if results:
                    resolved_symbol = results[0].stock_code
                    logger.info(
                        f"從資料庫解析: {symbol} -> {resolved_symbol} ({results[0].company_name})"
                    )
                else:
                    logger.warning(f"在資料庫中找不到: {symbol}")
                    raise ValidationError(f"無效的股票代號格式: {symbol}") from None
            except ValidationError:
                # 重新拋出 ValidationError
                raise
            except Exception as e:
                logger.error(f"資料庫查詢失敗: {symbol} - {e}")
                raise ValidationError(f"無效的股票代號格式: {symbol}") from e
        else:
            # 如果資料庫不可用，退回到格式驗證
            logger.warning("證券資料庫不可用，使用格式驗證")
            if not validate_taiwan_stock_symbol(symbol):
                logger.error(f"股票代號格式驗證失敗: {symbol}")
                raise ValidationError(f"無效的股票代號格式: {symbol}")
            resolved_symbol = symbol

        # 自動判斷市場類型
        if market is None:
            market = determine_market_type(resolved_symbol)
            logger.debug(f"自動判斷市場類型: {resolved_symbol} -> {market}")
        else:
            logger.debug(f"使用指定市場類型: {resolved_symbol} -> {market}")

        # 建立請求物件
        request = StockQuoteRequest(symbol=resolved_symbol, market=market)
        logger.debug(f"建立股票報價請求: {request}")

        try:
            # 發送 API 請求
            raw_response = await self._make_api_request(request)
            logger.debug(f"API 請求成功，回應大小: {len(str(raw_response))} 字元")

            # 解析回應資料
            stock_data_list = self.parser.parse_stock_data(raw_response)

            if not stock_data_list:
                logger.warning(f"API 回應中找不到股票 {resolved_symbol} 的資料")
                raise APIError(f"找不到股票 {resolved_symbol} 的資料")

            stock_data = stock_data_list[0]
            logger.info(
                f"成功取得股票報價: {resolved_symbol} ({stock_data.company_name}) = ${stock_data.current_price}"
            )

            if self.enable_cache:
                cache_service = _get_cache_service()
                result_dict = _prepare_for_cache(stock_data)
                if result_dict:
                    response_time = (time.time() - start_time) * 1000
                    await cache_service.record_successful_request(
                        symbol, result_dict, response_time, cache_key_prefix
                    )

            return stock_data

        except (ValidationError, APIError):
            # 重新拋出已知的業務邏輯錯誤
            raise
        except Exception as e:
            logger.error(f"查詢股票報價時發生未預期錯誤: {resolved_symbol} - {e}")
            raise APIError(f"查詢股票 {resolved_symbol} 時發生錯誤: {e}") from e

    async def get_multiple_quotes(self, symbols: list[str]) -> list[TWStockResponse]:
        """
        取得多支股票的即時報價。

        Args:
            symbols: 股票代號清單

        Returns:
            list[TWStockResponse]: 股票報價資料清單
        """
        logger.info(f"開始批量查詢股票報價，共 {len(symbols)} 支股票: {symbols}")

        tasks = []
        for symbol in symbols:
            task = self.get_stock_quote(symbol)
            tasks.append(task)

        # 並行處理多個請求
        logger.debug(f"開始並行處理 {len(tasks)} 個查詢任務")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 過濾掉異常結果，只返回成功的資料
        valid_results = []
        failed_symbols = []
        for i, result in enumerate(results):
            if isinstance(result, TWStockResponse):
                valid_results.append(result)
                logger.debug(f"成功查詢: {symbols[i]} -> {result.company_name}")
            else:
                failed_symbols.append(symbols[i])
                logger.warning(f"查詢失敗: {symbols[i]} - {result}")

        logger.info(
            f"批量查詢完成 - 成功: {len(valid_results)}, 失敗: {len(failed_symbols)}"
        )
        if failed_symbols:
            logger.warning(f"失敗的股票代號: {failed_symbols}")

        return valid_results

    async def _make_api_request(self, request: StockQuoteRequest) -> TWAPIRawResponse:
        """
        發送 API 請求並處理重試邏輯。

        Args:
            request: 股票報價請求

        Returns:
            TWAPIRawResponse: API 原始回應

        Raises:
            APIError: API 請求失敗且重試次數用盡
        """
        logger.debug(f"開始 API 請求，最大重試次數: {self.max_retries}")
        last_exception = None

        for attempt in range(self.max_retries):
            logger.debug(
                f"API 請求嘗試 {attempt + 1}/{self.max_retries}: {request.symbol}"
            )
            try:
                response = await self._send_http_request(request)
                logger.debug(f"API 請求成功 (嘗試 {attempt + 1}): {request.symbol}")
                return response
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                logger.warning(
                    f"API 請求失敗 (嘗試 {attempt + 1}): {type(e).__name__} - {e}"
                )
                if attempt < self.max_retries - 1:
                    # 指數退避重試
                    wait_time = 2**attempt
                    logger.debug(f"等待 {wait_time}s 後重試...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    break
            except Exception as e:
                # 其他錯誤不重試
                logger.error(f"API 請求發生不可重試的錯誤: {type(e).__name__} - {e}")
                raise APIError(f"API 請求失敗: {e}") from e

        # 所有重試都失敗
        logger.error(
            f"API 請求失敗，已重試 {self.max_retries} 次，最後錯誤: {last_exception}"
        )
        raise APIError(
            f"API 請求失敗，已重試 {self.max_retries} 次"
        ) from last_exception

    async def _send_http_request(self, request: StockQuoteRequest) -> TWAPIRawResponse:
        """
        發送 HTTP 請求到證交所 API。

        Args:
            request: 股票報價請求

        Returns:
            TWAPIRawResponse: API 原始回應

        Raises:
            APIError: HTTP 請求失敗或回應格式錯誤
        """
        # 建構查詢參數
        params = self._build_query_params(request)
        logger.debug(f"建構查詢參數: {params}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.debug(f"發送 HTTP GET 請求到 {self.base_url}")
                response = await client.get(
                    self.base_url, params=params, headers=self.headers
                )

                logger.debug(
                    f"收到 HTTP 回應，狀態碼: {response.status_code}, 大小: {len(response.content)} bytes"
                )

                # 檢查 HTTP 狀態碼
                if response.status_code != 200:
                    logger.error(f"API 回應狀態碼異常: {response.status_code}")
                    raise APIError(
                        f"API 回應錯誤，狀態碼: {response.status_code}",
                        status_code=response.status_code,
                    )

                # 解析 JSON 回應
                try:
                    json_data = response.json()
                    logger.debug(
                        f"成功解析 JSON 回應，鍵值: {list(json_data.keys()) if isinstance(json_data, dict) else type(json_data)}"
                    )
                except Exception as e:
                    logger.error(f"JSON 解析失敗: {e}")
                    raise APIError(f"無法解析 JSON 回應: {e}") from e

                # 驗證回應格式
                parsed_response = self.parser.parse_raw_response(json_data)
                logger.debug("成功解析 API 回應")
                return parsed_response

            except httpx.TimeoutException as e:
                logger.error(f"HTTP 請求超時: {e}")
                raise APIError(f"請求超時: {e}") from e
            except httpx.ConnectError as e:
                logger.error(f"HTTP 連線錯誤: {e}")
                raise APIError(f"連線錯誤: {e}") from e
            except Exception as e:
                logger.error(f"HTTP 請求發生未預期錯誤: {type(e).__name__} - {e}")
                raise APIError(f"HTTP 請求失敗: {e}") from e

    def _build_query_params(self, request: StockQuoteRequest) -> dict[str, Any]:
        """
        建構 API 查詢參數。

        Args:
            request: 股票報價請求

        Returns:
            dict: 查詢參數字典
        """
        # 根據市場類型建構 ex_ch 參數
        ex_ch = f"{request.market}_{request.symbol}.tw"
        timestamp = str(int(datetime.now().timestamp() * 1000))

        params = {
            "ex_ch": ex_ch,
            "json": "1",
            "delay": "0",
            "_": timestamp,  # 時間戳避免快取
        }

        logger.debug(f"建構查詢參數完成 - ex_ch: {ex_ch}, timestamp: {timestamp}")
        return params

    async def check_api_health(self) -> bool:
        """
        檢查 API 服務健康狀態。

        Returns:
            bool: API 是否可用

        Examples:
            >>> client = TWStockAPIClient()
            >>> await client.check_api_health()
            True
        """
        logger.info("開始 API 健康檢查")
        try:
            # 使用台積電 (2330) 作為健康檢查標的
            stock_data = await self.get_stock_quote("2330")
            logger.info(
                f"API 健康檢查通過 - 成功取得 2330 資料: {stock_data.company_name}"
            )
            return True
        except Exception as e:
            logger.error(f"API 健康檢查失敗: {e}")
            return False

    def close(self):
        """關閉 HTTP 客戶端連線。"""
        # httpx AsyncClient 會自動清理連線
        logger.debug("關閉 TWStockAPIClient")

    async def __aenter__(self):
        """非同步內容管理器進入。"""
        logger.debug("進入 TWStockAPIClient 內容管理器")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同步內容管理器退出。"""
        logger.debug("退出 TWStockAPIClient 內容管理器")
        self.close()


def create_client(
    enable_cache: bool = True,
    enable_rate_limit: bool = True,
) -> TWStockAPIClient:
    """
    建立台灣證交所 API 客戶端實例。

    Args:
        enable_cache: 是否啟用快取
        enable_rate_limit: 是否啟用速率限制

    Returns:
        TWStockAPIClient: 帶有或不帶快取和速率限制功能的 API 客戶端實例
    """
    logger.debug(
        f"建立 TWStockAPIClient 實例 (快取: {enable_cache}, 速率限制: {enable_rate_limit})"
    )
    return TWStockAPIClient(enable_cache=enable_cache, enable_rate_limit=enable_rate_limit)


# 增加 main 函式以便直接執行測試
if __name__ == "__main__":
    import asyncio
    import os
    import sys

    # 直接讀取 .env 文件中的環境變數
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    env_path = os.path.join(project_root, ".env")

    # 手動讀取 .env 文件
    if os.path.exists(env_path):
        print(f"讀取環境變數從: {env_path}")
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
                    print(f"設定環境變數: {key}={value}")
    else:
        print(f"未找到 .env 文件: {env_path}")

    # 將專案根目錄加入 Python 路徑，讓相對引入可以正常運作
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    async def main():
        client = create_client()
        try:
            quote = await client.get_stock_quote("1101")  # 台泥
            print("成功取得股票資料:")
            print(f"公司名稱: {quote.company_name}")
            print(f"股票代號: {quote.symbol}")
            print(f"目前價格: ${quote.current_price}")
            print(f"漲跌幅: {quote.change:+.2f} ({quote.change_percent * 100:+.2f}%)")
            print(f"成交量: {quote.volume:,}")
            print(f"開盤價: ${quote.open_price}")
            print(f"最高價: ${quote.high_price}")
            print(f"最低價: ${quote.low_price}")
            print(f"昨收價: ${quote.previous_close}")
        except Exception as e:
            print(f"錯誤: {e}")
        finally:
            client.close()

    asyncio.run(main())
