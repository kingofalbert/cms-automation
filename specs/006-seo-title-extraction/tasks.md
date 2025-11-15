# SEO Title 提取與建議功能 - 任務清單

**Feature ID:** 006-seo-title-extraction
**創建日期:** 2025-01-14
**總預估時間:** 14 天

---

## 任務概覽

本文檔列出 SEO Title 功能實施的所有具體任務，包括負責人、預估時間、優先級和依賴關係。

**圖例：**
- ⏳ 待開始
- 🔄 進行中
- ✅ 已完成
- ❌ 已取消
- ⚠️ 受阻

---

## Phase 1: 資料庫架構調整（2 天）

### Task 1.1: 創建 articles 表遷移腳本

**ID:** SEO-001
**負責人:** 後端工程師
**預估時間:** 4 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** 無

**描述:**
創建 Alembic 遷移腳本，新增 SEO Title 相關字段到 articles 表。

**子任務:**
1. [ ] 創建遷移檔案 `backend/src/alembic/versions/xxxx_add_seo_title_to_articles.py`
2. [ ] 新增 `seo_title` 字段 (VARCHAR(200), nullable)
3. [ ] 新增 `seo_title_extracted` 字段 (BOOLEAN, default=false)
4. [ ] 新增 `seo_title_source` 字段 (VARCHAR(50), nullable)
5. [ ] 添加歷史數據遷移邏輯（title_main → seo_title）
6. [ ] 編寫 downgrade() 回滾函數
7. [ ] 在本地測試遷移（upgrade 和 downgrade）

**驗收標準:**
- ✅ 遷移腳本可成功執行
- ✅ 新增字段的資料類型和約束正確
- ✅ 歷史數據遷移邏輯正確（seo_title_source = 'migrated'）
- ✅ 回滾腳本可正常執行

**產出物:**
- `backend/src/alembic/versions/xxxx_add_seo_title_to_articles.py`

---

### Task 1.2: 創建 title_suggestions 表遷移腳本

**ID:** SEO-002
**負責人:** 後端工程師
**預估時間:** 3 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** 無

**描述:**
創建 Alembic 遷移腳本，新增 SEO Title 建議字段到 title_suggestions 表。

**子任務:**
1. [ ] 創建遷移檔案 `backend/src/alembic/versions/xxxx_add_seo_suggestions_to_title_suggestions.py`
2. [ ] 新增 `suggested_seo_titles` 字段 (JSONB, nullable)
3. [ ] 更新 `suggested_title_sets` 字段註釋（明確為 H1 標題）
4. [ ] 編寫 downgrade() 回滾函數
5. [ ] 在本地測試遷移

**驗收標準:**
- ✅ 遷移腳本可成功執行
- ✅ JSONB 字段可儲存複雜結構
- ✅ 註釋清晰準確

**產出物:**
- `backend/src/alembic/versions/xxxx_add_seo_suggestions_to_title_suggestions.py`

---

### Task 1.3: 更新 Article 模型

**ID:** SEO-003
**負責人:** 後端工程師
**預估時間:** 2 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-001

**描述:**
更新 SQLAlchemy Article 模型，新增 SEO Title 字段。

**子任務:**
1. [ ] 更新 `backend/src/models/article.py`
2. [ ] 新增 `seo_title: Mapped[str | None]` 字段
3. [ ] 新增 `seo_title_extracted: Mapped[bool]` 字段
4. [ ] 新增 `seo_title_source: Mapped[str | None]` 字段
5. [ ] 添加字段註釋（docstring）
6. [ ] 更新 `title_main` 字段註釋（明確為 H1 標題）

**驗收標準:**
- ✅ 模型字段與資料庫結構一致
- ✅ 類型提示正確
- ✅ 註釋清晰

**產出物:**
- 更新後的 `backend/src/models/article.py`

---

### Task 1.4: 更新 TitleSuggestion 模型

**ID:** SEO-004
**負責人:** 後端工程師
**預估時間:** 1 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-002

**描述:**
更新 TitleSuggestion 模型，新增 SEO Title 建議字段。

**子任務:**
1. [ ] 更新 `backend/src/models/title_suggestions.py`
2. [ ] 新增 `suggested_seo_titles: Mapped[dict | None]` 字段
3. [ ] 更新 `suggested_title_sets` 字段註釋
4. [ ] 添加字段註釋

