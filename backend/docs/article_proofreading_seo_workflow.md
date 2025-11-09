# CMS自动化系统 - 文章校对+SEO优化完整工作流需求文档

**版本:** 2.0.0
**创建日期:** 2025-10-26
**最后更新:** 2025-10-27
**状态:** 需求设计阶段
**优先级:** 高（上稿前必经流程）
**重大变更:** v2.0.0 采用单一 Prompt 综合分析架构，详见 `single_prompt_design.md`

---

## 📋 目录

1. [概述](#1-概述)
2. [业务场景与目标](#2-业务场景与目标)
3. [文稿格式规范](#3-文稿格式规范)
4. [版本管理系统](#4-版本管理系统)
5. [完整工作流程](#5-完整工作流程)
6. [功能模块详细设计](#6-功能模块详细设计)
7. [数据库模型设计](#7-数据库模型设计)
8. [API接口设计](#8-api接口设计)
9. [前端UI需求](#9-前端ui需求)
10. [AI服务集成](#10-ai服务集成)
11. [实现优先级与里程碑](#11-实现优先级与里程碑)
12. [测试与验证](#12-测试与验证)

---

## 1. 概述

### 1.1 文档目的

本文档定义了CMS自动化系统中**文章上稿前的完整处理流程**，包括：
- 文稿格式解析
- 多版本管理（原始/建议/最终）
- 全面校对（A-F类规则）
- AI驱动的内容优化
- SEO元数据优化
- FAQ Schema结构化数据生成
- 用户审核与确认

### 1.2 核心价值

| 价值维度 | 说明 |
|---------|------|
| **质量保证** | 通过A-F类规则全面校对，确保内容符合《大纪元、新唐人总部写作风格指南》|
| **SEO优化** | 自动生成并优化Meta Description、SEO关键词、FAQ Schema |
| **效率提升** | AI驱动的智能建议，减少人工修改时间 |
| **版本追溯** | 完整记录原始→建议→最终三个版本，支持回溯 |
| **合规保障** | F类规则强制验证，阻止不合规内容发布 |
| **术语一致性** | 单一Prompt架构确保正文、Meta、关键词、FAQ术语自动保持一致 |
| **成本优化** | 单次AI调用节省34% tokens，降低13%成本 |

### 1.3 适用范围

**适用于以下文章类型：**
- 新闻报道
- 评论文章
- 专题报道
- 所有需要上稿到WordPress的内容

**不适用于：**
- 紧急快讯（可能需要快速通道）
- 已发布文章的小修改（除非需要重新校对）

---

## 2. 业务场景与目标

### 2.1 典型业务场景

#### 场景1：记者提交新文稿
```
记者撰写文章 → 复制到系统 → 系统自动解析三部分 →
校对分析 → 生成建议版本 → 记者审核修改 →
确认最终版本 → 上稿发布
```

#### 场景2：编辑审核文稿
```
记者提交初稿 → 系统校对分析 → 编辑查看建议 →
编辑手动调整 → 系统重新分析 → 确认发布
```

#### 场景3：批量导入文章
```
CSV/JSON批量导入 → 逐篇解析校对 → 生成批量建议 →
人工批量审核 → 批量确认发布
```

### 2.2 业务目标

| 目标 | 衡量指标 | 目标值 |
|------|---------|--------|
| 校对准确率 | F类规则检测准确率 | ≥ 95% |
| 处理效率 | 单篇文章AI处理时间 | ≤ 3秒（单一Prompt架构） |
| SEO优化率 | Meta Description优化接受率 | ≥ 70% |
| 用户满意度 | 建议采纳率 | ≥ 60% |
| 发布合规性 | F类规则拦截率 | 100% |
| 术语一致性 | Meta/关键词/FAQ术语一致率 | 100%（自动保证） |
| 成本控制 | 单篇文章AI成本 | ≤ $0.053 |

---

## 3. 文稿格式规范

### 3.1 标准三部分结构

#### 格式说明

```
正文内容开始...
这里是文章的主体部分，可以包含多个段落。
段落之间用换行符分隔。

正文可以很长，包含多个段落。

Meta描述:
这里是Meta Description的内容，用于搜索引擎显示。建议长度150-160字符。

SEO关键词:
关键词1, 关键词2, 关键词3, 关键词4
```

#### 固定标记规范

| 标记 | 规则 | 示例 |
|------|------|------|
| **Meta描述标记** | 固定使用"Meta描述:" | `Meta描述:` |
| **SEO关键词标记** | 固定使用"SEO关键词:" | `SEO关键词:` |
| **标记位置** | 必须在独立行开头 | 不能在行中间 |
| **大小写** | 严格匹配（冒号必须是中文全角） | `Meta描述：` ❌ `Meta描述:` ✅ |

### 3.2 三个部分详细定义

#### 3.2.1 正文 (Main Body)

**定义：** 从文稿开始到第一个固定标记之间的所有内容

**特征：**
- 通常包含多个段落
- 可能包含标题、小标题
- 可能包含列表、引用等格式

**解析规则：**
```python
# 伪代码
content_end = min(
    position_of("Meta描述:") if exists else len(text),
    position_of("SEO关键词:") if exists else len(text)
)
main_body = text[0:content_end].strip()
```

#### 3.2.2 Meta描述 (Meta Description)

**定义：** "Meta描述:" 标记后到下一个标记或文末的内容

**特征：**
- 单段落文本
- 建议长度：150-160字符（中文约75-80字）
- 用于搜索引擎结果页显示

**解析规则：**
```python
# 伪代码
meta_start = position_of("Meta描述:") + len("Meta描述:")
meta_end = position_of("SEO关键词:") if exists else len(text)
meta_description = text[meta_start:meta_end].strip()
```

**验证规则：**
- 长度验证：警告过短（<100字符）或过长（>200字符）
- 内容验证：不应包含特殊字符、HTML标签
- 语义验证：应与正文内容相关（AI检测）

#### 3.2.3 SEO关键词 (SEO Keywords)

**定义：** "SEO关键词:" 标记后到文末的内容

**特征：**
- 逗号分隔的关键词列表
- 建议数量：3-8个关键词
- 每个关键词2-5个字为佳

**解析规则：**
```python
# 伪代码
keywords_start = position_of("SEO关键词:") + len("SEO关键词:")
keywords_text = text[keywords_start:].strip()
keywords_list = [kw.strip() for kw in keywords_text.split(",")]
```

**验证规则：**
- 数量验证：警告过少（<2个）或过多（>10个）
- 格式验证：去除空白、验证分隔符
- 重复验证：检测并警告重复关键词
- 相关性验证：关键词应在正文中出现（AI检测）

### 3.3 不完整文稿处理

#### 情况1：仅有正文
```
正文内容...
（无Meta描述和SEO关键词）
```
**处理方式：**
- 正常解析正文
- `meta_description = None`
- `seo_keywords = []`
- 系统生成建议的Meta和关键词

#### 情况2：有正文和Meta，无关键词
```
正文内容...

Meta描述:
这是描述内容
（无SEO关键词）
```
**处理方式：**
- 解析正文和Meta
- `seo_keywords = []`
- 系统生成建议的关键词

#### 情况3：有正文和关键词，无Meta
```
正文内容...

SEO关键词:
关键词1, 关键词2
（无Meta描述）
```
**处理方式：**
- 解析正文和关键词
- `meta_description = None`
- 系统生成建议的Meta

### 3.4 特殊情况处理

#### 情况A：标记顺序错误
```
正文内容...

SEO关键词:
关键词列表

Meta描述:
描述内容
```
**处理方式：**
- 智能识别，不强制顺序
- 按标记类型正确归类
- 记录警告日志

#### 情况B：重复标记
```
正文内容...

Meta描述:
第一个描述

Meta描述:
第二个描述
```
**处理方式：**
- 采用第一次出现的标记
- 后续同名标记内容归入正文
- 记录警告

#### 情况C：标记在正文中间
```
正文第一段...

Meta描述:
这是描述

正文第二段...（此段如何处理？）
```
**处理方式：**
- 标记后的内容不再视为正文
- 记录警告：检测到正文被截断
- 建议用户调整格式

---

## 4. 版本管理系统

### 4.1 三版本架构

#### 版本定义

| 版本名称 | 英文名 | 用途 | 可编辑 | 来源 |
|---------|-------|------|--------|------|
| **原始版本** | Original | 保存原始输入，追溯来源 | ❌ 否 | 用户输入 |
| **建议版本** | Suggested | AI分析后的优化建议 | ❌ 否 | AI生成 |
| **最终版本** | Final | 用户确认的发布版本 | ✅ 是 | 用户确认 |

#### 版本流转图

```
┌─────────────┐
│  用户输入    │
│  原始文稿    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 原始版本     │ ◄─── 永久保存，不可修改
│ (Original)  │
└──────┬──────┘
       │
       │ AI分析
       │ 校对+优化
       ▼
┌─────────────┐
│ 建议版本     │ ◄─── AI生成，不可修改
│ (Suggested) │      （可重新生成）
└──────┬──────┘
       │
       │ 用户审核
       │ 接受/拒绝/修改
       ▼
┌─────────────┐
│ 最终版本     │ ◄─── 用户可编辑
│ (Final)     │      确认后发布
└──────┬──────┘
       │
       │ 确认发布
       ▼
┌─────────────┐
│  上稿发布    │
└─────────────┘
```

### 4.2 版本字段详细设计

#### 原始版本字段 (Original Version)

```python
class ArticleOriginalVersion:
    # 正文
    original_content: Text
    original_content_word_count: Integer

    # Meta描述
    original_meta_description: Optional[Text]
    original_meta_char_count: Optional[Integer]

    # SEO关键词
    original_seo_keywords: Optional[JSONB]  # ["关键词1", "关键词2", ...]
    original_keyword_count: Optional[Integer]

    # 元数据
    original_received_at: DateTime
    original_format_valid: Boolean
    original_parse_warnings: Optional[JSONB]  # 解析警告列表
```

#### 建议版本字段 (Suggested Version)

```python
class ArticleSuggestedVersion:
    # 正文建议
    suggested_content: Text
    suggested_content_changes: JSONB  # 修改详情（diff数据）

    # Meta描述建议
    suggested_meta_description: Text
    suggested_meta_reasoning: Text  # AI生成理由
    suggested_meta_score: Float  # 评分 0-1

    # SEO关键词建议
    suggested_seo_keywords: JSONB
    suggested_keywords_reasoning: Text
    suggested_keywords_score: Float

    # 段落建议
    paragraph_suggestions: JSONB  # 段落优化建议
    paragraph_split_suggestions: JSONB  # 分段建议

    # FAQ Schema建议
    faq_schema_proposals: JSONB  # 多套FAQ方案

    # 校对问题
    proofreading_issues: JSONB  # A-F类规则检测问题
    critical_issues_count: Integer  # F类关键问题数

    # 生成元数据
    suggested_generated_at: DateTime
    ai_model_used: String  # 使用的AI模型
    generation_cost: Decimal  # 生成成本（API费用）
```

#### 最终版本字段 (Final Version)

```python
class ArticleFinalVersion:
    # 正文
    final_content: Text
    final_content_word_count: Integer

    # Meta描述
    final_meta_description: Text
    final_meta_char_count: Integer

    # SEO关键词
    final_seo_keywords: JSONB
    final_keyword_count: Integer

    # FAQ Schema
    final_faq_schema: Optional[JSONB]  # 最终选定的FAQ Schema

    # 用户选择记录
    user_accepted_suggestions: JSONB  # 用户接受的建议项
    user_rejected_suggestions: JSONB  # 用户拒绝的建议项
    user_manual_edits: JSONB  # 用户手动编辑内容

    # 确认元数据
    final_confirmed_at: DateTime
    final_confirmed_by: Integer  # user_id
    final_version_number: Integer  # 版本号（支持多次修改）
```

### 4.2 用户决策与调优追踪 ⭐新增

```python
class ProofreadingDecisionRecord:
    decision_id: UUID
    history_id: Integer
    suggestion_id: UUID
    suggestion_type: String  # proofreading / seo / tag / segmentation / other
    rule_id: Optional[String]
    original_text: Text
    suggested_text: Optional[Text]
    final_text: Optional[Text]
    decision: String  # accepted / rejected / modified
    feedback_option_id: Optional[Integer]
    feedback_text: Optional[Text]
    decided_by: Integer
    decided_at: DateTime
    feedback_status: String  # pending / in_progress / completed / failed
    feedback_processed_at: Optional[DateTime]
    tuning_batch_id: Optional[UUID]
    prompt_or_rule_version: Optional[String]
```

> 注：此处“调优”指语言质量团队根据用户反馈手动复盘并调整 deterministic 规则或 AI Prompt，而非自动化模型训练。

**流程说明：**
1. UI 对每条建议提供「接受」「保留原文」「部分采用」操作。  
2. 当用户选择非接受路径时，弹出可选反馈（多选项 + 自定义文本）。  
3. 前端以批量方式调用 `POST /proofreading/decisions` 将决策写入 `proofreading_decisions`。  
4. 后端在保存时同步更新 `proofreading_history` 的 `accepted_count` / `rejected_count` / `modified_count` 与 `pending_feedback_count`。  
5. 调优导出任务依据 `feedback_status='pending'` 拉取数据，标记为 `in_progress`，成功完成人工复盘并用于脚本/Prompt 调优后更新为 `completed`，同时记录 `tuning_batch_id` / `prompt_or_rule_version` / `feedback_processed_at`。  
6. 若调优失败或暂未处理，标记 `failed` 并记录原因，允许运营重置为 `pending` 重新纳入复盘队列。  
7. 统计报表可通过 `pending_feedback_count`、`feedback_completed_count` 追踪未处理/已吸收的反馈比例。

**调优批次管理（可选）**
- `feedback_tuning_jobs` 表记录每次 prompt 或脚本调整所使用的反馈集合，支持溯源。  
- 导出/复盘完成后，将相关决策关联到对应批次，便于回顾是谁在何时基于哪些反馈做了哪些调整。  
- 监控面板展示各批次进度、失败率、涉及的 Prompt/规则版本。

### 4.3 版本状态机

#### 状态定义

```python
class ProofreadingStatus(Enum):
    PENDING = "pending"              # 待处理
    PARSING = "parsing"              # 解析中
    ANALYZING = "analyzing"          # 校对分析中
    SUGGESTED = "suggested"          # 已生成建议
    USER_REVIEWING = "user_reviewing" # 用户审核中
    USER_EDITING = "user_editing"    # 用户编辑中
    CONFIRMED = "confirmed"          # 已确认
    PUBLISHING = "publishing"        # 发布中
    PUBLISHED = "published"          # 已发布
    FAILED = "failed"                # 处理失败
```

#### 状态转换规则

```
PENDING → PARSING → ANALYZING → SUGGESTED
                                    ↓
                          USER_REVIEWING ↔ USER_EDITING
                                    ↓
                              CONFIRMED → PUBLISHING → PUBLISHED

任意状态 → FAILED（发生错误时）
```

#### 状态转换条件

| 从状态 | 到状态 | 触发条件 | 回滚条件 |
|-------|--------|---------|---------|
| PENDING | PARSING | 文章创建/导入 | - |
| PARSING | ANALYZING | 解析成功 | 解析失败→FAILED |
| ANALYZING | SUGGESTED | AI分析完成 | AI失败→FAILED |
| SUGGESTED | USER_REVIEWING | 用户打开审核页面 | - |
| USER_REVIEWING | USER_EDITING | 用户点击编辑 | - |
| USER_EDITING | USER_REVIEWING | 用户保存编辑 | - |
| USER_REVIEWING | CONFIRMED | 用户点击确认 | F类关键问题→阻止 |
| CONFIRMED | PUBLISHING | 用户点击发布 | - |
| PUBLISHING | PUBLISHED | 发布成功 | 发布失败→CONFIRMED |

---

## 5. 完整工作流程

### 5.1 流程总览

```
┌─────────────────────────────────────────────────────────────────┐
│                   文章上稿前处理流程 (v2.0 单一Prompt架构)           │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────┐
  │ 原稿输入  │
  └────┬─────┘
       │
       ▼
  ┌──────────────────┐
  │ 文稿格式解析       │
  │ (ArticleParser)  │
  │ - 识别三部分       │
  │ - 验证格式         │
  └────┬─────────────┘
       │
       ▼
  ┌──────────────────┐
  │ 保存原始版本       │
  │ (Original)       │
  └────┬─────────────┘
       │
       ▼
  ┌───────────────────────────────────────────────────────┐
  │   ProofreadingAnalysisService.analyze_article()        │
  │   单一 Prompt + 程序化校验（总耗时 ~3.0 秒）            │
  │                                                       │
  │  Step A: Claude 单次调用（PromptBuilder）               │
  │  ✓ A-F 类规则逐条审核（含 rule_coverage 列表）          │
  │  ✓ 正文优化 / Meta / 关键词 / FAQ                      │
  │                                                       │
  │  Step B: DeterministicRuleEngine.run()                │
  │  ✓ B2-002 半角逗号检测                                 │
  │  ✓ F1-002 特色图横幅校验                               │
  │  ✓ F2-001 标题层级检查（持续扩充可程序化规则）          │
  │                                                       │
  │  Step C: ProofreadingResultMerger.merge()             │
  │  ✓ AI + 脚本结果比对与去重                              │
  │  ✓ source_breakdown（ai/script/merged）统计            │
  │  ✓ F 类阻断自动写入 critical_issues_count             │
  └────────────────────────┬──────────────────────────────┘
                   │
                   ▼
            ┌─────────────┐
            │ 生成建议版本  │
            │ (Suggested) │
            │ - 应用校对建议│
            │ - 优化Meta   │
            │ - 优化关键词  │
            │ - 生成FAQ    │
            └──────┬──────┘
                   │
                   ▼
            ┌─────────────────┐
            │ 用户审核界面      │
            │ - 对比显示       │
            │ - Diff高亮       │
            │ - 逐项选择       │
            │ - FAQ版本选择   │
            └──────┬──────────┘
                   │
                   │ ┌─────────┐
                   │ │ 用户编辑 │
                   │ └────┬────┘
                   │      │
                   ▼◄─────┘
            ┌─────────────┐
            │ 确定最终版本  │
            │ (Final)     │
            └──────┬──────┘
                   │
                   ▼
            ┌─────────────┐
            │ F类规则最终  │
            │ 合规性检查    │
            └──────┬──────┘
                   │
                   │ 通过
                   ▼
            ┌─────────────┐
            │  上稿发布    │
            └─────────────┘

**关键改进 (v2.1):**
- ⚡ AI 单次调用 + 脚本并行合并，总耗时稳定在 ~3 秒
- 🔐 F 类强制规则由脚本兜底，杜绝幻觉导致的漏检
- 📊 `source_breakdown` 支撑监控 AI / 脚本命中率，快速发现漂移
- 📦 ProofreadingAnalysisService 统一 orchestrate，后端/前端/CI 共用同一输出 schema
```

### 5.2 阶段详细说明

#### 阶段1：原稿输入与解析

**输入来源：**
1. 前端Web编辑器手动输入
2. 文本文件批量导入（.txt）
3. CSV批量导入
4. API接口提交

**解析步骤：**
```python
async def parse_article(raw_text: str) -> ParsedArticle:
    """
    解析文稿，识别三部分
    """
    # 1. 检测固定标记
    meta_marker = "Meta描述:"
    keywords_marker = "SEO关键词:"

    # 2. 分割文本
    parts = split_by_markers(raw_text, [meta_marker, keywords_marker])

    # 3. 提取各部分
    main_body = parts.get("content", "").strip()
    meta_desc = parts.get("Meta描述", None)
    seo_keywords = parts.get("SEO关键词", None)

    # 4. 解析关键词列表
    if seo_keywords:
        keywords_list = [kw.strip() for kw in seo_keywords.split(",")]
    else:
        keywords_list = []

    # 5. 格式验证
    warnings = validate_format(parts)

    return ParsedArticle(
        main_body=main_body,
        meta_description=meta_desc,
        seo_keywords=keywords_list,
        parse_warnings=warnings,
        format_valid=len(warnings) == 0
    )
```

**验证项：**
- ✅ 正文是否为空
- ✅ Meta描述长度是否合理（100-200字符）
- ✅ 关键词数量是否合理（2-10个）
- ✅ 是否存在格式异常（如标记重复、顺序错误）

#### 阶段2：原始版本保存

**保存内容：**
```python
original_version = {
    "original_content": main_body,
    "original_content_word_count": count_words(main_body),
    "original_meta_description": meta_desc,
    "original_meta_char_count": len(meta_desc) if meta_desc else 0,
    "original_seo_keywords": keywords_list,
    "original_keyword_count": len(keywords_list),
    "original_received_at": datetime.now(),
    "original_format_valid": format_valid,
    "original_parse_warnings": warnings
}
```

**保存原则：**
- 🔒 **不可修改**：原始版本一旦保存，不允许任何修改
- 📝 **完整记录**：包括所有解析警告、元数据
- 🔍 **可追溯**：支持后续对比和审计

#### 阶段3：全面校对分析

**校对范围：**

| 校对对象 | 应用规则 | 规则数量 |
|---------|---------|---------|
| 正文内容 | A-F类全部规则 | ~450条 |
| Meta描述 | A-E类（语言规范）+ 长度限制 | ~430条 + 长度 |
| SEO关键词 | 格式验证 + 相关性检测 | 自定义规则 |

**正文校对：**
```python
async def proofread_content(content: str) -> ProofreadingResult:
    """
    对正文进行A-F类规则校对
    """
    issues = []

    # A类：用字与用词
    issues.extend(await check_word_usage(content))

    # B类：标点符号
    issues.extend(await check_punctuation(content))

    # C类：数字用法
    issues.extend(await check_number_usage(content))

    # D类：人名地名译名
    issues.extend(await check_name_translation(content))

    # E类：报导用词
    issues.extend(await check_reporting_terms(content))

    # F类：发布合规（如标题层级）
    issues.extend(await check_publishing_compliance(content))

    return ProofreadingResult(
        issues=issues,
        critical_count=count_critical(issues),
        error_count=count_errors(issues),
        warning_count=count_warnings(issues)
    )
```

**Meta描述校对：**
```python
async def proofread_meta_description(meta: str) -> MetaProofreadingResult:
    """
    校对Meta描述
    """
    issues = []

    # 应用A-E类语言规范
    issues.extend(await check_language_rules(meta))

    # 长度检查
    char_count = len(meta)
    if char_count < 100:
        issues.append(Issue(
            severity="warning",
            message=f"Meta描述过短({char_count}字符)，建议150-160字符"
        ))
    elif char_count > 200:
        issues.append(Issue(
            severity="error",
            message=f"Meta描述过长({char_count}字符)，可能被搜索引擎截断"
        ))

    # 内容质量检查
    if not contains_keywords(meta):
        issues.append(Issue(
            severity="warning",
            message="Meta描述中未包含SEO关键词"
        ))

    return MetaProofreadingResult(issues=issues)
```

**关键词校对：**
```python
async def proofread_keywords(keywords: List[str], content: str) -> KeywordProofreadingResult:
    """
    校对SEO关键词
    """
    issues = []

    # 数量检查
    if len(keywords) < 2:
        issues.append(Issue(severity="warning", message="关键词数量过少，建议3-8个"))
    elif len(keywords) > 10:
        issues.append(Issue(severity="warning", message="关键词数量过多，建议3-8个"))

    # 重复检查
    duplicates = find_duplicates(keywords)
    if duplicates:
        issues.append(Issue(
            severity="warning",
            message=f"发现重复关键词: {', '.join(duplicates)}"
        ))

    # 相关性检查（AI）
    for keyword in keywords:
        if not keyword_appears_in_content(keyword, content):
            issues.append(Issue(
                severity="info",
                message=f"关键词'{keyword}'未在正文中出现"
            ))

    return KeywordProofreadingResult(issues=issues)
```

#### 阶段4：AI内容优化

**4.1 段落分析**

```python
async def analyze_paragraphs(content: str) -> ParagraphAnalysis:
    """
    AI分析段落结构，提出优化建议
    """
    paragraphs = split_into_paragraphs(content)
    suggestions = []

    for idx, para in enumerate(paragraphs):
        word_count = count_words(para)

        # 检测过长段落（>200字）
        if word_count > 200:
            # 调用AI建议分段位置
            split_positions = await ai_suggest_split_positions(para)
            suggestions.append({
                "paragraph_index": idx,
                "issue": "paragraph_too_long",
                "current_word_count": word_count,
                "suggested_split_positions": split_positions,
                "reasoning": "段落过长影响阅读体验，建议分段"
            })

        # 检测过短段落（<20字）
        elif word_count < 20:
            suggestions.append({
                "paragraph_index": idx,
                "issue": "paragraph_too_short",
                "current_word_count": word_count,
                "suggestion": "consider_merging",
                "reasoning": "段落过短，考虑与前后段合并"
            })

    return ParagraphAnalysis(suggestions=suggestions)
```

**4.2 内容优化**

```python
async def optimize_content(content: str, issues: List[Issue]) -> ContentOptimization:
    """
    根据校对问题，AI生成优化建议
    """
    optimizations = []

    for issue in issues:
        if issue.severity in ["critical", "error"]:
            # 对于严重问题，AI提供修正建议
            fix_suggestion = await ai_suggest_fix(content, issue)
            optimizations.append({
                "issue_id": issue.id,
                "original_text": issue.context,
                "suggested_text": fix_suggestion,
                "reasoning": issue.message,
                "confidence": fix_suggestion.confidence
            })

    return ContentOptimization(optimizations=optimizations)
```

#### 阶段5：Meta & 关键词优化

**5.1 Meta描述优化**

```python
async def optimize_meta_description(
    original_meta: Optional[str],
    content: str,
    keywords: List[str]
) -> MetaOptimization:
    """
    优化Meta描述
    """
    if original_meta:
        # 有原始Meta，进行优化
        optimized = await ai_optimize_meta(original_meta, content, keywords)
    else:
        # 无原始Meta，AI生成
        optimized = await ai_generate_meta(content, keywords)

    # 确保长度合规
    optimized_text = adjust_length(optimized, target_length=155)

    return MetaOptimization(
        original=original_meta,
        suggested=optimized_text,
        char_count=len(optimized_text),
        includes_keywords=check_keywords_included(optimized_text, keywords),
        reasoning="基于正文内容和关键词优化",
        score=calculate_seo_score(optimized_text)
    )
```

**AI Prompt示例：**
```
你是一个SEO专家。请为以下文章生成Meta Description：

文章正文：
{content}

SEO关键词：
{keywords}

要求：
1. 长度：150-160字符（中文约75-80字）
2. 必须包含至少2个关键词
3. 准确概括文章核心内容
4. 语言吸引人，鼓励点击
5. 避免堆砌关键词

请生成Meta Description：
```

**5.2 关键词优化**

```python
async def optimize_keywords(
    original_keywords: List[str],
    content: str,
    meta: str
) -> KeywordOptimization:
    """
    优化SEO关键词
    """
    if original_keywords:
        # 有原始关键词，进行优化
        optimized = await ai_optimize_keywords(original_keywords, content)
    else:
        # 无原始关键词，AI提取
        optimized = await ai_extract_keywords(content, meta)

    # 关键词排序（相关性 + 重要性）
    optimized_sorted = await rank_keywords(optimized, content)

    # 限制数量（3-8个）
    final_keywords = optimized_sorted[:8]

    return KeywordOptimization(
        original=original_keywords,
        suggested=final_keywords,
        keyword_count=len(final_keywords),
        reasoning="基于内容相关性和SEO价值提取",
        relevance_scores={kw: score for kw, score in zip(final_keywords, scores)}
    )
```

**AI Prompt示例：**
```
你是一个SEO专家。请为以下文章提取SEO关键词：

文章正文：
{content}

Meta描述：
{meta}

要求：
1. 数量：3-8个关键词
2. 每个关键词2-5个字
3. 必须在正文中出现
4. 按重要性排序
5. 考虑搜索意图和竞争度

请提取关键词（JSON格式）：
[
  {"keyword": "关键词1", "relevance": 0.95, "reasoning": "原因"},
  ...
]
```

#### 阶段6：FAQ Schema生成

**（详见 `structured_data_faq_schema.md` 文档）**

```python
async def generate_faq_schema(content: str) -> FAQSchemaProposal:
    """
    生成FAQ Schema结构化数据
    """
    # AI提取3-5个常见问题
    questions = await ai_extract_questions(content, num_questions=5)

    # 为每个问题生成答案
    faq_items = []
    for q in questions:
        answer = await ai_generate_answer(q, content)
        faq_items.append({
            "question": q,
            "answer": answer
        })

    # 生成Schema.org格式
    schema = generate_schema_org_faq(faq_items)

    return FAQSchemaProposal(
        faq_items=faq_items,
        schema_json_ld=schema,
        item_count=len(faq_items)
    )
```

#### 阶段7：生成建议版本

**汇总所有优化建议：**
```python
async def generate_suggested_version(
    original: OriginalVersion,
    proofreading: ProofreadingResult,
    content_opt: ContentOptimization,
    meta_opt: MetaOptimization,
    keyword_opt: KeywordOptimization,
    paragraph_analysis: ParagraphAnalysis,
    faq_proposals: List[FAQSchemaProposal]
) -> SuggestedVersion:
    """
    汇总生成建议版本
    """
    return SuggestedVersion(
        # 正文建议
        suggested_content=apply_optimizations(
            original.content,
            content_opt.optimizations
        ),
        suggested_content_changes=compute_diff(
            original.content,
            suggested_content
        ),

        # Meta建议
        suggested_meta_description=meta_opt.suggested,
        suggested_meta_reasoning=meta_opt.reasoning,
        suggested_meta_score=meta_opt.score,

        # 关键词建议
        suggested_seo_keywords=keyword_opt.suggested,
        suggested_keywords_reasoning=keyword_opt.reasoning,
        suggested_keywords_score=calculate_avg_relevance(keyword_opt),

        # 段落建议
        paragraph_suggestions=paragraph_analysis.suggestions,

        # FAQ Schema建议（多套方案）
        faq_schema_proposals=faq_proposals,

        # 校对问题
        proofreading_issues=proofreading.issues,
        critical_issues_count=proofreading.critical_count,

        # 元数据
        suggested_generated_at=datetime.now(),
        ai_model_used="claude-3-5-sonnet",
        generation_cost=calculate_cost()
    )
```

#### 阶段8：用户审核与确认

**用户操作：**
1. **查看对比**：Original vs Suggested 并排显示
2. **逐项审核**：每个建议可独立接受/拒绝
3. **手动编辑**：可直接修改任何部分
4. **确认发布**：生成Final版本

**用户可选操作：**
```python
class UserReviewAction(Enum):
    ACCEPT_ALL = "accept_all"           # 全部接受建议
    ACCEPT_PARTIAL = "accept_partial"   # 部分接受
    REJECT_ALL = "reject_all"           # 全部拒绝（使用原始）
    MANUAL_EDIT = "manual_edit"         # 手动编辑
```

**生成最终版本：**
```python
async def generate_final_version(
    original: OriginalVersion,
    suggested: SuggestedVersion,
    user_choices: UserChoices
) -> FinalVersion:
    """
    根据用户选择生成最终版本
    """
    final_content = apply_user_choices(
        original.content,
        suggested.content,
        user_choices.content_decisions
    )

    final_meta = (
        user_choices.meta_custom if user_choices.meta_custom
        else suggested.meta if user_choices.accept_meta_suggestion
        else original.meta
    )

    final_keywords = (
        user_choices.keywords_custom if user_choices.keywords_custom
        else suggested.keywords if user_choices.accept_keywords_suggestion
        else original.keywords
    )

    final_faq = (
        user_choices.selected_faq_schema if user_choices.use_faq_schema
        else None
    )

    return FinalVersion(
        final_content=final_content,
        final_meta_description=final_meta,
        final_seo_keywords=final_keywords,
        final_faq_schema=final_faq,
        user_accepted_suggestions=user_choices.accepted,
        user_rejected_suggestions=user_choices.rejected,
        user_manual_edits=user_choices.manual_edits,
        final_confirmed_at=datetime.now(),
        final_confirmed_by=user_choices.user_id,
        final_version_number=1
    )
```

#### 阶段9：最终合规检查

**F类规则强制验证：**
```python
async def final_compliance_check(final: FinalVersion) -> ComplianceCheckResult:
    """
    发布前F类规则最终检查
    """
    critical_issues = []

    # F1: 图片规格（如有特色图片）
    if final.featured_image:
        image_issues = await validate_featured_image(final.featured_image)
        critical_issues.extend([i for i in image_issues if i.blocks_publish])

    # F2: 标题层级
    heading_issues = await validate_heading_hierarchy(final.content)
    critical_issues.extend([i for i in heading_issues if i.blocks_publish])

    # F3: 版权合规
    copyright_issues = await validate_copyright(final.images)
    critical_issues.extend([i for i in copyright_issues if i.blocks_publish])

    if critical_issues:
        return ComplianceCheckResult(
            passed=False,
            blocking_issues=critical_issues,
            message="存在阻止发布的关键问题，必须修正后才能发布"
        )

    return ComplianceCheckResult(passed=True)
```

**阻止发布示例：**
```python
if not compliance_check.passed:
    raise PublishBlockedException(
        message="发布被阻止：存在F类关键问题",
        blocking_issues=compliance_check.blocking_issues,
        article_id=article.id
    )
```

#### 阶段10：上稿发布

**发布流程：**
```python
async def publish_article(article_id: int) -> PublishResult:
    """
    发布文章到WordPress
    """
    article = await get_article(article_id)

    # 1. 获取最终版本
    final = article.final_version

    # 2. 最终合规检查
    compliance = await final_compliance_check(final)
    if not compliance.passed:
        raise PublishBlockedException(compliance.blocking_issues)

    # 3. 准备发布数据
    wordpress_data = {
        "title": article.title,
        "content": final.final_content,
        "excerpt": final.final_meta_description,
        "tags": final.final_seo_keywords,
        "status": "publish"
    }

    # 4. 如有FAQ Schema，注入到文章
    if final.final_faq_schema:
        wordpress_data["meta"] = {
            "faq_schema": json.dumps(final.final_faq_schema)
        }

    # 5. 发布到WordPress
    wp_response = await wordpress_client.create_post(wordpress_data)

    # 6. 更新文章状态
    article.proofreading_status = ProofreadingStatus.PUBLISHED
    article.published_at = datetime.now()
    article.wordpress_post_id = wp_response["id"]

    await save_article(article)

    return PublishResult(
        success=True,
        wordpress_post_id=wp_response["id"],
        wordpress_url=wp_response["link"]
    )
```

---

## 6. 功能模块详细设计

### 6.1 文稿解析器 (ArticleParser)

#### 模块职责
- 解析原始文稿，识别三部分结构
- 验证格式完整性
- 处理特殊情况和异常格式

#### 核心方法

```python
class ArticleParser:
    """文稿解析器"""

    def __init__(self):
        self.meta_marker = "Meta描述:"
        self.keywords_marker = "SEO关键词:"

    async def parse(self, raw_text: str) -> ParsedArticle:
        """主解析方法"""
        # 检测标记位置
        markers = self._detect_markers(raw_text)

        # 分割文本
        parts = self._split_by_markers(raw_text, markers)

        # 提取各部分
        main_body = self._extract_main_body(parts)
        meta_desc = self._extract_meta_description(parts)
        keywords = self._extract_keywords(parts)

        # 验证格式
        warnings = self._validate_format(parts, markers)

        return ParsedArticle(
            main_body=main_body,
            meta_description=meta_desc,
            seo_keywords=keywords,
            parse_warnings=warnings,
            format_valid=len(warnings) == 0
        )

    def _detect_markers(self, text: str) -> Dict[str, int]:
        """检测标记位置"""
        markers = {}

        # 查找Meta描述标记
        meta_pos = text.find(self.meta_marker)
        if meta_pos != -1:
            markers["Meta描述"] = meta_pos

        # 查找SEO关键词标记
        keywords_pos = text.find(self.keywords_marker)
        if keywords_pos != -1:
            markers["SEO关键词"] = keywords_pos

        return markers

    def _split_by_markers(self, text: str, markers: Dict) -> Dict[str, str]:
        """按标记分割文本"""
        parts = {}

        # 按位置排序标记
        sorted_markers = sorted(markers.items(), key=lambda x: x[1])

        # 提取正文（第一个标记之前）
        if sorted_markers:
            first_pos = sorted_markers[0][1]
            parts["正文"] = text[:first_pos].strip()
        else:
            parts["正文"] = text.strip()
            return parts

        # 提取标记内容
        for i, (marker_name, marker_pos) in enumerate(sorted_markers):
            # 标记开始位置（跳过标记本身）
            marker_text = self.meta_marker if marker_name == "Meta描述" else self.keywords_marker
            start = marker_pos + len(marker_text)

            # 标记结束位置（下一个标记或文末）
            if i + 1 < len(sorted_markers):
                end = sorted_markers[i + 1][1]
            else:
                end = len(text)

            parts[marker_name] = text[start:end].strip()

        return parts

    def _extract_keywords(self, parts: Dict) -> List[str]:
        """提取关键词列表"""
        keywords_text = parts.get("SEO关键词", "")
        if not keywords_text:
            return []

        # 按逗号分割
        keywords = [kw.strip() for kw in keywords_text.split(",")]

        # 过滤空关键词
        keywords = [kw for kw in keywords if kw]

        return keywords

    def _validate_format(self, parts: Dict, markers: Dict) -> List[str]:
        """验证格式，返回警告列表"""
        warnings = []

        # 检查正文是否为空
        if not parts.get("正文"):
            warnings.append("警告：正文内容为空")

        # 检查Meta描述
        meta = parts.get("Meta描述", "")
        if meta:
            char_count = len(meta)
            if char_count < 100:
                warnings.append(f"警告：Meta描述过短（{char_count}字符），建议150-160字符")
            elif char_count > 200:
                warnings.append(f"警告：Meta描述过长（{char_count}字符），可能被截断")

        # 检查关键词
        keywords = self._extract_keywords(parts)
        if keywords:
            if len(keywords) < 2:
                warnings.append(f"警告：关键词数量过少（{len(keywords)}个），建议3-8个")
            elif len(keywords) > 10:
                warnings.append(f"警告：关键词数量过多（{len(keywords)}个），建议3-8个")

        # 检查标记顺序
        if "Meta描述" in markers and "SEO关键词" in markers:
            if markers["SEO关键词"] < markers["Meta描述"]:
                warnings.append("信息：SEO关键词在Meta描述之前（非标准顺序，但已正确解析）")

        return warnings
```

### 6.2 校对引擎 (ProofreadingEngine)

#### 模块职责
- 应用A-F类规则校对文本
- 检测语言、标点、格式问题
- 生成问题报告和修正建议

#### 核心架构

```python
class ProofreadingEngine:
    """校对引擎 - 应用A-F类规则"""

    def __init__(self, rule_repository: RuleRepository):
        self.rules = rule_repository
        self.checkers = {
            "A": WordUsageChecker(self.rules.get_category("A")),
            "B": PunctuationChecker(self.rules.get_category("B")),
            "C": NumberUsageChecker(self.rules.get_category("C")),
            "D": NameTranslationChecker(self.rules.get_category("D")),
            "E": ReportingTermsChecker(self.rules.get_category("E")),
            "F": PublishingComplianceChecker(self.rules.get_category("F"))
        }

    async def proofread_full_article(
        self,
        content: str,
        meta: Optional[str],
        keywords: List[str]
    ) -> FullProofreadingResult:
        """校对完整文章（三部分）"""

        # 1. 校对正文（A-F全部规则）
        content_result = await self.proofread_content(content)

        # 2. 校对Meta描述（A-E类）
        meta_result = None
        if meta:
            meta_result = await self.proofread_meta(meta)

        # 3. 校对关键词（格式+相关性）
        keywords_result = await self.proofread_keywords(keywords, content)

        # 4. 汇总结果
        return FullProofreadingResult(
            content_issues=content_result,
            meta_issues=meta_result,
            keywords_issues=keywords_result,
            total_critical=sum_critical([content_result, meta_result, keywords_result]),
            total_errors=sum_errors([content_result, meta_result, keywords_result]),
            total_warnings=sum_warnings([content_result, meta_result, keywords_result])
        )

    async def proofread_content(self, content: str) -> ProofreadingResult:
        """校对正文内容"""
        all_issues = []

        # 应用A-F类规则
        for category, checker in self.checkers.items():
            issues = await checker.check(content)
            all_issues.extend(issues)

        return ProofreadingResult(
            issues=all_issues,
            critical_count=count_by_severity(all_issues, "critical"),
            error_count=count_by_severity(all_issues, "error"),
            warning_count=count_by_severity(all_issues, "warning"),
            info_count=count_by_severity(all_issues, "info")
        )

    async def proofread_meta(self, meta: str) -> MetaProofreadingResult:
        """校对Meta描述（A-E类 + 长度）"""
        issues = []

        # 应用A-E类语言规范
        for category in ["A", "B", "C", "D", "E"]:
            checker = self.checkers[category]
            category_issues = await checker.check(meta)
            issues.extend(category_issues)

        # 长度验证
        char_count = len(meta)
        if char_count < 100:
            issues.append(Issue(
                rule_id="META-001",
                severity="warning",
                category="meta",
                message=f"Meta描述过短（{char_count}字符），建议150-160字符",
                context=meta[:50]
            ))
        elif char_count > 200:
            issues.append(Issue(
                rule_id="META-002",
                severity="error",
                category="meta",
                message=f"Meta描述过长（{char_count}字符），将被搜索引擎截断",
                context=meta[:50]
            ))

        return MetaProofreadingResult(issues=issues, char_count=char_count)
```

### 6.3 段落分析器 (ParagraphAnalyzer)

#### 模块职责
- 检测段落长度问题
- AI建议分段位置
- 分析段落结构合理性

```python
class ParagraphAnalyzer:
    """段落分析器 - AI驱动"""

    def __init__(self, ai_client: AnthropicClient):
        self.ai = ai_client
        self.max_paragraph_length = 200  # 字数
        self.min_paragraph_length = 20

    async def analyze(self, content: str) -> ParagraphAnalysis:
        """分析段落结构"""
        paragraphs = self._split_paragraphs(content)
        suggestions = []

        for idx, para in enumerate(paragraphs):
            word_count = self._count_words(para)

            # 过长段落
            if word_count > self.max_paragraph_length:
                split_suggestions = await self._ai_suggest_splits(para)
                suggestions.append({
                    "type": "split",
                    "paragraph_index": idx,
                    "paragraph_text": para,
                    "word_count": word_count,
                    "split_positions": split_suggestions,
                    "reasoning": f"段落过长（{word_count}字），影响阅读体验"
                })

            # 过短段落
            elif word_count < self.min_paragraph_length:
                suggestions.append({
                    "type": "merge",
                    "paragraph_index": idx,
                    "paragraph_text": para,
                    "word_count": word_count,
                    "suggestion": "考虑与前后段合并",
                    "reasoning": f"段落过短（{word_count}字）"
                })

        return ParagraphAnalysis(
            total_paragraphs=len(paragraphs),
            suggestions=suggestions,
            issues_count=len(suggestions)
        )

    async def _ai_suggest_splits(self, paragraph: str) -> List[SplitSuggestion]:
        """AI建议分段位置"""
        prompt = f"""
        以下段落过长，请分析并建议在哪些位置分段（返回字符位置）：

        段落内容：
        {paragraph}

        要求：
        1. 识别自然的分段点（如话题转换、逻辑断点）
        2. 每段控制在100-150字左右
        3. 返回JSON格式：[{{"position": 120, "reason": "话题转换"}}, ...]
        """

        response = await self.ai.complete(prompt)
        split_positions = json.loads(response)

        return [SplitSuggestion(**sp) for sp in split_positions]

    def _split_paragraphs(self, content: str) -> List[str]:
        """分割段落"""
        # 按双换行符分割
        paragraphs = content.split("\n\n")
        # 去除空段落
        return [p.strip() for p in paragraphs if p.strip()]

    def _count_words(self, text: str) -> int:
        """统计字数（中文字符）"""
        return len([c for c in text if '\u4e00' <= c <= '\u9fff'])
```

### 6.4 Meta优化器 (MetaOptimizer)

```python
class MetaOptimizer:
    """Meta描述优化器"""

    def __init__(self, ai_client: AnthropicClient):
        self.ai = ai_client
        self.target_length = 155  # 字符
        self.length_range = (150, 160)

    async def optimize(
        self,
        original_meta: Optional[str],
        content: str,
        keywords: List[str]
    ) -> MetaOptimization:
        """优化Meta描述"""

        if original_meta:
            # 已有Meta，进行优化
            optimized = await self._optimize_existing(original_meta, content, keywords)
        else:
            # 无Meta，生成新的
            optimized = await self._generate_new(content, keywords)

        # 调整长度
        if len(optimized) > self.length_range[1]:
            optimized = self._trim_to_length(optimized, self.target_length)

        # 评分
        score = self._calculate_score(optimized, keywords, content)

        return MetaOptimization(
            original=original_meta,
            suggested=optimized,
            char_count=len(optimized),
            includes_keywords=self._check_keywords(optimized, keywords),
            score=score,
            reasoning=self._generate_reasoning(original_meta, optimized, score)
        )

    async def _generate_new(self, content: str, keywords: List[str]) -> str:
        """生成新Meta描述"""
        prompt = f"""
        你是SEO专家。请为以下文章生成Meta Description：

        文章正文（前500字）：
        {content[:500]}

        SEO关键词：
        {', '.join(keywords)}

        要求：
        1. 长度：150-160字符（中文约75-80字）
        2. 必须自然包含至少2个关键词
        3. 准确概括文章核心内容
        4. 语言吸引人，鼓励用户点击
        5. 避免堆砌关键词
        6. 使用第三人称或客观陈述

        只返回Meta Description文本，不要其他内容：
        """

        meta = await self.ai.complete(prompt)
        return meta.strip()

    async def _optimize_existing(
        self,
        original: str,
        content: str,
        keywords: List[str]
    ) -> str:
        """优化现有Meta描述"""
        issues = self._analyze_meta_issues(original, keywords)

        if not issues:
            return original  # 已经很好，不需要优化

        prompt = f"""
        请优化以下Meta Description：

        原始Meta：
        {original}

        文章正文（前500字）：
        {content[:500]}

        SEO关键词：
        {', '.join(keywords)}

        发现的问题：
        {chr(10).join(f"- {issue}" for issue in issues)}

        优化要求：
        1. 保持原意，但修正发现的问题
        2. 长度：150-160字符
        3. 自然包含关键词
        4. 提升吸引力和点击率

        只返回优化后的Meta Description：
        """

        optimized = await self.ai.complete(prompt)
        return optimized.strip()

    def _calculate_score(self, meta: str, keywords: List[str], content: str) -> float:
        """计算Meta质量评分（0-1）"""
        score = 0.0

        # 长度评分（30%）
        char_count = len(meta)
        if self.length_range[0] <= char_count <= self.length_range[1]:
            length_score = 1.0
        elif char_count < self.length_range[0]:
            length_score = char_count / self.length_range[0]
        else:
            length_score = self.length_range[1] / char_count
        score += length_score * 0.3

        # 关键词包含评分（40%）
        keywords_included = sum(1 for kw in keywords if kw in meta)
        keyword_score = min(keywords_included / max(len(keywords), 2), 1.0)
        score += keyword_score * 0.4

        # 内容相关性评分（30%）
        # 简单方法：检查Meta中的词是否在正文中
        meta_words = set(meta)
        content_words = set(content[:1000])
        overlap = len(meta_words & content_words)
        relevance_score = min(overlap / max(len(meta_words), 50), 1.0)
        score += relevance_score * 0.3

        return round(score, 2)
```

### 6.5 关键词优化器 (KeywordOptimizer)

```python
class KeywordOptimizer:
    """SEO关键词优化器"""

    def __init__(self, ai_client: AnthropicClient):
        self.ai = ai_client
        self.target_count = 5
        self.count_range = (3, 8)

    async def optimize(
        self,
        original_keywords: List[str],
        content: str,
        meta: str
    ) -> KeywordOptimization:
        """优化关键词列表"""

        if original_keywords:
            # 已有关键词，进行优化
            optimized = await self._optimize_existing(original_keywords, content, meta)
        else:
            # 无关键词，提取新的
            optimized = await self._extract_new(content, meta)

        # 排序并限制数量
        ranked = await self._rank_keywords(optimized, content)
        final = ranked[:self.count_range[1]]

        # 计算相关性得分
        relevance_scores = await self._calculate_relevance(final, content)

        return KeywordOptimization(
            original=original_keywords,
            suggested=final,
            keyword_count=len(final),
            relevance_scores=relevance_scores,
            avg_relevance=sum(relevance_scores.values()) / len(relevance_scores),
            reasoning=self._generate_reasoning(original_keywords, final)
        )

    async def _extract_new(self, content: str, meta: str) -> List[str]:
        """提取新关键词"""
        prompt = f"""
        你是SEO专家。请为以下文章提取SEO关键词：

        文章正文（前800字）：
        {content[:800]}

        Meta描述：
        {meta}

        要求：
        1. 提取5-8个关键词
        2. 每个关键词2-5个字
        3. 关键词必须在正文中出现
        4. 按SEO价值和相关性排序
        5. 考虑用户搜索意图
        6. 避免过于宽泛或竞争过大的词

        返回JSON数组格式：
        [
          {{"keyword": "关键词1", "relevance": 0.95, "reasoning": "核心主题"}},
          {{"keyword": "关键词2", "relevance": 0.88, "reasoning": "重要概念"}},
          ...
        ]
        """

        response = await self.ai.complete(prompt)
        keyword_data = json.loads(response)

        return [item["keyword"] for item in keyword_data]

    async def _rank_keywords(self, keywords: List[str], content: str) -> List[str]:
        """对关键词按重要性排序"""
        keyword_scores = {}

        for kw in keywords:
            score = 0.0

            # 出现频率（权重40%）
            frequency = content.count(kw)
            frequency_score = min(frequency / 5, 1.0)  # 5次及以上满分
            score += frequency_score * 0.4

            # 位置权重（权重30%）- 靠前的关键词更重要
            first_position = content.find(kw)
            if first_position >= 0:
                position_score = 1.0 - (first_position / len(content))
                score += position_score * 0.3

            # 长度适中性（权重30%）- 2-5字最佳
            length = len(kw)
            if 2 <= length <= 5:
                length_score = 1.0
            else:
                length_score = max(0, 1.0 - abs(length - 3.5) / 5)
            score += length_score * 0.3

            keyword_scores[kw] = score

        # 按得分排序
        return sorted(keywords, key=lambda k: keyword_scores[k], reverse=True)
```

### 6.6 FAQ Schema生成器 (FAQSchemaGenerator)

**（详见专项文档 `structured_data_faq_schema.md`）**

---

## 7. 数据库模型设计

### 7.1 Article表扩展字段

```sql
-- 在现有articles表基础上添加以下字段

-- ========================================
-- 原始版本字段 (Original Version)
-- ========================================

-- 正文
ALTER TABLE articles ADD COLUMN original_content TEXT;
ALTER TABLE articles ADD COLUMN original_content_word_count INTEGER DEFAULT 0;

-- Meta描述
ALTER TABLE articles ADD COLUMN original_meta_description TEXT;
ALTER TABLE articles ADD COLUMN original_meta_char_count INTEGER DEFAULT 0;

-- SEO关键词
ALTER TABLE articles ADD COLUMN original_seo_keywords JSONB DEFAULT '[]';
ALTER TABLE articles ADD COLUMN original_keyword_count INTEGER DEFAULT 0;

-- 元数据
ALTER TABLE articles ADD COLUMN original_received_at TIMESTAMP;
ALTER TABLE articles ADD COLUMN original_format_valid BOOLEAN DEFAULT TRUE;
ALTER TABLE articles ADD COLUMN original_parse_warnings JSONB DEFAULT '[]';

-- ========================================
-- 建议版本字段 (Suggested Version)
-- ========================================

-- 正文建议
ALTER TABLE articles ADD COLUMN suggested_content TEXT;
ALTER TABLE articles ADD COLUMN suggested_content_changes JSONB;

-- Meta描述建议
ALTER TABLE articles ADD COLUMN suggested_meta_description TEXT;
ALTER TABLE articles ADD COLUMN suggested_meta_reasoning TEXT;
ALTER TABLE articles ADD COLUMN suggested_meta_score DECIMAL(3,2);

-- SEO关键词建议
ALTER TABLE articles ADD COLUMN suggested_seo_keywords JSONB DEFAULT '[]';
ALTER TABLE articles ADD COLUMN suggested_keywords_reasoning TEXT;
ALTER TABLE articles ADD COLUMN suggested_keywords_score DECIMAL(3,2);

-- 段落建议
ALTER TABLE articles ADD COLUMN paragraph_suggestions JSONB DEFAULT '[]';
ALTER TABLE articles ADD COLUMN paragraph_split_suggestions JSONB DEFAULT '[]';

-- FAQ Schema建议
ALTER TABLE articles ADD COLUMN faq_schema_proposals JSONB DEFAULT '[]';

-- 校对问题
ALTER TABLE articles ADD COLUMN proofreading_issues JSONB DEFAULT '[]';
ALTER TABLE articles ADD COLUMN critical_issues_count INTEGER DEFAULT 0;

-- 生成元数据
ALTER TABLE articles ADD COLUMN suggested_generated_at TIMESTAMP;
ALTER TABLE articles ADD COLUMN ai_model_used VARCHAR(50);
ALTER TABLE articles ADD COLUMN generation_cost DECIMAL(10,4);

-- ========================================
-- 最终版本字段 (Final Version)
-- ========================================

-- 正文
ALTER TABLE articles ADD COLUMN final_content TEXT;
ALTER TABLE articles ADD COLUMN final_content_word_count INTEGER;

-- Meta描述
ALTER TABLE articles ADD COLUMN final_meta_description TEXT;
ALTER TABLE articles ADD COLUMN final_meta_char_count INTEGER;

-- SEO关键词
ALTER TABLE articles ADD COLUMN final_seo_keywords JSONB DEFAULT '[]';
ALTER TABLE articles ADD COLUMN final_keyword_count INTEGER;

-- FAQ Schema
ALTER TABLE articles ADD COLUMN final_faq_schema JSONB;

-- 用户选择记录
ALTER TABLE articles ADD COLUMN user_accepted_suggestions JSONB DEFAULT '[]';
ALTER TABLE articles ADD COLUMN user_rejected_suggestions JSONB DEFAULT '[]';
ALTER TABLE articles ADD COLUMN user_manual_edits JSONB DEFAULT '[]';

-- 确认元数据
ALTER TABLE articles ADD COLUMN final_confirmed_at TIMESTAMP;
ALTER TABLE articles ADD COLUMN final_confirmed_by INTEGER REFERENCES users(id);
ALTER TABLE articles ADD COLUMN final_version_number INTEGER DEFAULT 1;

-- ========================================
-- 状态管理字段
-- ========================================

ALTER TABLE articles ADD COLUMN proofreading_status VARCHAR(30) DEFAULT 'pending';
-- 可选值: pending, parsing, analyzing, suggested, user_reviewing,
--         user_editing, confirmed, publishing, published, failed

ALTER TABLE articles ADD COLUMN proofreading_started_at TIMESTAMP;
ALTER TABLE articles ADD COLUMN proofreading_completed_at TIMESTAMP;
ALTER TABLE articles ADD COLUMN proofreading_error TEXT;

-- 索引
CREATE INDEX idx_articles_proofreading_status ON articles(proofreading_status);
CREATE INDEX idx_articles_original_received ON articles(original_received_at);
CREATE INDEX idx_articles_final_confirmed ON articles(final_confirmed_at);
```

### 7.2 JSONB字段结构定义

#### original_parse_warnings

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

#### suggested_content_changes (Diff数据)

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

#### paragraph_suggestions

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

#### faq_schema_proposals

```json
[
  {
    "proposal_id": "faq_3q",
    "name": "简洁版（3个问答）",
    "item_count": 3,
    "items": [
      {
        "question": "这篇文章主要讲什么？",
        "answer": "文章主要介绍了..."
      },
      {
        "question": "有哪些关键发现？",
        "answer": "研究发现了三个关键点..."
      },
      {
        "question": "这对我们有什么影响？",
        "answer": "这意味着..."
      }
    ],
    "schema_json_ld": "{...}"  // 完整JSON-LD
  },
  {
    "proposal_id": "faq_5q",
    "name": "标准版（5个问答）",
    "item_count": 5,
    "items": [...]
  }
]
```

#### proofreading_issues

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

#### user_accepted_suggestions

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

#### user_manual_edits

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

---

## 8. API接口设计

### 8.1 文稿提交与解析

#### POST /api/articles/parse-and-create

**用途**: 提交原始文稿，解析并创建文章记录

**请求**:
```json
{
  "raw_text": "正文内容...\n\nMeta描述:\n这是描述\n\nSEO关键词:\n关键词1, 关键词2",
  "title": "文章标题（可选）",
  "author_id": 5,
  "category_id": 2
}
```

**响应**:
```json
{
  "success": true,
  "article_id": 123,
  "parsed_data": {
    "main_body": "正文内容...",
    "meta_description": "这是描述",
    "seo_keywords": ["关键词1", "关键词2"],
    "parse_warnings": [
      "警告：关键词数量偏少（2个），建议3-8个"
    ],
    "format_valid": true
  },
  "proofreading_status": "pending"
}
```

### 8.2 启动校对分析

#### POST /api/articles/{article_id}/start-proofreading

**用途**: 触发文章校对和优化分析

**请求**:
```json
{
  "options": {
    "analyze_paragraphs": true,
    "optimize_meta": true,
    "optimize_keywords": true,
    "generate_faq_schema": true,
    "faq_question_count": 5
  }
}
```

**响应**:
```json
{
  "success": true,
  "article_id": 123,
  "proofreading_status": "analyzing",
  "estimated_completion_seconds": 45,
  "task_id": "task_abc123"
}
```

### 8.3 获取分析结果

#### GET /api/articles/{article_id}/proofreading-result

**用途**: 获取校对和优化的完整结果（建议版本）

**响应**:
```json
{
  "success": true,
  "article_id": 123,
  "proofreading_status": "suggested",
  "original_version": {
    "content": "原始正文...",
    "meta_description": "原始Meta",
    "seo_keywords": ["关键词1", "关键词2"],
    "word_count": 1200
  },
  "suggested_version": {
    "content": "优化后正文...",
    "content_changes": {
      "total_changes": 15,
      "changes": [...]
    },
    "meta_description": "优化后的Meta描述...",
    "meta_reasoning": "基于正文核心内容和关键词优化",
    "meta_score": 0.92,
    "seo_keywords": ["关键词1", "关键词2", "新关键词3", "新关键词4"],
    "keywords_reasoning": "增加了2个高相关性关键词",
    "keywords_score": 0.88,
    "paragraph_suggestions": [...],
    "faq_schema_proposals": [...]
  },
  "proofreading_issues": {
    "total_issues": 23,
    "critical_count": 0,
    "error_count": 3,
    "warning_count": 15,
    "info_count": 5,
    "issues": [...]
  },
  "generated_at": "2025-10-26T10:25:30Z",
  "ai_model": "claude-3-5-sonnet",
  "generation_cost": 0.0245
}
```

### 8.4 用户确认最终版本

#### POST /api/articles/{article_id}/confirm-final-version

**用途**: 用户审核后确认最终版本

**请求**:
```json
{
  "content_choice": "suggested",  // "original" | "suggested" | "custom"
  "custom_content": null,  // 如果content_choice="custom"，提供自定义内容

  "meta_choice": "suggested",
  "custom_meta": null,

  "keywords_choice": "custom",
  "custom_keywords": ["关键词1", "关键词2", "关键词3", "新关键词"],

  "faq_schema_choice": "faq_5q",  // proposal_id 或 null（不使用）
  "faq_schema_modifications": {
    "items[2].answer": "用户修改的答案..."
  },

  "accepted_suggestions": ["change_001", "change_005", "change_008"],
  "rejected_suggestions": ["change_002", "change_011"],
  "manual_edits": [
    {
      "field": "content",
      "position": 450,
      "old_value": "原文",
      "new_value": "新文"
    }
  ],

  "confirmed_by": 5
}
```

**响应**:
```json
{
  "success": true,
  "article_id": 123,
  "proofreading_status": "confirmed",
  "final_version": {
    "content": "最终确定的正文...",
    "meta_description": "最终Meta",
    "seo_keywords": ["关键词1", "关键词2", "关键词3", "新关键词"],
    "faq_schema": {...},
    "word_count": 1205
  },
  "final_compliance_check": {
    "passed": true,
    "blocking_issues": []
  },
  "confirmed_at": "2025-10-26T10:40:00Z",
  "ready_to_publish": true
}
```

### 8.5 发布前最终检查

#### POST /api/articles/{article_id}/final-compliance-check

**用途**: 发布前F类规则最终验证（自动在确认时调用）

**响应**:
```json
{
  "success": true,
  "article_id": 123,
  "compliance_passed": true,
  "blocking_issues": [],
  "warnings": [
    {
      "rule_id": "F2-002",
      "message": "建议添加H2小标题以优化SEO"
    }
  ],
  "ready_to_publish": true
}
```

**失败响应（有阻止发布的问题）**:
```json
{
  "success": false,
  "article_id": 123,
  "compliance_passed": false,
  "blocking_issues": [
    {
      "rule_id": "F1-001",
      "severity": "critical",
      "message": "特色图片缺失",
      "blocks_publish": true,
      "required_action": "请上传特色图片后重新检查"
    }
  ],
  "ready_to_publish": false,
  "error": "存在阻止发布的关键问题"
}
```

### 8.6 发布文章

#### POST /api/articles/{article_id}/publish

**用途**: 发布最终版本到WordPress

**请求**:
```json
{
  "publish_immediately": true,
  "scheduled_time": null,
  "wordpress_options": {
    "status": "publish",
    "comment_status": "open",
    "ping_status": "closed"
  }
}
```

**响应**:
```json
{
  "success": true,
  "article_id": 123,
  "wordpress_post_id": 456,
  "wordpress_url": "https://example.com/article-title/",
  "published_at": "2025-10-26T10:45:00Z",
  "proofreading_status": "published"
}
```

---

## 9. 前端UI需求

### 9.1 文稿输入页面

**组件**: `ArticleInputForm.tsx`

**功能**:
- 大文本框输入原始文稿
- 实时提示三部分格式
- 预览解析结果
- 一键提交校对

**UI布局**:
```
┌────────────────────────────────────────────────────┐
│  文稿输入                                           │
├────────────────────────────────────────────────────┤
│  提示：请按以下格式输入文稿                          │
│  1. 正文内容                                        │
│  2. Meta描述：（可选）                              │
│  3. SEO关键词：（可选）                             │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │ 正文内容开始...                                │ │
│  │                                               │ │
│  │ 多个段落...                                    │ │
│  │                                               │ │
│  │ Meta描述:                                      │ │
│  │ 这是Meta描述内容                               │ │
│  │                                               │ │
│  │ SEO关键词:                                     │ │
│  │ 关键词1, 关键词2, 关键词3                      │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  字数统计: 1,200字  |  格式检测: ✓ 有效            │
│                                                    │
│  [预览解析结果]  [提交校对]                         │
└────────────────────────────────────────────────────┘
```

### 9.2 对比审核页面（核心UI）

**组件**: `ProofreadingReviewPage.tsx`

**功能**:
- 左右分屏对比（Original vs Suggested）
- Diff高亮显示修改
- 逐项接受/拒绝建议
- 手动编辑功能
- 确认最终版本

**UI布局**:
```
┌──────────────────────────────────────────────────────────────────┐
│  文章校对审核 - [文章标题]                                          │
├──────────────────────────────────────────────────────────────────┤
│  [校对问题总览]  关键: 0  错误: 3  警告: 15  信息: 5              │
├─────────────────────────────┬────────────────────────────────────┤
│  原始版本                    │  建议版本                           │
├─────────────────────────────┼────────────────────────────────────┤
│                             │                                    │
│  正文内容...                 │  正文内容...                        │
│                             │                                    │
│  这个问题很严重，            │  这个问题较为严重，  ◄─ [接受] [拒绝] │
│                             │  ^~~~~~~~~~~~~                     │
│                             │  (修改: A1-023 避免绝对化)          │
│                             │                                    │
│  专家表示...                 │  据专家分析，专家表示... ◄─ [接受]   │
│                             │  +++++++++                         │
│                             │  (添加: E2-015 说明信息来源)        │
│                             │                                    │
│  [段落过长建议]              │  [点击查看分段建议]                 │
│                             │                                    │
├─────────────────────────────┼────────────────────────────────────┤
│  Meta描述:                   │  Meta描述:  [✓ 接受建议] [✗ 保留原始] │
│  原始描述内容(85字)          │  优化后的描述内容，更简洁更吸引人... │
│  ⚠ 过短                     │  (155字) ✓ 长度合适  评分: 0.92    │
├─────────────────────────────┼────────────────────────────────────┤
│  SEO关键词:                  │  SEO关键词:  [✓ 接受] [编辑]       │
│  关键词1, 关键词2            │  关键词1, 关键词2, 新关键词3,       │
│  ⚠ 数量偏少                  │  新关键词4                          │
│                             │  相关性评分: 0.88                   │
├─────────────────────────────┴────────────────────────────────────┤
│  FAQ Schema 建议                                                  │
│  ○ 不使用FAQ Schema                                              │
│  ◉ 简洁版（3个问答）  ○ 标准版（5个问答）  ○ 详细版（7个问答）    │
│  [预览JSON-LD] [编辑Q&A]                                          │
├──────────────────────────────────────────────────────────────────┤
│  [全部接受建议]  [保留原始]  [手动编辑]  [确认最终版本]           │
└──────────────────────────────────────────────────────────────────┘
```

### 9.3 Diff高亮规则

**颜色方案**:
- 🟢 **绿色背景**: 添加的内容
- 🔴 **红色背景**: 删除的内容
- 🟡 **黄色背景**: 修改的内容
- 🔵 **蓝色边框**: 当前查看的修改
- 🟣 **紫色标记**: 与规则相关的修改（显示规则ID）

**交互**:
- 点击修改处显示详细说明
- Hover显示规则解释
- 右键菜单：接受/拒绝此修改

### 9.4 段落建议展示

**组件**: `ParagraphSuggestionModal.tsx`

**功能**:
- 显示过长段落
- 标记建议分段位置
- 一键应用分段
- 预览分段效果

**UI**:
```
┌─────────────────────────────────────────┐
│  段落优化建议                            │
├─────────────────────────────────────────┤
│  第3段落过长（285字），建议分段          │
│                                         │
│  原段落:                                 │
│  这是一个很长的段落内容...（前100字）     │
│  [这里可以分段] ◄─ 话题转换              │
│  继续的内容...（中间100字）              │
│  [这里可以分段] ◄─ 逻辑断点              │
│  最后的内容...（后85字）                 │
│                                         │
│  分段后效果预览:                         │
│  段落3-1: （142字）✓                    │
│  段落3-2: （96字）✓                     │
│  段落3-3: （47字）⚠ 偏短                │
│                                         │
│  [应用此建议]  [取消]                    │
└─────────────────────────────────────────┘
```

### 9.5 FAQ Schema编辑器

**组件**: `FAQSchemaEditor.tsx`

**功能**:
- 选择方案（3/5/7问答）
- 编辑Q&A内容
- 添加/删除问答
- 预览JSON-LD代码

**UI**:
```
┌──────────────────────────────────────────────────┐
│  FAQ Schema 编辑器                                │
├──────────────────────────────────────────────────┤
│  选择方案: ◉ 标准版（5个问答）                     │
│                                                  │
│  问答列表:                                        │
│  ┌────────────────────────────────────────────┐ │
│  │ Q1: 这篇文章主要讲什么？              [编辑] │ │
│  │ A:  文章主要介绍了...                      │ │
│  │ ───────────────────────────────────────   │ │
│  │ Q2: 有哪些关键发现？                  [编辑] │ │
│  │ A:  研究发现了...                          │ │
│  │ [+ 添加问答]                              │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  JSON-LD 预览:                                   │
│  ┌────────────────────────────────────────────┐ │
│  │ {                                          │ │
│  │   "@context": "https://schema.org",       │ │
│  │   "@type": "FAQPage",                     │ │
│  │   "mainEntity": [...]                     │ │
│  │ }                                          │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  [复制JSON-LD]  [保存]  [取消]                   │
└──────────────────────────────────────────────────┘
```

### 9.6 最终确认页面

**组件**: `FinalConfirmationPage.tsx`

**功能**:
- 显示最终版本全貌
- 再次检查F类规则合规性
- 确认并发布

**UI**:
```
┌──────────────────────────────────────────────────┐
│  最终版本确认                                      │
├──────────────────────────────────────────────────┤
│  ✓ 校对检查完成（0关键问题，3错误已修正）           │
│  ✓ Meta描述已优化（155字符）                       │
│  ✓ SEO关键词已优化（4个关键词）                    │
│  ✓ FAQ Schema已生成                              │
│  ✓ F类合规性检查通过                              │
│                                                  │
│  最终版本预览:                                     │
│  ┌────────────────────────────────────────────┐ │
│  │ 正文: [展开查看全文]                        │ │
│  │                                            │ │
│  │ Meta: 最终确定的Meta描述内容...             │ │
│  │                                            │ │
│  │ 关键词: 关键词1, 关键词2, 关键词3, 关键词4  │ │
│  │                                            │ │
│  │ FAQ Schema: 5个问答  [预览JSON-LD]         │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  ⚠ 确认后将立即发布到WordPress，是否继续？        │
│                                                  │
│  [返回修改]  [确认并发布]                          │
└──────────────────────────────────────────────────┘
```

---

## 10. AI服务集成

> **重要**: v2.0 采用**单一 Prompt 综合分析架构**，所有AI任务通过一次调用完成。
> 详细设计请参考: `single_prompt_design.md`

### 10.1 使用的AI模型

| 服务 | 模型 | 调用方式 (v2.0) |
|------|------|----------------|
| **综合分析服务** | Claude 3.5 Sonnet | **单一 Prompt 调用**，一次性完成所有任务 |
| - 校对检测 (A-F类规则) | ↑ 同上 | 集成在综合Prompt中 |
| - 内容优化建议 | ↑ 同上 | 集成在综合Prompt中 |
| - Meta描述优化 | ↑ 同上 | 集成在综合Prompt中 |
| - SEO关键词提取 | ↑ 同上 | 集成在综合Prompt中 |
| - FAQ Schema生成 | ↑ 同上 | 集成在综合Prompt中 (3/5/7版本) |
| - 发布合规性检查 | ↑ 同上 | 集成在综合Prompt中 |

**v2.0 架构优势:**
- ✅ **Token节省**: 34% (文章内容只发送一次)
- ✅ **速度提升**: 58% (从~6秒降到~2.5秒)
- ✅ **术语一致性**: 所有内容在同一上下文生成，自动保持一致
- ✅ **代码简化**: 单一服务类 `ProofreadingAnalysisService`

### 10.2 核心服务实现

```python
# backend/app/services/article_analysis.py

from typing import Dict, Any
from anthropic import Anthropic
from app.core.config import settings
import json
import time

class ProofreadingAnalysisService:
    """
    v2.0 单一 Prompt 文章综合分析服务

    一次性完成：
    - A-F类 450条校对规则检查
    - Meta描述优化
    - SEO关键词提取/优化
    - FAQ Schema生成 (3/5/7版本)
    - 发布合规性检查
    """

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-5-20250929"

    async def analyze_article(
        self,
        article_content: str,
        article_id: int
    ) -> Dict[str, Any]:
        """
        使用单一 Prompt 完成所有分析

        Args:
            article_content: 文章内容（三部分格式）
            article_id: 文章ID

        Returns:
            完整的分析结果JSON，包含：
            - parsed_content: 解析后的三部分内容
            - proofreading_results: 校对结果和问题列表
            - optimized_meta: Meta描述优化建议
            - optimized_keywords: 关键词优化建议
            - faq_schema: 3个版本的FAQ Schema
            - compliance_check: 发布合规性检查结果
            - processing_metadata: 处理元数据
        """

        # 1. 构建综合 Prompt（详见 single_prompt_design.md）
        full_prompt = self._build_comprehensive_prompt(article_content)

        # 2. 单次 AI 调用
        start_time = time.time()

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,  # 足够容纳完整JSON输出
            temperature=0.3,  # 较低温度确保稳定性
            messages=[
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]
        )

        processing_time = int((time.time() - start_time) * 1000)

        # 3. 解析 AI 响应的 JSON
        response_text = response.content[0].text

        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # 容错：提取JSON代码块
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response_text[json_start:json_end])
            else:
                raise ValueError("AI响应不包含有效的JSON")

        # 4. 添加处理元数据
        result['processing_metadata'] = {
            'model': self.model,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'processing_time_ms': processing_time,
            'total_tokens': {
                'input': response.usage.input_tokens,
                'output': response.usage.output_tokens,
                'total': response.usage.input_tokens + response.usage.output_tokens
            },
            'article_id': article_id
        }

        return result

    def _build_comprehensive_prompt(self, article_content: str) -> str:
        """
        构建综合分析 Prompt

        完整的 Prompt 模板请参考:
        - single_prompt_design.md (详细设计)
        - prompts/comprehensive_analysis_v1.md (Prompt模板文件)
        """

        # 加载系统 Prompt 模板
        system_prompt = self._load_system_prompt()

        # 拼接用户内容
        user_prompt = f"""
# 待分析文稿

```
{article_content}
```

请按照系统指示完成全面分析，输出完整的JSON结果。
确保所有内容（正文、Meta、关键词、FAQ）的术语保持一致。
"""

        return f"{system_prompt}\n\n{user_prompt}"

    def _load_system_prompt(self) -> str:
        """
        加载系统 Prompt 模板

        实际项目中建议从文件读取，便于版本控制和维护
        """
        # 从配置文件或数据库加载
        # with open('prompts/comprehensive_analysis_v1.md', 'r') as f:
        #     return f.read()

        # 或直接返回 Prompt 内容
        return """
[单一综合Prompt的完整内容，参见 single_prompt_design.md]
包含：
- 角色定义
- 450条校对规则
- Meta优化要求
- 关键词提取要求
- FAQ生成要求
- JSON输出格式定义
"""
```

### 10.3 Prompt设计原则 (v2.0)

**v2.0 综合Prompt的核心原则:**

1. **单一上下文**: 所有任务在同一个Prompt中定义，确保AI在统一上下文中理解
2. **结构化输出**: 严格定义JSON Schema，确保输出可解析
3. **术语一致性**: 明确要求保持术语一致（如"纽约市"不混用"纽约"或"NYC"）
4. **优先级明确**: 校对规则 > 内容优化 > SEO优化 > FAQ生成
5. **置信度评分**: 每个建议都要求AI提供置信度（0.0-1.0）
6. **完整性检查**: Prompt中包含所有450条规则的简要说明

**详细的Prompt设计文档:**
- 📄 `single_prompt_design.md` - 完整的Prompt模板和JSON Schema
- 📄 `prompts/comprehensive_analysis_v1.md` - 可执行的Prompt文件

### 10.4 成本控制与优化 (v2.0)

**v2.0 单一Prompt架构的成本优势:**

| 指标 | 旧方案 (v1.0) | 新方案 (v2.0) | 节省 |
|------|--------------|--------------|------|
| AI调用次数 | 4次 | 1次 | 75% |
| Token使用 (500字文章) | ~9,550 tokens | ~6,300 tokens | 34% |
| 成本/篇 | $0.0605 | $0.0525 | 13% |
| 处理时间 | ~6秒 | ~2.5秒 | 58% |

**月度成本估算:**

| 每日文章量 | 旧方案月成本 | 新方案月成本 | 每月节省 |
|-----------|------------|-------------|---------|
| 10篇 | $18.15 | $15.75 | $2.40 (13%) |
| 50篇 | $90.75 | $78.75 | $12.00 (13%) |
| 100篇 | $181.50 | $157.50 | $24.00 (13%) |
| 500篇 | $907.50 | $787.50 | $120.00 (13%) |

```python
class AIUsageTracker:
    """
    v2.0 AI使用跟踪和成本控制

    针对单一Prompt架构优化
    """

    async def estimate_cost_v2(self, article_length: int) -> Decimal:
        """
        估算处理成本 (v2.0 单一Prompt)

        v2.0 只调用一次，token使用更少
        """
        # 基于文章长度估算token数
        article_tokens = article_length * 1.5  # 中文约1.5倍

        # v2.0: 文章内容只发送一次 + 综合Prompt
        prompt_tokens = 1500  # 综合Prompt约1500 tokens (包含450条规则简要说明)
        input_tokens = article_tokens + prompt_tokens

        # 输出: 完整JSON结果 (校对+Meta+关键词+FAQ)
        output_tokens = article_tokens * 0.8  # 输出约80%

        # Claude 3.5 Sonnet价格
        input_cost = Decimal("0.003") / 1000  # $0.003 per 1K tokens
        output_cost = Decimal("0.015") / 1000  # $0.015 per 1K tokens

        total_cost = (
            input_tokens * input_cost +
            output_tokens * output_cost
        )

        return total_cost

    async def estimate_cost_v1_comparison(self, article_length: int) -> Dict:
        """
        对比 v1.0 和 v2.0 的成本
        """
        article_tokens = article_length * 1.5

        # v1.0: 多次调用
        v1_input = article_tokens * 4 + 800  # 文章发送4次 + 各自的Prompt
        v1_output = article_tokens * 0.3 * 4
        v1_cost = (v1_input * Decimal("0.003") + v1_output * Decimal("0.015")) / 1000

        # v2.0: 单次调用
        v2_cost = await self.estimate_cost_v2(article_length)

        return {
            'v1_cost': float(v1_cost),
            'v2_cost': float(v2_cost),
            'savings': float(v1_cost - v2_cost),
            'savings_percent': float((v1_cost - v2_cost) / v1_cost * 100)
        }

    async def check_budget(self, user_id: int, estimated_cost: Decimal) -> bool:
        """检查用户预算"""
        user_budget = await get_user_monthly_budget(user_id)
        user_usage = await get_user_monthly_usage(user_id)

        if user_usage + estimated_cost > user_budget:
            raise BudgetExceededException(
                f"预算不足：已使用${user_usage}，预算${user_budget}"
            )

        return True
```

---

## 11. 实现优先级与里程碑

### 11.1 优先级分级

| 优先级 | 功能模块 | 关键性 | 实现顺序 |
|--------|---------|--------|---------|
| **P0** | 文稿解析器 | 核心基础 | 第1周 |
| **P0** | 原始版本保存 | 核心基础 | 第1周 |
| **P0** | A-F类校对引擎 | 核心功能 | 第2-3周 |
| **P0** | 建议版本生成 | 核心功能 | 第3周 |
| **P0** | 对比UI（基础版） | 核心功能 | 第4周 |
| **P0** | 最终版本确认 | 核心功能 | 第4周 |
| **P0** | F类合规检查 | 强制要求 | 第4周 |
| **P1** | 段落分析器 | 重要优化 | 第5周 |
| **P1** | Meta优化器 | 重要优化 | 第5周 |
| **P1** | 关键词优化器 | 重要优化 | 第5周 |
| **P1** | 对比UI（完整版） | 用户体验 | 第6周 |
| **P2** | FAQ Schema生成 | 增值功能 | 第7周 |
| **P2** | FAQ Schema编辑器 | 增值功能 | 第7周 |
| **P2** | 批量处理 | 效率提升 | 第8周 |
| **P3** | 用户偏好学习 | 长期优化 | 未来版本 |
| **P3** | 协作审核 | 团队功能 | 未来版本 |

### 11.2 实现里程碑

#### 里程碑1: 基础校对流程（第1-4周）

**目标**: 实现原稿→校对→建议→确认→发布的基础流程

**交付物**:
- ✅ 文稿解析API
- ✅ A-F类校对引擎
- ✅ 基础对比UI
- ✅ 三版本数据库模型
- ✅ F类合规检查

**验收标准**:
- 可解析三部分文稿
- 可检测A-F类规则问题
- 用户可查看对比并确认
- F类关键问题阻止发布

#### 里程碑2: AI优化功能（第5-6周）

**目标**: 集成AI驱动的内容优化

**交付物**:
- ✅ 段落分析和分段建议
- ✅ Meta描述优化
- ✅ SEO关键词优化
- ✅ 完整对比UI（含Diff高亮）

**验收标准**:
- AI可检测过长段落并建议分段
- AI可生成高质量Meta（评分>0.8）
- AI可提取相关关键词（相关性>0.85）
- UI可清晰显示所有修改

#### 里程碑3: 结构化数据（第7周）

**目标**: 集成FAQ Schema生成

**交付物**:
- ✅ FAQ Schema生成器
- ✅ 多方案生成（3/5/7问答）
- ✅ FAQ编辑器UI
- ✅ JSON-LD代码生成

**验收标准**:
- 可生成Schema.org标准FAQ
- 用户可编辑Q&A内容
- JSON-LD代码可直接用于WordPress

#### 里程碑4: 生产就绪（第8周）

**目标**: 完善功能，准备上线

**交付物**:
- ✅ 批量处理API
- ✅ 错误处理和重试机制
- ✅ 性能优化
- ✅ 完整测试覆盖
- ✅ 用户文档

**验收标准**:
- 单篇处理时间<60秒
- API可靠性>99%
- 测试覆盖率>80%
- 用户文档完整

---

## 12. 测试与验证

### 12.1 单元测试

#### 文稿解析测试
```python
def test_parse_full_article():
    """测试完整三部分文稿解析"""
    raw_text = """
    正文内容第一段。

    正文内容第二段。

    Meta描述:
    这是Meta描述内容，约150字符。

    SEO关键词:
    关键词1, 关键词2, 关键词3
    """

    result = ArticleParser().parse(raw_text)

    assert result.main_body.startswith("正文内容第一段")
    assert result.meta_description == "这是Meta描述内容，约150字符。"
    assert result.seo_keywords == ["关键词1", "关键词2", "关键词3"]
    assert result.format_valid == True

def test_parse_incomplete_article():
    """测试不完整文稿（仅正文）"""
    raw_text = "只有正文内容，没有Meta和关键词。"

    result = ArticleParser().parse(raw_text)

    assert result.main_body == "只有正文内容，没有Meta和关键词。"
    assert result.meta_description is None
    assert result.seo_keywords == []
    assert len(result.parse_warnings) > 0

def test_parse_wrong_order():
    """测试标记顺序错误"""
    raw_text = """
    正文内容。

    SEO关键词:
    关键词1, 关键词2

    Meta描述:
    这是描述
    """

    result = ArticleParser().parse(raw_text)

    # 应正确识别，但记录警告
    assert result.meta_description == "这是描述"
    assert result.seo_keywords == ["关键词1", "关键词2"]
    assert any("顺序" in w for w in result.parse_warnings)
```

#### 校对引擎测试
```python
@pytest.mark.asyncio
async def test_proofread_punctuation():
    """测试B类标点符号规则"""
    content = '他说"这很重要"。'  # 错误：使用了半角引号

    engine = ProofreadingEngine(rule_repository)
    result = await engine.proofread_content(content)

    # 应检测到B2-005规则违反
    assert any(issue.rule_id == "B2-005" for issue in result.issues)
    assert result.error_count >= 1

@pytest.mark.asyncio
async def test_proofread_meta_length():
    """测试Meta描述长度检查"""
    short_meta = "过短的Meta"  # <100字符

    engine = ProofreadingEngine(rule_repository)
    result = await engine.proofread_meta(short_meta)

    # 应有长度警告
    assert any("过短" in issue.message for issue in result.issues)
    assert result.char_count < 100
```

### 12.2 集成测试

#### 完整工作流测试
```python
@pytest.mark.asyncio
async def test_full_proofreading_workflow():
    """测试完整校对工作流"""
    # 1. 创建文章
    article_data = {
        "raw_text": TEST_ARTICLE_FULL,
        "title": "测试文章",
        "author_id": 1
    }

    response = await client.post("/api/articles/parse-and-create", json=article_data)
    assert response.status_code == 200
    article_id = response.json()["article_id"]

    # 2. 启动校对
    response = await client.post(
        f"/api/articles/{article_id}/start-proofreading",
        json={"options": {"analyze_paragraphs": True, "optimize_meta": True}}
    )
    assert response.status_code == 200

    # 3. 等待完成
    await wait_for_status(article_id, "suggested", timeout=60)

    # 4. 获取结果
    response = await client.get(f"/api/articles/{article_id}/proofreading-result")
    assert response.status_code == 200
    result = response.json()

    assert result["proofreading_status"] == "suggested"
    assert "suggested_version" in result
    assert len(result["proofreading_issues"]["issues"]) >= 0

    # 5. 确认最终版本
    confirm_data = {
        "content_choice": "suggested",
        "meta_choice": "suggested",
        "keywords_choice": "suggested",
        "confirmed_by": 1
    }

    response = await client.post(
        f"/api/articles/{article_id}/confirm-final-version",
        json=confirm_data
    )
    assert response.status_code == 200
    assert response.json()["ready_to_publish"] == True
```

### 12.3 性能测试

```python
@pytest.mark.performance
async def test_proofreading_performance():
    """测试校对性能"""
    article_lengths = [500, 1000, 2000, 5000]  # 字数

    for length in article_lengths:
        content = generate_test_article(length)

        start_time = time.time()
        result = await proofread_article(content)
        duration = time.time() - start_time

        # 性能要求：每1000字<10秒
        max_duration = (length / 1000) * 10
        assert duration < max_duration, \
            f"校对{length}字文章耗时{duration}秒，超过限制{max_duration}秒"
```

### 12.4 验收测试清单

#### 功能验收

- [ ] **文稿解析**
  - [ ] 可正确解析完整三部分文稿
  - [ ] 可处理不完整文稿（缺Meta或关键词）
  - [ ] 可检测格式异常并给出警告
  - [ ] 可处理标记顺序错误

- [ ] **校对检测**
  - [ ] A类规则检测准确率>90%
  - [ ] B类规则检测准确率>95%
  - [ ] C类规则检测准确率>90%
  - [ ] D类规则检测准确率>85%
  - [ ] E类规则检测准确率>90%
  - [ ] F类规则检测准确率100%

- [ ] **AI优化**
  - [ ] 段落分析可检测过长/过短段落
  - [ ] Meta优化评分平均>0.8
  - [ ] 关键词相关性平均>0.85
  - [ ] FAQ Schema生成质量合格

- [ ] **版本管理**
  - [ ] 原始版本保存完整
  - [ ] 建议版本生成正确
  - [ ] 最终版本反映用户选择
  - [ ] 版本间可对比查看

- [ ] **UI/UX**
  - [ ] 对比界面清晰易懂
  - [ ] Diff高亮准确显示
  - [ ] 逐项接受/拒绝功能正常
  - [ ] 手动编辑功能可用

- [ ] **合规检查**
  - [ ] F类关键问题阻止发布
  - [ ] 非关键问题仅警告
  - [ ] 发布前最终检查有效

#### 性能验收

- [ ] 单篇文章（1000字）处理时间<60秒
- [ ] API响应时间<2秒
- [ ] 并发处理能力>10篇/分钟
- [ ] 系统稳定性>99%

#### 安全验收

- [ ] 用户数据隔离
- [ ] API权限验证
- [ ] 敏感信息脱敏
- [ ] SQL注入防护

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| **原始版本 (Original)** | 用户输入的原始文稿，不可修改 |
| **建议版本 (Suggested)** | AI分析后生成的优化建议版本 |
| **最终版本 (Final)** | 用户确认的发布版本 |
| **A-F类规则** | 《大纪元写作风格指南》中的校对规则分类 |
| **Meta描述** | 搜索引擎结果页显示的文章摘要 |
| **FAQ Schema** | Schema.org定义的常见问题结构化数据 |
| **Diff** | 文本差异对比 |
| **F类规则** | 发布合规类规则，包含阻止发布的关键检查 |

### B. 相关文档

- `proofreading_requirements.md` - A-F类校对规则详细说明
- `structured_data_faq_schema.md` - FAQ Schema生成专项文档
- `database_schema_updates.md` - 数据库模型变更说明
- `api_reference.md` - 完整API参考文档
- `ui_design_specs.md` - UI设计规范和组件文档

### C. 示例文稿

#### 示例1：完整格式文稿
```
纽约市政府宣布新政策，将从下月起实施新的交通管理措施。

据市长办公室发布的声明，新政策旨在缓解市中心交通拥堵问题。主要措施包括：增加公交车道、限制私家车进入特定区域、提高停车费用等。

交通专家表示，这些措施预计将使通勤时间减少15%，同时降低空气污染。但也有批评者担心，限制措施可能影响商业活动。

Meta描述:
纽约市政府宣布新交通管理政策，旨在缓解市中心拥堵。措施包括增加公交车道、限制私家车进入等，预计可减少15%通勤时间。

SEO关键词:
纽约交通, 交通管理政策, 市中心拥堵, 公交车道, 通勤时间
```

#### 示例2：不完整格式（仅正文）
```
最新研究发现，每天步行30分钟可显著降低心血管疾病风险。

哈佛大学的研究团队对5000名参与者进行了为期10年的跟踪调查。结果显示，坚持每天步行的人群，心脏病发作风险降低了40%。

专家建议，即使是轻度运动也能带来健康益处。步行、慢跑、骑自行车等都是不错的选择。
```
*（系统将自动生成Meta和关键词建议）*

---

**文档版本**: 1.0.0
**最后更新**: 2025-10-26
**维护者**: CMS自动化系统团队
**审核状态**: 待审核

---

## 结语

本文档定义了CMS自动化系统中**文章上稿前完整处理流程**的详细需求。该流程是确保内容质量、SEO效果和发布合规的关键环节。

**核心价值**:
1. **自动化**: AI驱动，减少人工工作量
2. **标准化**: 统一的校对规则和流程
3. **可追溯**: 完整记录原始→建议→最终三个版本
4. **灵活性**: 用户保持最终控制权
5. **合规性**: F类规则强制保障

**下一步**:
- 审核并批准本需求文档
- 进入技术设计和原型开发阶段
- 按里程碑逐步实现功能模块
