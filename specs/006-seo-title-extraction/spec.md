# SEO Title 提取與建議功能 - 需求規格說明

**Feature ID:** 006-seo-title-extraction
**創建日期:** 2025-01-14
**最後更新:** 2025-01-14
**優先級:** High
**狀態:** 待實施 (Planned)

---

## 📋 概述

### 背景

當前系統在 Phase 7 已實現文章結構化解析（Title、Author、Body、SEO Metadata、Images），但存在以下問題：

1. **SEO Title 與 H1 標題混用**：系統未區分搜尋引擎顯示的 SEO Title 和頁面內容的 H1 標題
2. **原文 SEO Title 無法提取**：即使文章中標記了「這是 SEO title」，解析器也無法識別
3. **AI 建議不夠精準**：目前的 Title Suggestions 僅針對 H1，未生成專門的 SEO Title 選項
4. **用戶無法選擇**：前端沒有提供 SEO Title 的選擇和編輯介面
5. **WordPress 發佈問題**：發佈時 SEO Title 和 H1 使用相同內容，不符合 SEO 最佳實踐

### SEO Title vs H1 vs Meta Description 說明

| 元素 | 位置 | 功能 | SEO 權重 | 長度限制 | 用途 |
|------|------|------|---------|---------|------|
| **SEO Title (Title Tag)** | HTML `<head>` 中的 `<title>` | 搜尋結果頁面顯示的標題 | 最高 | ~30 字 | 給搜尋引擎和用戶的第一印象 |
| **H1 標題** | HTML `<body>` 中的 `<h1>` | 頁面內容的主標題 | 中等 | 較長 | 用戶閱讀體驗 |
| **Meta Description** | HTML `<head>` 中的 `<meta name="description">` | 搜尋結果中 Title 下方的摘要 | 不直接影響排名 | 150-160 字 | 吸引用戶點擊 |

**建議關係**：
- 三者應主題一致但角度不同
- SEO Title：精簡聚焦關鍵字
- H1：更完整描述內容
- Meta Description：補充說明吸引點擊
- **不建議三者完全相同**

### 目標

實現「SEO Title 提取 → AI 建議生成 → 用戶選擇 → WordPress 發佈」的完整流程：

1. **原文提取**：從 Google Docs 中識別並提取標記為「這是 SEO title」的內容
2. **獨立儲存**：在資料庫中將 SEO Title 與 H1 標題分離儲存
3. **AI 建議**：生成 2-3 個針對 SEO 優化的標題選項（30 字以內）
4. **用戶選擇**：提供清晰的介面讓用戶選擇原文提取/AI 建議/自定義
5. **WordPress 整合**：發佈時正確設定 SEO Title 和 H1 標題

### 範圍

- ✅ 資料庫架構調整（新增 SEO Title 字段）
- ✅ AI 解析器更新（識別 SEO Title 標記）
- ✅ 啟發式解析器更新（正則表達式匹配）
- ✅ 統一優化服務擴展（生成 SEO Title 建議）
- ✅ 前端 SEO Title 選擇元件
- ✅ WordPress 發佈整合
- ✅ 完整測試方案
- ❌ 多語言 SEO Title（後續優化）
- ❌ A/B 測試框架（後續優化）

---

## 🎯 需求詳情

### 功能需求 (FR)

