#!/bin/bash
# 開發專用執行腳本 - 避免 uvx 快取問題

echo "🚀 開發模式啟動 CasualMarket MCP Server"
echo "使用 uv run 避免快取問題"

# 使用 uv run 直接執行，避免 uvx 快取
uv run python -m src.main "$@"
