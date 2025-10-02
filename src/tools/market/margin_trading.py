"""
融資融券資訊工具
"""

from typing import Any

from ..base import ToolBase


class MarginTradingTool(ToolBase):
    """
    融資融券資訊查詢工具。
    """

    def __init__(self):
        super().__init__("margin_trading")

    async def execute(self, **kwargs) -> dict[str, Any]:
        """
        取得融資融券資訊。

        Returns:
            包含融資融券資訊的字典
        """
        try:
            self.logger.info("查詢融資融券資訊")
            data = await self.api_client.get_data("/exchangeReport/MI_MARGN")

            if not data:
                return self._error_response("No margin trading data available")

            # 限制前10筆避免資料過多
            top_10 = data[:10] if len(data) > 10 else data

            result = {
                "margin_data": top_10,
                "total_count": len(data),
                "displayed_count": len(top_10),
            }

            self.logger.info(f"成功取得融資融券資料: {len(top_10)} 筆")
            return self._success_response(
                data=result, source="TWSE Margin Trading Report"
            )

        except Exception as e:
            self.logger.error(f"查詢融資融券資料失敗: {e}")
            return self._error_response(str(e))
