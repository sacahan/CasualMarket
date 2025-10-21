"""
新架構的 MCP Server - 完全模組化版本
使用統一的工具模組架構和 Python 3.12+ 語法
"""

from fastmcp import FastMCP

# API 客戶端導入
from .api.twse_client import create_client
from .tools.financial import (
    CompanyProfileTool,
    DividendScheduleTool,
    DividendTool,
    FinancialStatementsTool,
    RevenueTool,
    ValuationTool,
)
from .tools.foreign import ForeignInvestmentTool
from .tools.market import (
    ETFRankingTool,
    HistoricalIndexTool,
    HolidayTool,
    IndexInfoTool,
    MarginTradingTool,
    TradingDayTool,
    TradingStatsTool,
)

# 新架構工具導入
from .tools.trading import (
    DailyTradingTool,
    StockPriceTool,
    StockTradingTool,
    TradingStatisticsTool,
)

# 設置日誌
from .utils.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

# 創建 FastMCP 實例
mcp = FastMCP(name="casual-market-mcp")

# 創建工具實例 - 交易相關
stock_price_tool = StockPriceTool()
stock_trading_tool = StockTradingTool()
daily_trading_tool = DailyTradingTool()
trading_statistics_tool = TradingStatisticsTool()

# 創建工具實例 - 財務相關
financial_statements_tool = FinancialStatementsTool()
company_profile_tool = CompanyProfileTool()
dividend_tool = DividendTool()
revenue_tool = RevenueTool()
valuation_tool = ValuationTool()
dividend_schedule_tool = DividendScheduleTool()

# 創建工具實例 - 市場相關
margin_trading_tool = MarginTradingTool()
trading_stats_tool = TradingStatsTool()
etf_ranking_tool = ETFRankingTool()
index_info_tool = IndexInfoTool()
historical_index_tool = HistoricalIndexTool()
holiday_tool = HolidayTool()
trading_day_tool = TradingDayTool()

# 創建工具實例 - 外資相關
foreign_investment_tool = ForeignInvestmentTool()

# 創建 API 客戶端實例（用於剩餘未重構的工具）
api_client = create_client()

logger = get_logger(__name__)

# === 交易相關工具 ===


@mcp.tool
async def get_taiwan_stock_price(symbol: str):
    """
    取得台灣股票即時價格資訊。

    支援股票代碼或公司名稱查詢：
    - 股票代碼: 4-6位數字 + 可選字母 (例如: 2330, 0050, 00648R)
    - 公司名稱: 完整或部分公司名稱 (例如: "台積電", "鴻海")

    使用範例:
        get_taiwan_stock_price("2330")      # 使用股票代碼
        get_taiwan_stock_price("台積電")     # 使用公司名稱
        get_taiwan_stock_price("0050")      # 查詢ETF

    Args:
        symbol: 台灣股票代號或公司名稱

    Returns:
        MCPToolResponse[StockPriceData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (StockPriceData): 股票價格資訊，包含：
          * symbol: 股票代碼
          * company_name: 公司名稱
          * current_price: 當前價格
          * change: 漲跌金額
          * change_percent: 漲跌幅百分比
          * volume: 成交量
          * high/low/open: 最高/最低/開盤價
          * previous_close: 昨收價
          * last_update: 最後更新時間
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱
        - timestamp: 回應時間戳

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 股票代碼不存在
        - 網路連線問題
        - API 服務異常
    """
    logger.info(f"工具調用: get_taiwan_stock_price, 參數: symbol={symbol}")
    return await stock_price_tool.safe_execute(symbol=symbol)


@mcp.tool
async def buy_taiwan_stock(symbol: str, quantity: int, price: float | None = None):
    """
    模擬台灣股票買入操作。

    執行模擬的股票買入交易，計算手續費、交易稅等費用。
    注意：台股最小交易單位為1000股（1張）。

    使用範例:
        buy_taiwan_stock("2330", 1000)              # 市價買入1張台積電
        buy_taiwan_stock("2330", 2000, 510.0)       # 限價510元買入2張台積電

    Args:
        symbol: 股票代碼 (例如: "2330")
        quantity: 購買股數，必須是1000的倍數 (台股最小單位為1000股)
        price: 指定價格 (可選，不指定則為市價)

    Returns:
        MCPToolResponse[TradingResultData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (TradingResultData): 交易結果資訊，包含：
          * symbol: 股票代碼
          * action: 交易動作 ("buy")
          * quantity: 交易股數
          * price: 成交價格
          * total_amount: 交易總金額
          * fee: 手續費
          * tax: 交易稅
          * net_amount: 實際支付金額
          * timestamp: 交易時間
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        交易失敗時返回錯誤回應，可能的原因：
        - 股票代碼不存在
        - 交易股數不符合規定（非1000的倍數）
        - 指定價格超出漲跌停限制
        - 模擬交易系統異常
    """
    logger.info(
        f"工具調用: buy_taiwan_stock, 參數: symbol={symbol}, quantity={quantity}, price={price}"
    )
    return await stock_trading_tool.buy(symbol=symbol, quantity=quantity, price=price)


