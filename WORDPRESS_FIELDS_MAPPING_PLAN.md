# WordPress 字段映射與解析規劃

> 基於 Gemini Computer Use 腳本分析，對比現有系統的完整規劃

## 一、字段對照總覽

### 1. 已完全支持的字段

| PDF Schema | 我們的字段 | 解析來源 | 狀態 |
|------------|-----------|---------|------|
| `article_content.title` | `title` + `title_prefix` / `title_main` / `title_suffix` | Google Doc 檔名 + AI 解析 | ✅ |
| `article_content.subtitle` | `title_suffix` | AI 解析 | ✅ |
| `article_content.body_text` | `body` + `body_html` | Google Doc HTML 導出 | ✅ |
| `taxonomy.tags` | `tags: list[str]` | AI 解析從正文提取 | ✅ |
| `taxonomy.author` | `author_name` + `author_line` | AI 解析第一段 | ✅ |
| `seo_settings.seo_title` | `seo_title` + `seo_title_extracted` + `seo_title_source` | AI 解析 / 用戶輸入 | ✅ |
| `seo_settings.meta_description` | `meta_description` + `suggested_meta_description` | AI 解析 + AI 建議 | ✅ |
| `media.featured_image.file_path` | `featured_image_path` | Google Doc 圖片提取 | ✅ |
| `media.featured_image.caption` | `ArticleImage.caption` | AI 解析圖說 | ✅ |

### 2. 部分支持（需要增強）

| PDF Schema | 現有字段 | 缺失部分 | 優先級 |
|------------|---------|---------|--------|
| `taxonomy.primary_category` | `categories: list[str]` | 無主分類區分 | **高** |
| `taxonomy.secondary_categories` | `categories: list[str]` | 無層級結構 | 中 |
| `seo_settings.focus_keyword` | `seo_keywords: list[str]` | 無單一焦點 | 中 |

### 3. 完全缺失的字段

| PDF Schema | 用途 | 解析難度 | 優先級 |
|------------|------|---------|--------|
| `media.featured_image.alt_text` | SEO + 無障礙訪問 | 低 (AI 生成) | **高** |
| `media.featured_image.description` | WordPress 媒體庫 | 低 (AI 生成) | 中 |
| `article_content.internal_links` | 內部鏈接優化 | 高 (需要鏈接庫) | 低 |
| `article_content.cta_code` | Shortcode 注入 | 低 (模板化) | 低 |
| `media.embedded_video` | 視頻嵌入 | 中 (正則提取) | 中 |

---

## 二、需要新增的數據庫字段

### Phase 1: 高優先級字段 (建議立即實施)

```python
# backend/src/models/article.py

class Article(Base, TimestampMixin):
    # ... 現有字段 ...

    # ==================== 新增字段 ====================

    # 1. 主分類 (WordPress 必需)
    primary_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="WordPress primary category (主分類，從候選列表匹配)",
    )

    # 2. 焦點關鍵詞 (Yoast SEO 核心字段)
    focus_keyword: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Yoast SEO focus keyword (從 seo_keywords 中選取或 AI 推薦)",
    )
```

```python
# backend/src/models/article_image.py

class ArticleImage(Base, TimestampMixin):
    # ... 現有字段 ...

    # ==================== 新增字段 ====================

    # 3. 圖片替代文字 (SEO + 無障礙)
    alt_text: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Image alt text for SEO and accessibility",
    )

    # 4. 圖片描述 (WordPress 媒體庫)
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Image description for WordPress media library",
    )
```

### Phase 2: 中優先級字段 (後續實施)

```python
# backend/src/models/article.py

class Article(Base, TimestampMixin):
    # ... 現有字段 ...

    # 5. 嵌入視頻 (YouTube/Vimeo)
    embedded_videos: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Embedded videos: [{platform, video_id, embed_code, position}]",
    )

    # 6. 分類層級標記
    category_primary_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="ID of primary category in WordPress taxonomy",
    )
```

### Phase 3: 低優先級字段 (可選實施)

```python
# backend/src/models/article.py

class Article(Base, TimestampMixin):
    # ... 現有字段 ...

    # 7. 內部鏈接 (結構化存儲)
    internal_links: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Internal links: [{keyword, url, position}]",
    )

    # 8. CTA Shortcode
    cta_shortcode: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="WordPress shortcode for CTA button (e.g., [ept_ms...])",
    )
```

---

## 三、解析流程增強方案

### 現有解析流程

```
Google Doc → HTML 導出 → ArticleParserService.parse_document()
                              ↓
                        ParsedArticle 對象
                              ↓
                        存入 Article 表
```

### 增強後的解析流程

