# SEO Title 提取與建議功能實施方案

## 📋 執行摘要

本方案旨在實現以下功能：
1. **從原始文章中提取 SEO Title**：識別文章中標註為「這是 SEO title」的內容
2. **儲存到資料庫**：在資料庫中獨立儲存 SEO Title，與正文分離
3. **AI 生成 SEO Title 建議**：提供 2-3 個不同的 SEO Title 選項供客戶選擇
4. **前端審核介面**：允許用戶查看、選擇和編輯建議的 SEO Title

## 🎯 SEO Title vs H1 vs Meta Description 說明

根據您提供的定義：

| 元素 | 位置 | 功能 | SEO 權重 | 長度限制 |
|------|------|------|---------|---------|
| **SEO Title (Title Tag)** | HTML `<head>` 中的 `<title>` | 搜尋結果頁面顯示的標題，是搜尋引擎判斷主題的重要依據 | 最高 | ~30 字 |
| **H1 標題** | HTML `<body>` 中的 `<h1>` | 頁面內容的主標題，影響用戶閱讀體驗 | 中等 | 較長，描述性強 |
| **Meta Description** | HTML `<head>` 中的 `<meta name="description">` | 搜尋結果中 Title 下方的摘要 | 不直接影響排名但影響點擊率 | 150-160 字 |

**建議關係**：三者應主題一致但角度不同
- SEO Title：精簡聚焦關鍵字
- H1：完整描述內容
- Meta Description：補充說明吸引點擊

## 🔍 當前系統分析

### 1. 資料庫結構 (現有)

**`articles` 表**：
```python
# Phase 7 現有字段
title: Mapped[str]                    # 完整標題 (用於前端顯示)
title_prefix: Mapped[str | None]      # 標題前綴 (e.g., "【專題報導】")
title_main: Mapped[str | None]        # 主標題
title_suffix: Mapped[str | None]      # 副標題
meta_description: Mapped[str | None]  # Meta Description (150-160 字)
seo_keywords: Mapped[list[str] | None] # SEO 關鍵字
```

**`title_suggestions` 表** (Phase 7 已存在)：
```python
class TitleSuggestion(Base):
    id: int
    article_id: int

    # AI 生成的標題建議 (2-3 組)
    suggested_title_sets: dict = {
        "variants": [
            {
                "id": "variant_1",
                "prefix": "【專題】",
                "main": "2024年AI醫療創新",
                "suffix": "從診斷到治療的革命",
                "reasoning": "..."
            },
            # ... 更多變體
        ]
    }

    optimization_notes: list[str]  # AI 優化建議
    generated_at: datetime
    ai_model_used: str
```

### 2. 文章解析流程 (現有)

```
Google Drive → worklist_items (raw_html)
            ↓
    [Parse] ArticleParserService
            ├─ AI (Claude Sonnet 4.5) → 提取 title_prefix/main/suffix
            └─ Heuristic (BeautifulSoup) → 正則表達式提取
            ↓
    articles 表 (populated with parsed data)
            ↓
    [Confirm] ArticleParsingPage.tsx
            ↓
    [Auto-generate] UnifiedOptimizationService
            ├─ Title Suggestions (2-3 variants)
            ├─ SEO Keywords
            ├─ Meta Description
            └─ FAQ
            ↓
    title_suggestions, seo_suggestions, article_faqs 表
            ↓
    [Review] ArticleSEOConfirmationPage.tsx
```

### 3. 現有問題

**缺少的功能**：
1. ❌ 沒有獨立的 `seo_title` 字段（與 H1 混用）
2. ❌ AI 解析時未識別「這是 SEO title」標記
3. ❌ 無法從原始 HTML 中提取標記的 SEO Title
4. ❌ Title Suggestions 未區分 H1 和 SEO Title
5. ❌ 前端未提供 SEO Title 編輯和選擇介面

## 🏗️ 實施方案

### Phase 1: 資料庫架構調整

#### 1.1 新增 SEO Title 字段到 `articles` 表

**資料庫遷移** (`backend/src/alembic/versions/xxxx_add_seo_title.py`)：

```python
"""Add SEO Title fields to articles table

Revision ID: xxxx_add_seo_title
Revises: <previous_revision>
Create Date: 2025-XX-XX

"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # 新增 seo_title 字段
    op.add_column(
        'articles',
        sa.Column(
            'seo_title',
            sa.String(length=200),
            nullable=True,
            comment='SEO Title Tag (30字左右，用於搜尋引擎顯示，與H1分離)'
        )
    )

    # 新增 seo_title_extracted 字段（標記是否從原文提取）
    op.add_column(
        'articles',
        sa.Column(
            'seo_title_extracted',
            sa.Boolean(),
            nullable=False,
            default=False,
            server_default='false',
            comment='是否從原文中提取了標記的 SEO Title'
        )
    )

    # 新增 seo_title_source 字段（來源追蹤）
    op.add_column(
        'articles',
        sa.Column(
            'seo_title_source',
            sa.String(length=50),
            nullable=True,
            comment='SEO Title 來源：extracted（從原文提取）/ ai_generated（AI生成）/ user_input（用戶輸入）'
        )
    )

    # 為現有記錄遷移：將 title_main 複製為 seo_title（作為初始值）
    op.execute(
        """
        UPDATE articles
        SET seo_title = title_main,
            seo_title_source = 'migrated'
        WHERE title_main IS NOT NULL AND seo_title IS NULL
        """
    )

def downgrade() -> None:
    op.drop_column('articles', 'seo_title_source')
    op.drop_column('articles', 'seo_title_extracted')
    op.drop_column('articles', 'seo_title')
```

#### 1.2 更新 `title_suggestions` 表結構

**資料庫遷移** (`backend/src/alembic/versions/xxxx_update_title_suggestions.py`)：

