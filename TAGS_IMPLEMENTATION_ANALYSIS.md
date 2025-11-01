# Tags 功能实现分析文档

**日期**: 2025-10-31
**需求**: 在从 Google Drive 导入文章时支持 Tags，区分于 SEO Keywords

---

## 1. SEO Keywords vs Tags 核心区别

根据提供的 PDF 文档，主要区别如下：

| 维度 | SEO Keywords | Tags |
|------|--------------|------|
| **目的** | 提升搜索引擎可见度 | 改善网站内部导航 |
| **面向对象** | 搜索引擎（Google/Bing） | 访客用户 |
| **设置位置** | SEO 插件（Yoast/Rank Math） | WordPress 文章编辑页"标签"栏 |
| **影响范围** | 外部搜索结果（Meta、URL、内容优化） | 内部网站结构（内部链接、归档页面） |
| **数量建议** | 1-3 个核心关键词 | 3-6 个自然分类 |
| **最佳实践** | <ul><li>主关键词：核心主题</li><li>长尾关键词：具体搜索意图</li><li>密度 1-2%，避免堆砌</li></ul> | <ul><li>自然词汇分类</li><li>建立文章关联</li><li>避免每篇都创建新标签</li><li>定期清理重复标签</li></ul> |

### 技术实现差异

**SEO Keywords**:
- 存储在 `seo_metadata` 表
- 字段：`focus_keyword`, `primary_keywords`, `secondary_keywords`
- 影响 WordPress SEO 插件（Yoast/Rank Math）的 meta 数据
- 用于搜索引擎优化

**Tags**:
- 存储在 `articles` 表（需新增）
- WordPress 原生分类系统
- 用于内部导航和相关文章推荐
- 提高网站停留时间和内部链接结构

---

## 2. 现有架构分析

### 2.1 数据库模型现状

#### Article Model (`backend/src/models/article.py`)

**现有字段** (相关部分):
```python
class Article(Base, TimestampMixin):
    id: Mapped[int]
    title: Mapped[str]
    body: Mapped[str]  # Content
    status: Mapped[ArticleStatus]
    source: Mapped[str]

    # 元数据字段
    article_metadata: Mapped[dict]  # JSONB

    # 关系
    seo_metadata: Mapped[Optional["SEOMetadata"]]  # 1:1
```

**缺失字段**:
- ❌ `tags` - WordPress Tags
- ❌ `categories` - WordPress Categories

#### SEOMetadata Model (`backend/src/models/seo.py`)

**现有字段**:
```python
class SEOMetadata(Base, TimestampMixin):
    focus_keyword: Mapped[str]              # 主关键词
    primary_keywords: Mapped[List[str]]     # 3-5 个主要关键词
    secondary_keywords: Mapped[List[str]]   # 5-10 个次要关键词
    meta_title: Mapped[str]
    meta_description: Mapped[str]
    # ...
```

**功能**: SEO 优化专用，不包含 WordPress 原生 Tags

#### WorklistItem Model (需查看)

让我查看 WorklistItem 的结构：

---

### 2.2 前端类型定义

#### Article Type (`frontend/src/types/article.ts`)

```typescript
export interface Article {
  id: string;
  title: string;
  content: string;
  status: ArticleStatus;
  tags?: string[];        // ✅ 已定义
  categories?: string[];  // ✅ 已定义
  seo_metadata?: SEOMetadata;
  // ...
}
```

#### SEOMetadata Type

```typescript
export interface SEOMetadata {
  meta_title: string;
  meta_description: string;
  focus_keyword: string;
  keywords?: string[];  // SEO Keywords
  // ...
}
```

**结论**: 前端已经区分 `tags` 和 SEO `keywords`

---

### 2.3 Google Drive 同步服务

**文件**: `backend/src/services/google_drive/sync_service.py`

**现有解析逻辑** (`_parse_document_content`):
```python
def _parse_document_content(self, content: str) -> dict[str, Any]:
    """Parse raw document content into structured data."""
    lines = [line.strip() for line in content.splitlines()]
    lines = [line for line in lines if line]

    # 简单解析：第一行作为标题，其余作为正文
    title = lines[0][:500] if lines else "Untitled Document"
    body = "\n".join(lines[1:]) if len(lines) > 1 else ""

    return {
        "title": title,
        "content": body,
        "author": None,
        "notes": [],
    }
```

