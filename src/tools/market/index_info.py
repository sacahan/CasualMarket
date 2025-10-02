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

    async def execute(
        self,
        category: str = "major",
        count: int = 20,
        format: str = "detailed",
        **kwargs,
    ) -> dict[str, Any]:
        """
        取得市場指數資訊。

        Args:
            category: 指數類別 (major, sector, all)
            count: 返回數量
            format: 格式 (detailed, simple)

        Returns:
            包含市場指數資訊的字典
        """
        try:
            self.logger.info(
                f"查詢市場指數: category={category}, count={count}, format={format}"
            )

            data = await self.api_client.get_latest_market_data(
                "/exchangeReport/MI_INDEX"
            )

            if not data:
                return self._error_response("No market index data available")

            # 根據類別篩選指數
            if category == "major":
                filtered_data = [
                    item
                    for item in data
                    if not any(
                        pattern in item.get("指數", "")
                        for pattern in ["類指數", "報酬指數", "兩倍", "反向", "槓桿"]
                    )
                    and any(
                        pattern in item.get("指數", "")
                        for pattern in ["發行量加權", "寶島", "臺灣50", "中型", "小型"]
                    )
                ]
            elif category == "sector":
                filtered_data = [
                    item
                    for item in data
                    if "類指數" in item.get("指數", "")
                    and "報酬指數" not in item.get("指數", "")
                ]
            else:
                filtered_data = data

            result_data = filtered_data[:count] if count > 0 else filtered_data

            result = {
                "category": category,
                "count": len(result_data),
                "format": format,
                "indices": result_data,
            }

            self.logger.info(f"成功取得指數資料: {len(result_data)} 筆")
            return self._success_response(
                data=result, source="TWSE Market Index Report"
            )

        except Exception as e:
            self.logger.error(f"查詢市場指數失敗: {e}")
            return self._error_response(str(e))