```python
"""Update title_suggestions to separate H1 and SEO Title

Revision ID: xxxx_update_title_suggestions
Revises: xxxx_add_seo_title
Create Date: 2025-XX-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

def upgrade() -> None:
    # 新增 suggested_seo_titles 字段（專門儲存 SEO Title 建議）
    op.add_column(
        'title_suggestions',
        sa.Column(
            'suggested_seo_titles',
            JSONB,
            nullable=True,
            comment='AI生成的 SEO Title 建議 (2-3 個選項，30字左右)'
        )
    )

    # 示例結構：
    # {
    #   "variants": [
    #     {
    #       "id": "seo_variant_1",
    #       "seo_title": "2024年AI醫療創新趨勢",
    #       "reasoning": "聚焦關鍵字「AI醫療」和「創新」，30字內",
    #       "keywords_focus": ["AI醫療", "創新", "2024"],
    #       "character_count": 12
    #     },
    #     {
    #       "id": "seo_variant_2",
    #       "seo_title": "【醫療科技】AI診斷如何改變未來",
    #       "reasoning": "加入分類前綴提升專業度，強調「診斷」和「未來」",
    #       "keywords_focus": ["醫療科技", "AI診斷", "未來"],
    #       "character_count": 17
    #     },
    #     {
    #       "id": "seo_variant_3",
    #       "seo_title": "遠距醫療與AI結合：2024突破",
    #       "reasoning": "結合兩個熱門話題「遠距醫療」和「AI」",
    #       "keywords_focus": ["遠距醫療", "AI", "2024"],
    #       "character_count": 16
    #     }
    #   ],
    #   "original_seo_title": "2024年醫療保健創新趨勢",  # 如果原文有提取
    #   "notes": [
    #     "SEO Title 建議保持在 30 字以內",
    #     "包含核心關鍵字以提升搜尋排名",
    #     "與 H1 標題主題一致但更精簡"
    #   ]
    # }

    # 更新現有 suggested_title_sets 的註釋
    op.alter_column(
        'title_suggestions',
        'suggested_title_sets',
        comment='AI生成的 H1 標題建議 (prefix + main + suffix 組合)',
        existing_type=JSONB,
        existing_nullable=True
    )

def downgrade() -> None:
    op.drop_column('title_suggestions', 'suggested_seo_titles')
```

#### 1.3 更新 Article 模型

**文件**：`backend/src/models/article.py`

```python
# 在 Article 類中新增字段
class Article(Base, TimestampMixin):
    # ... 現有字段 ...

    # === Phase 7: 現有標題字段 (H1 標題) ===
    title_prefix: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment='H1 標題前綴 (optional), e.g., "【專題報導】"',
    )

    title_main: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment='H1 主標題 (required), e.g., "2024年醫療保健創新趨勢"',
    )

    title_suffix: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment='H1 副標題 (optional), e.g., "從AI診斷到遠距醫療"',
    )

    # === NEW: SEO Title 字段 ===
    seo_title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment='SEO Title Tag (30字左右，用於<title>標籤和搜尋結果顯示)',
    )

    seo_title_extracted: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default='false',
        comment='是否從原文中提取了標記的 SEO Title',
    )

    seo_title_source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment='SEO Title 來源：extracted/ai_generated/user_input/migrated',
    )

    # ... 其他字段 ...
```

#### 1.4 更新 TitleSuggestion 模型

**文件**：`backend/src/models/title_suggestions.py`

```python
class TitleSuggestion(Base):
    # ... 現有字段 ...

    # 更新註釋：明確區分 H1 和 SEO Title
    suggested_title_sets: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment='AI生成的 H1 標題建議 (prefix + main + suffix 組合，用於頁面內容)',
    )

    # NEW: 新增 SEO Title 建議字段
    suggested_seo_titles: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment='AI生成的 SEO Title 建議 (2-3 個選項，30字左右，用於<title>標籤)',
    )
```

### Phase 2: 後端 API 實施

#### 2.1 更新 ArticleParserService - 提取標記的 SEO Title

**文件**：`backend/src/services/parser/article_parser.py`

##### 2.1.1 更新 AI 解析提示詞

```python
def _build_ai_parsing_prompt(self, raw_html: str) -> str:
    """Build the prompt for Claude to parse article HTML."""
    return f"""You are an expert at parsing Chinese article HTML from Google Docs into structured data.

Parse the following Google Doc HTML and extract structured information.

**Instructions**:
1. **Title (H1)**: Split into prefix (optional, e.g., "【專題】"), main title (required), and suffix (optional subtitle)
2. **SEO Title**: Look for text explicitly marked as "這是 SEO title" or "SEO標題：" in the document. Extract the SEO title separately from H1.
   - If found, extract the full SEO title text (excluding the marker)
   - SEO Title should be concise (around 30 characters)
   - If no explicit SEO title marker is found, set to null
3. **Author**: Extract from "文／" or "作者：" patterns. Provide both raw line and cleaned name.
4. **Body**: Remove header metadata, navigation elements, and images. Keep only article paragraphs.
5. **Meta Description**: Create a 150-160 character SEO description summarizing the article.
6. **SEO Keywords**: Extract 5-10 relevant keywords for SEO.
7. **Tags**: Extract 3-6 content tags/categories.
8. **Images**: Extract all images with their position (paragraph index), URL, and caption.

**Output Format** (JSON):
```json
{{
  "title_prefix": "【專題報導】",  // Optional H1 prefix
  "title_main": "2024年醫療保健創新趨勢",  // Required H1 main title
  "title_suffix": "從AI診斷到遠距醫療",  // Optional H1 suffix

  "seo_title": "2024年AI醫療創新突破",  // NEW: Extracted SEO Title (if marked)
  "seo_title_found": true,  // NEW: Whether explicit SEO title marker was found

  "author_line": "文／張三｜編輯／李四",
  "author_name": "張三",
  "body_html": "<p>正文內容...</p>",
  "meta_description": "探討2024年醫療保健領域的AI創新...",
  "seo_keywords": ["AI醫療", "遠距醫療", "醫療創新"],
  "tags": ["醫療科技", "人工智慧", "數位健康"],
  "images": [...]
}}
```

<HTML>
{raw_html}
</HTML>

Return ONLY the JSON object, no other text."""
```

##### 2.1.2 更新啟發式解析 - 正則表達式匹配

```python
def _parse_with_heuristics(self, raw_html: str) -> ParsingResult:
    """Parse document using heuristic rules (BeautifulSoup + regex)."""

    soup = BeautifulSoup(raw_html, 'html.parser')

    # 1. 提取 SEO Title（新增）
    seo_title = None
    seo_title_extracted = False

    # 正則表達式匹配「這是 SEO title」、「SEO標題：」等模式
    seo_title_patterns = [
        r'(?:這是\s*)?SEO\s*[Tt]itle[：:]\s*(.+?)(?:\n|$|<)',
        r'SEO\s*標題[：:]\s*(.+?)(?:\n|$|<)',
        r'<title[^>]*>(.+?)</title>',  # 如果有明確的 <title> 標籤
    ]

    text_content = soup.get_text()
    for pattern in seo_title_patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            seo_title = match.group(1).strip()
            seo_title_extracted = True
            logger.info(f"Extracted SEO title from marker: {seo_title}")
            break

    # 2. 提取 H1 標題（現有邏輯）
    title_prefix, title_main, title_suffix = self._extract_title_components(soup)

    # ... 其他解析邏輯 ...

    parsed_article = ParsedArticle(
        title_prefix=title_prefix,
        title_main=title_main,
        title_suffix=title_suffix,
        seo_title=seo_title,  # NEW
        seo_title_extracted=seo_title_extracted,  # NEW
        # ... 其他字段 ...
    )

    return ParsingResult(success=True, parsed_article=parsed_article)
```

