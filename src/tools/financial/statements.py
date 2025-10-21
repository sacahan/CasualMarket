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
            # 關鍵步驟 1: 根據產業別決定 API 格式
            # 不同產業（一般業、金融業、金控業等）使用不同的報表格式
            suffix = await self.api_client.get_industry_api_suffix(symbol)
            endpoint = f"/opendata/t187ap06_L{suffix}"

            self.logger.info(f"查詢 {symbol} 損益表，使用格式: {suffix}")

            # 關鍵步驟 2: 從 TWSE OpenAPI 取得原始資料
            data = await self.api_client.get_company_data(endpoint, symbol)

            # 檢查是否取得資料
            if not data:
                return self._error_response(
                    error=f"找不到 {symbol} 的損益表資料",
                    company_code=symbol,
                    statement_type="綜合損益表",
                )

            # 關鍵步驟 3: 將原始資料轉換為標準化格式
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
            # 關鍵步驟 1: 根據產業別決定 API 格式
            # 不同產業使用不同的報表格式
            suffix = await self.api_client.get_industry_api_suffix(symbol)
            endpoint = f"/opendata/t187ap07_L{suffix}"

            self.logger.info(f"查詢 {symbol} 資產負債表，使用格式: {suffix}")

            # 關鍵步驟 2: 從 TWSE OpenAPI 取得原始資料
            data = await self.api_client.get_company_data(endpoint, symbol)

            # 檢查是否取得資料
            if not data:
                return self._error_response(
                    error=f"找不到 {symbol} 的資產負債表資料",
                    company_code=symbol,
                    statement_type="資產負債表",
                )

            # 關鍵步驟 3: 將原始資料轉換為標準化格式
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
        """
        格式化損益表資料。
        
        將原始 API 回應轉換為結構化格式，包含原始資料和關鍵財務指標。
        關鍵指標包括營業收入、營業利益、淨利和每股盈餘。
        """
        return {
            # 保留原始資料以供進階查詢
            "raw_data": data,
            # 提取關鍵財務指標供快速查閱
            "key_metrics": {
                "revenue": data.get("營業收入", "N/A"),  # 營業收入
                "operating_income": data.get("營業利益", "N/A"),  # 營業利益
                "net_income": data.get("本期淨利", "N/A"),  # 本期淨利
                "earnings_per_share": data.get("基本每股盈餘", "N/A"),  # EPS
            },
        }

    def _format_balance_sheet(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        格式化資產負債表資料。
        
        將原始 API 回應轉換為結構化格式，包含原始資料和關鍵財務指標。
        關鍵指標包括總資產、負債、股東權益和每股淨值。
        """
        return {
            # 保留原始資料以供進階查詢
            "raw_data": data,
            # 提取關鍵財務指標供快速查閱
            "key_metrics": {
                "total_assets": data.get("資產總額", "N/A"),  # 資產總額
                "total_liabilities": data.get("負債總額", "N/A"),  # 負債總額
                "stockholders_equity": data.get("股東權益總額", "N/A"),  # 股東權益
                "book_value_per_share": data.get("每股淨值", "N/A"),  # 每股淨值
            },
        }

    async def execute(self, **kwargs) -> dict[str, Any]:
        """基類要求的執行方法"""
        return self._error_response(
            "請使用 get_income_statement() 或 get_balance_sheet() 方法"
        )
