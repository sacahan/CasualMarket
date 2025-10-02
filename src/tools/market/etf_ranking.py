"""
ETF定期定額排名工具
"""

from typing import Any

from ..base import ToolBase


class ETFRankingTool(ToolBase):
    """
    ETF定期定額排名查詢工具。
    """

    def __init__(self):
        super().__init__("etf_ranking")

    async def execute(self, **kwargs) -> dict[str, Any]:
        """
        取得ETF定期定額排名資訊（前10名）。

        Returns:
            包含ETF排名的字典
        """
        try:
            self.logger.info("查詢ETF定期定額排名")
            data = await self.api_client.get_data("/ETFReport/ETFRank")

            if not data:
                return self._error_response("No ETF ranking data available")

            top_10 = data[:10] if len(data) > 10 else data

            result = {
                "ranking_date": None,
                "rankings": top_10,
                "total_count": len(data),
                "displayed_count": len(top_10),
            }

            self.logger.info(f"成功取得ETF排名: {len(top_10)} 筆")
            return self._success_response(data=result, source="TWSE ETF Report")

        except Exception as e:
            self.logger.error(f"查詢ETF排名失敗: {e}")
            return self._error_response(str(e))
