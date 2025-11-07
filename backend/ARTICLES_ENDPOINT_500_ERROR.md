# Articles Endpoint 500 Error - 问题分析报告

## 问题摘要

`/v1/articles` endpoint 返回 HTTP 500 错误，而其他相关的 endpoints 都已成功修复并正常工作。

## 问题表现

### 错误响应

```bash
$ curl -s https://cms-automation-backend-baau2zqeqq-ue.a.run.app/v1/articles
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "request_id": "8a844e83-294c-4ddf-9854-b8411f0d20e5"
}

HTTP Status: 500
```

### 其他 Endpoints 状态对比

| Endpoint | Status | Response |
|----------|--------|----------|
| `/v1/settings` | ✅ 200 | 正常返回配置数据 |
| `/v1/worklist` | ✅ 200 | `{"items":[],"total":0,...}` |
| `/v1/publish/tasks` | ✅ 200 | `{"items":[],"total":0,...}` |
| `/v1/articles` | ❌ 500 | Internal Server Error |

## 背景上下文

### 最近完成的修复

#### 1. 数据库迁移问题（已解决）
- **问题**：迁移执行但未创建表（Docker 缓存问题）
- **修复**：在 `run_migrations.sh` 中添加 `-v "$(pwd):/code"` 挂载
- **结果**：所有16个表成功创建在 Supabase

#### 2. Worklist Endpoint 500错误（已解决）
- **问题**：Column name mismatch (`drive_metadata` vs `metadata`)
- **根因**：
  - 数据库列名：`metadata`
  - Python 属性名：`drive_metadata`
  - SQLAlchemy 无法自动映射
- **修复**：添加显式列名映射
  ```python
  drive_metadata: Mapped[dict] = mapped_column(
      "metadata",  # Database column name
      JSONType,
      nullable=False,
      default=dict,
      comment="Drive metadata (links, owners, custom fields)",
  )
  ```
- **文件**：`src/models/worklist.py:100-106`

### 当前部署状态

- **Backend Revision**: `cms-automation-backend-00011-wc4`
- **部署时间**: 2025-11-05
- **数据库**: Supabase PostgreSQL (16 tables)
- **Platform**: GCP Cloud Run (us-east1)

## 已完成的调查工作

### 1. Article 模型检查 ✓

**文件**: `src/models/article.py`

模型定义看起来正确：

```python
class Article(Base, TimestampMixin):
    """Generated article content."""

    __tablename__ = "articles"

    # ... other fields ...

    # Metadata - 使用正确的字段名
    article_metadata: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="CMS-specific metadata (featured image, excerpt, etc.)",
    )
```

**关键点**：
- 字段名为 `article_metadata`（不是 `metadata`）
- 这是经过重命名迁移后的正确名称

### 2. 数据库迁移历史检查 ✓

**相关迁移**：

1. **20251025_0200**: 创建 articles 表，列名为 `metadata`
2. **3824f61361b3** (`20251026_0232_rename_metadata_to_article_metadata.py`):
   - 将 `metadata` 列重命名为 `article_metadata`
   - 迁移已成功执行（见日志）

**迁移日志确认**：
```
INFO  [alembic.runtime.migration] Running upgrade 20251025_0200 -> 3824f61361b3, rename_metadata_to_article_metadata
```

### 3. Article Schema 检查 ✓

**文件**: `src/api/schemas/article.py`

```python
class ArticleResponse(TimestampSchema):
    """Schema for article response."""

    # ... other fields ...
    article_metadata: dict  # ✓ 使用正确的字段名
    formatting: dict
```

```python
class ArticleListResponse(BaseSchema):
    """Schema for article list response."""

    articles: list[ArticleResponse]
    total: int
```

**关键点**：Schema 正确使用 `article_metadata`

### 4. Article Routes 检查 ✓

**文件**: `src/api/routes/articles.py`

**List Articles Endpoint** (line 29-42):
```python
@router.get("", response_model=list[ArticleListResponse])
async def list_articles(
    skip: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
) -> list[Article]:
    """List articles."""
    result = await session.execute(
        select(Article)
        .order_by(Article.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
```

**其他代码片段**使用 `article_metadata` (line 83-85, 107):
```python
article.article_metadata = _merge_proofreading_metadata(
    article.article_metadata, result.model_dump(mode="json")
)

# ...

metadata = dict(article.article_metadata or {})
```