##### 2.1.3 更新 ParsedArticle 模型

**文件**：`backend/src/services/parser/models.py`

```python
@dataclass
class ParsedArticle:
    """Structured article data extracted from parsing."""

    # H1 Title components
    title_prefix: str | None
    title_main: str
    title_suffix: str | None

    # NEW: SEO Title
    seo_title: str | None = None
    seo_title_extracted: bool = False  # 是否從原文提取

    # Author
    author_line: str | None
    author_name: str | None

    # Content
    body_html: str

    # SEO
    meta_description: str | None
    seo_keywords: list[str]
    tags: list[str]

    # Images
    images: list[ParsedImage]

    # Metadata
    parsing_method: str  # 'ai' or 'heuristic'
    parsing_confidence: float
```

#### 2.2 更新 UnifiedOptimizationService - 生成 SEO Title 建議

**文件**：`backend/src/services/optimization/unified_optimization_service.py`

```python
class UnifiedOptimizationService:
    """Service for generating all article optimizations in one API call."""

    async def generate_all_optimizations(
        self,
        article: Article,
        regenerate: bool = False,
    ) -> OptimizationsResponse:
        """Generate title, SEO, and FAQ optimizations in a single Claude API call."""

        # 構建優化提示詞（包含 SEO Title 生成）
        prompt = self._build_unified_optimization_prompt(article)

        # 調用 Claude API
        response = await self._call_claude_api(prompt)

        # 解析回應
        optimizations = self._parse_optimization_response(response)

        # 儲存到資料庫
        await self._save_optimizations(article, optimizations)

        return optimizations

    def _build_unified_optimization_prompt(self, article: Article) -> str:
        """Build prompt for unified optimization generation."""

        # 提取現有 SEO Title（如果有）
        existing_seo_title = article.seo_title or article.title_main
        seo_title_source = "extracted from document" if article.seo_title_extracted else "not provided"

        return f"""You are an SEO and content optimization expert for Chinese articles.

Given the following article information, generate optimizations for:
1. **H1 Title Suggestions** (2-3 variants for page display)
2. **SEO Title Suggestions** (2-3 variants for search engines, ~30 characters)
3. **SEO Keywords** (focus, primary, secondary)
4. **Meta Description** (150-160 characters)
5. **Tags** (3-6 WordPress categories)
6. **FAQ Schema** (8-10 Q&A pairs)

**Article Information**:
- Current H1 Title: {article.title_prefix or ""}{article.title_main}{article.title_suffix or ""}
  - Prefix: {article.title_prefix or "None"}
  - Main: {article.title_main}
  - Suffix: {article.title_suffix or "None"}

- Current SEO Title: {existing_seo_title} ({seo_title_source})
- Author: {article.author_name or "Unknown"}
- Body: {article.body_html[:1000]}... (truncated)
- Current Meta Description: {article.meta_description or "None"}
- Current SEO Keywords: {', '.join(article.seo_keywords or [])}

**Output Format** (JSON):
```json
{{
  "title_suggestions": {{
    "suggested_title_sets": [
      {{
        "id": "h1_variant_1",
        "prefix": "【專題】",
        "main": "2024年AI醫療創新全解析",
        "suffix": "診斷、治療、預防三大突破",
        "reasoning": "加強專業性和完整性..."
      }},
      // ... 2-3 variants for H1
    ],
    "optimization_notes": ["建議1", "建議2"]
  }},

  "seo_title_suggestions": {{
    "variants": [
      {{
        "id": "seo_variant_1",
        "seo_title": "2024年AI醫療創新趨勢",
        "reasoning": "聚焦核心關鍵字，30字內",
        "keywords_focus": ["AI醫療", "創新", "2024"],
        "character_count": 12
      }},
      {{
        "id": "seo_variant_2",
        "seo_title": "【醫療科技】AI診斷改變未來",
        "reasoning": "加入分類標籤，強調「診斷」和「未來」",
        "keywords_focus": ["醫療科技", "AI診斷", "未來"],
        "character_count": 16
      }},
      {{
        "id": "seo_variant_3",
        "seo_title": "遠距醫療結合AI：2024突破",
        "reasoning": "結合兩個熱門主題",
        "keywords_focus": ["遠距醫療", "AI", "2024"],
        "character_count": 15
      }}
    ],
    "original_seo_title": "{existing_seo_title}",
    "notes": [
      "SEO Title 保持在 30 字以內",
      "包含核心關鍵字提升搜尋排名",
      "與 H1 主題一致但更精簡"
    ]
  }},

  "seo_keywords": {{
    "focus_keyword": "AI醫療創新",
    "primary_keywords": ["遠距醫療", "智能診斷", "醫療科技"],
    "secondary_keywords": ["數位健康", "精準醫療"],
    "reasoning": "..."
  }},

  "meta_description": {{
    "description": "探討2024年AI如何改變醫療保健...",
    "character_count": 156,
    "quality_score": 0.92,
    "reasoning": "..."
  }},

  "tags": ["醫療科技", "人工智慧", "數位健康"],

  "faq_schema": [
    {{
      "question": "AI在醫療診斷中如何應用？",
      "answer": "...",
      "position": 1
    }},
    // ... 8-10 Q&A pairs
  ]
}}
```

Return ONLY the JSON object."""

    async def _save_optimizations(
        self,
        article: Article,
        optimizations: dict
    ) -> None:
        """Save optimization results to database."""

        # 儲存 H1 Title Suggestions
        title_suggestion = TitleSuggestion(
            article_id=article.id,
            suggested_title_sets=optimizations['title_suggestions']['suggested_title_sets'],
            suggested_seo_titles=optimizations['seo_title_suggestions'],  # NEW
            optimization_notes=optimizations['title_suggestions']['optimization_notes'],
            generated_at=datetime.utcnow(),
            ai_model_used=self.model,
        )

        # ... 儲存其他優化結果 ...
```

#### 2.3 新增 API 端點

**文件**：`backend/src/api/v1/endpoints/parsing.py`

##### 2.3.1 更新解析結果回應模型

