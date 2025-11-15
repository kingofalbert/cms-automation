# SEO Title 提取與建議功能 - 實施計劃

**Feature ID:** 006-seo-title-extraction
**創建日期:** 2025-01-14
**預估工期:** 3 週（14 個工作日）
**團隊成員:** 後端工程師 x1、前端工程師 x1、QA x1

---

## 📋 實施概覽

### 目標

在 3 週內完成 SEO Title 提取與建議功能的完整實施，包括：
- 資料庫架構調整
- 後端 API 實施
- 前端 UI 實施
- WordPress 整合
- 完整測試

### 實施原則

1. **零停機部署**：資料庫遷移使用 nullable 字段，不影響現有功能
2. **向後兼容**：未選擇 SEO Title 時 fallback 到 title_main
3. **測試驅動**：每個階段完成後進行測試驗證
4. **增量發布**：先部署到測試環境，驗證通過後再部署生產環境

---

## 🗓️ 實施階段

### Phase 1: 資料庫架構調整（2 天）

#### 1.1 創建資料庫遷移腳本

**負責人：** 後端工程師
**時間：** 0.5 天

**任務：**
1. 創建 Alembic 遷移檔案：`xxxx_add_seo_title_to_articles.py`
2. 新增 3 個字段到 articles 表：
   - `seo_title` (VARCHAR(200), nullable)
   - `seo_title_extracted` (BOOLEAN, default=false)
   - `seo_title_source` (VARCHAR(50), nullable)
3. 添加歷史數據遷移邏輯（將 title_main 複製為初始 seo_title）

**產出物：**
- `backend/src/alembic/versions/xxxx_add_seo_title_to_articles.py`

**驗收標準：**
- ✅ 遷移腳本可在本地資料庫成功執行
- ✅ 新增字段的資料類型和約束正確
- ✅ 歷史數據遷移邏輯正確（seo_title = title_main, source = 'migrated'）

#### 1.2 更新 title_suggestions 表

**負責人：** 後端工程師
**時間：** 0.5 天

**任務：**
1. 創建 Alembic 遷移檔案：`xxxx_add_seo_suggestions_to_title_suggestions.py`
2. 新增 `suggested_seo_titles` (JSONB, nullable) 字段
3. 更新 `suggested_title_sets` 字段的註釋（明確為 H1 標題）

**產出物：**
- `backend/src/alembic/versions/xxxx_add_seo_suggestions_to_title_suggestions.py`

**驗收標準：**
- ✅ 遷移腳本可成功執行
- ✅ JSONB 字段可儲存複雜結構

#### 1.3 更新 Pydantic/SQLAlchemy 模型

**負責人：** 後端工程師
**時間：** 0.5 天

**任務：**
1. 更新 `Article` 模型（`backend/src/models/article.py`）
   - 新增 `seo_title`, `seo_title_extracted`, `seo_title_source` 字段
   - 更新字段註釋
2. 更新 `TitleSuggestion` 模型（`backend/src/models/title_suggestions.py`）
   - 新增 `suggested_seo_titles` 字段
3. 更新 Pydantic schemas（`backend/src/schemas/article.py`）
   - 新增對應的回應模型

**產出物：**
- 更新後的模型檔案
- 更新後的 schema 檔案

**驗收標準：**
- ✅ 模型與資料庫結構一致
- ✅ 類型提示正確
- ✅ API 文檔自動更新

#### 1.4 在測試環境執行遷移

**負責人：** 後端工程師
**時間：** 0.5 天

**任務：**
1. 備份測試環境資料庫
2. 執行遷移腳本
3. 驗證新增字段
4. 驗證歷史數據遷移
5. 測試回滾腳本

**驗收標準：**
- ✅ 遷移成功完成
- ✅ 歷史文章的 seo_title 已自動填充
- ✅ 回滾腳本可正常執行

---

### Phase 2: 後端 API 實施（4 天）

#### 2.1 更新 ArticleParserService - AI 解析

**負責人：** 後端工程師
**時間：** 1 天

**任務：**
1. 更新 `_build_ai_parsing_prompt()` 方法
   - 增加 SEO Title 提取指示
   - 增加 SEO Title 標記識別說明