| ID | 描述 | 優先級 |
|----|------|-------|
| **FR-1** | 系統必須能從 Google Docs HTML 中識別「這是 SEO title：」、「SEO標題：」等標記並提取 SEO Title | P0 |
| **FR-2** | 資料庫必須新增 `seo_title`、`seo_title_extracted`、`seo_title_source` 字段到 articles 表 | P0 |
| **FR-3** | AI 解析器（Claude）必須能在解析時同時提取 H1 標題和 SEO Title | P0 |
| **FR-4** | 啟發式解析器必須使用正則表達式匹配多種 SEO Title 標記模式 | P0 |
| **FR-5** | UnifiedOptimizationService 必須生成 2-3 個 SEO Title 建議選項（每個 ≤30 字） | P0 |
| **FR-6** | SEO Title 建議必須包含：標題文本、推理說明、關鍵字焦點、字數統計 | P0 |
| **FR-7** | 前端必須提供 SEO Title 選擇介面，支援選擇原文提取/AI 建議/自定義 | P0 |
| **FR-8** | 系統必須提供 `/articles/{id}/select-seo-title` API 端點用於選擇 SEO Title | P0 |
| **FR-9** | WordPress 發佈時必須將 SEO Title 設定到 Yoast SEO 或 Rank Math 的 meta_title 字段 | P1 |
| **FR-10** | 前端必須清楚區分 SEO Title 和 H1 標題的顯示和用途 | P1 |
| **FR-11** | SEO Title 選擇後必須記錄來源（extracted/ai_generated/user_input） | P1 |
| **FR-12** | 系統必須驗證自定義 SEO Title 不超過 30 字（60 characters） | P1 |

### 非功能需求 (NFR)

| ID | 描述 | 優先級 |
|----|------|-------|
| **NFR-1** | SEO Title 提取準確率必須 > 95%（當文章有標記時） | P0 |
| **NFR-2** | AI 生成 SEO Title 建議的時間必須 < 30 秒（作為統一優化的一部分） | P0 |
| **NFR-3** | SEO Title 選擇 API 回應時間必須 < 500ms | P0 |
| **NFR-4** | 前端頁面載入時間必須 < 2 秒 | P1 |
| **NFR-5** | AI 生成的 SEO Title 必須與 H1 有差異化（非完全相同） | P1 |
| **NFR-6** | 資料庫遷移必須保證零停機（使用 nullable 字段） | P0 |
| **NFR-7** | 歷史文章必須自動遷移（將 title_main 複製為初始 seo_title） | P0 |

### 業務規則 (BR)

| ID | 規則 |
|----|------|
| **BR-1** | SEO Title 長度建議 ≤ 30 中文字（約 60 characters） |
| **BR-2** | SEO Title 必須包含核心關鍵字以提升搜尋排名 |
| **BR-3** | SEO Title 與 H1 標題應主題一致但表達不同 |
| **BR-4** | 如果原文有標記 SEO Title，優先顯示原文提取的選項 |
| **BR-5** | AI 建議必須提供 2-3 個不同風格的選項（含/不含分類標籤、不同關鍵字焦點等） |
| **BR-6** | 用戶未選擇 SEO Title 時，系統應使用 H1 的 title_main 作為 fallback |
| **BR-7** | SEO Title 來源必須可追溯（extracted/ai_generated/user_input/migrated） |

---

## 👥 用戶故事

### Story 1: 編輯提取原文 SEO Title

**作為**編輯，
**我想要**系統能自動識別文章中標記的「這是 SEO title」內容，
**以便**我不需要手動複製粘貼到單獨的欄位中。

**驗收標準：**
- ✅ 上傳包含「這是 SEO title：XXX」的 Google Docs
- ✅ 解析後顯示「原文提取」的 SEO Title
- ✅ SEO Title 與 H1 標題分別顯示
- ✅ 可以選擇使用原文提取的 SEO Title

### Story 2: 編輯選擇 AI 建議的 SEO Title

**作為**編輯，
**我想要**AI 生成 2-3 個針對 SEO 優化的標題選項，
**以便**我可以選擇最適合搜尋引擎的標題而不需要自己撰寫。

**驗收標準：**
- ✅ 確認解析後自動生成 SEO Title 建議
- ✅ 顯示 2-3 個不同的 SEO Title 選項
- ✅ 每個選項顯示推理說明、關鍵字焦點、字數
- ✅ 可以點擊「選擇」按鈕選擇任一選項
- ✅ 選擇後顯示「✓ 已選擇」狀態

### Story 3: 編輯自定義 SEO Title

