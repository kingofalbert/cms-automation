# Tags Feature MVP 实施计划（Computer Use 优先）

**策略**: MVP 优先使用 **Computer Use**，后续迭代优化 **Playwright**
**原因**:
- ✅ Computer Use 开发快（自然语言指令，无需精确选择器）
- ✅ 灵活性强（自动适应不同 WordPress 主题）
- ✅ 快速验证业务流程
- ⚠️ 有成本（$0.20/篇左右）
- 🔄 后续用 Playwright 优化成本（降至 $0.02/篇）

**修订日期**: 2025-10-31
**状态**: MVP 实施中

---

## 实施优先级

### 🚀 Phase A: Computer Use MVP (2小时) - **优先实施**

**目标**: 快速支持 Tags/Categories 发布到 WordPress

**任务 A.1: 更新 Computer Use 指令** (1h)

**文件**: `backend/src/services/computer_use_cms.py`

**变更**: 在 `_build_wordpress_instructions()` 方法中添加 Tags/Categories 指令

```python
def _build_wordpress_instructions(
    self,
    cms_url: str,
    username: str,
    password: str,
    title: str,
    body: str,
    seo_data: SEOMetadata,
    tags: list[str] = None,              # 新增
    categories: list[str] = None,        # 新增
    article_images: list[dict] = None,
) -> str:
    """Build WordPress-specific instructions."""

    # ... 现有代码 ...

    # 添加 Tags/Categories 信息
    tags_info = ""
    if tags:
        tags_info = f"\n**WordPress Tags (add to article):**\n"
        for tag in tags:
            tags_info += f"  - {tag}\n"

    categories_info = ""
    if categories:
        categories_info = f"\n**WordPress Categories (select or create):**\n"
        for category in categories:
            categories_info += f"  - {category}\n"

    instructions = f"""You are an AI assistant helping to publish an article to WordPress with SEO, tags, and categories.

**Your Task:**
1. Navigate to WordPress admin and log in
2. Create a new post
3. Set article title and content
4. {'Upload article images' if article_images else 'Skip images'}
5. **Set WordPress Tags and Categories**  <-- 新增
6. Configure SEO metadata (Yoast/Rank Math)
7. Publish the article
8. Return the article URL and ID

**WordPress Details:**
- Admin URL: {cms_url}/wp-admin
- Username: {username}
- Password: {password}

**Article Content:**
Title: {title}
Body: {body[:500]}...{tags_info}{categories_info}

**SEO Configuration:**
- Focus Keyword: {seo_data.focus_keyword}
- Meta Description: {seo_data.meta_description}
- ...

**Step-by-Step Instructions:**

1-4. [现有登录、标题、内容步骤]

5. **Set WordPress Tags and Categories**
   {"- **Tags**: In the right sidebar, find the 'Tags' panel" if tags else "- Skip tags (none provided)"}
   {"  - Click 'Add New Tag' or type in the tags input field" if tags else ""}
   {"  - Enter each tag: " + ", ".join(tags) if tags else ""}
   {"  - Press Enter after each tag to create it" if tags else ""}
   {"  - WordPress will create new tags automatically if they don't exist" if tags else ""}
   {"  - Take a screenshot showing tags added" if tags else ""}

   {"- **Categories**: In the right sidebar, find the 'Categories' panel" if categories else "- Skip categories (none provided)"}
   {"  - Look for checkboxes of existing categories" if categories else ""}
   {"  - For each category: " + ", ".join(categories) if categories else ""}
   {"    a. If checkbox exists, check it" if categories else ""}
   {"    b. If not, click 'Add New Category' and create it" if categories else ""}
   {"  - Take a screenshot showing categories selected" if categories else ""}

6. **Configure SEO** (Yoast/Rank Math)
   [现有 SEO 配置步骤]

7. **Publish Article**
   [现有发布步骤]

**Important Notes:**
- Tags are free-form text - WordPress creates them automatically
- Categories may need to be created if they don't exist
- Take screenshots at each step for verification
- If panels are collapsed, click to expand them

**Full article body:**
{body}

**Start the task now!**
"""
    return instructions
```

**任务 A.2: 更新方法签名** (0.5h)

```python
async def publish_article_with_seo(
    self,
    article_title: str,
    article_body: str,
    seo_data: SEOMetadata,
    cms_url: str,
    cms_username: str,
    cms_password: str,
    cms_type: str = "wordpress",
    tags: list[str] = None,              # 新增
    categories: list[str] = None,        # 新增
    article_images: list[dict] = None,
) -> dict[str, Any]:
    """Publish article with SEO, tags, and categories."""

    # Build instructions with tags/categories
    instructions = self._build_cms_instructions(
        cms_type=cms_type,
        cms_url=cms_url,
        cms_username=cms_username,
        cms_password=cms_password,
        article_title=article_title,
        article_body=article_body,
        seo_data=seo_data,
        tags=tags,              # 传递
        categories=categories,  # 传递
        article_images=article_images or [],
    )

    # ... 其余逻辑不变 ...
```

**任务 A.3: 更新 Publishing Orchestrator** (0.5h)

