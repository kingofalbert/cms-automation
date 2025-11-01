# Tags Feature - Phase 4 & 5 实施计划（修订版）

**修订原因**: 原计划错误地认为使用 WordPress REST API，实际上是使用 **Playwright/Computer Use 浏览器自动化**

**修订日期**: 2025-10-31
**状态**: 待实施

---

## 错误分析

### ❌ 原计划（错误）
- 使用 WordPress REST API 创建 tags/categories
- 调用 `/wp-json/wp/v2/tags` 和 `/wp-json/wp/v2/categories` 端点
- 获取 tag/category IDs 然后发布文章

### ✅ 正确方案
- 使用 **Playwright** 浏览器自动化
- 通过 **CSS 选择器** 定位 WordPress 编辑器界面元素
- **模拟人工操作** 填写 tags 和 categories 输入框
- WordPress 自动处理 tag/category 的创建和关联

---

## 当前实现分析

### Playwright WordPress Publisher

**文件**: `backend/src/services/providers/playwright_wordpress_publisher.py`

**现有发布流程**:
1. ✅ `_step_login()` - 登录 WordPress
2. ✅ `_step_navigate_to_new_post()` - 导航到新文章页面
3. ✅ `_step_set_title()` - 设置标题
4. ✅ `_step_upload_images()` - 上传图片（可选）
5. ✅ `_step_set_content()` - 设置正文内容
6. ✅ `_step_configure_seo()` - 配置 SEO（Yoast）
7. ✅ `_step_publish()` - 发布文章

**缺少的步骤**:
- ❌ `_step_set_tags()` - 设置 WordPress Tags
- ❌ `_step_set_categories()` - 设置 WordPress Categories

### 配置结构

配置在 `_get_default_config()` 方法中定义，包含：

```python
{
    "metadata": {...},
    "login": {...},
    "dashboard": {...},
    "editor": {
        "title_field": ".editor-post-title__input",
        "content_area": ".block-editor-default-block-appender__content",
        ...
    },
    "seo": {
        "panel": "#wpseo-metabox-root",
        "focus_keyword_field": "input[name='yoast_wpseo_focuskw']",
        "meta_description_field": "textarea[name='yoast_wpseo_metadesc']",
    },
    # ❌ 缺少 taxonomy 配置
    "waits": {...}
}
```

---

## Phase 4: Playwright Tags/Categories 自动化 (4h)

### 目标
更新 Playwright publisher 支持 tags 和 categories 的浏览器自动化

### 任务 4.1: 添加 Taxonomy 配置 (1h)

**文件**: `backend/src/services/providers/playwright_wordpress_publisher.py`

**变更**: 在 `_get_default_config()` 方法中添加 taxonomy 选择器

```python
def _get_default_config(self) -> Dict:
    return {
        # ... 现有配置 ...

        "taxonomy": {
            # Tags 区域（WordPress 标准编辑器）
            "tags_panel": ".components-panel__body.editor-post-taxonomies__panel",
            "tags_panel_toggle": "button[aria-label*='Tags']",
            "tags_input": "input.components-form-token-field__input",
            "tags_suggestions": ".components-form-token-field__suggestions-list",

            # Categories 区域
            "categories_panel": ".editor-post-taxonomies__hierarchical-terms-list",
            "categories_panel_toggle": "button[aria-label*='Categories']",
            "category_checkbox": "input[type='checkbox'][id^='editor-post-taxonomies__hierarchical-terms-choice-']",
            "category_add_new": "button.editor-post-taxonomies__hierarchical-terms-add",
            "category_new_name_input": "input[type='text'][id='editor-post-taxonomies__hierarchical-terms-input']",
        },

        "waits": {
            # ... 现有 waits ...
            "after_tag_input": 500,      # 输入 tag 后等待
            "after_category_select": 300,  # 选择 category 后等待
        }
    }
```

**WordPress 标准编辑器 (Gutenberg) Tags/Categories 位置**:
- Tags: 右侧边栏 → Document → Tags
- Categories: 右侧边栏 → Document → Categories

