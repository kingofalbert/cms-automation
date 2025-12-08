# Phase 12: 相關文章內部鏈接系統實施文檔

**版本**: 1.0
**日期**: 2025-12-08
**狀態**: 已完成部署

---

## 1. 系統架構概述

### 1.1 功能目標

為 CMS 自動化系統添加 AI 驅動的相關文章推薦功能，用於：
- 提升網站 SEO（內部鏈接結構優化）
- 增加用戶停留時間和頁面瀏覽量
- 改善用戶體驗（智能相關閱讀推薦）

### 1.2 技術架構

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                 │
│  ArticleParsingPage.tsx                                         │
│  ├── 相關文章推薦區塊                                            │
│  ├── 刷新匹配按鈕 (RefreshCw)                                    │
│  └── 匹配類型標籤 (semantic/content/keyword)                     │
└─────────────────────┬───────────────────────────────────────────┘
                      │ POST /v1/articles/{id}/refresh-related-articles
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (Cloud Run)                         │
│  articles.py router                                              │
│  ├── refresh_related_articles() endpoint                         │
│  └── InternalLinkService                                         │
│       └── match_related_articles()                               │
└─────────────────────┬───────────────────────────────────────────┘
                      │ POST /functions/v1/match-internal-links
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Supabase Edge Functions                        │
│  match-internal-links/index.ts                                   │
│  ├── 語義搜索 (pgvector cosine similarity)                       │
│  ├── 內容搜索 (full-text search)                                 │
│  └── 關鍵詞搜索 (array overlap)                                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Supabase PostgreSQL                            │
│  health_articles 表                                              │
│  ├── title, content, url                                         │
│  ├── ai_keywords (text[])                                        │
│  └── title_embedding (vector(1536))                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 後端實現

### 2.1 InternalLinkService (`backend/src/services/internal_links.py`)

```python
class InternalLinkService:
    """內部鏈接匹配服務 - 調用 Supabase Edge Function"""

    SUPABASE_URL = "https://twsbhjmlmspjwfystpti.supabase.co"
    FUNCTION_NAME = "match-internal-links"

    async def match_related_articles(
        self,
        title: str,
        keywords: list[str] | None = None,
        limit: int = 5,
    ) -> InternalLinkResult:
        """
        調用 Supabase Edge Function 獲取相關文章

        Args:
            title: 文章標題（用於語義搜索）
            keywords: SEO 關鍵詞列表（用於關鍵詞匹配）
            limit: 返回結果數量上限

        Returns:
            InternalLinkResult 包含匹配結果和統計信息
        """
```

**關鍵特性:**
- 使用 `httpx.AsyncClient` 進行異步 HTTP 調用
- 30 秒超時設置，避免阻塞主流程
- 錯誤處理：API 失敗時返回空結果，不阻塞文章處理

### 2.2 API Endpoint (`backend/src/api/routes/articles.py`)

```python
@router.post("/{article_id}/refresh-related-articles", response_model=ArticleResponse)
async def refresh_related_articles(
    article_id: int,
    session: AsyncSession = Depends(get_session),
) -> Article:
    """
    刷新文章的相關文章推薦（無需重新解析整篇文章）

    流程:
    1. 獲取文章的 title_main 和 seo_keywords
    2. 調用 InternalLinkService.match_related_articles()
    3. 更新 article.related_articles JSONB 欄位
    4. 返回更新後的文章數據
    """
```

### 2.3 數據模型

#### RelatedArticle (`backend/src/services/parser/models.py`)

```python
class RelatedArticle(BaseModel):
    """相關文章推薦數據"""
    article_id: str = Field(..., description="文章唯一標識符 (e.g., n12345678)")
    title: str = Field(..., description="文章標題")
    title_main: str | None = Field(None, description="主標題")
    url: str = Field(..., description="文章 URL")
    excerpt: str | None = Field(None, description="文章摘要")
    similarity: float = Field(..., ge=0, le=1, description="相似度分數 0-1")
    match_type: str = Field(..., description="匹配類型: semantic/content/keyword")
    ai_keywords: list[str] = Field(default_factory=list, description="AI 關鍵詞")
```

#### ArticleResponse Schema (`backend/src/api/schemas/article.py`)

```python
class RelatedArticleResponse(BaseSchema):
    """Response schema for related article recommendations"""
    article_id: str
    title: str
    title_main: str | None = None
    url: str
    excerpt: str | None = None
    similarity: float = Field(..., ge=0, le=1)
    match_type: str
    ai_keywords: list[str] = Field(default_factory=list)

class ArticleResponse(TimestampSchema):
    # ... 其他欄位 ...

    # Phase 12: Related Articles
    related_articles: list[RelatedArticleResponse] = Field(
        default_factory=list,
        description='AI-recommended related articles for internal linking'
    )
```

