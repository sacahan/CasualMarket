# CasualMarket - 台灣股票交易 MCP Server

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.7.0+-green.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-98%25%20passing-success.svg)](https://github.com/sacahan/CasualMarket)

一個功能完整的**台灣股票交易 MCP Server**，提供超過 **23 個專業工具**，涵蓋即時股價查詢、財務分析、市場資訊、模擬交易等多種功能。基於 **FastMCP 2.7.0+** 框架開發，具備智慧快取和頻率限制機制。

## 目錄

- [快速開始](#快速開始)
- [核心功能](#核心功能)
- [工具列表](#工具列表)
- [使用範例](#使用範例)
- [配置說明](#配置說明)
- [測試與品質](#測試與品質)
- [專案結構](#專案結構)
- [技術架構](#技術架構)
- [部署](#部署)
- [貢獻指南](#貢獻指南)

## 快速開始

### 安裝依賴

```bash
# 使用 uv 套件管理器
uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 執行伺服器

```bash
# 開發模式
uv run python -m src.main

# 生產模式
uvx --from . casual-market-mcp
```

### Claude Desktop 配置

編輯 Claude Desktop 配置檔：

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

配置檔位置：

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

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

### 股票價格查詢

```python
# 使用股票代碼
result = await get_taiwan_stock_price("2330")

# 使用公司名稱
result = await get_taiwan_stock_price("台積電")
```

### 模擬交易

```python
# 買入 1000 股台積電（市價）
buy_result = await buy_taiwan_stock("2330", 1000)

# 限價買入 2000 股（每股 510 元）
buy_result = await buy_taiwan_stock("2330", 2000, 510.0)

# 賣出 1000 股
sell_result = await sell_taiwan_stock("2330", 1000)
```

### 財務資訊查詢

```python
# 公司基本資料
profile = await get_company_profile("2330")

# 損益表
income = await get_company_income_statement("2330")

# 股利分配
dividend = await get_company_dividend("2330")

# 估值比率
valuation = await get_stock_valuation_ratios("2330")
```

### 市場統計

```python
# 實時交易統計
stats = await get_real_time_trading_stats()

# 融資融券資訊
margin = await get_margin_trading_info()

# ETF排名
etf_rank = await get_etf_regular_investment_ranking()
```

### 節假日判斷

```python
# 查詢特定日期是否為假日
holiday = await get_taiwan_holiday_info("2025-01-01")

# 判斷是否為交易日
trading_day = await check_taiwan_trading_day("2025-10-07")
```

## 配置說明

### 環境變數

複製 `.env.simple` 並根據需求修改：

```bash
cp .env.simple .env
```

### 主要配置項目

```env
# 日誌級別：DEBUG, INFO, WARNING, ERROR
MARKET_MCP_LOG_LEVEL=INFO

# API 請求超時時間（秒）
MARKET_MCP_API_TIMEOUT=10

# 限速：每個股票的請求間隔（秒）
MARKET_MCP_RATE_LIMIT_INTERVAL=30.0

# 快取：快取存活時間（秒）
MARKET_MCP_CACHE_TTL=30

# 快取：最大條目數
MARKET_MCP_CACHE_MAX_SIZE=1000
```

## 測試與品質

### 運行測試

```bash
# 運行所有測試
uv run pytest

# 運行特定測試類別
uv run pytest tests/server/          # 伺服器功能測試
uv run pytest tests/tools/           # 工具功能測試
uv run pytest tests/api/             # API 整合測試

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

### 測試狀態

- **總測試案例**：110 個
- **通過測試**：108 個（98%）
- **跳過測試**：2 個（2%）
- **失敗測試**：0 個（0%）
- **程式碼覆蓋率**：62%

## 專案結構

```text
CasualMarket/
├── src/
│   ├── main.py                      # 應用程式入口
│   ├── server.py                    # MCP 服務器和工具註冊
│   ├── api/                         # API 客戶端層
│   │   ├── twse_client.py          # 台灣證交所 API
│   │   ├── openapi_client.py       # OpenAPI 客戶端
│   │   ├── holiday_client.py       # 節假日 API
│   │   └── decorators.py           # 快取和限速裝飾器
│   ├── tools/                       # MCP 工具實現
│   │   ├── trading/                # 交易工具
│   │   ├── financial/              # 財務工具
│   │   ├── market/                 # 市場工具
│   │   ├── foreign/                # 外資工具
│   │   └── base/                   # 基礎類別和工具
│   ├── models/                      # 資料模型
│   │   └── mcp_response.py        # MCP 統一回應格式
│   ├── utils/                       # 工具函數
│   │   ├── logging.py             # 日誌配置
│   │   └── validators.py          # 輸入驗證
│   ├── cache/                       # 快取系統
│   ├── data/                        # 資料檔案
│   └── securities_db.py            # 證券資料庫
├── tests/                           # 測試套件
│   ├── server/                      # 伺服器測試
│   ├── tools/                       # 工具測試
│   ├── api/                         # API 測試
│   └── mcp_tools/                   # MCP 整合測試
├── scripts/                         # 輔助腳本
│   ├── dev-run.sh                  # 開發執行腳本
│   └── dev-test.sh                 # 開發測試腳本
├── pyproject.toml                   # 專案配置
├── README.md                        # 本檔案
└── LICENSE                          # MIT 授權
```

## 技術架構

### 核心組件

1. **FastMCP Server** - 使用 `@mcp.tool` 裝飾器簡化工具註冊
2. **API 客戶端層** - 整合台灣證交所 API 與 OpenAPI
3. **快取系統** - 整合限速與快取服務
4. **工具基類** - 提供統一的 MCP 回應格式和錯誤處理
5. **模型層** - 類型安全的資料模型定義

### 架構模式

- **FastMCP 整合** - 使用 `@mcp.tool` 裝飾器代替傳統 MCP 伺服器設定
- **模組化設計** - 可插拔的工具組件，易於擴展
- **統一回應格式** - 所有工具返回 `MCPToolResponse[T]` 格式
- **多層級驗證** - 符號格式、市場類型、API 回應驗證
- **錯誤處理** - 統一的錯誤處理和日誌記錄

### 工作流程示例

```python
# 1. 查詢股票價格
price_info = await get_taiwan_stock_price("2330")

# 2. 查詢公司財務資訊
company_profile = await get_company_profile("2330")
valuation = await get_stock_valuation_ratios("2330")

# 3. 查詢市場統計
market_stats = await get_real_time_trading_stats()

# 4. 執行模擬交易
buy_result = await buy_taiwan_stock("2330", 1000)

# 5. 查詢交易統計
daily_trading = await get_stock_daily_trading("2330")
```

## 部署

### Docker 部署

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

CMD ["uv", "run", "python", "-m", "src.main"]
```

### 系統需求

- Python 3.12+
- uv 套件管理器
- 網路連線（用於 API 調用）
- SQLite 支援

### 效能特性

- **快取機制** - 30秒 TTL，最多1000條目
- **限速保護** - 每個股票30秒間隔，全域每分鐘20個請求
- **非同步設計** - 完整的非同步 API，支援高併發
- **智慧重試** - 最多5次 API 重試

## 貢獻指南

歡迎提交 Issue 和 Pull Request！

### 開發流程

1. Fork 本專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

### 開發工具

```bash
# 開發模式運行
./scripts/dev-run.sh

# 快速測試
./scripts/dev-test.sh
```

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
