# 大紀元健康欄目內部鏈接智能推薦系統

## 實施方案 - Supabase 原生架構 (V2)

**版本**: 2.0
**日期**: 2025-12-07
**作者**: CMS Automation Team

---

## V2 變更說明

### 主要改進
1. **完整文章解析**：V2 版本訪問文章詳情頁，提取完整內容（正文、圖片、作者等）
2. **AI 能力邊界明確**：明確標記 GPT-4o-mini 能做和不能做的任務
3. **三層匹配策略**：標題語義 → 正文深度 → 關鍵詞備選
4. **正文向量支持**：可選的 content embedding 用於深度內容匹配

### AI 功能邊界（GPT-4o-mini）
| 功能 | 狀態 | 說明 |
|------|------|------|
| 關鍵詞提取 | ✅ 可用 | 3-5 個健康領域關鍵詞 |
| 標題分解 | ✅ 可用 | 前綴/主標題/副標題 |
| 分類驗證 | ✅ 可用 | 確認或修正文章分類 |
| 作者清理 | ✅ 可用 | 從作者行提取乾淨名字 |
| FAQ 生成 | ❌ 不可用 | 需要深度內容理解 |
| 深度 SEO | ❌ 不可用 | 需要搜索意圖分析 |
| 內容校對 | ❌ 不可用 | 需要專家級模型 |

---

## 1. 專案概述

### 1.1 目標
為大紀元健康欄目文章建立智能內部鏈接推薦系統，通過向量相似度搜索自動匹配相關文章，提升網站SEO和用戶體驗。

### 1.2 技術選型
- **數據庫**: Supabase PostgreSQL + pgvector 擴展
- **無服務器函數**: Supabase Edge Functions (Deno)
- **定時任務**: pg_cron + pg_net
- **AI 模型**:
  - 輕量級解析: OpenAI GPT-4o-mini
  - 向量嵌入: OpenAI text-embedding-3-small (1536維)

### 1.3 處理流程
```
scraped (爬取完成，DOM 解析)
   ↓
parsed (AI 增強解析：標題分解、關鍵詞、分類)
   ↓
embedded (向量嵌入生成)
   ↓
ready (可用於匹配)
```

### 1.4 成本估算（4000篇文章）
| 項目 | 初始處理 | 月度增量 |
|------|---------|---------|
| GPT-4o-mini (解析) | $0.60 | $0.05 |
| text-embedding-3-small (標題) | $0.08 | $0.01 |
| text-embedding-3-small (正文，可選) | $0.72 | $0.06 |
| **總計（不含正文）** | **$0.68** | **$0.06** |
| **總計（含正文）** | **$1.40** | **$0.12** |

---

## 2. 數據庫設計

### 2.1 啟用擴展

```sql
-- 啟用必要的 PostgreSQL 擴展
create extension if not exists vector with schema extensions;
create extension if not exists pg_cron with schema extensions;
create extension if not exists pg_net with schema extensions;
```

### 2.2 健康文章表 (V2 Enhanced)

```sql
create table if not exists public.health_articles (
    id bigint primary key generated always as identity,

    -- ===== 原始爬取數據 (DOM 解析，無 AI) =====
    original_url text not null unique,
    article_id text not null unique,  -- 從 URL 提取 (e.g., n12345678)

    -- 標題 (完整標題 + AI 分解)
    title text not null,                    -- 完整原始標題
    title_prefix text,                      -- AI 分解：前綴 (如【專題】)
    title_main text,                        -- AI 分解：主標題
    title_suffix text,                      -- AI 分解：副標題

    -- 作者信息
    author_line text,                       -- 原始作者行
    author_name text,                       -- AI 清理後的作者名

    -- 內容字段
    body_html text,                         -- 正文 HTML (清理後)
    excerpt text,                           -- 文章摘要/導語
    word_count int,                         -- 正文字數統計

    -- 分類和標籤
    category text default '健康',           -- 原始爬取的欄目分類
    original_tags text[] default '{}',      -- 原始爬取的標籤
    primary_category text,                  -- AI 驗證後的主分類
    secondary_categories text[] default '{}', -- AI 推斷的副分類

    -- 日期
    publish_date date,                      -- 發佈日期

    -- ===== AI 增強數據 (GPT-4o-mini) =====
    ai_keywords text[] default '{}',        -- AI 提取的關鍵詞 (3-5 個)

    -- ===== 向量嵌入數據 =====
    title_embedding extensions.vector(1536),    -- 標題向量
    content_embedding extensions.vector(1536),  -- 正文向量 (可選)

    -- ===== 處理狀態追蹤 =====
    status text default 'scraped' check (status in (
        'scraped',          -- 階段1完成：已爬取 DOM
        'parsed',           -- 階段2完成：AI 增強解析
        'embedded',         -- 階段3完成：向量嵌入生成
        'ready'             -- 全部完成，可用於匹配
    )),

    -- ===== AI 功能標記 =====
    ai_features jsonb default '{
        "keywords": "available",
        "title_decomposition": "available",
        "category_inference": "available",
        "faq_generation": "not_available",
        "deep_seo": "not_available",
        "proofreading": "not_available"
    }'::jsonb,

    -- ===== 時間戳 =====
    scraped_at timestamptz default now(),
    parsed_at timestamptz,
    embedded_at timestamptz,
    updated_at timestamptz default now()
);
```