@mcp.tool
async def sell_taiwan_stock(symbol: str, quantity: int, price: float | None = None):
    """
    模擬台灣股票賣出操作。

    執行模擬的股票賣出交易，計算手續費、證券交易稅等費用。
    注意：台股最小交易單位為1000股（1張），賣出時需扣除0.3%證券交易稅。

    使用範例:
        sell_taiwan_stock("2330", 1000)             # 市價賣出1張台積電
        sell_taiwan_stock("2330", 1000, 530.0)      # 限價530元賣出1張台積電

    Args:
        symbol: 股票代碼 (例如: "2330")
        quantity: 賣出股數，必須是1000的倍數 (台股最小單位為1000股)
        price: 指定價格 (可選，不指定則為市價)

    Returns:
        MCPToolResponse[TradingResultData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (TradingResultData): 交易結果資訊，包含：
          * symbol: 股票代碼
          * action: 交易動作 ("sell")
          * quantity: 交易股數
          * price: 成交價格
          * total_amount: 交易總金額
          * fee: 手續費
          * tax: 證券交易稅（0.3%）
          * net_amount: 實際收入金額
          * timestamp: 交易時間
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        交易失敗時返回錯誤回應，可能的原因：
        - 股票代碼不存在
        - 交易股數不符合規定（非1000的倍數）
        - 指定價格超出漲跌停限制
        - 模擬交易系統異常
    """
    logger.info(
        f"工具調用: sell_taiwan_stock, 參數: symbol={symbol}, quantity={quantity}, price={price}"
    )
    return await stock_trading_tool.sell(symbol=symbol, quantity=quantity, price=price)


@mcp.tool
async def get_stock_daily_trading(symbol: str):
    """
    取得股票日交易統計資訊。

    提供指定股票當日的詳細交易統計，包括成交量、成交金額、
    委買委賣資訊等交易面數據。

    使用範例:
        get_stock_daily_trading("2330")       # 查詢台積電日交易資訊
        get_stock_daily_trading("0050")       # 查詢0050 ETF日交易資訊

    Args:
        symbol: 股票代碼 (例如: "2330")

    Returns:
        MCPToolResponse[dict]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (dict): 日交易統計資訊，包含：
          * trading_date: 交易日期
          * total_volume: 總成交量
          * total_value: 總成交金額
          * transaction_count: 成交筆數
          * average_price: 平均成交價
          * bid_ask_spread: 買賣價差
          * market_cap: 市值
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 股票代碼不存在
        - 非交易日或市場尚未開盤
        - 資料來源暫時無法存取
    """
    logger.info(f"工具調用: get_stock_daily_trading, 參數: symbol={symbol}")
    return await daily_trading_tool.safe_execute(symbol=symbol)


# === 財務分析工具 ===


@mcp.tool
async def get_company_income_statement(symbol: str):
    """
    取得上市公司綜合損益表。

    自動偵測公司所屬行業並使用相應的財務報表格式。
    支援不同行業的特殊會計科目和計算方式。

    支援行業別：
    - 一般業：製造業、科技業等傳統產業
    - 金融業：銀行、證券、期貨等金融機構
    - 金控業：金融控股公司
    - 保險業：壽險、產險等保險公司
    - 異業：其他特殊行業

    使用範例:
        get_company_income_statement("2330")     # 查詢台積電（一般業）
        get_company_income_statement("2884")     # 查詢玉山金（金控業）
        get_company_income_statement("2886")     # 查詢兆豐金（金控業）

    Args:
        symbol: 公司股票代碼 (例如: "2330")

    Returns:
        MCPToolResponse[dict]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (dict): 綜合損益表資訊，包含：
          * report_period: 報告期間
          * revenue: 營業收入
          * operating_cost: 營業成本
          * gross_profit: 毛利
          * operating_expense: 營業費用
          * operating_income: 營業利益
          * non_operating_income: 營業外收入
          * pre_tax_income: 稅前淨利
          * net_income: 稅後淨利
          * eps: 每股盈餘
          * industry_specific_items: 行業特有科目
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 公司代碼不存在
        - 財報資料尚未公布
        - OpenAPI 服務異常
        - 行業別偵測失敗
    """
    logger.info(f"工具調用: get_company_income_statement, 參數: symbol={symbol}")
    return await financial_statements_tool.get_income_statement(symbol)


