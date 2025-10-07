# CasualMarket - 台灣股票交易 MCP Server

一個功能完整的台灣股票交易 Model Context Protocol (MCP) Server，提供即時股價查詢、財務分析、市場資訊等多種功能。

## 🌟 特色功能

- **即時股價查詢** - 支援股票代碼或公司名稱查詢
- **模擬交易** - 買賣股票模擬功能
- **財務分析** - 綜合損益表、資產負債表、股利資訊等
- **市場資訊** - 指數資料、外資持股、融資融券等
- **節假日查詢** - 台灣國定假日與股市交易日判斷
- **智慧快取** - 內建頻率限制與快取機制
- **多語言支援** - 完整的中文本地化

## 📋 目錄

- [安裝與設定](#安裝與設定)
- [MCP 工具詳細說明](#mcp-工具詳細說明)
  - [交易相關工具](#交易相關工具)
  - [財務分析工具](#財務分析工具)
  - [交易統計工具](#交易統計工具)
  - [市場資訊工具](#市場資訊工具)
  - [節假日工具](#節假日工具)
  - [外資投資工具](#外資投資工具)
- [配置說明](#配置說明)
- [開發指南](#開發指南)

## 🚀 安裝與設定

### 系統需求

- Python 3.12+
- uv 套件管理器

### 快速安裝

#### 1. 直接使用 uvx 執行（推薦）

```bash
# 生產環境執行
uvx --from . casual-market-mcp

# 開發環境執行
./scripts/dev-run.sh
# 或
uv run python -m src.main
```

#### 2. 從源碼安裝

```bash
# 克隆專案
git clone https://github.com/sacahan/CasualMarket.git
cd CasualMarket

# 安裝依賴
uv sync

# 運行測試
uv run pytest

# 運行服務
uv run python -m src.main
```

### Claude Desktop 配置

在 Claude Desktop 的配置文件中添加以下設定：

```json
{
  "mcpServers": {
    "casual-market": {
      "command": "uvx",
      "args": ["--from", "/path/to/CasualMarket", "casual-market-mcp"],
      "env": {
        "MARKET_MCP_SERVER_VERSION": "1.0.0",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## 🛠 MCP 工具詳細說明

### 交易相關工具

#### 📈 `get_taiwan_stock_price` - 即時股價查詢

查詢台灣股票的即時價格資訊。

**參數：**

- `symbol` (string): 股票代碼或公司名稱

**支援格式：**

- 股票代碼：2330、0050、00648R
- 公司名稱：台積電、鴻海、中華電信

**使用範例：**

```javascript
// 使用股票代碼查詢
await get_taiwan_stock_price("2330");

// 使用公司名稱查詢
await get_taiwan_stock_price("台積電");

// 查詢 ETF
await get_taiwan_stock_price("0050");
```

**回傳資料格式：**

```json
{
  "success": true,
  "data": {
    "symbol": "2330",
    "company_name": "台積電",
    "current_price": 520.0,
    "change": 5.0,
    "change_percent": 0.97,
    "volume": 15420000,
    "high": 525.0,
    "low": 515.0,
    "open": 518.0,
    "previous_close": 515.0,
    "last_update": "2024-01-15T13:30:00"
  },
  "tool": "stock_price",
  "timestamp": "2024-01-15T13:30:15.123456",
  "metadata": {}
}
```

#### 💰 `buy_taiwan_stock` - 模擬買入股票

模擬買入台灣股票。

**參數：**

- `symbol` (string): 股票代碼
- `quantity` (integer): 購買股數（最小單位 1000 股）
- `price` (number, 可選): 指定價格，不指定則為市價

**使用範例：**

```javascript
// 市價買入 1000 股台積電
await buy_taiwan_stock("2330", 1000);

// 限價買入 2000 股台積電（每股 510 元）
await buy_taiwan_stock("2330", 2000, 510.0);
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "symbol": "2330",
    "action": "buy",
    "quantity": 1000,
    "price": 520.0,
    "total_amount": 520000,
    "fee": 1456,
    "tax": 0,
    "net_amount": 521456,
    "timestamp": "2024-01-15T13:30:00"
  },
  "tool": "stock_trading",
  "timestamp": "2024-01-15T13:30:15.123456",
  "metadata": {}
}
```

#### 💸 `sell_taiwan_stock` - 模擬賣出股票

模擬賣出台灣股票。

**參數：**

- `symbol` (string): 股票代碼
- `quantity` (integer): 賣出股數（最小單位 1000 股）
- `price` (number, 可選): 指定價格，不指定則為市價

**使用範例：**

```javascript
// 市價賣出 1000 股台積電
await sell_taiwan_stock("2330", 1000);

// 限價賣出 1000 股台積電（每股 530 元）
await sell_taiwan_stock("2330", 1000, 530.0);
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "symbol": "2330",
    "action": "sell",
    "quantity": 1000,
    "price": 530.0,
    "total_amount": 530000,
    "fee": 1484,
    "tax": 1590,
    "net_amount": 526926,
    "timestamp": "2024-01-15T13:35:00"
  },
  "tool": "stock_trading",
  "timestamp": "2024-01-15T13:35:15.123456",
  "metadata": {}
}
```

#### 📊 `get_stock_daily_trading` - 日交易資訊

取得指定股票的日交易統計資訊。

**參數：**

- `symbol` (string): 股票代碼

**使用範例：**

```javascript
await get_stock_daily_trading("2330");
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "trading_date": "2024-01-15",
    "symbol": "2330",
    "total_volume": 15420000,
    "total_value": 8018400000,
    "transaction_count": 12545,
    "average_price": 520.15,
    "bid_ask_spread": 0.5,
    "market_cap": 13500000000000
  },
  "tool": "daily_trading",
  "timestamp": "2024-01-15T15:00:00.123456",
  "metadata": {}
}
```

### 財務分析工具

#### 📋 `get_company_income_statement` - 綜合損益表

取得上市公司的綜合損益表，自動偵測行業別並使用對應格式。

**支援行業：**

- 一般業、金融業、證券期貨業、金控業、保險業、異業

**參數：**

- `symbol` (string): 公司股票代碼

**使用範例：**

```javascript
// 查詢台積電損益表
await get_company_income_statement("2330");

// 查詢銀行業損益表
await get_company_income_statement("2884");
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "symbol": "2330",
    "report_period": "2024Q3",
    "revenue": 759690000000,
    "operating_cost": 456200000000,
    "gross_profit": 303490000000,
    "operating_expense": 45600000000,
    "operating_income": 257890000000,
    "non_operating_income": 12300000000,
    "pre_tax_income": 270190000000,
    "net_income": 228480000000,
    "eps": 8.81,
    "industry_specific_items": {}
  },
  "tool": "financial_statements",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {}
}
```

#### 🏦 `get_company_balance_sheet` - 資產負債表

取得上市公司的資產負債表，自動偵測行業別。

**參數：**

- `symbol` (string): 公司股票代碼

**使用範例：**

```javascript
await get_company_balance_sheet("2330");
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "symbol": "2330",
    "report_period": "2024Q3",
    "total_assets": 4890000000000,
    "current_assets": 2156000000000,
    "non_current_assets": 2734000000000,
    "total_liabilities": 1654000000000,
    "current_liabilities": 896000000000,
    "non_current_liabilities": 758000000000,
    "equity": 3236000000000,
    "book_value_per_share": 124.8,
    "debt_to_equity_ratio": 0.51
  },
  "tool": "financial_statements",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {}
}
```

#### 🏢 `get_company_profile` - 公司基本資訊

取得上市公司的基本資訊。

**參數：**

- `symbol` (string): 公司股票代碼

**使用範例：**

```javascript
await get_company_profile("2330");
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "symbol": "2330",
    "company_name": "台灣積體電路製造股份有限公司",
    "industry": "半導體業",
    "chairman": "劉德音",
    "established": "1987-02-21",
    "capital": 259303433920,
    "employees": 75000,
    "website": "https://www.tsmc.com"
  },
  "tool": "company_profile",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {}
}
```

#### 💎 `get_company_dividend` - 股利分配資訊

取得公司的股利分配歷史資訊。

**參數：**

- `symbol` (string): 公司股票代碼

**使用範例：**

```javascript
await get_company_dividend("2330");
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "symbol": "2330",
    "dividend_history": [
      {
        "year": 2024,
        "cash_dividend": 11.0,
        "stock_dividend": 0.0,
        "total_dividend": 11.0,
        "dividend_yield": 2.12,
        "ex_dividend_date": "2024-06-13",
        "payment_date": "2024-07-18"
      },
      {
        "year": 2023,
        "cash_dividend": 10.5,
        "stock_dividend": 0.0,
        "total_dividend": 10.5,
        "dividend_yield": 2.35,
        "ex_dividend_date": "2023-06-15",
        "payment_date": "2023-07-20"
      }
    ]
  },
  "tool": "company_dividend",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {}
}
```

#### 💹 `get_company_monthly_revenue` - 月營收資訊

取得公司的月營收統計資訊。

**參數：**

- `symbol` (string): 公司股票代碼

**使用範例：**

```javascript
await get_company_monthly_revenue("2330");
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "symbol": "2330",
    "revenue_data": [
      {
        "year_month": "2024-12",
        "revenue": 86550000000,
        "monthly_growth": 12.4,
        "yearly_growth": 34.8,
        "cumulative_revenue": 2590000000000
      },
      {
        "year_month": "2024-11",
        "revenue": 77020000000,
        "monthly_growth": -7.5,
        "yearly_growth": 31.5,
        "cumulative_revenue": 2503450000000
      }
    ]
  },
  "tool": "company_revenue",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {}
}
```

#### 📊 `get_stock_valuation_ratios` - 估值比率

取得股票的估值比率，包括本益比、股價淨值比、殖利率等。

**參數：**

- `symbol` (string): 股票代碼

**使用範例：**

```javascript
await get_stock_valuation_ratios("2330");
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "symbol": "2330",
    "pe_ratio": 18.5,
    "pb_ratio": 4.2,
    "dividend_yield": 2.1,
    "roe": 22.8,
    "eps": 28.15,
    "book_value": 124.5
  },
  "tool": "stock_valuation",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {}
}
```

#### 📅 `get_dividend_rights_schedule` - 除權息行事曆

取得除權息行事曆。

**參數：**

- `symbol` (string, 可選): 股票代碼，空字串則查詢全部

**使用範例：**

```javascript
// 查詢所有除權息資訊
await get_dividend_rights_schedule("");

