"""
新聞資訊工具
"""

from typing import Any

from ...api.openapi_client import OpenAPIClient
from ..base import ToolBase


class NewsTool(ToolBase):
    """
    市場新聞資訊查詢工具。

    提供股市新聞、公告等資訊服務。
    """

    def __init__(self):
        super().__init__("news")
        self.openapi_client = OpenAPIClient()

    async def execute(
        self, symbol: str = "", category: str = "market", **kwargs
    ) -> dict[str, Any]:
        """
        取得新聞資訊。

        Args:
            symbol: 股票代碼 (可選)
            category: 新聞類別 (market, company, announcement)

        Returns:
            包含新聞資訊的字典
        """
        try:
            self.logger.info(f"查詢新聞資訊: symbol={symbol}, category={category}")

            # 從 TWSE OpenAPI 取得新聞列表
            news_data = await self.openapi_client.get_data("/news/newsList")

            if not news_data:
                return self._error_response("無法取得新聞資料")

            # 如果有指定股票代碼，過濾相關新聞
            if symbol:
                filtered_news = []
                for news_item in news_data:
                    if symbol in str(news_item.get("title", "")) or symbol in str(
                        news_item.get("content", "")
                    ):
                        filtered_news.append(news_item)
                news_data = filtered_news

            # 限制返回數量
            max_items = kwargs.get("limit", 20)
            if len(news_data) > max_items:
                news_data = news_data[:max_items]

            return {
                "status": "success",
                "data": {
                    "symbol": symbol,
                    "category": category,
                    "news_count": len(news_data),
                    "news_items": news_data,
                },
            }

        except Exception as e:
            self.logger.error(f"查詢新聞資訊失敗: {e}")
            return self._error_response(str(e))