@mcp.tool
async def get_company_balance_sheet(symbol: str):
    """
    取得上市公司資產負債表。

    自動偵測公司所屬行業並使用相應的財務報表格式。
    不同行業的資產負債表科目會有所不同，系統會自動適配。

    使用範例:
        get_company_balance_sheet("2330")      # 查詢台積電資產負債表
        get_company_balance_sheet("2884")      # 查詢玉山金資產負債表

    Args:
        symbol: 公司股票代碼 (例如: "2330")

    Returns:
        MCPToolResponse[dict]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (dict): 資產負債表資訊，包含：
          * report_period: 報告期間
          * total_assets: 總資產
          * current_assets: 流動資產
          * non_current_assets: 非流動資產
          * total_liabilities: 總負債
          * current_liabilities: 流動負債
          * non_current_liabilities: 非流動負債
          * equity: 股東權益
          * book_value_per_share: 每股淨值
          * debt_to_equity_ratio: 負債權益比
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 公司代碼不存在
        - 財報資料尚未公布
        - OpenAPI 服務異常
    """
    logger.info(f"工具調用: get_company_balance_sheet, 參數: symbol={symbol}")
    return await financial_statements_tool.get_balance_sheet(symbol)


@mcp.tool
async def get_company_profile(symbol: str):
    """
    取得上市公司基本資訊。

    提供公司的基本概況，包括公司名稱、行業別、董事長、
    成立日期、實收資本額、員工人數等基本資料。

    使用範例:
        get_company_profile("2330")         # 查詢台積電基本資訊
        get_company_profile("2317")         # 查詢鴻海基本資訊

    Args:
        symbol: 公司股票代碼 (例如: "2330")

    Returns:
        MCPToolResponse[CompanyProfileData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (CompanyProfileData): 公司基本資訊，包含：
          * symbol: 股票代碼
          * company_name: 公司全名
          * industry: 所屬行業
          * chairman: 董事長姓名
          * established: 成立日期
          * capital: 實收資本額
          * employees: 員工人數
          * website: 公司官網
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 公司代碼不存在或已下市
        - 資料來源暫時無法存取
        - 公司資訊尚未更新
    """
    logger.info(f"工具調用: get_company_profile, 參數: symbol={symbol}")
    return await company_profile_tool.safe_execute(symbol=symbol)


@mcp.tool
async def get_company_dividend(symbol: str):
    """
    取得公司股利分配資訊。

    提供公司歷年股利分配記錄，包括現金股利、股票股利、
    除息日期、發放日期等完整股利資訊。

    使用範例:
        get_company_dividend("2330")        # 查詢台積電股利資訊
        get_company_dividend("0050")        # 查詢0050 ETF配息資訊

    Args:
        symbol: 公司股票代碼 (例如: "2330")

    Returns:
        MCPToolResponse[DividendData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (DividendData): 股利分配資訊，包含：
          * symbol: 股票代碼
          * dividend_history: 歷年股利列表，每項包含：
            - year: 配息年度
            - cash_dividend: 現金股利
            - stock_dividend: 股票股利
            - total_dividend: 總股利
            - dividend_yield: 殖利率
            - ex_dividend_date: 除息日
            - payment_date: 發放日
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 公司代碼不存在
        - 尚無股利分配記錄
        - 資料來源暫時無法存取
    """
    logger.info(f"工具調用: get_company_dividend, 參數: symbol={symbol}")
    return await dividend_tool.safe_execute(symbol=symbol)