// 查詢特定公司除權息資訊
await get_dividend_rights_schedule("2330");
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": [
    {
      "symbol": "2330",
      "company_name": "台積電",
      "ex_dividend_date": "2024-06-13",
      "cash_dividend": 3.5,
      "stock_dividend": 0.0,
      "record_date": "2024-06-13",
      "payment_date": "2024-07-18"
    },
    {
      "symbol": "2454",
      "company_name": "聯發科",
      "ex_dividend_date": "2024-06-20",
      "cash_dividend": 15.0,
      "stock_dividend": 0.0,
      "record_date": "2024-06-20",
      "payment_date": "2024-07-25"
    }
  ],
  "tool": "dividend_schedule",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {}
}
```

### 交易統計工具

#### 📊 `get_stock_monthly_trading` - 月交易統計

取得股票的月交易統計資訊。

**參數：**

- `symbol` (string): 股票代碼

**使用範例：**

```javascript
await get_stock_monthly_trading("2330");
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "symbol": "2330",
    "monthly_data": [
      {
        "year_month": "2024-12",
        "total_volume": 456780000,
        "total_value": 237800000000,
        "average_price": 520.45,
        "highest_price": 578.0,
        "lowest_price": 485.0,
        "trading_days": 21
      }
    ]
  },
  "tool": "trading_statistics",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {}
}
```

#### 📈 `get_stock_yearly_trading` - 年交易統計

取得股票的年交易統計資訊。

**參數：**

- `symbol` (string): 股票代碼

**使用範例：**

```javascript
await get_stock_yearly_trading("2330");
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "symbol": "2330",
    "yearly_data": [
      {
        "year": 2024,
        "total_volume": 5480000000,
        "total_value": 2850000000000,
        "average_price": 520.07,
        "highest_price": 615.0,
        "lowest_price": 445.0,
        "trading_days": 252,
        "year_change_percent": 34.8
      },
      {
        "year": 2023,
        "total_volume": 4920000000,
        "total_value": 2100000000000,
        "average_price": 426.83,
        "highest_price": 530.0,
        "lowest_price": 380.0,
        "trading_days": 249,
        "year_change_percent": -15.2
      }
    ]
  },
  "tool": "trading_statistics",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {}
}
```

#### 📊 `get_stock_monthly_average` - 月平均價格

取得股票的月平均價格統計。

**參數：**

- `symbol` (string): 股票代碼

**使用範例：**

```javascript
await get_stock_monthly_average("2330");
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "symbol": "2330",
    "monthly_averages": [
      {
        "year_month": "2024-12",
        "average_price": 520.45,
        "weighted_average": 521.2,
        "median_price": 518.5,
        "volume_weighted_price": 520.85,
        "trading_days": 21,
        "monthly_change": 2.8
      },
      {
        "year_month": "2024-11",
        "average_price": 506.3,
        "weighted_average": 507.15,
        "median_price": 505.0,
        "volume_weighted_price": 506.9,
        "trading_days": 22,
        "monthly_change": -1.2
      }
    ]
  },
  "tool": "trading_statistics",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {}
}
```

### 市場資訊工具

#### 💰 `get_margin_trading_info` - 融資融券資訊

取得整體市場的融資融券統計資訊。

**使用範例：**

```javascript
await get_margin_trading_info();
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "trading_date": "2024-01-15",
    "financing": {
      "balance": 187500000000,
      "daily_buy": 12800000000,
      "daily_sell": 11200000000,
      "net_change": 1600000000,
      "utilization_rate": 67.8
    },
    "securities_lending": {
      "balance": 25600000000,
      "daily_lend": 890000000,
      "daily_return": 1200000000,
      "net_change": -310000000,
      "utilization_rate": 23.4
    },
    "margin_trading_summary": {
      "total_margin_balance": 213100000000,
      "daily_net_change": 1290000000,
      "margin_ratio": 41.2
    }
  },
  "tool": "margin_trading",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {}
}
```

#### ⚡ `get_real_time_trading_stats` - 即時交易統計

取得即時交易統計資訊（每 5 分鐘更新）。

**使用範例：**

```javascript
await get_real_time_trading_stats();
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "update_time": "2024-01-15T13:30:00",
    "market_status": "trading",
    "total_volume": 8450000000,
    "total_value": 185600000000,
    "transaction_count": 892000,
    "advancing_stocks": 896,
    "declining_stocks": 1245,
    "unchanged_stocks": 89,
    "limit_up_stocks": 45,
    "limit_down_stocks": 12,
    "top_gainers": [
      {
        "symbol": "3231",
        "name": "緯創",
        "price": 89.5,
        "change_percent": 9.87
      }
    ],
    "top_losers": [
      {
        "symbol": "2454",
        "name": "聯發科",
        "price": 785.0,
        "change_percent": -4.23
      }
    ],
    "active_stocks": [
      {
        "symbol": "2330",
        "name": "台積電",
        "volume": 28500000,
        "value": 14820000000
      }
    ]
  },
  "tool": "trading_stats",
  "timestamp": "2024-01-15T13:30:15.123456",
  "metadata": {}
}
```

#### 🏆 `get_etf_regular_investment_ranking` - ETF 定期定額排名

取得 ETF 定期定額投資排名資訊（前 10 名）。

**使用範例：**

```javascript
await get_etf_regular_investment_ranking();
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": [
    {
      "rank": 1,
      "symbol": "0050",
      "name": "元大台灣50",
      "investment_amount": 1250000000,
      "investor_count": 487000,
      "average_investment": 2568,
      "monthly_growth": 12.4
    },
    {
      "rank": 2,
      "symbol": "0056",
      "name": "元大高股息",
      "investment_amount": 890000000,
      "investor_count": 623000,
      "average_investment": 1428,
      "monthly_growth": 8.7
    },
    {
      "rank": 3,
      "symbol": "00878",
      "name": "國泰永續高股息",
      "investment_amount": 670000000,
      "investor_count": 345000,
      "average_investment": 1942,
      "monthly_growth": 15.2
    }
  ],
  "tool": "etf_ranking",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {
    "report_period": "2024-12",
    "total_etf_count": 50
  }
}
```

#### 📊 `get_market_index_info` - 市場指數資訊

取得市場指數資訊。

**參數：**

- `category` (string, 預設: "major"): 指數類別
- `count` (integer, 預設: 20): 返回數量
- `format` (string, 預設: "detailed"): 格式

**使用範例：**

```javascript
// 查詢主要指數
await get_market_index_info("major", 10, "detailed");