```
Google Doc → HTML 導出 → ArticleParserService.parse_document()
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
             基礎解析              增強解析 (新增)
         (title, body,           (primary_category,
          author, tags)           focus_keyword,
                                  alt_text, video)
                    ↓                   ↓
                    └─────────┬─────────┘
                              ↓
                        ParsedArticle 對象 (擴展)
                              ↓
                        存入 Article 表
```

### 3.1 主分類 (primary_category) 解析策略

**方案 A: 候選列表匹配 (推薦)**

```python
# 預定義的分類候選列表 (從 WordPress 導出)
CATEGORY_CANDIDATES = {
    "中國": ["中國時局", "中國經濟", "中國社會", "中國人權"],
    "國際": ["美國新聞", "歐洲", "亞太", "中東"],
    "財經": ["股市", "房地產", "科技財經"],
    "生活": ["健康", "美食", "旅遊", "時尚"],
    "文化": ["傳統文化", "藝術", "歷史"],
    # ... 完整列表從 WordPress 獲取
}

def match_primary_category(
    title: str,
    body: str,
    tags: list[str],
    categories_candidates: dict
) -> str | None:
    """
    基於內容匹配主分類

    優先級:
    1. 標題關鍵詞匹配
    2. 標籤與分類交集
    3. 正文內容 AI 分類
    """
    # 實現邏輯...
```

**方案 B: AI 分類 (備選)**

```python
CATEGORY_PROMPT = """
根據以下文章內容，從候選分類中選擇最合適的主分類：

候選分類：{category_list}

文章標題：{title}
文章摘要：{summary}

請只返回一個最匹配的分類名稱。
"""
```

### 3.2 焦點關鍵詞 (focus_keyword) 解析策略

```python
def extract_focus_keyword(
    seo_keywords: list[str],
    title: str,
    meta_description: str
) -> str | None:
    """
    從 SEO 關鍵詞中選取焦點關鍵詞

    選取邏輯:
    1. 優先選擇出現在標題中的關鍵詞
    2. 其次選擇出現在 meta_description 中的
    3. 最後選擇 seo_keywords[0]
    """
    if not seo_keywords:
        return None

    # 優先標題中的關鍵詞
    for kw in seo_keywords:
        if kw in title:
            return kw

    # 其次 meta_description 中的
    for kw in seo_keywords:
        if meta_description and kw in meta_description:
            return kw

    # 默認第一個
    return seo_keywords[0]
```

### 3.3 圖片 Alt Text 生成策略

```python
def generate_image_alt_text(
    caption: str | None,
    article_title: str,
    image_position: int
) -> str:
    """
    為圖片生成 alt text

    策略:
    1. 如果有 caption，基於 caption 生成
    2. 如果是首圖，使用文章標題
    3. 其他情況，使用 "圖{position}: {title}相關圖片"
    """
    if caption:
        # 清理 caption，移除圖片來源等
        clean_caption = re.sub(r'[（(].*?[）)]', '', caption).strip()
        if len(clean_caption) > 10:
            return clean_caption[:100]

    if image_position == 0:
        return f"{article_title} - 題圖"

    return f"{article_title} - 配圖{image_position}"
```

### 3.4 嵌入視頻提取策略

```python
VIDEO_PATTERNS = {
    "youtube": [
        r'<iframe[^>]*src=["\'].*?youtube\.com/embed/([^"\'?]+)',
        r'https?://(?:www\.)?youtube\.com/watch\?v=([^&\s]+)',
        r'https?://youtu\.be/([^?\s]+)',
    ],
    "vimeo": [
        r'<iframe[^>]*src=["\'].*?player\.vimeo\.com/video/(\d+)',
        r'https?://vimeo\.com/(\d+)',
    ],
}

def extract_embedded_videos(body_html: str) -> list[dict]:
    """
    從正文 HTML 中提取嵌入視頻

    返回:
    [
        {
            "platform": "youtube",
            "video_id": "abc123",
            "embed_code": "<iframe...>",
            "position": 3  # 段落位置
        }
    ]
    """
    videos = []
    for platform, patterns in VIDEO_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, body_html)
            for match in matches:
                videos.append({
                    "platform": platform,
                    "video_id": match.group(1),
                    "embed_code": generate_embed_code(platform, match.group(1)),
                    "position": calculate_position(body_html, match.start())
                })
    return videos
```

---

## 四、AI 解析 Prompt 增強

### 現有 Prompt 結構

```python
CURRENT_PROMPT = """
解析以下文章，提取：
- 標題 (title_prefix, title_main, title_suffix)
- 作者 (author_line, author_name)
- SEO 關鍵詞 (seo_keywords)
- 標籤 (tags)
- Meta Description
...
"""
```

### 增強後的 Prompt