@mcp.tool
async def get_company_monthly_revenue(symbol: str):
    """
    取得公司月營收資訊。

    提供公司每月營收數據，包括當月營收、年增率、月增率等，
    是觀察公司營運狀況的重要指標。

    使用範例:
        get_company_monthly_revenue("2330")    # 查詢台積電月營收
        get_company_monthly_revenue("2454")    # 查詢聯發科月營收

    Args:
        symbol: 公司股票代碼 (例如: "2330")

    Returns:
        MCPToolResponse[MonthlyRevenueData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (MonthlyRevenueData): 月營收資訊，包含：
          * symbol: 股票代碼
          * revenue_data: 月營收列表，每項包含：
            - year_month: 年月 (YYYY-MM)
            - revenue: 當月營收
            - monthly_growth: 月增率 (%)
            - yearly_growth: 年增率 (%)
            - cumulative_revenue: 累計營收
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 公司代碼不存在
        - 月營收資料尚未公布
        - 資料來源暫時無法存取
    """
    logger.info(f"工具調用: get_company_monthly_revenue, 參數: symbol={symbol}")
    return await revenue_tool.safe_execute(symbol=symbol)


@mcp.tool
async def get_stock_valuation_ratios(symbol: str):
    """
    取得股票估值比率分析。

    提供股票的關鍵估值指標，包括本益比、股價淨值比、殖利率等，
    幫助投資人評估股票的投資價值。

    使用範例:
        get_stock_valuation_ratios("2330")    # 查詢台積電估值比率
        get_stock_valuation_ratios("2454")    # 查詢聯發科估值比率

    Args:
        symbol: 股票代碼 (例如: "2330")

    Returns:
        MCPToolResponse[ValuationRatiosData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (ValuationRatiosData): 估值比率資訊，包含：
          * symbol: 股票代碼
          * pe_ratio: 本益比 (Price-to-Earnings)
          * pb_ratio: 股價淨值比 (Price-to-Book)
          * dividend_yield: 殖利率
          * roe: 股東權益報酬率
          * eps: 每股盈餘
          * book_value: 每股淨值
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 股票代碼不存在
        - 財務數據不完整
        - 計算數據暫時無法取得
    """
    logger.info(f"工具調用: get_stock_valuation_ratios, 參數: symbol={symbol}")
    return await valuation_tool.safe_execute(symbol=symbol)


@mcp.tool
async def get_dividend_rights_schedule(symbol: str = ""):
    """
    取得除權息行事曆。

    提供上市公司的除權息相關日期資訊，包括除權息交易日、
    停止過戶日、股東會日期等重要時程。

    使用範例:
        get_dividend_rights_schedule()          # 查詢所有公司除權息行事曆
        get_dividend_rights_schedule("2330")    # 查詢台積電除權息行事曆
        get_dividend_rights_schedule("0050")    # 查詢0050除權息行事曆

    Args:
        symbol: 股票代碼 (可選，空字串或不提供則查詢全部)

    Returns:
        MCPToolResponse[DividendScheduleData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data: 除權息行事曆資訊列表，每項包含：
          * symbol: 股票代碼
          * company_name: 公司名稱
          * ex_dividend_date: 除權息交易日
          * cash_dividend: 現金股利
          * stock_dividend: 股票股利
          * record_date: 停止過戶日
          * payment_date: 發放日
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 指定的股票代碼不存在
        - 尚無除權息資料
        - 資料來源暫時無法存取
    """
    logger.info(f"工具調用: get_dividend_rights_schedule, 參數: symbol={symbol}")
    return await dividend_schedule_tool.safe_execute(symbol=symbol)


# === 交易統計工具 ===


@mcp.tool
async def get_stock_monthly_trading(symbol: str):
    """
    取得股票月交易資訊。

    提供股票每月的交易統計資料，包括月成交量、月成交金額、
    月均價、最高最低價等，適合中長期趨勢分析。

    使用範例:
        get_stock_monthly_trading("2330")     # 查詢台積電月交易資訊
        get_stock_monthly_trading("0050")     # 查詢0050月交易資訊

    Args:
        symbol: 股票代碼 (例如: "2330")

    Returns:
        MCPToolResponse[MonthlyTradingData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (MonthlyTradingData): 月交易資訊，包含：
          * symbol: 股票代碼
          * monthly_data: 月交易列表，每項包含：
            - year_month: 年月 (YYYY-MM)
            - total_volume: 月成交量
            - total_value: 月成交金額
            - average_price: 月均價
            - highest_price: 月最高價
            - lowest_price: 月最低價
            - trading_days: 交易日數
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 股票代碼不存在
        - 月交易資料尚未彙整
        - 資料來源暫時無法存取
    """
    logger.info(f"工具調用: get_stock_monthly_trading, 參數: symbol={symbol}")
    return await trading_statistics_tool.get_monthly_trading(symbol)