**驗收標準:**
- ✅ 模型字段與資料庫結構一致
- ✅ JSONB 類型映射正確

**產出物:**
- 更新後的 `backend/src/models/title_suggestions.py`

---

### Task 1.5: 更新 Pydantic Schemas

**ID:** SEO-005
**負責人:** 後端工程師
**預估時間:** 2 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-003, SEO-004

**描述:**
更新 Pydantic schemas 以支援 SEO Title 字段。

**子任務:**
1. [ ] 更新 `backend/src/schemas/article.py`
2. [ ] 新增 `ParsedArticleResponse` 的 SEO Title 字段
3. [ ] 新增 `SEOTitleSuggestionsData` schema
4. [ ] 新增 `SEOTitleVariant` schema
5. [ ] 新增 `SEOTitleSelectionRequest` schema
6. [ ] 更新 `OptimizationsResponse` schema

**驗收標準:**
- ✅ Schema 定義完整
- ✅ 類型驗證正確
- ✅ API 文檔自動生成

**產出物:**
- 更新後的 `backend/src/schemas/article.py`

---

### Task 1.6: 在測試環境執行遷移

**ID:** SEO-006
**負責人:** 後端工程師
**預估時間:** 2 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-001, SEO-002

**描述:**
在測試環境執行資料庫遷移並驗證。

**子任務:**
1. [ ] 備份測試環境資料庫
2. [ ] 執行 `alembic upgrade head`
3. [ ] 驗證新增字段存在
4. [ ] 驗證歷史數據遷移（檢查 seo_title 已填充）
5. [ ] 測試回滾 `alembic downgrade -1`
6. [ ] 重新執行 upgrade
7. [ ] 記錄遷移時間和結果

**驗收標準:**
- ✅ 遷移成功完成
- ✅ 歷史文章的 seo_title 已自動填充
- ✅ 回滾腳本可正常執行
- ✅ 無資料遺失

**產出物:**
- 遷移驗證報告

---

## Phase 2: 後端 API 實施（4 天）

### Task 2.1: 更新 ParsedArticle 模型

**ID:** SEO-007
**負責人:** 後端工程師
**預估時間:** 1 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-003

**描述:**
更新 ParsedArticle 數據類，新增 SEO Title 字段。

**子任務:**
1. [ ] 更新 `backend/src/services/parser/models.py`
2. [ ] 新增 `seo_title: str | None` 字段
3. [ ] 新增 `seo_title_extracted: bool` 字段
4. [ ] 更新字段註釋

**驗收標準:**
- ✅ 數據類定義正確
- ✅ 默認值合理

**產出物:**
- 更新後的 `backend/src/services/parser/models.py`

---

### Task 2.2: 更新 AI 解析提示詞

**ID:** SEO-008
**負責人:** 後端工程師
**預估時間:** 3 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-007

**描述:**
更新 Claude API 提示詞，增加 SEO Title 提取指示。

**子任務:**
1. [ ] 更新 `backend/src/services/parser/article_parser.py` 中的 `_build_ai_parsing_prompt()`
2. [ ] 增加 SEO Title 提取指示
3. [ ] 增加 SEO Title 標記識別說明（「這是 SEO title」、「SEO標題：」等）
4. [ ] 更新 JSON 輸出格式說明（包含 seo_title 和 seo_title_found 字段）
5. [ ] 添加 SEO Title 長度建議（30 字以內）
6. [ ] 測試提示詞（使用測試 HTML）

**驗收標準:**
- ✅ 提示詞清晰明確
- ✅ Claude 可正確識別 SEO Title 標記
- ✅ 輸出格式符合預期

**產出物:**
- 更新後的 `_build_ai_parsing_prompt()` 方法

---

### Task 2.3: 更新 AI 解析邏輯

**ID:** SEO-009
**負責人:** 後端工程師
**預估時間:** 3 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-008

**描述:**
更新 AI 解析邏輯，處理 SEO Title 提取。

**子任務:**
1. [ ] 更新 `_parse_with_ai()` 方法
2. [ ] 解析 Claude 回應中的 `seo_title` 字段
3. [ ] 解析 `seo_title_found` 字段
4. [ ] 設定 `ParsedArticle.seo_title_extracted` 標記
5. [ ] 添加錯誤處理（SEO title 格式錯誤）
6. [ ] 添加日誌記錄

**驗收標準:**
- ✅ AI 解析邏輯正確
- ✅ SEO Title 提取成功
- ✅ 錯誤處理完善

