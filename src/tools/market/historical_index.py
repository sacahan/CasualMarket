"""
歷史指數工具
"""

from typing import Any

from ..base import ToolBase


class HistoricalIndexTool(ToolBase):
    """
    市場歷史指數查詢工具。
    """

    def __init__(self):
        super().__init__("historical_index")

    async def execute(self, **kwargs) -> dict[str, Any]:
        """
        取得歷史指數資料。

        Returns:
            包含歷史指數資料的字典
        """
        try:
            self.logger.info("查詢歷史指數資料")
            endpoint = "/exchangeReport/MI_INDEX"
            data = await self.api_client.get_latest_market_data(endpoint)

            if not data:
                return self._error_response("No historical index data available")

            result = {
                "historical_indices": data,
                "count": len(data),
            }

            self.logger.info(f"成功取得歷史指數資料: {len(data)} 筆")
            return self._success_response(data=result, source="TWSE Exchange Report")

        except Exception as e:
            self.logger.error(f"查詢歷史指數資料失敗: {e}")
            return self._error_response(str(e))
