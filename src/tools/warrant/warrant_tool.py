"""
權證工具
"""

from typing import Any

from ...api.openapi_client import OpenAPIClient
from ..base import ToolBase


class WarrantTool(ToolBase):
    """
    權證資訊查詢工具。

    提供權證價格、履約價、到期日等資訊服務。
    """

    def __init__(self):
        super().__init__("warrant")
        self.openapi_client = OpenAPIClient()

    async def execute(
        self, symbol: str = "", warrant_type: str = "call", **kwargs
    ) -> dict[str, Any]:
        """
        取得權證資訊。

        Args:
            symbol: 標的股票代碼 (可選)
            warrant_type: 權證類型 (call, put)

        Returns:
            包含權證資訊的字典
        """
        try:
            self.logger.info(f"查詢權證資訊: symbol={symbol}, type={warrant_type}")

            # 從日交易資料中篩選權證
            trading_data = await self.openapi_client.get_data(
                "/exchangeReport/STOCK_DAY_ALL"
            )

            if not trading_data:
                return self._error_response("無法取得交易資料")

            # 權證通常代碼以 0 開頭且長度為 6 碼
            warrant_data = []
            for item in trading_data:
                stock_code = item.get("證券代號", "")
                stock_name = item.get("證券名稱", "")

                # 篩選權證（通常名稱包含「權證」或代碼特徵）
                is_warrant = (
                    "權證" in stock_name
                    or (stock_code.startswith("0") and len(stock_code) == 6)
                    or any(
                        keyword in stock_name
                        for keyword in ["元大", "凱基", "統一", "群益", "永豐", "富邦"]
                    )
                    and any(keyword in stock_name for keyword in ["購", "售", "認"])
                )

                if is_warrant:
                    # 根據標的股票篩選
                    if symbol and symbol not in stock_name:
                        continue

                    # 根據權證類型篩選
                    if warrant_type == "call" and "售" in stock_name:
                        continue
                    elif warrant_type == "put" and "購" in stock_name:
                        continue

                    warrant_info = {
                        "warrant_code": stock_code,
                        "warrant_name": stock_name,
                        "warrant_type": "put" if "售" in stock_name else "call",
                        "underlying_symbol": symbol,
                        "trading_volume": item.get("成交股數", 0),
                        "trading_value": item.get("成交金額", 0),
                        "opening_price": item.get("開盤價", 0),
                        "closing_price": item.get("收盤價", 0),
                        "highest_price": item.get("最高價", 0),
                        "lowest_price": item.get("最低價", 0),
                        "price_change": item.get("漲跌價差", 0),
                        "transaction_count": item.get("成交筆數", 0),
                    }
                    warrant_data.append(warrant_info)

            # 限制返回數量
            max_items = kwargs.get("limit", 50)
            if len(warrant_data) > max_items:
                warrant_data = warrant_data[:max_items]

            # 計算統計資訊
            total_warrants = len(warrant_data)
            call_warrants = len(
                [w for w in warrant_data if w["warrant_type"] == "call"]
            )
            put_warrants = len([w for w in warrant_data if w["warrant_type"] == "put"])

            return {
                "status": "success",
                "data": {
                    "underlying_symbol": symbol,
                    "warrant_type_filter": warrant_type,
                    "total_warrants": total_warrants,
                    "call_warrants": call_warrants,
                    "put_warrants": put_warrants,
                    "warrant_list": warrant_data,
                },
            }

        except Exception as e:
            self.logger.error(f"查詢權證資訊失敗: {e}")
            return self._error_response(str(e))
