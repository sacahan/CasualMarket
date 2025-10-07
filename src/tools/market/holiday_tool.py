"""
台灣節假日查詢工具

提供台灣節假日查詢和股市交易日判斷功能。
"""

from datetime import date, datetime
from typing import Any

from ...api.holiday_client import TaiwanHolidayAPIClient
from ...models.mcp_response import (
    HolidayInfoData,
    MCPToolResponse,
    TradingDayStatusData,
)
from ...tools.base.tool_base import ToolBase


class HolidayTool(ToolBase):
    """台灣節假日查詢工具"""

    def __init__(self):
        super().__init__("holiday_tool")
        self.holiday_client = TaiwanHolidayAPIClient()

    async def get_holiday_info(
        self, check_date: date | str
    ) -> MCPToolResponse[HolidayInfoData]:
        """
        查詢指定日期的節假日資訊

        Args:
            check_date: 要查詢的日期

        Returns:
            包含節假日資訊的回應
        """
        try:
            holiday_data = await self.holiday_client.get_holiday_info(check_date)

            if holiday_data is None:
                # 如果不是節假日，返回基本信息
                date_str = (
                    check_date
                    if isinstance(check_date, str)
                    else check_date.strftime("%Y-%m-%d")
                )
                return self._success_response(
                    HolidayInfoData(
                        date=date_str,
                        name="",
                        is_holiday=False,
                        holiday_category="",
                        description="非節假日",
                    )
                )

            # 返回節假日資訊
            response_data = HolidayInfoData(
                date=holiday_data.date,
                name=holiday_data.name,
                is_holiday=holiday_data.is_holiday,
                holiday_category=holiday_data.holiday_category,
                description=holiday_data.description,
            )

            return self._success_response(response_data)

        except Exception as e:
            self.logger.error(f"查詢節假日資訊失敗: {e}")
            return self._error_response(f"查詢節假日資訊失敗: {str(e)}")

    async def execute(self, **kwargs) -> MCPToolResponse[Any]:
        """執行節假日查詢"""
        check_date = kwargs.get("date")
        if not check_date:
            return self._error_response("缺少必要參數: date")

        return await self.get_holiday_info(check_date)


class TradingDayTool(ToolBase):
    """股市交易日判斷工具"""

    def __init__(self):
        super().__init__("trading_day_tool")
        self.holiday_client = TaiwanHolidayAPIClient()

    async def check_trading_day(
        self, check_date: date | str
    ) -> MCPToolResponse[TradingDayStatusData]:
        """
        檢查指定日期是否為股市交易日

        Args:
            check_date: 要檢查的日期

        Returns:
            包含交易日狀態的回應
        """
        try:
            # 統一日期格式
            if isinstance(check_date, str):
                try:
                    date_obj = datetime.strptime(check_date, "%Y-%m-%d").date()
                    date_str = check_date
                except ValueError:
                    return self._error_response(
                        f"日期格式錯誤，請使用 YYYY-MM-DD 格式: {check_date}"
                    )
            elif isinstance(check_date, date):
                date_obj = check_date
                date_str = check_date.strftime("%Y-%m-%d")
            else:
                return self._error_response(f"不支援的日期類型: {type(check_date)}")

            # 檢查是否為週末
            is_weekend = self.holiday_client.is_weekend(date_obj)

            # 檢查是否為國定假日
            holiday_data = await self.holiday_client.get_holiday_info(date_obj)
            is_holiday = holiday_data is not None and holiday_data.is_holiday
            holiday_name = holiday_data.name if holiday_data else None

            # 判斷是否為交易日
            is_trading_day = not is_weekend and not is_holiday

            # 決定不是交易日的原因
            if not is_trading_day:
                if is_weekend and is_holiday:
                    reason = f"週末且為國定假日（{holiday_name}）"
                elif is_weekend:
                    reason = "週末"
                elif is_holiday:
                    reason = f"國定假日（{holiday_name}）"
                else:
                    reason = "未知原因"
            else:
                reason = "是交易日"

            response_data = TradingDayStatusData(
                date=date_str,
                is_trading_day=is_trading_day,
                is_weekend=is_weekend,
                is_holiday=is_holiday,
                holiday_name=holiday_name,
                reason=reason,
            )

            return self._success_response(response_data)

        except Exception as e:
            self.logger.error(f"檢查交易日狀態失敗: {e}")
            return self._error_response(f"檢查交易日狀態失敗: {str(e)}")

    async def execute(self, **kwargs) -> MCPToolResponse[Any]:
        """執行交易日檢查"""
        check_date = kwargs.get("date")
        if not check_date:
            return self._error_response("缺少必要參數: date")

        return await self.check_trading_day(check_date)

    async def close(self):
        """關閉資源"""
        await self.holiday_client.close()
        super().close()