**作為**編輯，
**我想要**能夠輸入自定義的 SEO Title，
**以便**當 AI 建議和原文提取都不滿意時，我可以使用自己的版本。

**驗收標準：**
- ✅ 點擊「自定義 SEO Title」按鈕
- ✅ 顯示輸入框，可輸入自定義標題
- ✅ 即時顯示字數統計
- ✅ 超過 30 字時顯示警告
- ✅ 保存後更新為自定義的 SEO Title

### Story 4: 編輯理解 SEO Title 與 H1 的區別

**作為**編輯，
**我想要**介面清楚說明 SEO Title 和 H1 標題的區別，
**以便**我能理解為什麼需要分別設定。

**驗收標準：**
- ✅ 顯示 SEO Title vs H1 vs Meta Description 的對比說明
- ✅ 使用不同顏色或標籤區分 SEO Title 和 H1
- ✅ 提供 AI 優化建議（如「SEO Title 保持在 30 字以內」）
- ✅ 顯示每個選項的關鍵字焦點

### Story 5: WordPress 發佈正確設定 SEO Title

**作為**系統管理員，
**我想要**發佈到 WordPress 時正確設定 SEO Title 和 H1 標題，
**以便**網站的 SEO 優化符合最佳實踐。

**驗收標準：**
- ✅ 發佈時 WordPress 文章標題使用 H1 (title_main)
- ✅ Yoast SEO 的 meta_title 使用選定的 SEO Title
- ✅ 搜尋引擎抓取時顯示 SEO Title
- ✅ 頁面內容顯示 H1 標題
- ✅ 兩者內容不完全相同

---

## 🔧 技術需求

### 資料庫架構

#### 1. articles 表新增字段

```sql
-- 新增 SEO Title 字段
ALTER TABLE articles ADD COLUMN seo_title VARCHAR(200) NULL
  COMMENT 'SEO Title Tag (30字左右，用於<title>標籤和搜尋結果顯示)';

ALTER TABLE articles ADD COLUMN seo_title_extracted BOOLEAN NOT NULL DEFAULT FALSE
  COMMENT '是否從原文中提取了標記的 SEO Title';

ALTER TABLE articles ADD COLUMN seo_title_source VARCHAR(50) NULL
  COMMENT 'SEO Title 來源：extracted/ai_generated/user_input/migrated';

-- 歷史數據遷移
UPDATE articles
SET seo_title = title_main, seo_title_source = 'migrated'
WHERE title_main IS NOT NULL AND seo_title IS NULL;
```

#### 2. title_suggestions 表新增字段

```sql
-- 新增 SEO Title 建議字段
ALTER TABLE title_suggestions ADD COLUMN suggested_seo_titles JSONB NULL
  COMMENT 'AI生成的 SEO Title 建議 (2-3 個選項，30字左右)';

-- 更新現有字段註釋
COMMENT ON COLUMN title_suggestions.suggested_title_sets IS
  'AI生成的 H1 標題建議 (prefix + main + suffix 組合，用於頁面內容)';
```

#### 3. suggested_seo_titles JSONB 結構

```json
{
  "variants": [
    {
      "id": "seo_variant_1",
      "seo_title": "2024年AI醫療創新趨勢",
      "reasoning": "聚焦核心關鍵字「AI醫療」和「創新」，30字內",
      "keywords_focus": ["AI醫療", "創新", "2024"],
      "character_count": 12
    },
    {
      "id": "seo_variant_2",
      "seo_title": "【醫療科技】AI診斷如何改變未來",
      "reasoning": "加入分類前綴提升專業度，強調「診斷」和「未來」",
      "keywords_focus": ["醫療科技", "AI診斷", "未來"],
      "character_count": 17
    },
    {
      "id": "seo_variant_3",
      "seo_title": "遠距醫療與AI結合：2024突破",
      "reasoning": "結合兩個熱門話題「遠距醫療」和「AI」",
      "keywords_focus": ["遠距醫療", "AI", "2024"],
      "character_count": 16
    }
  ],
  "original_seo_title": "2024年醫療保健創新趨勢",
  "notes": [
    "SEO Title 建議保持在 30 字以內",
    "包含核心關鍵字以提升搜尋排名",
    "與 H1 標題主題一致但更精簡"
  ]
}
```

