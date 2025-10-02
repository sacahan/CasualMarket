# CasualMarket 尚未實作工具清單

本文件記錄了 TWSEMCPServer 專案中存在但 CasualMarket 專案尚未實作的工具功能。

## 📊 實作進度概覽

- **已實作**: 21 個工具 (13 + 8)
- **尚未實作**: 12 個工具 (20 - 8)
- **總計**: 33 個工具
- **完成度**: 63.6%

---

## ❌ 尚未實作的工具 (12個)

### 🏢 Company/ESG Tools (5個)

#### 1. `get_company_governance_info`

- **功能**: 取得公司治理資訊
- **API端點**: `/opendata/t187ap46_L_9`
- **參數**: `code: str` - 公司股票代碼
- **回傳**: 公司治理相關資訊

#### 2. `get_company_climate_management`

- **功能**: 取得氣候相關管理資訊
- **API端點**: `/opendata/t187ap46_L_8`
- **參數**: `code: str` - 公司股票代碼
- **回傳**: 氣候管理政策與措施

#### 3. `get_company_risk_management`

- **功能**: 取得風險管理政策資訊
- **API端點**: `/opendata/t187ap46_L_19`
- **參數**: `code: str` - 公司股票代碼
- **回傳**: 風險管理相關資料

#### 4. `get_company_supply_chain_management`

- **功能**: 取得供應鏈管理資訊
- **API端點**: `/opendata/t187ap46_L_13`
- **參數**: `code: str` - 公司股票代碼
- **回傳**: 供應鏈管理政策與實務

#### 5. `get_company_info_security`

- **功能**: 取得資訊安全資料
- **API端點**: `/opendata/t187ap46_L_16`
- **參數**: `code: str` - 公司股票代碼
- **回傳**: 資訊安全管理資訊

---

### 📰 News Tools (3個)

#### 6. `get_company_major_news`

- **功能**: 取得公司重大訊息
- **API端點**: `/opendata/t187ap04_L`
- **參數**: `code: str = ""` - 公司股票代碼 (可選)
- **回傳**: 重大訊息公告
- **特殊功能**: 可查詢特定公司或全部公司的重大訊息

#### 7. `get_twse_news`

- **功能**: 取得證交所新聞
- **API端點**: `/news/newsList`
- **參數**:
  - `start_date: str = ""` - 開始日期 (YYYYMMDD)
  - `end_date: str = ""` - 結束日期 (YYYYMMDD)
- **回傳**: 證交所官方新聞
- **特殊功能**: 支援日期範圍篩選，自動處理民國年轉換

#### 8. `get_twse_events`

- **功能**: 取得證交所活動資訊
- **API端點**: `/news/eventList`
- **參數**: `top: int = 10` - 返回筆數
- **回傳**: 證交所舉辦的活動、研習會等資訊

---

### 📈 Trading/Periodic Tools (3個)

#### 9. `get_stock_monthly_average`

- **功能**: 取得股票月平均價格
- **API端點**: `/exchangeReport/STOCK_DAY_AVG_ALL`
- **參數**: `code: str` - 股票代碼
- **回傳**: 日收盤價與月平均價格

#### 10. `get_stock_monthly_trading`

- **功能**: 取得月交易資訊
- **API端點**: `/exchangeReport/FMSRFK_ALL`
- **參數**: `code: str` - 股票代碼
- **回傳**: 月度交易統計資料

#### 11. `get_stock_yearly_trading`

- **功能**: 取得年交易資訊
- **API端點**: `/exchangeReport/FMNPTK_ALL`
- **參數**: `code: str` - 股票代碼
- **回傳**: 年度交易統計資料

---

### 💰 Valuation Tools (1個)

#### 12. `get_stock_valuation_ratios`

- **功能**: 取得估值比率 (P/E, P/B, 殖利率)
- **API端點**: `/exchangeReport/BWIBBU_ALL`
- **參數**: `code: str` - 股票代碼
- **回傳**: 本益比、股價淨值比、殖利率等估值指標

---

### 🎫 Warrant Tools (3個)

#### 13. `get_warrant_basic_info`

- **功能**: 取得權證基本資訊
- **API端點**: `/opendata/t187ap37_L`
- **參數**: `code: str = ""` - 權證代碼 (可選)
- **回傳**: 權證基本資料、履約條件等
- **特殊功能**: 可查詢特定權證或全部權證

#### 14. `get_warrant_daily_trading`

