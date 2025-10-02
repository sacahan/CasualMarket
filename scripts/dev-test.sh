#!/bin/bash
# 開發專用測試腳本 - 即時測試功能

echo "🧪 開發模式測試"

# 測試股價查詢功能
echo "測試股價查詢 (台積電 2330)..."
uv run python -c "
import asyncio
from src.api.twse_client import create_client

async def test():
    client = create_client()
    try:
        result = await client.get_stock_quote('2330')
        print(f'✅ 台積電價格: {result.current_price}')
    except Exception as e:
        print(f'❌ 錯誤: {e}')
    finally:
        client.close()

asyncio.run(test())
"

echo ""
echo "測試財務分析功能..."
uv run python -c "
import asyncio
from src.tools.financial.company_profile import CompanyProfileTool

async def test():
    tool = CompanyProfileTool()
    try:
        result = await tool.safe_execute(symbol='2330')
        if result['success']:
            company_data = result.get('data', {})
            company_name = company_data.get('公司簡稱', company_data.get('name', 'N/A'))
            print(f'✅ 公司資料: {company_name}')
        else:
            print(f'❌ 財務查詢失敗: {result.get(\"error\", \"Unknown\")}')
    except Exception as e:
        print(f'❌ 錯誤: {e}')

asyncio.run(test())
"