**產出物:**
- 更新後的 `_parse_with_ai()` 方法

---

### Task 2.4: 更新啟發式解析邏輯

**ID:** SEO-010
**負責人:** 後端工程師
**預估時間:** 2 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-007

**描述:**
更新啟發式解析邏輯，使用正則表達式提取 SEO Title。

**子任務:**
1. [ ] 更新 `_parse_with_heuristics()` 方法
2. [ ] 定義 SEO Title 正則表達式模式：
   - `(?:這是\s*)?SEO\s*[Tt]itle[：:]\s*(.+?)(?:\n|$|<)`
   - `SEO\s*標題[：:]\s*(.+?)(?:\n|$|<)`
   - `<title[^>]*>(.+?)</title>`
3. [ ] 實現匹配邏輯（按優先順序嘗試）
4. [ ] 設定 `seo_title_extracted` 標記
5. [ ] 添加日誌記錄

**驗收標準:**
- ✅ 正則表達式可匹配多種標記模式
- ✅ 提取準確率 > 95%
- ✅ 無 false positives

**產出物:**
- 更新後的 `_parse_with_heuristics()` 方法

---

### Task 2.5: 編寫解析器單元測試

**ID:** SEO-011
**負責人:** 後端工程師
**預估時間:** 3 小時
**優先級:** P1
**狀態:** ⏳ 待開始
**依賴:** SEO-009, SEO-010

**描述:**
編寫 ArticleParserService 的單元測試，測試 SEO Title 提取。

**子任務:**
1. [ ] 創建 `backend/tests/services/test_article_parser_seo_title.py`
2. [ ] 測試 AI 解析提取 SEO Title
3. [ ] 測試啟發式解析提取 SEO Title
4. [ ] 測試無 SEO Title 標記的情況
5. [ ] 測試多種標記格式
6. [ ] 測試邊界情況（空字符串、超長標題等）
7. [ ] Mock Claude API 回應

**驗收標準:**
- ✅ 測試覆蓋率 > 80%
- ✅ 所有測試通過
- ✅ 測試案例全面

**產出物:**
- `backend/tests/services/test_article_parser_seo_title.py`

---

### Task 2.6: 更新統一優化提示詞

**ID:** SEO-012
**負責人:** 後端工程師
**預估時間:** 4 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-004

**描述:**
更新 UnifiedOptimizationService 的 Claude 提示詞，增加 SEO Title 建議生成。

**子任務:**
1. [ ] 更新 `backend/src/services/optimization/unified_optimization_service.py`
2. [ ] 更新 `_build_unified_optimization_prompt()` 方法
3. [ ] 增加 SEO Title 建議生成指示
4. [ ] 明確 SEO Title 與 H1 的區別
5. [ ] 要求生成 2-3 個選項
6. [ ] 添加 SEO Title 格式說明（JSON schema）
7. [ ] 添加優化建議說明
8. [ ] 測試提示詞

**驗收標準:**
- ✅ 提示詞清晰明確
- ✅ Claude 可生成 2-3 個 SEO Title 選項
- ✅ 輸出格式符合預期

**產出物:**
- 更新後的 `_build_unified_optimization_prompt()` 方法

---

### Task 2.7: 更新優化結果解析邏輯

**ID:** SEO-013
**負責人:** 後端工程師
**預估時間:** 2 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-012

**描述:**
更新優化結果解析邏輯，處理 SEO Title 建議。

**子任務:**
1. [ ] 更新 `_parse_optimization_response()` 方法
2. [ ] 解析 `seo_title_suggestions` 字段
3. [ ] 驗證 JSON 結構（variants 數組、notes 等）
4. [ ] 添加錯誤處理
5. [ ] 添加日誌記錄

**驗收標準:**
- ✅ 解析邏輯正確
- ✅ 錯誤處理完善
- ✅ 日誌記錄完整

**產出物:**
- 更新後的 `_parse_optimization_response()` 方法

---

### Task 2.8: 更新優化結果儲存邏輯

**ID:** SEO-014
**負責人:** 後端工程師
**預估時間:** 2 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-013

**描述:**
更新優化結果儲存邏輯，將 SEO Title 建議儲存到資料庫。

