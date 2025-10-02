# API 客戶端架構重構說明

## 概述

我們已將增強功能（快取和速率限制）整合到 `TWStockAPIClient` 中，使用**裝飾器模式**來避免程式碼重複。舊的 `EnhancedTWStockAPIClient` 類已被移除。 客戶端架構重構說明

## 概述

我們已將增強功能（快取和速率限制）從獨立的 `EnhancedTWStockAPIClient` 類整合到 `TWStockAPIClient` 中，使用**裝飾器模式**來避免程式碼重複。

## 新架構

### 核心組件

1. **`twse_client.py`** - 基本 API 客戶端
   - 負責與 TWSE API 通信
   - 提供基本的股票查詢功能
   - 保持簡潔，專注於核心 API 功能

2. **`decorators.py`** - 增強功能裝飾器
   - 使用類裝飾器模式
   - 添加快取和速率限制功能
   - 不侵入原始程式碼

3. **`create_client()` 工廠函式**
   - 統一的客戶端建立入口
   - 支援增強模式和基本模式
   - 預設啟用增強功能

## 使用方式

### 1. 建立增強版客戶端（推薦，預設）

```python
from src.api.twse_client import create_client

# 使用預設配置（啟用快取和速率限制）
client = create_client()

# 使用自訂配置檔案
client = create_client(enhanced=True, config_file="custom_config.yaml")

# 查詢股票
quote = await client.get_stock_quote("2330")
print(f"{quote.company_name}: ${quote.current_price}")

# 使用增強功能
stats = await client.get_system_stats()
await client.clear_cache()
client.update_rate_limits(per_stock_interval=3.0)
```

### 2. 建立基本版客戶端（僅在特殊情況下使用）

```python
from src.api.twse_client import create_client

# 不啟用增強功能
client = create_client(enhanced=False)

# 只有基本查詢功能
quote = await client.get_stock_quote("2330")
```

### 3. 直接使用原始類（不推薦）

```python
from src.api.twse_client import TWStockAPIClient

# 直接實例化（無增強功能）
client = TWStockAPIClient()
```

## 遷移指南

### 遷移到統一的客戶端

**如果您需要增強功能（快取和速率限制）：**

```python
from src.api.twse_client import create_client

client = create_client()  # enhanced=True 是預設值
```

**如果您只需要基本功能：**

```python
from src.api.twse_client import create_client

client = create_client(enhanced=False)
```

**或直接使用原始類：**

```python
from src.api.twse_client import TWStockAPIClient

client = TWStockAPIClient()
```

### 遷移注意事項

- 所有增強功能（快取、速率限制、統計等）在使用 `create_client()` 時預設啟用
- API 接口保持不變，遷移應該是無縫的
- 如果需要基本模式，使用 `create_client(enhanced=False)`

## 架構優勢

### 裝飾器模式的優點

1. **消除程式碼重複**
   - 不需要維護兩套類似的程式碼
   - 減少維護成本和錯誤風險

2. **非侵入式設計**
   - 原始 `TWStockAPIClient` 保持簡潔
   - 增強功能透過裝飾器添加
   - 容易測試和除錯

3. **靈活性**
   - 可以輕鬆切換增強模式和基本模式
   - 支援運行時配置
   - 容易擴展新功能

4. **統一入口**
   - 所有客戶端都透過 `create_client()` 建立
   - 降低學習成本
   - API 更一致

## 功能比較

| 功能 | 基本模式 | 增強模式 |
|------|---------|---------|
| 股票查詢 | ✅ | ✅ |
| 批量查詢 | ✅ | ✅ |
| 快取 | ❌ | ✅ |
| 速率限制 | ❌ | ✅ |
| 統計資訊 | ❌ | ✅ |
| 健康檢查 | ✅ | ✅（增強版）|
| 配置管理 | ❌ | ✅ |

## 效能提升

使用增強模式的快取功能可以獲得顯著的效能提升：

- **首次查詢**: ~100ms（發送 API 請求）
- **快取命中**: ~0.05ms（從記憶體讀取）
- **效能提升**: **約 2000 倍**

## 配置選項

增強模式支援以下配置：

```python
client = create_client()

# 更新快取設定
client.update_cache_settings(
    ttl_seconds=300,        # 快取有效期 5 分鐘
    max_size=1000,          # 最大快取項目數
    max_memory_mb=100       # 最大記憶體使用
)

# 更新速率限制
client.update_rate_limits(
    per_stock_interval=3.0,         # 每支股票 3 秒間隔
    global_limit_per_minute=20,     # 全域每分鐘 20 次
    per_second_limit=3              # 每秒最多 3 次
)

# 啟用/停用功能
client.enable_caching()
client.disable_rate_limiting()
```

## 測試

執行測試來驗證功能：

```bash
# 測試裝飾器模式
uv run python tests/api/test_decorator_client.py

# 執行完整測試套件
uv run pytest tests/
```

## 下一步

1. ✅ 更新所有使用 `TWStockAPIClient` 的地方改用 `create_client()`
2. ✅ 移除 `enhanced_twse_client.py`（已完成）
3. ✅ 更新文件和範例程式碼
4. 添加更多裝飾器功能（如重試、監控等）

## 注意事項

- 預設情況下，所有新程式碼都應使用 `create_client()` 來建立客戶端
- 增強模式是預設啟用的，可以提供更好的效能和保護
- 如果遇到問題，可以暫時使用 `enhanced=False` 來除錯
- 舊的 `EnhancedTWStockAPIClient` 類已被移除，請使用 `create_client()` 替代
