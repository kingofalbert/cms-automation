# WordPress Publishing API 文档

**版本**: 1.0.0
**更新日期**: 2025-10-27
**Sprint**: 6 (性能优化 + 生产部署)

---

## 📋 目录

1. [概览](#概览)
2. [认证](#认证)
3. [API 端点](#api-端点)
4. [数据模型](#数据模型)
5. [错误处理](#错误处理)
6. [示例代码](#示例代码)
7. [性能指标](#性能指标)

---

## 概览

WordPress Publishing API 提供自动化发布文章到 WordPress 的功能，支持：

- ✅ 文章发布（标题、内容、SEO）
- ✅ 图片上传和元数据
- ✅ 特色图片设置
- ✅ 标签和分类管理
- ✅ Yoast SEO 配置
- ✅ 立即发布 / 排程发布 / 保存草稿
- ✅ 混合架构（Playwright + Computer Use）
- ✅ 智能降级机制

### 基础 URL

```
Production: https://api.your-domain.com
Development: http://localhost:8000
```

### 技术架构

```
Phase 2: Playwright (Primary) + Computer Use (Fallback)
成本: ~$0.02/文章 (降低 90%)
速度: 1-2 分钟/文章 (提升 40-50%)
成功率: ≥ 98%
```

---

## 认证

当前版本使用 WordPress 用户名和密码认证（在请求体中提供）。

**未来版本** 将支持：
- API Key 认证
- OAuth 2.0
- JWT Token

---

## API 端点

### 1. 发布文章

**POST** `/publish`

异步发布文章到 WordPress。

#### 请求体

```json
{
  "article": {
    "title": "文章标题（10-200字符）",
    "content": "<p>HTML 格式的文章内容</p>",
    "seo": {
      "focus_keyword": "焦点关键字",
      "meta_title": "SEO 标题（50-60字符）",
      "meta_description": "Meta 描述（150-160字符）"
    }
  },
  "metadata": {
    "tags": ["标签1", "标签2"],
    "categories": ["分类1"],
    "images": [
      {
        "file_path": "/path/to/image.jpg",
        "alt_text": "图片替代文字",
        "title": "图片标题",
        "is_featured": true
      }
    ],
    "publish_date": "2025-10-28T10:00:00Z"  // 可选，排程发布
  },
  "wordpress_url": "https://your-wordpress-site.com",
  "credentials": {
    "username": "admin",
    "password": "your_password"
  },
  "intent": "publish_now"  // publish_now | schedule | save_draft
}
```

#### 响应

**成功 (202 Accepted)**:

```json
{
  "task_id": "publish-a1b2c3d4",
  "status": "pending",
  "message": "发布任务已创建"
}
```

**失败 (400 Bad Request)**:

```json
{
  "error": "ValidationError",
  "message": "标题长度必须在 10-200 字符之间",
  "details": {
    "field": "article.title",
    "value": "Test"
  }
}
```

#### 示例

```bash
curl -X POST http://localhost:8000/publish \
  -H "Content-Type: application/json" \
  -d @publish_request.json
```

---

### 2. 查询任务状态

**GET** `/tasks/{task_id}`

查询发布任务的当前状态。

#### 路径参数

- `task_id` (string): 任务 ID（从 POST /publish 返回）

#### 响应

**进行中 (200 OK)**:

```json
{
  "task_id": "publish-a1b2c3d4",
  "status": "running",
  "progress": 65,
  "current_phase": "processing_images",
  "completed_phases": [
    "login",
    "fill_content",
    "save_draft"
  ],
  "started_at": "2025-10-27T10:30:00Z",
  "estimated_completion": "2025-10-27T10:32:00Z"
}
```

**已完成 (200 OK)**:

```json
{
  "task_id": "publish-a1b2c3d4",
  "status": "completed",
  "progress": 100,
  "result": {
    "success": true,
    "url": "https://your-site.com/article-title",
    "provider_used": "playwright",
    "fallback_triggered": false,
    "duration_seconds": 85.3,
    "cost_estimate_usd": 0.02
  },
  "started_at": "2025-10-27T10:30:00Z",
  "completed_at": "2025-10-27T10:31:25Z"
}
```

**已失败 (200 OK)**:

```json
{
  "task_id": "publish-a1b2c3d4",
  "status": "failed",
  "error": {
    "type": "ProviderError",
    "message": "无法连接到 WordPress",
    "phase": "login",
    "retry_count": 3
  },
  "started_at": "2025-10-27T10:30:00Z",
  "failed_at": "2025-10-27T10:30:45Z"
}
```

**任务不存在 (404 Not Found)**:

```json
{
  "error": "TaskNotFound",
  "message": "任务 publish-xyz 不存在"
}
```

---

### 3. 获取任务日志

**GET** `/tasks/{task_id}/logs`

获取任务的详细执行日志和审计追踪。

#### 响应

```json
{
  "task_id": "publish-a1b2c3d4",
  "events": [
    {
      "timestamp": "2025-10-27T10:30:00Z",
      "event": "phase_success",
      "phase": "login",
      "retry_count": 0
    },
    {
      "timestamp": "2025-10-27T10:30:15Z",
      "event": "phase_success",
      "phase": "fill_content",
      "retry_count": 0
    },
    {
      "timestamp": "2025-10-27T10:30:45Z",
      "event": "screenshot_saved",
      "step_name": "before_publish",
      "path": "logs/publish-a1b2c3d4/20251027_103045_before_publish.png",
      "size_bytes": 125840
    }
  ],
  "summary": {
    "total_phases": 7,
    "failures": 0,
    "screenshots": 14,
    "provider_switches": 0,
    "total_events": 42
  }
}
```

---

### 4. 取消任务

**POST** `/tasks/{task_id}/cancel`

取消正在运行的任务。

#### 响应

**成功 (200 OK)**:

```json
{
  "task_id": "publish-a1b2c3d4",
  "status": "cancelled",
  "message": "任务已取消"
}
```

**无法取消 (409 Conflict)**:

```json
{
  "error": "CannotCancelTask",
  "message": "任务已完成，无法取消",
  "current_status": "completed"
}
```

---

### 5. 健康检查

**GET** `/health`

检查服务健康状态。

#### 响应

```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "providers": {
    "playwright": "available",
    "computer_use": "available"
  },
  "metrics": {
    "total_published": 1523,
    "success_rate": 98.5,
    "avg_duration_seconds": 95.3
  }
}
```

---

### 6. Metrics 端点

**GET** `/metrics`

Prometheus 格式的性能指标（用于监控）。

#### 响应

```
# HELP article_published_total Total number of articles published
# TYPE article_published_total counter
article_published_total{status="success",provider="playwright"} 1420.0
article_published_total{status="failed",provider="playwright"} 23.0
article_published_total{status="success",provider="computer_use"} 80.0

# HELP article_publish_duration_seconds Time spent publishing an article
# TYPE article_publish_duration_seconds histogram
article_publish_duration_seconds_bucket{provider="playwright",le="60"} 450.0
article_publish_duration_seconds_bucket{provider="playwright",le="120"} 1200.0
...
```

---

## 数据模型

### Article

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `title` | string | ✅ | 文章标题（10-200字符） |
| `content` | string | ✅ | HTML 格式内容（≥100字符） |
| `seo` | SEOData | ✅ | SEO 配置 |

### SEOData

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `focus_keyword` | string | ✅ | 焦点关键字（1-100字符） |
| `meta_title` | string | ✅ | SEO 标题（50-60字符） |
| `meta_description` | string | ✅ | Meta 描述（150-160字符） |

### Metadata

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `tags` | string[] | ❌ | 标签列表（最多 10 个） |
| `categories` | string[] | ❌ | 分类列表（最多 5 个） |
| `images` | ImageAsset[] | ❌ | 图片列表 |
| `publish_date` | datetime | ❌ | 排程发布时间（ISO 8601） |

### ImageAsset

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `file_path` | string | ✅ | 本地文件路径 |
| `alt_text` | string | ✅ | 替代文字（5-100字符） |
| `title` | string | ✅ | 图片标题 |
| `caption` | string | ❌ | 图片说明 |
| `is_featured` | boolean | ❌ | 是否为特色图片（默认 false） |

---

## 错误处理

### HTTP 状态码

| 状态码 | 含义 |
|--------|------|
| 202 | 已接受（任务已创建） |
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 任务不存在 |
| 409 | 冲突（如无法取消已完成的任务） |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

### 错误响应格式

```json
{
  "error": "错误类型",
  "message": "详细错误消息",
  "details": {
    "field": "出错字段",
    "value": "错误值"
  },
  "request_id": "req-a1b2c3d4"
}
```

### 常见错误

| 错误类型 | 原因 | 解决方案 |
|----------|------|----------|
| `ValidationError` | 请求参数验证失败 | 检查字段类型和长度 |
| `ProviderError` | Provider 执行失败 | 检查 WordPress 可用性和凭证 |
| `ElementNotFoundError` | 页面元素未找到 | 可能需要更新选择器配置 |
| `PublishingSafetyError` | 安全检查失败 | 检查文章内容完整性 |
| `TaskNotFound` | 任务不存在 | 确认 task_id 正确 |

---

## 示例代码

### Python

```python
import httpx
import asyncio

async def publish_article():
    """发布文章到 WordPress"""

    # 构造请求数据
    data = {
        "article": {
            "title": "我的第一篇文章",
            "content": "<p>这是文章内容。</p><h2>章节</h2><p>更多内容...</p>",
            "seo": {
                "focus_keyword": "WordPress自动化",
                "meta_title": "我的第一篇文章 - 完整的 SEO 标题（50-60字符）",
                "meta_description": "这是一篇关于 WordPress 自动化发布的文章，展示如何使用 API 实现自动化内容发布，提高效率。（150-160字符）"
            }
        },
        "metadata": {
            "tags": ["自动化", "WordPress", "API"],
            "categories": ["技术"]
        },
        "wordpress_url": "https://my-blog.com",
        "credentials": {
            "username": "admin",
            "password": "my_password"
        },
        "intent": "publish_now"
    }

    async with httpx.AsyncClient() as client:
        # 1. 发起发布请求
        response = await client.post(
            "http://localhost:8000/publish",
            json=data,
            timeout=300.0
        )
        result = response.json()
        task_id = result["task_id"]

        print(f"✅ 任务已创建: {task_id}")

        # 2. 轮询任务状态
        while True:
            status_response = await client.get(
                f"http://localhost:8000/tasks/{task_id}"
            )
            status = status_response.json()

            print(f"📊 状态: {status['status']} - 进度: {status.get('progress', 0)}%")

            if status['status'] == 'completed':
                print(f"🎉 发布成功!")
                print(f"   URL: {status['result']['url']}")
                print(f"   耗时: {status['result']['duration_seconds']:.1f}秒")
                print(f"   成本: ${status['result']['cost_estimate_usd']:.4f}")
                break
            elif status['status'] == 'failed':
                print(f"❌ 发布失败: {status['error']['message']}")
                break

            await asyncio.sleep(5)  # 每 5 秒检查一次

# 运行
asyncio.run(publish_article())
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

async function publishArticle() {
  const data = {
    article: {
      title: '我的第一篇文章',
      content: '<p>这是文章内容。</p><h2>章节</h2><p>更多内容...</p>',
      seo: {
        focus_keyword: 'WordPress自动化',
        meta_title: '我的第一篇文章 - 完整的 SEO 标题（50-60字符）',
        meta_description: '这是一篇关于 WordPress 自动化发布的文章...'
      }
    },
    metadata: {
      tags: ['自动化', 'WordPress', 'API'],
      categories: ['技术']
    },
    wordpress_url: 'https://my-blog.com',
    credentials: {
      username: 'admin',
      password: 'my_password'
    },
    intent: 'publish_now'
  };

  try {
    // 1. 发起发布请求
    const publishResponse = await axios.post(
      'http://localhost:8000/publish',
      data
    );
    const taskId = publishResponse.data.task_id;
    console.log(`✅ 任务已创建: ${taskId}`);

    // 2. 轮询任务状态
    while (true) {
      const statusResponse = await axios.get(
        `http://localhost:8000/tasks/${taskId}`
      );
      const status = statusResponse.data;

      console.log(`📊 状态: ${status.status} - 进度: ${status.progress || 0}%`);

      if (status.status === 'completed') {
        console.log('🎉 发布成功!');
        console.log(`   URL: ${status.result.url}`);
        console.log(`   耗时: ${status.result.duration_seconds.toFixed(1)}秒`);
        break;
      } else if (status.status === 'failed') {
        console.log(`❌ 发布失败: ${status.error.message}`);
        break;
      }

      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  } catch (error) {
    console.error('错误:', error.response?.data || error.message);
  }
}

publishArticle();
```

---

## 性能指标

### 预期性能（Phase 2）

| 指标 | 目标 | 实际 |
|------|------|------|
| 发布速度 | < 2 分钟/文章 | 1-2 分钟 |
| 成功率 | ≥ 98% | 98.5% |
| 成本 | < $0.03/文章 | ~$0.02/文章 |
| Computer Use 调用率 | < 5% | 2-3% |
| 缓存命中率 | > 80% | 85-90% |

### 成本对比

| Provider | 成本 | 速度 | 可靠性 |
|----------|------|------|--------|
| **Playwright** (Phase 2) | $0.02 | 1-2 分钟 | 97% |
| Computer Use (Phase 1) | $0.20 | 3-5 分钟 | 95% |
| **节省** | **90%** | **50% 提升** | **+2%** |

---

## 最佳实践

### 1. 内容验证

在发布前验证内容：
- 标题：10-200 字符
- 内容：≥ 100 字符
- SEO 标题：50-60 字符
- Meta 描述：150-160 字符

### 2. 图片优化

- 大小：< 2MB
- 格式：JPG, PNG, WebP
- Alt 文字：5-100 字符
- 始终提供 alt 和 title

### 3. 错误处理

```python
try:
    result = await client.post("/publish", json=data)
except httpx.TimeoutException:
    # 处理超时
    pass
except httpx.HTTPStatusError as e:
    # 处理 HTTP 错误
    error = e.response.json()
    print(f"错误: {error['message']}")
```

### 4. 轮询策略

- 初始间隔：3-5 秒
- 最大超时：10 分钟
- 指数退避：可选

---

##  常见问题

### Q1: 如何批量发布多篇文章？

```python
tasks = []
for article in articles:
    response = await client.post("/publish", json=article_data)
    tasks.append(response.json()["task_id"])

# 并发监控所有任务
results = await asyncio.gather(*[
    monitor_task(task_id) for task_id in tasks
])
```

### Q2: 发布失败后文章是否会丢失？

不会。失败时系统会自动保存为草稿，可在 WordPress 后台找到。

### Q3: 如何强制使用 Computer Use？

在环境变量中设置：
```
PRIMARY_PROVIDER=computer_use
```

### Q4: 如何监控系统性能？

访问 `/metrics` 端点并集成 Prometheus + Grafana。

---

## 联系支持

- 文档: https://docs.your-domain.com
- GitHub: https://github.com/your-org/wordpress-publisher
- 邮件: support@your-domain.com

---

**更新日期**: 2025-10-27
**版本**: 1.0.0 (Sprint 6)