**子任務:**
1. [ ] 更新 `_save_optimizations()` 方法
2. [ ] 儲存 `seo_title_suggestions` 到 `title_suggestions.suggested_seo_titles`
3. [ ] 驗證儲存成功
4. [ ] 添加事務處理
5. [ ] 添加日誌記錄

**驗收標準:**
- ✅ 儲存邏輯正確
- ✅ 資料完整性保證
- ✅ 事務處理正確

**產出物:**
- 更新後的 `_save_optimizations()` 方法

---

### Task 2.9: 編寫優化服務單元測試

**ID:** SEO-015
**負責人:** 後端工程師
**預估時間:** 3 小時
**優先級:** P1
**狀態:** ⏳ 待開始
**依賴:** SEO-014

**描述:**
編寫 UnifiedOptimizationService 的單元測試，測試 SEO Title 建議生成。

**子任務:**
1. [ ] 創建 `backend/tests/services/test_optimization_seo_title.py`
2. [ ] 測試 SEO Title 建議生成
3. [ ] 測試建議數量（2-3 個）
4. [ ] 測試建議結構（id, seo_title, reasoning, keywords_focus, character_count）
5. [ ] 測試 SEO Title 與 H1 的差異化
6. [ ] 測試字數限制
7. [ ] Mock Claude API 回應

**驗收標準:**
- ✅ 測試覆蓋率 > 80%
- ✅ 所有測試通過
- ✅ 測試案例全面

**產出物:**
- `backend/tests/services/test_optimization_seo_title.py`

---

### Task 2.10: 創建 SEO Title 選擇 API 端點

**ID:** SEO-016
**負責人:** 後端工程師
**預估時間:** 4 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-005

**描述:**
創建 POST /articles/{id}/select-seo-title API 端點。

**子任務:**
1. [ ] 創建 `backend/src/api/v1/endpoints/parsing.py` 中的新端點
2. [ ] 定義請求模型 `SEOTitleSelectionRequest`
3. [ ] 定義回應模型 `SuccessResponse`
4. [ ] 實現選擇邏輯：
   - 選擇 AI 建議（variant_id）
   - 使用原文提取（use_original）
   - 自定義輸入（custom_seo_title）
5. [ ] 實現驗證：
   - variant_id 存在性檢查
   - 原文提取前提檢查
   - 自定義長度檢查
6. [ ] 更新資料庫（seo_title, seo_title_source）
7. [ ] 添加錯誤處理
8. [ ] 添加日誌記錄

**驗收標準:**
- ✅ API 端點可正常工作
- ✅ 三種選擇模式都可正常使用
- ✅ 驗證邏輯正確
- ✅ 錯誤處理完善

**產出物:**
- 新增的 API 端點

---

### Task 2.11: 編寫 API 端點測試

**ID:** SEO-017
**負責人:** 後端工程師
**預估時間:** 3 小時
**優先級:** P1
**狀態:** ⏳ 待開始
**依賴:** SEO-016

**描述:**
編寫 SEO Title 選擇 API 的測試。

**子任務:**
1. [ ] 創建 `backend/tests/api/test_seo_title_selection.py`
2. [ ] 測試選擇 AI 建議
3. [ ] 測試使用原文提取
4. [ ] 測試自定義輸入
5. [ ] 測試驗證錯誤（無效 variant_id、無原文提取、超長自定義等）
6. [ ] 測試權限檢查
7. [ ] 測試資料庫更新

**驗收標準:**
- ✅ 測試覆蓋率 > 80%
- ✅ 所有測試通過
- ✅ 測試案例全面

**產出物:**
- `backend/tests/api/test_seo_title_selection.py`

---

## Phase 3: 前端實施（3 天）

### Task 3.1: 更新前端類型定義

**ID:** SEO-018
**負責人:** 前端工程師
**預估時間:** 2 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-005

**描述:**
更新前端 TypeScript 類型定義，支援 SEO Title。

**子任務:**
1. [ ] 更新 `frontend/src/services/parsing.ts`
2. [ ] 更新 `ParsedArticleData` 介面（新增 SEO Title 字段）
3. [ ] 創建 `SEOTitleSuggestionsData` 介面
4. [ ] 創建 `SEOTitleVariant` 介面
5. [ ] 創建 `SEOTitleSelectionRequest` 介面
6. [ ] 更新 `OptimizationsResponse` 介面
7. [ ] 確保類型定義與後端一致

**驗收標準:**
- ✅ 類型定義完整
- ✅ TypeScript 編譯無錯誤
- ✅ 與後端 API 一致

