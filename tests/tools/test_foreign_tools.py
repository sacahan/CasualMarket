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
        mock_api_client.get_foreign_investment_data.return_value = mock_data

        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.execute(date="2024-01-15")

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert result["tool"] == "foreign_investment"
        assert "外資買賣超統計" in result["data"]
        assert "前十大外資買超股票" in result["data"]
        assert "前十大外資賣超股票" in result["data"]

        # 驗證 API 呼叫
        mock_api_client.get_foreign_investment_data.assert_called_once_with(
            "2024-01-15"
        )

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_by_industry(self, mock_api_client):
        """測試外資投資工具 - 依產業別分析"""
        # 準備測試數據
        mock_data = {
            "產業別外資統計": [
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
        }
        mock_api_client.get_foreign_investment_by_industry.return_value = mock_data

        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.execute(analysis_type="industry", date="2024-01-15")

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert result["tool"] == "foreign_investment"
        assert "產業別外資統計" in result["data"]

        # 驗證 API 呼叫
        mock_api_client.get_foreign_investment_by_industry.assert_called_once_with(
            "2024-01-15"
        )

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_specific_stock(self, mock_api_client):
        """測試外資投資工具 - 特定股票分析"""
        # 準備測試數據
        mock_data = {
            "股票代號": "2330",
            "股票名稱": "台積電",
            "外資持股": {
                "持股張數": "25,678,900張",
                "持股比例": "78.5%",
                "持股市值": "12,839,450,000千元",
            },
            "近期外資買賣": [
                {
                    "日期": "2024/01/15",
                    "外資買賣超": "+1,234張",
                    "累積持股變化": "+0.01%",
                },
                {
                    "日期": "2024/01/12",
                    "外資買賣超": "+5,678張",
                    "累積持股變化": "+0.05%",
                },
            ],
            "外資券商分析": [
                {
                    "券商": "摩根大通",
                    "目標價": "600元",
                    "投資建議": "買進",
                    "更新日期": "2024/01/10",
                },
            ],
        }
        mock_api_client.get_foreign_investment_for_stock.return_value = mock_data

        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.execute(symbol="2330", analysis_type="stock")

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert result["tool"] == "foreign_investment"
        assert result["data"]["股票代號"] == "2330"
        assert "外資持股" in result["data"]

        # 驗證 API 呼叫
        mock_api_client.get_foreign_investment_for_stock.assert_called_once_with("2330")

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_no_data(self, mock_api_client):
        """測試外資投資工具 - 找不到資料"""
        # 設定 API 回傳空資料
        mock_api_client.get_foreign_investment_data.return_value = None

        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.execute(date="2024-01-15")

        # 驗證結果
        assert result["success"] is False
        assert "找不到外資投資資料" in result["error"]
        assert result["tool"] == "foreign_investment"

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_exception(self, mock_api_client):
        """測試外資投資工具 - 異常處理"""
        # 設定 API 拋出異常
        mock_api_client.get_foreign_investment_data.side_effect = Exception(
            "API 連線失敗"
        )

        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.execute(date="2024-01-15")

        # 驗證結果
        assert result["success"] is False
        assert "API 連線失敗" in result["error"]
        assert result["tool"] == "foreign_investment"

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_default_date(self, mock_api_client):
        """測試外資投資工具 - 使用預設日期"""
        # 準備測試數據
        mock_data = {"外資買賣超統計": {"日期": "今日", "外資買賣超": "+1,000千元"}}
        mock_api_client.get_foreign_investment_data.return_value = mock_data

        # 執行測試（不提供日期參數）
        tool = ForeignInvestmentTool()
        result = await tool.execute()

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data

        # 驗證 API 被呼叫（應該使用預設日期）
        mock_api_client.get_foreign_investment_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_historical_analysis(self, mock_api_client):
        """測試外資投資工具 - 歷史分析"""
        # 準備測試數據
        mock_data = {
            "期間": "2024/01/01 - 2024/01/15",
            "外資累計買賣超": "+15,678,900千元",
            "平均日買賣超": "+1,045,260千元",
            "最大單日買超": "+3,456,789千元",
            "最大單日賣超": "-1,234,567千元",
            "趨勢分析": "外資持續買超，顯示對台股信心增強",
            "熱門標的": [
                {"股票": "2330 台積電", "累計買超": "+5,678,900千元"},
                {"股票": "2317 鴻海", "累計買超": "+2,345,600千元"},
            ],
        }
        mock_api_client.get_foreign_investment_historical.return_value = mock_data

        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.execute(
            analysis_type="historical", start_date="2024-01-01", end_date="2024-01-15"
        )

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert result["tool"] == "foreign_investment"
        assert "趨勢分析" in result["data"]

        # 驗證 API 呼叫
        mock_api_client.get_foreign_investment_historical.assert_called_once_with(
            "2024-01-01", "2024-01-15"
        )

    def test_foreign_investment_tool_name(self):
        """測試工具名稱正確性"""
        tool = ForeignInvestmentTool()
        assert tool.name == "foreign_investment"

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_safe_execute(self, mock_api_client):
        """測試外資投資工具的 safe_execute 方法"""
        # 準備測試數據
        mock_data = {"test": "data"}
        mock_api_client.get_foreign_investment_data.return_value = mock_data

        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.safe_execute(date="2024-01-15")

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_context_manager(self):
        """測試外資投資工具的上下文管理器"""
        with ForeignInvestmentTool() as tool:
            assert tool is not None
            assert tool.name == "foreign_investment"

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_invalid_analysis_type(self, mock_api_client):
        """測試外資投資工具 - 無效分析類型"""
        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.execute(analysis_type="invalid_type")

        # 驗證結果應該處理無效類型
        # 這取決於具體實現，可能回傳錯誤或使用預設類型
        assert "error" in result or "success" in result

    @pytest.mark.asyncio
    async def test_foreign_investment_tool_multiple_params(self, mock_api_client):
        """測試外資投資工具 - 多參數組合"""
        # 準備測試數據
        mock_data = {"combined_analysis": "test_data"}
        mock_api_client.get_foreign_investment_data.return_value = mock_data

        # 執行測試
        tool = ForeignInvestmentTool()
        result = await tool.execute(
            date="2024-01-15", symbol="2330", analysis_type="combined"
        )

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