2. 更新 `_parse_with_ai()` 方法
   - 解析 Claude 回應中的 `seo_title` 和 `seo_title_found` 字段
   - 設定 `seo_title_extracted` 標記
3. 更新 `ParsedArticle` 模型
   - 新增 `seo_title` 和 `seo_title_extracted` 字段

**產出物：**
- 更新後的 `backend/src/services/parser/article_parser.py`
- 更新後的 `backend/src/services/parser/models.py`

**驗收標準：**
- ✅ AI 可識別「這是 SEO title」標記
- ✅ 提取的 SEO Title 正確儲存
- ✅ 單元測試通過

#### 2.2 更新 ArticleParserService - 啟發式解析

**負責人：** 後端工程師
**時間：** 0.5 天

**任務：**
1. 更新 `_parse_with_heuristics()` 方法
2. 新增正則表達式模式：
   ```python
   seo_title_patterns = [
       r'(?:這是\s*)?SEO\s*[Tt]itle[：:]\s*(.+?)(?:\n|$|<)',
       r'SEO\s*標題[：:]\s*(.+?)(?:\n|$|<)',
       r'<title[^>]*>(.+?)</title>',
   ]
   ```
3. 設定 `seo_title_extracted` 標記

**產出物：**
- 更新後的啟發式解析邏輯

**驗收標準：**
- ✅ 正則表達式可匹配多種標記模式
- ✅ 提取準確率 > 95%
- ✅ 單元測試通過

#### 2.3 更新 UnifiedOptimizationService

**負責人：** 後端工程師
**時間：** 1.5 天

**任務：**
1. 更新 `_build_unified_optimization_prompt()` 方法
   - 增加 SEO Title 建議生成指示
   - 明確 SEO Title 與 H1 的區別
   - 要求生成 2-3 個選項
2. 更新 `_parse_optimization_response()` 方法
   - 解析 `seo_title_suggestions` 字段
3. 更新 `_save_optimizations()` 方法
   - 儲存 SEO Title 建議到 `title_suggestions.suggested_seo_titles`

**產出物：**
- 更新後的 `backend/src/services/optimization/unified_optimization_service.py`

**驗收標準：**
- ✅ Claude API 回應包含 SEO Title 建議
- ✅ 生成 2-3 個不同風格的選項
- ✅ 每個選項包含 reasoning、keywords_focus、character_count
- ✅ SEO Title 與 H1 有差異化
- ✅ 單元測試通過

#### 2.4 新增 SEO Title 選擇 API 端點

**負責人：** 後端工程師
**時間：** 1 天

**任務：**
1. 創建 `POST /api/v1/articles/{id}/select-seo-title` 端點
2. 實現選擇邏輯：
   - 選擇 AI 建議（variant_id）
   - 使用原文提取（use_original）
   - 自定義輸入（custom_seo_title）
3. 實現驗證：
   - variant_id 存在性檢查
   - 原文提取前提檢查（seo_title_extracted = true）
   - 自定義長度檢查（max 60 characters）
4. 更新 articles 表：
   - `seo_title`
   - `seo_title_source`

**產出物：**
- 新增的 API 端點
- Pydantic request/response models

**驗收標準：**
- ✅ API 端點可正確處理三種選擇模式
- ✅ 驗證邏輯正確
- ✅ 錯誤處理完善
- ✅ API 文檔自動生成
- ✅ 整合測試通過

---

### Phase 3: 前端實施（3 天）

#### 3.1 更新前端類型定義

**負責人：** 前端工程師
**時間：** 0.5 天

**任務：**
1. 更新 `frontend/src/services/parsing.ts` 的介面定義
   - `ParsedArticleData` 新增 SEO Title 字段
   - 新增 `SEOTitleSuggestionsData` 介面
   - 新增 `SEOTitleVariant` 介面
   - 新增 `SEOTitleSelectionRequest` 介面
2. 更新 `OptimizationsResponse` 介面

**產出物：**
- 更新後的類型定義檔案

**驗收標準：**
- ✅ 類型定義與後端 API 一致
- ✅ TypeScript 編譯無錯誤

#### 3.2 創建 SEOTitleSelectionCard 元件

**負責人：** 前端工程師
**時間：** 1.5 天