**產出物:**
- 更新後的 `frontend/src/services/parsing.ts`

---

### Task 3.2: 更新 API 服務

**ID:** SEO-019
**負責人:** 前端工程師
**預估時間:** 1 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-018

**描述:**
新增 selectSEOTitle API 調用方法。

**子任務:**
1. [ ] 更新 `frontend/src/services/parsing.ts`
2. [ ] 新增 `selectSEOTitle()` 方法
3. [ ] 定義請求和回應類型
4. [ ] 添加錯誤處理

**驗收標準:**
- ✅ API 方法可正常調用
- ✅ 類型安全
- ✅ 錯誤處理完善

**產出物:**
- 更新後的 `parsingAPI` 服務

---

### Task 3.3: 創建 SEOTitleSelectionCard 元件

**ID:** SEO-020
**負責人:** 前端工程師
**預估時間:** 6 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-019

**描述:**
創建 SEO Title 選擇元件。

**子任務:**
1. [ ] 創建 `frontend/src/components/parsing/SEOTitleSelectionCard.tsx`
2. [ ] 定義元件 Props 介面
3. [ ] 實現原文提取區塊（如果有）
4. [ ] 實現 AI 建議選項列表
5. [ ] 實現自定義輸入區塊
6. [ ] 實現即時字數統計
7. [ ] 實現選擇狀態管理
8. [ ] 實現 SEO Title vs H1 vs Meta Description 說明區塊
9. [ ] 實現 AI 優化建議顯示
10. [ ] 添加樣式（Tailwind CSS）
11. [ ] 添加響應式設計
12. [ ] 添加載入狀態

**驗收標準:**
- ✅ 元件可正確渲染
- ✅ 所有互動功能正常
- ✅ 樣式美觀專業
- ✅ 響應式佈局
- ✅ 無 TypeScript 錯誤

**產出物:**
- `frontend/src/components/parsing/SEOTitleSelectionCard.tsx`

---

### Task 3.4: 編寫元件單元測試

**ID:** SEO-021
**負責人:** 前端工程師
**預估時間:** 3 小時
**優先級:** P1
**狀態:** ⏳ 待開始
**依賴:** SEO-020

**描述:**
編寫 SEOTitleSelectionCard 元件的單元測試。

**子任務:**
1. [ ] 創建 `frontend/src/components/parsing/__tests__/SEOTitleSelectionCard.test.tsx`
2. [ ] 測試元件渲染
3. [ ] 測試原文提取顯示
4. [ ] 測試 AI 建議顯示
5. [ ] 測試選擇互動
6. [ ] 測試自定義輸入
7. [ ] 測試字數統計
8. [ ] 測試回調函數調用

**驗收標準:**
- ✅ 測試覆蓋率 > 70%
- ✅ 所有測試通過
- ✅ 測試案例全面

**產出物:**
- `frontend/src/components/parsing/__tests__/SEOTitleSelectionCard.test.tsx`

---

### Task 3.5: 整合到 ArticleParsingPage

**ID:** SEO-022
**負責人:** 前端工程師
**預估時間:** 4 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-020

**描述:**
將 SEOTitleSelectionCard 整合到文章解析頁面。

**子任務:**
1. [ ] 更新 `frontend/src/pages/ArticleParsingPage.tsx`
2. [ ] 匯入 SEOTitleSelectionCard 元件
3. [ ] 新增狀態管理：
   - `selectedSEOTitleId`
   - `currentSEOTitle`
4. [ ] 新增 API 調用：
   - `selectSEOTitleMutation`
5. [ ] 實現回調函數：
   - `handleSelectSEOTitleVariant`
   - `handleUseOriginalSEOTitle`
   - `handleCustomSEOTitle`
6. [ ] 整合元件到頁面（在優化建議生成後顯示）
7. [ ] 更新標題卡片（區分 H1 和 SEO Title）
8. [ ] 添加成功/錯誤提示
9. [ ] 測試整合流程

**驗收標準:**
- ✅ 元件正確整合
- ✅ 選擇流程完整
- ✅ 狀態管理正確
- ✅ 錯誤處理完善
- ✅ 用戶體驗良好

**產出物:**
- 更新後的 `frontend/src/pages/ArticleParsingPage.tsx`

---

### Task 3.6: 更新標題顯示元件