@mcp.tool
async def get_stock_yearly_trading(symbol: str):
    """
    取得股票年交易資訊。

    提供股票每年的交易統計資料，包括年成交量、年成交金額、
    年均價、年度漲跌幅等，適合長期投資分析與歷史回顧。

    使用範例:
        get_stock_yearly_trading("2330")      # 查詢台積電年交易資訊
        get_stock_yearly_trading("2454")      # 查詢聯發科年交易資訊

    Args:
        symbol: 股票代碼 (例如: "2330")

    Returns:
        MCPToolResponse[YearlyTradingData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (YearlyTradingData): 年交易資訊，包含：
          * symbol: 股票代碼
          * yearly_data: 年交易列表，每項包含：
            - year: 年度
            - total_volume: 年成交量
            - total_value: 年成交金額
            - average_price: 年均價
            - highest_price: 年最高價
            - lowest_price: 年最低價
            - trading_days: 交易日數
            - year_change_percent: 年度漲跌幅 (%)
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 股票代碼不存在
        - 年交易資料尚未彙整
        - 資料來源暫時無法存取
    """
    logger.info(f"工具調用: get_stock_yearly_trading, 參數: symbol={symbol}")
    return await trading_statistics_tool.get_yearly_trading(symbol)


@mcp.tool
async def get_stock_monthly_average(symbol: str):
    """
    取得股票月平均價格。

    計算股票每月的平均成交價格，可用於觀察價格趨勢、
    技術分析參考，以及定期定額投資績效評估。

    使用範例:
        get_stock_monthly_average("2330")     # 查詢台積電月均價
        get_stock_monthly_average("0050")     # 查詢0050月均價

    Args:
        symbol: 股票代碼 (例如: "2330")

    Returns:
        MCPToolResponse[MonthlyAverageData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (MonthlyAverageData): 月平均價格資訊，包含：
          * symbol: 股票代碼
          * monthly_averages: 月平均列表，每項包含：
            - year_month: 年月 (YYYY-MM)
            - average_price: 月平均成交價
            - weighted_average: 加權平均價
            - median_price: 中位數價格
            - volume_weighted_price: 成交量加權價
            - trading_days: 交易日數
            - monthly_change: 月變化百分比
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 股票代碼不存在
        - 月均價資料尚未計算
        - 資料來源暫時無法存取
    """
    logger.info(f"工具調用: get_stock_monthly_average, 參數: symbol={symbol}")
    return await trading_statistics_tool.get_monthly_average(symbol)


# === 市場資訊工具 ===


@mcp.tool
async def get_margin_trading_info():
    """
    取得融資融券資訊。

    提供市場整體及個股的融資融券統計資料，包括融資餘額、
    融券餘額、資券相抵等，可用於觀察市場籌碼面變化。

    使用範例:
        get_margin_trading_info()             # 查詢融資融券資訊

    Args:
        無參數

    Returns:
        MCPToolResponse[MarginTradingData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (MarginTradingData): 融資融券資訊，包含：
          * trading_date: 資料日期
          * financing: 融資資訊
            - balance: 融資餘額 (億元)
            - daily_buy: 今日融資買進
            - daily_sell: 今日融資賣出
            - net_change: 淨變化
            - utilization_rate: 使用率 (%)
          * securities_lending: 融券資訊
            - balance: 融券餘額 (億元)
            - daily_lend: 今日融券借出
            - daily_return: 今日融券返還
            - net_change: 淨變化
            - utilization_rate: 使用率 (%)
          * margin_trading_summary: 整體摘要
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 非交易日無資料
        - 資料來源暫時無法存取
        - 服務暫時異常
    """
    logger.info("工具調用: get_margin_trading_info")
    return await margin_trading_tool.safe_execute()


