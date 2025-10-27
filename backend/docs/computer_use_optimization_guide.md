# Computer Use优化指南 - 提升发布成功率

## 概述

Computer Use（Claude）是预训练的AI，**不需要传统的训练过程**。但我们可以通过提供更好的指令、示例和上下文来提升它的表现。

## Computer Use如何工作

### 基本原理
```
用户请求发布文章
    ↓
系统生成详细指令（Prompt）
    ↓
Claude读取指令 + 看到屏幕截图
    ↓
Claude推理下一步操作（点击、输入、滚动等）
    ↓
执行操作 → 获取新截图
    ↓
重复直到完成任务
```

### Claude已经知道什么？
- ✅ WordPress基本界面和操作
- ✅ 常见的CMS操作流程
- ✅ HTML/CSS选择器
- ✅ SEO概念和最佳实践
- ✅ 如何使用浏览器开发工具

### Claude不知道什么？
- ❌ 你的WordPress站点的具体配置
- ❌ 自定义主题的特殊UI
- ❌ 自定义插件的界面
- ❌ 你的WordPress版本的具体细节

## 优化策略

### 策略1️⃣：提供WordPress站点的参考截图

创建一个"参考截图库"，包含：

**关键界面截图：**
```
screenshots/
├── wordpress_login.png           # 登录页面
├── wordpress_dashboard.png       # 仪表盘
├── wordpress_new_post.png        # 新建文章界面
├── wordpress_block_editor.png    # 块编辑器
├── wordpress_media_upload.png    # 媒体上传
├── yoast_seo_panel.png          # Yoast SEO面板
└── publish_button.png            # 发布按钮
```

**如何使用：**
在指令中引用这些截图作为"示例"：

```python
instructions = f"""
参考以下截图来理解WordPress界面：

1. 登录页面应该看起来像这样：
   [参考截图：wordpress_login.png]
   - 用户名字段通常在页面中央
   - 密码字段在用户名下方
   - "登录"按钮是蓝色的

2. Yoast SEO面板位置：
   [参考截图：yoast_seo_panel.png]
   - 通常在文章编辑器下方
   - 或者在右侧边栏的"Yoast SEO"标签中

现在开始操作...
"""
```

### 策略2️⃣：提供精确的CSS选择器

如果你的WordPress有自定义主题，可以提供具体的CSS选择器：

```python
# 在指令中添加：
wordpress_selectors = {
    "username_field": "#user_login",
    "password_field": "#user_pass",
    "login_button": "#wp-submit",
    "new_post_button": "a[href='post-new.php']",
    "title_field": ".editor-post-title__input",
    "yoast_focus_keyword": "#yoast-google-preview-focus-keyword",
    "publish_button": ".editor-post-publish-button",
}

instructions += f"""
使用以下CSS选择器定位元素：
- 用户名输入框：{wordpress_selectors['username_field']}
- 密码输入框：{wordpress_selectors['password_field']}
...
"""
```

### 策略3️⃣：记录成功案例的"playbook"

创建一个成功发布的"playbook"（操作序列）：

```python
successful_publishing_playbook = {
    "steps": [
        {
            "step": 1,
            "action": "navigate",
            "target": "https://example.com/wp-admin",
            "expected_result": "看到登录表单",
            "screenshot": "step1_login_page.png"
        },
        {
            "step": 2,
            "action": "type",
            "target": "#user_login",
            "value": "admin",
            "expected_result": "用户名已填写",
            "screenshot": "step2_username_filled.png"
        },
        # ... 更多步骤
    ]
}
```

### 策略4️⃣：添加错误恢复指令

告诉Claude如何处理常见错误：

```python
error_handling_instructions = """
常见问题处理：

1. 如果登录失败：
   - 检查是否有错误消息
   - 确认用户名和密码正确
   - 尝试刷新页面重新登录

2. 如果找不到"新建文章"按钮：
   - 检查是否在仪表盘页面
   - 尝试点击顶部的"+ 新建" → "文章"
   - 或者直接导航到 /wp-admin/post-new.php

3. 如果Yoast SEO面板没有显示：
   - 向下滚动查找
   - 检查右侧边栏
   - 如果仍然找不到，跳过SEO配置步骤

4. 如果图片上传失败：
   - 检查文件大小（不超过10MB）
   - 检查文件格式（JPG、PNG、GIF）
   - 重试一次，如果仍然失败则跳过该图片
"""
```

