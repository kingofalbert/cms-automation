# SEO 分析到 WordPress 发布完整流程

## 📋 完整流程图

```
┌─────────────────────────────────────────────────────────────────┐
│ 阶段 1: 文章生成 + SEO 分析（自动完成）                          │
└─────────────────────────────────────────────────────────────────┘

用户提交主题
"写一篇关于 PostgreSQL pgvector 的教程"
       ↓
┌──────────────────────────────────────┐
│  Claude Messages API 生成文章         │
│  - 标题：PostgreSQL pgvector 教程     │
│  - 正文：完整的 Markdown 内容         │
│  - 耗时：3-5 分钟                    │
└──────────────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│  SEO Analyzer 自动分析               │
│  输入：标题 + 正文                    │
│  输出：                              │
│  {                                   │
│    meta_title: "...",                │
│    meta_description: "...",          │
│    focus_keyword: "...",             │
│    keywords: [...],                  │
│    seo_score: 85.0                   │
│  }                                   │
│  - 耗时：15-25 秒                    │
└──────────────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│  保存到 PostgreSQL 数据库             │
│  Article {                           │
│    id: 1                             │
│    title: "..."                      │
│    body: "..."                       │
│    article_metadata: {               │
│      seo: { ... },    ← SEO 数据     │
│      cost_usd: 0.08                  │
│    }                                 │
│    status: "draft"    ← 草稿状态     │
│  }                                   │
└──────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 阶段 2: Computer Use 发布（用户触发）                            │
└─────────────────────────────────────────────────────────────────┘

用户点击 "发布到 WordPress" 按钮
或者调用 API: POST /v1/computer-use/publish
       ↓
┌──────────────────────────────────────┐
│  创建 Celery 异步任务                 │
│  Task ID: abc123-def456               │
│  任务名称: publish_article_with_      │
│           computer_use_task           │
└──────────────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│  从数据库读取文章数据                 │
│  - 标题                               │
│  - 正文                               │
│  - SEO 元数据 ← 这是关键！            │
└──────────────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│  启动 Computer Use 会话               │
│  - 启动 Chromium 浏览器               │
│  - 分辨率：1920x1080                  │
│  - 可通过 VNC 实时观看                │
└──────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────┐
│  Computer Use API 执行浏览器操作（详细步骤如下）             │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔍 Computer Use 详细操作步骤

### 构建的指令（Instructions）

系统会将 **文章内容** 和 **SEO 数据** 组合成详细的操作指令发送给 Claude Computer Use API：

```python
instructions = f"""
你是一个自动化助手，需要将文章发布到 WordPress 并设置 SEO。

=== 文章信息 ===
标题：{article.title}
正文：{article.body}

=== SEO 配置（重要！）===
Meta Title: {seo_data.meta_title}
Meta Description: {seo_data.meta_description}
Focus Keyword: {seo_data.focus_keyword}
Additional Keywords: {', '.join(seo_data.keywords)}

=== WordPress 登录信息 ===
URL: {cms_url}/wp-admin
用户名: {username}
密码: {password}

=== 操作步骤 ===

步骤 1: 打开浏览器并登录
- 访问 {cms_url}/wp-admin
- 输入用户名和密码
- 点击"登录"
- 截图确认登录成功

步骤 2: 创建新文章
- 点击"文章" → "新建文章"
- 等待编辑器加载
- 截图

步骤 3: 填写文章内容
- 在标题栏输入：{article.title}
- 在内容区域输入：{article.body}
- 截图

步骤 4: 配置 Yoast SEO（关键步骤！）
- 向下滚动找到 Yoast SEO 元框
- 点击"编辑 snippet"

  4.1 设置 SEO Title
  - 找到"SEO title"字段
  - 清空现有内容
  - 输入：{seo_data.meta_title}
  - 截图

  4.2 设置 Meta Description
  - 找到"Meta description"字段
  - 清空现有内容
  - 输入：{seo_data.meta_description}
  - 截图

  4.3 设置 Focus Keyword
  - 找到"Focus keyphrase"字段
  - 输入：{seo_data.focus_keyword}
  - 等待 Yoast 分析完成
  - 截图显示 SEO 评分

  4.4 检查 SEO 评分
  - 确认 SEO 指示灯为绿色或橙色
  - 如果是红色，查看建议并尝试优化
  - 截图最终评分

步骤 5: 设置分类和标签（如果有）
- 在右侧边栏找到"分类"
- 选择或创建适当的分类
- 在"标签"部分添加关键词
- 截图

步骤 6: 发布文章
- 点击右上角"发布"按钮
- 如果有确认对话框，再次点击"发布"
- 等待"文章已发布"消息
- 截图成功消息

步骤 7: 获取文章 URL
- 点击"查看文章"或复制 URL
- 记录文章 ID（通常在 URL 中，如 ?p=123）
- 截图最终发布的文章

步骤 8: 返回结果
返回 JSON 格式：
{{
  "article_url": "完整的文章 URL",
  "article_id": "WordPress 文章 ID"
}}

重要提示：
- 每个关键步骤都要截图
- 如果遇到错误，尝试解决并记录
- 确保 SEO 数据完全填写正确
"""
```

---

## 🎬 实际操作演示

### Claude Computer Use 如何执行

Computer Use API 会将指令转换为实际的浏览器操作：

```python
# Claude Computer Use 内部流程（简化版）

