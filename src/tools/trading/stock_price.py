"""
股票價格查詢工具
"""

from typing import Any

from ..base import ToolBase


class StockPriceTool(ToolBase):
    """
    股票價格查詢工具，支援股票代碼或公司名稱查詢。
    """

    def __init__(self):
        super().__init__("stock_price")

    async def execute(self, symbol: str) -> dict[str, Any]:
        """
        取得台灣股票即時價格資訊。

        Args:
            symbol: 台灣股票代號或公司名稱

        Returns:
            包含股票價格資訊的字典
        """
        try:
            self.logger.info(f"查詢股票價格: {symbol}")

            # 呼叫 API 取得股票資料
            stock_data = await self.stock_client.get_stock_quote(symbol)

            # 格式化回應
            data = {
                "symbol": stock_data.symbol,
                "name": stock_data.company_name,
                "price": stock_data.current_price,
                "change": stock_data.change,
                "change_percent": stock_data.change_percent,
                "volume": stock_data.volume,
                "high": stock_data.high_price,
                "low": stock_data.low_price,
                "open": stock_data.open_price,
                "previous_close": stock_data.previous_close,
                "last_update": (
                    stock_data.update_time.isoformat()
                    if stock_data.update_time
                    else None
                ),
            }

            return self._success_response(data=data, status="success", symbol=symbol)

        except Exception as e:
            return self._error_response(error=str(e), symbol=symbol)