**文件**: `backend/src/services/publishing/orchestrator.py`

```python
async def publish_article(self, task_id, article_id, provider, options):
    """Execute publishing workflow."""

    # Load article
    article = await self._load_article(article_id)
    seo_data = await self._load_seo_metadata(article_id)

    # Extract tags and categories
    tags = article.tags or []
    categories = article.categories or []

    # Publish with Computer Use (MVP)
    if provider == Provider.COMPUTER_USE:
        computer_use_service = await create_computer_use_cms_service()

        result = await computer_use_service.publish_article_with_seo(
            article_title=article.title,
            article_body=article.body,
            seo_data=seo_data,
            cms_url=self.settings.DEFAULT_WP_URL,
            cms_username=self.settings.DEFAULT_WP_USERNAME,
            cms_password=self.settings.DEFAULT_WP_PASSWORD,
            tags=tags,               # 新增
            categories=categories,   # 新增
            article_images=article.additional_images,
        )

    # ... 其他 provider 逻辑 ...
```

---

### 🔄 Phase B: Playwright 优化 (4小时) - **后续迭代**

**目标**: 降低成本，从 $0.20/篇 降至 $0.02/篇

这部分延后实施，详见 `TAGS_FEATURE_PHASE_4_5_REVISED.md`

---

## Computer Use vs Playwright 对比

### MVP 阶段 (使用 Computer Use)

| 特性 | Computer Use | Playwright |
|------|-------------|-----------|
| **开发速度** | ✅ 快（2小时） | ⚠️ 慢（4小时） |
| **实现难度** | ✅ 简单（自然语言） | ⚠️ 复杂（CSS 选择器） |
| **灵活性** | ✅ 高（自动适应） | ⚠️ 低（选择器可能失效） |
| **成本** | ⚠️ $0.20/篇 | ✅ $0/篇 |
| **成功率** | ✅ 95%+ | ⚠️ 80-85% |
| **调试** | ✅ 简单（有截图） | ⚠️ 复杂（需要检查选择器） |

### 优化阶段 (混合模式)

**策略**: Playwright 优先，失败时降级到 Computer Use

```python
# Phase B 实现的混合模式
async def publish_with_hybrid(article):
    try:
        # 先用 Playwright (免费)
        result = await playwright_publisher.publish(article)
        if result["success"]:
            return result  # 成功，成本 $0
    except Exception as e:
        logger.warning("playwright_failed", error=e)

    # 降级到 Computer Use (收费但可靠)
    result = await computer_use_service.publish(article)
    return result  # 成本 $0.20
```

**成本优化效果**:
- 假设 Playwright 成功率 85%
- 混合模式成本: `0.85 * $0 + 0.15 * $0.20 = $0.03/篇`
- 比纯 Computer Use 降低 **85%** 成本

---

## Computer Use 指令优化技巧

### 1. 详细的步骤说明

```python
# ✅ Good
"""
5. **Set WordPress Tags**
   - In the right sidebar, scroll down to find 'Tags' panel
   - If panel is collapsed, click the panel header to expand
   - Find the text input field labeled 'Add New Tag'
   - Type the first tag: {tags[0]}
   - Press Enter key to create the tag
   - Repeat for remaining tags: {tags[1:]}\n"""

# ❌ Bad
"5. Set tags: {tags}"
```

### 2. 提供视觉线索

```python
# ✅ Good
"""
- Look for a panel with a 'Tags' icon (usually a tag symbol 🏷️)
- The tags input field is usually a white text box
- After pressing Enter, the tag should appear as a colored pill/badge\n"""
```

### 3. 错误处理指导

```python
# ✅ Good
"""
- If 'Tags' panel is not visible, try scrolling the sidebar down
- If you can't find tags, check if the theme uses a different location
- Take a screenshot if you're stuck - we can debug later
- If tags are not critical, you can skip and continue publishing\n"""
```

### 4. 成功验证

```python
# ✅ Good
"""
- After adding all tags, take a screenshot showing:
  1. All tags appear as colored badges/pills below the input
  2. Tag count matches the number provided ({len(tags)} tags)
- If any tag failed to create, note it in your final response\n"""
```

---

## MVP 测试计划

### 测试 1: 基础 Tags/Categories

**YAML 文档**:
```yaml
---
title: "Computer Use MVP Test - Basic Tags"
tags:
  - Testing
  - Automation
categories:
  - Technology
---
Test content here.
```

**预期结果**:
- ✅ Tags "Testing" 和 "Automation" 创建成功
- ✅ Category "Technology" 选择或创建成功
- ✅ 文章发布成功
- ✅ 截图显示 tags/categories 正确设置

### 测试 2: 多个 Categories

**YAML 文档**:
```yaml
---
title: "Computer Use MVP Test - Multiple Categories"
tags:
  - Tutorial
  - Guide
  - Beginner
categories:
  - Technology
  - Tutorial
  - WordPress
---
Test content here.
```

**预期结果**:
- ✅ 3 个 tags 创建
- ✅ 3 个 categories 选择/创建
- ✅ WordPress 正确显示层级关系

### 测试 3: 中文 Tags/Categories

