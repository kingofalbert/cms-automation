# Computer Use SEO 自动化使用指南

## 概述

本系统实现了使用 Anthropic Computer Use API 自动分析文章 SEO 并在 CMS 后台完成设置和发布的功能。

## 功能特性

### 1. 自动 SEO 分析
- ✅ Meta Title 优化（50-60 字符）
- ✅ Meta Description 生成（120-160 字符）
- ✅ Focus Keyword 识别
- ✅ 相关关键词提取
- ✅ Open Graph 标签配置
- ✅ SEO 评分（0-100）
- ✅ 可读性分析（Flesch-Kincaid）

### 2. Computer Use 自动化 CMS 操作
- ✅ 自动登录 WordPress 后台
- ✅ 创建新文章
- ✅ 设置 SEO 配置（支持 Yoast SEO / Rank Math / Lite SEO）
- ✅ 配置 Open Graph 标签
- ✅ 发布文章
- ✅ 截图记录操作过程

> **生产环境 (admin.epochtimes.com)**: 使用 **Classic Editor** + **Lite SEO**（非 Gutenberg + Yoast）

## 架构流程

```
用户提交文章主题
    ↓
Claude Messages API 生成文章内容
    ↓
SEO 分析服务生成 SEO 元数据
    ↓
保存到数据库（PostgreSQL）
    ↓
【可选】Computer Use API 自动操作 CMS
    ↓
在 WordPress 后台设置 SEO 并发布
    ↓
返回发布 URL 和 ID
```

## 快速开始

### 1. 启动服务

```bash
# 启动所有服务（包括 Computer Use 环境）
docker compose up -d

# 检查服务状态
docker compose ps
```

**重要服务端口：**
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- VNC Server: `vnc://localhost:5901` (密码: vnc_password)
- noVNC Web: http://localhost:6080 (调试用)
- Flower: http://localhost:5555

### 2. 测试 Computer Use 环境

```bash
# 使用 API 测试环境
curl -X POST http://localhost:8000/v1/computer-use/test-environment
```

**预期响应：**
```json
{
  "status": "ok",
  "checks": {
    "display": ":1",
    "vnc_running": true,
    "browser_available": true,
    "anthropic_api_key_set": true
  },
  "message": "All checks passed"
}
```

### 3. 生成带 SEO 的文章

#### 方法 1: 使用 API

```bash
# 1. 提交文章主题
curl -X POST http://localhost:8000/v1/topics \
  -H "Content-Type: application/json" \
  -d '{
    "topic_description": "如何使用 PostgreSQL pgvector 进行向量搜索",
    "style_tone": "professional",
    "target_word_count": 1500
  }'

# 响应示例
{
  "id": 1,
  "status": "pending",
  "topic_description": "..."
}

# 2. 等待文章生成（约 3-5 分钟）
curl http://localhost:8000/v1/topics/1

# 3. 查看生成的文章（包含 SEO 数据）
curl http://localhost:8000/v1/articles/1
```

**生成的文章包含的 SEO 数据：**
```json
{
  "id": 1,
  "title": "PostgreSQL pgvector 向量搜索完整指南",
  "body": "...",
  "article_metadata": {
    "seo": {
      "meta_title": "PostgreSQL pgvector 向量搜索：实战指南与最佳实践",
      "meta_description": "学习如何使用 PostgreSQL pgvector 扩展实现高性能向量搜索。包含安装配置、索引优化、查询技巧等实用教程。",
      "focus_keyword": "pgvector 向量搜索",
      "keywords": ["PostgreSQL", "向量数据库", "相似度搜索", "AI 应用"],
      "seo_score": 85.5,
      "readability_score": 68.0
    }
  }
}
```

### 4. 使用 Computer Use 发布到 WordPress

#### 方法 1: 通过 API 触发

```bash
# 触发 Computer Use 发布任务
curl -X POST http://localhost:8000/v1/computer-use/publish \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 1,
    "cms_type": "wordpress"
  }'

# 响应示例
{
  "task_id": "abc123-def456-789",
  "message": "Computer Use publishing task started...",
  "article_id": 1
}

# 查询任务状态
curl http://localhost:8000/v1/computer-use/task/abc123-def456-789

# 响应示例
{
  "task_id": "abc123-def456-789",
  "status": "SUCCESS",
  "result": {
    "success": true,
    "cms_article_id": "456",
    "url": "https://your-wordpress.com/article-slug",
    "metadata": {
      "session_id": "cu_1698765432",
      "execution_time_seconds": 125.5,
      "screenshots": [
        "/screenshots/cu_1698765432/screenshot_1.png",
        "/screenshots/cu_1698765432/screenshot_5.png"
      ]
    }
  }
}
```

#### 方法 2: 通过前端界面

1. 访问 http://localhost:3000
2. 点击已生成的文章
3. 点击 "Publish with Computer Use" 按钮
4. 查看实时发布进度

## 调试和监控

### 1. 查看 VNC 实时操作

**选项 A: 使用 VNC 客户端**
```bash
# 连接 VNC
vnc://localhost:5901
# 密码: vnc_password
```

**选项 B: 使用 noVNC Web 界面**
```
在浏览器打开: http://localhost:6080
```

### 2. 查看 Celery 任务

