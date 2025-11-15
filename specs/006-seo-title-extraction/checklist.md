# SEO Title 提取與建議功能 - 測試與驗收清單

**Feature ID:** 006-seo-title-extraction
**創建日期:** 2025-01-14
**最後更新:** 2025-01-14

---

## 📋 測試概覽

本文檔提供 SEO Title 功能的完整測試清單，涵蓋單元測試、整合測試、E2E 測試和驗收測試。

**測試原則：**
- ✅ 測試驅動開發（TDD）
- ✅ 自動化優先
- ✅ 回歸測試
- ✅ 性能測試
- ✅ 安全測試

**測試環境：**
- 本地開發環境
- CI/CD 環境
- 測試環境
- 生產環境（smoke tests）

---

## 🧪 單元測試

### 後端單元測試

#### 1. ArticleParserService - SEO Title 提取

**測試檔案：** `backend/tests/services/test_article_parser_seo_title.py`

| 測試案例 ID | 測試描述 | 預期結果 | 狀態 |
|------------|---------|---------|------|
| **UT-P-001** | AI 解析：識別「這是 SEO title：」標記 | seo_title 正確提取，seo_title_extracted = true | ⏳ |
| **UT-P-002** | AI 解析：識別「SEO標題：」標記 | seo_title 正確提取，seo_title_extracted = true | ⏳ |
| **UT-P-003** | AI 解析：無 SEO title 標記 | seo_title = null, seo_title_extracted = false | ⏳ |
| **UT-P-004** | 啟發式解析：匹配「這是 SEO title：」 | seo_title 正確提取 | ⏳ |
| **UT-P-005** | 啟發式解析：匹配「SEO標題：」 | seo_title 正確提取 | ⏳ |
| **UT-P-006** | 啟發式解析：匹配 `<title>` 標籤 | seo_title 正確提取 | ⏳ |
| **UT-P-007** | 啟發式解析：無匹配模式 | seo_title = null | ⏳ |
| **UT-P-008** | 邊界測試：空字符串 SEO title | 適當的錯誤處理 | ⏳ |
| **UT-P-009** | 邊界測試：超長 SEO title (>200 chars) | 適當的截斷或警告 | ⏳ |
| **UT-P-010** | 邊界測試：特殊字符 | 正確處理特殊字符 | ⏳ |

#### 2. UnifiedOptimizationService - SEO Title 建議生成

**測試檔案：** `backend/tests/services/test_optimization_seo_title.py`

| 測試案例 ID | 測試描述 | 預期結果 | 狀態 |
|------------|---------|---------|------|
| **UT-O-001** | 生成 SEO Title 建議 | 返回 2-3 個 variants | ⏳ |
| **UT-O-002** | 驗證 variant 結構 | 包含 id, seo_title, reasoning, keywords_focus, character_count | ⏳ |
| **UT-O-003** | 驗證字數限制 | 每個 variant 的 character_count ≤ 60 | ⏳ |
| **UT-O-004** | SEO Title 與 H1 差異化 | seo_title != h1_main 或 length(seo_title) < length(h1_main) | ⏳ |
| **UT-O-005** | 包含關鍵字焦點 | keywords_focus 包含核心關鍵字 | ⏳ |
| **UT-O-006** | 包含優化建議 notes | notes 數組非空 | ⏳ |
| **UT-O-007** | Claude API 失敗處理 | 適當的錯誤處理和 fallback | ⏳ |
| **UT-O-008** | JSON 解析錯誤處理 | 適當的錯誤處理 | ⏳ |

#### 3. SEO Title 選擇 API

**測試檔案：** `backend/tests/api/test_seo_title_selection.py`