**YAML 文档**:
```yaml
---
title: "测试中文标签和分类"
tags:
  - 芳香疗法
  - 家居香氛
  - 健康生活
categories:
  - 健康与保健
  - 生活方式
---
测试内容。
```

**预期结果**:
- ✅ 中文 tags 正确创建
- ✅ 中文 categories 正确处理
- ✅ UTF-8 编码正确

---

## 成本分析

### MVP 阶段 (纯 Computer Use)

**假设**: 每月发布 100 篇文章

| 项目 | 数值 |
|------|------|
| 每篇成本 | $0.20 |
| 月发布量 | 100 篇 |
| **月成本** | **$20** |
| 年成本 | $240 |

### 优化后 (Playwright + Computer Use 混合)

**假设**: Playwright 成功率 85%

| 项目 | 数值 |
|------|------|
| Playwright 成功 | 85 篇 × $0 = $0 |
| Computer Use 降级 | 15 篇 × $0.20 = $3 |
| **月成本** | **$3** |
| 年成本 | $36 |
| **成本降低** | **85%** |

### ROI 分析

| 阶段 | 开发时间 | 月运营成本 | 累计成本 (6个月) |
|------|---------|-----------|----------------|
| MVP (Computer Use) | 2h | $20/月 | $120 |
| 优化 (混合模式) | +4h | $3/月 | $18 |
| **节省** | - | -$17/月 | **$102** |

**结论**: 即使优化开发需要额外 4 小时，6 个月后累计节省 $102，ROI 非常高。

---

## 实施时间表

### Week 1: MVP (Computer Use)

| Day | 任务 | 时长 |
|-----|------|------|
| Day 1 | 更新 Computer Use 指令 | 1h |
| Day 1 | 更新方法签名和 Orchestrator | 0.5h |
| Day 1 | 端到端测试（英文） | 0.5h |
| Day 2 | 端到端测试（中文） | 0.5h |
| Day 2 | 调整指令优化成功率 | 0.5h |
| **总计** | **MVP 完成** | **3h** |

### Week 2-3: 验证和优化指令

- 收集真实使用数据
- 优化指令提示（提高成功率）
- 修复边缘情况

### Week 4+: Playwright 优化（可选）

- 实施 Playwright tags/categories 自动化
- 实施混合模式（Playwright 优先 + Computer Use 降级）
- 成本降低 85%

---

## 文件变更清单

### Phase A: Computer Use MVP (优先)

1. ✅ `backend/src/services/computer_use_cms.py`:
   - 更新 `_build_wordpress_instructions()` 添加 tags/categories 指令
   - 更新 `publish_article_with_seo()` 方法签名

2. ✅ `backend/src/services/publishing/orchestrator.py`:
   - 从 Article 提取 tags/categories
   - 传递给 Computer Use service

3. ✅ 端到端测试脚本

**总计**: 2 个文件修改 + 测试

### Phase B: Playwright 优化 (后续)

详见 `TAGS_FEATURE_PHASE_4_5_REVISED.md`

---

## 风险与缓解

### 风险 1: Computer Use 成功率低于预期

**预期**: 95%+ 成功率
**缓解**:
- ✅ 详细的步骤说明
- ✅ 视觉线索和错误处理指导
- ✅ 截图验证每一步
- ✅ 如果失败，提供详细日志

### 风险 2: Tags/Categories 面板找不到

**缓解**:
- ✅ 指令中提供多个查找方式
- ✅ 提供视觉描述（图标、颜色）
- ✅ 允许跳过（非关键功能）

### 风险 3: 成本超预算

**当前成本**: $0.20/篇 × 100 篇/月 = $20/月

**缓解**:
- ✅ 设置成本告警
- ✅ 监控发布成功率
- ✅ 优先实施 Playwright 优化（如果成本高）

---

## 下一步行动

### 立即开始 (MVP)

1. ✅ 更新 `computer_use_cms.py` 添加 tags/categories 指令
2. ✅ 更新 `publishing/orchestrator.py` 传递参数
3. ✅ 创建测试文档并测试
4. ✅ 验证成功率 > 90%

### 后续优化 (Week 4+)

1. 🔄 实施 Playwright tags/categories 自动化
2. 🔄 实施混合模式（Playwright + Computer Use）
3. 🔄 监控成本降低效果

---

## 总结

### MVP 策略优势

1. ✅ **快速上线**: 2-3 小时即可完成
2. ✅ **低风险**: Computer Use 成功率高
3. ✅ **灵活**: 自动适应不同 WordPress 主题
4. ✅ **可迭代**: 后续优化成本

### 成本 vs 速度权衡

| 方案 | 开发时间 | 月成本 | 何时选择 |
|------|---------|--------|---------|
| Computer Use MVP | 2-3h | $20 | ✅ 现在（验证流程） |
| Playwright 完整 | 6-8h | $0 | 🔄 后续（优化成本） |
| 混合模式 | 8-10h | $3 | 🔄 长期（最佳方案） |

**推荐路径**: MVP → 混合模式

---

**文档版本**: 1.0 (MVP 优先)
**最后更新**: 2025-10-31 20:00
**状态**: 准备实施 Phase A
