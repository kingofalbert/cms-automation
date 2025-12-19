# Playwright vs Computer Use 方案对比与配置指南

## 🆚 两种方案对比

### Anthropic Computer Use (智能AI方案) 🤖

**工作原理：**
```
Claude看屏幕截图 → 理解界面 → 推理下一步 → 执行操作
```

**优点 ✅**
- 🧠 **智能适应**：能理解不同的WordPress主题和布局
- 🔄 **灵活处理**：界面变化了也能找到按钮
- 🛠️ **自动修复**：遇到错误能自己尝试解决
- 📝 **简单配置**：只需提供文字说明即可

**缺点 ❌**
- 💰 **费用**：每次发布约 $0.10-0.50
- ⏱️ **较慢**：需要AI推理时间（2-5分钟/篇）
- 🎲 **不确定性**：成功率约85-95%

**适合场景：**
- WordPress主题经常更新
- 需要处理复杂的自定义界面
- 预算充足
- 发布量不大（<100篇/月）

---

### Playwright + Chrome DevTools (精确脚本方案) 🎭

**工作原理：**
```
读取预设脚本 → 精确定位元素 → 机械执行操作
```

**优点 ✅**
- 💵 **完全免费**：无任何API费用
- ⚡ **极快**：30秒-2分钟/篇
- 🎯 **确定性**：配置对了100%成功
- 📊 **可预测**：每次操作完全一致

**缺点 ❌**
- 🔧 **配置复杂**：需要精确的CSS选择器
- 💔 **脆弱**：界面变化后需要重新配置
- 🚫 **无智能**：不会处理意外情况
- ⏰ **维护成本**：WordPress更新后可能需要调整

**适合场景：**
- WordPress主题稳定不变
- 大量发布需求（>100篇/月）
- 预算有限
- 技术能力强（能配置CSS选择器）

---

## 📊 成本对比（假设发布100篇文章）

| 方案 | 单篇成本 | 100篇总成本 | 配置时间 | 维护成本 |
|------|---------|------------|---------|---------|
| **Computer Use** | $0.20 | $20 | 10分钟 | 很低 |
| **Playwright** | $0 | $0 | 2-4小时 | 中等 |

**结论：**
- 发布 < 100篇：用 Computer Use（省时间）
- 发布 > 500篇：用 Playwright（省钱）
- 100-500篇：看你更看重时间还是钱

---

## 🛠️ Playwright 完整配置流程

### 步骤1️⃣：提取WordPress选择器（最重要！）

1. **登录你的WordPress后台**

2. **打开浏览器开发者工具**
   - 按 `F12` 或右键 → "检查"

3. **切换到Console标签**

4. **复制粘贴选择器提取工具**
   - 打开文件：`/backend/tools/extract_wordpress_selectors.js`
   - 全选复制整个脚本
   - 粘贴到Console中，按回车

5. **按提示操作**
   ```
   选项1：自动检测（快速，但可能不完整）
   运行：autoDetect()

   选项2：手动分步提取（推荐，完整准确）
   第1步：step1_extractLoginSelectors()
         → 在登录页面运行 step1_complete()

   第2步：step2_extractDashboardSelectors()
         → 在仪表盘运行 step2_complete()

   第3步：step3_extractEditorSelectors()
         → 点击"新建文章"后运行 step3_complete()

   第4步：step4_extractMediaSelectors()
         → 打开媒体上传后运行 step4_complete()

   第5步：step5_extractSEOSelectors()
         → 找到SEO面板后运行 step5_complete()

   完成：showResults()
         → 自动复制JSON配置到剪贴板
   ```

6. **保存配置文件**
   - 创建文件：`/backend/config/wordpress_selectors.json`
   - 粘贴刚才复制的JSON配置

### 步骤2️⃣：验证配置

提取到的JSON应该类似这样：