# 1. 解析指令
task = parse_instructions(instructions)

# 2. 执行操作序列
for step in task.steps:
    if step.type == "navigate":
        # 使用 computer tool 控制浏览器
        result = await computer.navigate(url=step.url)
        screenshot = await computer.screenshot()

    elif step.type == "input":
        # 找到输入框并输入
        await computer.mouse_move(x=step.x, y=step.y)
        await computer.left_click()
        await computer.type_text(step.text)
        screenshot = await computer.screenshot()

    elif step.type == "click":
        # 点击按钮
        await computer.mouse_move(x=step.x, y=step.y)
        await computer.left_click()
        await computer.wait(seconds=2)
        screenshot = await computer.screenshot()

# 3. 返回结果
return {
    "success": True,
    "article_url": extracted_url,
    "article_id": extracted_id,
    "screenshots": all_screenshots
}
```

---

## 📊 SEO 数据的传递路径

```
┌─────────────────────────────────────────────────────────────┐
│  SEO Analyzer 生成                                           │
│  {                                                           │
│    "meta_title": "PostgreSQL pgvector：向量搜索完整指南",    │
│    "meta_description": "学习 PostgreSQL pgvector...",        │
│    "focus_keyword": "PostgreSQL pgvector",                   │
│    "keywords": ["向量搜索", "数据库", "AI"]                  │
│  }                                                           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ 存储到数据库
┌─────────────────────────────────────────────────────────────┐
│  PostgreSQL - Article Table                                  │
│  article_metadata: {                                         │
│    "seo": {                                                  │
│      "meta_title": "...",      ← 存储在这里                  │
│      "meta_description": "...",                              │
│      "focus_keyword": "...",                                 │
│      ...                                                     │
│    }                                                         │
│  }                                                           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ Computer Use 任务读取
┌─────────────────────────────────────────────────────────────┐
│  Celery Task                                                 │
│  seo_data = article.article_metadata["seo"]                  │
│  seo_metadata = SEOMetadata(**seo_data)                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ 构建 Computer Use 指令
┌─────────────────────────────────────────────────────────────┐
│  Computer Use Instructions                                   │
│  "在 Yoast SEO 中设置："                                      │
│  "- SEO Title: {seo_metadata.meta_title}"                    │
│  "- Meta Description: {seo_metadata.meta_description}"       │
│  "- Focus Keyword: {seo_metadata.focus_keyword}"             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ Computer Use 执行
┌─────────────────────────────────────────────────────────────┐
│  浏览器操作                                                   │
│  1. 找到"SEO title"输入框                                     │
│  2. 清空并输入 seo_metadata.meta_title                        │
│  3. 找到"Meta description"输入框                              │
│  4. 清空并输入 seo_metadata.meta_description                  │
│  5. 找到"Focus keyphrase"输入框                               │
│  6. 输入 seo_metadata.focus_keyword                           │
│  7. 等待 Yoast 分析完成                                       │
│  8. 截图验证                                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🖥️ WordPress 后台 Yoast SEO 界面

当 Computer Use 操作 WordPress 时，它看到的界面：