| 測試案例 ID | 測試描述 | 預期結果 | 狀態 |
|------------|---------|---------|------|
| **UT-A-001** | 選擇 AI 建議（variant_id） | seo_title 更新，source = "ai_generated" | ⏳ |
| **UT-A-002** | 使用原文提取（use_original=true） | seo_title 更新，source = "extracted" | ⏳ |
| **UT-A-003** | 自定義輸入（custom_seo_title） | seo_title 更新，source = "user_input" | ⏳ |
| **UT-A-004** | 驗證錯誤：無效 variant_id | 返回 400 錯誤 | ⏳ |
| **UT-A-005** | 驗證錯誤：use_original 但 seo_title_extracted = false | 返回 400 錯誤 | ⏳ |
| **UT-A-006** | 驗證錯誤：custom_seo_title 超長 | 返回 400 錯誤 | ⏳ |
| **UT-A-007** | 驗證錯誤：未提供任何選擇參數 | 返回 400 錯誤 | ⏳ |
| **UT-A-008** | 權限檢查：未授權用戶 | 返回 401/403 錯誤 | ⏳ |

#### 4. WordPress 發佈整合

**測試檔案：** `backend/tests/services/test_wordpress_seo_title.py`

| 測試案例 ID | 測試描述 | 預期結果 | 狀態 |
|------------|---------|---------|------|
| **UT-W-001** | 發佈時設定 SEO Title | _yoast_wpseo_title = seo_title | ⏳ |
| **UT-W-002** | 發佈時設定 H1 標題 | title = article.title | ⏳ |
| **UT-W-003** | SEO Title fallback（無 seo_title） | _yoast_wpseo_title = title_main | ⏳ |
| **UT-W-004** | Rank Math 支援 | rank_math_title = seo_title | ⏳ |
| **UT-W-005** | Meta description 設定 | _yoast_wpseo_metadesc = meta_description | ⏳ |
| **UT-W-006** | Focus keyword 設定 | _yoast_wpseo_focuskw = seo_keywords[0] | ⏳ |

### 前端單元測試

#### 5. SEOTitleSelectionCard 元件

**測試檔案：** `frontend/src/components/parsing/__tests__/SEOTitleSelectionCard.test.tsx`

| 測試案例 ID | 測試描述 | 預期結果 | 狀態 |
|------------|---------|---------|------|
| **UT-F-001** | 元件渲染 | 元件正確渲染 | ⏳ |
| **UT-F-002** | 顯示原文提取的 SEO Title | 原文區塊顯示，「原文提取」標籤存在 | ⏳ |
| **UT-F-003** | 不顯示原文（seo_title_extracted=false） | 原文區塊不顯示 | ⏳ |
| **UT-F-004** | 顯示 AI 建議選項 | 顯示 2-3 個選項卡片 | ⏳ |
| **UT-F-005** | 選擇 AI 建議 | 調用 onSelect 回調，顯示「✓ 已選擇」 | ⏳ |
| **UT-F-006** | 使用原文提取 | 調用 onUseOriginal 回調 | ⏳ |
| **UT-F-007** | 自定義輸入顯示 | 點擊後顯示輸入框 | ⏳ |
| **UT-F-008** | 自定義輸入保存 | 調用 onCustom 回調，傳遞輸入值 | ⏳ |
| **UT-F-009** | 字數統計 | 即時顯示字數 | ⏳ |
| **UT-F-010** | 超長警告 | 超過 60 字符時顯示警告 | ⏳ |
| **UT-F-011** | 載入狀態 | isLoading=true 時禁用按鈕 | ⏳ |
| **UT-F-012** | SEO Title vs H1 說明 | 說明區塊正確顯示 | ⏳ |

---

## 🔗 整合測試

### 完整工作流程測試

**測試檔案：** `backend/tests/integration/test_seo_title_workflow.py`