- **功能**: 取得權證日交易資料
- **API端點**: `/opendata/t187ap42_L`
- **參數**: `code: str = ""` - 權證代碼 (可選)
- **回傳**: 權證日交易量值統計
- **特殊功能**: 可查詢特定權證或全部權證

#### 15. `get_warrant_trader_count`

- **功能**: 取得權證交易人數
- **API端點**: `/opendata/t187ap43_L`
- **參數**: 無
- **回傳**: 每日權證交易人數統計

---

### 💸 Dividend Schedule Tools (1個)

#### 16. `get_dividend_rights_schedule`

- **功能**: 取得除權息行事曆
- **API端點**: `/exchangeReport/TWT48U_ALL`
- **參數**: `code: str = ""` - 股票代碼 (可選)
- **回傳**: 除權息日期、配股配息資訊等
- **特殊功能**: 可查詢特定公司或全部公司的除權息資訊

---

### 🌐 Market/Foreign Tools (4個)

#### 17. `get_market_historical_index`

- **功能**: 取得歷史指數資料
- **API端點**: `/indicesReport/MI_5MINS_HIST`
- **參數**: 無
- **回傳**: TAIEX 歷史資料，用於長期趨勢分析

#### 18. `get_foreign_investment_by_industry`

- **功能**: 取得外資持股(按產業別)
- **API端點**: `/fund/MI_QFIIS_cat`
- **參數**: 無
- **回傳**: 各產業外資與陸資持股比率統計

#### 19. `get_top_foreign_holdings`

- **功能**: 取得外資持股前20名
- **API端點**: `/fund/MI_QFIIS_sort_20`
- **參數**: 無
- **回傳**: 外資持股排名前20的公司詳細資訊

---

## 🛠️ 實作建議

### 優先級分類

#### 🔴 高優先級 (核心交易功能)

1. `get_stock_valuation_ratios` - 估值分析必備
2. `get_dividend_rights_schedule` - 股息投資策略必需
3. `get_stock_monthly_trading` / `get_stock_yearly_trading` - 長期分析
4. `get_foreign_investment_by_industry` / `get_top_foreign_holdings` - 外資分析

#### 🟡 中優先級 (市場資訊)

1. `get_company_major_news` - 重大訊息影響股價
2. `get_market_historical_index` - 市場趨勢分析
3. `get_stock_monthly_average` - 技術分析參考

#### 🟢 低優先級 (進階功能)

1. ESG 相關工具 (5個) - 永續投資趨勢
2. 權證相關工具 (3個) - 衍生性商品
3. 新聞活動工具 (2個) - 資訊服務

### 實作架構

#### 1. 新增到 FinancialAnalysisTool

- ESG 相關工具
- 估值分析工具
- 外資分析工具

#### 2. 新增到 server.py 主要工具

- 新聞相關工具
- 權證相關工具
- 週期性交易資料工具

#### 3. 建立新的工具類別

- `NewsAnalysisTool` - 新聞與公告分析
- `WarrantAnalysisTool` - 權證分析
- `ForeignInvestmentTool` - 外資分析

---

## 📋 實作檢查清單

### Phase 1: 核心功能 (8個工具) ✅ 已完成

- [x] `get_stock_valuation_ratios`
- [x] `get_dividend_rights_schedule`
- [x] `get_stock_monthly_trading`
- [x] `get_stock_yearly_trading`
- [x] `get_stock_monthly_average`
- [x] `get_foreign_investment_by_industry`
- [x] `get_top_foreign_holdings`
- [x] `get_market_historical_index`

### Phase 2: 資訊服務 (7個工具)

- [ ] `get_company_major_news`
- [ ] `get_twse_news`
- [ ] `get_twse_events`
- [ ] `get_warrant_basic_info`
- [ ] `get_warrant_daily_trading`
- [ ] `get_warrant_trader_count`

### Phase 3: ESG 與治理 (5個工具)

- [ ] `get_company_governance_info`
- [ ] `get_company_climate_management`
- [ ] `get_company_risk_management`
- [ ] `get_company_supply_chain_management`
- [ ] `get_company_info_security`

---

## 🔧 技術考量

### API 整合

- 所有工具都使用現有的 `OpenAPIClient`
- 透過 `@with_cache` 裝飾器提供快取與速率限制
- 統一的錯誤處理與日誌記錄

### 資料格式

- 維持與現有工具一致的回傳格式
- 提供 `success/error` 狀態指示
- 包含 `source` 欄位標示資料來源

### 測試策略

- 每個工具都需要單元測試
- 整合測試驗證 API 連線
- 錯誤處理測試確保穩定性

---

_最後更新: 2025-10-02_
_文件版本: 1.0_