访问 Flower: http://localhost:5555

- 查看所有任务列表
- 监控任务执行时间
- 查看失败任务的错误信息

### 3. 查看截图

```bash
# 进入 Computer Use 容器
docker compose exec computer_use bash

# 查看截图
ls -la /app/screenshots/
```

## 配置说明

### 环境变量 (.env)

```bash
# Anthropic API Key（必需）
ANTHROPIC_API_KEY=sk-ant-your-key-here

# WordPress 配置（必需）
CMS_TYPE=wordpress
CMS_BASE_URL=https://your-wordpress-site.com
CMS_USERNAME=your-username
CMS_APPLICATION_PASSWORD=xxxx xxxx xxxx xxxx

# Computer Use 配置（可选）
COMPUTER_USE_DISPLAY_WIDTH=1920
COMPUTER_USE_DISPLAY_HEIGHT=1080
COMPUTER_USE_MAX_ITERATIONS=50
```

### WordPress Application Password

1. 登录 WordPress 后台
2. 进入：用户 → 个人资料
3. 滚动到 "应用密码" 部分
4. 输入名称：CMS Automation
5. 点击 "添加新应用密码"
6. 复制生成的密码（格式：xxxx xxxx xxxx xxxx）
7. 粘贴到 .env 文件的 `CMS_APPLICATION_PASSWORD`

## 成本估算

### 每篇文章成本

| 操作 | API 调用 | 估算成本 |
|------|---------|---------|
| 文章生成 | Messages API | $0.05 - $0.10 |
| SEO 分析 | Messages API | $0.02 - $0.05 |
| Computer Use 发布 | Computer Use API | $0.15 - $0.30 |
| **总计** | | **$0.22 - $0.45** |

### 成本优化建议

1. **优先使用 REST API**：如果 WordPress 支持 API，使用传统方法发布（成本 < $0.10）
2. **批量处理**：一次生成多篇文章，然后批量发布
3. **失败重试限制**：设置最大重试次数避免重复成本

## 故障排除

### 问题 1: Computer Use 任务一直处于 PENDING 状态

**原因**：Celery worker 未启动或未连接

**解决方案**：
```bash
# 检查 worker 状态
docker compose logs celery_worker

# 重启 worker
docker compose restart celery_worker
```

### 问题 2: VNC 无法连接

**原因**：X11 server 未启动

**解决方案**：
```bash
# 进入容器
docker compose exec computer_use bash

# 检查 X11 进程
ps aux | grep Xvfb

# 重启 Computer Use 容器
docker compose restart computer_use
```

### 问题 3: SEO 数据未生成

**原因**：SEO analyzer 失败

**解决方案**：
```bash
# 查看后端日志
docker compose logs backend | grep seo

# 检查文章 metadata
curl http://localhost:8000/v1/articles/1 | jq '.article_metadata'
```

### 问题 4: Computer Use 发布失败

**常见原因和解决方案**：

1. **WordPress 登录失败**
   - 检查 CMS_USERNAME 和 CMS_APPLICATION_PASSWORD
   - 确认 Application Password 未过期

2. **SEO 插件未找到**
   - 确认已安装 SEO 插件（Yoast SEO / Rank Math / Lite SEO）
   - 插件已激活
   - **生产环境**: `admin.epochtimes.com` 使用 **Lite SEO**

3. **网络问题**
   - 检查 CMS_BASE_URL 是否可访问
   - 尝试手动访问 WordPress 后台

## 高级用法

### 自定义 SEO 分析

```python
from src.services.seo_analyzer import SEOAnalyzerService

analyzer = SEOAnalyzerService()

# 分析现有文章
analysis = await analyzer.analyze_article(
    title="文章标题",
    body="文章内容...",
    target_keyword="目标关键词"
)

print(f"SEO 评分: {analysis.seo_data.seo_score}")
print(f"建议: {analysis.suggestions}")
```

### 监控 Computer Use 操作

```python
# 订阅 Celery 任务事件
from celery import Celery

app = Celery('cms_automation')

@app.task(bind=True)
def monitor_computer_use(self):
    # 自定义监控逻辑
    pass
```

## 安全注意事项

1. **凭证保护**
   - 不要将 .env 文件提交到 Git
   - 使用 Application Password 而非主密码
   - 定期轮换密码

2. **访问控制**
   - 限制 Computer Use 只能访问配置的 CMS URL
   - 使用防火墙规则限制出站连接

3. **审计日志**
   - 所有 Computer Use 操作都会截图记录
   - 定期检查 /app/screenshots/ 目录
   - 监控异常登录尝试

## 下一步

1. **配置生产环境**
   - 使用 HTTPS for CMS
   - 配置 S3 存储截图
   - 设置告警监控

2. **优化性能**
   - 增加 Celery worker 数量
   - 使用 Redis 缓存
   - 优化浏览器启动时间

3. **扩展功能**
   - 支持更多 CMS 平台（Strapi, Ghost）
   - 添加图片自动上传
   - 实现 A/B 测试 SEO 标题

## 支持

- **文档**: `specs/001-cms-automation/computer-use-seo-design.md`
- **API 文档**: http://localhost:8000/docs
- **问题反馈**: GitHub Issues

---

**更新日期**: 2025-10-26
**版本**: 1.0.0