### 2.4 數據庫遷移

**Migration:** `20251207_1200_add_related_articles.py`

```python
def upgrade():
    op.add_column(
        'articles',
        sa.Column(
            'related_articles',
            postgresql.JSONB,
            nullable=True,
            server_default='[]',
            comment='AI 推薦的相關文章內部鏈接列表'
        )
    )

def downgrade():
    op.drop_column('articles', 'related_articles')
```

---

## 3. Supabase Edge Functions

### 3.1 match-internal-links (`supabase/functions/match-internal-links/index.ts`)

**主要功能:**
- 接收文章標題和關鍵詞
- 執行三種匹配策略
- 返回去重和排序後的結果

**匹配策略:**

| 策略 | 方法 | 權重 |
|------|------|------|
| Semantic | pgvector cosine similarity | 最高 |
| Content | PostgreSQL full-text search | 中等 |
| Keyword | Array overlap on ai_keywords | 基礎 |

**API 請求:**
```json
POST /functions/v1/match-internal-links
Authorization: Bearer {SERVICE_ROLE_KEY}
Content-Type: application/json

{
  "title": "文章標題",
  "keywords": ["關鍵詞1", "關鍵詞2"],
  "limit": 5
}
```

**API 響應:**
```json
{
  "success": true,
  "matches": [
    {
      "article_id": "n12345678",
      "title": "相關文章標題",
      "title_main": "主標題",
      "url": "https://www.epochtimes.com/...",
      "excerpt": "文章摘要...",
      "ai_keywords": ["關鍵詞"],
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

### 3.2 generate-embeddings (`supabase/functions/generate-embeddings/index.ts`)

- 調用 OpenAI `text-embedding-3-small` API
- 生成 1536 維向量
- 批量處理健康文章庫

### 3.3 scrape-health-articles (`supabase/functions/scrape-health-articles/index.ts`)

- 爬取大紀元健康頻道文章
- 提取標題、內容、URL
- 使用 AI 生成關鍵詞
- 存儲到 health_articles 表

---

## 4. 前端實現

### 4.1 API Service (`frontend/src/services/parsing.ts`)

```typescript
// 類型定義
export interface RelatedArticle {
  article_id: string;
  title: string;
  title_main?: string;
  url: string;
  excerpt?: string;
  similarity: number;
  match_type: 'semantic' | 'content' | 'keyword';
  ai_keywords: string[];
}

// API 函數
export async function refreshRelatedArticles(
  articleId: number
): Promise<ParsedArticleData> {
  return api.post<ParsedArticleData>(
    `/v1/articles/${articleId}/refresh-related-articles`,
    {}
  );
}

// Query Key
export const parsingKeys = {
  // ...
  result: (articleId: number) => ['parsing', 'result', articleId] as const,
};
```

### 4.2 UI 組件 (`frontend/src/pages/ArticleParsingPage.tsx`)

**React Query Mutation:**
```typescript
const refreshRelatedArticlesMutation = useMutation({
  mutationFn: () => parsingAPI.refreshRelatedArticles(articleId),
  onSuccess: () => {
    queryClient.invalidateQueries({
      queryKey: parsingAPI.parsingKeys.result(articleId),
    });
  },
});
```

**相關文章區塊 JSX:**
```tsx
{/* Related Articles Section */}
<Card>
  <CardHeader>
    <div className="flex justify-between items-center">
      <div>
        <CardTitle>
          相關文章推薦 ({parsingData.related_articles?.length || 0})
        </CardTitle>
        <CardDescription>
          AI 根據標題和關鍵詞自動匹配的內部鏈接文章
        </CardDescription>
      </div>
      <Button
        variant="outline"
        size="sm"
        onClick={() => refreshRelatedArticlesMutation.mutate()}
        disabled={refreshRelatedArticlesMutation.isPending}
      >
        {refreshRelatedArticlesMutation.isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            匹配中...
          </>
        ) : (
          <>
            <RefreshCw className="mr-2 h-4 w-4" />
            刷新匹配
          </>
        )}
      </Button>
    </div>
  </CardHeader>
  <CardContent>
    {/* 文章列表或空狀態 */}
  </CardContent>
</Card>
```

**匹配類型標籤樣式:**
```tsx
<Badge variant={
  article.match_type === 'semantic' ? 'default' :
  article.match_type === 'content' ? 'secondary' : 'outline'
}>
  {article.match_type}
