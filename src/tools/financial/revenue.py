"""
營收資訊工具
"""

from typing import Any

from ..base import ToolBase


class RevenueTool(ToolBase):
    """
    公司營收資訊工具。
    """

    def __init__(self):
        super().__init__("revenue")

    async def execute(self, symbol: str) -> dict[str, Any]:
        """
        取得公司月營收資訊。

        Args:
            symbol: 公司股票代碼

        Returns:
            包含月營收資訊的字典
        """
        try:
            self.logger.info(f"查詢公司月營收: {symbol}")

            endpoint = "/opendata/t187ap05_L"
            data = await self.api_client.get_company_data(endpoint, symbol)

            if not data:
                return self._error_response(
                    error=f"找不到 {symbol} 的月營收資料", company_code=symbol
                )

            return self._success_response(
                data=data, company_code=symbol, source="TWSE OpenAPI"
            )

        except Exception as e:
            return self._error_response(error=str(e), company_code=symbol)
