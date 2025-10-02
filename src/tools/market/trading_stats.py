"""
即時交易統計工具
"""

from typing import Any

from ..base import ToolBase


class TradingStatsTool(ToolBase):
    """
    即時交易統計查詢工具。
    """

    def __init__(self):
        super().__init__("trading_stats")

    async def execute(self, **kwargs) -> dict[str, Any]:
        """
        取得即時交易統計資訊（5分鐘資料）。

        Returns:
            包含即時交易統計的字典
        """
        try:
            self.logger.info("查詢即時交易統計")
            data = await self.api_client.get_latest_market_data(
                "/exchangeReport/MI_5MINS", count=10
            )

            if not data:
                return self._error_response("No real-time trading stats available")

            result = {
                "trading_stats": data,
                "count": len(data),
                "frequency": "5_minutes",
            }

            self.logger.info(f"成功取得即時交易統計: {len(data)} 筆")
            return self._success_response(
                data=result, source="TWSE Real-time Trading Statistics"
            )

        except Exception as e:
            self.logger.error(f"查詢即時交易統計失敗: {e}")
            return self._error_response(str(e))
