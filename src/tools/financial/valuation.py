"""
估值比率工具
"""

from typing import Any

from ..base import ToolBase


class ValuationTool(ToolBase):
    """
    股票估值比率工具，提供 P/E, P/B, 殖利率等指標。
    """

    def __init__(self):
        super().__init__("valuation")

    async def execute(self, symbol: str) -> dict[str, Any]:
        """
        取得股票估值比率 (P/E, P/B, 殖利率)。

        Args:
            symbol: 股票代碼

        Returns:
            包含估值比率的字典
        """
        try:
            self.logger.info(f"查詢股票估值比率: {symbol}")

            endpoint = "/exchangeReport/BWIBBU_ALL"
            data = await self.api_client.get_company_data(endpoint, symbol)

            if not data:
                return self._error_response(
                    error=f"找不到 {symbol} 的估值比率資料", company_code=symbol
                )

            return self._success_response(
                data=data, company_code=symbol, source="TWSE Exchange Report"
            )

        except Exception as e:
            return self._error_response(error=str(e), company_code=symbol)
