# Feature 006: SEO Title 提取與建議功能

**狀態:** ⏳ 待實施 (Planned)
**優先級:** High (P0)
**預估工期:** 3 週（14 個工作日）
**創建日期:** 2025-01-14
**最後更新:** 2025-01-14

---

## 📋 快速概覽

### 功能簡介

實現 SEO Title 提取與建議功能，使系統能夠：
1. 從 Google Docs 中識別並提取標記為「這是 SEO title」的內容
2. 在資料庫中將 SEO Title 與 H1 標題分離儲存
3. 使用 AI 生成 2-3 個針對 SEO 優化的標題建議
4. 提供前端介面讓用戶選擇原文提取/AI 建議/自定義
5. WordPress 發佈時正確設定 SEO Title 和 H1 標題

### 為什麼需要這個功能？

當前系統存在以下問題：
- ❌ SEO Title 與 H1 標題混用，不符合 SEO 最佳實踐
- ❌ 無法提取文章中標記的 SEO Title
- ❌ AI 建議僅針對 H1，沒有專門的 SEO Title 選項
- ❌ 前端沒有 SEO Title 編輯介面
- ❌ WordPress 發佈時 SEO Title 和 H1 使用相同內容

### SEO Title vs H1 vs Meta Description

| 元素 | 功能 | SEO 權重 | 長度 |
|------|------|---------|------|
| **SEO Title** | 搜尋結果顯示的標題 | 最高 | ~30 字 |
| **H1 標題** | 頁面內容的主標題 | 中等 | 較長 |
| **Meta Description** | 搜尋結果摘要 | 影響點擊率 | 150-160 字 |

**核心原則**：三者應主題一致但角度不同，不建議完全相同。

---

## 📚 文檔導航

### 核心文檔

| 文檔 | 描述 | 狀態 |
|------|------|------|
| **[spec.md](./spec.md)** | 需求規格說明 - 完整的功能需求、用戶故事、技術需求 | ✅ 完成 |
| **[plan.md](./plan.md)** | 實施計劃 - 詳細的實施階段、時間表、風險管理 | ✅ 完成 |
| **[tasks.md](./tasks.md)** | 任務清單 - 34 個具體任務，包含負責人、時間、依賴 | ✅ 完成 |
| **[checklist.md](./checklist.md)** | 測試與驗收清單 - 77 個測試案例，涵蓋單元/整合/E2E/性能/安全 | ✅ 完成 |

### 補充文檔

| 文檔 | 描述 | 位置 |
|------|------|------|
| **SEO Title Implementation Plan** | 詳細的技術實施方案（含代碼範例） | [../../SEO_TITLE_IMPLEMENTATION_PLAN.md](../../SEO_TITLE_IMPLEMENTATION_PLAN.md) |
| **Architecture Investigation** | 當前系統架構分析 | [../../ARCHITECTURE_INVESTIGATION.md](../../ARCHITECTURE_INVESTIGATION.md) |

---

## 🎯 核心目標

### 主要目標

1. ✅ **提取準確率 > 95%**：從標記文章中正確提取 SEO Title
2. ✅ **AI 建議生成成功率 > 98%**：穩定生成 2-3 個 SEO Title 選項
3. ✅ **用戶選擇完成率 > 85%**：用戶能順利完成 SEO Title 選擇
4. ✅ **WordPress 發佈正確率 100%**：SEO Title 和 H1 正確分離

### 成功指標

| 類別 | 指標 | 目標值 |
|------|------|--------|
| **功能** | SEO Title 提取準確率 | > 95% |
| **功能** | AI 建議生成成功率 | > 98% |
| **性能** | AI 解析時間 | < 30s |
| **性能** | API 回應時間 | < 500ms |
| **用戶體驗** | 用戶理解 SEO Title 用途 | > 90% |
| **業務** | SEO Title 與 H1 差異化率 | > 80% |

---

## 🏗️ 架構概覽

### 技術棧

| 層級 | 技術 |
|------|------|
| **資料庫** | PostgreSQL + Alembic 遷移 |
| **後端** | Python + FastAPI + SQLAlchemy |
| **AI** | Anthropic Claude Sonnet 4.5 |
| **前端** | React 18 + TypeScript 5 + Tailwind CSS |
| **測試** | pytest + Jest + Playwright |