### 策略5️⃣：使用Few-Shot示例

提供1-2个完整的成功案例：

```python
few_shot_example = """
示例：成功发布案例

用户要求：发布标题为"如何使用WordPress"的文章

步骤记录：
1. ✅ 访问 https://example.com/wp-admin
   截图显示：登录表单

2. ✅ 输入用户名 "admin"
   截图显示：用户名字段已填充

3. ✅ 输入密码
   截图显示：密码字段显示点点

4. ✅ 点击"登录"按钮
   截图显示：WordPress仪表盘

5. ✅ 点击"文章" → "写文章"
   截图显示：块编辑器已加载

... (完整的25个步骤)

25. ✅ 返回结果
    文章URL: https://example.com/how-to-use-wordpress
    文章ID: 789

现在按照类似的方式发布你的文章。
"""
```

## 实现优化的代码

### 修改 `_build_wordpress_instructions` 方法

我可以帮你添加这些优化：

```python
def _build_wordpress_instructions(
    self,
    cms_url: str,
    username: str,
    password: str,
    title: str,
    body: str,
    seo_data: SEOMetadata,
    article_images: list[dict],
    include_examples: bool = True,  # 新参数
    css_selectors: dict = None,      # 新参数
) -> str:
    """构建WordPress发布指令（优化版）"""

    # 加载CSS选择器（如果提供）
    selectors = css_selectors or self._get_default_selectors()

    # 加载成功案例示例（如果启用）
    examples = ""
    if include_examples:
        examples = self._load_successful_examples()

    # 加载错误处理指令
    error_handling = self._load_error_handling_instructions()

    instructions = f"""
{examples}

{error_handling}

现在发布以下文章：
标题：{title}
...

使用这些CSS选择器：
{json.dumps(selectors, indent=2)}
"""

    return instructions
```

## 优化优先级建议

### 立即实施（高优先级）⭐⭐⭐
1. **添加错误处理指令**
   - 工作量：小
   - 效果：显著提升容错能力

2. **提供CSS选择器**
   - 工作量：中等（需要检查你的WordPress站点）
   - 效果：提升准确性

### 短期实施（中优先级）⭐⭐
3. **记录一个成功案例**
   - 工作量：中等
   - 效果：作为Few-Shot示例

4. **创建参考截图库**
   - 工作量：中等
   - 效果：帮助Claude理解特定界面

### 长期优化（低优先级）⭐
5. **构建完整的playbook系统**
   - 工作量：大
   - 效果：可复用的操作模板

## 不需要的事情 ❌

1. **不需要**训练机器学习模型
2. **不需要**fine-tune Claude
3. **不需要**准备大量训练数据
4. **不需要**标注数据集
5. **不需要**GPU训练资源

## 测试和迭代流程

```
1. 首次发布尝试
   ↓
2. 观察VNC录屏，看Claude在哪里卡住
   ↓
3. 在指令中添加针对性的说明
   ↓
4. 重新测试
   ↓
5. 记录成功的操作序列
   ↓
6. 更新指令模板
```

## 监控和改进

### 关键指标
- 首次成功率：理想应 >80%
- 平均尝试次数：理想应 <2次
- 平均耗时：理想应 <3分钟
- 错误类型分布：找出最常见的失败点

### 日志分析
```sql
-- 查看最常见的失败步骤
SELECT
    step_name,
    COUNT(*) as failure_count
FROM execution_logs
WHERE action_result = 'failed'
GROUP BY step_name
ORDER BY failure_count DESC;
```

## 总结

**Computer Use不需要传统的"训练"，但需要好的"指令工程"。**

类比：
- ❌ 不是：训练一个新员工从零学习WordPress（需要数周）
- ✅ 而是：给一个已经懂WordPress的专家提供你公司的操作手册（需要数分钟）

当前代码已经包含了基础的操作指令。如果你发现成功率不高，我可以帮你：
1. 添加更详细的错误处理
2. 提取你的WordPress站点的CSS选择器
3. 创建一个成功案例的示例
4. 优化指令的措辞和结构

需要我现在就实施这些优化吗？
