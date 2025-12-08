# 相關文章內部鏈接集成方案

## 實施方案文檔

**版本**: 1.0
**日期**: 2025-12-07
**狀態**: 實施中

---

## 1. 需求概述

### 1.1 業務需求

在 Google Docs 文章解析流程中，自動為每篇文章推薦相關的內部鏈接文章，用於：
- 提升網站 SEO（內部鏈接結構）
- 增加用戶停留時間
- 改善用戶體驗（相關閱讀推薦）

### 1.2 功能需求

1. **解析時自動匹配**：在文章解析完成後，自動調用 Supabase 內部鏈接 API 獲取相關文章
2. **存儲相關文章**：將匹配結果存儲到數據庫
3. **UI 顯示**：在 ArticleParsingPage 顯示相關文章列表
4. **可編輯**：用戶可以添加、刪除或重新排序相關文章

### 1.3 數據結構

每個相關文章包含：
- `article_id`: 文章唯一標識符（如 n12345678）
- `title`: 文章標題
- `url`: 文章 URL
- `similarity`: 相似度分數 (0-1)
- `match_type`: 匹配類型（semantic/content/keyword）

---

## 2. 技術架構

### 2.1 系統流程

```
┌─────────────────┐
│ Google Docs     │
│ 文章解析        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ArticleParser   │
│ Service         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ ArticleProc-    │────▶│ Supabase Edge   │
│ essingService   │     │ Function        │
└────────┬────────┘     │ match-internal- │
         │              │ links           │
         │              └─────────────────┘
         ▼
┌─────────────────┐
│ PostgreSQL      │
│ articles +      │
│ related_articles│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Frontend        │
│ ArticleParsing- │
│ Page.tsx        │
└─────────────────┘
```

### 2.2 API 集成

**Supabase Edge Function 調用**：
```
POST https://twsbhjmlmspjwfystpti.supabase.co/functions/v1/match-internal-links
Authorization: Bearer {SERVICE_ROLE_KEY}
Content-Type: application/json

{
  "title": "文章標題",
  "keywords": ["關鍵詞1", "關鍵詞2"],
  "limit": 5
}
```

**響應格式**：
```json
{
  "success": true,
  "matches": [
    {
      "article_id": "n12345678",
      "title": "相關文章標題",
      "title_main": "主標題",
      "url": "https://...",
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

---

## 3. 實施計劃

### 3.1 後端修改

#### 3.1.1 ParsedArticle 模型 (`backend/src/services/parser/models.py`)

添加 `related_articles` 字段：

```python
class RelatedArticle(BaseModel):
    """相關文章推薦數據"""
    article_id: str = Field(..., description="文章唯一標識符")
    title: str = Field(..., description="文章標題")
    title_main: str | None = Field(None, description="主標題")
    url: str = Field(..., description="文章 URL")
    excerpt: str | None = Field(None, description="文章摘要")
    similarity: float = Field(..., ge=0, le=1, description="相似度分數")
    match_type: str = Field(..., description="匹配類型")
    ai_keywords: list[str] = Field(default_factory=list, description="AI 關鍵詞")

class ParsedArticle(BaseModel):
    # ... existing fields ...

    # Phase 12: Internal Link Recommendations
    related_articles: list[RelatedArticle] = Field(
        default_factory=list,
        description="AI 推薦的相關文章內部鏈接"
    )
```

#### 3.1.2 內部鏈接服務 (`backend/src/services/internal_links.py`)

新建服務類：

```python
class InternalLinkService:
    """內部鏈接匹配服務"""

    SUPABASE_URL = "https://twsbhjmlmspjwfystpti.supabase.co"

    async def match_related_articles(
        self,
        title: str,
        keywords: list[str] | None = None,
        limit: int = 5
    ) -> list[dict]:
        """調用 Supabase Edge Function 獲取相關文章"""
        ...
```

#### 3.1.3 ArticleProcessingService 集成

在 `process_article` 方法中添加相關文章匹配步驟：

```python
async def process_article(self, ...):
    # Step 1-4: Existing parsing logic

    # Step 5: Match related articles (NEW)
    if parsed_article.seo_keywords:
        related_articles = await self._match_related_articles(
            title=parsed_article.title_main,
            keywords=parsed_article.seo_keywords
        )
        parsed_article.related_articles = related_articles
```

#### 3.1.4 數據庫模型 (`backend/src/models/article.py`)

添加 `related_articles` 列：

```python
class Article(Base, TimestampMixin):
    # ... existing fields ...

    # Phase 12: Internal Link Recommendations
    related_articles: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="AI 推薦的相關文章內部鏈接列表"
    )
