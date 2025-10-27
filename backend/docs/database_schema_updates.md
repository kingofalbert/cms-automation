# CMS自动化系统 - 数据库模型扩展说明文档

**版本:** 1.1.0
**创建日期:** 2025-10-26
**最后更新:** 2025-10-27
**状态:** 需求设计阶段
**关联需求:** 文章校对+SEO优化完整工作流 v3.0.0 (更新至v2.0单一Prompt架构)

---

## 📋 目录

1. [概述](#1-概述)
2. [Articles表扩展](#2-articles表扩展)
3. [数据迁移方案](#3-数据迁移方案)
4. [索引设计](#4-索引设计)
5. [存储估算](#5-存储估算)
6. [查询优化](#6-查询优化)
7. [备份与回滚](#7-备份与回滚)
8. [实施计划](#8-实施计划)

---

## 1. 概述

### 1.1 变更目标

扩展 `articles` 表以支持**三版本管理系统**和**FAQ Schema存储**，实现：
- 原始版本（Original）保存
- 建议版本（Suggested）生成
- 最终版本（Final）确认
- 版本状态管理
- FAQ Schema结构化数据存储

### 1.2 影响范围

| 影响对象 | 影响程度 | 说明 |
|---------|---------|------|
| **articles表** | 高 | 新增约30个字段 |
| **API接口** | 高 | 需要更新所有文章相关API |
| **存储空间** | 中 | 预计每篇文章增加50-100KB |
| **查询性能** | 低 | 需要添加索引优化 |
| **现有数据** | 低 | 向后兼容，不影响现有数据 |

### 1.3 向后兼容性

✅ **完全向后兼容**:
- 所有新增字段均为可空（NULLABLE）或有默认值
- 现有API继续工作（仅返回原有字段）
- 现有文章数据不受影响
- 逐步迁移，无需停机

---

## 2. Articles表扩展

### 2.1 完整字段列表

#### 2.1.1 原始版本字段（Original Version）

```sql
-- ========================================
-- 原始版本字段 (6个字段)
-- ========================================

-- 正文
ALTER TABLE articles ADD COLUMN original_content TEXT;
COMMENT ON COLUMN articles.original_content IS '原始正文内容（用户输入的原始版本）';

ALTER TABLE articles ADD COLUMN original_content_word_count INTEGER DEFAULT 0;
COMMENT ON COLUMN articles.original_content_word_count IS '原始正文字数';

-- Meta描述
ALTER TABLE articles ADD COLUMN original_meta_description TEXT;
COMMENT ON COLUMN articles.original_meta_description IS '原始Meta描述（可为空）';

ALTER TABLE articles ADD COLUMN original_meta_char_count INTEGER DEFAULT 0;
COMMENT ON COLUMN articles.original_meta_char_count IS '原始Meta字符数';

-- SEO关键词
ALTER TABLE articles ADD COLUMN original_seo_keywords JSONB DEFAULT '[]'::jsonb;
COMMENT ON COLUMN articles.original_seo_keywords IS '原始SEO关键词列表 ["关键词1", "关键词2"]';

ALTER TABLE articles ADD COLUMN original_keyword_count INTEGER DEFAULT 0;
COMMENT ON COLUMN articles.original_keyword_count IS '原始关键词数量';

-- 元数据
ALTER TABLE articles ADD COLUMN original_received_at TIMESTAMP WITH TIME ZONE;
COMMENT ON COLUMN articles.original_received_at IS '原始文稿接收时间';

ALTER TABLE articles ADD COLUMN original_format_valid BOOLEAN DEFAULT TRUE;
COMMENT ON COLUMN articles.original_format_valid IS '原始格式是否有效';

ALTER TABLE articles ADD COLUMN original_parse_warnings JSONB DEFAULT '[]'::jsonb;
COMMENT ON COLUMN articles.original_parse_warnings IS '解析警告列表 [{type, message, severity}]';
```

**字段说明:**

| 字段名 | 类型 | 可空 | 默认值 | 说明 |
|-------|------|------|--------|------|
| `original_content` | TEXT | YES | NULL | 用户输入的原始正文，永久保存 |
| `original_content_word_count` | INTEGER | NO | 0 | 原始正文字数（中文字符） |
| `original_meta_description` | TEXT | YES | NULL | 用户输入的原始Meta描述 |
| `original_meta_char_count` | INTEGER | NO | 0 | 原始Meta字符数 |
| `original_seo_keywords` | JSONB | NO | `[]` | 原始SEO关键词JSON数组 |
| `original_keyword_count` | INTEGER | NO | 0 | 原始关键词数量 |
| `original_received_at` | TIMESTAMP | YES | NULL | 文稿接收时间 |
| `original_format_valid` | BOOLEAN | NO | TRUE | 格式验证结果 |
| `original_parse_warnings` | JSONB | NO | `[]` | 解析时的警告信息 |

**JSONB示例 - original_parse_warnings:**
```json
[
  {
    "type": "warning",
    "code": "META_TOO_SHORT",
    "message": "Meta描述过短（85字符），建议150-160字符",
    "severity": "warning"
  },
  {
    "type": "info",
    "code": "KEYWORD_COUNT_LOW",
    "message": "关键词数量偏少（2个），建议3-8个",
    "severity": "info"
  }
]
```

#### 2.1.2 建议版本字段（Suggested Version）

> **v1.1 架构说明**: 采用单一Prompt架构后，所有AI分析结果通过一次调用生成。
> 建议添加一个 `ai_analysis_result` JSONB字段存储完整的AI响应，其他字段可以从中提取。

```sql
-- ========================================
-- 建议版本字段 (v1.1: 15个字段，新增ai_analysis_result)
-- ========================================

-- ⭐ v1.1 新增：AI综合分析结果 (单一Prompt完整响应)
ALTER TABLE articles ADD COLUMN ai_analysis_result JSONB;
COMMENT ON COLUMN articles.ai_analysis_result IS 'v1.1: 单一Prompt综合分析的完整JSON结果，包含校对、Meta、关键词、FAQ等所有内容。详见 single_prompt_design.md';

-- 正文建议
ALTER TABLE articles ADD COLUMN suggested_content TEXT;
COMMENT ON COLUMN articles.suggested_content IS '校对和优化后的正文内容';

ALTER TABLE articles ADD COLUMN suggested_content_changes JSONB;
COMMENT ON COLUMN articles.suggested_content_changes IS '正文修改详情（diff数据）';

-- Meta描述建议
ALTER TABLE articles ADD COLUMN suggested_meta_description TEXT;
COMMENT ON COLUMN articles.suggested_meta_description IS '优化后的Meta描述';

ALTER TABLE articles ADD COLUMN suggested_meta_reasoning TEXT;
COMMENT ON COLUMN articles.suggested_meta_reasoning IS 'Meta优化理由说明';

ALTER TABLE articles ADD COLUMN suggested_meta_score DECIMAL(3,2);
COMMENT ON COLUMN articles.suggested_meta_score IS 'Meta质量评分（0-1）';

-- SEO关键词建议
ALTER TABLE articles ADD COLUMN suggested_seo_keywords JSONB DEFAULT '[]'::jsonb;
COMMENT ON COLUMN articles.suggested_seo_keywords IS '优化后的SEO关键词列表';

ALTER TABLE articles ADD COLUMN suggested_keywords_reasoning TEXT;
COMMENT ON COLUMN articles.suggested_keywords_reasoning IS '关键词优化理由';

ALTER TABLE articles ADD COLUMN suggested_keywords_score DECIMAL(3,2);
COMMENT ON COLUMN articles.suggested_keywords_score IS '关键词相关性评分（0-1）';

-- 段落建议
ALTER TABLE articles ADD COLUMN paragraph_suggestions JSONB DEFAULT '[]'::jsonb;
COMMENT ON COLUMN articles.paragraph_suggestions IS '段落优化建议列表';

ALTER TABLE articles ADD COLUMN paragraph_split_suggestions JSONB DEFAULT '[]'::jsonb;
COMMENT ON COLUMN articles.paragraph_split_suggestions IS '段落分段建议';

-- FAQ Schema建议
ALTER TABLE articles ADD COLUMN faq_schema_proposals JSONB DEFAULT '[]'::jsonb;
COMMENT ON COLUMN articles.faq_schema_proposals IS 'FAQ Schema多方案建议 (3/5/7个问题)';

-- 校对问题
ALTER TABLE articles ADD COLUMN proofreading_issues JSONB DEFAULT '[]'::jsonb;
COMMENT ON COLUMN articles.proofreading_issues IS '校对检测到的问题列表（A-F类规则）';

ALTER TABLE articles ADD COLUMN critical_issues_count INTEGER DEFAULT 0;
COMMENT ON COLUMN articles.critical_issues_count IS '关键问题数量（F类阻止发布）';

-- 生成元数据
ALTER TABLE articles ADD COLUMN suggested_generated_at TIMESTAMP WITH TIME ZONE;
COMMENT ON COLUMN articles.suggested_generated_at IS '建议版本生成时间';

ALTER TABLE articles ADD COLUMN ai_model_used VARCHAR(50) DEFAULT 'claude-3-5-sonnet-20241022';
COMMENT ON COLUMN articles.ai_model_used IS '使用的AI模型名称 (v1.1默认Claude 3.5 Sonnet)';

ALTER TABLE articles ADD COLUMN generation_cost DECIMAL(10,4);
COMMENT ON COLUMN articles.generation_cost IS 'AI生成成本（美元）- v1.1: 单次调用，约$0.05/篇';

ALTER TABLE articles ADD COLUMN generation_time_ms INTEGER;
COMMENT ON COLUMN articles.generation_time_ms IS 'AI处理时间（毫秒）- v1.1: 约2500ms';
```

**v1.1 架构的数据存储策略:**

```python
# 保存AI分析结果
article.ai_analysis_result = analysis_result  # 完整JSON
article.suggested_meta_description = analysis_result['optimized_meta']['suggestion']
article.suggested_seo_keywords = analysis_result['optimized_keywords']['primary']
article.faq_schema_proposals = analysis_result['faq_schema']
article.proofreading_issues = analysis_result['proofreading_results']['issues']
article.generation_cost = analysis_result['processing_metadata']['cost']
article.generation_time_ms = analysis_result['processing_metadata']['processing_time_ms']
```

**字段说明:**

| 字段名 | 类型 | 可空 | 默认值 | 说明 |
|-------|------|------|--------|------|
| `suggested_content` | TEXT | YES | NULL | AI优化后的正文内容 |
| `suggested_content_changes` | JSONB | YES | NULL | 修改详情和diff数据 |
| `suggested_meta_description` | TEXT | YES | NULL | AI优化后的Meta描述 |
| `suggested_meta_reasoning` | TEXT | YES | NULL | Meta优化的理由说明 |
| `suggested_meta_score` | DECIMAL(3,2) | YES | NULL | Meta质量评分（0.00-1.00） |
| `suggested_seo_keywords` | JSONB | NO | `[]` | AI建议的SEO关键词 |
| `suggested_keywords_reasoning` | TEXT | YES | NULL | 关键词优化理由 |
| `suggested_keywords_score` | DECIMAL(3,2) | YES | NULL | 关键词相关性评分 |
| `paragraph_suggestions` | JSONB | NO | `[]` | 段落优化建议（过长/过短） |
| `paragraph_split_suggestions` | JSONB | NO | `[]` | 段落分段位置建议 |
| `faq_schema_proposals` | JSONB | NO | `[]` | FAQ Schema多套方案 |
| `proofreading_issues` | JSONB | NO | `[]` | A-F类规则检测问题 |
| `critical_issues_count` | INTEGER | NO | 0 | F类关键问题数量 |
| `suggested_generated_at` | TIMESTAMP | YES | NULL | 建议生成时间 |
| `ai_model_used` | VARCHAR(50) | YES | NULL | AI模型标识 |
| `generation_cost` | DECIMAL(10,4) | YES | NULL | API调用成本 |

**JSONB示例 - suggested_content_changes:**
```json
{
  "total_changes": 15,
  "additions": 5,
  "deletions": 3,
  "modifications": 7,
  "changes": [
    {
      "type": "modification",
      "original_text": "这个问题很严重",
      "suggested_text": "这个问题较为严重",
      "position": 245,
      "rule_id": "A1-023",
      "reasoning": "避免使用绝对化表述"
    },
    {
      "type": "addition",
      "suggested_text": "据专家分析，",
      "position": 520,
      "rule_id": "E2-015",
      "reasoning": "添加信息来源说明"
    }
  ]
}
```

**JSONB示例 - paragraph_suggestions:**
```json
[
  {
    "paragraph_index": 2,
    "issue_type": "too_long",
    "word_count": 285,
    "suggested_splits": [
      {
        "position": 142,
        "reason": "话题转换：从背景介绍转向事件描述"
      },
      {
        "position": 238,
        "reason": "逻辑断点：总结前文，引入新观点"
      }
    ]
  },
  {
    "paragraph_index": 5,
    "issue_type": "too_short",
    "word_count": 15,
    "suggestion": "考虑与第4段或第6段合并"
  }
]
```

**JSONB示例 - faq_schema_proposals:**
```json
[
  {
    "proposal_id": "faq_3q",
    "name": "简洁版（3个问答）",
    "description": "适合短新闻和移动端",
    "item_count": 3,
    "items": [
      {
        "question": "纽约新交通政策主要内容是什么？",
        "answer": "新政策包括增加10条公交专用道...",
        "question_type": "what",
        "priority": "P0",
        "quality_score": 0.92
      }
    ],
    "schema_json_ld": "{\"@context\":\"https://schema.org\",...}",
    "overall_quality": 0.89,
    "seo_score": 7.2
  },
  {
    "proposal_id": "faq_5q",
    "name": "标准版（5个问答）",
    "item_count": 5,
    "items": [...]
  }
]
```

**JSONB示例 - proofreading_issues:**
```json
[
  {
    "issue_id": "issue_001",
    "rule_id": "B2-005",
    "category": "B",
    "severity": "error",
    "blocks_publish": false,
    "message": "中文语境下应使用全角引号",
    "original_text": "他说\"这很重要\"",
    "suggested_fix": "他说"这很重要"",
    "position": 125,
    "context": "...专家表示，他说\"这很重要\"，需要..."
  },
  {
    "issue_id": "issue_002",
    "rule_id": "F1-001",
    "category": "F",
    "severity": "critical",
    "blocks_publish": true,
    "message": "特色图片不存在或格式不支持",
    "suggested_fix": "请上传横向（宽>高）的JPG/PNG图片"
  }
]
```

#### 2.1.3 最终版本字段（Final Version）

```sql
-- ========================================
-- 最终版本字段 (12个字段)
-- ========================================

-- 正文
ALTER TABLE articles ADD COLUMN final_content TEXT;
COMMENT ON COLUMN articles.final_content IS '最终确认的正文内容（发布版本）';

ALTER TABLE articles ADD COLUMN final_content_word_count INTEGER;
COMMENT ON COLUMN articles.final_content_word_count IS '最终正文字数';

-- Meta描述
ALTER TABLE articles ADD COLUMN final_meta_description TEXT;
COMMENT ON COLUMN articles.final_meta_description IS '最终确认的Meta描述';

ALTER TABLE articles ADD COLUMN final_meta_char_count INTEGER;
COMMENT ON COLUMN articles.final_meta_char_count IS '最终Meta字符数';

-- SEO关键词
ALTER TABLE articles ADD COLUMN final_seo_keywords JSONB DEFAULT '[]'::jsonb;
COMMENT ON COLUMN articles.final_seo_keywords IS '最终确认的SEO关键词';

ALTER TABLE articles ADD COLUMN final_keyword_count INTEGER;
COMMENT ON COLUMN articles.final_keyword_count IS '最终关键词数量';

-- FAQ Schema
ALTER TABLE articles ADD COLUMN final_faq_schema JSONB;
COMMENT ON COLUMN articles.final_faq_schema IS '最终选定的FAQ Schema（JSON-LD格式）';

-- 用户选择记录
ALTER TABLE articles ADD COLUMN user_accepted_suggestions JSONB DEFAULT '[]'::jsonb;
COMMENT ON COLUMN articles.user_accepted_suggestions IS '用户接受的建议项列表';

ALTER TABLE articles ADD COLUMN user_rejected_suggestions JSONB DEFAULT '[]'::jsonb;
COMMENT ON COLUMN articles.user_rejected_suggestions IS '用户拒绝的建议项列表';

ALTER TABLE articles ADD COLUMN user_manual_edits JSONB DEFAULT '[]'::jsonb;
COMMENT ON COLUMN articles.user_manual_edits IS '用户手动编辑内容记录';

-- 确认元数据
ALTER TABLE articles ADD COLUMN final_confirmed_at TIMESTAMP WITH TIME ZONE;
COMMENT ON COLUMN articles.final_confirmed_at IS '最终版本确认时间';

ALTER TABLE articles ADD COLUMN final_confirmed_by INTEGER REFERENCES users(id);
COMMENT ON COLUMN articles.final_confirmed_by IS '确认用户ID';

ALTER TABLE articles ADD COLUMN final_version_number INTEGER DEFAULT 1;
COMMENT ON COLUMN articles.final_version_number IS '版本号（支持多次修改）';
```

**字段说明:**

| 字段名 | 类型 | 可空 | 默认值 | 说明 |
|-------|------|------|--------|------|
| `final_content` | TEXT | YES | NULL | 用户确认的最终正文 |
| `final_content_word_count` | INTEGER | YES | NULL | 最终正文字数 |
| `final_meta_description` | TEXT | YES | NULL | 最终Meta描述 |
| `final_meta_char_count` | INTEGER | YES | NULL | 最终Meta字符数 |
| `final_seo_keywords` | JSONB | NO | `[]` | 最终SEO关键词 |
| `final_keyword_count` | INTEGER | YES | NULL | 最终关键词数量 |
| `final_faq_schema` | JSONB | YES | NULL | 最终FAQ Schema |
| `user_accepted_suggestions` | JSONB | NO | `[]` | 接受的建议记录 |
| `user_rejected_suggestions` | JSONB | NO | `[]` | 拒绝的建议记录 |
| `user_manual_edits` | JSONB | NO | `[]` | 手动编辑记录 |
| `final_confirmed_at` | TIMESTAMP | YES | NULL | 确认时间 |
| `final_confirmed_by` | INTEGER | YES | NULL | 确认用户ID（外键） |
| `final_version_number` | INTEGER | NO | 1 | 版本号 |

**JSONB示例 - user_accepted_suggestions:**
```json
[
  {
    "suggestion_id": "change_001",
    "type": "content_change",
    "accepted": true,
    "accepted_at": "2025-10-26T10:30:00Z"
  },
  {
    "suggestion_id": "meta_optimization",
    "type": "meta_description",
    "accepted": true,
    "accepted_at": "2025-10-26T10:31:00Z"
  },
  {
    "suggestion_id": "faq_5q",
    "type": "faq_schema",
    "accepted": true,
    "modified": true,
    "modifications": {
      "items[2].answer": "用户自定义答案内容..."
    },
    "accepted_at": "2025-10-26T10:35:00Z"
  }
]
```

**JSONB示例 - user_manual_edits:**
```json
[
  {
    "edit_id": "edit_001",
    "field": "final_content",
    "edit_type": "manual_text_change",
    "original_value": "原文内容片段",
    "new_value": "用户修改后的内容",
    "position": 450,
    "edited_at": "2025-10-26T10:32:00Z",
    "edited_by": 5
  },
  {
    "edit_id": "edit_002",
    "field": "final_meta_description",
    "edit_type": "complete_rewrite",
    "original_value": "AI建议的Meta",
    "new_value": "用户完全重写的Meta",
    "edited_at": "2025-10-26T10:33:00Z",
    "edited_by": 5
  }
]
```

**JSONB示例 - final_faq_schema:**
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "纽约新交通政策主要内容是什么？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "新政策包括增加10条公交专用道、限制私家车进入市中心、提高停车费用至每小时15美元，以及新增1000辆公交车。"
      }
    },
    {
      "@type": "Question",
      "name": "政策什么时候生效？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "新政策将从下月1日起实施，分为3个月过渡期（仅警告）和之后的全面执法期。"
      }
    }
  ]
}
```

#### 2.1.4 状态管理字段

```sql
-- ========================================
-- 状态管理字段 (4个字段)
-- ========================================

ALTER TABLE articles ADD COLUMN proofreading_status VARCHAR(30) DEFAULT 'pending';
COMMENT ON COLUMN articles.proofreading_status IS '校对状态';

ALTER TABLE articles ADD COLUMN proofreading_started_at TIMESTAMP WITH TIME ZONE;
COMMENT ON COLUMN articles.proofreading_started_at IS '校对开始时间';

ALTER TABLE articles ADD COLUMN proofreading_completed_at TIMESTAMP WITH TIME ZONE;
COMMENT ON COLUMN articles.proofreading_completed_at IS '校对完成时间';

ALTER TABLE articles ADD COLUMN proofreading_error TEXT;
COMMENT ON COLUMN articles.proofreading_error IS '校对错误信息（失败时）';

-- 添加CHECK约束验证状态值
ALTER TABLE articles ADD CONSTRAINT check_proofreading_status
CHECK (proofreading_status IN (
    'pending', 'parsing', 'analyzing', 'suggested',
    'user_reviewing', 'user_editing', 'confirmed',
    'publishing', 'published', 'failed'
));
```

**状态说明:**

| 状态值 | 说明 | 下一个状态 |
|-------|------|-----------|
| `pending` | 待处理 | `parsing` |
| `parsing` | 解析中 | `analyzing` 或 `failed` |
| `analyzing` | 校对分析中 | `suggested` 或 `failed` |
| `suggested` | 已生成建议 | `user_reviewing` |
| `user_reviewing` | 用户审核中 | `user_editing` 或 `confirmed` |
| `user_editing` | 用户编辑中 | `user_reviewing` 或 `confirmed` |
| `confirmed` | 已确认 | `publishing` |
| `publishing` | 发布中 | `published` 或 `confirmed`（失败回滚） |
| `published` | 已发布 | - |
| `failed` | 处理失败 | `pending`（重试） |

### 2.2 字段统计

| 类别 | 字段数量 | 说明 |
|------|---------|------|
| **原始版本** | 9个 | 保存用户输入的原始内容 |
| **建议版本** | 16个 | AI分析和优化结果 |
| **最终版本** | 13个 | 用户确认的发布内容 |
| **状态管理** | 4个 | 工作流状态控制 |
| **总计** | **42个** | 新增字段总数 |

---

## 3. 数据迁移方案

### 3.1 迁移策略

**采用渐进式迁移：**
1. ✅ **阶段1**: 添加新字段（所有可空或有默认值）
2. ✅ **阶段2**: 更新应用代码支持新字段
3. ✅ **阶段3**: 逐步填充现有数据（可选）
4. ✅ **阶段4**: 验证和监控

### 3.2 迁移脚本

#### 3.2.1 添加所有新字段

```sql
-- ========================================
-- CMS自动化系统 - Articles表扩展
-- 版本: v3.0.0
-- 日期: 2025-10-26
-- ========================================

BEGIN;

-- 原始版本字段
ALTER TABLE articles ADD COLUMN IF NOT EXISTS original_content TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS original_content_word_count INTEGER DEFAULT 0;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS original_meta_description TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS original_meta_char_count INTEGER DEFAULT 0;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS original_seo_keywords JSONB DEFAULT '[]'::jsonb;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS original_keyword_count INTEGER DEFAULT 0;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS original_received_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS original_format_valid BOOLEAN DEFAULT TRUE;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS original_parse_warnings JSONB DEFAULT '[]'::jsonb;

-- 建议版本字段
ALTER TABLE articles ADD COLUMN IF NOT EXISTS suggested_content TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS suggested_content_changes JSONB;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS suggested_meta_description TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS suggested_meta_reasoning TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS suggested_meta_score DECIMAL(3,2);
ALTER TABLE articles ADD COLUMN IF NOT EXISTS suggested_seo_keywords JSONB DEFAULT '[]'::jsonb;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS suggested_keywords_reasoning TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS suggested_keywords_score DECIMAL(3,2);
ALTER TABLE articles ADD COLUMN IF NOT EXISTS paragraph_suggestions JSONB DEFAULT '[]'::jsonb;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS paragraph_split_suggestions JSONB DEFAULT '[]'::jsonb;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS faq_schema_proposals JSONB DEFAULT '[]'::jsonb;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS proofreading_issues JSONB DEFAULT '[]'::jsonb;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS critical_issues_count INTEGER DEFAULT 0;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS suggested_generated_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS ai_model_used VARCHAR(50);
ALTER TABLE articles ADD COLUMN IF NOT EXISTS generation_cost DECIMAL(10,4);

-- 最终版本字段
ALTER TABLE articles ADD COLUMN IF NOT EXISTS final_content TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS final_content_word_count INTEGER;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS final_meta_description TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS final_meta_char_count INTEGER;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS final_seo_keywords JSONB DEFAULT '[]'::jsonb;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS final_keyword_count INTEGER;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS final_faq_schema JSONB;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS user_accepted_suggestions JSONB DEFAULT '[]'::jsonb;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS user_rejected_suggestions JSONB DEFAULT '[]'::jsonb;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS user_manual_edits JSONB DEFAULT '[]'::jsonb;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS final_confirmed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS final_confirmed_by INTEGER REFERENCES users(id);
ALTER TABLE articles ADD COLUMN IF NOT EXISTS final_version_number INTEGER DEFAULT 1;

-- 状态管理字段
ALTER TABLE articles ADD COLUMN IF NOT EXISTS proofreading_status VARCHAR(30) DEFAULT 'pending';
ALTER TABLE articles ADD COLUMN IF NOT EXISTS proofreading_started_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS proofreading_completed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS proofreading_error TEXT;

-- 添加约束
ALTER TABLE articles DROP CONSTRAINT IF EXISTS check_proofreading_status;
ALTER TABLE articles ADD CONSTRAINT check_proofreading_status
CHECK (proofreading_status IN (
    'pending', 'parsing', 'analyzing', 'suggested',
    'user_reviewing', 'user_editing', 'confirmed',
    'publishing', 'published', 'failed'
));

COMMIT;
```

#### 3.2.2 迁移现有数据（可选）

```sql
-- ========================================
-- 迁移现有文章数据到原始版本字段
-- 仅当需要对已存在文章启用校对功能时执行
-- ========================================

BEGIN;

-- 将现有content复制到original_content
UPDATE articles
SET
    original_content = content,
    original_content_word_count = CHAR_LENGTH(content),
    original_received_at = created_at,
    original_format_valid = TRUE,
    proofreading_status = 'published'  -- 已发布文章不需要校对
WHERE
    original_content IS NULL
    AND content IS NOT NULL;

-- 记录迁移日志
INSERT INTO migration_logs (migration_name, rows_affected, executed_at)
VALUES ('migrate_existing_articles_v3', ROW_COUNT(), NOW());

COMMIT;
```

### 3.3 回滚脚本

```sql
-- ========================================
-- 回滚脚本 - 删除v3.0.0新增字段
-- 仅在紧急情况下使用
-- ========================================

BEGIN;

-- 警告：此操作不可逆，将删除所有校对数据
-- 确保已备份数据库

ALTER TABLE articles DROP COLUMN IF EXISTS original_content;
ALTER TABLE articles DROP COLUMN IF EXISTS original_content_word_count;
ALTER TABLE articles DROP COLUMN IF EXISTS original_meta_description;
ALTER TABLE articles DROP COLUMN IF EXISTS original_meta_char_count;
ALTER TABLE articles DROP COLUMN IF EXISTS original_seo_keywords;
ALTER TABLE articles DROP COLUMN IF EXISTS original_keyword_count;
ALTER TABLE articles DROP COLUMN IF EXISTS original_received_at;
ALTER TABLE articles DROP COLUMN IF EXISTS original_format_valid;
ALTER TABLE articles DROP COLUMN IF EXISTS original_parse_warnings;

ALTER TABLE articles DROP COLUMN IF EXISTS suggested_content;
ALTER TABLE articles DROP COLUMN IF EXISTS suggested_content_changes;
ALTER TABLE articles DROP COLUMN IF EXISTS suggested_meta_description;
ALTER TABLE articles DROP COLUMN IF EXISTS suggested_meta_reasoning;
ALTER TABLE articles DROP COLUMN IF EXISTS suggested_meta_score;
ALTER TABLE articles DROP COLUMN IF EXISTS suggested_seo_keywords;
ALTER TABLE articles DROP COLUMN IF EXISTS suggested_keywords_reasoning;
ALTER TABLE articles DROP COLUMN IF EXISTS suggested_keywords_score;
ALTER TABLE articles DROP COLUMN IF EXISTS paragraph_suggestions;
ALTER TABLE articles DROP COLUMN IF EXISTS paragraph_split_suggestions;
ALTER TABLE articles DROP COLUMN IF EXISTS faq_schema_proposals;
ALTER TABLE articles DROP COLUMN IF EXISTS proofreading_issues;
ALTER TABLE articles DROP COLUMN IF EXISTS critical_issues_count;
ALTER TABLE articles DROP COLUMN IF EXISTS suggested_generated_at;
ALTER TABLE articles DROP COLUMN IF EXISTS ai_model_used;
ALTER TABLE articles DROP COLUMN IF EXISTS generation_cost;

ALTER TABLE articles DROP COLUMN IF EXISTS final_content;
ALTER TABLE articles DROP COLUMN IF EXISTS final_content_word_count;
ALTER TABLE articles DROP COLUMN IF EXISTS final_meta_description;
ALTER TABLE articles DROP COLUMN IF EXISTS final_meta_char_count;
ALTER TABLE articles DROP COLUMN IF EXISTS final_seo_keywords;
ALTER TABLE articles DROP COLUMN IF EXISTS final_keyword_count;
ALTER TABLE articles DROP COLUMN IF EXISTS final_faq_schema;
ALTER TABLE articles DROP COLUMN IF EXISTS user_accepted_suggestions;
ALTER TABLE articles DROP COLUMN IF EXISTS user_rejected_suggestions;
ALTER TABLE articles DROP COLUMN IF EXISTS user_manual_edits;
ALTER TABLE articles DROP COLUMN IF EXISTS final_confirmed_at;
ALTER TABLE articles DROP COLUMN IF EXISTS final_confirmed_by;
ALTER TABLE articles DROP COLUMN IF EXISTS final_version_number;

ALTER TABLE articles DROP COLUMN IF EXISTS proofreading_status;
ALTER TABLE articles DROP COLUMN IF EXISTS proofreading_started_at;
ALTER TABLE articles DROP COLUMN IF EXISTS proofreading_completed_at;
ALTER TABLE articles DROP COLUMN IF EXISTS proofreading_error;

COMMIT;
```

---

## 4. 索引设计

### 4.1 推荐索引

```sql
-- ========================================
-- 索引创建脚本
-- 提升查询性能
-- ========================================

-- 状态索引（最常用查询）
CREATE INDEX idx_articles_proofreading_status
ON articles(proofreading_status)
WHERE proofreading_status IS NOT NULL;

-- 时间范围索引
CREATE INDEX idx_articles_original_received
ON articles(original_received_at DESC)
WHERE original_received_at IS NOT NULL;

CREATE INDEX idx_articles_suggested_generated
ON articles(suggested_generated_at DESC)
WHERE suggested_generated_at IS NOT NULL;

CREATE INDEX idx_articles_final_confirmed
ON articles(final_confirmed_at DESC)
WHERE final_confirmed_at IS NOT NULL;

-- 用户关联索引
CREATE INDEX idx_articles_final_confirmed_by
ON articles(final_confirmed_by)
WHERE final_confirmed_by IS NOT NULL;

-- 复合索引（状态 + 时间）
CREATE INDEX idx_articles_status_time
ON articles(proofreading_status, proofreading_started_at DESC)
WHERE proofreading_status IN ('analyzing', 'suggested', 'user_reviewing');

-- JSONB字段GIN索引（支持JSONB查询）
CREATE INDEX idx_articles_proofreading_issues_gin
ON articles USING GIN (proofreading_issues);

CREATE INDEX idx_articles_faq_schema_proposals_gin
ON articles USING GIN (faq_schema_proposals);

CREATE INDEX idx_articles_final_faq_schema_gin
ON articles USING GIN (final_faq_schema);
```

### 4.2 索引维护

```sql
-- 定期分析表统计信息
ANALYZE articles;

-- 重建膨胀的索引
REINDEX TABLE CONCURRENTLY articles;

-- 查看索引使用情况
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'articles'
ORDER BY idx_scan DESC;
```

---

## 5. 存储估算

### 5.1 单篇文章存储估算

| 字段类别 | 平均大小 | 说明 |
|---------|---------|------|
| **原始版本** | 15-25 KB | 取决于文章长度 |
| **建议版本** | 20-40 KB | 包含diff和建议数据 |
| **最终版本** | 15-25 KB | 与原始版本类似 |
| **JSONB字段** | 10-20 KB | 建议、FAQ Schema等 |
| **合计** | **60-110 KB** | 每篇文章额外存储 |

### 5.2 数据库容量规划

**假设场景：10,000篇文章**

| 项目 | 计算 | 结果 |
|------|------|------|
| 新字段总存储 | 10,000 × 80KB（平均） | **800 MB** |
| 索引开销 | 800 MB × 30% | **240 MB** |
| 预留增长空间 | (800 + 240) × 50% | **520 MB** |
| **总需求** | | **1.56 GB** |

**结论**: 10,000篇文章约需 **1.5-2 GB** 额外存储空间。

### 5.3 存储优化建议

1. **压缩JSONB字段**
   ```sql
   -- PostgreSQL会自动压缩大于2KB的TOAST数据
   -- 无需额外配置
   ```

2. **定期清理**
   ```sql
   -- 清理90天前的建议版本数据（保留最终版本）
   UPDATE articles
   SET
       suggested_content = NULL,
       suggested_content_changes = NULL,
       paragraph_suggestions = '[]'::jsonb,
       faq_schema_proposals = '[]'::jsonb
   WHERE
       proofreading_status = 'published'
       AND final_confirmed_at < NOW() - INTERVAL '90 days';
   ```

3. **分区表（未来优化）**
   ```sql
   -- 按时间分区articles表
   CREATE TABLE articles_2025_q1 PARTITION OF articles
   FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
   ```

---

## 6. 查询优化

### 6.1 常用查询示例

#### 查询1：获取待审核文章列表

```sql
-- 优化前
SELECT * FROM articles
WHERE proofreading_status IN ('suggested', 'user_reviewing')
ORDER BY suggested_generated_at DESC;

-- 优化后（使用复合索引）
SELECT
    id, title, proofreading_status,
    suggested_generated_at, critical_issues_count
FROM articles
WHERE proofreading_status IN ('suggested', 'user_reviewing')
ORDER BY suggested_generated_at DESC
LIMIT 50;

-- 使用索引：idx_articles_status_time
```

#### 查询2：检查用户的确认记录

```sql
SELECT
    id, title,
    final_confirmed_at,
    final_content IS NOT NULL as has_final_content,
    final_faq_schema IS NOT NULL as has_faq
FROM articles
WHERE final_confirmed_by = $1
ORDER BY final_confirmed_at DESC
LIMIT 100;

-- 使用索引：idx_articles_final_confirmed_by
```

#### 查询3：统计校对问题分布

```sql
-- 统计各状态文章数量
SELECT
    proofreading_status,
    COUNT(*) as count,
    AVG(critical_issues_count) as avg_critical_issues
FROM articles
WHERE proofreading_status IS NOT NULL
GROUP BY proofreading_status
ORDER BY count DESC;

-- 使用索引：idx_articles_proofreading_status
```

#### 查询4：查找包含特定问题的文章

```sql
-- 查找包含F1-001规则违反的文章（图片问题）
SELECT
    id, title, proofreading_status,
    jsonb_array_length(proofreading_issues) as issue_count
FROM articles
WHERE proofreading_issues @> '[{"rule_id": "F1-001"}]'::jsonb
ORDER BY suggested_generated_at DESC;

-- 使用索引：idx_articles_proofreading_issues_gin
```

#### 查询5：获取FAQ Schema统计

```sql
-- 统计使用FAQ Schema的文章
SELECT
    COUNT(*) as total_with_faq,
    COUNT(*) FILTER (WHERE jsonb_array_length(
        final_faq_schema->'mainEntity'
    ) >= 3) as faq_3plus,
    COUNT(*) FILTER (WHERE jsonb_array_length(
        final_faq_schema->'mainEntity'
    ) >= 5) as faq_5plus
FROM articles
WHERE final_faq_schema IS NOT NULL;
```

### 6.2 性能基准

| 查询类型 | 预期性能 | 索引要求 |
|---------|---------|---------|
| 按状态查询（<1000条） | <50ms | idx_articles_proofreading_status |
| 按时间范围查询 | <100ms | idx_articles_original_received |
| JSONB字段搜索 | <200ms | GIN索引 |
| 复杂聚合查询 | <500ms | 复合索引 |

---

## 7. 备份与回滚

### 7.1 备份策略

#### 迁移前备份

```bash
# 完整备份
pg_dump -U cms_user -d cms_automation \
    --format=custom \
    --file=/backup/cms_before_v3_migration_$(date +%Y%m%d).dump

# 仅备份articles表
pg_dump -U cms_user -d cms_automation \
    --table=articles \
    --format=custom \
    --file=/backup/articles_before_v3_$(date +%Y%m%d).dump

# 备份验证
pg_restore --list /backup/cms_before_v3_migration_*.dump | head -20
```

#### 增量备份

```bash
# 每天备份增量数据
pg_dump -U cms_user -d cms_automation \
    --table=articles \
    --where="updated_at > '$(date -d '1 day ago' +%Y-%m-%d)'" \
    --format=custom \
    --file=/backup/articles_incremental_$(date +%Y%m%d).dump
```

### 7.2 回滚方案

#### 方案1：仅回滚schema（保留数据）

```sql
-- 设置所有新字段为NULL（不删除列）
BEGIN;

UPDATE articles SET
    original_content = NULL,
    suggested_content = NULL,
    final_content = NULL,
    proofreading_status = 'pending';

-- 验证
SELECT COUNT(*) FROM articles WHERE original_content IS NOT NULL;

COMMIT;
```

#### 方案2：完全回滚（删除列）

```bash
# 使用回滚脚本（3.3节）
psql -U cms_user -d cms_automation -f rollback_v3_schema.sql
```

#### 方案3：从备份恢复

```bash
# 停止应用服务
systemctl stop cms-backend cms-frontend

# 恢复整个数据库
pg_restore -U cms_user -d cms_automation \
    --clean \
    --if-exists \
    /backup/cms_before_v3_migration_*.dump

# 重启服务
systemctl start cms-backend cms-frontend
```

---

## 8. 实施计划

### 8.1 实施阶段

#### 阶段1：准备阶段（T-3天）

**任务清单:**
- [ ] 代码审查和测试
- [ ] 在测试环境执行迁移脚本
- [ ] 验证新字段功能
- [ ] 准备回滚脚本
- [ ] 完整数据库备份

**责任人:** 后端团队
**预计时间:** 3天

#### 阶段2：迁移阶段（T-Day，维护窗口）

**时间规划:**
```
00:00 - 00:15  通知用户，设置只读模式
00:15 - 00:20  最终备份
00:20 - 00:30  执行迁移脚本
00:30 - 00:40  创建索引
00:40 - 00:50  验证数据完整性
00:50 - 01:00  部署新版本应用
01:00 - 01:15  冒烟测试
01:15 - 01:30  恢复服务，监控
```

**总维护时间:** 90分钟

#### 阶段3：验证阶段（T+1周）

**验证项:**
- [ ] 新文章创建和校对流程
- [ ] 版本管理功能正常
- [ ] FAQ Schema生成和存储
- [ ] 查询性能符合预期
- [ ] 存储空间增长正常
- [ ] 无数据丢失或损坏

**责任人:** QA团队
**预计时间:** 1周

#### 阶段4：优化阶段（T+2周）

**优化项:**
- [ ] 根据实际使用调整索引
- [ ] 优化慢查询
- [ ] 清理无用数据
- [ ] 文档更新

**责任人:** 后端团队 + DBA
**预计时间:** 1周

### 8.2 风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|---------|
| 迁移时间超时 | 低 | 高 | 提前在测试环境演练，准备分步迁移方案 |
| 索引创建失败 | 低 | 中 | 索引可后续创建，不影响功能 |
| 应用兼容性问题 | 中 | 高 | 充分测试，准备回滚方案 |
| 存储空间不足 | 低 | 高 | 提前扩容，监控存储使用 |
| 性能下降 | 低 | 中 | 索引优化，查询优化 |

### 8.3 成功标准

✅ **迁移成功标准:**
1. 所有迁移脚本执行成功（0错误）
2. 数据完整性验证通过（0数据丢失）
3. 索引创建成功（查询性能达标）
4. 应用服务正常启动（无报错）
5. 核心功能测试通过（100%通过率）

✅ **上线成功标准:**
1. 用户可正常创建和校对文章
2. 三版本管理功能正常
3. FAQ Schema生成和存储正常
4. 系统响应时间符合SLA（<2秒）
5. 无P0/P1级别bug

---

## 附录

### A. 字段命名规范

**命名原则:**
- 使用下划线分隔（snake_case）
- 版本前缀：`original_`, `suggested_`, `final_`
- 计数后缀：`_count`
- 时间后缀：`_at`
- JSONB字段：复数形式（`suggestions`, `issues`）

### B. JSONB最佳实践

**存储建议:**
1. 避免过深嵌套（<4层）
2. 数组元素数量控制（<1000个）
3. 单个JSONB字段<1MB
4. 使用合适的索引类型（GIN）

**查询优化:**
```sql
-- 好的查询（使用索引）
WHERE jsonb_field @> '{"key": "value"}'::jsonb

-- 差的查询（全表扫描）
WHERE jsonb_field->>'key' = 'value'
```

### C. 相关文档

- 📄 `article_proofreading_seo_workflow.md` - 完整工作流需求
- 📄 `structured_data_faq_schema.md` - FAQ Schema规范
- 📄 `proofreading_requirements.md` v3.0.0 - 校对功能需求

---

**文档版本**: 1.0.0
**最后更新**: 2025-10-26
**维护者**: CMS自动化系统团队 - 数据库组
**审核状态**: 待审核