// 查詢所有指數
await get_market_index_info("all", 50, "simple");
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": [
    {
      "index_name": "加權股價指數",
      "current_value": 18456.78,
      "change": 156.23,
      "change_percent": 0.85,
      "volume": 184500000000,
      "last_update": "2024-01-15T13:30:00"
    },
    {
      "index_name": "櫃買指數",
      "current_value": 198.45,
      "change": 2.34,
      "change_percent": 1.19,
      "volume": 12450000000,
      "last_update": "2024-01-15T13:30:00"
    },
    {
      "index_name": "台灣50指數",
      "current_value": 14567.89,
      "change": 123.45,
      "change_percent": 0.86,
      "volume": 45600000000,
      "last_update": "2024-01-15T13:30:00"
    }
  ],
  "tool": "market_index",
  "timestamp": "2024-01-15T13:30:15.123456",
  "metadata": {
    "category": "major",
    "total_indices": 10
  }
}
```

#### 📈 `get_market_historical_index` - 歷史指數資料

取得市場歷史指數資料。

**使用範例：**

```javascript
await get_market_historical_index();
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": {
    "index_name": "加權股價指數",
    "historical_data": [
      {
        "date": "2024-01-15",
        "open": 18298.45,
        "high": 18487.23,
        "low": 18256.78,
        "close": 18456.78,
        "volume": 184500000000,
        "change": 156.23,
        "change_percent": 0.85
      },
      {
        "date": "2024-01-12",
        "open": 18345.67,
        "high": 18398.12,
        "low": 18285.34,
        "close": 18300.55,
        "volume": 167800000000,
        "change": -45.12,
        "change_percent": -0.25
      },
      {
        "date": "2024-01-11",
        "open": 18289.34,
        "high": 18367.89,
        "low": 18234.56,
        "close": 18345.67,
        "volume": 152300000000,
        "change": 56.33,
        "change_percent": 0.31
      }
    ],
    "period": "30_days",
    "statistics": {
      "average_volume": 168200000000,
      "highest_close": 18456.78,
      "lowest_close": 18234.56,
      "period_return": 1.22
    }
  },
  "tool": "historical_index",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {
    "data_source": "TWSE",
    "total_records": 30
  }
}
```

### 節假日工具

#### 📅 `get_taiwan_holiday_info` - 台灣節假日查詢

查詢指定日期是否為台灣國定假日，並取得節假日詳細資訊。

**參數：**

- `date` (string): 要查詢的日期，格式為 YYYY-MM-DD

**使用範例：**

```javascript
await get_taiwan_holiday_info("2025-01-01"); // 查詢元旦
await get_taiwan_holiday_info("2025-10-06"); // 查詢中秋節
await get_taiwan_holiday_info("2025-10-07"); // 查詢一般工作日
```

**回傳資料範例（節假日）：**

```json
{
  "success": true,
  "data": {
    "date": "20251006",
    "name": "中秋節",
    "is_holiday": true,
    "holiday_category": "放假之紀念日及節日",
    "description": "全國各機關學校放假一日。"
  },
  "tool": "holiday_tool",
  "timestamp": "2025-10-07T10:30:00.123456"
}
```

**回傳資料範例（非節假日）：**

```json
{
  "success": true,
  "data": {
    "date": "2025-10-07",
    "name": "",
    "is_holiday": false,
    "holiday_category": "",
    "description": "非節假日"
  },
  "tool": "holiday_tool",
  "timestamp": "2025-10-07T10:30:00.123456"
}
```

#### 📊 `check_taiwan_trading_day` - 股市交易日判斷

檢查指定日期是否為台灣股市交易日，綜合考慮週末和國定假日。

**參數：**

- `date` (string): 要檢查的日期，格式為 YYYY-MM-DD

**交易日條件：**

- 非週末（週一至週五）
- 非國定假日

**使用範例：**

```javascript
await check_taiwan_trading_day("2025-01-01"); // 元旦（非交易日）
await check_taiwan_trading_day("2025-10-06"); // 中秋節（非交易日）
await check_taiwan_trading_day("2025-10-07"); // 一般工作日（交易日）
await check_taiwan_trading_day("2025-10-11"); // 週六（非交易日）
```

**回傳資料範例（交易日）：**

```json
{
  "success": true,
  "data": {
    "date": "2025-10-07",
    "is_trading_day": true,
    "is_weekend": false,
    "is_holiday": false,
    "holiday_name": null,
    "reason": "是交易日"
  },
  "tool": "trading_day_tool",
  "timestamp": "2025-10-07T10:30:00.123456"
}
```

**回傳資料範例（國定假日）：**

```json
{
  "success": true,
  "data": {
    "date": "2025-10-06",
    "is_trading_day": false,
    "is_weekend": false,
    "is_holiday": true,
    "holiday_name": "中秋節",
    "reason": "國定假日（中秋節）"
  },
  "tool": "trading_day_tool",
  "timestamp": "2025-10-07T10:30:00.123456"
}
```

**回傳資料範例（週末）：**

```json
{
  "success": true,
  "data": {
    "date": "2025-10-11",
    "is_trading_day": false,
    "is_weekend": true,
    "is_holiday": false,
    "holiday_name": null,
    "reason": "週末"
  },
  "tool": "trading_day_tool",
  "timestamp": "2025-10-07T10:30:00.123456"
}
```

### 外資投資工具

#### 🌍 `get_foreign_investment_by_industry` - 外資持股（按產業別）

取得外資持股按產業別分布的統計資訊。

**使用範例：**

```javascript
await get_foreign_investment_by_industry();
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": [
    {
      "industry": "半導體業",
      "total_holding": 125000000000,
      "percentage": 18.5,
      "top_stocks": ["2330", "2454", "3034"]
    },
    {
      "industry": "金融保險業",
      "total_holding": 89000000000,
      "percentage": 13.2,
      "top_stocks": ["2884", "2881", "2882"]
    }
  ],
  "tool": "foreign_investment",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {}
}
```

#### 🥇 `get_top_foreign_holdings` - 外資持股前 20 名

取得外資持股前 20 名個股的詳細資訊。

**使用範例：**

```javascript
await get_top_foreign_holdings();
```

**回傳資料範例：**

```json
{
  "success": true,
  "data": [
    {
      "rank": 1,
      "symbol": "2330",
      "company_name": "台積電",
      "foreign_holding": 4250000000,
      "percentage": 78.2,
      "recent_change": 15000000
    }
  ],
  "tool": "foreign_investment",
  "timestamp": "2024-01-15T16:00:00.123456",
  "metadata": {}
}
```

## ⚙️ 配置說明

### 環境變數配置

複製配置範本並根據需求修改：

```bash
cp .env.simple .env
```

### 主要配置項目

#### API 客戶端配置

```env
# API 請求超時時間（秒）
MARKET_MCP_API_TIMEOUT=10

