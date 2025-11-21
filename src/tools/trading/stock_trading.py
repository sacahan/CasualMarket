"""
股票交易模擬工具
"""

from typing import Any

from ..base import ToolBase


class StockTradingTool(ToolBase):
    """
    股票交易模擬工具，支援買入和賣出操作。
    """

    def __init__(self):
        super().__init__("stock_trading")

    async def buy(
        self, symbol: str, quantity: int, price: float | None = None
    ) -> dict[str, Any]:
        """
        模擬台灣股票買入操作。

        Args:
            symbol: 股票代碼
            quantity: 購買股數 (台股最小單位為1000股)
            price: 指定價格 (可選，不指定則為市價)

        Returns:
            交易結果資訊
        """
        try:
            self.logger.info(f"模擬買入: {symbol} x {quantity} 股")

            # 驗證股數 (台股最小單位1000股)
            if quantity % 1000 != 0:
                return self._error_response(
                    error="台股交易最小單位為1000股", symbol=symbol, quantity=quantity
                )

            # 取得目前股價作為參考
            stock_data = await self.stock_client.get_stock_quote(symbol)
            current_price = stock_data.current_price

            # 處理市價單或限價單
            if price is None:
                # 市價單：立即以當前價格成交
                order_price = current_price
                total_amount = order_price * quantity
                order_type = "market"
                executed = True
                execution_message = "市價單立即成交"
            else:
                # 限價單：檢查是否符合成交條件
                order_price = price
                total_amount = order_price * quantity
                order_type = "limit"

                # 買入限價單：出價必須 >= 當前賣價才能成交
                if order_price >= current_price:
                    executed = True
                    execution_message = (
                        f"限價買單成交（出價 {order_price} >= 市價 {current_price}）"
                    )
                else:
                    executed = False
                    execution_message = (
                        f"限價買單無法成交（出價 {order_price} < 市價 {current_price}）"
                    )

            # 構建交易結果
            order_data = {
                "action": "buy",
                "symbol": symbol,
                "name": stock_data.company_name,
                "quantity": quantity,
                "price": order_price,
                "total_amount": total_amount,
                "current_price": current_price,
                "order_type": order_type,
                "executed": executed,
                "message": execution_message,
                "timestamp": (
                    stock_data.update_time.isoformat()
                    if stock_data.update_time
                    else None
                ),
            }

            if executed:
                self.logger.info(
                    f"買入交易成功: {symbol} -> {quantity} x ${order_price}"
                )
                return self._success_response(
                    data={"order": order_data}, status="success"
                )
            else:
                self.logger.info(f"買入交易失敗: {symbol} -> {execution_message}")
                return self._success_response(
                    data={"order": order_data}, status="failed"
                )

        except Exception as e:
            return self._error_response(error=str(e), symbol=symbol)

    async def sell(
        self, symbol: str, quantity: int, price: float | None = None
    ) -> dict[str, Any]:
        """
        模擬台灣股票賣出操作。

        Args:
            symbol: 股票代碼
            quantity: 賣出股數 (台股最小單位為1000股)
            price: 指定價格 (可選，不指定則為市價)

        Returns:
            交易結果資訊
        """
        try:
            self.logger.info(f"模擬賣出: {symbol} x {quantity} 股")

            # 驗證股數 (台股最小單位1000股)
            if quantity % 1000 != 0:
                return self._error_response(
                    error="台股交易最小單位為1000股", symbol=symbol, quantity=quantity
                )

            # 取得目前股價作為參考
            stock_data = await self.stock_client.get_stock_quote(symbol)
            current_price = stock_data.current_price

            # 處理市價單或限價單
            if price is None:
                # 市價單：立即以當前價格成交
                order_price = current_price
                total_amount = order_price * quantity
                order_type = "market"
                executed = True
                execution_message = "市價單立即成交"
            else:
                # 限價單：檢查是否符合成交條件
                order_price = price
                total_amount = order_price * quantity
                order_type = "limit"

                # 賣出限價單：售價必須 <= 當前買價才能成交
                if order_price <= current_price:
                    executed = True
                    execution_message = (
                        f"限價賣單成交（售價 {order_price} <= 市價 {current_price}）"
                    )
                else:
                    executed = False
                    execution_message = (
                        f"限價賣單無法成交（售價 {order_price} > 市價 {current_price}）"
                    )

            # 構建交易結果
            order_data = {
                "action": "sell",
                "symbol": symbol,
                "name": stock_data.company_name,
                "quantity": quantity,
                "price": order_price,
                "total_amount": total_amount,
                "current_price": current_price,
                "order_type": order_type,
                "executed": executed,
                "message": execution_message,
                "timestamp": (
                    stock_data.update_time.isoformat()
                    if stock_data.update_time
                    else None
                ),
            }

            if executed:
                self.logger.info(
                    f"賣出交易成功: {symbol} -> {quantity} x ${order_price}"
                )
                return self._success_response(
                    data={"order": order_data}, status="success"
                )
            else:
                self.logger.info(f"賣出交易失敗: {symbol} -> {execution_message}")
                return self._success_response(
                    data={"order": order_data}, status="failed"
                )

        except Exception as e:
            return self._error_response(error=str(e), symbol=symbol)

    async def execute(self, **kwargs) -> dict[str, Any]:
        """
        基類要求的執行方法，這裡不直接使用。
        """
        return self._error_response("請使用 buy() 或 sell() 方法")
