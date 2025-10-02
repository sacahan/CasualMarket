"""
股票交易統計工具
"""

from typing import Any

from ..base import ToolBase


class TradingStatisticsTool(ToolBase):
    """
    股票交易統計分析工具，提供月/年交易資料和平均價格。
    """

    def __init__(self):
        super().__init__("trading_statistics")

    async def get_monthly_trading(self, symbol: str, **kwargs) -> dict[str, Any]:
        """
        取得股票月交易資訊。

        Args:
            symbol: 股票代碼

        Returns:
            包含月交易資訊的字典
        """
        try:
            self.logger.info(f"查詢股票月交易資訊: {symbol}")
            endpoint = "/exchangeReport/FMSRFK_ALL"
            data = await self.api_client.get_company_data(endpoint, symbol)

            if not data:
                return self._error_response(
                    f"No monthly trading data found for {symbol}", symbol=symbol
                )

            self.logger.info(f"成功取得 {symbol} 月交易資料")
            return self._success_response(
                data=data, source="TWSE Exchange Report", company_code=symbol
            )

        except Exception as e:
            self.logger.error(f"查詢月交易資料失敗: {e}")
            return self._error_response(str(e), symbol=symbol)

    async def get_yearly_trading(self, symbol: str, **kwargs) -> dict[str, Any]:
        """
        取得股票年交易資訊。

        Args:
            symbol: 股票代碼

        Returns:
            包含年交易資訊的字典
        """
        try:
            self.logger.info(f"查詢股票年交易資訊: {symbol}")
            endpoint = "/exchangeReport/FMNPTK_ALL"
            data = await self.api_client.get_company_data(endpoint, symbol)

            if not data:
                return self._error_response(
                    f"No yearly trading data found for {symbol}", symbol=symbol
                )

            self.logger.info(f"成功取得 {symbol} 年交易資料")
            return self._success_response(
                data=data, source="TWSE Exchange Report", company_code=symbol
            )

        except Exception as e:
            self.logger.error(f"查詢年交易資料失敗: {e}")
            return self._error_response(str(e), symbol=symbol)

    async def get_monthly_average(self, symbol: str, **kwargs) -> dict[str, Any]:
        """
        取得股票月平均價格。

        Args:
            symbol: 股票代碼

        Returns:
            包含月平均價格的字典
        """
        try:
            self.logger.info(f"查詢股票月平均價格: {symbol}")
            endpoint = "/exchangeReport/FMSRFK_ALL"
            data = await self.api_client.get_company_data(endpoint, symbol)

            if not data:
                return self._error_response(
                    f"No monthly average data found for {symbol}", symbol=symbol
                )

            self.logger.info(f"成功取得 {symbol} 月平均價格")
            return self._success_response(
                data=data, source="TWSE Exchange Report", company_code=symbol
            )

        except Exception as e:
            self.logger.error(f"查詢月平均價格失敗: {e}")
            return self._error_response(str(e), symbol=symbol)

    async def execute(
        self, symbol: str, stat_type: str = "monthly", **kwargs
    ) -> dict[str, Any]:
        """
        執行交易統計查詢。

        Args:
            symbol: 股票代碼
            stat_type: 統計類型 ("monthly", "yearly", "average")

        Returns:
            統計結果
        """
        if stat_type == "monthly":
            return await self.get_monthly_trading(symbol, **kwargs)
        elif stat_type == "yearly":
            return await self.get_yearly_trading(symbol, **kwargs)
        elif stat_type == "average":
            return await self.get_monthly_average(symbol, **kwargs)
        else:
            return self._error_response(
                f"Unknown stat_type: {stat_type}", symbol=symbol
            )