### 任务 4.2: 更新 `publish_article()` 方法签名 (0.5h)

**变更**: 添加 `tags` 和 `categories` 参数

```python
async def publish_article(
    self,
    cms_url: str,
    username: str,
    password: str,
    article_title: str,
    article_body: str,
    seo_data: SEOMetadata,
    tags: List[str] = None,              # 新增
    categories: List[str] = None,        # 新增
    article_images: List[Dict] = None,
    headless: bool = False,
) -> Dict[str, Any]:
```

### 任务 4.3: 实现 `_step_set_tags()` 方法 (1h)

**新增方法**:

```python
async def _step_set_tags(self, tags: List[str]) -> None:
    """Set WordPress post tags using Playwright automation.

    WordPress tags are free-form text that users can create on-the-fly.
    This method:
    1. Locates the Tags panel in the sidebar
    2. Opens it if collapsed
    3. Types each tag into the input field
    4. Presses Enter to create each tag

    Args:
        tags: List of tag names (3-6 recommended)
    """
    if not tags:
        logger.info("playwright_step_set_tags_skipped", reason="no_tags_provided")
        return

    logger.info("playwright_step_set_tags", count=len(tags))

    try:
        # Scroll to sidebar (tags are usually in the right sidebar)
        await self.page.evaluate("""
            const sidebar = document.querySelector('.edit-post-sidebar');
            if (sidebar) sidebar.scrollIntoView();
        """)
        await asyncio.sleep(0.5)

        # Open Tags panel if collapsed
        tags_panel_toggle = self.config["taxonomy"]["tags_panel_toggle"]
        try:
            # Check if panel is collapsed
            panel_button = await self.page.query_selector(tags_panel_toggle)
            if panel_button:
                is_expanded = await panel_button.get_attribute("aria-expanded")
                if is_expanded == "false":
                    await panel_button.click()
                    await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning("tags_panel_toggle_failed", error=str(e))

        # Locate tags input field
        tags_input = self.config["taxonomy"]["tags_input"]
        await self.page.wait_for_selector(tags_input, timeout=5000)

        # Input each tag
        for tag in tags:
            logger.debug(f"Adding tag: {tag}")

            # Click input field
            await self.page.click(tags_input)
            await asyncio.sleep(0.3)

            # Type tag name
            await self.page.keyboard.type(tag)
            await asyncio.sleep(self.config["waits"]["after_tag_input"] / 1000)

            # Press Enter to create tag
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(0.3)

        logger.info("playwright_tags_set", count=len(tags))

    except Exception as e:
        logger.warning(
            "set_tags_failed",
            error=str(e),
            tags=tags,
        )
        # Continue without tags - not critical
```

### 任务 4.4: 实现 `_step_set_categories()` 方法 (1h)

**新增方法**:

```python
async def _step_set_categories(self, categories: List[str]) -> None:
    """Set WordPress post categories using Playwright automation.

    WordPress categories are hierarchical and predefined.
    This method:
    1. Locates the Categories panel in the sidebar
    2. Opens it if collapsed
    3. Checks checkboxes for existing categories
    4. Creates new categories if needed

    Args:
        categories: List of category names (1-3 recommended)
    """
    if not categories:
        logger.info("playwright_step_set_categories_skipped", reason="no_categories_provided")
        return

    logger.info("playwright_step_set_categories", count=len(categories))

    try:
        # Scroll to sidebar
        await self.page.evaluate("""
            const sidebar = document.querySelector('.edit-post-sidebar');
            if (sidebar) sidebar.scrollIntoView();
        """)
        await asyncio.sleep(0.5)

        # Open Categories panel if collapsed
        categories_panel_toggle = self.config["taxonomy"]["categories_panel_toggle"]
        try:
            panel_button = await self.page.query_selector(categories_panel_toggle)
            if panel_button:
                is_expanded = await panel_button.get_attribute("aria-expanded")
                if is_expanded == "false":
                    await panel_button.click()
                    await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning("categories_panel_toggle_failed", error=str(e))

        # Wait for categories panel
        categories_panel = self.config["taxonomy"]["categories_panel"]
        await self.page.wait_for_selector(categories_panel, timeout=5000)

        for category in categories:
            logger.debug(f"Setting category: {category}")

            # Try to find existing category checkbox
            # Look for checkbox with label matching category name
            category_found = False

            # Get all category checkboxes
            checkboxes = await self.page.query_selector_all(
                f"{categories_panel} input[type='checkbox']"
            )

            for checkbox in checkboxes:
                # Get associated label
                checkbox_id = await checkbox.get_attribute("id")
                label = await self.page.query_selector(f"label[for='{checkbox_id}']")

                if label:
                    label_text = await label.inner_text()

                    if label_text.strip().lower() == category.lower():
                        # Found matching category - check it
                        is_checked = await checkbox.is_checked()
                        if not is_checked:
                            await checkbox.check()
                            await asyncio.sleep(self.config["waits"]["after_category_select"] / 1000)
                        category_found = True
                        break

            # If category doesn't exist, create it
            if not category_found:
                logger.debug(f"Category not found, creating: {category}")

                try:
                    # Click "Add New Category" button
                    add_new_button = self.config["taxonomy"]["category_add_new"]
                    await self.page.click(add_new_button)
                    await asyncio.sleep(0.5)

                    # Type new category name
                    new_category_input = self.config["taxonomy"]["category_new_name_input"]
                    await self.page.fill(new_category_input, category)
                    await asyncio.sleep(0.3)

                    # Submit (usually pressing Enter)
                    await self.page.keyboard.press("Enter")
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.warning(
                        "category_creation_failed",
                        category=category,
                        error=str(e),
                    )

        logger.info("playwright_categories_set", count=len(categories))

    except Exception as e:
        logger.warning(
            "set_categories_failed",
            error=str(e),
            categories=categories,
        )
        # Continue without categories - not critical
```

### 任务 4.5: 更新发布流程 (0.5h)

**文件**: `backend/src/services/providers/playwright_wordpress_publisher.py`

**变更**: 在 `publish_article()` 方法中添加新步骤

```python
async def publish_article(self, ..., tags=None, categories=None, ...):
    try:
        # ... 现有步骤 ...

        await self._step_login(cms_url, username, password)
        await self._step_navigate_to_new_post()
        await self._step_set_title(article_title)

        if article_images:
            uploaded_images = await self._step_upload_images(article_images)
            article_body = self._replace_image_references(article_body, uploaded_images)

        await self._step_set_content(article_body)

        # 新增: 设置 Tags 和 Categories
        if tags:
            await self._step_set_tags(tags)

        if categories:
            await self._step_set_categories(categories)

        await self._step_configure_seo(seo_data)
        article_url, article_id = await self._step_publish()

        # ... 其余代码 ...
```

---

## Phase 5: 服务层和 API 集成 (2h)

### 任务 5.1: 更新 Publishing Orchestrator (0.5h)

**文件**: `backend/src/services/publishing/orchestrator.py`

**目标**: 从 Article 或 WorklistItem 中提取 tags/categories 并传递给 Playwright publisher

**变更**:

```python
async def publish_article(
    self,
    task_id: int,
    article_id: int,
    provider: Provider,
    options: dict
) -> PublishTask:
    """Execute publishing workflow."""

    # Load article
    article = await self._load_article(article_id)

    # Extract tags and categories
    tags = article.tags or []
    categories = article.categories or []

    # Load SEO metadata
    seo_data = await self._load_seo_metadata(article_id)

    # Publish based on provider
    if provider == Provider.PLAYWRIGHT:
        publisher = await create_playwright_publisher()

        result = await publisher.publish_article(
            cms_url=self.settings.DEFAULT_WP_URL,
            username=self.settings.DEFAULT_WP_USERNAME,
            password=self.settings.DEFAULT_WP_PASSWORD,
            article_title=article.title,
            article_body=article.body,
            seo_data=seo_data,
            tags=tags,               # 新增
            categories=categories,   # 新增
            article_images=article.additional_images,
            headless=options.get("headless", False),
        )

    # ... 其他 provider 处理 ...
```