### API 端點

#### 1. 更新解析結果回應（現有端點）

**GET** `/api/v1/articles/{article_id}/parsing-result`

回應增加字段：
```json
{
  "title_prefix": "【專題報導】",
  "title_main": "2024年醫療保健創新趨勢分析",
  "title_suffix": "從AI診斷到遠距醫療的全面突破",
  "full_title": "【專題報導】2024年醫療保健創新趨勢分析：從AI診斷到遠距醫療的全面突破",

  "seo_title": "2024年AI醫療創新趨勢",
  "seo_title_extracted": true,
  "seo_title_source": "extracted",

  "author_name": "張三",
  "body_html": "<p>...</p>",
  "meta_description": "探討2024年...",
  "seo_keywords": ["AI醫療", "遠距醫療"],
  "parsing_method": "ai",
  "parsing_confidence": 0.95
}
```

#### 2. 更新優化建議回應（現有端點）

**GET** `/api/v1/articles/{article_id}/optimizations`

回應增加字段：
```json
{
  "title_suggestions": {
    "suggested_title_sets": [...]
  },

  "seo_title_suggestions": {
    "variants": [
      {
        "id": "seo_variant_1",
        "seo_title": "2024年AI醫療創新趨勢",
        "reasoning": "聚焦核心關鍵字...",
        "keywords_focus": ["AI醫療", "創新", "2024"],
        "character_count": 12
      }
    ],
    "original_seo_title": "2024年AI醫療創新趨勢",
    "notes": [...]
  },

  "seo_keywords": {...},
  "meta_description": {...},
  "faq_schema": [...]
}
```

#### 3. 新增 SEO Title 選擇端點

**POST** `/api/v1/articles/{article_id}/select-seo-title`

**請求體：**
```json
{
  "variant_id": "seo_variant_1",      // 選擇 AI 建議（三選一）
  "use_original": false,              // 使用原文提取
  "custom_seo_title": null            // 自定義 SEO Title
}
```

**回應：**
```json
{
  "success": true,
  "message": "SEO Title updated successfully",
  "data": {
    "article_id": 123,
    "seo_title": "2024年AI醫療創新趨勢",
    "source": "ai_generated"
  }
}
```

**驗證規則：**
- 必須提供 `variant_id`、`use_original=true` 或 `custom_seo_title` 三者之一
- `custom_seo_title` 長度不超過 60 characters（約 30 中文字）
- `variant_id` 必須存在於 title_suggestions.suggested_seo_titles 中
- `use_original=true` 時必須確保 article.seo_title_extracted = true

### 前端元件

#### 1. SEOTitleSelectionCard 元件

**Props:**
```typescript
interface SEOTitleSelectionCardProps {
  // 原文提取的 SEO Title
  originalSEOTitle: string | null;
  seoTitleExtracted: boolean;

  // AI 建議的 SEO Title 選項
  suggestions: SEOTitleVariant[];
  notes: string[];

  // 當前選中的 SEO Title
  currentSEOTitle: string | null;

  // 回調函數
  onSelect: (variantId: string) => void;
  onUseOriginal: () => void;
  onCustom: (customTitle: string) => void;

  // 狀態
  isLoading?: boolean;
}
```

**功能：**
- 顯示原文提取的 SEO Title（如果有）
- 顯示 AI 建議的 2-3 個選項
- 支援自定義輸入
- 即時字數統計
- 清楚說明 SEO Title vs H1 的區別

#### 2. 整合到 ArticleParsingPage

**位置：** `frontend/src/pages/ArticleParsingPage.tsx`