**任務：**
1. 創建 `frontend/src/components/parsing/SEOTitleSelectionCard.tsx`
2. 實現功能：
   - 顯示原文提取的 SEO Title（如果有）
   - 顯示 AI 建議的 2-3 個選項
   - 每個選項顯示推理說明、關鍵字焦點、字數
   - 支援選擇 AI 建議
   - 支援使用原文提取
   - 支援自定義輸入
   - 即時字數統計
   - 顯示 SEO Title vs H1 vs Meta Description 說明
3. 實現樣式：
   - 使用 Tailwind CSS
   - 響應式設計
   - 選中狀態視覺反饋

**產出物：**
- `SEOTitleSelectionCard.tsx` 元件

**驗收標準：**
- ✅ 元件可正確顯示所有內容
- ✅ 互動功能正常
- ✅ 樣式美觀
- ✅ 響應式佈局
- ✅ 無 TypeScript 錯誤

#### 3.3 整合到 ArticleParsingPage

**負責人：** 前端工程師
**時間：** 1 天

**任務：**
1. 更新 `frontend/src/pages/ArticleParsingPage.tsx`
2. 新增狀態管理：
   - `selectedSEOTitleId`
   - `currentSEOTitle`
3. 新增 API 調用：
   - `selectSEOTitle` mutation
4. 整合 SEOTitleSelectionCard 元件
5. 更新顯示邏輯：
   - 在優化建議生成後顯示
   - 位於 TitleOptimizationCard 之後
6. 更新標題卡片：
   - 清楚區分 H1 和 SEO Title
   - 使用不同的視覺標籤

**產出物：**
- 更新後的 `ArticleParsingPage.tsx`

**驗收標準：**
- ✅ SEO Title 選擇流程完整
- ✅ 選擇後立即更新顯示
- ✅ 錯誤處理正確
- ✅ 載入狀態顯示
- ✅ 成功提示顯示

---

### Phase 4: WordPress 發佈整合（1 天）

#### 4.1 更新 WordPress 發佈邏輯

**負責人：** 後端工程師
**時間：** 1 天

**任務：**
1. 更新 `backend/src/services/article_importer/wordpress_importer.py`
2. 更新 `_prepare_post_data()` 方法：
   - 使用 `article.seo_title or article.title_main` 作為 SEO Title
   - 使用 `article.title` 作為 H1 標題
   - 設定 Yoast SEO meta 字段
   - 設定 Rank Math meta 字段（備選）
3. 添加驗證邏輯：
   - 確保 SEO Title 和 H1 正確設定
   - 記錄發佈日誌

**產出物：**
- 更新後的 WordPress 發佈邏輯

**驗收標準：**
- ✅ WordPress 文章標題使用 H1
- ✅ Yoast SEO title 使用 seo_title
- ✅ 發佈後驗證 HTML 中的 `<title>` 標籤
- ✅ 整合測試通過

---

### Phase 5: 測試（3 天）

#### 5.1 單元測試

**負責人：** 後端工程師、前端工程師
**時間：** 1 天

**任務：**
1. **後端單元測試**
   - 測試 SEO Title 提取邏輯（AI 和啟發式）
   - 測試 AI 建議生成邏輯
   - 測試 SEO Title 選擇 API
   - 測試 WordPress 發佈邏輯
2. **前端單元測試**
   - 測試 SEOTitleSelectionCard 元件
   - 測試選擇邏輯
   - 測試表單驗證

**產出物：**
- `backend/tests/services/test_article_parser_seo_title.py`
- `backend/tests/services/test_optimization_seo_title.py`
- `backend/tests/api/test_seo_title_selection.py`
- `frontend/src/components/parsing/__tests__/SEOTitleSelectionCard.test.tsx`

**驗收標準：**
- ✅ 後端測試覆蓋率 > 80%
- ✅ 前端測試覆蓋率 > 70%
- ✅ 所有測試通過

#### 5.2 整合測試

**負責人：** QA
**時間：** 1 天

**任務：**
1. 測試完整工作流程：
   - 上傳包含 SEO Title 標記的文章
   - 驗證解析結果
   - 確認解析並生成優化建議
   - 選擇 SEO Title（三種模式）
   - 發佈到 WordPress
2. 創建測試腳本：
   - `backend/tests/integration/test_seo_title_workflow.py`