# API 請求重試次數
MARKET_MCP_API_RETRIES=5

# 台灣證交所 API URL
MARKET_MCP_TWSE_API_URL="https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
```

#### 限速配置

```env
# 每個股票的請求間隔（秒）
MARKET_MCP_RATE_LIMIT_INTERVAL=30.0

# 全域每分鐘請求限制
MARKET_MCP_RATE_LIMIT_GLOBAL_PER_MINUTE=20

# 每秒請求限制
MARKET_MCP_RATE_LIMIT_PER_SECOND=2

# 是否啟用限速功能
MARKET_MCP_RATE_LIMITING_ENABLED=true
```

#### 快取配置

```env
# 快取存活時間（秒）
MARKET_MCP_CACHE_TTL=30

# 快取最大條目數
MARKET_MCP_CACHE_MAX_SIZE=1000

# 快取最大記憶體使用（MB）
MARKET_MCP_CACHE_MAX_MEMORY_MB=200.0

# 是否啟用快取功能
MARKET_MCP_CACHING_ENABLED=true
```

#### 日誌配置

```env
# 日誌級別：DEBUG, INFO, WARNING, ERROR
MARKET_MCP_LOG_LEVEL=INFO

# 日誌格式
MARKET_MCP_LOG_FORMAT="<green>{time}</green> | <level>{level}</level> | <cyan>{name}</cyan> | {message}"
```

## 🧪 開發指南

### 運行測試

```bash
# 運行所有測試
uv run pytest