**问题**:
- ❌ 没有解析 Meta Description
- ❌ 没有解析 SEO Keywords
- ❌ 没有解析 Tags
- ❌ 没有解析 Categories
- ⚠️ 只是简单的行解析，没有结构化格式

---

## 3. 实施方案设计

### 3.1 数据库架构更新

#### 方案 A: 在 Article 表添加字段（推荐）

**优点**:
- 符合 WordPress 数据模型（wp_posts + wp_term_relationships）
- 查询性能好（无需 JOIN）
- 前端已有对应类型定义

**实施**:

```python
# backend/src/models/article.py

from sqlalchemy import ARRAY, String

class Article(Base, TimestampMixin):
    # ... existing fields ...

    # WordPress taxonomy fields
    tags: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        default=list,
        comment="WordPress post tags (3-6 natural categories for internal navigation)",
    )

    categories: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        default=list,
        comment="WordPress post categories (hierarchical taxonomy)",
    )
```

**Alembic Migration**:
```python
# migrations/versions/YYYYMMDD_HHMM_add_tags_categories_to_articles.py

"""Add tags and categories to articles

Revision ID: abc123
Revises: previous_revision
Create Date: 2025-10-31

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column('articles',
        sa.Column('tags', postgresql.ARRAY(sa.String(100)), nullable=True)
    )
    op.add_column('articles',
        sa.Column('categories', postgresql.ARRAY(sa.String(100)), nullable=True)
    )

def downgrade():
    op.drop_column('articles', 'categories')
    op.drop_column('articles', 'tags')
```

#### 方案 B: 存储在 article_metadata JSONB（不推荐）

**缺点**:
- 无法高效查询和索引
- 不符合 WordPress 数据模型
- 不利于未来扩展

---

### 3.2 Google Drive 文档格式规范

为了从 Google Drive 文档中提取结构化信息，需要定义文档格式。

#### 推荐格式（YAML Front Matter）

```markdown
---
title: Essential Oil Diffuser Benefits
meta_description: Discover the top benefits of using essential oil diffusers...
seo_keywords:
  - essential oil diffuser
  - aromatherapy benefits
  - home fragrance
tags:
  - Aromatherapy
  - Home Fragrance
  - Wellness Tips
  - Essential Oils
categories:
  - Health & Wellness
  - Home & Living
author: John Doe
---

# Essential Oil Diffuser Benefits

Aromatherapy has become increasingly popular...
```

**优点**:
- 标准化格式（Jekyll/Hugo/Hexo 通用）
- 易于解析（PyYAML）
- 清晰区分元数据和正文
- 支持所有需要的字段

#### 替代格式（HTML 注释）

```html
<!--
META_DESCRIPTION: Discover the top benefits of using essential oil diffusers...
SEO_KEYWORDS: essential oil diffuser, aromatherapy benefits, home fragrance
TAGS: Aromatherapy, Home Fragrance, Wellness Tips, Essential Oils
CATEGORIES: Health & Wellness, Home & Living
AUTHOR: John Doe
-->

<h1>Essential Oil Diffuser Benefits</h1>
<p>Aromatherapy has become increasingly popular...</p>
```

---

### 3.3 解析服务更新

#### 更新 `_parse_document_content` 方法

```python
# backend/src/services/google_drive/sync_service.py

import re
import yaml  # pip install PyYAML

def _parse_document_content(self, content: str) -> dict[str, Any]:
    """Parse raw document content with YAML front matter support."""

    # 尝试解析 YAML front matter
    yaml_match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)

    if yaml_match:
        # 有 YAML front matter
        front_matter_raw, body_content = yaml_match.groups()
        try:
            metadata = yaml.safe_load(front_matter_raw)
        except yaml.YAMLError as e:
            logger.warning(f"YAML parsing failed: {e}")
            metadata = {}

        return {
            "title": metadata.get("title", "Untitled Document")[:500],
            "content": body_content.strip(),
            "meta_description": metadata.get("meta_description"),
            "seo_keywords": metadata.get("seo_keywords", []),
            "tags": metadata.get("tags", []),
            "categories": metadata.get("categories", []),
            "author": metadata.get("author"),
            "notes": [],
        }
    else:
        # 降级到简单解析（向后兼容）
        lines = [line.strip() for line in content.splitlines()]
        lines = [line for line in lines if line]

        title = lines[0][:500] if lines else "Untitled Document"
        body = "\n".join(lines[1:]) if len(lines) > 1 else ""

        return {
            "title": title,
            "content": body,
            "meta_description": None,
            "seo_keywords": [],
            "tags": [],
            "categories": [],
            "author": None,
            "notes": [],
        }
```