@mcp.tool
async def get_real_time_trading_stats():
    """
    取得即時交易統計資訊。

    提供市場即時交易狀態，包括當盤成交量、成交金額、
    漲跌家數分布等，資料每5分鐘更新一次。

    使用範例:
        get_real_time_trading_stats()         # 查詢即時交易統計

    Args:
        無參數

    Returns:
        MCPToolResponse[TradingStatsData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (TradingStatsData): 即時交易統計資訊，包含：
          * update_time: 資料更新時間
          * market_status: 市場狀態
          * total_volume: 總成交量 (億股)
          * total_value: 總成交金額 (億元)
          * transaction_count: 總成交筆數
          * advancing_stocks: 上漲家數
          * declining_stocks: 下跌家數
          * unchanged_stocks: 平盤家數
          * limit_up_stocks: 漲停家數
          * limit_down_stocks: 跌停家數
          * top_gainers: 漲幅前幾名列表
          * top_losers: 跌幅前幾名列表
          * active_stocks: 成交量前幾名列表
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 非交易時段
        - 資料來源暫時無法存取
        - 服務暫時異常
    """
    logger.info("工具調用: get_real_time_trading_stats")
    return await trading_stats_tool.safe_execute()


@mcp.tool
async def get_etf_regular_investment_ranking():
    """
    取得ETF定期定額排名資訊。

    提供ETF定期定額投資人數排名，反映一般投資人偏好的ETF標的，
    可作為ETF投資參考指標，資料顯示前10名熱門標的。

    使用範例:
        get_etf_regular_investment_ranking()  # 查詢ETF定期定額排名

    Args:
        無參數

    Returns:
        MCPToolResponse[ETFRankingData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data: ETF排名資訊列表（前10名），每項包含：
          * rank: 排名
          * symbol: ETF代碼
          * name: ETF名稱
          * investment_amount: 投資金額
          * investor_count: 定期定額人數
          * average_investment: 平均投資金額
          * monthly_growth: 月成長率 (%)
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱
        - metadata: 包含報告期間等額外資訊

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 排名資料尚未更新
        - 資料來源暫時無法存取
        - 服務暫時異常
    """
    logger.info("工具調用: get_etf_regular_investment_ranking")
    return await etf_ranking_tool.safe_execute()


@mcp.tool
async def get_market_index_info():
    """
    取得台灣加權指數資訊。

    提供台灣股市最主要的「發行量加權股價指數」即時資訊，
    包括指數點數、漲跌幅等關鍵數據。

    使用範例:
        get_market_index_info()  # 查詢發行量加權股價指數

    Args:
        無參數

    Returns:
        MCPToolResponse[dict]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (dict): 發行量加權股價指數資訊，包含：
          * 日期: 資料日期
          * 指數: 指數名稱
          * 收盤指數: 收盤點數
          * 漲跌: 漲跌符號
          * 漲跌點數: 漲跌點數
          * 漲跌百分比: 漲跌幅百分比
          * 特殊處理註記: 特殊狀況註記
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱
        - metadata: 包含資料來源等額外資訊

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 非交易時段
        - 資料來源暫時無法存取
        - 發行量加權股價指數資料不存在
    """
    logger.info("工具調用: get_market_index_info")
    return await index_info_tool.safe_execute()


@mcp.tool
async def get_market_historical_index():
    """
    取得市場重要指數資料。

    精選10個最重要的市場指數，提供完整的市場概覽：
    
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

    使用範例:
        get_market_historical_index()  # 查詢市場重要指數

    Args:
        無參數

    Returns:
        MCPToolResponse[dict]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (dict): 市場指數資料，包含：
          * indices: 指數列表（10個），每項包含：
            - 日期: 資料日期
            - 指數: 指數名稱
            - 收盤指數: 收盤點數
            - 漲跌: 漲跌符號
            - 漲跌點數: 漲跌點數
            - 漲跌百分比: 漲跌幅百分比
            - 特殊處理註記: 特殊狀況註記
          * count: 指數數量
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱
        - metadata: 包含資料來源等額外資訊

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 資料來源暫時無法存取
        - 無法取得市場指數資料
    """
    logger.info("工具調用: get_market_historical_index")
    return await historical_index_tool.safe_execute()


# === 外資工具 ===


@mcp.tool
async def get_foreign_investment_by_industry(count: int = 10):
    """
    取得外資持股（按產業別）。

    提供外資在各產業的持股狀況統計，包括持股比重、買賣超金額等，
    可用於觀察外資對不同產業的偏好與資金流向。

    使用範例:
        get_foreign_investment_by_industry()        # 查詢外資前10個產業持股（預設）
        get_foreign_investment_by_industry(count=5)  # 查詢外資前5個產業持股
        get_foreign_investment_by_industry(count=20) # 查詢外資前20個產業持股

    Args:
        count (int): 限制返回的產業數量，預設為10個產業

    Returns:
        MCPToolResponse[ForeignInvestmentByIndustryData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data: 外資產業持股資訊，包含：
          * industry_foreign_investment: 產業列表，每項包含：
            - 產業別: 產業名稱
            - 外資持股: 外資持股相關數據
            - 買賣超: 買賣超金額等資訊
          * total_industries: 總產業數量
          * displayed_industries: 顯示的產業數量
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 非交易日無資料
        - 資料來源暫時無法存取
        - 服務暫時異常
    """
    logger.info(f"工具調用: get_foreign_investment_by_industry, 參數: count={count}")
    return await foreign_investment_tool.get_investment_by_industry(count=count)