# 運行特定測試類別
uv run pytest tests/api/           # API 整合測試
uv run pytest tests/server/        # 伺服器功能測試
uv run pytest tests/tools/         # 工具功能測試

# 生成覆蓋率報告
uv run pytest --cov=src --cov-report=html
```

### 代碼品質檢查

```bash
# 使用 ruff 進行程式碼檢查
uv run ruff check src/ tests/

# 使用 mypy 進行型別檢查
uv run mypy src/

# 自動修復可修復的問題
uv run ruff check --fix src/ tests/
```

### 開發模式運行

```bash
# 開發模式（避免 uvx 快取問題）
./scripts/dev-run.sh

# 或手動使用 uv run
uv run python -m src.main

# 快速功能測試
./scripts/dev-test.sh
```

### 測試狀態

**整體健康度**：✅ 優秀（98% 通過率）

- **總測試案例**：110 個
- **通過測試**：108 個（98%）
- **跳過測試**：2 個（2%）
- **失敗測試**：0 個（0%）
- **程式碼覆蓋率**：62%

## 📚 技術架構

### 核心組件

1. **FastMCP Server** - 使用 `@mcp.tool` 裝飾器簡化工具註冊
2. **API 客戶端層** - 整合台灣證交所 API 與 OpenAPI
3. **快取系統** - 整合限速與快取服務
4. **證券資料庫** - SQLite 資料庫處理 ISIN 代碼與公司名稱解析
5. **財務工具** - 使用 TWSE OpenAPI 進行進階財務分析

### 關鍵架構模式

- **FastMCP 整合**：使用 `@mcp.tool` 裝飾器代替傳統 MCP 伺服器設定
- **裝飾器增強**：函數裝飾器為 API 方法添加快取與限速功能
- **層次化驗證**：多層級輸入驗證（符號格式、市場類型、API 回應）
- **模組化工具設計**：可插拔的財務分析工具組件

## 📝 許可證

MIT License

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📞 支援

- GitHub Issues: [https://github.com/sacahan/CasualMarket/issues](https://github.com/sacahan/CasualMarket/issues)
- 文檔: [專案 Wiki](https://github.com/sacahan/CasualMarket/wiki)

---

**注意事項：**

- 本工具僅供學習和研究用途
- 股票資料可能有延遲，請勿用於實際交易決策
- 模擬交易功能不涉及真實資金