---

### 3.4 Worklist → Article 转换流程

当从 Worklist 发布文章到 WordPress 时，需要转换数据：

```python
# backend/src/services/worklist/publisher.py (新建)

from src.models import Article, SEOMetadata, WorklistItem
from sqlalchemy.ext.asyncio import AsyncSession

async def publish_worklist_to_article(
    worklist_item: WorklistItem,
    session: AsyncSession
) -> Article:
    """Convert WorklistItem to Article and create SEO metadata."""

    # 1. 创建 Article
    article = Article(
        title=worklist_item.title,
        body=worklist_item.content,
        status=ArticleStatus.READY_TO_PUBLISH,
        source="google_drive",
        author_id=1,  # TODO: Map from worklist author
        tags=worklist_item.tags,  # 🆕 Tags
        categories=worklist_item.categories,  # 🆕 Categories
        article_metadata={
            "worklist_id": worklist_item.id,
            "drive_file_id": worklist_item.drive_file_id,
        },
    )
    session.add(article)
    await session.flush()

    # 2. 创建 SEO Metadata（如果有）
    if worklist_item.seo_keywords:
        seo_meta = SEOMetadata(
            article_id=article.id,
            meta_title=worklist_item.title[:60],
            meta_description=worklist_item.meta_description or "",
            focus_keyword=worklist_item.seo_keywords[0] if worklist_item.seo_keywords else "",
            primary_keywords=worklist_item.seo_keywords[:5],
            secondary_keywords=[],  # TODO: Generate if needed
        )
        session.add(seo_meta)

    await session.commit()
    await session.refresh(article)

    return article
```

---

### 3.5 WordPress 发布集成

确保发布到 WordPress 时正确设置 Tags：

```python
# backend/src/services/providers/wordpress_publisher.py

async def publish_to_wordpress(article: Article, wp_config: dict):
    """Publish article to WordPress with tags and categories."""

    # WordPress REST API 格式
    post_data = {
        "title": article.title,
        "content": article.body,
        "status": "publish",

        # SEO Keywords → WordPress meta (via Yoast/Rank Math)
        "meta": {
            "_yoast_wpseo_focuskw": article.seo_metadata.focus_keyword if article.seo_metadata else "",
            "_yoast_wpseo_metadesc": article.seo_metadata.meta_description if article.seo_metadata else "",
        },

        # Tags → WordPress Tags (taxonomy: post_tag)
        "tags": await _resolve_tag_ids(article.tags, wp_config),

        # Categories → WordPress Categories (taxonomy: category)
        "categories": await _resolve_category_ids(article.categories, wp_config),
    }

    # POST to WordPress REST API
    response = await wp_client.post("/wp-json/wp/v2/posts", json=post_data)
    return response.json()

async def _resolve_tag_ids(tag_names: List[str], wp_config: dict) -> List[int]:
    """Convert tag names to WordPress tag IDs (create if not exist)."""
    tag_ids = []
    for tag_name in tag_names:
        # GET /wp-json/wp/v2/tags?search={tag_name}
        existing = await wp_client.get(f"/wp-json/wp/v2/tags?search={tag_name}")
        if existing:
            tag_ids.append(existing[0]["id"])
        else:
            # POST /wp-json/wp/v2/tags
            new_tag = await wp_client.post("/wp-json/wp/v2/tags", json={"name": tag_name})
            tag_ids.append(new_tag["id"])
    return tag_ids
```

---

## 4. API 更新

### 4.1 Pydantic Schemas 更新

```python
# backend/src/api/schemas/article.py

from pydantic import BaseModel, Field
from typing import List, Optional

class ArticleCreate(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = Field(default=[], max_length=6)  # 🆕
    categories: Optional[List[str]] = Field(default=[], max_length=3)  # 🆕
    # ...

class ArticleResponse(BaseModel):
    id: int
    title: str
    content: str
    tags: List[str]  # 🆕
    categories: List[str]  # 🆕
    seo_metadata: Optional[SEOMetadataResponse]
    # ...
```

