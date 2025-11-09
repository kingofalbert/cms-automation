# Phase 7 Step 3: SEO/元数据确认 - 需求分析

**文档版本**: v1.0
**创建日期**: 2025-11-08
**状态**: 需求分析中
**优先级**: P0 (Critical - 发布前必需步骤)

---

## 📋 目录

1. [需求背景](#需求背景)
2. [完整工作流](#完整工作流)
3. [Step 3 功能需求](#step-3-功能需求)
4. [数据模型设计](#数据模型设计)
5. [API 设计](#api-设计)
6. [前端 UI 设计](#前端-ui-设计)
7. [AI 服务设计](#ai-服务设计)
8. [实施计划](#实施计划)
9. [测试策略](#测试策略)
10. [验收标准](#验收标准)

---

## 🎯 需求背景

### 用户原始需求

> "解析的時候，就校驗和确认文章整体是否解析正确。只是確認解析的結構是正確的。
>
> 然後，下一步呢，就是校對。再下一步呢，就是進行AI推薦的正文外的其他元素进行确认，提供给用户推荐的SEO關鍵詞、Tag、Meta description，以及由系統AI提供的那些Q&A，以及推荐的标题等。让用户确认（APPROVE和REJECT）和更改。
>
> 這些涉及到的文章，還有一些AI搜索的优化，包括在AI搜索中常問的問題和答案，這按照原始的需求要由本系统额外提供（原文不提供）。
>
> 這幾個部分是在校對之後要加上去的环节。它應該會在校对這一步之後，再加上一個界面——第三步的界面。在整個上傳之前，還必须有這麼一步。"

### 关键发现

1. **Step 1（解析确认）**: 仅验证**结构正确性**，不涉及内容质量
2. **Step 2（正文校对）**: 只针对 `body_html` 正文内容
3. **Step 3（SEO/元数据确认）**: ⭐ **新需求**，是发布前的**必需步骤**
4. **AI搜索优化**: 系统额外生成Q&A，原文不提供

---

## 🔄 完整工作流

### 四步工作流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                         完整文章处理工作流                            │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Google Drive    │
│  导入文章         │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 1: 解析确认（Parse Confirmation）                          │
│  ─────────────────────────────────────────────────────────────   │
│  目的: 确认结构化数据解析正确                                      │
│  验证:                                                            │
│    ✓ 标题组件（title_prefix, title_main, title_suffix）         │
│    ✓ 作者信息（author_line, author_name）                        │
│    ✓ 图片（预览、源链接、caption、规格）                          │
│    ✓ 初步SEO数据（meta_description, keywords, tags - 从文档提取）│
│    ✓ 正文HTML（body_html - 清理后）                              │
│  用户操作: 确认/修正结构化数据                                     │
└────────┬─────────────────────────────────────────────────────────┘
         │ parsing_confirmed = true
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 2: 正文校对（Proofreading）                                 │
│  ─────────────────────────────────────────────────────────────   │
│  目的: 检查正文内容的语法、风格、准确性                            │
│  范围: 仅校对 body_html（不包括title/author/meta）                │
│  AI检查:                                                          │
│    • 语法错误                                                     │
│    • 标点符号                                                     │
│    • 风格一致性                                                   │
│    • 事实准确性                                                   │
│  用户操作: 接受/拒绝/修改校对建议                                  │
└────────┬─────────────────────────────────────────────────────────┘
         │ proofreading_confirmed = true
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 3: SEO/元数据确认（SEO/Metadata Enhancement）⭐ 新增        │
│  ─────────────────────────────────────────────────────────────   │
│  目的: AI优化SEO元素、生成AI搜索优化内容                           │
│  AI生成内容:                                                       │
│    1️⃣ SEO优化建议                                                 │
│       • Focus Keyword（主关键词，1个）                            │
│       • Primary Keywords（主要关键词，3-5个）                     │
│       • Secondary Keywords（次要关键词，5-10个）                  │
│       • Meta Description（150-160字符，优化版）                   │
│    2️⃣ 标题优化建议                                                │
│       • 基于title_main提供2-3个优化版本                           │
│       • SEO友好、吸引点击                                          │
│    3️⃣ 标签（Tags）建议                                            │
│       • 分析内容后推荐相关标签                                     │
│       • 热门标签 + 长尾标签组合                                    │
│    4️⃣ FAQ生成（AI搜索优化）⭐ 核心功能                             │
│       • 根据文章内容生成3-5个常见问题                              │
│       • 为每个问题生成简洁答案（50-150字）                         │
│       • 针对Perplexity/ChatGPT等AI搜索引擎优化                    │
│       • 以Schema.org FAQPage格式嵌入                              │
│  用户操作: 对每项建议 APPROVE/REJECT/MODIFY                        │
└────────┬─────────────────────────────────────────────────────────┘
         │ seo_metadata_confirmed = true
         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 4: 发布到WordPress（Publishing）                            │
│  ─────────────────────────────────────────────────────────────   │
│  • 使用确认后的所有数据                                            │
│  • 嵌入FAQ Schema到文章HTML                                       │
│  • 配置SEO插件（Yoast/Rank Math）                                 │
│  • 设置标签和分类                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📝 Step 3 功能需求

### ⚠️ 重要调整说明

根据用户反馈，**Step 1和Step 3的职责分工**如下：

**Step 1（解析+初步优化）**:
- ✅ 解析标题组件（title_prefix/main/suffix）
- ✅ **AI提供标题优化建议**（2-3个备选）⭐ 在Step 1完成
- ✅ 解析作者、图片、初步SEO（从文档提取）
- ✅ 用户确认所有结构化数据+优化后的标题

**Step 3（SEO深度优化+FAQ）**:
- ✅ SEO关键词深度分析（focus/primary/secondary）
- ✅ Meta Description AI优化
- ✅ Tags AI推荐扩展
- ✅ **FAQ生成（8-10个）** ⭐ 核心功能
- ❌ **不处理标题**（避免与Step 1重复）

---

### FR-3.1: SEO关键词优化建议

**需求描述**: AI分析文章内容，生成SEO优化的关键词建议（focus/primary/secondary三级结构）

**输入**:
- `body_html` (正文内容)
- `title_main` (主标题)
- `meta_description` (初步描述 - 来自Step 1)

**输出**:
```json
{
  "focus_keyword": "人工智能医疗应用",
  "focus_keyword_rationale": "该词搜索量高、竞争中等，与文章核心内容匹配",
  "primary_keywords": [
    "AI诊断",
    "医疗影像分析",
    "智能辅助诊断"
  ],
  "secondary_keywords": [
    "深度学习医疗",
    "计算机视觉医学应用",
    "AI早期筛查",
    "医疗AI伦理",
    "智能医疗设备"
  ],
  "keyword_difficulty": {
    "focus_keyword": 0.65,  // 0-1，越高越难排名
    "average_difficulty": 0.52
  },
  "search_volume_estimate": {
    "focus_keyword": "5000-10000/月",
    "primary_keywords_total": "15000-25000/月"
  }
}
```

**用户操作**:
- ✅ **APPROVE**: 接受所有建议
- ❌ **REJECT**: 拒绝，使用Step 1提取的原始关键词
- ✏️ **MODIFY**: 手动编辑关键词列表

**验收标准**:
- [ ] AI生成的focus_keyword与文章主题高度相关（人工评估≥85%准确率）
- [ ] Primary keywords覆盖文章核心概念
- [ ] Secondary keywords包含长尾词，有利于长尾流量
- [ ] 提供关键词难度和搜索量参考

---

### FR-3.2: Meta Description优化

**需求描述**: AI基于文章内容生成吸引点击的Meta Description

**输入**:
- `body_html` (正文前200字)
- `title_main` (主标题)
- `focus_keyword` (主关键词)
- `meta_description` (Step 1提取的原始描述 - 可能为空)

**输出**:
```json
{
  "original_meta_description": "本文介绍AI在医疗领域的应用。",  // 来自Step 1
  "suggested_meta_description": "深入解析AI如何革新医疗诊断：从影像分析到早期筛查，了解人工智能如何提升诊断准确率30%以上。",
  "character_count": 156,
  "improvements": [
    "添加具体数据（30%准确率提升）增强可信度",
    "使用动作词"革新"、"提升"增强吸引力",
    "包含主关键词"AI医疗诊断"",
    "符合150-160字符最佳长度"
  ],
  "seo_score": 92  // 0-100分
}
```

**用户操作**:
- ✅ **APPROVE**: 使用AI优化版本
- ❌ **REJECT**: 保留原始描述（如果存在）
- ✏️ **MODIFY**: 手动编辑描述

**验收标准**:
- [ ] 生成的描述长度在150-160字符之间
- [ ] 包含focus_keyword
- [ ] 具有吸引点击的元素（数据、行动号召、独特价值）
- [ ] 符合搜索引擎最佳实践

---

### FR-3.3: 标签（Tags）推荐

**需求描述**: AI分析内容后推荐相关标签

**输入**:
- `body_html` (正文)
- `primary_keywords` (主要关键词)
- `category` (文章分类)

**输出**:
```json
{
  "suggested_tags": [
    {
      "tag": "人工智能",
      "relevance": 0.95,
      "type": "primary",  // primary, secondary, trending
      "existing": true,   // 是否已存在于系统中
      "article_count": 256  // 使用该标签的文章数量
    },
    {
      "tag": "医疗AI",
      "relevance": 0.92,
      "type": "primary",
      "existing": true,
      "article_count": 89
    },
    {
      "tag": "深度学习医疗应用",
      "relevance": 0.78,
      "type": "secondary",
      "existing": false,
      "article_count": 0
    },
    {
      "tag": "AI诊断工具",
      "relevance": 0.85,
      "type": "trending",  // 最近30天热门
      "existing": true,
      "article_count": 34
    }
  ],
  "recommended_tag_count": "建议使用5-8个标签，当前推荐6个",
  "tag_strategy": "3个高频标签（流量入口）+ 2个中频标签（精准定位）+ 1个长尾标签（细分流量）"
}
```

**用户操作**:
- ✅ 批量接受所有推荐标签
- ✏️ 选择性接受部分标签
- ➕ 添加自定义标签
- ❌ 删除不相关标签

**验收标准**:
- [ ] 推荐标签数量在5-10个之间
- [ ] 标签与文章内容高度相关
- [ ] 优先推荐已存在的热门标签
- [ ] 提供标签使用数据辅助决策

---

### FR-3.4: FAQ生成（AI搜索优化）⭐ 核心功能

**需求描述**: AI根据文章内容生成**8-10个**常见问题和答案，优化在AI搜索引擎中的表现

**用户反馈调整**:
- ✅ 目标数量：**8-10个FAQ**（原计划3-5个）
- ✅ 仅生成JSON-LD Schema.org标记（隐藏，供搜索引擎识别）
- ❌ 不嵌入文章末尾可见区块
- ✅ 存入数据库（`article_faqs`表）
- 🔄 以后通过发布流程上传到WordPress

**业务价值**:
- 提升在Perplexity、ChatGPT、Google SGE等AI搜索中的可见度
- 增加文章在语音搜索中的曝光
- 提供结构化数据，增强搜索引擎理解

**输入**:
- `body_html` (完整正文)
- `title_main` (主标题)
- `focus_keyword` (主关键词)

**输出**:
```json
{
  "faqs": [
    {
      "id": "faq_001",
      "question": "人工智能在医疗诊断中的准确率有多高？",
      "answer": "根据最新研究，AI医疗诊断系统在影像分析领域的准确率可达95%以上，部分场景甚至超过人类医生。例如在肺癌早期筛查中，AI系统的准确率比传统方法提升了30-40%。",
      "answer_length": 96,
      "question_type": "factual",  // factual, how_to, comparison, definition
      "search_intent": "informational",  // informational, navigational, transactional
      "keywords_covered": ["AI医疗诊断", "准确率", "影像分析"],
      "ai_search_optimized": true,
      "confidence": 0.92
    },
    {
      "id": "faq_002",
      "question": "AI医疗诊断系统如何帮助早期发现疾病？",
      "answer": "AI系统通过深度学习算法分析医疗影像（如CT、MRI扫描），能够识别人眼难以察觉的早期病变信号。系统在毫秒级别完成数千张图像对比，发现微小异常，显著提高早期癌症、心血管疾病的检出率。",
      "answer_length": 112,
      "question_type": "how_to",
      "search_intent": "informational",
      "keywords_covered": ["AI医疗", "早期发现", "深度学习", "医疗影像"],
      "ai_search_optimized": true,
      "confidence": 0.89
    },
    {
      "id": "faq_003",
      "question": "使用AI医疗诊断系统需要哪些条件？",
      "answer": "医疗机构需要具备：1）高质量的医疗影像设备（CT/MRI）；2）足够的历史病例数据用于AI训练；3）经过认证的AI诊断软件；4）专业医生团队进行结果验证。初期投入约需100-500万元。",
      "answer_length": 118,
      "question_type": "how_to",
      "search_intent": "transactional",
      "keywords_covered": ["AI诊断系统", "医疗设备", "投入成本"],
      "ai_search_optimized": true,
      "confidence": 0.85
    }
  ],
  "generation_metadata": {
    "total_faqs": 3,
    "target_count": "3-5个FAQ",
    "avg_answer_length": 108,
    "target_length": "50-150字",
    "keyword_coverage": 0.87,  // 覆盖了87%的主要关键词
    "ai_search_score": 91  // AI搜索优化评分
  },
  "schema_preview": {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "人工智能在医疗诊断中的准确率有多高？",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "根据最新研究，AI医疗诊断系统..."
        }
      }
    ]
  }
}
```

**用户操作**:
- ✅ **APPROVE ALL**: 接受所有FAQ
- ✏️ **EDIT**: 编辑问题或答案
- ❌ **DELETE**: 删除某个FAQ
- ➕ **ADD**: 添加自定义FAQ
- 🔄 **REGENERATE**: 重新生成所有FAQ

**FAQ嵌入方式**:

根据用户反馈，采用以下方式：

1. **仅生成JSON-LD Schema.org标记** ✅:
   ```html
   <script type="application/ld+json">
   {
     "@context": "https://schema.org",
     "@type": "FAQPage",
     "mainEntity": [
       {
         "@type": "Question",
         "name": "问题1？",
         "acceptedAnswer": {
           "@type": "Answer",
           "text": "答案1"
         }
       },
       // ... 8-10个FAQ
     ]
   }
   </script>
   ```

2. **存储策略**:
   - 存入`article_faqs`表（PostgreSQL）
   - 每个FAQ独立记录，便于管理
   - 通过`position`字段控制顺序
   - `status`字段标记是否发布

3. **发布流程**:
   - Step 3确认后，FAQ状态设为`approved`
   - 发布到WordPress时，自动生成JSON-LD并嵌入文章HTML
   - 不在前端显示可见FAQ区块（用户不可见，仅供搜索引擎）

**验收标准**:
- [ ] 生成**8-10个**高质量FAQ（调整后数量）
- [ ] 每个答案长度在50-150字之间
- [ ] 问题覆盖文章核心主题
- [ ] 问题符合用户真实搜索意图
- [ ] 答案准确且基于文章内容（不杜撰）
- [ ] 生成正确的Schema.org FAQPage JSON-LD
- [ ] FAQ在AI搜索引擎测试中可被正确识别
- [ ] 仅生成JSON-LD，不生成可见HTML区块

---

## 💾 数据模型设计

### 新增表：`seo_suggestions`

存储AI生成的SEO建议（不包含标题优化，标题在Step 1处理）

```sql
CREATE TABLE seo_suggestions (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,

    -- SEO关键词建议
    focus_keyword VARCHAR(100),
    focus_keyword_rationale TEXT,
    primary_keywords TEXT[],  -- PostgreSQL数组
    secondary_keywords TEXT[],
    keyword_difficulty JSONB,  -- {"focus_keyword": 0.65, ...}
    search_volume_estimate JSONB,

    -- Meta Description建议
    original_meta_description TEXT,
    suggested_meta_description TEXT,
    meta_description_improvements TEXT[],
    meta_description_score INTEGER,  -- 0-100

    -- 标签建议
    suggested_tags JSONB,  -- [{"tag": "AI", "relevance": 0.95, ...}, ...]

    -- 生成元数据
    generated_by VARCHAR(50) DEFAULT 'claude-sonnet-4.5',  -- AI模型
    generation_cost DECIMAL(10, 4),  -- API成本
    generation_tokens INTEGER,
    generation_duration_ms INTEGER,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    CONSTRAINT unique_article_seo_suggestion UNIQUE (article_id)
);

CREATE INDEX idx_seo_suggestions_article ON seo_suggestions(article_id);
```

**调整说明**:
- ❌ 移除 `original_title` 和 `suggested_titles` 字段
- 标题优化功能移至Step 1（解析阶段）

---

### 新增表：`article_faqs`

存储AI生成的FAQ

```sql
CREATE TABLE article_faqs (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,

    -- FAQ内容
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    answer_length INTEGER,

    -- FAQ元数据
    question_type VARCHAR(20),  -- factual, how_to, comparison, definition
    search_intent VARCHAR(20),  -- informational, navigational, transactional
    keywords_covered TEXT[],
    ai_search_optimized BOOLEAN DEFAULT true,
    confidence DECIMAL(3, 2),  -- 0.00-1.00

    -- 排序
    position INTEGER NOT NULL DEFAULT 0,  -- 显示顺序

    -- 状态
    status VARCHAR(20) DEFAULT 'draft',  -- draft, approved, rejected, published

    -- 生成元数据
    generated_by VARCHAR(50) DEFAULT 'claude-sonnet-4.5',

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_article_faqs_article ON article_faqs(article_id);
CREATE INDEX idx_article_faqs_article_position ON article_faqs(article_id, position);
CREATE INDEX idx_article_faqs_status ON article_faqs(status);
```

---

### 新增表：`seo_metadata_confirmations`

记录用户对SEO建议的决策（不包含标题决策）

```sql
CREATE TABLE seo_metadata_confirmations (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    seo_suggestion_id INTEGER REFERENCES seo_suggestions(id) ON DELETE SET NULL,

    -- 决策内容
    focus_keyword_decision VARCHAR(20),  -- approved, rejected, modified
    final_focus_keyword VARCHAR(100),

    meta_description_decision VARCHAR(20),
    final_meta_description TEXT,

    tags_decision VARCHAR(20),
    final_tags TEXT[],

    faqs_decision VARCHAR(20),  -- approved_all, approved_partial, rejected, modified
    approved_faq_ids INTEGER[],  -- 批准的FAQ ID列表

    -- 用户反馈
    user_feedback TEXT,
    quality_rating INTEGER,  -- 1-5星，对AI建议的评分

    -- 确认人和时间
    confirmed_by VARCHAR(100) NOT NULL,
    confirmed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT unique_article_seo_confirmation UNIQUE (article_id)
);

CREATE INDEX idx_seo_confirmations_article ON seo_metadata_confirmations(article_id);
CREATE INDEX idx_seo_confirmations_confirmed_by ON seo_metadata_confirmations(confirmed_by);
```

**调整说明**:
- ❌ 移除 `title_decision` 和 `final_title` 字段
- 标题决策在Step 1完成

---

### 扩展 `articles` 表

添加Step 3确认状态

```sql
ALTER TABLE articles ADD COLUMN IF NOT EXISTS seo_metadata_confirmed BOOLEAN DEFAULT FALSE;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS seo_metadata_confirmed_at TIMESTAMP;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS seo_metadata_confirmed_by VARCHAR(100);
```

---

## 🔌 API 设计

### 1. 生成SEO建议

```http
POST /v1/articles/{article_id}/generate-seo-suggestions
```

**请求体**:
```json
{
  "regenerate": false,  // 是否强制重新生成（默认false，有缓存则返回）
  "options": {
    "include_tag_suggestions": true,
    "target_keywords_count": {
      "primary": 5,
      "secondary": 10
    }
  }
}
```

**调整说明**: 移除 `include_title_suggestions` 选项（标题在Step 1处理）

**响应**:
```json
{
  "success": true,
  "suggestion_id": 123,
  "suggestions": {
    "focus_keyword": "...",
    "primary_keywords": [...],
    "secondary_keywords": [...],
    "suggested_meta_description": "...",
    "suggested_titles": [...],
    "suggested_tags": [...]
  },
  "generation_metadata": {
    "cost_usd": 0.03,
    "tokens": 1500,
    "duration_ms": 2340
  }
}
```

---

### 2. 生成FAQ

```http
POST /v1/articles/{article_id}/generate-faqs
```

**请求体**:
```json
{
  "target_count": 10,  // 目标FAQ数量（8-10推荐）⭐ 调整后
  "question_types": ["factual", "how_to", "comparison"],  // 可选，限定问题类型
  "regenerate": false
}
```

**响应**:
```json
{
  "success": true,
  "faqs": [
    {
      "id": 1,
      "question": "...",
      "answer": "...",
      "question_type": "factual",
      "confidence": 0.92
    }
  ],
  "schema_org_json_ld": "{\"@context\": ...}",  // Schema.org JSON-LD
  "generation_metadata": {
    "total_faqs": 5,
    "avg_answer_length": 108,
    "ai_search_score": 91
  }
}
```

---

### 3. 获取SEO建议

```http
GET /v1/articles/{article_id}/seo-suggestions
```

**响应**:
```json
{
  "success": true,
  "suggestion_id": 123,
  "suggestions": { ... },
  "confirmation": {
    "confirmed": false,
    "confirmed_by": null,
    "confirmed_at": null
  }
}
```

---

### 4. 确认SEO建议

```http
POST /v1/articles/{article_id}/confirm-seo-metadata
```

**请求体**:
```json
{
  "confirmed_by": "reviewer_user_id",

  "focus_keyword": {
    "decision": "modified",  // approved, rejected, modified
    "final_value": "AI医疗诊断应用"
  },

  "meta_description": {
    "decision": "approved",
    "final_value": "深入解析AI如何革新医疗诊断..."
  },

  "tags": {
    "decision": "modified",
    "final_value": ["人工智能", "医疗AI", "深度学习医疗应用", "AI诊断"]
  },

  "faqs": {
    "decision": "approved_partial",
    "approved_faq_ids": [1, 2, 3, 4, 5, 6, 7, 8],  // 批准的FAQ ID（8-10个）
    "custom_faqs": [  // 用户添加的自定义FAQ
      {
        "question": "...",
        "answer": "..."
      }
    ]
  },

  "user_feedback": "建议的关键词很准确，FAQ覆盖全面",
  "quality_rating": 4  // 1-5星
}
```

**调整说明**:
- ❌ 移除 `title` 决策（标题在Step 1确认）
- ✅ FAQ批准数量调整为8-10个

**响应**:
```json
{
  "success": true,
  "confirmation_id": 456,
  "article": {
    "id": 123,
    "seo_metadata_confirmed": true,
    "seo_metadata_confirmed_at": "2025-11-08T14:30:00Z",
    "seo_metadata_confirmed_by": "reviewer_user_id"
  },
  "next_step": "ready_to_publish"  // 可以进入发布流程
}
```

---

### 5. 更新FAQ

```http
PATCH /v1/articles/{article_id}/faqs/{faq_id}
```

**请求体**:
```json
{
  "question": "更新后的问题？",
  "answer": "更新后的答案。",
  "status": "approved"
}
```

---

### 6. 删除FAQ

```http
DELETE /v1/articles/{article_id}/faqs/{faq_id}
```

---

### 7. 添加自定义FAQ

```http
POST /v1/articles/{article_id}/faqs
```

**请求体**:
```json
{
  "question": "自定义问题？",
  "answer": "自定义答案。",
  "position": 4,
  "question_type": "how_to",
  "search_intent": "informational"
}
```

---

## 🎨 前端 UI 设计

### Step 3 页面布局

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: SEO深度优化与FAQ生成                   [返回Step 2]    │
├─────────────────────────────────────────────────────────────────┤
│  进度条: ████████████████░░░░  75% (3/4)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  💡 提示：标题优化已在Step 1完成，此步骤专注于SEO深度优化      │
│                                                                 │
│  ┌─ 1️⃣ SEO关键词 ──────────────────────────────────────┐      │
│  │                                                         │    │
│  │  主关键词 (Focus Keyword):                               │    │
│  │  [人工智能医疗应用] ✏️                                    │    │
│  │  理由: 搜索量高、竞争中等、匹配度高                       │    │
│  │  难度: ●●●○○ 中等  月搜索量: 5,000-10,000               │    │
│  │                                                         │    │
│  │  主要关键词 (Primary Keywords):                          │    │
│  │  [AI诊断] [医疗影像分析] [智能辅助诊断] ➕               │    │
│  │                                                         │    │
│  │  次要关键词 (Secondary Keywords):                        │    │
│  │  [深度学习医疗] [计算机视觉医学应用] [AI早期筛查]        │    │
│  │  [医疗AI伦理] [智能医疗设备] ➕                          │    │
│  │                                                         │    │
│  │  [✅ 全部接受]  [❌ 使用原关键词]  [✏️ 自定义编辑]        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─ 2️⃣ Meta Description ────────────────────────────────┐     │
│  │                                                         │    │
│  │  原始描述 (来自文档):                                     │    │
│  │  本文介绍AI在医疗领域的应用。                             │    │
│  │                                                         │    │
│  │  AI优化版本: ⭐ 92分                                      │    │
│  │  ┌──────────────────────────────────────────────┐      │    │
│  │  │深入解析AI如何革新医疗诊断：从影像分析到早期筛 │      │    │
│  │  │查，了解人工智能如何提升诊断准确率30%以上。    │      │    │
│  │  └──────────────────────────────────────────────┘      │    │
│  │  字符数: 156/160 ✓                                       │    │
│  │                                                         │    │
│  │  优化亮点:                                               │    │
│  │  • ✓ 添加具体数据增强可信度                             │    │
│  │  • ✓ 使用动作词增强吸引力                               │    │
│  │  • ✓ 包含主关键词                                       │    │
│  │  • ✓ 符合最佳长度                                       │    │
│  │                                                         │    │
│  │  [✅ 使用优化版]  [❌ 保留原版]  [✏️ 自定义编辑]          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─ 3️⃣ 标签建议 ──────────────────────────────────────┐      │
│  │                                                         │    │
│  │  推荐标签 (点击选择):                                    │    │
│  │                                                         │    │
│  │  ☑ 人工智能 (256篇文章) ⭐ 高频                          │    │
│  │  ☑ 医疗AI (89篇) ⭐ 高频                                 │    │
│  │  ☑ 深度学习医疗应用 (新标签) ⭐ 长尾                     │    │
│  │  ☑ AI诊断工具 (34篇) 🔥 趋势                            │    │
│  │  ☐ 医学影像分析 (156篇) ⭐ 中频                          │    │
│  │  ☐ 智能医疗 (201篇) ⭐ 高频                              │    │
│  │                                                         │    │
│  │  自定义标签: [________________] ➕添加                   │    │
│  │                                                         │    │
│  │  已选择: 4个标签  建议: 5-8个                            │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─ 4️⃣ FAQ生成（AI搜索优化）⭐ ──────────────────────┐       │
│  │                                                         │    │
│  │  为了提升在Perplexity、ChatGPT等AI搜索中的可见度，      │    │
│  │  系统已自动生成**8-10个**常见问题（仅生成JSON-LD）      │    │
│  │                                                         │    │
│  │  ┌─ FAQ #1 ─────────────────────────────┐ [✏️] [🗑️]    │    │
│  │  │ Q: 人工智能在医疗诊断中的准确率有多高？ │              │    │
│  │  │                                        │              │    │
│  │  │ A: 根据最新研究，AI医疗诊断系统在影像  │              │    │
│  │  │ 分析领域的准确率可达95%以上，部分场景  │              │    │
│  │  │ 甚至超过人类医生。例如在肺癌早期筛查  │              │    │
│  │  │ 中，AI系统的准确率比传统方法提升了    │              │    │
│  │  │ 30-40%。                               │              │    │
│  │  │                                        │              │    │
│  │  │ 类型: 事实型  搜索意图: 信息查询       │              │    │
│  │  │ 置信度: ⭐⭐⭐⭐⭐ 92%                   │              │    │
│  │  └────────────────────────────────────────┘              │    │
│  │                                                         │    │
│  │  ┌─ FAQ #2 ─────────────────────────────┐ [✏️] [🗑️]    │    │
│  │  │ Q: AI医疗诊断系统如何帮助早期发现疾病？│              │    │
│  │  │                                        │              │    │
│  │  │ A: AI系统通过深度学习算法分析医疗影像  │              │    │
│  │  │ （如CT、MRI扫描），能够识别人眼难以    │              │    │
│  │  │ 察觉的早期病变信号...                  │              │    │
│  │  │                                        │              │    │
│  │  │ 类型: 操作型  搜索意图: 信息查询       │              │    │
│  │  │ 置信度: ⭐⭐⭐⭐⭐ 89%                   │              │    │
│  │  └────────────────────────────────────────┘              │    │
│  │                                                         │    │
│  │  ┌─ FAQ #3 ─────────────────────────────┐ [✏️] [🗑️]    │    │
│  │  │ Q: 使用AI医疗诊断系统需要哪些条件？    │              │    │
│  │  │                                        │              │    │
│  │  │ A: 医疗机构需要具备：1）高质量的医疗   │              │    │
│  │  │ 影像设备（CT/MRI）；2）足够的历史病例  │              │    │
│  │  │ 数据用于AI训练...                      │              │    │
│  │  │                                        │              │    │
│  │  │ 类型: 操作型  搜索意图: 交易型         │              │    │
│  │  │ 置信度: ⭐⭐⭐⭐○ 85%                   │              │    │
│  │  └────────────────────────────────────────┘              │    │
│  │                                                         │    │
│  │  ... (共8-10个FAQ，此处省略) ...                        │    │
│  │                                                         │    │
│  │  [➕ 添加自定义FAQ]  [🔄 重新生成全部]                   │    │
│  │                                                         │    │
│  │  已生成: 10个FAQ  AI搜索优化评分: ⭐ 91/100             │    │
│  │  Schema.org标记: ✓ 已生成                               │    │
│  │  ⚠️ FAQ仅生成JSON-LD（隐藏），不显示在文章前端          │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─ 💬 反馈 (可选) ─────────────────────────────────────┐      │
│  │                                                         │    │
│  │  对AI建议的评价:                                         │    │
│  │  ⭐⭐⭐⭐⭐ (1-5星)                                        │    │
│  │                                                         │    │
│  │  其他意见: [__________________________________]          │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │           [⬅️ 返回Step 2]      [✅ 确认并继续发布] ➡️   │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🤖 AI 服务设计

### SEO建议生成服务

**文件**: `backend/src/services/seo/seo_suggestion_service.py`

```python
from anthropic import AsyncAnthropic
from typing import Dict, List, Any

class SEOSuggestionService:
    """
    AI驱动的SEO建议生成服务
    """

    def __init__(self, anthropic_client: AsyncAnthropic):
        self.client = anthropic_client
        self.model = "claude-sonnet-4.5-20250929"

    async def generate_comprehensive_suggestions(
        self,
        article: Article
    ) -> Dict[str, Any]:
        """
        生成全面的SEO建议（关键词、描述、标签）

        ⚠️ 不包含标题优化（标题在Step 1处理）

        一次API调用生成所有建议，节省成本
        """

        prompt = self._build_seo_analysis_prompt(article)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.3,  # 较低温度，确保一致性
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # 解析AI响应，提取结构化建议
        suggestions = self._parse_seo_response(response.content[0].text)

        return suggestions

    def _build_seo_analysis_prompt(self, article: Article) -> str:
        """
        构建SEO分析Prompt
        """
        return f"""
你是一位资深的SEO专家和内容营销顾问。请分析以下文章，提供全面的SEO优化建议。

## 文章信息

**标题**: {article.title_main}
{f"**前缀**: {article.title_prefix}" if article.title_prefix else ""}
{f"**副标题**: {article.title_suffix}" if article.title_suffix else ""}

**正文** (前500字):
{article.body_html[:500]}...

**当前Meta Description** (如果有):
{article.meta_description or "（无）"}

**当前关键词** (如果有):
{", ".join(article.seo_keywords) if article.seo_keywords else "（无）"}

---

## 任务要求

请以JSON格式提供以下SEO建议：

### 1. 关键词分析
- **focus_keyword**: 1个主关键词（搜索量高、竞争适中、与内容高度相关）
- **focus_keyword_rationale**: 选择该关键词的理由（1-2句话）
- **primary_keywords**: 3-5个主要关键词（语义相关）
- **secondary_keywords**: 5-10个次要关键词（长尾词）
- **keyword_difficulty**: 估算关键词难度（0-1，0.7以下为佳）
- **search_volume_estimate**: 估算月搜索量范围

### 2. Meta Description优化
- **suggested_meta_description**: 优化后的Meta Description（150-160字符）
- **meta_description_improvements**: 改进点列表（3-5点）
- **meta_description_score**: SEO评分（0-100）

### 3. 标签建议
- **suggested_tags**: 6-8个推荐标签，每个包含：
  - tag: 标签名称
  - relevance: 相关性（0-1）
  - type: 类型（primary, secondary, trending）

---

## 输出格式

请严格按照以下JSON Schema输出：

```json
{{
  "focus_keyword": "...",
  "focus_keyword_rationale": "...",
  "primary_keywords": ["...", "..."],
  "secondary_keywords": ["...", "...", "..."],
  "keyword_difficulty": {{"focus_keyword": 0.65, "average_difficulty": 0.52}},
  "search_volume_estimate": {{"focus_keyword": "5000-10000/月", "primary_keywords_total": "15000-25000/月"}},

  "suggested_meta_description": "...",
  "meta_description_improvements": ["...", "..."],
  "meta_description_score": 92,

  "suggested_tags": [
    {{"tag": "...", "relevance": 0.95, "type": "primary"}},
    {{"tag": "...", "relevance": 0.88, "type": "secondary"}}
  ]
}}
```

## 注意事项
- 关键词必须与文章内容高度相关
- Meta Description必须吸引点击，包含具体价值
- 标签要实用，有助于内容分类和发现
- ⚠️ 不要生成标题建议（标题在Step 1已处理）
"""
```

---

### FAQ生成服务

**文件**: `backend/src/services/seo/faq_generation_service.py`

```python
class FAQGenerationService:
    """
    AI驱动的FAQ生成服务（针对AI搜索优化）
    """

    async def generate_faqs(
        self,
        article: Article,
        target_count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        生成FAQ（针对AI搜索引擎优化）
        """

        prompt = self._build_faq_generation_prompt(article, target_count)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            temperature=0.4,  # 稍高温度，增加问题多样性
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        faqs = self._parse_faq_response(response.content[0].text)

        return faqs

    def _build_faq_generation_prompt(
        self,
        article: Article,
        target_count: int
    ) -> str:
        """
        构建FAQ生成Prompt
        """
        return f"""
你是一位专业的内容策略师，专注于优化内容在AI搜索引擎（如Perplexity、ChatGPT Search、Google SGE）中的表现。

## 任务

为以下文章生成 {target_count} 个高质量FAQ（常见问题与答案），以提升在AI搜索中的可见度。

## 文章信息

**标题**: {article.title_main}

**主关键词**: {article.focus_keyword or "（待定）"}

**正文摘要**:
{article.body_html[:800]}...

---

## FAQ生成要求

### 问题设计原则
1. **匹配真实搜索意图**: 问题应该是用户在AI搜索中真正会问的
2. **覆盖核心概念**: 围绕文章的关键信息点
3. **多样化问题类型**:
   - 事实型（What is...? 数据型）
   - 操作型（How to...? 步骤型）
   - 对比型（...vs...? 优劣型）
   - 定义型（What does...mean?）
4. **语言自然**: 口语化，符合真实提问习惯

### 答案撰写原则
1. **简洁准确**: 50-150字，直接回答问题
2. **包含关键词**: 自然融入主关键词和相关词
3. **提供价值**: 给出具体数据、案例或步骤
4. **引用文章**: 答案内容必须基于文章，不杜撰
5. **AI友好**: 易于AI搜索引擎理解和引用

---

## 输出格式

请严格按照以下JSON Schema输出：

```json
[
  {{
    "question": "具体问题？",
    "answer": "简洁、准确、有价值的答案。",
    "question_type": "factual",  // factual, how_to, comparison, definition
    "search_intent": "informational",  // informational, navigational, transactional
    "keywords_covered": ["关键词1", "关键词2"],
    "confidence": 0.92  // 0.00-1.00，答案准确度置信度
  }},
  // ... 更多FAQ
]
```

## 示例

问题: "人工智能在医疗诊断中的准确率有多高？"
答案: "根据最新研究，AI医疗诊断系统在影像分析领域的准确率可达95%以上，部分场景甚至超过人类医生。例如在肺癌早期筛查中，AI系统的准确率比传统方法提升了30-40%。"
类型: factual
意图: informational
关键词: ["AI医疗诊断", "准确率", "影像分析"]
置信度: 0.92

---

现在请生成 {target_count} 个FAQ（推荐8-10个）。

⚠️ 重要：FAQ将仅以JSON-LD Schema.org格式嵌入，不会在文章前端显示可见区块。
"""

    def generate_schema_org_faq(self, faqs: List[Dict]) -> Dict:
        """
        生成Schema.org FAQPage JSON-LD
        """
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": faq["question"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": faq["answer"]
                    }
                }
                for faq in faqs if faq.get("status") == "approved"
            ]
        }
```

---

## 📅 实施计划

### Week 24: 后端开发（SEO建议生成）

**任务**:
- T7.37: 设计数据库Schema（`seo_suggestions`, `article_faqs`, `seo_metadata_confirmations`）
- T7.38: 实现`SEOSuggestionService`（关键词、描述、标题、标签生成）
- T7.39: 实现`FAQGenerationService`（FAQ生成 + Schema.org）
- T7.40: 创建API端点（生成、获取、确认）
- T7.41: 单元测试

**预估工时**: 24小时

---

### Week 25: 前端开发（Step 3 UI）

**任务**:
- T7.42: 构建Step 3页面框架
- T7.43: 实现标题优化卡片（单选+自定义）
- T7.44: 实现SEO关键词卡片（标签输入+编辑）
- T7.45: 实现Meta Description卡片（可编辑文本框+字符计数）
- T7.46: 实现标签建议卡片（多选+自定义添加）
- T7.47: 实现FAQ生成卡片（编辑/删除/添加/重新生成）
- T7.48: 实现确认逻辑和状态管理
- T7.49: i18n支持

**预估工时**: 32小时

---

### Week 26: 集成测试与优化

**任务**:
- T7.50: 端到端工作流测试（Parse → Proofread → SEO → Publish）
- T7.51: AI生成质量评估（人工评估20篇文章的建议质量）
- T7.52: FAQ Schema.org测试（Google Rich Results Test）
- T7.53: 性能优化（缓存、批量处理）
- T7.54: 文档更新

**预估工时**: 16小时

---

**总预估工时**: 72小时（3周，约18天）

---

## ✅ 验收标准

### 功能验收

- [ ] **SEO建议生成**: AI生成的建议准确率≥85%（人工评估）
- [ ] **标题优化**: 提供3个不同风格的标题，评分合理
- [ ] **Meta Description**: 长度符合规范，包含关键词，吸引点击
- [ ] **关键词推荐**: 主关键词与内容高度相关，覆盖核心概念
- [ ] **标签建议**: 推荐标签实用，有助于分类和发现
- [ ] **FAQ生成**: 生成3-5个FAQ，问题自然，答案准确
- [ ] **Schema.org**: 生成正确的FAQPage JSON-LD，通过Google验证
- [ ] **用户确认**: 支持APPROVE/REJECT/MODIFY所有建议
- [ ] **工作流集成**: Step 3必须在Step 2之后、发布之前

### 质量验收

- [ ] **AI生成速度**: SEO建议生成≤30秒，FAQ生成≤20秒
- [ ] **成本控制**: 单篇文章SEO+FAQ生成成本≤$0.10
- [ ] **准确性**: FAQ答案准确率≥90%（基于文章内容，不杜撰）
- [ ] **Schema.org验证**: 通过Google Rich Results Test
- [ ] **AI搜索测试**: 在Perplexity/ChatGPT中搜索相关问题，FAQ内容可被引用

### 技术验收

- [ ] **API性能**: 所有API响应时间≤3秒（95th percentile）
- [ ] **数据库性能**: 查询响应时间≤500ms
- [ ] **测试覆盖率**: 后端≥85%，前端≥80%
- [ ] **错误处理**: 优雅处理AI生成失败、超时等异常
- [ ] **向后兼容**: 不破坏现有工作流

---

## 🎯 总结

### Step 3核心价值

1. **SEO优化**: AI生成专业的SEO建议，提升搜索排名
2. **AI搜索优化**: FAQ生成针对Perplexity等AI搜索引擎，抢占新流量入口
3. **内容质量保障**: 多维度优化（标题、描述、关键词、标签），确保发布质量
4. **用户体验**: 提供AI建议+人工确认的混合模式，平衡效率和控制

### 与Phase 7其他步骤的关系

```
Step 1 (解析确认) → 验证结构正确性
Step 2 (正文校对) → 验证内容质量
Step 3 (SEO确认) → 优化搜索可见度 ⭐ 新增
Step 4 (发布) → 上线
```

### 技术栈

- **后端**: FastAPI + SQLAlchemy + Anthropic Claude 4.5
- **前端**: React + TypeScript + TanStack Query
- **数据库**: PostgreSQL (JSONB for Schema.org)
- **AI**: Claude Sonnet 4.5 (SEO分析 + FAQ生成)
- **SEO**: Schema.org FAQPage

---

**下一步**: 等待用户审核和批准，确认需求理解正确后开始实施。
