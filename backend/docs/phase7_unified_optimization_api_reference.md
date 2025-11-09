# Phase 7 Unified Optimization API Reference

## 概述

Phase 7 统一AI优化服务提供了一套完整的REST API端点，用于生成和管理文章的AI优化建议（标题、SEO、FAQ）。

**关键特性:**
- 📊 单次API调用生成所有优化建议
- 💰 相比分离调用节省40-60%成本
- ⏱️ 相比分离调用节省30-40%时间
- 💾 自动缓存机制，二次访问零成本
- 📈 完整的监控和成本追踪

**API Base URL:**
- Development: `http://localhost:8000`
- Production: `https://your-domain.com`

**认证:** 所有端点需要有效的认证token（具体实现根据项目配置）

---

## 目录

1. [优化生成端点](#优化生成端点)
   - [POST /v1/articles/{article_id}/generate-all-optimizations](#1-生成统一优化建议)
   - [GET /v1/articles/{article_id}/optimizations](#2-获取缓存的优化建议)
   - [GET /v1/articles/{article_id}/optimization-status](#3-检查优化状态)
   - [DELETE /v1/articles/{article_id}/optimizations](#4-删除优化建议)

2. [监控端点](#监控端点)
   - [GET /v1/monitoring/optimization/cost-statistics](#1-获取成本统计)
   - [GET /v1/monitoring/optimization/performance-statistics](#2-获取性能统计)
   - [GET /v1/monitoring/optimization/expensive-articles](#3-获取高成本文章)
   - [GET /v1/monitoring/optimization/report](#4-获取综合报告)
   - [GET /v1/monitoring/optimization/cost-report/formatted](#5-获取格式化报告)

3. [数据模型](#数据模型)
4. [错误处理](#错误处理)
5. [使用场景](#使用场景)
6. [最佳实践](#最佳实践)

---

## 优化生成端点

### 1. 生成统一优化建议

生成标题、SEO和FAQ优化建议（单次AI调用）。

**端点:** `POST /v1/articles/{article_id}/generate-all-optimizations`

**描述:**
- 调用Claude API一次性生成所有优化建议
- 结果自动缓存到数据库
- 支持强制重新生成选项

#### 请求

**路径参数:**
| 参数 | 类型 | 必需 | 描述 |
|-----|------|-----|------|
| article_id | integer | 是 | 文章ID |

**请求体:**
```json
{
  "regenerate": false,
  "options": {
    "include_title": true,
    "include_seo": true,
    "include_tags": true,
    "include_faqs": true,
    "faq_target_count": 10
  }
}
```

**字段说明:**
- `regenerate` (boolean, default: false): 强制重新生成，即使缓存存在
- `options.include_title` (boolean, default: true): 是否生成标题建议
- `options.include_seo` (boolean, default: true): 是否生成SEO建议
- `options.include_tags` (boolean, default: true): 是否生成标签建议
- `options.include_faqs` (boolean, default: true): 是否生成FAQ
- `options.faq_target_count` (integer, 3-15, default: 10): 目标FAQ数量

#### 响应

**成功响应 (200 OK):**

```json
{
  "title_suggestions": {
    "suggested_title_sets": [
      {
        "id": "option_1",
        "title_prefix": "完整",
        "title_main": "Python编程从入门到精通",
        "title_suffix": "2024最新版",
        "full_title": "完整 | Python编程从入门到精通 | 2024最新版",
        "score": 95,
        "strengths": [
          "包含核心关键词",
          "明确受众层次",
          "时效性强"
        ],
        "type": "comprehensive_guide",
        "recommendation": "综合性强，适合初学者到进阶用户",
        "character_count": {
          "prefix": 2,
          "main": 12,
          "suffix": 7,
          "total": 21
        }
      },
      {
        "id": "option_2",
        "title_prefix": null,
        "title_main": "如何用Python开发Web应用",
        "title_suffix": "实战教程",
        "full_title": "如何用Python开发Web应用 | 实战教程",
        "score": 90,
        "strengths": [
          "问题导向",
          "突出实战价值",
          "清晰明了"
        ],
        "type": "how_to",
        "recommendation": "适合动手实践的学习者",
        "character_count": {
          "prefix": 0,
          "main": 13,
          "suffix": 4,
          "total": 17
        }
      }
    ],
    "optimization_notes": [
      "建议使用Option 1作为主标题",
      "Option 2可作为备选",
      "注意标题长度控制在30字以内"
    ]
  },
  "seo_suggestions": {
    "seo_keywords": {
      "focus_keyword": "Python编程",
      "focus_keyword_rationale": "核心主题，搜索量大，与内容高度相关",
      "primary_keywords": [
        "Python教程",
        "Python入门",
        "Web开发",
        "编程学习"
      ],
      "secondary_keywords": [
        "Python框架",
        "Django",
        "Flask",
        "数据分析",
        "机器学习",
        "爬虫开发"
      ],
      "keyword_difficulty": {
        "Python编程": "medium",
        "Python教程": "high",
        "Web开发": "high"
      },
      "search_volume_estimate": {
        "Python编程": "10k-50k/month",
        "Python教程": "50k-100k/month"
      }
    },
    "meta_description": {
      "original_meta_description": "学习Python编程的基础知识",
      "suggested_meta_description": "完整的Python编程教程，涵盖从基础语法到Web开发、数据分析的实战案例。适合初学者和进阶开发者，2024最新内容更新。",
      "meta_description_improvements": [
        "增加了具体内容范围",
        "突出目标受众",
        "加入时效性"
      ],
      "meta_description_score": 92
    },
    "tags": {
      "suggested_tags": [
        {
          "tag": "Python",
          "relevance": 1.0,
          "type": "primary"
        },
        {
          "tag": "编程教程",
          "relevance": 0.95,
          "type": "primary"
        },
        {
          "tag": "Web开发",
          "relevance": 0.85,
          "type": "secondary"
        },
        {
          "tag": "数据分析",
          "relevance": 0.80,
          "type": "secondary"
        },
        {
          "tag": "Django",
          "relevance": 0.75,
          "type": "secondary"
        },
        {
          "tag": "机器学习",
          "relevance": 0.70,
          "type": "trending"
        }
      ],
      "recommended_tag_count": "6-8 tags recommended",
      "tag_strategy": "使用2个核心标签 + 4-6个相关标签，平衡覆盖面和精准度"
    }
  },
  "faqs": [
    {
      "question": "Python适合初学者学习吗？",
      "answer": "非常适合。Python语法简洁清晰，上手快，有丰富的学习资源和社区支持。",
      "question_type": "factual",
      "search_intent": "informational",
      "keywords_covered": ["Python", "初学者", "学习"],
      "confidence": 0.95
    },
    {
      "question": "学习Python需要多长时间？",
      "answer": "基础语法1-2个月可掌握，达到就业水平需要3-6个月持续练习。具体时间因人而异。",
      "question_type": "factual",
      "search_intent": "informational",
      "keywords_covered": ["学习", "时间", "入门"],
      "confidence": 0.90
    },
    {
      "question": "Python可以开发哪些类型的应用？",
      "answer": "Web应用、数据分析、机器学习、自动化脚本、爬虫、游戏开发等多个领域。",
      "question_type": "factual",
      "search_intent": "informational",
      "keywords_covered": ["应用", "Web开发", "数据分析"],
      "confidence": 0.92
    }
  ],
  "generation_metadata": {
    "total_cost_usd": 0.0342,
    "total_tokens": 3542,
    "input_tokens": 2100,
    "output_tokens": 1442,
    "duration_ms": 8234,
    "savings_vs_separate": {
      "original_tokens": 5800,
      "original_cost_usd": 0.0574,
      "original_duration_ms": 13500,
      "saved_tokens": 2258,
      "saved_cost_usd": 0.0232,
      "saved_duration_ms": 5266,
      "cost_savings_percentage": 40.4,
      "time_savings_percentage": 39.0
    },
    "cached": false,
    "message": "Freshly generated"
  }
}
```

**缓存响应 (200 OK):**
当缓存存在且 `regenerate=false` 时，返回结构相同，但：
```json
{
  "generation_metadata": {
    "cached": true,
    "message": "Loaded from cache"
  }
}
```

#### 错误响应

**404 Not Found - 文章不存在:**
```json
{
  "detail": "Article 123 not found"
}
```

**400 Bad Request - 文章无内容:**
```json
{
  "detail": "Article has no content to optimize. Please ensure article has body or body_html."
}
```

**500 Internal Server Error - AI API错误:**
```json
{
  "detail": "Failed to generate optimizations: API rate limit exceeded"
}
```

#### cURL 示例

```bash
# 首次生成
curl -X POST "http://localhost:8000/v1/articles/123/generate-all-optimizations" \
  -H "Content-Type: application/json" \
  -d '{
    "regenerate": false,
    "options": {
      "faq_target_count": 8
    }
  }'

# 强制重新生成
curl -X POST "http://localhost:8000/v1/articles/123/generate-all-optimizations" \
  -H "Content-Type: application/json" \
  -d '{
    "regenerate": true
  }'
```

---

### 2. 获取缓存的优化建议

快速检索已生成的优化建议，无需AI API调用。

**端点:** `GET /v1/articles/{article_id}/optimizations`

**描述:**
- 从数据库加载缓存结果
- 零成本、即时返回
- 用于Step 3显示SEO和FAQ建议

#### 请求

**路径参数:**
| 参数 | 类型 | 必需 | 描述 |
|-----|------|-----|------|
| article_id | integer | 是 | 文章ID |

**无请求体**

#### 响应

**成功响应 (200 OK):**
返回格式与 `generate-all-optimizations` 相同，但 `generation_metadata.cached = true`。

#### 错误响应

**404 Not Found - 未生成优化:**
```json
{
  "detail": "No optimizations found for article 123. Please generate them first."
}
```

#### cURL 示例

```bash
curl "http://localhost:8000/v1/articles/123/optimizations"
```

---

### 3. 检查优化状态

检查文章的优化生成状态和元数据。

**端点:** `GET /v1/articles/{article_id}/optimization-status`

**描述:**
- 检查是否已生成优化
- 获取生成时间和成本
- 查看各类优化的可用性

#### 请求

**路径参数:**
| 参数 | 类型 | 必需 | 描述 |
|-----|------|-----|------|
| article_id | integer | 是 | 文章ID |

#### 响应

**成功响应 (200 OK):**
```json
{
  "article_id": 123,
  "generated": true,
  "generated_at": "2025-01-08T10:30:45.123456Z",
  "cost_usd": 0.0342,
  "has_title_suggestions": true,
  "has_seo_suggestions": true,
  "has_faqs": true,
  "faq_count": 8
}
```

**未生成状态:**
```json
{
  "article_id": 123,
  "generated": false,
  "generated_at": null,
  "cost_usd": null,
  "has_title_suggestions": false,
  "has_seo_suggestions": false,
  "has_faqs": false,
  "faq_count": 0
}
```

#### cURL 示例

```bash
curl "http://localhost:8000/v1/articles/123/optimization-status"
```

---

### 4. 删除优化建议

删除文章的所有优化建议。

**端点:** `DELETE /v1/articles/{article_id}/optimizations`

**描述:**
- 删除标题、SEO、FAQ所有建议
- 重置article的优化元数据
- 用于重新生成前清理数据

#### 请求

**路径参数:**
| 参数 | 类型 | 必需 | 描述 |
|-----|------|-----|------|
| article_id | integer | 是 | 文章ID |

#### 响应

**成功响应 (204 No Content):**
无响应体

#### 错误响应

**404 Not Found:**
```json
{
  "detail": "Article 123 not found"
}
```

#### cURL 示例

```bash
curl -X DELETE "http://localhost:8000/v1/articles/123/optimizations"
```

---

## 监控端点

### 1. 获取成本统计

获取指定时间范围内的成本统计数据。

**端点:** `GET /v1/monitoring/optimization/cost-statistics`

#### 请求

**查询参数:**
| 参数 | 类型 | 默认值 | 范围 | 描述 |
|-----|------|-------|-----|------|
| days | integer | 30 | 1-90 | 分析的天数 |
| limit | integer | 100 | 1-500 | 最大文章数量 |

#### 响应

**成功响应 (200 OK):**
```json
{
  "period_days": 30,
  "article_count": 156,
  "total_cost_usd": 12.4589,
  "average_cost_usd": 0.0798,
  "min_cost_usd": 0.0234,
  "max_cost_usd": 0.1456,
  "median_cost_usd": 0.0789,
  "estimated_monthly_cost_usd": 12.46
}
```

#### cURL 示例

```bash
# 获取最近7天成本
curl "http://localhost:8000/v1/monitoring/optimization/cost-statistics?days=7&limit=50"
```

---

### 2. 获取性能统计

获取性能指标，包括缓存命中率。

**端点:** `GET /v1/monitoring/optimization/performance-statistics`

#### 请求

**查询参数:**
| 参数 | 类型 | 默认值 | 范围 | 描述 |
|-----|------|-------|-----|------|
| days | integer | 7 | 1-30 | 分析的天数 |

#### 响应

**成功响应 (200 OK):**
```json
{
  "period_days": 7,
  "total_optimizations": 67,
  "cache_hit_rate": 12.5,
  "recent_optimizations": [
    {
      "article_id": 123,
      "generated_at": "2025-01-08T10:30:00Z",
      "cost_usd": 0.0845
    },
    {
      "article_id": 124,
      "generated_at": "2025-01-08T09:15:00Z",
      "cost_usd": 0.0678
    }
  ]
}
```

#### cURL 示例

```bash
curl "http://localhost:8000/v1/monitoring/optimization/performance-statistics?days=7"
```

---

### 3. 获取高成本文章

识别成本最高的优化操作。

**端点:** `GET /v1/monitoring/optimization/expensive-articles`

#### 请求

**查询参数:**
| 参数 | 类型 | 默认值 | 范围 | 描述 |
|-----|------|-------|-----|------|
| days | integer | 30 | 1-90 | 分析的天数 |
| limit | integer | 10 | 1-50 | 返回文章数量 |

#### 响应

**成功响应 (200 OK):**
```json
{
  "period_days": 30,
  "count": 10,
  "articles": [
    {
      "article_id": 456,
      "title": "深度学习完整指南",
      "cost_usd": 0.1456,
      "generated_at": "2025-01-07T14:20:00Z",
      "body_length": 15234
    },
    {
      "article_id": 789,
      "title": "区块链技术详解",
      "cost_usd": 0.1289,
      "generated_at": "2025-01-06T11:45:00Z",
      "body_length": 13567
    }
  ]
}
```

#### cURL 示例

```bash
curl "http://localhost:8000/v1/monitoring/optimization/expensive-articles?days=30&limit=5"
```

---

### 4. 获取综合报告

生成包含所有指标的完整监控报告。

**端点:** `GET /v1/monitoring/optimization/report`

#### 请求

**查询参数:**
| 参数 | 类型 | 默认值 | 范围 | 描述 |
|-----|------|-------|-----|------|
| days | integer | 7 | 1-30 | 分析的天数 |

#### 响应

**成功响应 (200 OK):**
```json
{
  "report_generated_at": "2025-01-08T15:30:00Z",
  "period_days": 7,
  "cost_statistics": {
    "period_days": 7,
    "article_count": 45,
    "total_cost_usd": 3.2145,
    "average_cost_usd": 0.0714,
    "min_cost_usd": 0.0234,
    "max_cost_usd": 0.1123,
    "median_cost_usd": 0.0689,
    "estimated_monthly_cost_usd": 13.78
  },
  "performance_statistics": {
    "period_days": 7,
    "total_optimizations": 45,
    "cache_hit_rate": 15.6,
    "recent_optimizations": [...]
  },
  "top_expensive_articles": [...],
  "summary": {
    "total_articles_optimized": 45,
    "total_cost_usd": 3.2145,
    "average_cost_per_article": 0.0714,
    "estimated_monthly_cost": 13.78,
    "cache_hit_rate": 15.6
  }
}
```

#### cURL 示例

```bash
curl "http://localhost:8000/v1/monitoring/optimization/report?days=7"
```

---

### 5. 获取格式化报告

获取人类可读的文本格式成本报告。

**端点:** `GET /v1/monitoring/optimization/cost-report/formatted`

#### 请求

**查询参数:**
| 参数 | 类型 | 默认值 | 范围 | 描述 |
|-----|------|-------|-----|------|
| days | integer | 30 | 1-90 | 分析的天数 |
| limit | integer | 100 | 1-500 | 最大文章数量 |

#### 响应

**成功响应 (200 OK):**
```json
{
  "report": "📊 Cost Statistics Report (30 days)\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📈 Article Count: 156\n\n💰 Cost Metrics:\n   • Total Cost:    $12.4589\n   • Average Cost:  $0.0798 per article\n   • Min Cost:      $0.0234\n   • Max Cost:      $0.1456\n   • Median Cost:   $0.0789\n\n📅 Projection:\n   • Est. Monthly Cost: $12.46\n   • (Based on 30-day trend)\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
  "statistics": {
    "period_days": 30,
    "article_count": 156,
    "total_cost_usd": 12.4589,
    ...
  }
}
```

#### cURL 示例

```bash
curl "http://localhost:8000/v1/monitoring/optimization/cost-report/formatted?days=30"
```

---

## 数据模型

### TitleOptionData

标题优化选项的数据模型。

```typescript
{
  id: string;                    // 选项ID，如 "option_1"
  title_prefix: string | null;   // 前缀 (2-6字符)
  title_main: string;            // 主标题 (15-30字符)
  title_suffix: string | null;   // 后缀 (4-12字符)
  full_title: string;            // 完整标题（含分隔符）
  score: number;                 // 质量评分 (0-100)
  strengths: string[];           // 关键优势列表
  type: string;                  // 标题类型
  recommendation: string;        // 推荐理由
  character_count: {
    prefix: number;
    main: number;
    suffix: number;
    total: number;
  };
}
```

**type 可选值:**
- `data_driven` - 数据驱动型
- `authority_backed` - 权威背书型
- `how_to` - 教程型
- `comprehensive_guide` - 综合指南型
- `question_based` - 问题导向型

### SEOKeywordsData

SEO关键词数据模型。

```typescript
{
  focus_keyword: string | null;           // 焦点关键词
  focus_keyword_rationale: string | null; // 选择理由
  primary_keywords: string[];             // 主关键词 (3-5个)
  secondary_keywords: string[];           // 次关键词 (5-10个)
  keyword_difficulty: object | null;      // 关键词难度
  search_volume_estimate: object | null;  // 搜索量估计
}
```

### FAQData

FAQ数据模型。

```typescript
{
  question: string;               // FAQ问题
  answer: string;                 // FAQ答案 (50-150字)
  question_type: string | null;   // 问题类型
  search_intent: string | null;   // 搜索意图
  keywords_covered: string[];     // 覆盖的关键词
  confidence: number | null;      // 置信度 (0-1)
}
```

**question_type 可选值:**
- `factual` - 事实型
- `how_to` - 操作型
- `comparison` - 对比型
- `definition` - 定义型

**search_intent 可选值:**
- `informational` - 信息型
- `navigational` - 导航型
- `transactional` - 交易型

### GenerationMetadata

生成元数据模型。

```typescript
{
  total_cost_usd: number | null;        // 总成本 (USD)
  total_tokens: number | null;          // 总tokens
  input_tokens: number | null;          // 输入tokens
  output_tokens: number | null;         // 输出tokens
  duration_ms: number | null;           // 耗时 (毫秒)
  savings_vs_separate: {                // 节省对比
    original_tokens: number;
    original_cost_usd: number;
    original_duration_ms: number;
    saved_tokens: number;
    saved_cost_usd: number;
    saved_duration_ms: number;
    cost_savings_percentage: number;
    time_savings_percentage: number;
  } | null;
  cached: boolean;                      // 是否缓存
  message: string | null;               // 附加消息
}
```

---

## 错误处理

### HTTP 状态码

| 状态码 | 含义 | 使用场景 |
|-------|-----|---------|
| 200 | OK | 请求成功 |
| 204 | No Content | 删除成功 |
| 400 | Bad Request | 请求参数错误、文章状态无效 |
| 404 | Not Found | 文章不存在、优化未生成 |
| 500 | Internal Server Error | AI API错误、数据库错误 |

### 错误响应格式

所有错误响应使用统一格式：

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误及解决方案

#### 1. "Article not found"
**原因:** 指定的文章ID不存在

**解决:** 检查article_id是否正确

#### 2. "No optimizations found"
**原因:** 文章尚未生成优化建议

**解决:** 先调用 `generate-all-optimizations` 端点

#### 3. "Article has no content to optimize"
**原因:** 文章的body和body_html都为空

**解决:** 确保文章已经过解析，有完整内容

#### 4. "Failed to generate optimizations: API rate limit exceeded"
**原因:** Anthropic API限流

**解决:** 稍后重试，或联系管理员增加配额

#### 5. "Optimizations already exist"
**原因:** 优化已存在，但未设置 `regenerate=true`

**解决:** 设置 `regenerate: true` 强制重新生成

---

## 使用场景

### 场景1: Step 2完成后自动生成优化

**工作流:**
1. 用户完成Step 2（文章解析确认）
2. 前端自动调用 `POST /articles/{id}/generate-all-optimizations`
3. 后台生成优化建议并缓存
4. Step 3可立即加载缓存结果

**代码示例 (TypeScript):**
```typescript
// Step 2确认后自动生成
async function onParsingConfirmed(articleId: number) {
  try {
    // 生成优化建议
    const response = await fetch(
      `/v1/articles/${articleId}/generate-all-optimizations`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ regenerate: false })
      }
    );

    if (!response.ok) {
      throw new Error('Generation failed');
    }

    const data = await response.json();
    console.log(`Generated optimizations, cost: $${data.generation_metadata.total_cost_usd}`);

    // 跳转到Step 3
    navigateToStep3(articleId);
  } catch (error) {
    console.error('Failed to generate optimizations:', error);
    showErrorMessage('优化生成失败，请稍后重试');
  }
}
```

### 场景2: Step 3加载缓存优化

**工作流:**
1. 用户进入Step 3
2. 前端调用 `GET /articles/{id}/optimizations`
3. 从缓存加载，零成本、即时返回
4. 显示SEO和FAQ建议

**代码示例:**
```typescript
async function loadOptimizations(articleId: number) {
  try {
    const response = await fetch(`/v1/articles/${articleId}/optimizations`);

    if (response.status === 404) {
      // 未生成优化，显示提示
      showMessage('优化建议尚未生成，正在生成中...');
      await generateOptimizations(articleId);
      return;
    }

    const data = await response.json();

    // 显示优化建议
    displayTitleSuggestions(data.title_suggestions);
    displaySEOSuggestions(data.seo_suggestions);
    displayFAQs(data.faqs);

    // 显示缓存状态
    if (data.generation_metadata.cached) {
      showCacheIndicator('从缓存加载');
    }
  } catch (error) {
    console.error('Failed to load optimizations:', error);
  }
}
```

### 场景3: 重新生成优化

**工作流:**
1. 用户点击"重新生成"按钮
2. 前端调用 `POST /articles/{id}/generate-all-optimizations` with `regenerate: true`
3. 重新调用AI API生成
4. 更新显示

**代码示例:**
```typescript
async function regenerateOptimizations(articleId: number) {
  const confirmed = confirm('确定要重新生成优化建议吗？这将产生API调用费用。');
  if (!confirmed) return;

  try {
    showLoading('正在重新生成...');

    const response = await fetch(
      `/v1/articles/${articleId}/generate-all-optimizations`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          regenerate: true,
          options: {
            faq_target_count: 8  // 可调整选项
          }
        })
      }
    );

    const data = await response.json();
    hideLoading();

    // 显示新结果
    displayOptimizations(data);

    showMessage(
      `重新生成完成，成本: $${data.generation_metadata.total_cost_usd.toFixed(4)}`
    );
  } catch (error) {
    hideLoading();
    showError('重新生成失败');
  }
}
```

### 场景4: 监控成本

**工作流:**
1. 管理员定期查看监控仪表板
2. 调用监控API获取统计数据
3. 分析成本趋势
4. 识别高成本文章并优化

**代码示例:**
```typescript
async function loadMonitoringDashboard() {
  try {
    // 获取7天成本统计
    const costStats = await fetch(
      '/v1/monitoring/optimization/cost-statistics?days=7'
    ).then(r => r.json());

    // 获取性能统计
    const perfStats = await fetch(
      '/v1/monitoring/optimization/performance-statistics?days=7'
    ).then(r => r.json());

    // 获取高成本文章
    const expensiveArticles = await fetch(
      '/v1/monitoring/optimization/expensive-articles?days=7&limit=5'
    ).then(r => r.json());

    // 显示仪表板
    displayCostChart(costStats);
    displayPerformanceMetrics(perfStats);
    displayExpensiveArticlesList(expensiveArticles.articles);

    // 显示关键指标
    document.getElementById('total-cost').textContent =
      `$${costStats.total_cost_usd.toFixed(2)}`;
    document.getElementById('avg-cost').textContent =
      `$${costStats.average_cost_usd.toFixed(4)}`;
    document.getElementById('cache-hit-rate').textContent =
      `${perfStats.cache_hit_rate.toFixed(1)}%`;
  } catch (error) {
    console.error('Failed to load monitoring data:', error);
  }
}
```

---

## 最佳实践

### 1. 成本优化

**利用缓存机制:**
- 默认使用 `regenerate: false`
- 只在必要时重新生成
- 预期缓存命中率: 80%+

**合理设置FAQ数量:**
```typescript
// 根据文章长度调整
const faqCount = articleLength < 1000 ? 5 :
                 articleLength < 3000 ? 8 : 10;

await generateOptimizations(articleId, { faq_target_count: faqCount });
```

**批量处理:**
```typescript
// 避免频繁调用
// ❌ 不好的做法
for (const article of articles) {
  await generateOptimizations(article.id);
}

// ✅ 好的做法
await Promise.all(
  articles.map(a => generateOptimizations(a.id))
);
```

### 2. 错误处理

**实现重试逻辑:**
```typescript
async function generateWithRetry(articleId: number, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await generateOptimizations(articleId);
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(1000 * (i + 1));  // 指数退避
    }
  }
}
```

**优雅降级:**
```typescript
async function loadOptimizationsWithFallback(articleId: number) {
  try {
    return await fetch(`/v1/articles/${articleId}/optimizations`).then(r => r.json());
  } catch (error) {
    // 降级：返回部分数据或默认值
    return {
      title_suggestions: { suggested_title_sets: [], optimization_notes: [] },
      seo_suggestions: { seo_keywords: {}, meta_description: {}, tags: {} },
      faqs: [],
      generation_metadata: { cached: false, message: 'Failed to load' }
    };
  }
}
```

### 3. 用户体验

**显示进度指示:**
```typescript
async function generateOptimizationsWithProgress(articleId: number) {
  showProgress('正在生成优化建议...', 0);

  const response = await fetch(
    `/v1/articles/${articleId}/generate-all-optimizations`,
    { method: 'POST', body: JSON.stringify({}) }
  );

  showProgress('正在生成标题建议...', 33);
  // 实际上是单次调用，但可以模拟进度
  await sleep(500);

  showProgress('正在生成SEO建议...', 66);
  await sleep(500);

  showProgress('正在生成FAQ...', 90);
  const data = await response.json();

  showProgress('完成！', 100);
  return data;
}
```

**缓存状态展示:**
```tsx
{data.generation_metadata.cached && (
  <Badge color="green">
    <CacheIcon /> 从缓存加载
  </Badge>
)}

{data.generation_metadata.savings_vs_separate && (
  <Tooltip content={`节省成本: $${data.generation_metadata.savings_vs_separate.saved_cost_usd.toFixed(4)}`}>
    <Badge color="blue">
      节省 {data.generation_metadata.savings_vs_separate.cost_savings_percentage.toFixed(0)}%
    </Badge>
  </Tooltip>
)}
```

### 4. 监控告警

**设置成本告警:**
```typescript
// 每日成本检查
async function checkDailyCostAlert() {
  const stats = await fetch(
    '/v1/monitoring/optimization/cost-statistics?days=1'
  ).then(r => r.json());

  if (stats.total_cost_usd > DAILY_BUDGET * 1.1) {
    sendAlert({
      level: 'HIGH',
      message: `Daily cost exceeded: $${stats.total_cost_usd.toFixed(2)}`,
      details: stats
    });
  }
}
```

**性能监控:**
```typescript
// 检测慢响应
async function trackOptimizationPerformance(articleId: number) {
  const startTime = Date.now();

  try {
    const result = await generateOptimizations(articleId);
    const duration = Date.now() - startTime;

    if (duration > 35000) {  // 35秒阈值
      logWarning('slow_optimization', {
        article_id: articleId,
        duration_ms: duration
      });
    }

    return result;
  } catch (error) {
    logError('optimization_failed', { article_id: articleId, error });
    throw error;
  }
}
```

---

## 附录

### A. FastAPI自动文档

访问以下URL查看交互式API文档（开发环境）:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### B. 成本计算公式

```
Total Cost = (Input Tokens / 1,000,000) × $3.00 +
             (Output Tokens / 1,000,000) × $15.00
```

**示例:**
- Input: 2100 tokens
- Output: 1442 tokens
- Cost = (2100/1M × $3) + (1442/1M × $15) = $0.0063 + $0.0216 = $0.0279

### C. 相关文档

- [Phase 7 统一优化服务设计](./phase7_unified_ai_optimization_service.md)
- [优化监控指南](./optimization_monitoring_guide.md)
- [文章审核SEO工作流](./article_proofreading_seo_workflow.md)
- [单Prompt设计](./single_prompt_design.md)

---

**文档版本:** 1.0
**最后更新:** 2025-01-08
**维护者:** CMS Automation Team