### 2.3 文章圖片表 (V2 New)

```sql
create table if not exists public.health_article_images (
    id bigint primary key generated always as identity,
    article_id text not null,
    position int not null default 0,
    source_url text not null,
    caption text,
    alt_text text,
    width int,
    height int,
    is_featured boolean default false,
    created_at timestamptz default now(),

    constraint fk_article
        foreign key (article_id)
        references public.health_articles(article_id)
        on delete cascade
);
```

### 2.4 向量搜索函數

```sql
-- 標題向量匹配
create or replace function public.match_health_articles(
    query_embedding extensions.vector(1536),
    match_threshold float default 0.7,
    match_count int default 5,
    exclude_article_id text default null
)
returns table (
    id bigint,
    article_id text,
    title text,
    title_main text,
    original_url text,
    ai_keywords text[],
    excerpt text,
    similarity float
);

-- 正文向量匹配 (V2 New)
create or replace function public.match_by_content(
    query_embedding extensions.vector(1536),
    match_threshold float default 0.6,
    match_count int default 5,
    exclude_article_id text default null
)
returns table (
    id bigint,
    article_id text,
    title text,
    original_url text,
    excerpt text,
    similarity float
);

-- 關鍵詞匹配
create or replace function public.match_by_keywords(
    source_keywords text[],
    match_count int default 5,
    exclude_article_id text default null
)
returns table (
    article_id text,
    title text,
    title_main text,
    original_url text,
    matched_keywords text[],
    match_score int
);
```

---

## 3. Edge Functions 設計 (V2)

### 3.1 爬取健康文章 (scrape-health-articles)

**V2 變更**：現在訪問文章詳情頁提取完整內容

```
輸入: { maxPages, incrementalOnly, maxArticles }
輸出: { processed, new, failed, jobId }

處理流程:
1. 從列表頁獲取文章 URL
2. 訪問每篇文章詳情頁
3. DOM 解析提取完整內容（標題、作者、正文、圖片）
4. 存入 health_articles 和 health_article_images 表
5. 狀態設為 'scraped'
```

### 3.2 AI 解析文章 (parse-articles)

**V2 變更**：原 `extract-keywords`，現統一為 AI 解析

```
輸入: { batchSize }
輸出: { processed, failed, tokensUsed, estimatedCost, aiFeatures }

處理內容 (GPT-4o-mini):
✅ 標題分解：title_prefix, title_main, title_suffix
✅ 關鍵詞提取：ai_keywords (3-5 個)
✅ 分類驗證：primary_category, secondary_categories
✅ 作者清理：author_name

不處理:
❌ FAQ 生成
❌ 深度 SEO 優化
❌ 內容校對
```

### 3.3 生成嵌入向量 (generate-embeddings)

**V2 變更**：支持可選的正文向量

```
輸入: { batchSize, includeContent }
輸出: { processed, failed, estimatedTokens, estimatedCost }

處理流程:
1. 使用 title_main + ai_keywords 生成標題向量
2. (可選) 使用 excerpt + body_html 前部分生成正文向量
3. 狀態從 'parsed' 更新為 'ready'
```

### 3.4 匹配內部鏈接 (match-internal-links)

**V2 變更**：三層匹配策略，返回更多字段