```python
ENHANCED_PROMPT = """
解析以下文章，提取以下信息：

## 基礎信息
- 標題 (title_prefix, title_main, title_suffix)
- 作者 (author_line, author_name)

## SEO 信息
- SEO 關鍵詞 (seo_keywords): 5-8 個
- 焦點關鍵詞 (focus_keyword): 從關鍵詞中選最重要的 1 個
- Meta Description: 150-160 字符
- SEO 標題 (seo_title): 30 字左右

## 分類信息
候選主分類列表：{CATEGORY_CANDIDATES}
- 主分類 (primary_category): 從候選列表中選擇最匹配的 1 個
- 標籤 (tags): 3-6 個自然標籤

## 圖片信息 (對每張圖片)
- alt_text: 圖片替代文字，10-50 字
- description: 圖片描述，可選

## 多媒體
- embedded_videos: 識別文中的 YouTube/Vimeo 視頻

輸出 JSON 格式...
"""
```

---

## 五、實施計劃

### Phase 1: 數據庫遷移 (1-2 天)

1. 創建 Alembic 遷移腳本
2. 新增字段：
   - `Article.primary_category`
   - `Article.focus_keyword`
   - `ArticleImage.alt_text`
   - `ArticleImage.description`
3. 部署遷移

### Phase 2: 解析服務增強 (2-3 天)

1. 更新 `ParsedArticle` 數據結構
2. 增強 AI 解析 Prompt
3. 實現 `primary_category` 匹配邏輯
4. 實現 `focus_keyword` 選取邏輯
5. 實現 `alt_text` 生成邏輯

### Phase 3: API 和前端更新 (1-2 天)

1. 更新 API Schema
2. 前端解析確認頁面增加新字段編輯
3. WordPress 發布接口增加新字段

### Phase 4: 視頻和高級功能 (後續)

1. 視頻提取功能
2. 內部鏈接結構化
3. CTA Shortcode 模板

---

## 六、分類候選列表管理

### 建議方案

創建一個配置表或 JSON 文件來管理 WordPress 分類候選列表：

```python
# backend/src/config/wordpress_taxonomy.py

WORDPRESS_CATEGORIES = {
    "primary": [
        {"id": 1, "name": "中國時局", "slug": "china-politics"},
        {"id": 2, "name": "中國經濟", "slug": "china-economy"},
        {"id": 3, "name": "國際新聞", "slug": "world-news"},
        {"id": 4, "name": "美國新聞", "slug": "us-news"},
        {"id": 5, "name": "港台新聞", "slug": "hk-tw-news"},
        {"id": 6, "name": "財經", "slug": "finance"},
        {"id": 7, "name": "科技", "slug": "tech"},
        {"id": 8, "name": "健康", "slug": "health"},
        {"id": 9, "name": "生活", "slug": "life"},
        {"id": 10, "name": "文化", "slug": "culture"},
        # ... 從 WordPress 導出完整列表
    ],
    "keywords_mapping": {
        # 關鍵詞到分類的映射，用於自動匹配
        "中共": "中國時局",
        "習近平": "中國時局",
        "美國": "美國新聞",
        "川普": "美國新聞",
        "拜登": "美國新聞",
        "股市": "財經",
        "房價": "財經",
        "健康": "健康",
        "養生": "健康",
        # ...
    }
}
```

### 同步機制 (未來)

```python
async def sync_wordpress_categories():
    """
    從 WordPress REST API 同步分類列表

    調用頻率：每天一次或手動觸發
    """
    # GET /wp-json/wp/v2/categories
    pass
```

---

## 七、總結

### 立即實施 (Phase 1)

| 字段 | 模型 | 解析方式 |
|------|------|---------|
| `primary_category` | Article | 關鍵詞匹配 + AI 輔助 |
| `focus_keyword` | Article | 從 seo_keywords 選取 |
| `alt_text` | ArticleImage | 基於 caption 生成 |
| `description` | ArticleImage | 可選，AI 生成 |

### 後續實施

| 字段 | 模型 | 優先級 |
|------|------|--------|
| `embedded_videos` | Article | 中 |
| `internal_links` | Article | 低 |
| `cta_shortcode` | Article | 低 |

### 不需要實施

| 字段 | 原因 |
|------|------|
| `meta_info.action` | 我們用 status 狀態機管理 |
| `meta_info.target_site` | 由 PublishTask 處理 |

---

## 八、相關文件清單

需要修改的文件：

1. `backend/src/models/article.py` - 新增字段
2. `backend/src/models/article_image.py` - 新增字段
3. `backend/src/services/parser/article_parser.py` - 增強解析
4. `backend/src/services/parser/models.py` - ParsedArticle 結構
5. `backend/src/api/schemas/article.py` - API Schema
6. `backend/alembic/versions/xxx_add_wordpress_fields.py` - 遷移腳本
7. `frontend/src/components/ParsingConfirmation.tsx` - 前端編輯

---

*文檔創建日期: 2024-11-24*
*最後更新: 2024-11-24*
