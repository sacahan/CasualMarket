"""
除權息行事曆工具
"""

from typing import Any

from ..base import ToolBase


class DividendScheduleTool(ToolBase):
    """
    除權息行事曆查詢工具。
    """

    def __init__(self):
        super().__init__("dividend_schedule")

    async def execute(self, symbol: str = "", **kwargs) -> dict[str, Any]:
        """
        取得除權息行事曆。

        Args:
            symbol: 股票代碼 (可選，空字串則查詢全部)

        Returns:
            包含除權息行事曆的字典
        """
        try:
            self.logger.info(f"查詢除權息行事曆: {symbol or '全部'}")
            endpoint = "/exchangeReport/TWT48U_ALL"

            if symbol:
                # 查詢特定公司
                data = await self.api_client.get_company_data(endpoint, symbol)
                if not data:
                    return self._error_response(
                        f"No dividend schedule found for {symbol}", symbol=symbol
                    )
                result_data = [data] if isinstance(data, dict) else data
                total_count = 1
            else:
                # 查詢全部
                data = await self.api_client.get_data(endpoint)
                if not data:
                    return self._error_response("No dividend schedule data available")

                # 限制前20筆避免資料過多
                result_data = data[:20] if len(data) > 20 else data
                total_count = len(data)

            result = {
                "dividend_schedule": result_data,
                "query_symbol": symbol or "all",
                "total_count": total_count,
                "displayed_count": len(result_data),
            }

            self.logger.info(f"成功取得除權息資料: {len(result_data)} 筆")
            return self._success_response(data=result, source="TWSE Exchange Report")

        except Exception as e:
            self.logger.error(f"查詢除權息資料失敗: {e}")
            return self._error_response(str(e), symbol=symbol)