</Badge>
<Badge variant="outline">
  {(article.similarity * 100).toFixed(0)}%
</Badge>
```

---

## 5. 數據庫結構

### 5.1 PostgreSQL (Supabase)

**health_articles 表:**
```sql
CREATE TABLE health_articles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  article_id TEXT UNIQUE NOT NULL,  -- e.g., 'n12345678'
  title TEXT NOT NULL,
  title_main TEXT,
  content TEXT,
  url TEXT NOT NULL,
  excerpt TEXT,
  ai_keywords TEXT[] DEFAULT '{}',
  title_embedding vector(1536),     -- OpenAI embedding
  status TEXT DEFAULT 'pending',    -- pending/ready/error
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 向量索引
CREATE INDEX ON health_articles
USING ivfflat (title_embedding vector_cosine_ops)
WITH (lists = 100);

-- 全文搜索索引
CREATE INDEX ON health_articles
USING gin (to_tsvector('chinese', title || ' ' || COALESCE(content, '')));
```

### 5.2 PostgreSQL (Backend - Alembic)

**articles 表 related_articles 欄位:**
```python
related_articles: Mapped[list[dict] | None] = mapped_column(
    JSONB,
    nullable=True,
    default=list,
    comment="AI 推薦的相關文章內部鏈接列表"
)
```

---

## 6. 環境配置

### 6.1 Cloud Run 環境變量

| 變量名 | 說明 |
|--------|------|
| `SUPABASE_URL` | Supabase 項目 URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role 密鑰 |

### 6.2 Supabase Secrets

| 變量名 | 說明 |
|--------|------|
| `OPENAI_API_KEY` | OpenAI API 密鑰（用於生成 embeddings）|

---

## 7. 部署信息

### 7.1 服務端點

| 服務 | URL |
|------|-----|
| Backend API | `https://cms-automation-backend-297291472291.us-east1.run.app` |
| Frontend | `https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/app.html` |
| Supabase Functions | `https://twsbhjmlmspjwfystpti.supabase.co/functions/v1/` |

### 7.2 API 端點

| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/v1/articles/{id}/refresh-related-articles` | 刷新相關文章推薦 |
| GET | `/v1/articles/{id}/parsing-result` | 獲取解析結果（含 related_articles）|

---

## 8. 測試驗證

### 8.1 API 測試

```bash
# 刷新相關文章
curl -X POST 'https://cms-automation-backend-297291472291.us-east1.run.app/v1/articles/7/refresh-related-articles'

# 檢查結果
curl 'https://cms-automation-backend-297291472291.us-east1.run.app/v1/articles/7/parsing-result' | jq '.related_articles'
```

### 8.2 UI 測試路徑

1. 訪問 `app.html#/articles/{id}/parsing`
2. 滾動到「相關文章推薦」區塊
3. 點擊「刷新匹配」按鈕
4. 驗證 loading 狀態和結果顯示

---

## 9. 注意事項

### 9.1 匹配結果為空的原因

- 健康文章庫內容與目標文章主題不匹配
- 目標文章的關鍵詞未被健康文章庫覆蓋
- 語義相似度閾值過高

### 9.2 性能考慮

- Edge Function 超時: 30 秒
- 匹配結果限制: 預設 5 篇
- 向量搜索使用 IVFFlat 索引優化

### 9.3 後續優化方向

1. 擴充健康文章庫覆蓋更多主題
2. 調整相似度閾值提高召回率
3. 添加用戶手動編輯相關文章功能
4. 實現相關文章緩存機制

---

## 10. 相關文件索引

| 文件路徑 | 說明 |
|----------|------|
| `backend/src/services/internal_links.py` | InternalLinkService 服務類 |
| `backend/src/api/routes/articles.py` | refresh-related-articles 端點 |
| `backend/src/api/schemas/article.py` | RelatedArticleResponse schema |
| `backend/src/services/parser/models.py` | RelatedArticle 模型 |
| `backend/src/models/article.py` | Article ORM 模型 |
| `backend/migrations/versions/20251207_1200_add_related_articles.py` | 數據庫遷移 |
| `frontend/src/services/parsing.ts` | 前端 API 服務 |
| `frontend/src/pages/ArticleParsingPage.tsx` | 相關文章 UI 組件 |
| `supabase/functions/match-internal-links/index.ts` | 匹配 Edge Function |
| `supabase/migrations/001_internal_link_system.sql` | Supabase 數據庫結構 |
