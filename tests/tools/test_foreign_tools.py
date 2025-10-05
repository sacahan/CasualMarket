"""
測試外資分析工具
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.tools.foreign import ForeignInvestmentTool


class TestForeignTools:
    """測試外資分析工具類別"""

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
    async def test_foreign_investment_tool_success(self, mock_api_client):
        """測試外資投資工具 - 成功案例"""
        # 準備測試數據
        mock_data = {
            "外資買賣超統計": {
                "日期": "2024/01/15",
                "外資買進": "15,678,900千元",
                "外資賣出": "12,345,600千元",
                "外資買賣超": "+3,333,300千元",
                "外資持股比例": "42.5%",
            },
            "前十大外資買超股票": [
                {
                    "股票代號": "2330",
                    "股票名稱": "台積電",
                    "外資買超": "+1,234,567千元",
                    "外資持股比例": "78.5%",
                },
                {
                    "股票代號": "2317",
                    "股票名稱": "鴻海",
                    "外資買超": "+567,890千元",
                    "外資持股比例": "35.2%",
                },
            ],
            "前十大外資賣超股票": [
                {
                    "股票代號": "2454",
                    "股票名稱": "聯發科",
                    "外資賣超": "-234,567千元",
                    "外資持股比例": "68.9%",
                },
            ],
        }
        # Mock the get_data method instead since that's what the tool calls
        mock_api_client.get_data.return_value = [
            mock_data
        ]  # Wrap in list since tool expects array

        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.execute(date="2024-01-15")

        # 驗證結果 - data structure is wrapped by the tool
        assert result["success"] is True
        assert result["data"]["industry_foreign_investment"] == [mock_data]
        assert result["data"]["total_industries"] == 1
        assert result["tool"] == "foreign_investment"

        # 驗證 API 呼叫
        mock_api_client.get_data.assert_called_once_with("/fund/MI_QFIIS_cat")

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_by_industry(self, mock_api_client):
        """測試外資投資工具 - 依產業別分析"""
        # 準備測試數據 - 這是API返回的原始數據
        mock_raw_data = [
            {
                "產業別": "半導體業",
                "外資買超": "+5,678,900千元",
                "主要標的": ["2330 台積電", "2454 聯發科", "3034 聯詠"],
            },
            {
                "產業別": "電腦及週邊設備業",
                "外資買超": "+1,234,500千元",
                "主要標的": ["2317 鴻海", "2382 廣達", "2408 南亞科"],
            },
            {
                "產業別": "金融保險業",
                "外資賣超": "-567,800千元",
                "主要標的": ["2891 中信金", "2884 玉山金", "2892 第一金"],
            },
        ]
        # Mock工具實際調用的方法
        mock_api_client.get_data.return_value = mock_raw_data

        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.execute(action="industry", date="2024-01-15")

        # 驗證結果 - 工具會包裝返回的數據
        assert result["success"] is True
        assert result["data"]["industry_foreign_investment"] == mock_raw_data
        assert result["data"]["total_industries"] == len(mock_raw_data)
        assert result["tool"] == "foreign_investment"
        assert result["source"] == "TWSE Fund Report"

        # 驗證 API 呼叫
        mock_api_client.get_data.assert_called_once_with("/fund/MI_QFIIS_cat")

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_top_holdings(self, mock_api_client):
        """測試外資投資工具 - 外資持股前20名"""
        # 準備測試數據 - 這是API返回的原始數據
        mock_raw_data = [
            {
                "股票代號": "2330",
                "股票名稱": "台積電",
                "外資持股比例": "78.5%",
                "外資持股張數": "25,678,900",
            },
            {
                "股票代號": "2317",
                "股票名稱": "鴻海",
                "外資持股比例": "35.2%",
                "外資持股張數": "12,345,600",
            },
        ]
        # Mock工具實際調用的方法
        mock_api_client.get_data.return_value = mock_raw_data

        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.execute(action="top_holdings")

        # 驗證結果 - 工具會包裝返回的數據
        assert result["success"] is True
        assert result["data"]["top_foreign_holdings"] == mock_raw_data
        assert result["data"]["count"] == len(mock_raw_data)
        assert result["tool"] == "foreign_investment"
        assert result["source"] == "TWSE Fund Report"

        # 驗證 API 呼叫
        mock_api_client.get_data.assert_called_once_with("/fund/MI_QFIIS_sort_20")

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_no_data(self, mock_api_client):
        """測試外資投資工具 - 找不到資料"""
        # 設定 API 回傳空資料
        mock_api_client.get_data.return_value = None

        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.execute(action="industry")

        # 驗證結果
        assert result["success"] is False
        assert "No foreign investment data by industry available" in result["error"]
        assert result["tool"] == "foreign_investment"

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_exception(self, mock_api_client):
        """測試外資投資工具 - 異常處理"""
        # 設定 API 拋出異常
        mock_api_client.get_data.side_effect = Exception("API 連線失敗")

        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.execute(action="industry")

        # 驗證結果
        assert result["success"] is False
        assert "API 連線失敗" in result["error"]
        assert result["tool"] == "foreign_investment"

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_default_date(self, mock_api_client):
        """測試外資投資工具 - 使用預設日期"""
        # 準備測試數據
        mock_raw_data = [{"產業別": "測試產業", "外資買賣超": "+1,000千元"}]
        mock_api_client.get_data.return_value = mock_raw_data

        # 執行測試（不提供日期參數，預設action為industry）
        tool = ForeignInvestmentTool()
        result = await tool.execute()

        # 驗證結果
        assert result["success"] is True
        assert result["data"]["industry_foreign_investment"] == mock_raw_data
        assert result["data"]["total_industries"] == 1

        # 驗證 API 被呼叫（應該使用預設action=industry）
        mock_api_client.get_data.assert_called_once_with("/fund/MI_QFIIS_cat")

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_invalid_action(self, mock_api_client):
        """測試外資投資工具 - 無效action處理"""
        # 執行測試 - 使用無效的action
        tool = ForeignInvestmentTool()
        result = await tool.execute(action="invalid_action")

        # 驗證結果 - 應該返回錯誤
        assert result["success"] is False
        assert "Unknown action: invalid_action" in result["error"]
        assert result["tool"] == "foreign_investment"

        # 驗證沒有API呼叫
        mock_api_client.get_data.assert_not_called()

    def test_foreign_investment_tool_name(self):
        """測試工具名稱正確性"""
        tool = ForeignInvestmentTool()
        assert tool.name == "foreign_investment"

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_safe_execute(self, mock_api_client):
        """測試外資投資工具的 safe_execute 方法"""
        # 準備測試數據
        mock_raw_data = [{"test": "data"}]
        mock_api_client.get_data.return_value = mock_raw_data

        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.safe_execute(action="industry")

        # 驗證結果
        assert result["success"] is True
        assert result["data"]["industry_foreign_investment"] == mock_raw_data
        assert result["data"]["total_industries"] == 1

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_context_manager(self):
        """測試外資投資工具的上下文管理器"""
        with ForeignInvestmentTool() as tool:
            assert tool is not None
            assert tool.name == "foreign_investment"

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_invalid_analysis_type(self, mock_api_client):
        """測試外資投資工具 - 無效分析類型"""
        # 執行測試 - 使用無效的action
        tool = ForeignInvestmentTool()
        result = await tool.execute(action="invalid_type")

        # 驗證結果應該返回錯誤
        assert result["success"] is False
        assert "Unknown action: invalid_type" in result["error"]

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_multiple_params(self, mock_api_client):
        """測試外資投資工具 - 多參數組合"""
        # 準備測試數據
        mock_raw_data = [{"combined_analysis": "test_data"}]
        mock_api_client.get_data.return_value = mock_raw_data

        # 執行測試 - 使用有效的action，額外參數應該被忽略
        tool = ForeignInvestmentTool()
        result = await tool.execute(action="industry", date="2024-01-15", symbol="2330")

        # 驗證結果
        assert result["success"] is True
        assert result["data"]["industry_foreign_investment"] == mock_raw_data
        assert result["data"]["total_industries"] == 1