```
輸入: {
  title: string,           // 必填
  keywords?: string[],     // 可選
  content?: string,        // 可選，啟用深度匹配
  article_id?: string,     // 排除自己
  limit?: number,
  include_content_match?: boolean
}

輸出: {
  matches: [{
    article_id, title, title_main, url,
    excerpt, ai_keywords, similarity,
    match_type: 'semantic' | 'content' | 'keyword'
  }],
  stats: { totalMatches, semanticMatches, contentMatches, keywordMatches }
}

匹配策略:
1. 標題語義匹配 (threshold: 0.7)
2. 正文深度匹配 (threshold: 0.6, 可選)
3. 關鍵詞備選匹配 (補充不足)
```

---

## 4. 定時任務配置

### 4.1 pg_cron 排程設定 (V2)

```sql
-- 每日凌晨 2:00 執行增量爬取
select cron.schedule(
    'daily-scrape-health-articles',
    '0 2 * * *',
    $$ select net.http_post(...'/functions/v1/scrape-health-articles'...) $$
);

-- 每日凌晨 2:30 AI 解析 (原 extract-keywords)
select cron.schedule(
    'daily-parse-articles',  -- V2: 重命名
    '30 2 * * *',
    $$ select net.http_post(...'/functions/v1/parse-articles'...) $$
);

-- 每日凌晨 3:00 生成嵌入向量
select cron.schedule(
    'daily-generate-embeddings',
    '0 3 * * *',
    $$ select net.http_post(...'/functions/v1/generate-embeddings'...) $$
);
```

---

## 5. API 使用說明

### 5.1 查詢相關文章（前端使用）

```typescript
// 基本匹配
const result = await fetch('/functions/v1/match-internal-links', {
  method: 'POST',
  body: JSON.stringify({
    title: '糖尿病患者如何選擇健康零食',
    keywords: ['糖尿病', '血糖', '零食'],
    limit: 5
  })
})

// 深度匹配（包含正文）
const deepResult = await fetch('/functions/v1/match-internal-links', {
  method: 'POST',
  body: JSON.stringify({
    title: '糖尿病患者如何選擇健康零食',
    content: '正文片段...',
    include_content_match: true,
    limit: 5
  })
})
```

### 5.2 響應示例

```json
{
  "success": true,
  "matches": [
    {
      "article_id": "n12345678",
      "title": "控制血糖的十種食物",
      "title_main": "控制血糖的十種食物",
      "url": "https://...",
      "excerpt": "文章摘要...",
      "ai_keywords": ["血糖", "糖尿病", "飲食"],
      "similarity": 0.89,
      "match_type": "semantic"
    }
  ],
  "stats": {
    "totalMatches": 5,
    "semanticMatches": 3,
    "contentMatches": 1,
    "keywordMatches": 1
  }
}
```

---

## 6. 文件結構

```
supabase/
├── config.toml                          # Supabase 配置
├── migrations/
│   ├── 001_internal_link_system.sql     # 數據庫結構 (V2)
│   └── 002_cron_jobs.sql                # 定時任務 (V2)
└── functions/
    ├── scrape-health-articles/
    │   └── index.ts                     # 爬取函數 (V2)
    ├── parse-articles/
    │   └── index.ts                     # AI 解析函數 (V2, 原 extract-keywords)
    ├── generate-embeddings/
    │   └── index.ts                     # 嵌入生成函數 (V2)
    └── match-internal-links/
        └── index.ts                     # 匹配函數 (V2)
```

---

## 7. 實施計劃

### 階段 1：數據庫設置
- [x] 啟用 vector、pg_cron、pg_net 擴展
- [x] 創建 health_articles 表 (V2 結構)
- [x] 創建 health_article_images 表
- [x] 創建向量搜索函數（含 match_by_content）

### 階段 2：Edge Functions 開發
- [x] 開發 scrape-health-articles (V2)
- [x] 開發 parse-articles (V2)
- [x] 開發 generate-embeddings (V2)
- [x] 開發 match-internal-links (V2)

### 階段 3：配置和部署
- [x] 創建 config.toml
- [x] 配置 cron jobs (V2)
- [ ] 部署到 Supabase
- [ ] 配置環境變量

### 階段 4：測試和優化
- [ ] 執行初始爬取測試
- [ ] 驗證 AI 解析結果
- [ ] 測試匹配準確度
- [ ] 優化閾值參數

---

## 附錄 A：環境變數配置

```bash
# Supabase 項目配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbG...
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...

# OpenAI API
OPENAI_API_KEY=sk-...
```

## 附錄 B：監控視圖

```sql
-- 處理狀態分布
select * from v_processing_status;

-- 最近任務歷史
select * from v_recent_jobs;

-- 文章圖片統計
select * from v_articles_with_images;
```