```json
{
  "metadata": {
    "wordpress_version": "WordPress 6.4",
    "editor_type": "Gutenberg",  // 或 "Classic Editor" - 见下方生产环境说明
    "seo_plugin": "Yoast SEO",   // 或 "Lite SEO" - 见下方生产环境说明
    "extracted_at": "2025-01-15T10:30:00Z"
  },
  "login": {
    "username_field": "#user_login",
    "password_field": "#user_pass",
    "submit_button": "#wp-submit"
  },
  "dashboard": {
    "posts_menu": "#menu-posts",
    "new_post_link": "#menu-posts a[href*='post-new']"
  },
  "editor": {
    "title_field": ".editor-post-title__input",
    "content_area": ".block-editor-default-block-appender__content",
    "add_block_button": ".block-editor-inserter__toggle"
  },
  "seo": {
    "focus_keyword_field": "input[name='yoast_wpseo_focuskw']",
    "meta_description_field": "textarea[name='yoast_wpseo_metadesc']"
  },
  "publish": {
    "publish_button": ".editor-post-publish-button__button"
  },
  "waits": {
    "after_login": 2000,
    "editor_load": 5000,
    "after_type": 500,
    "media_upload": 3000,
    "before_publish": 1000
  }
}
```

### 步骤3️⃣：集成到代码

修改 `computer_use_tasks.py` 使用Playwright：

```python
# 在文件顶部添加导入
from src.services.providers.playwright_wordpress_publisher import (
    create_playwright_publisher
)

# 在 publish_article_with_computer_use_task 函数中
# 替换这部分：
# computer_use_service = ComputerUseCMSService()

# 改为：
config_path = "/app/config/wordpress_selectors.json"
playwright_publisher = await create_playwright_publisher(config_path)

# 发布文章
publish_result = await playwright_publisher.publish_article(
    cms_url=cms_url,
    username=cms_username,
    password=cms_password,
    article_title=article.title,
    article_body=article.body,
    seo_data=seo_data,
    article_images=article_images,
    headless=True,  # 无头模式（后台运行）
)
```

### 步骤4️⃣：安装Playwright依赖

```bash
# 进入backend容器
docker compose exec backend bash

# 安装Playwright
pip install playwright

# 安装浏览器
playwright install chromium
playwright install-deps
```

### 步骤5️⃣：测试

```bash
# 测试发布
curl -X POST http://localhost:8000/v1/computer-use/publish \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 123,
    "cms_type": "wordpress"
  }'
```

---

## 🔧 配置优化技巧

### 技巧1：找不到元素怎么办？

**问题：** CSS选择器不工作

**解决方案：**
1. 打开Chrome DevTools
2. 在Elements标签中找到该元素
3. 右键元素 → Copy → Copy selector
4. 粘贴到配置文件

**示例：**
```json
// 如果默认的 ".editor-post-title__input" 不工作
// 用DevTools找到新的选择器
"title_field": "textarea.editor-post-title__input.wp-block-post-title"
```

### 技巧2：等待时间太短/太长

**调整等待时间：**
```json
"waits": {
  "after_login": 3000,      // 登录慢？增加到3秒
  "editor_load": 8000,      // 编辑器加载慢？增加到8秒
  "media_upload": 5000      // 图片上传慢？增加到5秒
}
```

### 技巧3：处理iframe

**如果编辑器在iframe中：**
```python
# 在 playwright_wordpress_publisher.py 中添加：
async def _step_set_content(self, content: str):
    # 切换到iframe
    frame = self.page.frame(name="editor-frame")
    if frame:
        await frame.click(self.config["editor"]["content_area"])
        await frame.keyboard.type(content)
    else:
        # 正常处理
        await self.page.click(self.config["editor"]["content_area"])
        await self.page.keyboard.type(content)
```

### 技巧4：不同主题的配置

**Elementor主题：**
```json
{
  "metadata": {
    "editor_type": "Elementor"
  },
  "editor": {
    "add_section_button": ".elementor-add-section-button",
    "text_widget": ".elementor-element-edit-mode[data-widget_type='text-editor']"
  }
}
```

**Classic Editor：**
```json
{
  "metadata": {
    "editor_type": "Classic Editor"
  },
  "editor": {
    "title_field": "#title",
    "content_area": "#content",
    "visual_tab": "#content-tmce",
    "text_tab": "#content-html"
  }
}
```