**ID:** SEO-023
**負責人:** 前端工程師
**預估時間:** 2 小時
**優先級:** P1
**狀態:** ⏳ 待開始
**依賴:** SEO-022

**描述:**
更新標題顯示元件，清楚區分 H1 和 SEO Title。

**子任務:**
1. [ ] 更新標題卡片佈局
2. [ ] H1 標題顯示區塊：
   - 標註「H1 標題（頁面顯示）」
   - 使用「頁面內容」標籤
3. [ ] SEO Title 顯示區塊（如果有原文提取）：
   - 標註「SEO Title（搜尋引擎）」
   - 使用「原文提取」標籤
   - 使用不同顏色區分
4. [ ] 添加說明文字
5. [ ] 測試視覺效果

**驗收標準:**
- ✅ H1 和 SEO Title 清楚區分
- ✅ 視覺設計清晰
- ✅ 說明文字易懂

**產出物:**
- 更新後的標題顯示元件

---

## Phase 4: WordPress 發佈整合（1 天）

### Task 4.1: 更新 WordPress 發佈邏輯

**ID:** SEO-024
**負責人:** 後端工程師
**預估時間:** 4 小時
**優先級:** P1
**狀態:** ⏳ 待開始
**依賴:** SEO-003

**描述:**
更新 WordPress 發佈邏輯，正確設定 SEO Title 和 H1 標題。

**子任務:**
1. [ ] 更新 `backend/src/services/article_importer/wordpress_importer.py`
2. [ ] 更新 `_prepare_post_data()` 方法
3. [ ] 使用 `article.seo_title or article.title_main` 作為 SEO Title
4. [ ] 使用 `article.title` 作為 WordPress 文章標題（H1）
5. [ ] 設定 Yoast SEO meta 字段：
   - `_yoast_wpseo_title`
   - `_yoast_wpseo_metadesc`
   - `_yoast_wpseo_focuskw`
6. [ ] 設定 Rank Math meta 字段（備選）：
   - `rank_math_title`
   - `rank_math_description`
   - `rank_math_focus_keyword`
7. [ ] 添加驗證邏輯
8. [ ] 添加日誌記錄

**驗收標準:**
- ✅ SEO Title 正確設定
- ✅ H1 標題正確設定
- ✅ 兩者不相同（除非用戶未選擇 SEO Title）
- ✅ 支援 Yoast SEO 和 Rank Math

**產出物:**
- 更新後的 WordPress 發佈邏輯

---

### Task 4.2: 編寫 WordPress 整合測試

**ID:** SEO-025
**負責人:** 後端工程師
**預估時間:** 3 小時
**優先級:** P1
**狀態:** ⏳ 待開始
**依賴:** SEO-024

**描述:**
編寫 WordPress 發佈的整合測試。

**子任務:**
1. [ ] 創建 `backend/tests/services/test_wordpress_seo_title.py`
2. [ ] 測試 SEO Title 和 H1 設定
3. [ ] 測試 Yoast SEO meta 字段
4. [ ] 測試 Rank Math meta 字段
5. [ ] 測試 fallback 邏輯（無 SEO Title 時）
6. [ ] Mock WordPress API 回應

**驗收標準:**
- ✅ 測試覆蓋率 > 80%
- ✅ 所有測試通過
- ✅ 測試案例全面

**產出物:**
- `backend/tests/services/test_wordpress_seo_title.py`

---

### Task 4.3: WordPress 發佈驗證

**ID:** SEO-026
**負責人:** QA
**預估時間:** 2 小時
**優先級:** P1
**狀態:** ⏳ 待開始
**依賴:** SEO-024

**描述:**
在測試 WordPress 網站驗證發佈結果。

**子任務:**
1. [ ] 準備測試 WordPress 網站
2. [ ] 安裝 Yoast SEO 或 Rank Math 外掛
3. [ ] 發佈測試文章
4. [ ] 驗證 WordPress 文章標題（H1）
5. [ ] 驗證 SEO Title（檢視原始碼 `<title>` 標籤）
6. [ ] 驗證搜尋引擎預覽
7. [ ] 截圖記錄

**驗收標準:**
- ✅ H1 標題顯示正確
- ✅ SEO Title 設定正確
- ✅ 兩者內容不同（如預期）
- ✅ Yoast SEO/Rank Math 顯示正確

**產出物:**
- WordPress 發佈驗證報告（含截圖）

---

## Phase 5: 測試（3 天）