```

#### 3.1.5 API Schema (`backend/src/api/schemas/article.py`)

添加相關文章響應 schema：

```python
class RelatedArticleResponse(BaseSchema):
    """相關文章響應"""
    article_id: str
    title: str
    title_main: str | None = None
    url: str
    excerpt: str | None = None
    similarity: float
    match_type: str
    ai_keywords: list[str] = Field(default_factory=list)

class ArticleResponse(TimestampSchema):
    # ... existing fields ...

    # Phase 12: Internal Links
    related_articles: list[RelatedArticleResponse] = Field(
        default_factory=list,
        description="AI 推薦的相關文章"
    )
```

### 3.2 數據庫遷移

創建 Alembic 遷移文件：

```python
"""Add related_articles column to articles table

Revision ID: xxx
"""

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

### 3.3 前端修改

#### 3.3.1 類型定義 (`frontend/src/services/parsing.ts`)

```typescript
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

export interface ParsedArticleData {
  // ... existing fields ...
  related_articles: RelatedArticle[];
}
```

#### 3.3.2 UI 組件 (`frontend/src/pages/ArticleParsingPage.tsx`)

添加相關文章顯示區塊：

```tsx
{/* Related Articles Section */}
{parsingData.related_articles?.length > 0 && (
  <Card>
    <CardHeader>
      <CardTitle>相關文章推薦 ({parsingData.related_articles.length})</CardTitle>
      <CardDescription>
        AI 根據標題和關鍵詞自動匹配的內部鏈接文章
      </CardDescription>
    </CardHeader>
    <CardContent>
      <div className="space-y-3">
        {parsingData.related_articles.map((article, idx) => (
          <div key={article.article_id} className="border rounded-lg p-3">
            <div className="flex justify-between items-start">
              <div>
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium hover:underline"
                >
                  {article.title}
                </a>
                {article.excerpt && (
                  <p className="text-sm text-muted-foreground mt-1">
                    {article.excerpt.substring(0, 100)}...
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <Badge variant={
                  article.match_type === 'semantic' ? 'default' :
                  article.match_type === 'content' ? 'secondary' : 'outline'
                }>
                  {article.match_type}
                </Badge>
                <Badge variant="info">
                  {(article.similarity * 100).toFixed(0)}%
                </Badge>
              </div>
            </div>
          </div>
        ))}
      </div>
    </CardContent>
  </Card>
)}
```

---

## 4. 環境配置

### 4.1 後端環境變量

```bash
# .env (backend)
SUPABASE_URL=https://twsbhjmlmspjwfystpti.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...
```

### 4.2 Supabase 配置

需要在 Supabase Dashboard > Edge Functions > Secrets 中配置：
- `OPENAI_API_KEY`: 用於生成向量嵌入

---

## 5. 測試計劃

### 5.1 單元測試

- InternalLinkService.match_related_articles() 正確調用 API
- ParsedArticle 正確序列化/反序列化 related_articles
- Article 模型正確存儲 related_articles

### 5.2 集成測試

- 完整解析流程包含相關文章匹配
- API 響應正確包含 related_articles
- 前端正確顯示相關文章列表

### 5.3 E2E 測試

- 從 Google Docs 導入到顯示相關文章的完整流程

---

## 6. 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Supabase API 不可用 | 無法匹配相關文章 | 設置超時，失敗不阻塞主流程 |
| 健康文章庫為空 | 匹配不到任何文章 | 顯示友好提示，引導先爬取文章 |
| API 響應慢 | 解析流程變慢 | 異步處理，設置合理超時 |

---

## 7. 實施狀態

- [x] 需求文檔
- [x] ParsedArticle 模型修改 (`backend/src/services/parser/models.py`)
- [x] InternalLinkService 服務創建 (`backend/src/services/internal_links.py`)
- [x] ArticleProcessingService 集成 (`backend/src/services/parser/article_processor.py`)
- [x] 數據庫遷移 (`backend/migrations/versions/20251207_1200_add_related_articles.py`)
- [x] API Schema 更新 (`backend/src/api/schemas/article.py`)
- [x] 前端 UI 實現 (`frontend/src/pages/ArticleParsingPage.tsx`)
- [x] 配置 Supabase OPENAI_API_KEY
- [x] 配置後端 SUPABASE_SERVICE_ROLE_KEY
- [x] 健康文章庫擴充 (53 篇 ready 狀態)
- [x] 內部鏈接匹配功能測試

---

## 8. 相關文件

- `/supabase/functions/match-internal-links/index.ts` - Supabase 匹配函數
- `/supabase/migrations/001_internal_link_system.sql` - 數據庫結構
- `/docs/internal-link-system-plan.md` - 內部鏈接系統整體方案