### 4.2 Worklist API 更新

```python
# backend/src/api/schemas/worklist.py

class WorklistItemCreate(BaseModel):
    title: str
    content: str
    meta_description: Optional[str] = None
    seo_keywords: List[str] = []  # SEO Keywords
    tags: List[str] = []  # WordPress Tags (🆕)
    categories: List[str] = []  # WordPress Categories (🆕)
```

---

## 5. 实施步骤总结

### Phase 1: 数据库更新（2h）
1. ✅ 更新 `Article` model 添加 `tags` 和 `categories` 字段
2. ✅ 创建 Alembic migration
3. ✅ 运行 migration
4. ✅ 更新 Pydantic schemas

### Phase 2: Google Drive 解析更新（4h）
1. ✅ 安装 PyYAML: `pip install PyYAML`
2. ✅ 更新 `_parse_document_content` 支持 YAML front matter
3. ✅ 添加单元测试验证解析逻辑
4. ✅ 创建文档格式规范说明

### Phase 3: Worklist Model 更新（3h）
1. ✅ 更新 `WorklistItem` model 添加 tags/categories 字段
2. ✅ 更新 `_upsert_worklist_item` 方法保存 tags/categories
3. ✅ 更新 API schemas
4. ✅ 测试完整同步流程

### Phase 4: WordPress 发布集成（4h）
1. ✅ 实现 `_resolve_tag_ids` 和 `_resolve_category_ids`
2. ✅ 更新 WordPress API 调用包含 tags/categories
3. ✅ 区分 SEO Keywords（Yoast meta）和 Tags（WordPress taxonomy）
4. ✅ 测试发布流程

### Phase 5: 前端集成（2h）
1. ✅ 验证前端 Article type 已支持 tags/categories
2. ✅ 更新 Worklist Detail Drawer 显示 tags
3. ✅ 更新 Article Import 表单支持 tags 输入
4. ✅ 测试端到端流程

**总计**: 15 小时

---

## 6. 测试用例

### 6.1 Google Drive 文档示例

**文件名**: `essential-oil-diffuser.md`

```markdown
---
title: Essential Oil Diffuser Benefits
meta_description: Discover the amazing benefits of essential oil diffusers for your home, health, and well-being.
seo_keywords:
  - essential oil diffuser
  - aromatherapy benefits
  - home fragrance
tags:
  - Aromatherapy
  - Home Fragrance
  - Wellness Tips
  - Essential Oils
categories:
  - Health & Wellness
  - Home & Living
author: Jane Smith
---

# Essential Oil Diffuser Benefits

Essential oil diffusers have become a popular way to enjoy aromatherapy...

## Health Benefits
...

## Home Benefits
...
```

### 6.2 预期数据流

1. **Google Drive → Worklist**:
   ```json
   {
     "title": "Essential Oil Diffuser Benefits",
     "content": "# Essential Oil Diffuser Benefits\n\nEssential oil diffusers...",
     "meta_description": "Discover the amazing benefits...",
     "seo_keywords": ["essential oil diffuser", "aromatherapy benefits", "home fragrance"],
     "tags": ["Aromatherapy", "Home Fragrance", "Wellness Tips", "Essential Oils"],
     "categories": ["Health & Wellness", "Home & Living"],
     "author": "Jane Smith"
   }
   ```

2. **Worklist → Article**:
   ```python
   Article(
     title="Essential Oil Diffuser Benefits",
     body="# Essential Oil Diffuser Benefits...",
     tags=["Aromatherapy", "Home Fragrance", "Wellness Tips", "Essential Oils"],
     categories=["Health & Wellness", "Home & Living"],
     seo_metadata=SEOMetadata(
       focus_keyword="essential oil diffuser",
       primary_keywords=["essential oil diffuser", "aromatherapy benefits", "home fragrance"],
       meta_description="Discover the amazing benefits..."
     )
   )
   ```

3. **Article → WordPress**:
   ```json
   {
     "title": "Essential Oil Diffuser Benefits",
     "content": "<h1>Essential Oil Diffuser Benefits</h1>...",
     "tags": [12, 45, 78, 91],  // Tag IDs resolved from names
     "categories": [5, 8],        // Category IDs
     "meta": {
       "_yoast_wpseo_focuskw": "essential oil diffuser",
       "_yoast_wpseo_metadesc": "Discover the amazing benefits..."
     }
   }
   ```