### Task 5.1: 整合測試腳本

**ID:** SEO-027
**負責人:** QA
**預估時間:** 4 小時
**優先級:** P1
**狀態:** ⏳ 待開始
**依賴:** SEO-017, SEO-025

**描述:**
創建完整工作流程的整合測試。

**子任務:**
1. [ ] 創建 `backend/tests/integration/test_seo_title_workflow.py`
2. [ ] 測試場景 1：原文包含 SEO Title 標記
3. [ ] 測試場景 2：原文無 SEO Title 標記
4. [ ] 測試場景 3：選擇 AI 建議
5. [ ] 測試場景 4：自定義 SEO Title
6. [ ] 測試場景 5：WordPress 發佈
7. [ ] 實現測試輔助函數
8. [ ] Mock 外部 API

**驗收標準:**
- ✅ 所有場景測試通過
- ✅ 測試可自動執行
- ✅ 測試穩定可靠

**產出物:**
- `backend/tests/integration/test_seo_title_workflow.py`

---

### Task 5.2: E2E 測試腳本

**ID:** SEO-028
**負責人:** QA
**預估時間:** 6 小時
**優先級:** P1
**狀態:** ⏳ 待開始
**依賴:** SEO-022

**描述:**
使用 Playwright 創建 E2E 測試。

**子任務:**
1. [ ] 創建 `frontend/e2e/seo-title-selection.spec.ts`
2. [ ] 測試場景 1：顯示原文提取的 SEO Title
3. [ ] 測試場景 2：選擇 AI 建議
4. [ ] 測試場景 3：自定義 SEO Title
5. [ ] 測試場景 4：字數統計
6. [ ] 測試場景 5：驗證錯誤處理
7. [ ] 添加測試截圖
8. [ ] 錄製測試視頻

**驗收標準:**
- ✅ E2E 測試可自動執行
- ✅ 所有場景測試通過
- ✅ 測試穩定可靠
- ✅ 無 UI/UX 問題

**產出物:**
- `frontend/e2e/seo-title-selection.spec.ts`
- 測試截圖和視頻

---

### Task 5.3: 性能測試

**ID:** SEO-029
**負責人:** QA
**預估時間:** 3 小時
**優先級:** P2
**狀態:** ⏳ 待開始
**依賴:** SEO-027

**描述:**
測試 SEO Title 功能的性能。

**子任務:**
1. [ ] 測試 AI 解析時間（包含 SEO Title 提取）
2. [ ] 測試優化建議生成時間（包含 SEO Title 建議）
3. [ ] 測試 SEO Title 選擇 API 回應時間
4. [ ] 測試前端頁面載入時間
5. [ ] 測試資料庫查詢性能
6. [ ] 創建性能測試報告

**驗收標準:**
- ✅ AI 解析時間 < 30s
- ✅ SEO Title 選擇 API < 500ms
- ✅ 前端頁面載入 < 2s
- ✅ 無性能瓶頸

**產出物:**
- 性能測試報告

---

### Task 5.4: 手動測試

**ID:** SEO-030
**負責人:** QA
**預估時間:** 4 小時
**優先級:** P1
**狀態:** ⏳ 待開始
**依賴:** SEO-022, SEO-026

**描述:**
手動測試完整工作流程和邊界情況。

**子任務:**
1. [ ] 測試各種 SEO Title 標記格式
2. [ ] 測試極長/極短的 SEO Title
3. [ ] 測試特殊字符
4. [ ] 測試多語言內容
5. [ ] 測試錯誤處理
6. [ ] 測試用戶體驗流程
7. [ ] 記錄測試結果和問題

**驗收標準:**
- ✅ 所有測試案例通過
- ✅ 無阻塞性 bug
- ✅ 用戶體驗良好

**產出物:**
- 手動測試報告

---

## Phase 6: 文檔與部署（1 天）

### Task 6.1: 更新 API 文檔

**ID:** SEO-031
**負責人:** 後端工程師
**預估時間:** 2 小時
**優先級:** P1
**狀態:** ⏳ 待開始
**依賴:** SEO-016

**描述:**
更新 API 文檔，說明 SEO Title 相關端點。

**子任務:**
1. [ ] 更新 OpenAPI/Swagger 文檔
2. [ ] 添加 SEO Title 選擇端點說明
3. [ ] 添加請求/回應範例
4. [ ] 更新現有端點的回應範例（包含 SEO Title 字段）
5. [ ] 添加錯誤碼說明
6. [ ] 審查文檔完整性