```python
from pydantic import BaseModel, Field

class ParsedArticleResponse(BaseModel):
    """Response model for parsed article data."""

    # H1 Title
    title_prefix: str | None
    title_main: str
    title_suffix: str | None
    full_title: str

    # NEW: SEO Title
    seo_title: str | None = Field(None, description="Extracted SEO Title from document")
    seo_title_extracted: bool = Field(False, description="Whether SEO title was found in document")
    seo_title_source: str | None = Field(None, description="Source of SEO title")

    # Author
    author_line: str | None
    author_name: str | None

    # Content
    body_html: str

    # SEO
    meta_description: str | None
    seo_keywords: list[str]
    tags: list[str]

    # Images
    images: list[ImageMetadata]

    # Parsing metadata
    parsing_method: str
    parsing_confidence: float
    parsing_confirmed: bool
    has_seo_data: bool
```

##### 2.3.2 新增 SEO Title 選擇端點

```python
@router.post(
    "/articles/{article_id}/select-seo-title",
    response_model=SuccessResponse,
    summary="選擇 SEO Title",
)
async def select_seo_title(
    article_id: int,
    request: SEOTitleSelectionRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    選擇或自定義 SEO Title。

    支持三種模式：
    1. 選擇 AI 建議的 SEO Title（variant_id）
    2. 使用原文提取的 SEO Title（use_original=true）
    3. 自定義 SEO Title（custom_seo_title）
    """

    # 獲取文章
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # 獲取 Title Suggestions
    title_suggestion = await db.execute(
        select(TitleSuggestion).where(TitleSuggestion.article_id == article_id)
    )
    title_suggestion = title_suggestion.scalar_one_or_none()

    if not title_suggestion:
        raise HTTPException(status_code=404, detail="Title suggestions not found")

    # 處理選擇邏輯
    if request.use_original:
        # 使用原文提取的 SEO Title
        if not article.seo_title_extracted:
            raise HTTPException(
                status_code=400,
                detail="No extracted SEO title available in original document"
            )
        selected_seo_title = article.seo_title
        source = "extracted"

    elif request.custom_seo_title:
        # 使用自定義 SEO Title
        selected_seo_title = request.custom_seo_title
        source = "user_input"

    elif request.variant_id:
        # 選擇 AI 建議的 SEO Title
        variants = title_suggestion.suggested_seo_titles.get('variants', [])
        selected_variant = next(
            (v for v in variants if v['id'] == request.variant_id),
            None
        )
        if not selected_variant:
            raise HTTPException(status_code=400, detail="Invalid variant_id")

        selected_seo_title = selected_variant['seo_title']
        source = "ai_generated"
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide variant_id, use_original=true, or custom_seo_title"
        )

    # 更新文章
    article.seo_title = selected_seo_title
    article.seo_title_source = source
    await db.commit()

    logger.info(
        f"SEO Title selected for article {article_id}: "
        f"'{selected_seo_title}' (source: {source})"
    )

    return SuccessResponse(
        success=True,
        message="SEO Title updated successfully",
        data={
            "article_id": article_id,
            "seo_title": selected_seo_title,
            "source": source,
        }
    )


class SEOTitleSelectionRequest(BaseModel):
    """Request model for SEO title selection."""

    variant_id: str | None = Field(None, description="AI 建議的 SEO Title variant ID")
    use_original: bool = Field(False, description="使用原文提取的 SEO Title")
    custom_seo_title: str | None = Field(None, description="自定義 SEO Title（最多30字）")

    @validator('custom_seo_title')
    def validate_custom_seo_title(cls, v):
        if v and len(v) > 60:  # 30 中文字 ≈ 60 characters
            raise ValueError('SEO Title should be within 30 characters')
        return v
```

##### 2.3.3 更新優化結果回應模型

```python
class OptimizationsResponse(BaseModel):
    """Response model for all optimizations."""

    title_suggestions: TitleSuggestionsData
    seo_title_suggestions: SEOTitleSuggestionsData  # NEW
    seo_keywords: SEOKeywordsData
    meta_description: MetaDescriptionData
    tags: list[str]
    faq_schema: list[FAQData]


class SEOTitleSuggestionsData(BaseModel):
    """SEO Title suggestions data."""

    variants: list[SEOTitleVariant]
    original_seo_title: str | None
    notes: list[str]


class SEOTitleVariant(BaseModel):
    """Single SEO title variant."""

    id: str
    seo_title: str
    reasoning: str
    keywords_focus: list[str]
    character_count: int
```

### Phase 3: 前端實施

#### 3.1 更新前端類型定義

**文件**：`frontend/src/services/parsing.ts`

```typescript
// 更新 ParsedArticleData 介面
export interface ParsedArticleData {
  // H1 Title
  title_prefix: string | null;
  title_main: string;
  title_suffix: string | null;
  full_title: string;

  // NEW: SEO Title
  seo_title: string | null;
  seo_title_extracted: boolean;
  seo_title_source: 'extracted' | 'ai_generated' | 'user_input' | 'migrated' | null;

  // Author
  author_line: string | null;
  author_name: string | null;

  // Content
  body_html: string;

  // SEO
  meta_description: string | null;
  seo_keywords: string[];
  tags: string[];

  // Images
  images: ArticleImage[];

  // Metadata
  parsing_method: 'ai' | 'heuristic';
  parsing_confidence: number;
  parsing_confirmed: boolean;
  has_seo_data: boolean;
}

// NEW: SEO Title Suggestions
export interface SEOTitleSuggestionsData {
  variants: SEOTitleVariant[];
  original_seo_title: string | null;
  notes: string[];
}

export interface SEOTitleVariant {
  id: string;
  seo_title: string;
  reasoning: string;
  keywords_focus: string[];
  character_count: number;
}

// 更新 OptimizationsResponse
export interface OptimizationsResponse {
  title_suggestions: TitleSuggestionsData;
  seo_title_suggestions: SEOTitleSuggestionsData; // NEW
  seo_keywords: SEOKeywordsData;
  meta_description: MetaDescriptionData;
  tags: string[];
  faq_schema: FAQData[];
}

// NEW: SEO Title Selection Request
export interface SEOTitleSelectionRequest {
  variant_id?: string;
  use_original?: boolean;
  custom_seo_title?: string;
}
```

#### 3.2 更新 API 服務

**文件**：`frontend/src/services/parsing.ts`

```typescript
export const parsingAPI = {
  // ... 現有方法 ...

  /**
   * 選擇 SEO Title
   */
  selectSEOTitle: async (
    articleId: number,
    request: SEOTitleSelectionRequest
  ): Promise<SuccessResponse> => {
    const response = await apiClient.post(
      `/articles/${articleId}/select-seo-title`,
      request
    );
    return response.data;
  },
};
```