### 核心元件

```
┌─────────────────────────────────────────────────────────────┐
│                     前端 (React + TypeScript)                │
├─────────────────────────────────────────────────────────────┤
│  ArticleParsingPage  →  SEOTitleSelectionCard              │
│  (文章解析頁面)         (SEO Title 選擇元件)                  │
└─────────────────┬───────────────────────────────────────────┘
                  │ REST API
┌─────────────────┴───────────────────────────────────────────┐
│                     後端 (FastAPI + Python)                  │
├─────────────────────────────────────────────────────────────┤
│  ArticleParserService      UnifiedOptimizationService       │
│  (文章解析服務)             (統一優化服務)                    │
│  ├─ AI 解析                 ├─ SEO Title 建議生成            │
│  └─ 啟發式解析              └─ 儲存到資料庫                  │
│                                                              │
│  API Endpoints:                                              │
│  POST /articles/{id}/select-seo-title                       │
│  (SEO Title 選擇端點)                                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────────┐
│                     資料庫 (PostgreSQL)                      │
├─────────────────────────────────────────────────────────────┤
│  articles 表                                                 │
│  ├─ seo_title (新增)                                         │
│  ├─ seo_title_extracted (新增)                               │
│  └─ seo_title_source (新增)                                  │
│                                                              │
│  title_suggestions 表                                        │
│  └─ suggested_seo_titles (新增，JSONB)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📅 實施時間表

### 週次規劃

| 週次 | 階段 | 產出物 |
|------|------|--------|
| **Week 1** | Phase 1-2 | 資料庫遷移完成 + 解析器更新 |
| **Week 2** | Phase 2-3 | 優化服務 + 前端元件 |
| **Week 3** | Phase 4-6 | WordPress 整合 + 測試 + 部署 |

### 里程碑

| 日期 | 里程碑 | 可交付成果 |
|------|--------|-----------|
| **Day 2** | M1: 資料庫完成 | 資料庫遷移，模型更新 |
| **Day 6** | M2: 後端完成 | API 端點可用，測試通過 |
| **Day 9** | M3: 前端完成 | UI 元件整合完成 |
| **Day 10** | M4: WordPress 整合 | 發佈流程驗證 |
| **Day 13** | M5: 測試完成 | 所有測試通過 |
| **Day 14** | M6: 生產部署 | 功能上線可用 |

詳細時間表請參考 [plan.md](./plan.md)

---

## 📊 需求摘要

### 功能需求 (Top 5)

| ID | 描述 | 優先級 |
|----|------|-------|
| FR-1 | 識別「這是 SEO title」標記並提取 | P0 |
| FR-2 | 新增 SEO Title 獨立儲存字段 | P0 |
| FR-3 | AI 同時提取 H1 和 SEO Title | P0 |
| FR-5 | 生成 2-3 個 SEO Title 建議 | P0 |
| FR-7 | 前端 SEO Title 選擇介面 | P0 |

完整需求請參考 [spec.md](./spec.md)

### 用戶故事 (Top 3)

1. **Story 1**: 編輯提取原文 SEO Title
   - 系統自動識別標記
   - 顯示「原文提取」選項
   - 一鍵使用原文 SEO Title

2. **Story 2**: 編輯選擇 AI 建議
   - AI 生成 2-3 個選項
   - 顯示推理和關鍵字焦點
   - 點擊選擇即可使用

3. **Story 3**: 編輯自定義 SEO Title
   - 輸入自定義標題
   - 即時字數統計
   - 超長時警告

---

## 🧪 測試概覽

### 測試統計

| 測試類型 | 案例數 | 覆蓋率目標 |
|---------|-------|-----------|
| 單元測試（後端） | 30 | > 80% |
| 單元測試（前端） | 12 | > 70% |
| 整合測試 | 5 | - |
| E2E 測試 | 7 | - |
| 性能測試 | 7 | - |
| 安全測試 | 6 | - |
| 驗收測試 | 10 | - |
| **總計** | **77** | **> 75%** |

### 關鍵測試場景

1. **原文包含 SEO Title 標記**：提取 → 顯示 → 選擇 → 發佈
2. **原文無 SEO Title 標記**：AI 生成 → 選擇 → 發佈
3. **自定義 SEO Title**：輸入 → 驗證 → 保存 → 發佈
4. **WordPress 發佈驗證**：H1 ≠ SEO Title
5. **錯誤處理**：API 失敗 → 重試 → 降級

詳細測試計劃請參考 [checklist.md](./checklist.md)

---

## 🚀 快速開始

### 開發前準備

1. **閱讀文檔**
   ```bash
   # 按順序閱讀核心文檔
   cat specs/006-seo-title-extraction/spec.md      # 了解需求
   cat specs/006-seo-title-extraction/plan.md      # 了解實施計劃
   cat specs/006-seo-title-extraction/tasks.md     # 了解具體任務
   ```

2. **設置開發環境**
   ```bash
   # 後端
   cd backend
   poetry install

   # 前端
   cd frontend
   npm install
   ```

3. **準備測試環境**
   ```bash
   # 準備測試資料庫
   createdb cms_automation_test

   # 執行現有遷移
   alembic upgrade head
   ```

### 開發流程

1. **選擇任務**：從 [tasks.md](./tasks.md) 中選擇待開始的任務
2. **創建分支**：`git checkout -b feature/seo-title-{task-id}`
3. **開發**：遵循 TDD 原則，先寫測試再寫實現
4. **測試**：確保單元測試通過
5. **提交 PR**：代碼審查後合併
6. **更新狀態**：在 tasks.md 中更新任務狀態

---

## 👥 團隊與職責

| 角色 | 負責人 | 任務數 |
|------|--------|--------|
| 後端工程師 | TBD | 17 |
| 前端工程師 | TBD | 7 |
| QA 工程師 | TBD | 7 |
| DevOps 工程師 | TBD | 3 |

---

## 🔗 相關資源

### 內部文檔

- [Phase 7 Article Parsing](../../backend/docs/phase7_article_parsing.md)
- [Phase 7 Unified Optimization](../../backend/docs/phase7_unified_optimization.md)
- [WordPress Integration](../../backend/docs/wordpress_integration.md)
- [Database Schema](../../backend/docs/database_schema.md)

### 外部資源

- [Anthropic Claude API 文檔](https://docs.anthropic.com/)
- [Yoast SEO 開發文檔](https://developer.yoast.com/)
- [Rank Math API 文檔](https://rankmath.com/kb/developers/)
- [Google SEO 最佳實踐](https://developers.google.com/search/docs)

---

## 📞 聯絡資訊

### 問題反饋

- **技術問題**：提交 GitHub Issue
- **需求討論**：在 spec.md 中添加註解
- **進度更新**：更新 tasks.md 狀態

### 文檔維護

- **文檔版本**：v1.0
- **創建日期**：2025-01-14
- **最後更新**：2025-01-14
- **審核狀態**：待審核

---

## 📜 變更日誌

### v1.0 (2025-01-14)

**初始版本**
- ✅ 創建完整的需求規格說明
- ✅ 創建詳細的實施計劃
- ✅ 創建 34 個具體任務
- ✅ 創建 77 個測試案例
- ✅ 創建 README 導航文檔

---

## 🎓 學習資源

### SEO Title 最佳實踐

1. **長度**：保持在 30 中文字（60 字符）以內
2. **關鍵字**：包含核心關鍵字，越靠前越好
3. **吸引力**：使用吸引點擊的詞語（數字、問題、利益點）
4. **獨特性**：與 H1 主題一致但表達不同
5. **品牌**：可考慮加入品牌名稱

### 範例

| H1 標題 | SEO Title | 說明 |
|---------|-----------|------|
| 【專題報導】2024年醫療保健創新趨勢分析：從AI診斷到遠距醫療的全面突破 | 2024年AI醫療創新趨勢 | 精簡，聚焦關鍵字 |
| 如何使用 React Hooks 優化應用性能：10 個實用技巧 | React Hooks 性能優化指南 | 更簡潔，保留核心價值 |
| 機器學習入門教程：從基礎到實戰的完整學習路線圖 | 機器學習入門完整指南 2025 | 加入年份提升時效性 |

---

**🚀 準備好開始了嗎？請先閱讀 [spec.md](./spec.md) 了解完整需求！**
