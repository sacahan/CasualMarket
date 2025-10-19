"""
市場指數資訊工具
"""

from typing import Any

from ..base import ToolBase


class IndexInfoTool(ToolBase):
    """
    市場指數資訊查詢工具。
    """

    def __init__(self):
        super().__init__("index_info")

    async def execute(self, **kwargs) -> dict[str, Any]:
        """
        取得台灣加權指數資訊。

        Returns:
            包含發行量加權股價指數的字典
        """
        try:
            self.logger.info("查詢發行量加權股價指數")

            data = await self.api_client.get_latest_market_data(
                "/exchangeReport/MI_INDEX"
            )

            if not data:
                return self._error_response("No market index data available")

            # 只取得發行量加權股價指數
            index_data = next(
                (
                    item
                    for item in data
                    if item.get("指數", "") == "發行量加權股價指數"
                ),
                None,
            )

            if not index_data:
                return self._error_response("發行量加權股價指數資料不存在")

            self.logger.info("成功取得發行量加權股價指數")
            return self._success_response(
                data=index_data, source="TWSE Market Index Report"
            )

        except Exception as e:
            self.logger.error(f"查詢市場指數失敗: {e}")
            return self._error_response(str(e))