---

## ⚠️ 生产环境配置说明 (admin.epochtimes.com)

> **重要**: 生产环境 WordPress 使用的配置与上述示例不同：
>
> | 配置项 | 示例配置 | 生产环境 (admin.epochtimes.com) |
> |--------|---------|-------------------------------|
> | **编辑器** | Gutenberg | **Classic Editor** |
> | **SEO 插件** | Yoast SEO | **Lite SEO** |
> | **认证** | 单层 | **双层** (HTTP Basic Auth + WordPress 登录) |
>
> **影响**:
> 1. **FAQ Schema JSON-LD**: 由于使用 Classic Editor，无法通过 Custom HTML 区块插入，系统会自动跳过此步骤
> 2. **SEO 字段**: 需要使用 Lite SEO 的选择器，而非 Yoast/Rank Math
> 3. **登录流程**: 需要先通过 HTTP Basic Auth (`djy/djy2013`)，再进行 WordPress 登录

---

## 🎯 我的建议（基于你的情况）

### 问题：你应该用哪个方案？

**我建议分两步走：**

### 第1步：先用Computer Use（快速开始）✅

**原因：**
1. ✅ 立即可用，我已经写好了指令
2. ✅ 发布几篇测试看看效果
3. ✅ 观察VNC录屏，了解WordPress操作流程
4. ✅ 验证整个系统能正常工作

**这一步只需要：**
- 配置好Google Drive Shared Drive
- 运行现有代码即可

**成本：** 测试10篇文章 ≈ $2

---

### 第2步：发布量大时切换到Playwright（省钱）💰

**什么时候切换？**
- 发布超过100篇后
- 月度发布成本超过$20
- 系统运行稳定了

**如何切换？**
1. 使用我提供的提取工具获取CSS选择器（30分钟）
2. 保存配置文件（5分钟）
3. 修改代码使用Playwright（15分钟）
4. 测试调优（1-2小时）

**节省：** 每月发布500篇
- Computer Use方案：$100/月
- Playwright方案：$0/月
- **节省：$100/月 = $1200/年**

---

## 📝 总结

### 你现在需要做什么？

#### 选项A：先用Computer Use（推荐） ⭐

**立即行动：**
1. ✅ 配置Google Drive Shared Drive（还没做的话）
2. ✅ 测试发布功能（代码已经ready）
3. ✅ 观察效果和成本

**什么都不用改，直接用！**

---

#### 选项B：直接上Playwright（省钱但耗时）

**需要做：**
1. ⏰ 花2-4小时提取CSS选择器
2. ⏰ 配置和测试
3. ⏰ 调试优化

**适合：**
- 你很在意成本
- 有技术能力配置
- 不急着马上上线

---

#### 选项C：混合使用（最佳实践）🎯

**策略：**
- 🤖 日常发布：用Playwright（免费）
- 🧠 特殊情况：用Computer Use（智能）
- 📊 AB测试：对比两种方案

**在代码中实现：**
```python
# 根据文章类型选择发布方式
if article.is_complex or article.has_custom_fields:
    # 复杂文章用Computer Use
    publisher = ComputerUseCMSService()
else:
    # 普通文章用Playwright
    publisher = await create_playwright_publisher(config_path)
```

---

## ❓ 你想怎么做？

**回答我这几个问题，我帮你决定：**

1. **预算敏感度：** 在意成本吗？
   - 在意 → Playwright
   - 不太在意 → Computer Use

2. **发布量：** 每月发布多少篇？
   - <100篇 → Computer Use
   - >500篇 → Playwright
   - 100-500篇 → 看预算

3. **技术能力：** 能配置CSS选择器吗？
   - 能 → Playwright
   - 不太会 → Computer Use

4. **时间紧迫度：** 需要马上上线吗？
   - 是 → Computer Use（已经ready）
   - 不急 → Playwright（需要配置）

**告诉我你的答案，我给你最合适的方案！** 🚀
