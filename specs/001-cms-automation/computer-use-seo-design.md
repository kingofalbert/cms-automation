# Computer Use SEO 自动化设计方案

## 概述

实现使用 Anthropic Computer Use API 自动分析文章 SEO 并在 CMS 后台完成设置的功能。

## 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                     Article Generation Flow                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Generate Article + SEO Data (Claude Messages API)           │
│     - Article Title & Body                                       │
│     - Meta Title (60 chars)                                      │
│     - Meta Description (155 chars)                               │
│     - Focus Keywords                                             │
│     - Open Graph Tags                                            │
│     - Schema.org Data                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Save to Database (PostgreSQL)                               │
│     - Article table (title, body, status)                       │
│     - article_metadata JSONB (seo_data)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Computer Use CMS Automation (Celery Task)                   │
│     - Launch browser session                                     │
│     - Login to WordPress wp-admin                                │
│     - Create new post                                            │
│     - Set Yoast SEO / RankMath settings                          │
│     - Upload featured image (optional)                           │
│     - Publish article                                            │
│     - Capture confirmation screenshot                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Update Database with CMS Article ID & URL                    │
└─────────────────────────────────────────────────────────────────┘
```

## 技术栈

### Computer Use 环境
- **Anthropic SDK**: `anthropic` Python 包 (Computer Use API)
- **浏览器环境**: Docker 容器运行 Chromium + X11 VNC
- **屏幕分辨率**: 1920x1080 (推荐)
- **VNC Server**: TigerVNC 或 NoVNC (用于调试)

### SEO 分析
- **AI 模型**: Claude 3.5 Sonnet (支持 Computer Use)
- **SEO 标准**:
  - Meta Title: 50-60 字符
  - Meta Description: 150-160 字符
  - Focus Keyword: 主关键词 + 2-3 相关关键词
  - URL Slug: SEO 友好的 URL

### 数据模型扩展

```python
# Article.article_metadata JSONB 结构
{
    "seo": {
        "meta_title": "优化后的SEO标题",
        "meta_description": "吸引人的描述...",
        "focus_keyword": "主要关键词",
        "keywords": ["关键词1", "关键词2", "关键词3"],
        "canonical_url": "https://example.com/article-slug",
        "og_title": "社交媒体标题",
        "og_description": "社交媒体描述",
        "og_image": "https://example.com/image.jpg",
        "schema_type": "Article",
        "readability_score": 65.5,
        "seo_score": 85
    },
    "computer_use": {
        "session_id": "cu_abc123",
        "attempts": 1,
        "last_attempt_at": "2025-10-26T10:30:00Z",
        "status": "completed",
        "screenshots": [
            "https://s3.../screenshot1.png",
            "https://s3.../screenshot2.png"
        ],
        "errors": []
    }
}
```

## 实现阶段

### Phase 1: SEO 数据生成（1-2天）
- [ ] 扩展 Article 数据模型
- [ ] 创建 SEOAnalyzerService
- [ ] 集成到 ArticleGeneratorService
- [ ] 添加 API 端点返回 SEO 数据

### Phase 2: Computer Use 基础设施（2-3天）
- [ ] 配置 Docker 容器（Browser + VNC）
- [ ] 实现 ComputerUseClient 包装器
- [ ] 测试基本的浏览器操作

### Phase 3: CMS 自动化操作（3-4天）
- [ ] 实现 WordPressComputerUseAdapter
- [ ] 登录流程
- [ ] 文章创建流程
- [ ] Yoast SEO 设置流程
- [ ] 发布流程

### Phase 4: 集成和测试（2-3天）
- [ ] 创建 Celery 任务
- [ ] 错误处理和重试逻辑
- [ ] 截图保存到 S3/本地
- [ ] E2E 测试

## 成本估算

### Computer Use API 成本
- **输入 tokens**: ~1000 tokens (指令)
- **输出 tokens**: ~500 tokens (响应)
- **工具调用**: 平均 10-15 次操作
- **估算成本**: $0.15 - $0.30 per article

### 对比 REST API
- REST API: $0.02 - $0.05 per article
- Computer Use: $0.15 - $0.30 per article
- **成本增加**: 3-6倍

### 建议策略
1. 优先使用 REST API（如果 CMS 支持）
2. Computer Use 作为备选（复杂操作或无 API）
3. 添加配置选项允许用户选择

## 监控和调试

### 日志记录
- 记录每次 Computer Use 会话
- 保存操作截图（每个关键步骤）
- 记录失败原因和重试次数

### 性能指标
- 平均操作时间: 2-5 分钟
- 成功率目标: >95%
- 超时设置: 10 分钟

## 安全考虑

1. **凭证管理**:
   - CMS 凭证加密存储
   - 使用 Application Password (不是主密码)

2. **会话隔离**:
   - 每个任务使用独立的浏览器会话
   - 任务完成后清理 cookies 和缓存

3. **访问控制**:
   - 限制 Computer Use 只能访问配置的 CMS URL
   - 防止 SSRF 攻击

## 下一步

1. 创建 SEO 分析服务
2. 扩展数据模型
3. 实现 Computer Use Client
4. 配置浏览器环境
