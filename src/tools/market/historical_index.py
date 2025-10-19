"""
歷史指數工具
"""

from typing import Any

from ..base import ToolBase


class HistoricalIndexTool(ToolBase):
    """
    市場歷史指數查詢工具。
    """

    def __init__(self):
        super().__init__("historical_index")

    async def execute(self, **kwargs) -> dict[str, Any]:
        """
        取得市場重要指數資料。
        
        精選10個最重要的市場指數,提供完整的市場概覽:
        
        1. 發行量加權股價指數 - 台灣股市大盤主指數
        2. 未含金融指數 - 排除金融股的市場指數
        3. 未含電子指數 - 排除電子股的市場指數
        4. 臺灣50指數 - 台灣市值前50大企業指數
        5. 臺灣中型100指數 - 台灣中型企業代表指數
        6. 電子工業類指數 - 電子產業整體表現
        7. 金融保險類指數 - 金融保險產業指數
        8. 半導體類指數 - 半導體產業指數
        9. 電腦及週邊設備類指數 - 電腦硬體產業指數
        10. 通信網路類指數 - 通訊網路產業指數

        Returns:
            包含精選市場指數列表的字典,每個指數包含完整的交易資訊
        """
        try:
            self.logger.info("查詢市場重要指數資料")
            endpoint = "/exchangeReport/MI_INDEX"
            data = await self.api_client.get_latest_market_data(endpoint)

            if not data:
                return self._error_response("No historical index data available")

            # 精選最重要的10個指數
            important_indices = [
                "發行量加權股價指數",
                "未含金融指數",
                "未含電子指數", 
                "臺灣50指數",
                "臺灣中型100指數",
                "電子工業類指數",
                "金融保險類指數",
                "半導體類指數",
                "電腦及週邊設備類指數",
                "通信網路類指數",
            ]
            
            # 篩選出精選指數
            selected_indices = [
                item for item in data
                if item.get("指數", "") in important_indices
            ]
            
            # 按照重要性排序
            sorted_indices = []
            for index_name in important_indices:
                for item in selected_indices:
                    if item.get("指數", "") == index_name:
                        sorted_indices.append(item)
                        break

            if not sorted_indices:
                return self._error_response("無法取得市場指數資料")

            result = {
                "indices": sorted_indices,
                "count": len(sorted_indices),
            }

            self.logger.info(f"成功取得市場重要指數資料: {len(sorted_indices)} 筆")
            return self._success_response(data=result, source="TWSE Exchange Report")

        except Exception as e:
            self.logger.error(f"查詢市場指數資料失敗: {e}")
            return self._error_response(str(e))
