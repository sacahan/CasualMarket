"""
財務報表工具 - 損益表和資產負債表
"""

from typing import Any

from ..base import ToolBase


class FinancialStatementsTool(ToolBase):
    """
    財務報表工具，提供損益表和資產負債表查詢。
    """

    def __init__(self):
        super().__init__("financial_statements")

    async def get_income_statement(self, symbol: str) -> dict[str, Any]:
        """
        取得上市公司綜合損益表。

        Args:
            symbol: 公司股票代碼

        Returns:
            包含綜合損益表資訊的字典
        """
        try:
            # 取得產業別對應的 API 後綴
            suffix = await self.api_client.get_industry_api_suffix(symbol)
            endpoint = f"/opendata/t187ap06_L{suffix}"

            self.logger.info(f"查詢 {symbol} 損益表，使用格式: {suffix}")

            # 取得資料
            data = await self.api_client.get_company_data(endpoint, symbol)

            if not data:
                return self._error_response(
                    error=f"找不到 {symbol} 的損益表資料",
                    company_code=symbol,
                    statement_type="綜合損益表",
                )

            # 格式化回應
            formatted_data = self._format_income_statement(data)

            return self._success_response(
                data=formatted_data,
                company_code=symbol,
                statement_type="綜合損益表",
                industry_format=suffix,
                source="TWSE OpenAPI",
            )

        except Exception as e:
            return self._error_response(
                error=str(e), company_code=symbol, statement_type="綜合損益表"
            )

    async def get_balance_sheet(self, symbol: str) -> dict[str, Any]:
        """
        取得上市公司資產負債表。

        Args:
            symbol: 公司股票代碼

        Returns:
            包含資產負債表資訊的字典
        """
        try:
            # 取得產業別對應的 API 後綴
            suffix = await self.api_client.get_industry_api_suffix(symbol)
            endpoint = f"/opendata/t187ap07_L{suffix}"

            self.logger.info(f"查詢 {symbol} 資產負債表，使用格式: {suffix}")

            # 取得資料
            data = await self.api_client.get_company_data(endpoint, symbol)

            if not data:
                return self._error_response(
                    error=f"找不到 {symbol} 的資產負債表資料",
                    company_code=symbol,
                    statement_type="資產負債表",
                )

            # 格式化回應
            formatted_data = self._format_balance_sheet(data)

            return self._success_response(
                data=formatted_data,
                company_code=symbol,
                statement_type="資產負債表",
                industry_format=suffix,
                source="TWSE OpenAPI",
            )

        except Exception as e:
            return self._error_response(
                error=str(e), company_code=symbol, statement_type="資產負債表"
            )

    def _format_income_statement(self, data: dict[str, Any]) -> dict[str, Any]:
        """格式化損益表資料"""
        return {
            "raw_data": data,
            "key_metrics": {
                "revenue": data.get("營業收入", "N/A"),
                "operating_income": data.get("營業利益", "N/A"),
                "net_income": data.get("本期淨利", "N/A"),
                "earnings_per_share": data.get("基本每股盈餘", "N/A"),
            },
        }

    def _format_balance_sheet(self, data: dict[str, Any]) -> dict[str, Any]:
        """格式化資產負債表資料"""
        return {
            "raw_data": data,
            "key_metrics": {
                "total_assets": data.get("資產總額", "N/A"),
                "total_liabilities": data.get("負債總額", "N/A"),
                "stockholders_equity": data.get("股東權益總額", "N/A"),
                "book_value_per_share": data.get("每股淨值", "N/A"),
            },
        }

    async def execute(self, **kwargs) -> dict[str, Any]:
        """基類要求的執行方法"""
        return self._error_response(
            "請使用 get_income_statement() 或 get_balance_sheet() 方法"
        )