**顯示邏輯：**
1. 解析完成後顯示 H1 標題卡片
2. 確認解析後自動生成優化建議
3. 優化建議完成後顯示：
   - TitleOptimizationCard（H1 標題選擇）
   - SEOTitleSelectionCard（SEO Title 選擇）← **新增**
   - SEO Keywords、Meta Description、FAQ 卡片

### WordPress 整合

**文件：** `backend/src/services/article_importer/wordpress_importer.py`

```python
def _prepare_post_data(self, article: Article) -> dict:
    """Prepare WordPress post data."""

    # SEO Title (fallback to title_main if not set)
    seo_title = article.seo_title or article.title_main

    # H1 Title (complete title with prefix/suffix)
    h1_title = article.title

    return {
        'title': h1_title,  # WordPress 文章標題（H1）
        'content': article.body_html,
        'status': 'publish',
        'meta': {
            # Yoast SEO 字段
            '_yoast_wpseo_title': seo_title,
            '_yoast_wpseo_metadesc': article.meta_description,
            '_yoast_wpseo_focuskw': article.seo_keywords[0] if article.seo_keywords else '',

            # Rank Math 字段（備選）
            'rank_math_title': seo_title,
            'rank_math_description': article.meta_description,
            'rank_math_focus_keyword': article.seo_keywords[0] if article.seo_keywords else '',
        },
    }
```

---

## 📊 資料流程

### 1. 文章解析流程

```
Google Docs HTML
      ↓
ArticleParserService.parse_document()
      ↓
┌─────────────────────┐
│ AI 解析 (Claude)    │ → 識別「這是 SEO title」標記
│ 或                  │ → 提取 SEO Title 和 H1 標題分別
│ 啟發式解析          │ → 設定 seo_title_extracted = true/false
└─────────────────────┘
      ↓
ParsedArticle {
  title_prefix, title_main, title_suffix,  // H1
  seo_title, seo_title_extracted,          // SEO Title
  author, body, meta_description, keywords
}
      ↓
儲存到 articles 表
```

### 2. AI 優化建議生成流程

```
用戶確認解析
      ↓
UnifiedOptimizationService.generate_all_optimizations()
      ↓
調用 Claude API（單次調用）
      ↓
生成：
  - H1 Title Suggestions (2-3 variants)
  - SEO Title Suggestions (2-3 variants) ← 新增
  - SEO Keywords
  - Meta Description
  - FAQ Schema
      ↓
儲存到 title_suggestions 表 (suggested_seo_titles 字段)
```

### 3. SEO Title 選擇流程

```
用戶在前端選擇 SEO Title
      ↓
POST /articles/{id}/select-seo-title
{
  variant_id: "seo_variant_1",
  use_original: false,
  custom_seo_title: null
}
      ↓
更新 articles 表：
  - seo_title = "2024年AI醫療創新趨勢"
  - seo_title_source = "ai_generated"
      ↓
回應成功
```

### 4. WordPress 發佈流程

```
用戶點擊發佈
      ↓
WordPressImporter.publish_article()
      ↓
準備發佈數據：
  - title = H1 完整標題 (title)
  - meta._yoast_wpseo_title = SEO Title (seo_title)
  - meta._yoast_wpseo_metadesc = Meta Description
      ↓
調用 WordPress REST API
      ↓
WordPress 文章發佈：
  - <title>SEO Title</title> ← 搜尋引擎抓取
  - <h1>H1 Title</h1> ← 頁面內容顯示
```

---

## 🚀 成功指標

### 功能指標

| 指標 | 目標值 | 測量方法 |
|------|-------|---------|
| SEO Title 提取準確率 | > 95% | 測試集中有標記的文章提取成功率 |
| AI 建議生成成功率 | > 98% | Claude API 調用成功率 |
| SEO Title 選擇成功率 | 100% | API 端點錯誤率 < 1% |
| WordPress 發佈正確率 | 100% | 發佈後驗證 SEO Title 和 H1 分離 |

### 性能指標