**產出物：**
- 整合測試腳本
- 測試報告

**驗收標準：**
- ✅ 完整流程可正常執行
- ✅ 所有場景測試通過
- ✅ 性能指標符合要求

#### 5.3 E2E 測試

**負責人：** QA
**時間：** 1 天

**任務：**
1. 使用 Playwright 創建 E2E 測試
2. 測試場景：
   - 場景 1：顯示原文提取的 SEO Title
   - 場景 2：選擇 AI 建議
   - 場景 3：自定義 SEO Title
   - 場景 4：驗證 WordPress 發佈
3. 創建測試檔案：
   - `frontend/e2e/seo-title-selection.spec.ts`

**產出物：**
- E2E 測試腳本
- 測試錄影

**驗收標準：**
- ✅ E2E 測試可自動執行
- ✅ 所有場景測試通過
- ✅ 無 UI/UX 問題

---

### Phase 6: 文檔與部署（1 天）

#### 6.1 更新 API 文檔

**負責人：** 後端工程師
**時間：** 0.25 天

**任務：**
1. 更新 OpenAPI/Swagger 文檔
2. 添加 SEO Title 選擇端點說明
3. 添加請求/回應範例
4. 更新現有端點的回應範例

**產出物：**
- 更新後的 API 文檔

**驗收標準：**
- ✅ 文檔完整準確
- ✅ 範例可正常使用

#### 6.2 創建用戶指南

**負責人：** 前端工程師
**時間：** 0.25 天

**任務：**
1. 創建 SEO Title 使用指南
2. 說明 SEO Title vs H1 vs Meta Description
3. 提供最佳實踐建議
4. 添加截圖和範例

**產出物：**
- `docs/user-guide/seo-title-guide.md`

**驗收標準：**
- ✅ 指南清晰易懂
- ✅ 包含實用範例

#### 6.3 部署到測試環境

**負責人：** DevOps
**時間：** 0.25 天

**任務：**
1. 備份生產資料庫
2. 在測試環境執行資料庫遷移
3. 部署後端代碼
4. 部署前端代碼
5. 驗證部署成功
6. 執行 smoke tests

**產出物：**
- 部署檢查清單
- 測試環境驗證報告

**驗收標準：**
- ✅ 遷移成功執行
- ✅ 應用程式正常運行
- ✅ 功能驗證通過

#### 6.4 部署到生產環境

**負責人：** DevOps
**時間：** 0.25 天

**任務：**
1. 備份生產資料庫
2. 執行資料庫遷移
3. 部署後端代碼
4. 部署前端代碼
5. 驗證部署成功
6. 監控錯誤日誌
7. 準備回滾方案

**產出物：**
- 生產部署報告
- 監控儀表板

**驗收標準：**
- ✅ 零停機部署
- ✅ 無錯誤日誌
- ✅ 性能指標正常

---

## 📅 時間表

| 週次 | 階段 | 任務 | 負責人 | 狀態 |
|------|------|------|-------|------|
| **Week 1** | Phase 1 | 資料庫架構調整 | 後端 | ⏳ Pending |
|  | Phase 2.1-2.2 | 解析器更新 | 後端 | ⏳ Pending |
| **Week 2** | Phase 2.3-2.4 | 優化服務與 API | 後端 | ⏳ Pending |
|  | Phase 3.1-3.2 | 前端類型與元件 | 前端 | ⏳ Pending |
| **Week 3** | Phase 3.3 | 前端整合 | 前端 | ⏳ Pending |
|  | Phase 4 | WordPress 整合 | 後端 | ⏳ Pending |
|  | Phase 5 | 測試 | QA | ⏳ Pending |
|  | Phase 6 | 文檔與部署 | 全員 | ⏳ Pending |

### 里程碑

| 里程碑 | 日期 | 可交付成果 |
|--------|------|-----------|
| **M1: 資料庫完成** | Day 2 | 資料庫遷移完成，模型更新 |
| **M2: 後端完成** | Day 6 | 所有 API 端點可用，單元測試通過 |
| **M3: 前端完成** | Day 9 | UI 元件完成，整合完成 |
| **M4: WordPress 整合** | Day 10 | 發佈流程驗證通過 |
| **M5: 測試完成** | Day 13 | 所有測試通過，測試報告完成 |
| **M6: 生產部署** | Day 14 | 功能在生產環境可用 |

