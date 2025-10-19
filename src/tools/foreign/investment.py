"""
外資投資工具
"""

from typing import Any

from ..base import ToolBase


class ForeignInvestmentTool(ToolBase):
    """
    外資投資分析工具。
    """

    def __init__(self):
        super().__init__("foreign_investment")

    async def get_investment_by_industry(self, **kwargs) -> dict[str, Any]:
        """
        取得外資持股(按產業別)。

        Args:
            count: 限制返回的產業數量,預設為10個產業

        Returns:
            包含各產業外資持股比率統計的字典
        """
        try:
            count = kwargs.get("count", 10)  # 預設返回前10個產業
            self.logger.info(f"查詢外資持股(按產業別),限制 {count} 個產業")
            endpoint = "/fund/MI_QFIIS_cat"
            data = await self.api_client.get_data(endpoint)

            if not data:
                return self._error_response(
                    "No foreign investment data by industry available"
                )

            # 限制返回數量
            limited_data = data[:count] if count else data
            total_count = len(data)
            displayed_count = len(limited_data)

            result = {
                "industry_foreign_investment": limited_data,
                "total_industries": total_count,
                "displayed_industries": displayed_count,
            }

            self.logger.info(f"成功取得外資持股產業資料: 顯示 {displayed_count}/{total_count} 個產業")
            return self._success_response(data=result, source="TWSE Fund Report")

        except Exception as e:
            self.logger.error(f"查詢外資持股產業資料失敗: {e}")
            return self._error_response(str(e))

    async def get_top_holdings(self, **kwargs) -> dict[str, Any]:
        """
        取得外資持股前20名。

        Returns:
            包含外資持股排名前20的公司詳細資訊的字典
        """
        try:
            self.logger.info("查詢外資持股前20名")
            endpoint = "/fund/MI_QFIIS_sort_20"
            data = await self.api_client.get_data(endpoint)

            if not data:
                return self._error_response("No top foreign holdings data available")

            result = {
                "top_foreign_holdings": data,
                "count": len(data),
            }

            self.logger.info(f"成功取得外資持股前20名: {len(data)} 筆")
            return self._success_response(data=result, source="TWSE Fund Report")

        except Exception as e:
            self.logger.error(f"查詢外資持股前20名失敗: {e}")
            return self._error_response(str(e))

    async def execute(self, action: str = "industry", **kwargs) -> dict[str, Any]:
        """
        執行外資投資查詢。

        Args:
            action: 查詢類型 ("industry" 或 "top_holdings")

        Returns:
            查詢結果
        """
        if action == "industry":
            return await self.get_investment_by_industry(**kwargs)
        elif action == "top_holdings":
            return await self.get_top_holdings(**kwargs)
        else:
            return self._error_response(f"Unknown action: {action}")