| 指標 | 目標值 | 測量方法 |
|------|-------|---------|
| AI 解析時間 | < 30s | 平均 API 回應時間 |
| SEO Title 選擇 API | < 500ms | P95 回應時間 |
| 前端頁面載入 | < 2s | Lighthouse Performance Score |
| 資料庫遷移時間 | < 5min | 在測試環境測量 |

### 用戶體驗指標

| 指標 | 目標值 | 測量方法 |
|------|-------|---------|
| 用戶理解 SEO Title 用途 | > 90% | 用戶訪談/調查 |
| SEO Title 選擇完成率 | > 85% | 分析用戶行為日誌 |
| 自定義 SEO Title 使用率 | < 20% | 統計 seo_title_source |
| AI 建議接受率 | > 60% | 統計選擇 AI variant 的比例 |

### 業務指標

| 指標 | 目標值 | 測量方法 |
|------|-------|---------|
| SEO Title 與 H1 差異化率 | > 80% | 比對 seo_title != title_main 的比例 |
| 搜尋排名提升 | 待觀察 | Google Search Console 數據 |
| 點擊率提升 | 待觀察 | Google Analytics 數據 |

---

## 🔒 安全與隱私

### 安全需求

1. **輸入驗證**
   - SEO Title 長度限制（max 60 characters）
   - 防止 XSS 注入（前端和後端雙重驗證）
   - API 端點需要身份驗證

2. **資料完整性**
   - variant_id 必須存在於資料庫中
   - 原文提取模式需驗證 seo_title_extracted = true
   - 資料庫遷移需保證原子性

3. **錯誤處理**
   - Claude API 失敗時提供 fallback
   - 資料庫更新失敗時回滾
   - 前端顯示友好錯誤訊息

### 隱私需求

1. **資料最小化**
   - 僅儲存必要的 SEO Title 相關數據
   - 不記錄用戶編輯過程的中間狀態

2. **存取控制**
   - 僅授權用戶可編輯 SEO Title
   - API 端點需檢查用戶權限

---

## 📝 假設與依賴

### 假設

1. 用戶會在 Google Docs 中使用「這是 SEO title：」等標記
2. 大部分文章的 SEO Title 需求在 30 字以內
3. 用戶理解 SEO Title 與 H1 的區別（需提供說明）
4. WordPress 網站已安裝 Yoast SEO 或 Rank Math 外掛

### 依賴

1. **外部服務**
   - Anthropic Claude API（用於 AI 解析和建議生成）
   - WordPress REST API（用於發佈）

2. **內部服務**
   - Phase 7 Article Parsing（已完成）
   - Phase 7 Unified Optimization Service（已完成）
   - PostgreSQL 資料庫

3. **前端依賴**
   - React 18
   - TypeScript 5
   - TanStack Query
   - Tailwind CSS

---

## 🔄 未來優化方向

### Phase 2 優化（未包含在本次實施）

1. **多語言 SEO Title**
   - 支援英文、日文等其他語言
   - 根據語言調整長度限制

2. **A/B 測試框架**
   - 測試不同 SEO Title 對點擊率的影響
   - 自動選擇表現最好的 SEO Title

3. **批次更新**
   - 批次更新歷史文章的 SEO Title
   - 批次生成 SEO Title 建議

4. **SEO 效果追蹤**
   - 整合 Google Search Console
   - 追蹤 SEO Title 對排名的影響
   - 提供優化建議

5. **智能推薦**
   - 根據歷史數據學習用戶偏好
   - 自動推薦最適合的 SEO Title 風格

---

## 📚 參考文檔

- [SEO Title Implementation Plan](../../SEO_TITLE_IMPLEMENTATION_PLAN.md)
- [Phase 7 Article Parsing](../../backend/docs/phase7_article_parsing.md)
- [Phase 7 Unified Optimization](../../backend/docs/phase7_unified_optimization.md)
- [WordPress Integration](../../backend/docs/wordpress_integration.md)
- [Database Schema](../../backend/docs/database_schema.md)

---

**文檔版本：** v1.0
**審核狀態：** 待審核
**核准人：** TBD
