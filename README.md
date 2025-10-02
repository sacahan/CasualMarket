# CasualMarket

台灣股價即時查詢 MCP Server，提供透過 Model Context Protocol 存取台灣證券交易所即時股價資訊的功能。基於 FastMCP 框架開發，具備智能速率限制、快取機制和進階財務分析功能。

## ✨ Features

### 核心功能

- 📈 **即時股價查詢** - 支援台灣證券交易所即時股價資訊
- 🔍 **智能查詢** - 支援股票代碼 (2330) 和公司名稱 ("台積電") 查詢
- ⚡ **速率限制與快取** - 內建 API 頻率限制和智能快取機制
- 💰 **模擬交易** - 完整的股票買賣模擬功能 (最小 1000 股單位)
- 📊 **財務報表分析** - 損益表、資產負債表和公司基本資訊查詢
- 🛡️ **容錯機制** - 智能快取和錯誤處理機制確保服務穩定性

### 技術特色

- 🚀 **FastMCP 整合** - 使用 `@mcp.tool` 裝飾器簡化工具註冊
- 🗄️ **本地證券資料庫** - SQLite 資料庫存儲 ISIN 代碼和公司名稱映射
- ⚡ **裝飾器增強** - 使用函數裝飾器為 API 方法添加快取和速率限制
- 📝 **完整類型支援** - 使用 Pydantic 模型進行數據驗證和序列化
- 🧪 **完善測試** - 覆蓋率 >80%，包含 API 整合和 MCP 協議測試

## 🚀 Installation & Usage

### 快速啟動

```bash
# 使用 uvx 啟動 MCP 伺服器 (推薦)
uvx --from . casual-market-mcp

# 或使用開發模式
uv run python src/main.py
```

### Claude Desktop 設定

在 Claude Desktop 配置檔中添加：

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

## 🛠️ MCP Tools

| 工具名稱                       | 功能描述             | 支援輸入               |
| ------------------------------ | -------------------- | ---------------------- |
| `get_taiwan_stock_price`       | 查詢台灣股票即時價格 | 股票代碼或公司名稱     |
| `buy_taiwan_stock`             | 模擬股票買入操作     | 代碼、股數、價格(可選) |
| `sell_taiwan_stock`            | 模擬股票賣出操作     | 代碼、股數、價格(可選) |
| `get_company_income_statement` | 取得公司綜合損益表   | 股票代碼               |
| `get_company_balance_sheet`    | 取得公司資產負債表   | 股票代碼               |
| `get_company_profile`          | 取得公司基本資訊     | 股票代碼               |

### 使用範例

```python
# 查詢台積電股價 (支援代碼或公司名稱)
await get_taiwan_stock_price("2330")
await get_taiwan_stock_price("台積電")

# 模擬買入 1000 股台積電
await buy_taiwan_stock("2330", 1000)

# 查詢公司財務報表
await get_company_income_statement("2330")
```

## 🏗️ Architecture

### 專案結構

```
src/
├── api/                    # API 客戶端層
│   ├── twse_client.py     # 標準 TWSE API 整合
│   ├── openapi_client.py  # OpenAPI 財務報表客戶端
│   └── decorators.py      # API 裝飾器和重試邏輯
├── cache/                  # 快取和速率限制
│   ├── rate_limited_cache_service.py
│   └── cache_manager.py
├── models/                 # 資料模型
│   ├── stock_data.py      # 股票資料模型
│   └── trading_models.py  # 交易操作模型
├── tools/analysis/         # 財務分析工具
│   └── financials.py      # 財務分析核心邏輯
├── scrapers/              # 資料爬蟲
│   └── twse_isin_scraper.py
├── utils/                 # 工具函數
├── server.py              # FastMCP 伺服器主程式
├── securities_db.py       # 證券資料庫管理
└── main.py               # 應用程式進入點
```

### 核心架構模式

- **FastMCP 整合**: 使用 `@mcp.tool` 裝飾器取代傳統 MCP 伺服器設定
- **裝飾器增強**: 使用 `@with_cache` 裝飾器為 API 方法添加快取和速率限制
- **速率限制快取**: 所有 API 呼叫透過 `RateLimitedCacheService` 防止 API 濫用
- **分層驗證**: 多層級輸入驗證 (符號格式、市場類型、API 回應)
- **公司名稱解析**: 透過本地 SQLite 資料庫支援代碼和名稱查詢
- **模組化工具設計**: 財務分析工具採用相依注入的可插拔組件

## 🧪 Development

### 測試

```bash
# 執行所有測試
uv run pytest

# 執行特定測試類別
uv run pytest tests/api/           # API 整合測試
uv run pytest tests/server/        # 伺服器功能測試
uv run pytest tests/mcp/           # MCP 協議測試
uv run pytest tests/tools/         # 工具功能測試

# 執行單一測試檔案
uv run pytest tests/api/test_twse_standalone.py

# 生成覆蓋率報告
uv run pytest --cov=src --cov-report=html
```

### 程式碼品質

```bash
# 程式碼檢查
uv run ruff check src/ tests/

# 類型檢查
uv run mypy src/

# 自動修復可修復的問題
uv run ruff check --fix src/ tests/
```

### 開發環境驗證

```bash
# 測試 uvx 執行和 MCP 協議
./tests/test_uvx_execution.sh

# 測試增強客戶端功能
uv run python tests/api/demo_enhanced_client.py

# API 功能除錯
uv run python tests/api/debug_api.py
```

## ⚙️ Configuration

### 環境變數

| 變數名稱                  | 預設值 | 描述              |
| ------------------------- | ------ | ----------------- |
| `MARKET_MCP_API_TIMEOUT`  | 10s    | API 請求超時時間  |
| `MARKET_MCP_API_RETRIES`  | 5      | 重試次數          |
| `MARKET_MCP_TWSE_API_URL` | -      | TWSE API 端點 URL |
| `LOG_LEVEL`               | INFO   | 日誌級別          |

### 資料庫管理

- **證券資料庫**: `src/twse_securities.db` 包含 ISIN 代碼和公司名稱映射
- **資料庫更新**: 使用 `src/scrapers/` 中的爬蟲更新公司資料
- **公司名稱解析**: 透過 `securities_db.py` 模組自動處理
- **測試資料庫**: 測試期間使用獨立的測試資料庫避免衝突

## 📄 License

MIT License - 詳見 [LICENSE](LICENSE) 檔案。

## 📚 Documentation

- [缺少工具實作清單](docs/MISSING_TOOLS_IMPLEMENTATION.md) - 尚未實作的 TWSEMCPServer 工具功能

## 🤝 Contributing

歡迎提交 Issue 和 Pull Request！請確保：

1. 遵循現有的程式碼風格
2. 添加適當的測試
3. 更新相關文件
4. 通過所有品質檢查

---

**注意**: 本專案僅供教育和研究用途，不構成投資建議。模擬交易功能僅用於測試，不涉及真實資金交易。