| 測試案例 ID | 測試場景 | 測試步驟 | 預期結果 | 狀態 |
|------------|---------|---------|---------|------|
| **IT-001** | 原文包含 SEO Title 標記 | 1. 上傳包含「這是 SEO title：XXX」的文章<br>2. 觸發解析<br>3. 確認解析<br>4. 生成優化建議<br>5. 選擇原文 SEO Title<br>6. 發佈到 WordPress | - 解析提取 seo_title<br>- seo_title_extracted = true<br>- 優化建議包含 SEO Title variants<br>- 選擇成功，source = "extracted"<br>- WordPress 設定正確 | ⏳ |
| **IT-002** | 原文無 SEO Title 標記 | 1. 上傳無 SEO Title 標記的文章<br>2. 觸發解析<br>3. 確認解析<br>4. 生成優化建議<br>5. 選擇 AI 建議 | - seo_title = null<br>- seo_title_extracted = false<br>- AI 生成 2-3 個建議<br>- 選擇成功，source = "ai_generated" | ⏳ |
| **IT-003** | 自定義 SEO Title | 1. 解析文章<br>2. 生成優化建議<br>3. 輸入自定義 SEO Title<br>4. 保存 | - 自定義 SEO Title 保存成功<br>- source = "user_input" | ⏳ |
| **IT-004** | 完整發佈流程 | 1. 解析文章<br>2. 選擇 SEO Title<br>3. 發佈到 WordPress<br>4. 驗證 WordPress 內容 | - WordPress H1 = article.title<br>- WordPress SEO Title = seo_title<br>- 搜尋引擎顯示正確 | ⏳ |
| **IT-005** | 錯誤恢復測試 | 1. 解析失敗重試<br>2. API 調用失敗重試<br>3. 資料庫更新失敗回滾 | - 適當的錯誤處理<br>- 資料一致性保持 | ⏳ |

---

## 🎭 E2E 測試

### Playwright E2E 測試

**測試檔案：** `frontend/e2e/seo-title-selection.spec.ts`

| 測試案例 ID | 測試場景 | 用戶操作 | 預期結果 | 狀態 |
|------------|---------|---------|---------|------|
| **E2E-001** | 顯示原文提取的 SEO Title | 1. 導航到文章解析頁面<br>2. 觸發解析（AI 模式）<br>3. 確認解析<br>4. 等待優化建議生成 | - 顯示「原文提取」區塊<br>- SEO Title 文本正確<br>- 「原文提取」標籤顯示<br>- 「使用此標題」按鈕可點擊 | ⏳ |
| **E2E-002** | 選擇 AI 建議 | 1. 查看 AI 建議選項<br>2. 點擊第一個選項的「選擇」按鈕<br>3. 等待 API 回應 | - 按鈕變為「✓ 已選擇」<br>- 當前選中的 SEO Title 更新<br>- 成功提示顯示 | ⏳ |
| **E2E-003** | 自定義 SEO Title | 1. 點擊「自定義 SEO Title」按鈕<br>2. 輸入自定義標題<br>3. 點擊「保存自定義標題」 | - 輸入框顯示<br>- 字數即時更新<br>- 保存成功<br>- 當前 SEO Title 更新 | ⏳ |
| **E2E-004** | 字數統計和警告 | 1. 點擊「自定義 SEO Title」<br>2. 輸入超過 30 字的標題 | - 字數統計顯示正確<br>- 超長時顯示警告 | ⏳ |
| **E2E-005** | SEO Title 說明顯示 | 1. 查看頁面 | - SEO Title vs H1 vs Meta Description 說明顯示<br>- 說明清晰易懂 | ⏳ |
| **E2E-006** | 導航和狀態保持 | 1. 選擇 SEO Title<br>2. 導航到其他頁面<br>3. 返回解析頁面 | - 選擇的 SEO Title 狀態保持 | ⏳ |
| **E2E-007** | 錯誤處理 | 1. 模擬 API 錯誤<br>2. 嘗試選擇 SEO Title | - 錯誤提示顯示<br>- 不會崩潰<br>- 可重試 | ⏳ |

---

## ⚡ 性能測試

### 性能基準測試

| 測試案例 ID | 測試指標 | 目標值 | 測量方法 | 狀態 |
|------------|---------|--------|---------|------|
| **PERF-001** | AI 解析時間（包含 SEO Title） | < 30s | 測量 API 回應時間 | ⏳ |
| **PERF-002** | 優化建議生成時間（包含 SEO Title） | < 30s | 測量 API 回應時間 | ⏳ |
| **PERF-003** | SEO Title 選擇 API 回應時間 | < 500ms | P95 回應時間 | ⏳ |
| **PERF-004** | 前端頁面載入時間 | < 2s | Lighthouse Performance Score | ⏳ |
| **PERF-005** | 資料庫遷移時間 | < 5min | 在測試環境測量 | ⏳ |
| **PERF-006** | 並發處理能力 | 支援 10+ 並發請求 | 負載測試 | ⏳ |
| **PERF-007** | 資料庫查詢性能 | < 100ms | 查詢時間測量 | ⏳ |