**驗收標準:**
- ✅ API 文檔完整準確
- ✅ 範例可正常使用
- ✅ 錯誤碼說明清晰

**產出物:**
- 更新後的 API 文檔

---

### Task 6.2: 創建用戶指南

**ID:** SEO-032
**負責人:** 前端工程師
**預估時間:** 2 小時
**優先級:** P2
**狀態:** ⏳ 待開始
**依賴:** SEO-022

**描述:**
創建 SEO Title 功能的用戶指南。

**子任務:**
1. [ ] 創建 `docs/user-guide/seo-title-guide.md`
2. [ ] 說明 SEO Title vs H1 vs Meta Description
3. [ ] 說明如何在 Google Docs 中標記 SEO Title
4. [ ] 說明如何選擇 SEO Title
5. [ ] 提供最佳實踐建議
6. [ ] 添加截圖和範例
7. [ ] 審查指南易讀性

**驗收標準:**
- ✅ 指南清晰易懂
- ✅ 包含實用範例
- ✅ 截圖清晰

**產出物:**
- `docs/user-guide/seo-title-guide.md`

---

### Task 6.3: 部署到測試環境

**ID:** SEO-033
**負責人:** DevOps
**預估時間:** 2 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-027, SEO-028

**描述:**
部署 SEO Title 功能到測試環境。

**子任務:**
1. [ ] 備份測試環境資料庫
2. [ ] 執行資料庫遷移
3. [ ] 部署後端代碼
4. [ ] 部署前端代碼
5. [ ] 驗證部署成功
6. [ ] 執行 smoke tests
7. [ ] 記錄部署結果

**驗收標準:**
- ✅ 遷移成功執行
- ✅ 應用程式正常運行
- ✅ Smoke tests 通過
- ✅ 無錯誤日誌

**產出物:**
- 測試環境部署報告

---

### Task 6.4: 部署到生產環境

**ID:** SEO-034
**負責人:** DevOps
**預估時間:** 2 小時
**優先級:** P0
**狀態:** ⏳ 待開始
**依賴:** SEO-033, SEO-030

**描述:**
部署 SEO Title 功能到生產環境。

**子任務:**
1. [ ] 備份生產環境資料庫
2. [ ] 執行資料庫遷移（使用事務）
3. [ ] 部署後端代碼（滾動部署）
4. [ ] 部署前端代碼（CDN 更新）
5. [ ] 驗證部署成功
6. [ ] 執行 smoke tests
7. [ ] 監控錯誤日誌（24 小時）
8. [ ] 記錄部署結果

**驗收標準:**
- ✅ 零停機部署
- ✅ 遷移成功執行
- ✅ 應用程式正常運行
- ✅ Smoke tests 通過
- ✅ 無錯誤日誌
- ✅ 性能指標正常

**產出物:**
- 生產環境部署報告
- 監控儀表板

---

## 📊 任務統計

### 按階段統計

| 階段 | 任務數 | 總時間 |
|------|-------|--------|
| Phase 1: 資料庫 | 6 | 2 天 |
| Phase 2: 後端 API | 11 | 4 天 |
| Phase 3: 前端 | 6 | 3 天 |
| Phase 4: WordPress | 3 | 1 天 |
| Phase 5: 測試 | 4 | 3 天 |
| Phase 6: 文檔與部署 | 4 | 1 天 |
| **總計** | **34** | **14 天** |

### 按優先級統計

| 優先級 | 任務數 |
|-------|--------|
| P0 | 20 |
| P1 | 12 |
| P2 | 2 |

### 按負責人統計

| 負責人 | 任務數 |
|--------|--------|
| 後端工程師 | 17 |
| 前端工程師 | 7 |
| QA | 7 |
| DevOps | 3 |

---

## 📝 備註

1. **並行任務**：同一 Phase 內的部分任務可並行執行（例如前端和後端測試）
2. **依賴管理**：嚴格遵守任務依賴關係，避免阻塞
3. **日常站會**：每日同步進度，及時發現和解決問題
4. **代碼審查**：所有 PR 必須經過審查後才能合併
5. **測試先行**：鼓勵 TDD，先寫測試再寫實現
6. **持續集成**：每次提交都觸發 CI 流程

---

**文檔版本：** v1.0
**最後更新：** 2025-01-14