```
┌─────────────────────────────────────────────────────────────┐
│ WordPress - 编辑文章                                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  标题：[PostgreSQL pgvector 教程                    ]        │
│                                                              │
│  正文：[Markdown 内容...                            ]        │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ▼ Yoast SEO                                         │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │                                                      │   │
│  │ SEO 分析  可读性  社交                               │   │
│  │                                                      │   │
│  │ Google 预览:                                         │   │
│  │ ┌──────────────────────────────────────────────┐   │   │
│  │ │ PostgreSQL pgvector：向量搜索完整指南          │   │   │
│  │ │ https://example.com/pgvector-guide           │   │   │
│  │ │ 学习 PostgreSQL pgvector 扩展实现高性能...    │   │   │
│  │ └──────────────────────────────────────────────┘   │   │
│  │                                                      │   │
│  │ SEO title:                                           │   │
│  │ [PostgreSQL pgvector：向量搜索完整指南        ] ✓   │   │
│  │                                                      │   │
│  │ Slug:                                                │   │
│  │ [pgvector-guide                               ]     │   │
│  │                                                      │   │
│  │ Meta description:                                    │   │
│  │ [学习 PostgreSQL pgvector 扩展实现高性能向量  ] ✓   │   │
│  │ [搜索。包含安装配置、索引优化、查询技巧。     ]     │   │
│  │                                                      │   │
│  │ Focus keyphrase:                                     │   │
│  │ [PostgreSQL pgvector                          ] ✓   │   │
│  │                                                      │   │
│  │ SEO 分析结果:                                        │   │
│  │ 🟢 SEO: Good    (85/100)                            │   │
│  │   ✓ Focus keyphrase in SEO title                   │   │
│  │   ✓ Focus keyphrase in meta description            │   │
│  │   ✓ Meta description length is good                │   │
│  │   ⚠ Add more internal links                        │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  [发布]                                                      │
└─────────────────────────────────────────────────────────────┘

Computer Use 会：
1. 找到 "SEO title" 输入框 ← 使用鼠标定位和点击
2. 输入我们的 meta_title      ← 使用键盘输入
3. 找到 "Meta description"   ← 继续定位
4. 输入我们的 meta_description
5. 找到 "Focus keyphrase"
6. 输入我们的 focus_keyword
7. 等待 Yoast 分析（几秒钟）
8. 截图显示绿色的 SEO 评分 ✓
9. 点击"发布"
```

---

## 🎥 实时观看 Computer Use 操作

您可以通过 VNC 实时观看整个过程：

```bash
# 方法 1: 浏览器访问 noVNC
打开: http://localhost:6080

# 方法 2: VNC 客户端
连接: vnc://localhost:5901
密码: vnc_password
```

**你会看到**：
1. 🌐 Chromium 浏览器打开
2. 📝 自动输入 WordPress 登录信息
3. ✍️ 自动创建新文章
4. ⚙️ 自动填写 Yoast SEO 字段
5. ✅ 自动点击发布按钮
6. 📸 每一步都有截图记录

---

## 💾 发布完成后的数据更新

```python
# Computer Use 成功后，更新数据库

# 1. 获取返回的结果
result = {
    "success": True,
    "cms_article_id": "456",  # WordPress 文章 ID
    "url": "https://example.com/pgvector-guide",
    "metadata": {
        "session_id": "cu_1698765432",
        "execution_time_seconds": 125.5,
        "screenshots": [
            "/screenshots/.../step_1_login.png",
            "/screenshots/.../step_4_seo_config.png",
            "/screenshots/.../step_7_published.png"
        ]
    }
}

# 2. 更新文章记录
article.cms_article_id = "456"
article.status = ArticleStatus.PUBLISHED
article.published_at = datetime.utcnow()

# 3. 添加 Computer Use 元数据
article.article_metadata["computer_use"] = {
    "session_id": "cu_1698765432",
    "status": "completed",
    "execution_time_seconds": 125.5,
    "screenshots": [...],
    "attempts": 1,
    "last_attempt_at": "2025-10-26T10:30:00Z"
}

# 4. 保存
await session.commit()
```

---

## 📋 完整的数据结构示例

发布完成后，数据库中的文章记录：

```json
{
  "id": 1,
  "title": "PostgreSQL pgvector 教程",
  "body": "完整的 Markdown 内容...",
  "status": "published",
  "cms_article_id": "456",
  "published_at": "2025-10-26T10:30:00Z",
  "article_metadata": {
    // ← SEO 分析阶段生成
    "seo": {
      "meta_title": "PostgreSQL pgvector：向量搜索完整指南",
      "meta_description": "学习 PostgreSQL pgvector 扩展...",
      "focus_keyword": "PostgreSQL pgvector",
      "keywords": ["向量搜索", "数据库", "AI"],
      "seo_score": 85.0,
      "readability_score": 72.0
    },

    // ← Computer Use 阶段生成
    "computer_use": {
      "session_id": "cu_1698765432",
      "status": "completed",
      "execution_time_seconds": 125.5,
      "attempts": 1,
      "screenshots": [
        "/screenshots/cu_1698765432/screenshot_1.png",
        "/screenshots/cu_1698765432/screenshot_4.png",
        "/screenshots/cu_1698765432/screenshot_7.png"
      ],
      "errors": []
    },

    // ← 文章生成阶段的元数据
    "cost_usd": 0.08,
    "model": "claude-3-5-sonnet-20241022",
    "input_tokens": 1500,
    "output_tokens": 3000
  }
}
```

---

## 🔄 两阶段的关系总结