---

## 7. 最佳实践建议

### 7.1 Tags 管理策略

1. **预定义 Tag 体系**:
   - 创建 Tag 管理页面（`/tags`）
   - 维护 3-6 个核心 Tag 类别
   - 定期清理低价值 Tags

2. **Tag 验证规则**:
   ```python
   @validator('tags')
   def validate_tags(cls, v):
       if len(v) > 6:
           raise ValueError("Maximum 6 tags allowed")
       if len(v) < 3:
           logger.warning("Recommended 3-6 tags, got {len(v)}")
       return v
   ```

3. **Tag 标准化**:
   ```python
   def normalize_tags(tags: List[str]) -> List[str]:
       """Normalize tag names (title case, trim whitespace)."""
       return [tag.strip().title() for tag in tags if tag.strip()]
   ```

### 7.2 SEO Keywords vs Tags 使用指南

**SEO Keywords**:
- ✅ 用于搜索引擎排名优化
- ✅ 主关键词：文章核心主题
- ✅ 长尾关键词：具体搜索意图
- ✅ 示例：`essential oil diffuser benefits`, `how to use aromatherapy diffuser`

**Tags**:
- ✅ 用于网站内部导航
- ✅ 自然分类词汇
- ✅ 建立文章间关联
- ✅ 示例：`Aromatherapy`, `Home Fragrance`, `Wellness Tips`

---

## 8. 未来扩展

### 8.1 智能 Tag 推荐

使用 AI 自动推荐 Tags：

```python
async def suggest_tags(article: Article) -> List[str]:
    """Use Claude to suggest relevant tags based on content."""
    prompt = f"""
    Based on this article content, suggest 3-6 WordPress tags for internal navigation:

    Title: {article.title}
    Content: {article.body[:500]}...

    Requirements:
    - Natural category words (not full sentences)
    - Help readers discover similar content
    - Different from SEO keywords

    Respond with just the tags, comma-separated.
    """
    # Call Claude API...
```

### 8.2 Tag 关联分析

```python
def get_related_articles_by_tags(article: Article, limit: int = 5) -> List[Article]:
    """Find related articles sharing similar tags."""
    # PostgreSQL array overlap query
    query = select(Article).where(
        Article.tags.overlap(article.tags)
    ).limit(limit)
```

---

## 9. 风险和注意事项

### 9.1 数据迁移

- ⚠️ 现有文章的 tags 字段为 NULL
- 💡 建议：提供批量 Tag 生成工具
- 💡 或：从 article_metadata 中迁移（如果有存储）

### 9.2 WordPress 兼容性

- ⚠️ 不同 WordPress 安装可能有不同的 Tag taxonomy
- 💡 建议：缓存 WordPress Tag IDs
- 💡 建议：处理 Tag 创建失败的情况

### 9.3 性能考虑

- ⚠️ Tag 解析（WordPress API 调用）可能较慢
- 💡 建议：批量查询 Tags（一次请求）
- 💡 建议：本地缓存 Tag ID 映射

---

## 10. 总结

### 实施优先级

1. **P0 - 必须实现**:
   - Article model 添加 tags/categories 字段
   - Google Drive 文档解析 YAML front matter
   - WordPress 发布时设置 Tags

2. **P1 - 建议实现**:
   - Tag 验证和标准化
   - 智能 Tag 推荐
   - Tag 管理界面

3. **P2 - 未来优化**:
   - Tag 关联分析
   - Tag 使用统计
   - 批量 Tag 更新工具

### 技术债务

- 需要明确区分 SEO Keywords 和 Tags 的使用场景
- 需要文档化 Google Drive 文档格式规范
- 需要培训用户正确使用 Tags vs Keywords

### 成功指标

- ✅ Google Drive 文档能正确解析 Tags
- ✅ Worklist 能显示和编辑 Tags
- ✅ 发布到 WordPress 时 Tags 正确设置
- ✅ SEO Keywords 和 Tags 功能互不干扰
- ✅ 用户能理解和正确使用两种分类系统

---

**文档版本**: 1.0
**最后更新**: 2025-10-31
**负责人**: Backend Team
**预计完成时间**: 15 小时（约 2 个工作日）
