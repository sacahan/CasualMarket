"""
台灣證券交易所 OpenAPI 客戶端，整合快取和速率限制功能。

擴展現有的增強架構，提供全面的台灣證交所資料存取服務。
"""

from typing import Any

import httpx

from ..utils.logging import get_logger
from .decorators import with_cache

logger = get_logger(__name__)


class OpenAPIClient:
    """
    台灣證交所 OpenAPI 客戶端，整合快取和速率限制功能。

    與增強型 TWStockAPIClient 架構協同工作。
    """

    BASE_URL = "https://openapi.twse.com.tw/v1"
    USER_AGENT = "CasualMarket-MCP/2.0"

    def __init__(self):
        """初始化 OpenAPI 客戶端。"""
        logger.debug("初始化 OpenAPIClient")
        self.session = httpx.Client(
            headers={"User-Agent": self.USER_AGENT, "Accept": "application/json"},
            timeout=30.0,
            verify=False,  # SSL verification bypass for TWSE compatibility
        )

        logger.debug(f"OpenAPIClient 初始化完成，基礎 URL: {self.BASE_URL}")
        logger.debug(
            f"HTTP Client 設定: User-Agent={self.USER_AGENT}, timeout=30.0s, verify=False"
        )

    @with_cache(enable_rate_limit=False)
    async def get_data(self, endpoint: str) -> list[dict[str, Any]]:
        """
        從台灣證交所 OpenAPI 端點取得資料，具備快取和速率限制功能。

        Args:
            endpoint: API 端點路徑（例如："/opendata/t187ap03_L"）

        Returns:
            包含 API 回應資料的字典清單
        """
        # 簡化的直接取得方式 - 快取和速率限制由裝飾器處理
        url = f"{self.BASE_URL}{endpoint}"
        logger.info(f"請求 OpenAPI 資料: {url}")

        try:
            response = self.session.get(url)
            response.raise_for_status()

            # 確保使用 UTF-8 編碼
            response.encoding = "utf-8"
            data = response.json()

            logger.debug(f"請求成功，狀態碼: {response.status_code}")
            # 正規化回應格式
            result = data if isinstance(data, list) else [data] if data else []
            logger.info(f"OpenAPI 請求完成: {endpoint}，取得 {len(result)} 筆資料")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 狀態錯誤: {url} - {e.response.status_code}: {e}")
            raise Exception(f"API 請求失敗: {e}") from e
        except Exception as e:
            logger.error(f"請求失敗: {url} - {type(e).__name__}: {e}")
            raise Exception(f"取得資料失敗: {e}") from e

    async def get_company_data(
        self, endpoint: str, symbol: str
    ) -> dict[str, Any] | None:
        """
        從台灣證交所 OpenAPI 取得公司特定資料。

        Args:
            endpoint: API 端點路徑
            symbol: 公司股票代號

        Returns:
            包含公司資料的字典，或 None（如果找不到）
        """
        try:
            data = await self.get_data(endpoint)

            # 根據公司代號篩選資料
            filtered_data = [
                item
                for item in data
                if isinstance(item, dict)
                and (
                    item.get("公司代號") == symbol
                    or item.get("Code") == symbol
                    or item.get("證券代號") == symbol
                )
            ]

            result = filtered_data[0] if filtered_data else None
            logger.debug(f"公司 {symbol} 的資料: {'找到' if result else '未找到'}")
            return result

        except Exception as e:
            logger.error(f"取得公司 {symbol} 資料失敗: {e}")
            return None

    async def get_latest_market_data(
        self, endpoint: str, count: int | None = None
    ) -> list[dict[str, Any]]:
        """
        從台灣證交所 OpenAPI 取得最新市場資料。

        Args:
            endpoint: API 端點路徑
            count: 要返回的最新記錄數量。如果為 None，則返回所有記錄。

        Returns:
            最新市場資料記錄清單
        """
        try:
            data = await self.get_data(endpoint)

            # 返回最新記錄或所有資料（如果 count 為 None）
            result = data[-count:] if data and count is not None else data
            logger.debug(f"從 {endpoint} 取得市場資料: {len(result)} 筆記錄")
            return result

        except Exception as e:
            logger.error(f"取得最新市場資料失敗: {e}")
            return []

    async def get_industry_api_suffix(self, symbol: str) -> str:
        """
        根據公司產業別取得適當的 API 後綴。

        Args:
            symbol: 公司股票代號

        Returns:
            該公司產業別對應的 API 後綴
        """
        try:
            profile_data = await self.get_company_data("/opendata/t187ap03_L", symbol)

            if not profile_data:
                return "_ci"  # 預設為一般業

            industry = profile_data.get("產業別", "")

            # 產業別對應 API 後綴的映射
            industry_mapping = {
                "金融業": "_basi",
                "證券期貨業": "_bd",
                "金控業": "_fh",
                "保險業": "_ins",
                "異業": "_mim",
                "一般業": "_ci",
            }

            # 檢查產業別是否完全符合或包含任何關鍵字
            for industry_key, suffix in industry_mapping.items():
                if industry_key in industry or industry == industry_key:
                    return suffix

            return "_ci"  # 如果沒有符合，預設為一般業

        except Exception as e:
            logger.error(f"判斷公司 {symbol} 產業別時發生錯誤: {e}")
            return "_ci"  # 發生錯誤時預設為一般業

    def close(self):
        """關閉 HTTP 會話。"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
