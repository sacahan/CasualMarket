"""
測試財務分析工具
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.tools.financial import (
    CompanyProfileTool,
    DividendTool,
    DividendScheduleTool,
    FinancialStatementsTool,
    RevenueTool,
    ValuationTool,
)


class TestFinancialTools:
    """測試財務分析工具類別"""

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
    async def test_company_profile_tool_success(self, mock_api_client):
        """測試公司基本資料工具 - 成功案例"""
        # 準備測試數據
        mock_data = {
            "公司代號": "2330",
            "公司名稱": "台灣積體電路製造股份有限公司",
            "公司簡稱": "台積電",
            "產業別": "半導體業",
            "董事長": "劉德音",
            "總經理": "魏哲家",
            "發言人": "何麗梅",
            "成立日期": "1987/02/21",
            "上市日期": "1994/09/05",
        }
        mock_api_client.get_company_data.return_value = mock_data

        # 執行測試
        tool = CompanyProfileTool()
        result = await tool.execute(symbol="2330")

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert result["tool"] == "company_profile"
        assert result["company_code"] == "2330"
        assert result["source"] == "TWSE OpenAPI"

        # 驗證 API 呼叫
        mock_api_client.get_company_data.assert_called_once_with(
            "/opendata/t187ap03_L", "2330"
        )

    @pytest.mark.asyncio
    async def test_company_profile_tool_no_data(self, mock_api_client):
        """測試公司基本資料工具 - 找不到資料"""
        # 設定 API 回傳空資料
        mock_api_client.get_company_data.return_value = None

        # 執行測試
        tool = CompanyProfileTool()
        result = await tool.execute(symbol="9999")

        # 驗證結果
        assert result["success"] is False
        assert "找不到 9999 的公司基本資料" in result["error"]
        assert result["tool"] == "company_profile"
        assert result["company_code"] == "9999"

    @pytest.mark.asyncio
    async def test_company_profile_tool_exception(self, mock_api_client):
        """測試公司基本資料工具 - 異常處理"""
        # 設定 API 拋出異常
        mock_api_client.get_company_data.side_effect = Exception("API 連線失敗")

        # 執行測試
        tool = CompanyProfileTool()
        result = await tool.execute(symbol="2330")

        # 驗證結果
        assert result["success"] is False
        assert "API 連線失敗" in result["error"]
        assert result["tool"] == "company_profile"

    @pytest.mark.asyncio
    async def test_dividend_tool_success(self, mock_api_client):
        """測試股利分析工具 - 成功案例"""
        # 準備測試數據
        mock_data = {
            "股票代號": "2330",
            "公司名稱": "台積電",
            "年度": "2023",
            "現金股利": 11.0,
            "股票股利": 0.0,
            "合計股利": 11.0,
            "現金殖利率": "2.8%",
            "除息日": "2023/06/15",
            "除權日": None,
        }
        mock_api_client.get_company_data.return_value = mock_data

        # 執行測試
        tool = DividendTool()
        result = await tool.execute(symbol="2330")

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert result["tool"] == "dividend"

        # 驗證 API 呼叫
        mock_api_client.get_company_data.assert_called_with(
            "/opendata/t187ap45_L", "2330"
        )

    @pytest.mark.asyncio
    async def test_financial_statements_tool_income_success(self, mock_api_client):
        """測試財務報表工具 - 損益表成功案例"""
        # 準備測試數據
        mock_data = {
            "營業收入": 75887000,
            "營業成本": 37435000,
            "營業毛利": 38452000,
            "營業費用": 12568000,
            "營業利益": 25884000,
            "稅前淨利": 26969000,
            "稅後淨利": 23503000,
            "基本每股盈餘": 9.06,
        }
        mock_api_client.get_industry_api_suffix.return_value = ""
        mock_api_client.get_company_data.return_value = mock_data

        # 執行測試
        tool = FinancialStatementsTool()
        result = await tool.get_income_statement(symbol="2330")

        # 驗證結果
        assert result["success"] is True
        assert result["tool"] == "financial_statements"
        assert result["statement_type"] == "綜合損益表"
        assert "key_metrics" in result["data"]

        # 驗證 API 呼叫
        mock_api_client.get_industry_api_suffix.assert_called_with("2330")
        mock_api_client.get_company_data.assert_called_with(
            "/opendata/t187ap06_L", "2330"
        )

    @pytest.mark.asyncio
    async def test_financial_statements_tool_balance_success(self, mock_api_client):
        """測試財務報表工具 - 資產負債表成功案例"""
        # 準備測試數據
        mock_data = {
            "資產總額": 15000000,
            "負債總額": 5000000,
            "股東權益總額": 10000000,
            "每股淨值": 156.25,
        }
        mock_api_client.get_industry_api_suffix.return_value = ""
        mock_api_client.get_company_data.return_value = mock_data

        # 執行測試
        tool = FinancialStatementsTool()
        result = await tool.get_balance_sheet(symbol="2330")

        # 驗證結果
        assert result["success"] is True
        assert result["tool"] == "financial_statements"
        assert result["statement_type"] == "資產負債表"
        assert "key_metrics" in result["data"]

        # 驗證 API 呼叫
        mock_api_client.get_industry_api_suffix.assert_called_with("2330")
        mock_api_client.get_company_data.assert_called_with(
            "/opendata/t187ap07_L", "2330"
        )

    @pytest.mark.asyncio
    async def test_revenue_tool_success(self, mock_api_client):
        """測試營收工具 - 成功案例"""
        # 準備測試數據
        mock_data = {
            "公司代號": "2330",
            "年月": "112/12",
            "營業收入": 7537478,
            "去年同月增減(%)": 14.37,
            "前期比較增減(%)": 2.89,
            "累計營業收入": 75887000,
            "去年累計增減(%)": 10.93,
        }
        mock_api_client.get_company_data.return_value = mock_data

        # 執行測試
        tool = RevenueTool()
        result = await tool.execute(symbol="2330")

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert result["tool"] == "revenue"

    @pytest.mark.asyncio
    async def test_valuation_tool_success(self, mock_api_client):
        """測試估值工具 - 成功案例"""
        # 準備測試數據
        mock_data = {
            "股票代號": "2330",
            "公司名稱": "台積電",
            "現價": 500.0,
            "本益比": 18.5,
            "股價淨值比": 3.2,
            "股息殖利率": 2.8,
            "每股淨值": 156.25,
            "每股盈餘": 27.03,
            "市值": 13000000000000,
        }
        mock_api_client.get_valuation_data.return_value = mock_data

        # 執行測試
        tool = ValuationTool()
        result = await tool.execute(symbol="2330")

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert result["tool"] == "valuation"

    @pytest.mark.asyncio
    async def test_dividend_schedule_tool_success(self, mock_api_client):
        """測試股利發放日程工具 - 成功案例"""
        # 準備測試數據
        mock_data = {
            "股票代號": "2330",
            "公司名稱": "台積電",
            "股東會日期": "2024/06/04",
            "除息日": "2024/06/13",
            "除權日": None,
            "現金股利": 4.0,
            "股票股利": 0.0,
            "發放日": "2024/07/11",
        }
        mock_api_client.get_dividend_schedule.return_value = mock_data

        # 執行測試
        tool = DividendScheduleTool()
        result = await tool.execute(symbol="2330")

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data
        assert result["tool"] == "dividend_schedule"

    @pytest.mark.asyncio
    async def test_safe_execute_wrapper(self, mock_api_client):
        """測試 safe_execute 包裝器"""
        # 準備測試數據
        mock_data = {"test": "data"}
        mock_api_client.get_company_data.return_value = mock_data

        # 執行測試
        tool = CompanyProfileTool()
        result = await tool.safe_execute(symbol="2330")

        # 驗證結果
        assert result["success"] is True
        assert result["data"] == mock_data

    @pytest.mark.asyncio
    async def test_safe_execute_with_exception(self, mock_api_client):
        """測試 safe_execute 異常處理"""
        # 設定 API 拋出異常
        mock_api_client.get_company_data.side_effect = Exception("嚴重錯誤")

        # 執行測試
        tool = CompanyProfileTool()
        result = await tool.safe_execute(symbol="2330")

        # 驗證結果
        assert result["success"] is False
        assert "嚴重錯誤" in result["error"]

    def test_context_manager(self, mock_api_client):
        """測試上下文管理器"""
        with CompanyProfileTool() as tool:
            assert tool is not None
            assert tool.name == "company_profile"

    def test_tool_initialization(self):
        """測試工具初始化"""
        tool = CompanyProfileTool()
        assert tool.name == "company_profile"
        assert hasattr(tool, "logger")
        assert hasattr(tool, "api_client")
        assert hasattr(tool, "stock_client")


class TestToolBase:
    """測試工具基類功能"""

    @pytest.fixture
    def mock_tool(self):
        """建立模擬工具"""
        from src.tools.base.tool_base import ToolBase

        class MockTool(ToolBase):
            async def execute(self, **kwargs):
                if kwargs.get("should_fail"):
                    raise ValueError("測試異常")
                return {"test": "success"}

        return MockTool("test_tool")

    @pytest.mark.asyncio
    async def test_success_response(self, mock_tool):
        """測試成功回應格式"""
        response = mock_tool._success_response(
            data={"test": "data"}, extra_field="extra_value"
        )

        assert response["success"] is True
        assert response["data"] == {"test": "data"}
        assert response["tool"] == "test_tool"
        assert response["extra_field"] == "extra_value"

    @pytest.mark.asyncio
    async def test_error_response(self, mock_tool):
        """測試錯誤回應格式"""
        response = mock_tool._error_response(error="測試錯誤", error_code="E001")

        assert response["success"] is False
        assert response["error"] == "測試錯誤"
        assert response["tool"] == "test_tool"
        assert response["error_code"] == "E001"

    @pytest.mark.asyncio
    async def test_safe_execute_success(self, mock_tool):
        """測試 safe_execute 成功案例"""
        result = await mock_tool.safe_execute()
        assert result == {"test": "success"}

    @pytest.mark.asyncio
    async def test_safe_execute_exception_handling(self, mock_tool):
        """測試 safe_execute 異常處理"""
        result = await mock_tool.safe_execute(should_fail=True)

        assert result["success"] is False
        assert "測試異常" in result["error"]
        assert result["tool"] == "test_tool"
