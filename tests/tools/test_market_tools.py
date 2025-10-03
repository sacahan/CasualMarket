"""
測試市場分析工具
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.tools.market import (
    ETFRankingTool,
    HistoricalIndexTool,
    IndexInfoTool,
    MarginTradingTool,
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
        # 準備測試數據
        mock_data = [
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
        mock_api_client.get_etf_ranking.return_value = mock_data

        # 執行測試
        tool = ETFRankingTool()
        result = await tool.execute()

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert result["tool"] == "etf_ranking"
        assert len(result["data"]) == 2

        # 驗證 API 呼叫
        mock_api_client.get_etf_ranking.assert_called_once()

    @pytest.mark.asyncio
    async def test_historical_index_tool_success(self, mock_api_client):
        """測試歷史指數工具 - 成功案例"""
        # 準備測試數據
        mock_data = {
            "指數名稱": "臺灣加權股價指數",
            "日期": "2024/01/15",
            "開盤指數": "17,500.25",
            "最高指數": "17,685.40",
            "最低指數": "17,420.15",
            "收盤指數": "17,632.83",
            "漲跌點數": "+152.58",
            "漲跌幅": "+0.87%",
            "成交量": "2,456,789",
        }
        mock_api_client.get_historical_index.return_value = mock_data

        # 執行測試
        tool = HistoricalIndexTool()
        result = await tool.execute(date="2024-01-15")

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert result["tool"] == "historical_index"

        # 驗證 API 呼叫
        mock_api_client.get_historical_index.assert_called_once_with("2024-01-15")

    @pytest.mark.asyncio
    async def test_index_info_tool_success(self, mock_api_client):
        """測試指數資訊工具 - 成功案例"""
        # 準備測試數據
        mock_data = {
            "指數代號": "TAIEX",
            "指數名稱": "臺灣加權股價指數",
            "現值": "17,632.83",
            "漲跌": "+152.58",
            "漲跌幅": "+0.87%",
            "開盤": "17,500.25",
            "最高": "17,685.40",
            "最低": "17,420.15",
            "成交量": "2,456,789千股",
            "成交值": "245,678百萬元",
        }
        mock_api_client.get_index_info.return_value = mock_data

        # 執行測試
        tool = IndexInfoTool()
        result = await tool.execute(index="TAIEX")

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert result["tool"] == "index_info"

        # 驗證 API 呼叫
        mock_api_client.get_index_info.assert_called_once_with("TAIEX")

    @pytest.mark.asyncio
    async def test_margin_trading_tool_success(self, mock_api_client):
        """測試融資融券工具 - 成功案例"""
        # 準備測試數據
        mock_data = {
            "股票代號": "2330",
            "股票名稱": "台積電",
            "融資餘額": "125,678",
            "融資變化": "+1,234",
            "融券餘額": "45,231",
            "融券變化": "-567",
            "融資使用率": "65.4%",
            "券資比": "0.36",
            "更新日期": "2024/01/15",
        }
        mock_api_client.get_margin_trading_data.return_value = mock_data

        # 執行測試
        tool = MarginTradingTool()
        result = await tool.execute(symbol="2330")

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert result["tool"] == "margin_trading"

        # 驗證 API 呼叫
        mock_api_client.get_margin_trading_data.assert_called_once_with("2330")

    @pytest.mark.asyncio
    async def test_trading_stats_tool_success(self, mock_api_client):
        """測試交易統計工具 - 成功案例"""
        # 準備測試數據
        mock_data = {
            "日期": "2024/01/15",
            "成交金額": "2,456,789百萬元",
            "成交量": "4,567,890千股",
            "成交筆數": "1,234,567筆",
            "上漲家數": "567",
            "下跌家數": "432",
            "持平家數": "89",
            "平均成交金額": "2,234萬元",
            "當日沖銷交易標的": "1,789檔",
            "當日沖銷成交金額": "456,789百萬元",
        }
        mock_api_client.get_trading_stats.return_value = mock_data

        # 執行測試
        tool = TradingStatsTool()
        result = await tool.execute(date="2024-01-15")

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert result["tool"] == "trading_stats"

        # 驗證 API 呼叫
        mock_api_client.get_trading_stats.assert_called_once_with("2024-01-15")

    @pytest.mark.asyncio
    async def test_etf_ranking_tool_no_data(self, mock_api_client):
        """測試 ETF 排行工具 - 找不到資料"""
        # 設定 API 回傳空資料
        mock_api_client.get_etf_ranking.return_value = None

        # 執行測試
        tool = ETFRankingTool()
        result = await tool.execute()

        # 驗證結果
        assert result["success"] is False
        assert "找不到 ETF 排行資料" in result["error"]
        assert result["tool"] == "etf_ranking"

    @pytest.mark.asyncio
    async def test_margin_trading_tool_exception(self, mock_api_client):
        """測試融資融券工具 - 異常處理"""
        # 設定 API 拋出異常
        mock_api_client.get_margin_trading_data.side_effect = Exception("API 連線失敗")

        # 執行測試
        tool = MarginTradingTool()
        result = await tool.execute(symbol="2330")

        # 驗證結果
        assert result["success"] is False
        assert "API 連線失敗" in result["error"]
        assert result["tool"] == "margin_trading"

    @pytest.mark.asyncio
    async def test_trading_stats_tool_invalid_date(self, mock_api_client):
        """測試交易統計工具 - 無效日期"""
        # 設定 API 回傳空資料表示無效日期
        mock_api_client.get_trading_stats.return_value = None

        # 執行測試
        tool = TradingStatsTool()
        result = await tool.execute(date="invalid-date")

        # 驗證結果
        assert result["success"] is False
        assert "找不到" in result["error"]
        assert result["tool"] == "trading_stats"

    @pytest.mark.asyncio
    async def test_historical_index_tool_with_default_date(self, mock_api_client):
        """測試歷史指數工具 - 使用預設日期"""
        # 準備測試數據
        mock_data = {"指數名稱": "臺灣加權股價指數", "收盤指數": "17,632.83"}
        mock_api_client.get_historical_index.return_value = mock_data

        # 執行測試（不提供日期參數）
        tool = HistoricalIndexTool()
        result = await tool.execute()

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data

        # 驗證 API 被呼叫（應該使用預設日期或當日）
        mock_api_client.get_historical_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_info_tool_multiple_indices(self, mock_api_client):
        """測試指數資訊工具 - 多個指數"""
        # 準備測試數據
        mock_data = [
            {
                "指數代號": "TAIEX",
                "指數名稱": "臺灣加權股價指數",
                "現值": "17,632.83",
            },
            {
                "指數代號": "OTC",
                "指數名稱": "櫃買指數",
                "現值": "185.45",
            },
        ]
        mock_api_client.get_index_info.return_value = mock_data

        # 執行測試
        tool = IndexInfoTool()
        result = await tool.execute()  # 不指定特定指數，取得所有指數

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert len(result["data"]) == 2

    def test_tool_names(self):
        """測試工具名稱正確性"""
        assert ETFRankingTool().name == "etf_ranking"
        assert HistoricalIndexTool().name == "historical_index"
        assert IndexInfoTool().name == "index_info"
        assert MarginTradingTool().name == "margin_trading"
        assert TradingStatsTool().name == "trading_stats"

    @pytest.mark.asyncio
    async def test_tool_safe_execute(self, mock_api_client):
        """測試工具的 safe_execute 方法"""
        # 準備測試數據
        mock_data = {"test": "data"}
        mock_api_client.get_etf_ranking.return_value = mock_data

        # 執行測試
        tool = ETFRankingTool()
        result = await tool.safe_execute()

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data

    @pytest.mark.asyncio
    async def test_tool_context_manager(self):
        """測試工具的上下文管理器"""
        with ETFRankingTool() as tool:
            assert tool is not None
            assert tool.name == "etf_ranking"