---

## 🔒 安全測試

### 安全基準測試

| 測試案例 ID | 測試項目 | 測試方法 | 預期結果 | 狀態 |
|------------|---------|---------|---------|------|
| **SEC-001** | XSS 防禦（SEO Title） | 提交包含 `<script>` 標籤的 SEO Title | 標籤被轉義或移除 | ⏳ |
| **SEC-002** | SQL 注入防禦 | 提交惡意 SQL 字符串 | 不影響資料庫 | ⏳ |
| **SEC-003** | 長度限制驗證 | 提交超長 SEO Title (>200 chars) | 返回驗證錯誤 | ⏳ |
| **SEC-004** | API 身份驗證 | 未授權訪問 SEO Title 選擇端點 | 返回 401 錯誤 | ⏳ |
| **SEC-005** | CSRF 防護 | CSRF 攻擊嘗試 | 請求被拒絕 | ⏳ |
| **SEC-006** | 資料驗證 | 提交無效的 variant_id | 返回 400 錯誤 | ⏳ |

---

## ✅ 驗收測試

### 功能驗收標準

| 驗收 ID | 驗收項目 | 驗收標準 | 驗證方法 | 狀態 |
|--------|---------|---------|---------|------|
| **AC-F-001** | SEO Title 提取 | 準確率 > 95%（有標記時） | 測試集驗證 | ⏳ |
| **AC-F-002** | AI 建議生成 | 成功率 > 98% | API 成功率統計 | ⏳ |
| **AC-F-003** | SEO Title 選擇 | 錯誤率 < 1% | API 錯誤率統計 | ⏳ |
| **AC-F-004** | WordPress 發佈 | SEO Title 和 H1 正確分離 | 手動驗證 | ⏳ |
| **AC-F-005** | 三種選擇模式 | 原文/AI/自定義都可正常工作 | 功能測試 | ⏳ |

### 非功能驗收標準

| 驗收 ID | 驗收項目 | 驗收標準 | 驗證方法 | 狀態 |
|--------|---------|---------|---------|------|
| **AC-NF-001** | 性能 | 符合性能基準（見性能測試） | 性能測試 | ⏳ |
| **AC-NF-002** | 安全 | 通過安全測試（見安全測試） | 安全測試 | ⏳ |
| **AC-NF-003** | 可用性 | 用戶可理解 SEO Title 用途（>90%） | 用戶訪談 | ⏳ |
| **AC-NF-004** | 可維護性 | 代碼覆蓋率 > 75% | 代碼覆蓋率報告 | ⏳ |
| **AC-NF-005** | 部署 | 零停機部署 | 部署驗證 | ⏳ |

### 用戶故事驗收

| 用戶故事 | 驗收標準 | 驗證方法 | 狀態 |
|---------|---------|---------|------|
| **Story 1: 編輯提取原文 SEO Title** | ✅ 上傳包含標記的文章<br>✅ 顯示「原文提取」區塊<br>✅ 可選擇使用原文 | 手動測試 | ⏳ |
| **Story 2: 編輯選擇 AI 建議** | ✅ 顯示 2-3 個選項<br>✅ 顯示推理和關鍵字<br>✅ 可點擊選擇<br>✅ 選擇後顯示「✓ 已選擇」 | 手動測試 | ⏳ |
| **Story 3: 編輯自定義 SEO Title** | ✅ 可輸入自定義標題<br>✅ 字數即時統計<br>✅ 超長時警告<br>✅ 保存成功 | 手動測試 | ⏳ |
| **Story 4: 編輯理解區別** | ✅ 說明清晰顯示<br>✅ 視覺區分明顯<br>✅ AI 建議顯示 | 用戶訪談 | ⏳ |
| **Story 5: WordPress 發佈** | ✅ H1 = article.title<br>✅ SEO Title = seo_title<br>✅ 兩者不同 | WordPress 驗證 | ⏳ |

---

## 📊 測試報告

### 測試執行摘要