**关键点**：
- 代码正确使用 `article.article_metadata`
- 查询逻辑看起来标准且简单

### 5. 与 Worklist 对比

**Worklist Endpoint** (working):
- 遇到过相同类型的问题（column name mismatch）
- 通过添加显式列名映射解决

**可能的相似性**：
- 是否存在其他字段的映射问题？
- 是否有关联查询导致的问题？

## 数据库当前状态

### Articles 表结构

基于迁移定义，articles 表应该有以下列：

```sql
-- Expected columns (from migrations)
- id (integer, primary key)
- title (varchar(500))
- body (text)
- status (enum: ArticleStatus)
- author_id (integer)
- source (varchar(50))
- featured_image_path (varchar(500), nullable)
- additional_images (jsonb, nullable)
- tags (array of varchar(100), nullable)
- categories (array of varchar(100), nullable)
- proofreading_issues (jsonb)
- critical_issues_count (integer)
- cms_article_id (varchar(255), nullable, unique)
- published_url (varchar(500), nullable)
- published_at (timestamp, nullable)
- article_metadata (jsonb) -- 重命名后的列名
- formatting (jsonb)
- created_at (timestamp)
- updated_at (timestamp)
```

**关键问题**：
- ✅ 迁移日志显示重命名迁移已执行
- ❓ 实际数据库列名是否真的是 `article_metadata`？
- ❓ 还是仍然是 `metadata`？

## 可能的根因分析

### 假设 1: 列名实际未重命名

**可能原因**：
- Alembic 的 `ALTER COLUMN ... RENAME TO` 可能在某些情况下失败但不报错
- PostgreSQL 权限问题导致重命名未生效

**验证方法**：
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'articles'
  AND column_name IN ('metadata', 'article_metadata');
```

**如果是这个问题**：
需要在 Article 模型中添加显式列名映射：
```python
article_metadata: Mapped[dict] = mapped_column(
    "metadata",  # Database column name (if rename failed)
    JSONB,
    nullable=False,
    default=dict,
    comment="CMS-specific metadata",
)
```

### 假设 2: Response Model 序列化问题

**可能原因**：
- ArticleResponse schema 期望某个字段，但数据库返回的 Article 对象缺失该字段
- 关联对象（如 `seo_metadata`, `publish_tasks`）加载失败

**验证方法**：
- 检查是否有空数据库（0条记录）时仍然500错误
- 添加异常捕获查看具体错误

### 假设 3: 关联关系加载问题

**Article 模型的关系**：
```python
# Relationships
seo_metadata: Mapped[Optional["SEOMetadata"]] = relationship(...)
publish_tasks: Mapped[list["PublishTask"]] = relationship(...)
uploaded_files: Mapped[list["UploadedFile"]] = relationship(...)
proofreading_histories: Mapped[list["ProofreadingHistory"]] = relationship(...)
proofreading_decisions: Mapped[list["ProofreadingDecision"]] = relationship(...)
```

**可能问题**：
- 某个关联表缺失或结构不匹配
- 关联查询失败导致整体序列化失败

### 假设 4: ENUM 类型问题

**ArticleStatus ENUM**：
```python
class ArticleStatus(str, PyEnum):
    IMPORTED = "imported"
    DRAFT = "draft"
    IN_REVIEW = "in-review"
    SEO_OPTIMIZED = "seo_optimized"
    READY_TO_PUBLISH = "ready_to_publish"
    PUBLISHING = "publishing"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
