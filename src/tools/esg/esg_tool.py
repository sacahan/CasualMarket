"""
ESG 治理評級工具
"""

from typing import Any

from ...api.openapi_client import OpenAPIClient
from ..base import ToolBase


class ESGTool(ToolBase):
    """
    ESG (Environmental, Social, Governance) 評級查詢工具。

    提供企業環境、社會責任、公司治理評級等資訊服務。
    """

    def __init__(self):
        super().__init__("esg")
        self.openapi_client = OpenAPIClient()

    async def execute(
        self, symbol: str = "", category: str = "overall", **kwargs
    ) -> dict[str, Any]:
        """
        取得 ESG 評級資訊。

        Args:
            symbol: 股票代碼 (可選)
            category: ESG 類別 (overall, environmental, social, governance)

        Returns:
            包含 ESG 評級資訊的字典
        """
        try:
            self.logger.info(f"查詢 ESG 資訊: symbol={symbol}, category={category}")

            esg_data = {}

            # 根據類別查詢不同的 ESG 資料
            if category in ["overall", "environmental"]:
                # 溫室氣體排放資料
                greenhouse_data = await self.openapi_client.get_data(
                    "/opendata/t187ap46_L_1"
                )
                if greenhouse_data:
                    esg_data["greenhouse_gas"] = greenhouse_data

                # 能源管理資料
                energy_data = await self.openapi_client.get_data(
                    "/opendata/t187ap46_L_2"
                )
                if energy_data:
                    esg_data["energy_management"] = energy_data

                # 水資源管理資料
                water_data = await self.openapi_client.get_data(
                    "/opendata/t187ap46_L_3"
                )
                if water_data:
                    esg_data["water_management"] = water_data

            # 如果有指定股票代碼，過濾相關資料
            if symbol and esg_data:
                filtered_data = {}
                for key, data_list in esg_data.items():
                    if isinstance(data_list, list):
                        filtered_items = []
                        for item in data_list:
                            if symbol in str(item.get("公司代號", "")) or symbol in str(
                                item.get("symbol", "")
                            ):
                                filtered_items.append(item)
                        if filtered_items:
                            filtered_data[key] = filtered_items
                esg_data = filtered_data

            if not esg_data:
                return self._error_response("無法取得 ESG 資料")

            # 計算 ESG 統計
            total_companies = 0
            environmental_metrics = {}

            for category_name, data_list in esg_data.items():
                if isinstance(data_list, list):
                    total_companies += len(data_list)

                    # 分析環境指標
                    if category_name == "greenhouse_gas":
                        environmental_metrics["greenhouse_gas_companies"] = len(
                            data_list
                        )
                    elif category_name == "energy_management":
                        environmental_metrics["energy_management_companies"] = len(
                            data_list
                        )
                    elif category_name == "water_management":
                        environmental_metrics["water_management_companies"] = len(
                            data_list
                        )

            return {
                "status": "success",
                "data": {
                    "symbol": symbol,
                    "category": category,
                    "total_companies": total_companies,
                    "environmental_metrics": environmental_metrics,
                    "esg_details": esg_data,
                },
            }

        except Exception as e:
            self.logger.error(f"查詢 ESG 資訊失敗: {e}")
            return self._error_response(str(e))
