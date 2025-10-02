"""
股利分配工具
"""

from typing import Any

from ..base import ToolBase


class DividendTool(ToolBase):
    """
    股利分配工具。
    """

    def __init__(self):
        super().__init__("dividend")

    async def execute(self, symbol: str) -> dict[str, Any]:
        """
        取得公司股利分配資訊。

        Args:
            symbol: 公司股票代碼

        Returns:
            包含股利分配資訊的字典
        """
        try:
            self.logger.info(f"查詢公司股利資訊: {symbol}")

            endpoint = "/opendata/t187ap45_L"
            data = await self.api_client.get_company_data(endpoint, symbol)

            if not data:
                return self._error_response(
                    error=f"找不到 {symbol} 的股利資料", company_code=symbol
                )

            return self._success_response(
                data=data, company_code=symbol, source="TWSE OpenAPI"
            )

        except Exception as e:
            return self._error_response(error=str(e), company_code=symbol)