```

**可能问题**：
- 数据库中的 enum 类型定义与代码不一致
- 序列化时 enum 值处理出错

## 需要进一步调查的方向

### 1. 验证数据库实际列名 [CRITICAL]

```sql
-- 在 Supabase SQL Editor 中执行
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'articles'
ORDER BY ordinal_position;
```

**期望结果**：应该看到 `article_metadata`，而不是 `metadata`

### 2. 检查 Cloud Run 日志

访问 GCP Console 查看详细错误堆栈：
```
https://console.cloud.google.com/run/detail/us-east1/cms-automation-backend/logs?project=cmsupload-476323
```

筛选条件：
- Severity: ERROR
- Text search: "articles" 或 request_id "8a844e83-294c-4ddf-9854-b8411f0d20e5"

### 3. 添加临时调试代码

在 `src/api/routes/articles.py` 的 `list_articles` 函数中：

```python
@router.get("", response_model=list[ArticleListResponse])
async def list_articles(
    skip: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
) -> list[Article]:
    """List articles."""
    try:
        logger.info(f"Listing articles: skip={skip}, limit={limit}")

        result = await session.execute(
            select(Article)
            .order_by(Article.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        articles = list(result.scalars().all())
        logger.info(f"Found {len(articles)} articles")

        # Test serialization
        for article in articles:
            logger.info(f"Article {article.id}: status={article.status}, has_metadata={hasattr(article, 'article_metadata')}")

        return articles

    except Exception as e:
        logger.error(f"Error listing articles: {type(e).__name__}: {str(e)}", exc_info=True)
        raise
```

### 4. 测试空数据库场景

当前数据库可能是空的（0条记录），验证是否即使没有数据也会500：

```bash
# 应该返回空数组，而不是500
curl https://cms-automation-backend-baau2zqeqq-ue.a.run.app/v1/articles
```

### 5. 检查所有相关表是否存在

```sql
-- 验证所有关联表都存在
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'articles',
    'seo_metadata',
    'publish_tasks',
    'uploaded_files',
    'proofreading_histories',
    'proofreading_decisions',
    'topic_requests'
  )
ORDER BY table_name;
```

## 相关文件清单

### 模型文件
- `src/models/article.py` - Article ORM 模型定义
- `src/models/worklist.py` - WorklistItem 模型（已修复的参考）

### 路由文件
- `src/api/routes/articles.py` - Articles API endpoints

### Schema 文件
- `src/api/schemas/article.py` - Article request/response schemas

### 迁移文件
- `migrations/versions/20251025_0200_create_article_models.py` - 创建 articles 表（使用 `metadata`）
- `migrations/versions/20251026_0232_rename_metadata_to_article_metadata.py` - 重命名列
- `migrations/versions/20251026_1229_add_multi_provider_architecture_tables.py` - 创建关联表

## 建议的修复步骤

### 优先级 1: 验证数据库列名

1. 在 Supabase SQL Editor 中执行：
   ```sql
   SELECT column_name FROM information_schema.columns
   WHERE table_name = 'articles' AND column_name LIKE '%metadata%';
   ```

2. 如果返回 `metadata` 而不是 `article_metadata`：
   - 说明重命名迁移未生效
   - 需要在 Article 模型添加显式映射

### 优先级 2: 查看 Cloud Run 错误日志

获取完整的错误堆栈，确定具体是哪行代码、什么操作导致的错误。

### 优先级 3: 根据日志调整修复方案

根据实际错误信息选择对应的修复方案。

## 对比参考：Worklist 的成功修复

**问题特征对比**：

| 特征 | Worklist | Articles |
|------|----------|----------|
| 错误代码 | 500 | 500 |
| 根因 | Column name mismatch | ❓ 待确认 |
| 数据库列名 | `metadata` | ❓ `metadata` 或 `article_metadata` |
| Python 属性名 | `drive_metadata` | `article_metadata` |
| 修复方法 | 添加显式列名映射 | ❓ 待确定 |
| 相关迁移 | 无重命名迁移 | 有重命名迁移（可能失败） |

**如果是相同问题**，修复代码应该是：

```python
# src/models/article.py
article_metadata: Mapped[dict] = mapped_column(
    "metadata",  # ← 添加这行，指定实际的数据库列名
    JSONB,
    nullable=False,
    default=dict,
    comment="CMS-specific metadata (featured image, excerpt, etc.)",
)
```

## 总结

**核心疑问**：数据库中 articles 表的实际列名是 `metadata` 还是 `article_metadata`？

**验证命令**：
```sql
\d articles  -- PostgreSQL
-- 或
SELECT column_name FROM information_schema.columns WHERE table_name = 'articles';
```

**最可能的根因**：与 Worklist 相同，重命名迁移虽然执行了，但实际列名未改变，导致 SQLAlchemy 映射失败。

**建议优先行动**：
1. 验证数据库实际列名
2. 查看 Cloud Run 错误日志
3. 根据结果决定是否需要添加显式列名映射
