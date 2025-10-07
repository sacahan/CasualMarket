"""
MCP 工具統一回應模型定義。

定義所有 MCP 工具的標準回應格式，確保一致性和類型安全。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# 定義泛型類型變量，用於強類型的資料欄位
T = TypeVar("T")


class MCPToolResponse(BaseModel, Generic[T]):
    """
    MCP 工具統一回應格式基類。

    所有 MCP 工具都應該返回此格式的資料，以確保一致性。
    """

    success: bool = Field(..., description="操作是否成功")
    data: T | None = Field(default=None, description="成功時的回傳資料")
    error: str | None = Field(default=None, description="失敗時的錯誤訊息")
    tool: str = Field(..., description="工具名稱")
    timestamp: datetime = Field(default_factory=datetime.now, description="回應時間戳")
    metadata: dict[str, Any] = Field(default_factory=dict, description="額外的元資料")

    class Config:
        """Pydantic 配置"""

        # 允許任意類型，用於泛型支援
        arbitrary_types_allowed = True
        # 使用 enum 值而非名稱進行序列化
        use_enum_values = True
        # JSON 編碼器配置
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class StockPriceData(BaseModel):
    """股票價格資料模型"""

    symbol: str = Field(..., description="股票代碼")
    company_name: str = Field(..., description="公司名稱")
    current_price: float = Field(..., description="當前價格")
    change: float = Field(..., description="漲跌金額")
    change_percent: float = Field(..., description="漲跌幅百分比")
    volume: int = Field(..., description="成交量")
    high: float = Field(..., description="最高價")
    low: float = Field(..., description="最低價")
    open: float = Field(..., description="開盤價")
    previous_close: float = Field(..., description="昨收價")
    last_update: str | None = Field(default=None, description="最後更新時間")


class CompanyProfileData(BaseModel):
    """公司基本資料模型"""

    symbol: str = Field(..., description="股票代碼")
    company_name: str = Field(..., description="公司名稱")
    industry: str = Field(..., description="行業別")
    chairman: str | None = Field(default=None, description="董事長")
    established: str | None = Field(default=None, description="成立日期")
    capital: int | None = Field(default=None, description="實收資本額")
    employees: int | None = Field(default=None, description="員工人數")
    website: str | None = Field(default=None, description="公司網站")


class ValuationRatiosData(BaseModel):
    """估值比率資料模型"""

    symbol: str = Field(..., description="股票代碼")
    pe_ratio: float | None = Field(default=None, description="本益比")
    pb_ratio: float | None = Field(default=None, description="股價淨值比")
    dividend_yield: float | None = Field(default=None, description="殖利率")
    roe: float | None = Field(default=None, description="股東權益報酬率")
    eps: float | None = Field(default=None, description="每股盈餘")
    book_value: float | None = Field(default=None, description="每股淨值")


class TradingResultData(BaseModel):
    """交易結果資料模型"""

    symbol: str = Field(..., description="股票代碼")
    action: str = Field(..., description="交易動作 (buy/sell)")
    quantity: int = Field(..., description="交易股數")
    price: float = Field(..., description="交易價格")
    total_amount: float = Field(..., description="交易總金額")
    fee: float = Field(..., description="手續費")
    tax: float = Field(default=0.0, description="交易稅")
    net_amount: float = Field(..., description="實際金額")
    timestamp: datetime = Field(default_factory=datetime.now, description="交易時間")


class MarketIndexData(BaseModel):
    """市場指數資料模型"""

    index_name: str = Field(..., description="指數名稱")
    current_value: float = Field(..., description="當前指數值")
    change: float = Field(..., description="漲跌點數")
    change_percent: float = Field(..., description="漲跌幅百分比")
    volume: int | None = Field(default=None, description="成交量")
    last_update: str | None = Field(default=None, description="最後更新時間")


class ForeignInvestmentData(BaseModel):
    """外資投資資料模型"""

    industry: str | None = Field(default=None, description="產業別")
    symbol: str | None = Field(default=None, description="股票代碼")
    company_name: str | None = Field(default=None, description="公司名稱")
    foreign_holding: int | None = Field(default=None, description="外資持股張數")
    percentage: float | None = Field(default=None, description="外資持股比例")
    recent_change: int | None = Field(default=None, description="近期變化")
    rank: int | None = Field(default=None, description="排名")


class HolidayInfoData(BaseModel):
    """節假日資訊模型"""

    date: str = Field(..., description="日期 (YYYY-MM-DD)")
    name: str = Field(..., description="節假日名稱")
    is_holiday: bool = Field(..., description="是否為節假日")
    holiday_category: str = Field(..., description="節假日類別")
    description: str = Field(..., description="節假日描述")


class TradingDayStatusData(BaseModel):
    """交易日狀態資料模型"""

    date: str = Field(..., description="查詢日期 (YYYY-MM-DD)")
    is_trading_day: bool = Field(..., description="是否為交易日")
    is_weekend: bool = Field(..., description="是否為週末")
    is_holiday: bool = Field(..., description="是否為國定假日")
    holiday_name: str | None = Field(
        default=None, description="節假日名稱（如果是節假日）"
    )
    reason: str = Field(..., description="不是交易日的原因（如果不是交易日）")


# 常用的類型別名，便於使用
StockPriceResponse = MCPToolResponse[StockPriceData]
CompanyProfileResponse = MCPToolResponse[CompanyProfileData]
ValuationRatiosResponse = MCPToolResponse[ValuationRatiosData]
TradingResultResponse = MCPToolResponse[TradingResultData]
MarketIndexResponse = MCPToolResponse[list[MarketIndexData]]
ForeignInvestmentResponse = MCPToolResponse[list[ForeignInvestmentData]]

# 通用回應類型
GenericResponse = MCPToolResponse[dict[str, Any]]


def create_success_response[T](
    data: T,
    tool: str,
    metadata: dict[str, Any] | None = None,
) -> MCPToolResponse[T]:
    """
    創建成功回應的輔助函數。

    Args:
        data: 回傳的資料
        tool: 工具名稱
        metadata: 額外的元資料

    Returns:
        標準格式的成功回應
    """
    return MCPToolResponse[T](
        success=True,
        data=data,
        tool=tool,
        metadata=metadata or {},
    )


def create_error_response(
    error: str,
    tool: str,
    metadata: dict[str, Any] | None = None,
) -> MCPToolResponse[None]:
    """
    創建錯誤回應的輔助函數。

    Args:
        error: 錯誤訊息
        tool: 工具名稱
        metadata: 額外的元資料

    Returns:
        標準格式的錯誤回應
    """
    return MCPToolResponse[None](
        success=False,
        error=error,
        tool=tool,
        metadata=metadata or {},
    )