---

## 🚧 風險與緩解

### 風險識別

| 風險 | 機率 | 影響 | 緩解策略 |
|------|------|------|---------|
| **Claude API 回應格式變更** | 低 | 高 | 使用版本鎖定（claude-sonnet-4-5），添加嚴格的 JSON 驗證 |
| **資料庫遷移失敗** | 中 | 高 | 在測試環境充分測試，準備回滾腳本，使用事務 |
| **前端整合複雜度** | 中 | 中 | 提前創建原型，與後端緊密協作 |
| **WordPress 外掛不兼容** | 低 | 中 | 同時支援 Yoast SEO 和 Rank Math，添加 fallback |
| **性能問題** | 低 | 中 | 添加緩存，優化資料庫查詢，監控 API 回應時間 |
| **用戶理解困難** | 中 | 低 | 提供清晰的 UI 說明，創建用戶指南 |

### 關鍵依賴

1. **外部依賴**
   - Anthropic Claude API 可用性（99.9% SLA）
   - WordPress REST API 穩定性

2. **內部依賴**
   - Phase 7 Article Parsing 功能正常
   - Phase 7 Unified Optimization Service 穩定

3. **團隊依賴**
   - 後端工程師可用性（全職 2 週）
   - 前端工程師可用性（全職 1.5 週）
   - QA 可用性（1 週）

---

## 📊 成功指標

### 開發指標

| 指標 | 目標 | 測量 |
|------|------|------|
| 按時交付 | 100% | 14 天內完成所有功能 |
| 測試覆蓋率 | > 75% | 後端 80%、前端 70% |
| 程式碼審查 | 100% | 所有 PR 必須經過審查 |
| 技術債務 | 0 | 無已知的技術債務 |

### 功能指標

| 指標 | 目標 | 測量 |
|------|------|------|
| SEO Title 提取準確率 | > 95% | 測試集驗證 |
| AI 建議生成成功率 | > 98% | API 成功率 |
| API 回應時間 | < 500ms | P95 回應時間 |
| 前端頁面載入 | < 2s | Lighthouse 分數 |

---

## 📝 檢查清單

### 開發前檢查

- [ ] 需求文檔已審核通過
- [ ] 技術方案已評審
- [ ] 資料庫設計已確認
- [ ] API 設計已確認
- [ ] 測試環境已準備
- [ ] 開發環境已設置

### 開發中檢查

- [ ] 每個 PR 都有對應的 issue
- [ ] 代碼遵循編碼規範
- [ ] 單元測試已編寫
- [ ] 代碼審查已完成
- [ ] 技術文檔已更新

### 部署前檢查

- [ ] 所有測試通過（單元、整合、E2E）
- [ ] 性能測試通過
- [ ] 安全測試通過
- [ ] 資料庫遷移已在測試環境驗證
- [ ] 回滾方案已準備
- [ ] 監控已配置
- [ ] 文檔已更新

### 部署後檢查

- [ ] 健康檢查通過
- [ ] 功能驗證通過
- [ ] 性能監控正常
- [ ] 錯誤日誌無異常
- [ ] 用戶反饋收集
- [ ] 知識轉移完成

---

## 🔄 迭代計劃

### 第一次迭代（本次）

**範圍：** 核心功能實現
- ✅ SEO Title 提取
- ✅ AI 建議生成
- ✅ 用戶選擇
- ✅ WordPress 發佈

### 第二次迭代（未來）

**範圍：** 優化與擴展
- 📅 多語言支援
- 📅 A/B 測試框架
- 📅 批次更新工具
- 📅 SEO 效果追蹤

### 第三次迭代（未來）

**範圍：** 智能化
- 📅 基於歷史數據的智能推薦
- 📅 自動化 SEO Title 優化
- 📅 與 Google Search Console 整合

---

## 📚 參考資料

- [需求規格說明](./spec.md)
- [任務清單](./tasks.md)
- [測試計劃](./checklist.md)
- [SEO Title Implementation Plan](../../SEO_TITLE_IMPLEMENTATION_PLAN.md)

---

**文檔版本：** v1.0
**最後更新：** 2025-01-14
**審核狀態：** 待審核