@mcp.tool
async def get_top_foreign_holdings():
    """
    取得外資持股前20名。

    列出外資持股比例最高的前20檔個股，包括持股比例、持股張數、
    當日買賣超等資訊，可瞭解外資重點布局標的。

    使用範例:
        get_top_foreign_holdings()            # 查詢外資持股前20名

    Args:
        無參數

    Returns:
        MCPToolResponse[TopForeignHoldingsData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data: 外資持股前20名資訊列表，每項包含：
          * rank: 排名
          * symbol: 股票代碼
          * company_name: 公司名稱
          * foreign_holding: 外資持股張數
          * percentage: 外資持股比例 (%)
          * recent_change: 近期買賣超變化
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 非交易日無資料
        - 資料來源暫時無法存取
        - 服務暫時異常
    """
    logger.info("工具調用: get_top_foreign_holdings")
    return await foreign_investment_tool.get_top_holdings()


# === 節假日工具 ===


@mcp.tool
async def get_taiwan_holiday_info(date: str):
    """
    取得台灣節假日資訊。

    查詢指定日期是否為台灣的國定假日，並取得節假日的詳細資訊。

    使用範例:
        get_taiwan_holiday_info("2025-01-01")      # 查詢元旦
        get_taiwan_holiday_info("2025-10-06")      # 查詢中秋節
        get_taiwan_holiday_info("2025-10-07")      # 查詢一般工作日

    Args:
        date: 要查詢的日期，格式為 YYYY-MM-DD (例如: "2025-01-01")

    Returns:
        MCPToolResponse[HolidayInfoData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (HolidayInfoData): 節假日資訊，包含：
          * date: 查詢日期
          * name: 節假日名稱（如果是節假日）
          * is_holiday: 是否為節假日
          * holiday_category: 節假日類別
          * description: 節假日描述
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 日期格式錯誤
        - API 服務異常
        - 網路連線問題
    """
    logger.info(f"工具調用: get_taiwan_holiday_info, 參數: date={date}")
    return await holiday_tool.execute(date=date)


@mcp.tool
async def check_taiwan_trading_day(date: str):
    """
    檢查台灣股市是否為交易日。

    綜合考慮週末和國定假日，判斷指定日期是否為台灣股市的交易日。
    台灣股市交易日條件：非週末且非國定假日。

    使用範例:
        check_taiwan_trading_day("2025-01-01")     # 元旦（非交易日）
        check_taiwan_trading_day("2025-10-06")     # 中秋節（非交易日）
        check_taiwan_trading_day("2025-10-07")     # 一般工作日（交易日）
        check_taiwan_trading_day("2025-10-11")     # 週六（非交易日）

    Args:
        date: 要檢查的日期，格式為 YYYY-MM-DD (例如: "2025-01-01")

    Returns:
        MCPToolResponse[TradingDayStatusData]: 統一格式的回應，包含：
        - success (bool): 操作是否成功
        - data (TradingDayStatusData): 交易日狀態資訊，包含：
          * date: 查詢日期
          * is_trading_day: 是否為交易日
          * is_weekend: 是否為週末
          * is_holiday: 是否為國定假日
          * holiday_name: 節假日名稱（如果是節假日）
          * reason: 不是交易日的原因（如果不是交易日）
        - error (str): 錯誤訊息（失敗時）
        - tool (str): 工具名稱

    Raises:
        查詢失敗時返回錯誤回應，可能的原因：
        - 日期格式錯誤
        - API 服務異常
        - 網路連線問題
    """
    logger.info(f"工具調用: check_taiwan_trading_day, 參數: date={date}")
    return await trading_day_tool.execute(date=date)


def main():
    """主程式入口點"""
    logger.info("啟動 Market MCP Server (FastMCP 模式)")
    mcp.run()


if __name__ == "__main__":
    main()