### 任务 5.2: 更新 Worklist 发布流程 (0.5h)

**文件**: `backend/src/api/routes/worklist_routes.py`

**目标**: 从 WorklistItem 发布时，将 tags/categories 复制到 Article

**变更**:

```python
@router.post("/worklist/{item_id}/publish")
async def publish_worklist_item(
    item_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Publish worklist item to WordPress."""

    # Load worklist item
    worklist_item = await session.get(WorklistItem, item_id)

    # Create Article from WorklistItem (if not exists)
    if not worklist_item.article_id:
        article = Article(
            title=worklist_item.title,
            body=worklist_item.content,
            author_id=1,  # TODO: get from session
            source="google_drive",
            status=ArticleStatus.IMPORTED,

            # 复制 taxonomy 数据
            tags=worklist_item.tags or [],
            categories=worklist_item.categories or [],
        )
        session.add(article)
        await session.commit()
        await session.refresh(article)

        # Create SEO metadata
        if worklist_item.meta_description or worklist_item.seo_keywords:
            seo_metadata = SEOMetadata(
                article_id=article.id,
                meta_description=worklist_item.meta_description,
                focus_keyword=worklist_item.seo_keywords[0] if worklist_item.seo_keywords else None,
                primary_keywords=worklist_item.seo_keywords[:3] if worklist_item.seo_keywords else [],
            )
            session.add(seo_metadata)
            await session.commit()

        # Link worklist item to article
        worklist_item.article_id = article.id
        await session.commit()

    # Create publish task
    # ... 现有逻辑 ...
```

### 任务 5.3: 端到端测试 (1h)

**测试流程**:

1. **准备测试文档** (YAML front matter):
```yaml
---
title: "Test Article with Tags and Categories"
meta_description: "This is a test article for validating tags and categories automation"
seo_keywords:
  - test automation
  - playwright tags
tags:
  - Automation Testing
  - WordPress Development
  - Playwright
categories:
  - Technology
  - Tutorial
---

This is the test article body content.
```

2. **上传到 Google Drive**:
   - 将文档上传到配置的 Google Drive 文件夹

3. **触发同步**:
   - 调用 `POST /api/v1/worklist/sync`
   - 验证 WorklistItem 创建成功
   - 验证 tags/categories 正确解析

4. **发布到 WordPress**:
   - 调用 `POST /api/v1/worklist/{id}/publish`
   - 选择 provider: `playwright`
   - 设置 `headless: false`（观察浏览器操作）

5. **验证结果**:
   - 检查 WordPress 文章是否创建成功
   - 验证 tags 是否正确设置
   - 验证 categories 是否正确设置
   - 验证 SEO meta description 和 keywords

---

## 技术细节

### WordPress Gutenberg 编辑器结构

**Tags 输入**:
```html
<div class="components-panel__body editor-post-taxonomies__panel">
  <button aria-expanded="true">Tags</button>
  <div class="components-panel__body-content">
    <div class="components-form-token-field">
      <input class="components-form-token-field__input" type="text" />
    </div>
  </div>
</div>
```

**Categories 选择**:
```html
<div class="components-panel__body editor-post-taxonomies__panel">
  <button aria-expanded="true">Categories</button>
  <div class="components-panel__body-content">
    <div class="editor-post-taxonomies__hierarchical-terms-list">
      <input type="checkbox" id="editor-post-taxonomies__hierarchical-terms-choice-1" />
      <label for="editor-post-taxonomies__hierarchical-terms-choice-1">Uncategorized</label>

      <input type="checkbox" id="editor-post-taxonomies__hierarchical-terms-choice-2" />
      <label for="editor-post-taxonomies__hierarchical-terms-choice-2">Technology</label>
    </div>
    <button class="editor-post-taxonomies__hierarchical-terms-add">Add New Category</button>
  </div>
</div>
```

### Playwright 操作模式

**Tags (自由输入)**:
1. 定位输入框
2. 输入 tag 文本
3. 按 Enter 键创建
4. WordPress 自动创建新 tag（如果不存在）