#### 3.3 新增 SEO Title 選擇元件

**文件**：`frontend/src/components/parsing/SEOTitleSelectionCard.tsx`

```typescript
import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui';
import { Button } from '../ui';
import { Badge } from '../ui';
import { Alert, AlertDescription } from '../ui/alert';

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

export default function SEOTitleSelectionCard({
  originalSEOTitle,
  seoTitleExtracted,
  suggestions,
  notes,
  currentSEOTitle,
  onSelect,
  onUseOriginal,
  onCustom,
  isLoading = false,
}: SEOTitleSelectionCardProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [customTitle, setCustomTitle] = useState('');

  const handleSelectVariant = (variantId: string) => {
    setSelectedId(variantId);
    setShowCustomInput(false);
    onSelect(variantId);
  };

  const handleUseOriginal = () => {
    setSelectedId(null);
    setShowCustomInput(false);
    onUseOriginal();
  };

  const handleSaveCustom = () => {
    if (customTitle.trim()) {
      setSelectedId(null);
      onCustom(customTitle.trim());
      setShowCustomInput(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          SEO Title 選擇
          <Badge variant="info">搜尋引擎標題</Badge>
        </CardTitle>
        <CardDescription>
          選擇用於搜尋引擎顯示的 SEO Title（建議 30 字以內）
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 說明區塊 */}
        <Alert>
          <AlertDescription>
            <div className="space-y-2">
              <p className="font-medium">💡 SEO Title 與 H1 的區別：</p>
              <ul className="list-disc list-inside text-sm space-y-1">
                <li><strong>SEO Title</strong>：出現在搜尋結果中，影響點擊率和排名（30字內）</li>
                <li><strong>H1 標題</strong>：出現在頁面內容中，用於用戶閱讀（可較長）</li>
                <li>兩者應主題一致但角度不同，不建議完全相同</li>
              </ul>
            </div>
          </AlertDescription>
        </Alert>

        {/* 原文提取的 SEO Title（如果有） */}
        {seoTitleExtracted && originalSEOTitle && (
          <div className="border-2 border-blue-200 rounded-lg p-4 bg-blue-50">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="primary">原文提取</Badge>
                  <span className="text-xs text-muted-foreground">
                    從文章中提取的標記 SEO Title
                  </span>
                </div>
                <p className="text-lg font-medium">{originalSEOTitle}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  長度: {originalSEOTitle.length} 字
                </p>
              </div>
              <Button
                size="sm"
                onClick={handleUseOriginal}
                disabled={isLoading}
              >
                使用此標題
              </Button>
            </div>
          </div>
        )}

        {/* AI 建議的 SEO Title 選項 */}
        <div className="space-y-3">
          <h4 className="font-medium text-sm text-muted-foreground">
            AI 建議的 SEO Title 選項：
          </h4>

          {suggestions.map((variant, index) => (
            <div
              key={variant.id}
              className={`border rounded-lg p-4 transition-all ${
                selectedId === variant.id
                  ? 'border-primary bg-primary/5 shadow-sm'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">選項 {index + 1}</Badge>
                  <span className="text-xs text-muted-foreground">
                    {variant.character_count} 字
                  </span>
                </div>
                <Button
                  size="sm"
                  variant={selectedId === variant.id ? 'primary' : 'outline'}
                  onClick={() => handleSelectVariant(variant.id)}
                  disabled={isLoading}
                >
                  {selectedId === variant.id ? '✓ 已選擇' : '選擇'}
                </Button>
              </div>

              <p className="text-lg font-medium mb-2">{variant.seo_title}</p>

              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  {variant.reasoning}
                </p>

                <div className="flex flex-wrap gap-2">
                  {variant.keywords_focus.map((keyword, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      🔑 {keyword}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 自定義 SEO Title */}
        <div className="border-t pt-4">
          {showCustomInput ? (
            <div className="space-y-3">
              <label className="text-sm font-medium">自定義 SEO Title：</label>
              <input
                type="text"
                value={customTitle}
                onChange={(e) => setCustomTitle(e.target.value)}
                placeholder="輸入自定義的 SEO Title（建議 30 字以內）"
                className="w-full px-3 py-2 border rounded-lg"
                maxLength={60}
              />
              <div className="flex justify-between items-center">
                <span className="text-xs text-muted-foreground">
                  長度: {customTitle.length} 字
                </span>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setShowCustomInput(false);
                      setCustomTitle('');
                    }}
                  >
                    取消
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSaveCustom}
                    disabled={!customTitle.trim() || isLoading}
                  >
                    保存自定義標題
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <Button
              variant="outline"
              onClick={() => setShowCustomInput(true)}
              className="w-full"
            >
              ✏️ 自定義 SEO Title
            </Button>
          )}
        </div>

        {/* AI 優化建議 */}
        {notes.length > 0 && (
          <Alert>
            <AlertDescription>
              <p className="font-medium mb-2">💡 AI 優化建議：</p>
              <ul className="list-disc list-inside text-sm space-y-1">
                {notes.map((note, idx) => (
                  <li key={idx}>{note}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* 當前選中的 SEO Title 顯示 */}
        {currentSEOTitle && (
          <div className="border-t pt-4">
            <p className="text-sm font-medium text-muted-foreground mb-2">
              當前選中的 SEO Title：
            </p>
            <p className="text-lg font-semibold">{currentSEOTitle}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

#### 3.4 更新 ArticleParsingPage

**文件**：`frontend/src/pages/ArticleParsingPage.tsx`

在文件中新增 SEO Title 選擇元件的展示：

```typescript
// ... 在 imports 中新增
import SEOTitleSelectionCard from '../components/parsing/SEOTitleSelectionCard';

export default function ArticleParsingPage() {
  // ... 現有狀態 ...

  const [selectedSEOTitleId, setSelectedSEOTitleId] = useState<string | null>(null);
  const [currentSEOTitle, setCurrentSEOTitle] = useState<string | null>(null);

  // Mutation: 選擇 SEO Title
  const selectSEOTitleMutation = useMutation({
    mutationFn: (request: SEOTitleSelectionRequest) =>
      parsingAPI.selectSEOTitle(articleId, request),
    onSuccess: (data) => {
      setCurrentSEOTitle(data.data.seo_title);
      // 顯示成功提示
      toast.success('SEO Title 已更新');
    },
  });

  const handleSelectSEOTitleVariant = (variantId: string) => {
    setSelectedSEOTitleId(variantId);
    selectSEOTitleMutation.mutate({ variant_id: variantId });
  };

  const handleUseOriginalSEOTitle = () => {
    setSelectedSEOTitleId(null);
    selectSEOTitleMutation.mutate({ use_original: true });
  };

  const handleCustomSEOTitle = (customTitle: string) => {
    setSelectedSEOTitleId(null);
    selectSEOTitleMutation.mutate({ custom_seo_title: customTitle });
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* ... 現有內容 ... */}

      {/* Title & Author Card */}
      <Card>
        <CardHeader>
          <CardTitle>標題與作者</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* H1 標題 */}
          <div>
            <label className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              H1 標題（頁面顯示）
              <Badge variant="info">頁面內容</Badge>
            </label>
            <p className="text-2xl font-bold mt-1">
              {parsingData.full_title}
            </p>
          </div>

          {/* SEO Title（如果有原文提取） */}
          {parsingData.seo_title_extracted && parsingData.seo_title && (
            <div className="border-t pt-4">
              <label className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                SEO Title（搜尋引擎）
                <Badge variant="primary">原文提取</Badge>
              </label>
              <p className="text-xl font-semibold mt-1 text-blue-600">
                {parsingData.seo_title}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                從原文中標記為「這是 SEO title」的內容提取
              </p>
            </div>
          )}

          {/* ... 作者信息 ... */}
        </CardContent>
      </Card>

      {/* ... TitleOptimizationCard (H1) ... */}

      {/* SEO Title Selection Card（在優化建議生成後顯示） */}
      {(optimizationsData || generateOptimizationsMutation.data) && (
        <SEOTitleSelectionCard
          originalSEOTitle={parsingData.seo_title}
          seoTitleExtracted={parsingData.seo_title_extracted}
          suggestions={
            optimizationsData?.seo_title_suggestions?.variants ||
            generateOptimizationsMutation.data?.seo_title_suggestions?.variants ||
            []
          }
          notes={
            optimizationsData?.seo_title_suggestions?.notes ||
            generateOptimizationsMutation.data?.seo_title_suggestions?.notes ||
            []
          }
          currentSEOTitle={currentSEOTitle}
          onSelect={handleSelectSEOTitleVariant}
          onUseOriginal={handleUseOriginalSEOTitle}
          onCustom={handleCustomSEOTitle}
          isLoading={selectSEOTitleMutation.isPending}
        />
      )}

      {/* ... 其他內容 ... */}
    </div>
  );
}
```

### Phase 4: WordPress 發佈整合

#### 4.1 更新 WordPress 發佈邏輯

**文件**：`backend/src/services/article_importer/wordpress_importer.py`

```python
class WordPressImporter:
    """Service for publishing articles to WordPress."""

    async def publish_article(
        self,
        article: Article,
        wp_config: WordPressConfig,
    ) -> PublishResult:
        """Publish article to WordPress."""

        # 準備發佈數據
        post_data = self._prepare_post_data(article)

        # 使用 WordPress REST API 發佈
        response = await self._publish_to_wordpress(post_data, wp_config)

        return response

    def _prepare_post_data(self, article: Article) -> dict:
        """Prepare WordPress post data."""

        # 決定使用哪個標題作為 SEO Title
        seo_title = article.seo_title or article.title_main

        # H1 標題（頁面內容標題）
        h1_title = article.title

        return {
            'title': h1_title,  # WordPress 文章標題（H1）
            'content': article.body_html,
            'status': 'publish',
            'meta': {
                # Yoast SEO 或 Rank Math 外掛字段
                '_yoast_wpseo_title': seo_title,  # SEO Title Tag
                '_yoast_wpseo_metadesc': article.meta_description,
                '_yoast_wpseo_focuskw': article.seo_keywords[0] if article.seo_keywords else '',

                # 或者使用 Rank Math
                'rank_math_title': seo_title,
                'rank_math_description': article.meta_description,
                'rank_math_focus_keyword': article.seo_keywords[0] if article.seo_keywords else '',
            },
            'tags': article.tags,
            'categories': article.categories,
        }
```

### Phase 5: 測試計劃

#### 5.1 單元測試

**文件**：`backend/tests/services/test_article_parser_seo_title.py`

```python
import pytest
from src.services.parser.article_parser import ArticleParserService

class TestSEOTitleExtraction:
    """Test SEO title extraction from documents."""

    @pytest.mark.asyncio
    async def test_extract_seo_title_with_marker(self):
        """測試從標記中提取 SEO Title"""

        raw_html = """
        <html>
            <body>
                <h1>【專題報導】2024年醫療保健創新趨勢分析：從AI診斷到遠距醫療的全面突破</h1>
                <p>這是 SEO title：2024年AI醫療創新趨勢</p>
                <p>文／張三</p>
                <p>正文內容...</p>
            </body>
        </html>
        """

        parser = ArticleParserService(use_ai=False)
        result = parser.parse_document(raw_html)

        assert result.success
        assert result.parsed_article.seo_title == "2024年AI醫療創新趨勢"
        assert result.parsed_article.seo_title_extracted is True
        assert result.parsed_article.title_main == "2024年醫療保健創新趨勢分析"

    @pytest.mark.asyncio
    async def test_no_seo_title_marker(self):
        """測試沒有 SEO Title 標記時的處理"""

        raw_html = """
        <html>
            <body>
                <h1>2024年醫療保健創新趨勢</h1>
                <p>文／張三</p>
                <p>正文內容...</p>
            </body>
        </html>
        """

        parser = ArticleParserService(use_ai=False)
        result = parser.parse_document(raw_html)

        assert result.success
        assert result.parsed_article.seo_title is None
        assert result.parsed_article.seo_title_extracted is False

    @pytest.mark.asyncio
    async def test_ai_seo_title_generation(self, mock_anthropic_client):
        """測試 AI 生成 SEO Title 建議"""

        # Mock Claude API 回應
        mock_anthropic_client.messages.create.return_value = Mock(
            content=[Mock(text=json.dumps({
                "title_main": "2024年醫療保健創新趨勢",
                "seo_title": "2024年AI醫療創新突破",
                "seo_title_found": False,
                "body_html": "<p>...</p>",
                # ... 其他字段
            }))]
        )

        parser = ArticleParserService(
            use_ai=True,
            anthropic_api_key="test-key"
        )
        result = parser.parse_document(raw_html)

        assert result.success
        assert result.parsed_article.seo_title == "2024年AI醫療創新突破"
```

**文件**：`backend/tests/services/test_optimization_seo_title.py`

```python
import pytest
from src.services.optimization.unified_optimization_service import UnifiedOptimizationService

class TestSEOTitleSuggestions:
    """Test SEO title suggestions generation."""

    @pytest.mark.asyncio
    async def test_generate_seo_title_suggestions(self, sample_article):
        """測試生成 SEO Title 建議"""

        service = UnifiedOptimizationService(api_key="test-key")
        optimizations = await service.generate_all_optimizations(sample_article)

        # 驗證 SEO Title Suggestions 結構
        assert 'seo_title_suggestions' in optimizations
        seo_suggestions = optimizations['seo_title_suggestions']

        assert 'variants' in seo_suggestions
        assert len(seo_suggestions['variants']) >= 2
        assert len(seo_suggestions['variants']) <= 3

        # 驗證每個 variant 的結構
        for variant in seo_suggestions['variants']:
            assert 'id' in variant
            assert 'seo_title' in variant
            assert 'reasoning' in variant
            assert 'keywords_focus' in variant
            assert 'character_count' in variant

            # 驗證字數限制
            assert variant['character_count'] <= 60  # 30 中文字 ≈ 60 characters

    @pytest.mark.asyncio
    async def test_seo_title_differs_from_h1(self, sample_article):
        """測試 SEO Title 與 H1 的差異化"""

        service = UnifiedOptimizationService(api_key="test-key")
        optimizations = await service.generate_all_optimizations(sample_article)

        h1_main = optimizations['title_suggestions']['suggested_title_sets'][0]['main']
        seo_title = optimizations['seo_title_suggestions']['variants'][0]['seo_title']

        # SEO Title 應該與 H1 不完全相同（允許部分相似）
        assert seo_title != h1_main or len(seo_title) < len(h1_main)
```

#### 5.2 整合測試

**文件**：`backend/tests/integration/test_seo_title_workflow.py`

```python
import pytest
from httpx import AsyncClient

class TestSEOTitleWorkflow:
    """Test complete SEO title workflow from parsing to selection."""

    @pytest.mark.asyncio
    async def test_complete_seo_title_workflow(
        self,
        async_client: AsyncClient,
        sample_article_html: str,
    ):
        """測試完整的 SEO Title 工作流程"""

        # 1. 上傳並解析文章
        response = await async_client.post(
            "/api/v1/articles/parse",
            json={
                "raw_html": sample_article_html,
                "use_ai": True,
            }
        )
        assert response.status_code == 200
        article_id = response.json()['article_id']

        # 2. 確認解析結果
        response = await async_client.post(
            f"/api/v1/articles/{article_id}/confirm-parsing",
            json={
                "confirmed_by": "test_user",
                "feedback": "Confirmed"
            }
        )
        assert response.status_code == 200

        # 3. 等待 AI 優化生成（自動觸發）
        # 輪詢優化狀態
        for _ in range(10):
            response = await async_client.get(
                f"/api/v1/articles/{article_id}/optimization-status"
            )
            if response.json()['generated']:
                break
            await asyncio.sleep(2)

        # 4. 獲取優化建議
        response = await async_client.get(
            f"/api/v1/articles/{article_id}/optimizations"
        )
        assert response.status_code == 200
        optimizations = response.json()

        # 驗證 SEO Title 建議
        assert 'seo_title_suggestions' in optimizations
        variants = optimizations['seo_title_suggestions']['variants']
        assert len(variants) >= 2

        # 5. 選擇第一個 SEO Title 建議
        selected_variant_id = variants[0]['id']
        response = await async_client.post(
            f"/api/v1/articles/{article_id}/select-seo-title",
            json={
                "variant_id": selected_variant_id
            }
        )
        assert response.status_code == 200

        # 6. 驗證文章已更新
        response = await async_client.get(
            f"/api/v1/articles/{article_id}"
        )
        article = response.json()
        assert article['seo_title'] == variants[0]['seo_title']
        assert article['seo_title_source'] == 'ai_generated'
```

#### 5.3 前端 E2E 測試

**文件**：`frontend/e2e/seo-title-selection.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('SEO Title Selection Workflow', () => {
  test('should display and select SEO title suggestions', async ({ page }) => {
    // 1. 導航到文章解析頁面
    await page.goto('/articles/1/parsing');

    // 2. 觸發解析
    await page.click('button:has-text("開始解析")');

    // 3. 等待解析完成
    await page.waitForSelector('button:has-text("確認解析結果")');

    // 4. 確認解析結果
    await page.click('button:has-text("確認解析結果")');

    // 5. 等待 AI 優化建議生成
    await page.waitForSelector('text=AI 建議的 SEO Title 選項', {
      timeout: 40000, // 最多等待 40 秒
    });

    // 6. 驗證 SEO Title 選項顯示
    const seoTitleVariants = page.locator('[data-testid="seo-title-variant"]');
    await expect(seoTitleVariants).toHaveCount(3); // 應該有 2-3 個選項

    // 7. 選擇第一個 SEO Title
    await page.click('[data-testid="seo-title-variant"]:first-child button:has-text("選擇")');

    // 8. 驗證已選中
    await expect(page.locator('button:has-text("✓ 已選擇")')).toBeVisible();

    // 9. 驗證當前 SEO Title 更新
    const currentSEOTitle = page.locator('[data-testid="current-seo-title"]');
    await expect(currentSEOTitle).not.toBeEmpty();
  });

  test('should allow custom SEO title input', async ({ page }) => {
    // ... 前置步驟 ...

    // 點擊自定義按鈕
    await page.click('button:has-text("自定義 SEO Title")');

    // 輸入自定義 SEO Title
    const customTitle = '測試自定義 SEO Title';
    await page.fill('input[placeholder*="自定義"]', customTitle);

    // 保存
    await page.click('button:has-text("保存自定義標題")');

    // 驗證更新成功
    await expect(page.locator(`text=${customTitle}`)).toBeVisible();
  });

  test('should display extracted SEO title if available', async ({ page }) => {
    // 創建包含 SEO Title 標記的測試文章
    const articleWithSEOTitle = {
      raw_html: `
        <h1>測試標題</h1>
        <p>這是 SEO title：測試 SEO 標題</p>
        <p>正文內容...</p>
      `,
    };

    // ... 解析流程 ...

    // 驗證原文提取的 SEO Title 顯示
    await expect(page.locator('[data-testid="original-seo-title"]')).toContainText(
      '測試 SEO 標題'
    );
    await expect(page.locator('text=原文提取')).toBeVisible();

    // 使用原文 SEO Title
    await page.click('button:has-text("使用此標題")');

    // 驗證已選中
    await expect(page.locator('text=當前選中的 SEO Title')).toBeVisible();
  });
});
```

### Phase 6: 實施時間表

| 階段 | 任務 | 預估時間 | 優先級 |
|-----|------|---------|-------|
| **Phase 1** | 資料庫架構調整 | 2 天 | P0 (最高) |
| | - 新增 seo_title 字段到 articles 表 | 0.5 天 | |
| | - 更新 title_suggestions 表結構 | 0.5 天 | |
| | - 更新 Pydantic 模型 | 0.5 天 | |
| | - 資料庫遷移腳本 | 0.5 天 | |
| **Phase 2** | 後端 API 實施 | 4 天 | P0 |
| | - 更新 ArticleParserService 提取邏輯 | 1.5 天 | |
| | - 更新 UnifiedOptimizationService | 1.5 天 | |
| | - 新增 SEO Title 選擇 API 端點 | 1 天 | |
| **Phase 3** | 前端實施 | 3 天 | P1 |
| | - 更新前端類型定義 | 0.5 天 | |
| | - 新增 SEO Title 選擇元件 | 1.5 天 | |
| | - 整合到 ArticleParsingPage | 1 天 | |
| **Phase 4** | WordPress 發佈整合 | 1 天 | P1 |
| | - 更新 WordPress 發佈邏輯 | 1 天 | |
| **Phase 5** | 測試 | 3 天 | P1 |
| | - 單元測試 | 1 天 | |
| | - 整合測試 | 1 天 | |
| | - E2E 測試 | 1 天 | |
| **Phase 6** | 文檔與部署 | 1 天 | P2 |
| | - 更新 API 文檔 | 0.5 天 | |
| | - 部署到測試環境 | 0.25 天 | |
| | - 部署到生產環境 | 0.25 天 | |

**總計**：約 14 個工作日（約 3 週）

### Phase 7: 部署與驗證

#### 7.1 部署檢查清單

**資料庫遷移**：
```bash
# 1. 備份生產資料庫
pg_dump $PRODUCTION_DATABASE_URL > backup_before_seo_title.sql

# 2. 在測試環境執行遷移
alembic upgrade head

# 3. 驗證遷移成功
psql $DATABASE_URL -c "\d articles"  # 檢查新字段
psql $DATABASE_URL -c "\d title_suggestions"

# 4. 測試環境驗證通過後，生產環境執行
alembic upgrade head --sql > migration.sql  # 先生成 SQL
# 人工審查 SQL 後執行
psql $PRODUCTION_DATABASE_URL < migration.sql
```

**後端部署**：
```bash
# 1. 運行測試
pytest backend/tests/services/test_article_parser_seo_title.py
pytest backend/tests/services/test_optimization_seo_title.py
pytest backend/tests/integration/test_seo_title_workflow.py

# 2. 部署後端
gcloud run deploy cms-automation-backend \
  --source backend/ \
  --region us-central1

# 3. 驗證健康檢查
curl https://cms-backend.example.com/health
```

**前端部署**：
```bash
# 1. 運行 E2E 測試
npm run test:e2e -- seo-title-selection.spec.ts

# 2. 構建前端
npm run build

# 3. 部署到 GCS
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-cmsupload-476323/

# 4. 驗證部署
curl https://cms-frontend.example.com/
```

#### 7.2 驗證測試場景

**場景 1：原文包含 SEO Title 標記**
```
輸入：Google Doc HTML 包含「這是 SEO title：2024年AI醫療突破」
預期：
1. 解析後 seo_title = "2024年AI醫療突破"
2. seo_title_extracted = true
3. 前端顯示「原文提取」標籤
4. 用戶可選擇使用原文或 AI 建議
```

**場景 2：原文無 SEO Title 標記**
```
輸入：Google Doc HTML 僅包含 H1 標題
預期：
1. 解析後 seo_title = null
2. seo_title_extracted = false
3. AI 生成 2-3 個 SEO Title 建議
4. 用戶可選擇 AI 建議或自定義
```

**場景 3：選擇 AI 建議**
```
操作：用戶點擊「選擇」按鈕
預期：
1. POST /articles/{id}/select-seo-title
2. 文章 seo_title 更新為選中的 variant
3. seo_title_source = "ai_generated"
4. 前端顯示「✓ 已選擇」
```

**場景 4：自定義 SEO Title**
```
操作：用戶輸入「自定義測試 SEO Title」並保存
預期：
1. POST /articles/{id}/select-seo-title
2. 文章 seo_title = "自定義測試 SEO Title"
3. seo_title_source = "user_input"
4. 前端顯示當前選中的 SEO Title
```

**場景 5：WordPress 發佈**
```
操作：發佈文章到 WordPress
預期：
1. WordPress 文章標題 = H1 title (title_main)
2. Yoast SEO title = seo_title
3. 搜尋引擎抓取時顯示 seo_title
```

## 📊 成功指標

### 功能指標
- ✅ SEO Title 提取準確率 > 95%（有標記時）
- ✅ AI 生成 SEO Title 建議 2-3 個，每個 ≤ 30 字
- ✅ SEO Title 與 H1 差異化（非完全相同）
- ✅ 用戶可選擇原文/AI 建議/自定義

### 性能指標
- ⏱️ AI 解析時間 < 30 秒
- ⏱️ SEO Title 選擇 API 回應 < 500ms
- ⏱️ 前端頁面載入 < 2 秒

### 用戶體驗指標
- 🎯 用戶可清楚區分 SEO Title 與 H1
- 🎯 介面提供明確的優化建議
- 🎯 選擇流程簡單直觀（< 3 步）

## 🔧 維護與優化

### 監控
1. **解析成功率**：監控 seo_title_extracted 的比例
2. **用戶選擇偏好**：統計使用原文/AI 建議/自定義的比例
3. **SEO 效果**：追蹤發佈後的搜尋排名變化

### 未來優化方向
1. **AI 提示詞優化**：根據用戶反饋調整 SEO Title 生成策略
2. **A/B 測試**：測試不同 SEO Title 對點擊率的影響
3. **批次處理**：支援批次更新歷史文章的 SEO Title
4. **多語言支援**：擴展到英文、日文等其他語言

## 📚 相關文檔

- [Phase 7 Article Parsing 文檔](./backend/docs/phase7_article_parsing.md)
- [Phase 7 Unified Optimization 文檔](./backend/docs/phase7_unified_optimization.md)
- [WordPress 發佈整合文檔](./backend/docs/wordpress_integration.md)
- [資料庫架構文檔](./backend/docs/database_schema.md)

---

**文檔版本**：v1.0
**創建日期**：2025-01-14
**最後更新**：2025-01-14
**作者**：Claude Code AI Assistant
