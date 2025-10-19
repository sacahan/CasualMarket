"""
測試市場分析工具
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.tools.market import (
    ETFRankingTool,
    HistoricalIndexTool,
    HolidayTool,
    IndexInfoTool,
    MarginTradingTool,
    TradingDayTool,
    TradingStatsTool,
)


class TestMarketTools:
    """測試市場分析工具類別"""

    @pytest.fixture
    def mock_api_client(self):
        """模擬 API 客戶端"""
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture
    def mock_stock_client(self):
        """模擬股票客戶端"""
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture(autouse=True)
    def mock_dependencies(self, mock_api_client, mock_stock_client):
        """模擬所有依賴項"""
        with (
            patch(
                "src.tools.base.tool_base.OpenAPIClient", return_value=mock_api_client
            ),
            patch(
                "src.tools.base.tool_base.create_client", return_value=mock_stock_client
            ),
        ):
            yield

    @pytest.mark.asyncio
    async def test_etf_ranking_tool_success(self, mock_api_client):
        """測試 ETF 排行工具 - 成功案例"""
        # 準備測試數據 - 這是API返回的原始數據
        mock_raw_data = [
            {
                "證券代號": "0050",
                "證券名稱": "元大台灣50",
                "成交價": "130.25",
                "漲跌": "+1.25",
                "漲跌幅": "+0.97%",
                "成交量": "15,678",
                "周轉率": "0.85%",
            },
            {
                "證券代號": "0056",
                "證券名稱": "元大高股息",
                "成交價": "35.80",
                "漲跌": "+0.15",
                "漲跌幅": "+0.42%",
                "成交量": "45,231",
                "周轉率": "1.23%",
            },
        ]
        # Mock工具實際調用的方法
        mock_api_client.get_data.return_value = mock_raw_data

        # 執行測試
        tool = ETFRankingTool()
        result = await tool.execute()

        # 驗證結果 - 工具會包裝返回的數據
        assert result.success is True
        assert result.data["rankings"] == mock_raw_data
        assert result.data["total_count"] == len(mock_raw_data)
        assert result.data["displayed_count"] == len(mock_raw_data)
        assert result.data["ranking_date"] is None
        assert result.tool == "etf_ranking"
        assert result.metadata["source"] == "TWSE ETF Report"

        # 驗證 API 呼叫
        mock_api_client.get_data.assert_called_once_with("/ETFReport/ETFRank")

    @pytest.mark.asyncio
    async def test_historical_index_tool_success(self, mock_api_client):
        """測試歷史指數工具 - 成功案例"""
        # 準備測試數據 - 包含精選的重要指數
        mock_raw_data = [
            {
                "日期": "1141017",
                "指數": "發行量加權股價指數",
                "收盤指數": "27302",
                "漲跌": "-",
                "漲跌點數": "345.50",
                "漲跌百分比": "-1.25",
                "特殊處理註記": "",
            },
            {
                "日期": "1141017",
                "指數": "未含金融指數",
                "收盤指數": "24144",
                "漲跌": "-",
                "漲跌點數": "327.43",
                "漲跌百分比": "-1.34",
                "特殊處理註記": "",
            },
            {
                "日期": "1141017",
                "指數": "電子工業類指數",
                "收盤指數": "1621",
                "漲跌": "-",
                "漲跌點數": "26.38",
                "漲跌百分比": "-1.60",
                "特殊處理註記": "",
            },
            {
                "日期": "1141017",
                "指數": "其他指數",  # 不在精選列表中
                "收盤指數": "12345",
                "漲跌": "+",
                "漲跌點數": "100.00",
                "漲跌百分比": "+0.82",
                "特殊處理註記": "",
            },
        ]
        # Mock工具實際調用的方法
        mock_api_client.get_latest_market_data.return_value = mock_raw_data

        # 執行測試
        tool = HistoricalIndexTool()
        result = await tool.execute()

        # 驗證結果 - 只返回精選的重要指數，過濾掉其他指數
        assert result.success is True
        assert result.data["count"] == 3  # 只有3個在精選列表中
        assert len(result.data["indices"]) == 3
        assert result.data["indices"][0]["指數"] == "發行量加權股價指數"
        assert result.data["indices"][1]["指數"] == "未含金融指數"
        assert result.data["indices"][2]["指數"] == "電子工業類指數"
        assert result.tool == "historical_index"
        assert result.metadata["source"] == "TWSE Exchange Report"

        # 驗證 API 呼叫
        mock_api_client.get_latest_market_data.assert_called_once_with(
            "/exchangeReport/MI_INDEX"
        )

    @pytest.mark.asyncio
    async def test_index_info_tool_success(self, mock_api_client):
        """測試指數資訊工具 - 成功案例"""
        # 準備測試數據 - 這是API返回的原始數據
        mock_raw_data = [
            {
                "指數": "臺灣發行量加權股價指數",
                "收盤指數": "17,632.83",
                "漲跌": "+152.58",
                "漲跌幅": "+0.87%",
                "開盤指數": "17,500.25",
                "最高指數": "17,685.40",
                "最低指數": "17,420.15",
            },
            {
                "指數": "臺灣50指數",
                "收盤指數": "14,235.67",
                "漲跌": "+85.42",
                "漲跌幅": "+0.60%",
                "開盤指數": "14,150.25",
                "最高指數": "14,285.40",
                "最低指數": "14,120.15",
            },
        ]
        # Mock工具實際調用的方法 - 返回包含發行量加權股價指數的數據
        mock_api_client.get_latest_market_data.return_value = [
            {
                "日期": "1141017",
                "指數": "發行量加權股價指數",
                "收盤指數": "27302",
                "漲跌": "-",
                "漲跌點數": "345.50",
                "漲跌百分比": "-1.25",
                "特殊處理註記": "",
            },
            {
                "日期": "1141017",
                "指數": "其他指數",
                "收盤指數": "12345",
                "漲跌": "+",
                "漲跌點數": "123.45",
                "漲跌百分比": "+1.01",
                "特殊處理註記": "",
            },
        ]

        # 執行測試
        tool = IndexInfoTool()
        result = await tool.execute()

        # 驗證結果 - 只返回發行量加權股價指數
        assert result.success is True
        assert result.data["指數"] == "發行量加權股價指數"
        assert result.data["收盤指數"] == "27302"
        assert result.tool == "index_info"
        assert result.metadata["source"] == "TWSE Market Index Report"

        # 驗證 API 呼叫
        mock_api_client.get_latest_market_data.assert_called_once_with(
            "/exchangeReport/MI_INDEX"
        )

    @pytest.mark.asyncio
    async def test_margin_trading_tool_success(self, mock_api_client):
        """測試融資融券工具 - 成功案例"""
        # 準備測試數據 - 這是API返回的原始數據
        mock_raw_data = [
            {
                "股票代號": "2330",
                "股票名稱": "台積電",
                "融資餘額": "125,678",
                "融資變化": "+1,234",
                "融券餘額": "45,231",
                "融券變化": "-567",
                "融資使用率": "65.4%",
                "券資比": "0.36",
            },
            {
                "股票代號": "2317",
                "股票名稱": "鴻海",
                "融資餘額": "85,432",
                "融資變化": "-567",
                "融券餘額": "23,145",
                "融券變化": "+234",
                "融資使用率": "45.2%",
                "券資比": "0.27",
            },
        ]
        # Mock工具實際調用的方法
        mock_api_client.get_data.return_value = mock_raw_data

        # 執行測試
        tool = MarginTradingTool()
        result = await tool.execute(symbol="2330")

        # 驗證結果 - 工具會包裝返回的數據
        assert result.success is True
        assert result.data["margin_data"] == mock_raw_data
        assert result.data["total_count"] == len(mock_raw_data)
        assert result.data["displayed_count"] == len(mock_raw_data)
        assert result.tool == "margin_trading"
        assert result.metadata["source"] == "TWSE Margin Trading Report"

        # 驗證 API 呼叫
        mock_api_client.get_data.assert_called_once_with("/exchangeReport/MI_MARGN")

    @pytest.mark.asyncio
    async def test_trading_stats_tool_success(self, mock_api_client):
        """測試交易統計工具 - 成功案例"""
        # 準備測試數據 - 這是API返回的原始數據
        mock_raw_data = [
            {
                "時間": "09:00",
                "成交金額": "2,456,789百萬元",
                "成交量": "4,567,890千股",
                "成交筆數": "1,234,567筆",
                "指數": "17,632.83",
            },
            {
                "時間": "09:05",
                "成交金額": "2,567,890百萬元",
                "成交量": "4,678,901千股",
                "成交筆數": "1,345,678筆",
                "指數": "17,645.21",
            },
        ]
        # Mock工具實際調用的方法
        mock_api_client.get_latest_market_data.return_value = mock_raw_data

        # 執行測試
        tool = TradingStatsTool()
        result = await tool.execute(date="2024-01-15")

        # 驗證結果 - 工具會包裝返回的數據
        assert result.success is True
        assert result.data["trading_stats"] == mock_raw_data
        assert result.data["count"] == len(mock_raw_data)
        assert result.data["frequency"] == "5_minutes"
        assert result.tool == "trading_stats"
        assert result.metadata["source"] == "TWSE Real-time Trading Statistics"

        # 驗證 API 呼叫
        mock_api_client.get_latest_market_data.assert_called_once_with(
            "/exchangeReport/MI_5MINS", count=10
        )

    @pytest.mark.asyncio
    async def test_etf_ranking_tool_no_data(self, mock_api_client):
        """測試 ETF 排行工具 - 找不到資料"""
        # 設定 API 回傳空資料
        mock_api_client.get_data.return_value = None

        # 執行測試
        tool = ETFRankingTool()
        result = await tool.execute()

        # 驗證結果
        assert result.success is False
        assert "No ETF ranking data available" in result.error
        assert result.tool == "etf_ranking"

    @pytest.mark.asyncio
    async def test_margin_trading_tool_exception(self, mock_api_client):
        """測試融資融券工具 - 異常處理"""
        # 設定 API 拋出異常
        mock_api_client.get_data.side_effect = Exception("API 連線失敗")

        # 執行測試
        tool = MarginTradingTool()
        result = await tool.execute(symbol="2330")

        # 驗證結果
        assert result.success is False
        assert "API 連線失敗" in result.error
        assert result.tool == "margin_trading"

    @pytest.mark.asyncio
    async def test_trading_stats_tool_invalid_date(self, mock_api_client):
        """測試交易統計工具 - 無效日期"""
        # 設定 API 回傳空資料表示無效日期
        mock_api_client.get_latest_market_data.return_value = None

        # 執行測試
        tool = TradingStatsTool()
        result = await tool.execute(date="invalid-date")

        # 驗證結果
        assert result.success is False
        assert "No real-time trading stats available" in result.error
        assert result.tool == "trading_stats"

    @pytest.mark.asyncio
    async def test_historical_index_tool_with_default_date(self, mock_api_client):
        """測試歷史指數工具 - 使用預設日期"""
        # 準備測試數據 - 包含一個重要指數
        mock_raw_data = [{"指數": "發行量加權股價指數", "收盤指數": "17,632.83"}]
        mock_api_client.get_latest_market_data.return_value = mock_raw_data

        # 執行測試（不提供日期參數）
        tool = HistoricalIndexTool()
        result = await tool.execute()

        # 驗證結果
        assert result.success is True
        assert len(result.data["indices"]) == 1  # 只有一個重要指數
        assert result.data["count"] == 1
        assert result.data["indices"][0]["指數"] == "發行量加權股價指數"

        # 驗證 API 被呼叫（應該使用預設日期或當日）
        mock_api_client.get_latest_market_data.assert_called_once_with(
            "/exchangeReport/MI_INDEX"
        )

    @pytest.mark.asyncio
    async def test_index_info_tool_multiple_indices(self, mock_api_client):
        """測試指數資訊工具 - 多個指數"""
        # 準備測試數據
        mock_raw_data = [
            {
                "指數": "臺灣發行量加權股價指數",
                "收盤指數": "17,632.83",
                "漲跌": "+152.58",
                "漲跌幅": "+0.87%",
            },
            {
                "指數": "臺灣50指數",
                "收盤指數": "14,235.67",
                "漲跌": "+85.42",
                "漲跌幅": "+0.60%",
            },
        ]
        # 添加發行量加權股價指數到測試數據中
        mock_raw_data.append(
            {
                "日期": "1141017",
                "指數": "發行量加權股價指數",
                "收盤指數": "14500.50",
                "漲跌": "+",
                "漲跌點數": "85.42",
                "漲跌百分比": "+0.59",
                "特殊處理註記": "",
            }
        )
        mock_api_client.get_latest_market_data.return_value = mock_raw_data

        # 執行測試
        tool = IndexInfoTool()
        result = await tool.execute()

        # 驗證結果 - 只返回發行量加權股價指數
        assert result.success is True
        assert result.data["指數"] == "發行量加權股價指數"
        assert result.data["收盤指數"] == "14500.50"

    def test_tool_names(self):
        """測試工具名稱正確性"""
        assert ETFRankingTool().name == "etf_ranking"
        assert HistoricalIndexTool().name == "historical_index"
        assert IndexInfoTool().name == "index_info"
        assert MarginTradingTool().name == "margin_trading"
        assert TradingStatsTool().name == "trading_stats"
        assert HolidayTool().name == "holiday_tool"
        assert TradingDayTool().name == "trading_day_tool"

    @pytest.mark.asyncio
    async def test_tool_safe_execute(self, mock_api_client):
        """測試工具的 safe_execute 方法"""
        # 準備測試數據
        mock_raw_data = [{"test": "data"}]
        mock_api_client.get_data.return_value = mock_raw_data

        # 執行測試
        tool = ETFRankingTool()
        result = await tool.safe_execute()

        # 驗證結果
        assert result.success is True
        assert result.data["rankings"] == mock_raw_data
        assert result.data["total_count"] == 1
        assert result.data["displayed_count"] == 1

    @pytest.mark.asyncio
    async def test_tool_context_manager(self):
        """測試工具的上下文管理器"""
        with ETFRankingTool() as tool:
            assert tool is not None
            assert tool.name == "etf_ranking"

    # === 節假日工具測試 ===

    @pytest.mark.asyncio
    async def test_holiday_tool_success_holiday(self):
        """測試節假日工具 - 查詢國定假日成功案例"""
        # 準備測試數據 - 模擬節假日API返回的數據
        mock_holiday_data = {
            "_id": 1528,
            "date": "20251006",
            "name": "中秋節",
            "isHoliday": 1,
            "holidaycategory": "放假之紀念日及節日",
            "description": "全國各機關學校放假一日。",
        }

        with patch(
            "src.tools.market.holiday_tool.TaiwanHolidayAPIClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # 模擬 HolidayData 對象
            from src.api.holiday_client import HolidayData

            mock_holiday_obj = HolidayData(mock_holiday_data)
            mock_client.get_holiday_info.return_value = mock_holiday_obj

            # 執行測試
            tool = HolidayTool()
            result = await tool.execute(date="2025-10-06")

            # 驗證結果
            assert result.success is True
            assert result.data.date == "20251006"
            assert result.data.name == "中秋節"
            assert result.data.is_holiday is True
            assert result.data.holiday_category == "放假之紀念日及節日"
            assert result.data.description == "全國各機關學校放假一日。"
            assert result.tool == "holiday_tool"

            # 驗證 API 呼叫
            mock_client.get_holiday_info.assert_called_once_with("2025-10-06")

    @pytest.mark.asyncio
    async def test_holiday_tool_success_no_holiday(self):
        """測試節假日工具 - 查詢非節假日成功案例"""
        with patch(
            "src.tools.market.holiday_tool.TaiwanHolidayAPIClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # 模擬非節假日情況（返回 None）
            mock_client.get_holiday_info.return_value = None

            # 執行測試
            tool = HolidayTool()
            result = await tool.execute(date="2025-10-07")

            # 驗證結果
            assert result.success is True
            assert result.data.date == "2025-10-07"
            assert result.data.name == ""
            assert result.data.is_holiday is False
            assert result.data.holiday_category == ""
            assert result.data.description == "非節假日"
            assert result.tool == "holiday_tool"

    @pytest.mark.asyncio
    async def test_trading_day_tool_success_trading_day(self):
        """測試交易日工具 - 正常交易日成功案例"""
        with patch(
            "src.tools.market.holiday_tool.TaiwanHolidayAPIClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # 模擬工作日（非週末、非節假日）
            # is_weekend 是同步方法,使用 Mock 而不是 AsyncMock
            from unittest.mock import Mock
            mock_client.is_weekend = Mock(return_value=False)
            mock_client.get_holiday_info = AsyncMock(return_value=None)

            # 執行測試
            tool = TradingDayTool()
            result = await tool.execute(date="2025-10-07")  # 假設是週二

            # 驗證結果
            assert result.success is True
            assert result.data.date == "2025-10-07"
            assert result.data.is_trading_day is True
            assert result.data.is_weekend is False
            assert result.data.is_holiday is False
            assert result.data.holiday_name is None
            assert result.data.reason == "是交易日"
            assert result.tool == "trading_day_tool"

    @pytest.mark.asyncio
    async def test_trading_day_tool_success_weekend(self):
        """測試交易日工具 - 週末非交易日案例"""
        with patch(
            "src.tools.market.holiday_tool.TaiwanHolidayAPIClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # 模擬週末
            # is_weekend 是同步方法,使用 Mock 而不是 AsyncMock
            from unittest.mock import Mock
            mock_client.is_weekend = Mock(return_value=True)
            mock_client.get_holiday_info = AsyncMock(return_value=None)

            # 執行測試
            tool = TradingDayTool()
            result = await tool.execute(date="2025-10-11")  # 假設是週六

            # 驗證結果
            assert result.success is True
            assert result.data.date == "2025-10-11"
            assert result.data.is_trading_day is False
            assert result.data.is_weekend is True
            assert result.data.is_holiday is False
            assert result.data.holiday_name is None
            assert result.data.reason == "週末"
            assert result.tool == "trading_day_tool"

    @pytest.mark.asyncio
    async def test_trading_day_tool_success_holiday(self):
        """測試交易日工具 - 國定假日非交易日案例"""
        # 準備測試數據
        mock_holiday_data = {
            "_id": 1528,
            "date": "20251006",
            "name": "中秋節",
            "isHoliday": 1,
            "holidaycategory": "放假之紀念日及節日",
            "description": "全國各機關學校放假一日。",
        }

        with patch(
            "src.tools.market.holiday_tool.TaiwanHolidayAPIClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # 模擬國定假日（非週末）
            from src.api.holiday_client import HolidayData
            from unittest.mock import Mock

            mock_holiday_obj = HolidayData(mock_holiday_data)
            # is_weekend 是同步方法,使用 Mock 而不是 AsyncMock
            mock_client.is_weekend = Mock(return_value=False)
            mock_client.get_holiday_info = AsyncMock(return_value=mock_holiday_obj)

            # 執行測試
            tool = TradingDayTool()
            result = await tool.execute(date="2025-10-06")

            # 驗證結果
            assert result.success is True
            assert result.data.date == "2025-10-06"
            assert result.data.is_trading_day is False
            assert result.data.is_weekend is False
            assert result.data.is_holiday is True
            assert result.data.holiday_name == "中秋節"
            assert result.data.reason == "國定假日（中秋節）"
            assert result.tool == "trading_day_tool"

    @pytest.mark.asyncio
    async def test_holiday_tool_error_missing_date(self):
        """測試節假日工具 - 缺少日期參數錯誤案例"""
        tool = HolidayTool()
        result = await tool.execute()

        # 驗證錯誤結果
        assert result.success is False
        assert "缺少必要參數: date" in result.error
        assert result.tool == "holiday_tool"

    @pytest.mark.asyncio
    async def test_trading_day_tool_error_missing_date(self):
        """測試交易日工具 - 缺少日期參數錯誤案例"""
        tool = TradingDayTool()
        result = await tool.execute()

        # 驗證錯誤結果
        assert result.success is False
        assert "缺少必要參數: date" in result.error
        assert result.tool == "trading_day_tool"

    @pytest.mark.asyncio
    async def test_trading_day_tool_error_invalid_date_format(self):
        """測試交易日工具 - 無效日期格式錯誤案例"""
        tool = TradingDayTool()
        result = await tool.execute(date="invalid-date")

        # 驗證錯誤結果
        assert result.success is False
        assert "日期格式錯誤" in result.error
        assert result.tool == "trading_day_tool"