**Categories (预定义选择)**:
1. 查找现有 category checkbox
2. 如果存在，勾选
3. 如果不存在，点击 "Add New Category"
4. 输入新 category 名称
5. WordPress 创建新 category

---

## 风险与缓解

### 风险 1: CSS 选择器变化

**风险**: WordPress 更新后选择器可能失效

**缓解**:
- ✅ 使用配置文件，易于更新选择器
- ✅ 提供多个备选选择器
- ✅ 详细的错误日志
- 🔄 TODO: 添加选择器验证工具

### 风险 2: Tags/Categories 面板未展开

**风险**: 默认情况下面板可能折叠

**缓解**:
- ✅ 检测 `aria-expanded` 属性
- ✅ 自动展开面板
- ✅ 添加等待时间

### 风险 3: Tag/Category 名称冲突

**风险**: 用户输入的 tag/category 与现有的相似但不完全匹配

**缓解**:
- ✅ 使用精确匹配（`.lower()` 比较）
- ✅ 如果不匹配则创建新的
- 📖 文档建议用户检查现有 tags/categories

### 风险 4: 浏览器自动化超时

**风险**: 网络慢或服务器响应慢导致超时

**缓解**:
- ✅ 所有 `wait_for_selector` 都设置 timeout
- ✅ 可配置的等待时间
- ✅ 失败后继续发布（tags/categories 非关键）

---

## 文件变更清单

### Phase 4

1. ✅ `backend/src/services/providers/playwright_wordpress_publisher.py`:
   - 添加 taxonomy 配置
   - 添加 `_step_set_tags()` 方法
   - 添加 `_step_set_categories()` 方法
   - 更新 `publish_article()` 方法签名和流程

### Phase 5

2. ✅ `backend/src/services/publishing/orchestrator.py`:
   - 从 Article 提取 tags/categories
   - 传递给 Playwright publisher

3. ✅ `backend/src/api/routes/worklist_routes.py`:
   - 从 WorklistItem 复制 tags/categories 到 Article

4. ✅ 端到端测试脚本（新建）

**总计**: 3 个文件修改 + 1 个测试脚本

---

## 总结

### Phase 4: Playwright Tags/Categories 自动化

| 任务 | 时长 | 描述 |
|------|------|------|
| 4.1 添加 Taxonomy 配置 | 1h | 更新选择器配置 |
| 4.2 更新方法签名 | 0.5h | 添加 tags/categories 参数 |
| 4.3 实现 `_step_set_tags()` | 1h | Tags 浏览器自动化 |
| 4.4 实现 `_step_set_categories()` | 1h | Categories 浏览器自动化 |
| 4.5 更新发布流程 | 0.5h | 集成新步骤到流程 |
| **总计** | **4h** | |

### Phase 5: 服务层和 API 集成

| 任务 | 时长 | 描述 |
|------|------|------|
| 5.1 更新 Publishing Orchestrator | 0.5h | 传递 tags/categories |
| 5.2 更新 Worklist 发布流程 | 0.5h | 复制 taxonomy 数据 |
| 5.3 端到端测试 | 1h | 完整流程验证 |
| **总计** | **2h** | |

### 关键差异（修订前后）

| 方面 | ❌ 原计划（错误） | ✅ 修订计划（正确） |
|------|------------------|-------------------|
| **技术方案** | WordPress REST API | Playwright 浏览器自动化 |
| **Tag 创建** | POST /wp-json/wp/v2/tags | 输入框输入 + Enter 键 |
| **Category 创建** | POST /wp-json/wp/v2/categories | 勾选 checkbox 或点击 "Add New" |
| **依赖** | requests, WordPress 权限 | Playwright, CSS 选择器 |
| **实现位置** | 新建 wordpress_api.py | 修改 playwright_wordpress_publisher.py |
| **配置** | API endpoints, token | CSS selectors, waits |

---

**文档版本**: 2.0 (修订版)
**最后更新**: 2025-10-31 19:30
**状态**: 待实施
