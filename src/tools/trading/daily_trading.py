"""
日交易資訊工具
"""

from typing import Any

from ..base import ToolBase


class DailyTradingTool(ToolBase):
    """
    股票日交易資訊工具。
    """

    def __init__(self):
        super().__init__("daily_trading")

    async def execute(self, symbol: str) -> dict[str, Any]:
        """
        取得股票日交易資訊。

        Args:
            symbol: 股票代碼

        Returns:
            包含日交易資訊的字典
        """
        try:
            self.logger.info(f"查詢股票日交易資訊: {symbol}")

            # 使用現有的 API 客戶端但針對日交易資料
            stock_data = await self.stock_client.get_stock_quote(symbol)

            # 格式化日交易資料
            data = {
                "trading_date": (
                    stock_data.update_time.strftime("%Y-%m-%d")
                    if stock_data.update_time
                    else None
                ),
                "open_price": stock_data.open_price,
                "high_price": stock_data.high_price,
                "low_price": stock_data.low_price,
                "close_price": stock_data.current_price,
                "volume": stock_data.volume,
                "change": stock_data.change,
                "change_percent": stock_data.change_percent,
                "previous_close": stock_data.previous_close,
            }

            return self._success_response(data=data, symbol=symbol)

        except Exception as e:
            return self._error_response(error=str(e), symbol=symbol)
