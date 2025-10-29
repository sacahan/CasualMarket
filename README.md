# CasualMarket - 台灣股票交易 MCP Server

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.7.0+-green.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-98%25%20passing-success.svg)](https://github.com/sacahan/CasualMarket)

一個功能完整的**台灣股票交易 MCP Server**，提供超過 **23 個專業工具**，涵蓋即時股價查詢、財務分析、市場資訊、模擬交易等多種功能。基於 **FastMCP 2.7.0+** 框架開發，具備智慧快取和頻率限制機制。

## 目錄

- [快速開始](#快速開始)
- [MCP 安裝與配置](#mcp-安裝與配置)
- [核心功能](#核心功能)
- [工具列表](#工具列表)
- [使用範例](#使用範例)
- [支援](#支援)
- [許可證](#許可證)

## 快速開始

CasualMarket MCP Server 已發佈在 PyPI，您可以直接透過 `uvx` 安裝並在支援 MCP 的工具中使用，無需本地配置。

**系統需求：**

- Python 3.12+
- [uv 套件管理器](https://github.com/astral-sh/uv)（用於執行 MCP Server）

**最簡單的方式是根據您使用的工具，按照下方「MCP 安裝與配置」部分進行配置即可。**

### MCP 安裝與配置

#### Claude Desktop 配置

編輯 Claude Desktop 配置檔：

**配置檔位置：**

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**配置內容（推薦方式 - 使用 GitHub Repo）：**

```json
{
  "mcpServers": {
    "casual-market": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/sacahan/CasualMarket", "casual-market-mcp"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**配置內容（本地開發方式）：**

```json
{
  "mcpServers": {
    "casual-market": {
      "command": "uvx",
      "args": ["--from", "/path/to/CasualMarket", "casual-market-mcp"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### Cursor 配置

編輯 Cursor 配置檔：

**配置檔位置：**

- macOS: `~/Library/Application Support/Cursor/User/settings.json`
- Windows: `%APPDATA%\Cursor\User\settings.json`
- Linux: `~/.config/Cursor/User/settings.json`

**配置內容：**

在 `settings.json` 中加入以下配置：

```json
{
  "mcpServerSettings": {
    "casual-market": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/sacahan/CasualMarket", "casual-market-mcp"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

或者直接編輯 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "casual-market": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/sacahan/CasualMarket", "casual-market-mcp"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### VS Code 配置（通過 Claude 擴展）

如果使用 VS Code 中的 Claude 擴展，配置方法類似：

**配置檔位置：**

- macOS: `~/Library/Application Support/Code/User/settings.json`
- Windows: `%APPDATA%\Code\User\settings.json`
- Linux: `~/.config/Code/User/settings.json`

**配置內容：**

```json
{
  "claude.mcpServers": {
    "casual-market": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/sacahan/CasualMarket", "casual-market-mcp"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### CodePilot / 其他 MCP 客戶端

對於支援 MCP 協定的其他工具，通用配置範本：

```json
{
  "mcpServers": {
    "casual-market": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/sacahan/CasualMarket", "casual-market-mcp"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### 配置參數說明

MCP Server 支援以下環境變數：

**API 和快取相關：**

| 參數 | 說明 | 預設值 |
|------|------|-------|
| `LOG_LEVEL` | 日誌級別 | `INFO` |
| `MARKET_MCP_API_TIMEOUT` | API 請求超時時間（秒） | `10` |
| `MARKET_MCP_API_RETRIES` | API 請求重試次數 | `5` |
| `MARKET_MCP_CACHE_TTL` | 快取存活時間（秒） | `1800` |
| `MARKET_MCP_CACHE_MAX_SIZE` | 快取最大條目數 | `1000` |
| `MARKET_MCP_CACHE_MAX_MEMORY_MB` | 快取最大記憶體使用（MB） | `200.0` |
| `MARKET_MCP_CACHING_ENABLED` | 是否啟用快取 | `true` |

**限速相關：**

| 參數 | 說明 | 預設值 |
|------|------|-------|
| `MARKET_MCP_RATE_LIMIT_INTERVAL` | 每個股票的請求間隔（秒） | `1.0` |
| `MARKET_MCP_RATE_LIMIT_GLOBAL_PER_MINUTE` | 全域每分鐘請求限制 | `200` |
| `MARKET_MCP_RATE_LIMIT_PER_SECOND` | 每秒請求限制 | `50` |
| `MARKET_MCP_RATE_LIMITING_ENABLED` | 是否啟用限速功能 | `false` |

**監控相關：**

| 參數 | 說明 | 預設值 |
|------|------|-------|
| `MARKET_MCP_MONITORING_STATS_RETENTION_HOURS` | 統計資料保留時間（小時） | `24` |
| `MARKET_MCP_MONITORING_CACHE_HIT_RATE_TARGET` | 快取命中率目標（百分比） | `80.0` |

**推薦配置範例（快速開始）：**

```json
{
  "mcpServers": {
    "casual-market": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/sacahan/CasualMarket", "casual-market-mcp"],
      "env": {
        "LOG_LEVEL": "INFO",
        "MARKET_MCP_API_TIMEOUT": "10",
        "MARKET_MCP_CACHE_TTL": "1800",
        "MARKET_MCP_CACHE_MAX_SIZE": "1000"
      }
    }
  }
}
```

**高效能配置範例（啟用限速和監控）：**

```json
{
  "mcpServers": {
    "casual-market": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/sacahan/CasualMarket", "casual-market-mcp"],
      "env": {
        "LOG_LEVEL": "INFO",
        "MARKET_MCP_API_TIMEOUT": "15",
        "MARKET_MCP_CACHE_TTL": "3600",
        "MARKET_MCP_CACHE_MAX_SIZE": "2000",
        "MARKET_MCP_CACHE_MAX_MEMORY_MB": "500",
        "MARKET_MCP_RATE_LIMITING_ENABLED": "true",
        "MARKET_MCP_RATE_LIMIT_INTERVAL": "2.0",
        "MARKET_MCP_RATE_LIMIT_GLOBAL_PER_MINUTE": "100"
      }
    }
  }
}
```

**調試配置範例（詳細日誌）：**

```json
{
  "mcpServers": {
    "casual-market": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/sacahan/CasualMarket", "casual-market-mcp"],
      "env": {
        "LOG_LEVEL": "DEBUG",
        "MARKET_MCP_API_TIMEOUT": "20",
        "MARKET_MCP_CACHE_TTL": "600",
        "MARKET_MCP_CACHING_ENABLED": "true"
      }
    }
  }
}
```

## 核心功能

### 交易工具 (4個)

- **即時股價查詢** - 股票代碼或公司名稱查詢
- **模擬買入/賣出** - 完整的交易模擬，包含手續費和交易稅
- **日交易統計** - 每日成交量、成交值、平均價格

### 財務分析工具 (6個)

- **損益表/資產負債表** - 自動行業別偵測
- **公司基本資料** - 董事長、資本額、員工數等
- **股利分配歷史** - 殖利率、現金股利、股票股利
- **月營收追蹤** - 營收數據與成長率
- **估值比率** - PE、PB、ROE、殖利率等關鍵指標
- **除權息行事曆** - 重要除權息日期提醒

### 交易統計工具 (3個)

- **月交易統計** - 月度成交量、成交值、平均價格
- **年交易統計** - 年度數據與年度漲跌幅
- **月平均價格** - 包含加權平均、中位數等多維度分析

### 市場資訊工具 (5個)

- **融資融券** - 市場籌碼面分析
- **即時交易統計** - 5分鐘更新的市場數據
- **ETF排名** - 定期定額投資排名
- **市場指數** - 發行量加權、未含金融等多種指數
- **歷史指數** - 精選10個重要市場指標

### 節假日工具 (2個)

- **國定假日查詢** - 台灣節假日詳細資訊
- **交易日判斷** - 智慧判斷股市開盤狀態

### 外資分析工具 (3個)

- **外資持股（按產業別）** - 外資持股分布統計
- **外資持股排名** - 外資持股前20名個股
- **資金流向分析** - 外資買賣超數據

## 工具列表

| 工具名稱 | 描述 | 分類 |
|---------|------|------|
| `get_taiwan_stock_price` | 即時股價查詢 | 交易 |
| `buy_taiwan_stock` | 模擬買入股票 | 交易 |
| `sell_taiwan_stock` | 模擬賣出股票 | 交易 |
| `get_stock_daily_trading` | 日交易統計 | 交易 |
| `get_company_income_statement` | 綜合損益表 | 財務 |
| `get_company_balance_sheet` | 資產負債表 | 財務 |
| `get_company_profile` | 公司基本資料 | 財務 |
| `get_company_dividend` | 股利分配資訊 | 財務 |
| `get_company_monthly_revenue` | 月營收資訊 | 財務 |
| `get_stock_valuation_ratios` | 估值比率 | 財務 |
| `get_dividend_rights_schedule` | 除權息行事曆 | 財務 |
| `get_stock_monthly_trading` | 月交易統計 | 統計 |
| `get_stock_yearly_trading` | 年交易統計 | 統計 |
| `get_stock_monthly_average` | 月平均價格 | 統計 |
| `get_margin_trading_info` | 融資融券資訊 | 市場 |
| `get_real_time_trading_stats` | 即時交易統計 | 市場 |
| `get_etf_regular_investment_ranking` | ETF定期定額排名 | 市場 |
| `get_market_index_info` | 台灣加權指數 | 市場 |
| `get_market_historical_index` | 市場重要指數 | 市場 |
| `get_taiwan_holiday_info` | 節假日查詢 | 節假日 |
| `check_taiwan_trading_day` | 交易日判斷 | 節假日 |
| `get_foreign_investment_by_industry` | 外資持股（按產業別） | 外資 |
| `get_top_foreign_holdings` | 外資持股前20名 | 外資 |

## 使用範例

以下是透過 Claude Desktop 或其他 MCP 客戶端使用這些工具的範例。

### 股票價格查詢

**使用者提問：**
> "請查詢台積電目前的股價"

**AI 回應：**
AI 會自動調用 `get_taiwan_stock_price` 工具，參數為 `"台積電"` 或 `"2330"`，然後返回即時股價、漲跌幅、成交量等資訊。

**工具調用：**

```json
{
  "tool": "get_taiwan_stock_price",
  "arguments": {
    "symbol": "2330"
  }
}
```

### 模擬交易

**使用者提問：**
> "幫我模擬買入 1000 股台積電"

**AI 回應：**
AI 會調用 `buy_taiwan_stock` 工具，計算手續費和總成本，並返回完整的交易結果。

**工具調用：**

```json
{
  "tool": "buy_taiwan_stock",
  "arguments": {
    "symbol": "2330",
    "quantity": 1000
  }
}
```

**限價交易範例：**
> "以每股 510 元的價格買入 2000 股台積電"

```json
{
  "tool": "buy_taiwan_stock",
  "arguments": {
    "symbol": "2330",
    "quantity": 2000,
    "price": 510.0
  }
}
```

### 財務資訊查詢

**使用者提問：**
> "請分析台積電的財務狀況，包括損益表和公司基本資料"

**AI 回應：**
AI 會依序調用多個工具來獲取完整資訊：

1. **公司基本資料**

```json
{
  "tool": "get_company_profile",
  "arguments": {
    "symbol": "2330"
  }
}
```

2. **損益表**

```json
{
  "tool": "get_company_income_statement",
  "arguments": {
    "symbol": "2330"
  }
}
```

3. **估值比率**

```json
{
  "tool": "get_stock_valuation_ratios",
  "arguments": {
    "symbol": "2330"
  }
}
```

### 綜合分析範例

**使用者提問：**
> "我想了解台積電是否適合投資，請幫我分析股價、財務狀況、股利配息和外資持股情況"

**AI 工作流程：**

AI 會智慧地調用多個工具來完成綜合分析：

1. 查詢即時股價 (`get_taiwan_stock_price`)
2. 獲取公司基本資料 (`get_company_profile`)
3. 查看估值比率 (`get_stock_valuation_ratios`)
4. 檢查股利配息記錄 (`get_company_dividend`)
5. 查詢外資持股前 20 名 (`get_top_foreign_holdings`)
6. 分析月營收趨勢 (`get_company_monthly_revenue`)

然後將所有資訊整合，提供完整的投資建議。

### 市場統計

**使用者提問：**
> "現在台股大盤的情況如何？"

**AI 回應：**

```json
{
  "tool": "get_real_time_trading_stats",
  "arguments": {}
}
```

AI 會返回當前市場的即時統計，包括成交量、漲跌家數、漲停跌停股票等。

### 節假日與交易日判斷

**使用者提問：**
> "2025年10月10日是交易日嗎？"

**AI 回應：**

```json
{
  "tool": "check_taiwan_trading_day",
  "arguments": {
    "date": "2025-10-10"
  }
}
```

AI 會告訴你該日期是否為交易日，並說明原因（是否為週末或國定假日）。

### 對話式交互範例

**完整對話流程：**

**使用者：** "請幫我查詢鴻海的股價，如果股價低於 100 元，就模擬買入 2000 股"

**AI 執行：**

1. 先調用 `get_taiwan_stock_price("鴻海")` 查詢股價
2. 根據返回結果判斷價格
3. 如果符合條件，調用 `buy_taiwan_stock("2317", 2000)`
4. 整合結果並回覆使用者

**使用者：** "今天外資買超最多的是哪些股票？"

**AI 執行：**

1. 調用 `get_top_foreign_holdings()` 獲取外資持股資訊
2. 分析買賣超數據
3. 整理並回覆前幾名的股票及買超金額

## 支援

- **GitHub Issues**: <https://github.com/sacahan/CasualMarket/issues>
- **GitHub Repository**: <https://github.com/sacahan/CasualMarket>

## 許可證

MIT License - 詳見 [LICENSE](LICENSE) 檔案

## 重要提示

- 本工具僅供學習和研究用途
- 股票資料可能有延遲，**請勿用於實際交易決策**
- 模擬交易功能**不涉及真實資金**
- 使用本工具產生的結果需自行承擔風險

## 鳴謝

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP 框架
- [台灣證交所](https://www.twse.com.tw/) - 市場資料
- 所有貢獻者和用戶的支持

---

**更新時間**: 2025年10月22日  
**版本**: 0.1.0
