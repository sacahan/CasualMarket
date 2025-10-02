#!/usr/bin/env python3
"""
測試裝飾器模式的增強 API 客戶端
"""

import asyncio

from src.api.twse_client import create_client


async def test_basic_client():
    """測試基本客戶端 (無增強功能)"""
    print("\n" + "=" * 60)
    print("測試基本客戶端 (無快取和速率限制)")
    print("=" * 60)

    client = create_client(enhanced=False)

    try:
        # 查詢台積電
        quote = await client.get_stock_quote("2330")
        print(f"\n✓ 成功查詢: {quote.company_name} ({quote.symbol})")
        print(f"  價格: ${quote.current_price}")
        print(f"  漲跌: {quote.change:+.2f} ({quote.change_percent * 100:+.2f}%)")
    except Exception as e:
        print(f"\n✗ 查詢失敗: {e}")


async def test_enhanced_client():
    """測試增強客戶端 (帶快取和速率限制)"""
    print("\n" + "=" * 60)
    print("測試增強客戶端 (帶快取和速率限制)")
    print("=" * 60)

    client = create_client(enhanced=True)

    # 顯示配置
    print("\n📋 客戶端配置:")
    print(f"  速率限制: {client.is_rate_limiting_enabled()}")
    print(f"  快取: {client.is_caching_enabled()}")

    # 配置短 TTL 以便測試
    client.update_cache_settings(ttl_seconds=5)
    client.update_rate_limits(
        per_stock_interval=2.0,
        global_limit_per_minute=10,
        per_second_limit=2,
    )

    print("\n🔧 已更新配置:")
    print("  快取 TTL: 5 秒")
    print("  每支股票間隔: 2 秒")
    print("  全域限制: 10 次/分鐘")
    print("  每秒限制: 2 次")

    try:
        # 第一次查詢 (應該會發送 API 請求)
        print("\n📡 第一次查詢台積電 (2330)...")
        quote1 = await client.get_stock_quote("2330")
        print(f"✓ {quote1.company_name}: ${quote1.current_price}")

        # 第二次查詢 (應該從快取返回)
        print("\n💾 第二次查詢台積電 (應該從快取返回)...")
        quote2 = await client.get_stock_quote("2330")
        print(f"✓ {quote2.company_name}: ${quote2.current_price}")

        # 強制刷新 (會清除快取並發送新請求)
        print("\n🔄 強制刷新查詢...")
        quote3 = await client.get_stock_quote("2330", force_refresh=True)
        print(f"✓ {quote3.company_name}: ${quote3.current_price}")

        # 批量查詢
        print("\n📊 批量查詢多支股票...")
        symbols = ["2330", "2317", "2454"]
        quotes = await client.get_multiple_quotes(symbols)
        print(f"✓ 成功查詢 {len(quotes)}/{len(symbols)} 支股票:")
        for q in quotes:
            print(f"  - {q.company_name} ({q.symbol}): ${q.current_price}")

        # 顯示統計資訊
        print("\n📈 系統統計:")
        stats = await client.get_system_stats()
        print(f"  快取命中率: {stats.get('cache', {}).get('hit_rate', 0) * 100:.1f}%")
        print(f"  總請求數: {stats.get('requests', {}).get('total', 0)}")
        print(f"  成功請求: {stats.get('requests', {}).get('successful', 0)}")
        print(f"  失敗請求: {stats.get('requests', {}).get('failed', 0)}")

    except Exception as e:
        print(f"\n✗ 發生錯誤: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """主測試函式"""
    print("\n🚀 台灣證交所 API 客戶端裝飾器測試")
    print("=" * 60)

    # 測試基本客戶端
    await test_basic_client()

    # 等待一下
    await asyncio.sleep(1)

    # 測試增強客戶端
    await test_enhanced_client()

    print("\n" + "=" * 60)
    print("✅ 測試完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