```
┌────────────────────────────────────────────────────────┐
│ 阶段 1: 内容准备（离线/自动）                          │
├────────────────────────────────────────────────────────┤
│ • 生成文章内容                                         │
│ • 分析 SEO（生成元数据）                               │
│ • 保存到数据库                                         │
│                                                         │
│ 时间：3-5 分钟                                         │
│ 成本：$0.08-$0.12                                      │
│ 状态：article.status = "draft"                         │
└────────────────────────────────────────────────────────┘
              │
              │ ⏸️ 暂停，等待用户触发发布
              │
              ▼
┌────────────────────────────────────────────────────────┐
│ 阶段 2: 自动发布（在线/Computer Use）                  │
├────────────────────────────────────────────────────────┤
│ • 读取文章内容 + SEO 数据                               │
│ • 启动浏览器                                           │
│ • 登录 WordPress                                       │
│ • 创建文章并填充内容                                   │
│ • 配置 Yoast SEO（使用阶段1的SEO数据）                 │
│ • 发布文章                                             │
│ • 更新数据库状态                                       │
│                                                         │
│ 时间：2-5 分钟                                         │
│ 成本：$0.15-$0.30                                      │
│ 状态：article.status = "published"                     │
└────────────────────────────────────────────────────────┘
```

**关键关系**：
- **阶段 1** 生成 SEO 数据（智能分析）
- **阶段 2** 使用 SEO 数据（自动填写）
- 两者通过 **数据库** 连接

---

## 🎯 为什么要分两个阶段？

### 优点

1. **解耦设计** 🔧
   - SEO 分析可以单独运行（快速、便宜）
   - Computer Use 可以稍后批量执行
   - 失败时易于重试

2. **人工审核** 👀
   - 用户可以先查看生成的文章和 SEO
   - 满意后再发布到 WordPress
   - 避免发布低质量内容

3. **成本控制** 💰
   - SEO 分析：$0.02（必需）
   - Computer Use：$0.25（可选）
   - 如果 WordPress 支持 API，可跳过 Computer Use

4. **调试友好** 🐛
   - 可以在阶段 1 检查 SEO 数据
   - 可以通过 VNC 观看阶段 2 的操作
   - 截图记录便于排查问题

---

## 🚀 实际使用流程

```bash
# 1. 生成文章（包含 SEO 分析）
curl -X POST http://localhost:8000/v1/topics \
  -d '{"topic_description": "Python 异步编程"}'

# 等待 3-5 分钟...

# 2. 查看生成的文章和 SEO 数据
curl http://localhost:8000/v1/articles/1 | jq '.'

# 输出：
{
  "id": 1,
  "title": "...",
  "body": "...",
  "article_metadata": {
    "seo": {
      "meta_title": "Python 异步编程完整指南：Async/Await 实战",
      "meta_description": "从零学习 Python 异步编程...",
      "seo_score": 88.0
    }
  },
  "status": "draft"  ← 草稿状态
}

# 3. 满意后，触发 Computer Use 发布
curl -X POST http://localhost:8000/v1/computer-use/publish \
  -d '{"article_id": 1}'

# 返回：
{
  "task_id": "abc123",
  "message": "Publishing task started"
}

# 4. 打开 VNC 观看实时操作（可选）
# 浏览器访问: http://localhost:6080

# 5. 等待 2-5 分钟，查询发布状态
curl http://localhost:8000/v1/computer-use/task/abc123

# 返回：
{
  "task_id": "abc123",
  "status": "SUCCESS",
  "result": {
    "success": true,
    "cms_article_id": "456",
    "url": "https://example.com/python-async-guide"
  }
}

# 6. 再次查看文章，状态已更新
curl http://localhost:8000/v1/articles/1 | jq '.status'
# 输出: "published"
```

---

## ✅ 总结

**SEO 分析** 和 **Computer Use WordPress 上传** 的关系：

1. **SEO 分析**（阶段 1）
   - 🧠 智能生成 SEO 元数据
   - 💾 保存到数据库
   - ⏱️ 快速（15-25 秒）
   - 💰 便宜（$0.02）

2. **Computer Use 发布**（阶段 2）
   - 📖 读取 SEO 数据
   - 🤖 自动操作浏览器
   - ⚙️ 填写 Yoast SEO 字段
   - 🚀 发布文章
   - ⏱️ 较慢（2-5 分钟）
   - 💰 较贵（$0.25）

**数据流**：
```
文章 → SEO 分析 → 保存 SEO 数据 → Computer Use 读取 → 填写 WordPress → 发布
```

**核心价值**：
- ✅ 完全自动化（无需人工填写 SEO）
- ✅ 专业 SEO 优化（AI 智能生成）
- ✅ 可视化验证（VNC 实时观看）
- ✅ 完整审计追踪（截图记录每一步）

这就是整个系统的工作原理！🎉