| 測試類型 | 總案例數 | 通過 | 失敗 | 跳過 | 通過率 |
|---------|---------|------|------|------|--------|
| 單元測試 - 後端 | 30 | - | - | - | -% |
| 單元測試 - 前端 | 12 | - | - | - | -% |
| 整合測試 | 5 | - | - | - | -% |
| E2E 測試 | 7 | - | - | - | -% |
| 性能測試 | 7 | - | - | - | -% |
| 安全測試 | 6 | - | - | - | -% |
| 驗收測試 | 10 | - | - | - | -% |
| **總計** | **77** | **-** | **-** | **-** | **-%** |

### 測試覆蓋率

| 模塊 | 行覆蓋率 | 分支覆蓋率 | 函數覆蓋率 | 目標 |
|------|---------|-----------|-----------|------|
| ArticleParserService | -% | -% | -% | > 80% |
| UnifiedOptimizationService | -% | -% | -% | > 80% |
| API 端點 | -% | -% | -% | > 80% |
| SEOTitleSelectionCard | -% | -% | -% | > 70% |
| ArticleParsingPage | -% | -% | -% | > 70% |
| **整體** | **-%** | **-%** | **-%** | **> 75%** |

---

## 🐛 缺陷追蹤

### 已發現問題

| Bug ID | 嚴重程度 | 描述 | 狀態 | 負責人 |
|--------|---------|------|------|-------|
| - | - | - | - | - |

### 嚴重程度定義

- **Critical (阻塞)**: 功能完全不可用，影響核心流程
- **High (嚴重)**: 主要功能受影響，有臨時解決方案
- **Medium (一般)**: 功能部分受影響，不影響主流程
- **Low (輕微)**: UI/UX 問題，不影響功能

---

## 📝 測試檢查清單

### 開發階段檢查

- [ ] 所有單元測試編寫完成
- [ ] 單元測試通過率 > 95%
- [ ] 代碼覆蓋率 > 75%
- [ ] 代碼審查完成
- [ ] 無已知的 critical/high bugs

### 測試階段檢查

- [ ] 整合測試完成
- [ ] E2E 測試完成
- [ ] 性能測試完成
- [ ] 安全測試完成
- [ ] 無阻塞性問題

### 部署階段檢查

- [ ] 測試環境驗證通過
- [ ] Smoke tests 通過
- [ ] 性能指標符合要求
- [ ] 回滾方案已準備
- [ ] 監控已配置

### 上線後檢查

- [ ] 生產環境 smoke tests 通過
- [ ] 無錯誤日誌
- [ ] 性能監控正常
- [ ] 用戶反饋收集
- [ ] 24 小時監控無異常

---

## 🔄 回歸測試

### 影響範圍分析

| 功能模塊 | 影響程度 | 需要回歸測試 |
|---------|---------|-------------|
| Article Parsing | 高 | ✅ 是 |
| Unified Optimization | 高 | ✅ 是 |
| WordPress Publishing | 高 | ✅ 是 |
| Frontend UI | 中 | ✅ 是 |
| Database | 高 | ✅ 是 |
| API | 中 | ✅ 是 |

### 回歸測試清單

- [ ] 現有解析功能不受影響（H1 標題提取）
- [ ] 現有優化功能不受影響（SEO Keywords、Meta Description）
- [ ] 現有 WordPress 發佈功能不受影響
- [ ] 歷史數據遷移正確
- [ ] 向後兼容性（未選擇 SEO Title 時使用 fallback）

---

## 📚 測試文檔

### 測試相關文檔

- [需求規格說明](./spec.md)
- [實施計劃](./plan.md)
- [任務清單](./tasks.md)
- [SEO Title Implementation Plan](../../SEO_TITLE_IMPLEMENTATION_PLAN.md)

### 測試工具

- **單元測試**: pytest (後端), Jest (前端)
- **整合測試**: pytest
- **E2E 測試**: Playwright
- **性能測試**: Locust, Lighthouse
- **代碼覆蓋率**: coverage.py, Istanbul
- **安全測試**: OWASP ZAP, Bandit

---

**文檔版本：** v1.0
**最後更新：** 2025-01-14
**審核狀態：** 待審核
