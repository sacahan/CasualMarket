# CasualMarket

台灣股價即時查詢 MCP Server，提供透過 Model Context Protocol 存取台灣證券交易所即時股價資訊的功能。

## Features

- 即時股價查詢
- 支援股票代碼和公司名稱查詢
- API 頻率限制和快取機制
- 模擬交易功能
- 財務報表查詢

## Installation & Usage

```bash
# 使用 uvx 啟動 MCP 伺服器
uvx --from . casual-market-mcp
```

## MCP Tools

- `get_taiwan_stock_price`: 查詢台灣股票即時價格
- `buy_taiwan_stock`: 模擬股票買入
- `sell_taiwan_stock`: 模擬股票賣出
- `get_company_income_statement`: 取得公司損益表
- `get_company_balance_sheet`: 取得公司資產負債表
- `get_company_profile`: 取得公司基本資訊

## Development

```bash
# 執行測試
uv run pytest

# 程式碼檢查
uv run ruff check src/ tests/
uv run mypy src/
```
