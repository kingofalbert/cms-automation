# Phase 7: 统一AI优化服务设计

**文档版本**: v2.0
**创建日期**: 2025-11-08
**最后更新**: 2025-12-07
**状态**: 已實施
**优先级**: P0 (Critical - 成本优化)

---

## ⚠️ 重要架構更新 (v2.0)

**解析 Prompt 已移除校對功能**

原設計中，解析 Prompt 包含了「Comprehensive Proofreading」任務。現已移除，原因：

1. **校對有獨立的專門服務**：`ProofreadingAnalysisService` 使用 405 條規則進行專業校對
2. **避免重複**：解析時的簡單校對遠不如專門校對服務完整
3. **節省 Token**：移除冗餘的校對任務，減少解析 Prompt 長度

**當前解析 Prompt 任務：**
- Task 1: 解析文章結構
- Task 2: 生成 SEO 優化
- Task 2.5: 分類（主分類 + 副分類）
- Task 3: 生成 FAQ（原 Task 4）

**校對流程**：由獨立的 `ProofreadingAnalysisService` 處理

---

## 🎯 设计目标

### 用户需求

> "所有三个step需要的AI建议的内容都在一个AI Prompt过程完成以节约Token。"

### 优化策略

**原设计**（两次AI调用）:
```
Step 1: 调用AI生成标题优化建议 → 成本 $0.02-0.03
Step 3: 调用AI生成SEO+FAQ → 成本 $0.08-0.10
──────────────────────────────────────────
总成本: $0.10-0.13/篇
总耗时: 30-40秒（两次调用）
```

**优化设计**（一次AI调用）:
```
Step 1: 调用AI生成【标题+SEO+FAQ】全部内容 → 成本 $0.06-0.08
Step 3: 直接使用Step 1生成的结果 → 成本 $0
──────────────────────────────────────────
总成本: $0.06-0.08/篇 ✅ 节省 40-60%
总耗时: 20-30秒（一次调用）✅ 节省 30-40%
```

---

## 🔄 调整后的工作流

### 完整流程（最终版）

```
┌────────────────────────────────────────────────────────────┐
│ Step 1: 解析确认 + AI综合优化（一次性生成所有建议）        │
├────────────────────────────────────────────────────────────┤
│ 1. 解析结构化数据                                           │
│    ├─ 标题组件（title_prefix/main/suffix）                 │
│    ├─ 作者（author_line/name）                             │
│    ├─ 图片（images + specs）                               │
│    └─ 初步SEO（meta_description/keywords/tags - 从文档）   │
│                                                            │
│ 2. ⭐ 调用"统一AI优化服务"（一次Prompt）                   │
│    生成以下全部内容：                                       │
│    ├─ 📝 标题优化建议（3段式，2-3个选项）                  │
│    ├─ 🔑 SEO关键词（focus/primary/secondary）              │
│    ├─ 📄 Meta Description优化                              │
│    ├─ 🏷️ Tags推荐扩展                                       │
│    └─ ❓ FAQ生成（8-10个问答对）                            │
│                                                            │
│ 3. 存储AI生成结果                                           │
│    ├─ title_suggestions 表（标题建议）                     │
│    ├─ seo_suggestions 表（SEO建议）                        │
│    └─ article_faqs 表（FAQ）                               │
│                                                            │
│ 4. UI显示 + 用户确认                                        │
│    ├─ 显示标题优化建议 ⭐ Step 1关注点                     │
│    └─ 用户选择标题并确认                                   │
│                                                            │
│ 输出: parsing_confirmed = true, title确认                  │
└────────────────────────────────────────────────────────────┘
                         ▼
┌────────────────────────────────────────────────────────────┐
│ Step 2: 正文校对                                            │
├────────────────────────────────────────────────────────────┤
│ • 仅校对body_html                                           │
│ • 不涉及AI优化（已在Step 1完成）                            │
│                                                            │
│ 输出: proofreading_confirmed = true                        │
└────────────────────────────────────────────────────────────┘
                         ▼
┌────────────────────────────────────────────────────────────┐
│ Step 3: SEO确认 + FAQ确认（使用Step 1生成的结果）          │
├────────────────────────────────────────────────────────────┤
│ 1. 从数据库加载已生成的建议                                 │
│    ├─ seo_suggestions 表                                   │
│    └─ article_faqs 表                                      │
│                                                            │
│ 2. UI显示 + 用户确认                                        │
│    ├─ 显示SEO关键词建议 ⭐ Step 3关注点                    │
│    ├─ 显示Meta Description优化                             │
│    ├─ 显示Tags推荐                                          │
│    └─ 显示FAQ（8-10个）                                     │
│                                                            │
│ 3. 用户操作                                                 │
│    ├─ 接受/拒绝/修改SEO建议                                 │
│    ├─ 接受/拒绝/修改Tags                                    │
│    └─ 接受/拒绝/编辑/删除FAQ                                │
│                                                            │
│ ⚠️ 注意: 不调用AI，仅使用Step 1生成的缓存结果              │
│                                                            │
│ 输出: seo_metadata_confirmed = true                        │
└────────────────────────────────────────────────────────────┘
                         ▼
┌────────────────────────────────────────────────────────────┐
│ Step 4: 发布到WordPress                                     │
└────────────────────────────────────────────────────────────┘
```

---

## 🤖 统一AI优化服务设计

### 服务接口

**文件**: `backend/src/services/parsing/unified_optimization_service.py`

```python
from anthropic import AsyncAnthropic
from typing import Dict, List, Any

class UnifiedOptimizationService:
    """
    统一AI优化服务

    在Step 1解析完成后，一次性生成：
    1. 标题优化建议（3段式，2-3个选项）
    2. SEO关键词（focus/primary/secondary）
    3. Meta Description优化
    4. Tags推荐
    5. FAQ生成（8-10个）

    优势：节省Token成本40-60%，减少API调用次数
    """

    def __init__(self, anthropic_client: AsyncAnthropic):
        self.client = anthropic_client
        self.model = "claude-sonnet-4.5-20250929"

    async def generate_all_optimizations(
        self,
        article: Article
    ) -> Dict[str, Any]:
        """
        一次性生成所有优化建议

        Args:
            article: 文章对象（包含解析后的结构化数据）

        Returns:
            {
                "title_suggestions": {...},    # 标题优化建议
                "seo_suggestions": {...},      # SEO建议
                "faqs": [...]                  # FAQ列表
            }
        """

        prompt = self._build_unified_prompt(article)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=6000,  # 增加token限制，因为要生成更多内容
            temperature=0.35,  # 适度创意
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # 解析AI响应
        result = self._parse_unified_response(response.content[0].text)

        # 分别存储到对应的表
        await self._store_optimizations(article.id, result)

        return result

    def _build_unified_prompt(self, article: Article) -> str:
        """
        构建统一优化Prompt

        包含5个子任务：
        1. 标题优化
        2. SEO关键词
        3. Meta Description
        4. Tags推荐
        5. FAQ生成
        """

        return f"""
你是一位资深的SEO专家、内容营销顾问和文案优化师。请为以下文章提供**全面的优化建议**。

## 📋 文章信息

### 结构化数据（已解析）

**标题组件**:
- 前缀: {article.title_prefix or "（无）"}
- 主标题: {article.title_main}
- 副标题: {article.title_suffix or "（无）"}
- 完整标题: {self._build_full_title(article)}

**作者**:
- 作者行: {article.author_line or "（无）"}
- 作者名: {article.author_name or "（无）"}

**初步SEO数据**（从文档提取）:
- Meta Description: {article.meta_description or "（无）"}
- 关键词: {", ".join(article.seo_keywords[:10]) if article.seo_keywords else "（无）"}
- 标签: {", ".join(article.tags[:5]) if article.tags else "（无）"}

**正文内容**（前800字符）:
{article.body_html[:800] if article.body_html else article.body[:800]}...

---

## 🎯 优化任务

请一次性完成以下**5个优化任务**：

---

### 任务1: 标题优化（3段式）📝

为三段式标题结构生成**2-3个**优化建议：

```
完整标题 = [前缀] | 主标题 | [副标题]
```

**要求**:
1. 生成2-3个不同风格的标题方案
2. 必须包含至少1个**Data-Driven型**（包含具体数据、百分比）
3. 推荐包含1个**Authority-Backed型**（权威背书）或**How-To型**（操作指南）
4. 可选1个**Comprehensive Guide型**（全面指南）或**Question-Based型**（疑问引导）

**长度规范**:
- 前缀: 2-6字符（简短有力）
- 主标题: 15-30字符（核心内容）
- 副标题: 4-12字符（补充信息）
- 完整标题: 25-50字符（推荐），不超过70字符

**输出格式**:
```json
"title_suggestions": {{
  "suggested_title_sets": [
    {{
      "id": "option_1",
      "title_prefix": "深度解析",
      "title_main": "人工智能革新医疗诊断：准确率提升30%",
      "title_suffix": "权威指南",
      "full_title": "深度解析 | 人工智能革新医疗诊断：准确率提升30% | 权威指南",
      "score": 95,
      "strengths": ["...", "..."],
      "type": "data_driven",
      "recommendation": "...",
      "character_count": {{"prefix": 4, "main": 22, "suffix": 4, "total": 34}}
    }},
    // ... 1-2个更多选项
  ],
  "optimization_notes": ["...", "..."]
}}
```

---

### 任务2: SEO关键词分析🔑

深度分析文章内容，生成三级关键词体系：

**要求**:
1. **Focus Keyword**（主关键词）: 1个，搜索量高、竞争适中、与内容高度相关
2. **Primary Keywords**（主要关键词）: 3-5个，语义相关
3. **Secondary Keywords**（次要关键词）: 5-10个，长尾词

**输出格式**:
```json
"seo_keywords": {{
  "focus_keyword": "人工智能医疗应用",
  "focus_keyword_rationale": "该词搜索量高、竞争中等，与文章核心内容匹配",
  "primary_keywords": ["AI诊断", "医疗影像分析", "智能辅助诊断"],
  "secondary_keywords": ["深度学习医疗", "计算机视觉医学应用", "AI早期筛查", ...],
  "keyword_difficulty": {{"focus_keyword": 0.65, "average_difficulty": 0.52}},
  "search_volume_estimate": {{"focus_keyword": "5000-10000/月", "primary_keywords_total": "15000-25000/月"}}
}}
```

---

### 任务3: Meta Description优化📄

基于文章内容生成吸引点击的Meta Description：

**要求**:
1. 长度: 150-160字符
2. 包含Focus Keyword
3. 具有吸引点击的元素（数据、行动号召、独特价值）
4. 如果原文已有Meta Description，进行优化改进

**输出格式**:
```json
"meta_description": {{
  "original_meta_description": "本文介绍AI在医疗领域的应用。",
  "suggested_meta_description": "深入解析AI如何革新医疗诊断：从影像分析到早期筛查，了解人工智能如何提升诊断准确率30%以上。",
  "meta_description_improvements": [
    "添加具体数据（30%）增强可信度",
    "使用动作词"革新"、"提升"增强吸引力",
    "包含主关键词"AI医疗诊断"",
    "符合150-160字符最佳长度"
  ],
  "meta_description_score": 92
}}
```

---

### 任务4: Tags推荐🏷️

分析内容后推荐相关标签：

**要求**:
1. 推荐6-8个标签
2. 包含高频标签（流量入口）+ 中频标签（精准定位）+ 长尾标签（细分流量）
3. 标签与文章内容高度相关
4. 优先推荐可能已存在的常见标签

**输出格式**:
```json
"tags": {{
  "suggested_tags": [
    {{"tag": "人工智能", "relevance": 0.95, "type": "primary"}},
    {{"tag": "医疗AI", "relevance": 0.92, "type": "primary"}},
    {{"tag": "深度学习医疗应用", "relevance": 0.78, "type": "secondary"}},
    {{"tag": "AI诊断工具", "relevance": 0.85, "type": "trending"}},
    // ... 4-6个更多标签
  ],
  "recommended_tag_count": "建议使用6-8个标签",
  "tag_strategy": "3个高频标签 + 2个中频标签 + 1个长尾标签"
}}
```

---

### 任务5: FAQ生成（AI搜索优化）❓

根据文章内容生成**8-10个**常见问题和答案，优化在AI搜索引擎中的表现：

**要求**:
1. 生成8-10个FAQ
2. 问题类型多样化：事实型、操作型、对比型、定义型
3. 问题符合真实搜索意图（用户在AI搜索中会问的）
4. 答案简洁准确（50-150字），基于文章内容，不杜撰
5. 自然融入主关键词和相关词

**输出格式**:
```json
"faqs": [
  {{
    "question": "人工智能在医疗诊断中的准确率有多高？",
    "answer": "根据最新研究，AI医疗诊断系统在影像分析领域的准确率可达95%以上，部分场景甚至超过人类医生。例如在肺癌早期筛查中，AI系统的准确率比传统方法提升了30-40%。",
    "question_type": "factual",
    "search_intent": "informational",
    "keywords_covered": ["AI医疗诊断", "准确率", "影像分析"],
    "confidence": 0.92
  }},
  // ... 7-9个更多FAQ
]
```

---

## 📤 最终输出格式

请严格按照以下JSON Schema输出所有5个任务的结果：

```json
{{
  "title_suggestions": {{
    "suggested_title_sets": [...],
    "optimization_notes": [...]
  }},
  "seo_keywords": {{
    "focus_keyword": "...",
    "primary_keywords": [...],
    "secondary_keywords": [...],
    ...
  }},
  "meta_description": {{
    "suggested_meta_description": "...",
    "meta_description_improvements": [...],
    ...
  }},
  "tags": {{
    "suggested_tags": [...],
    ...
  }},
  "faqs": [
    {{"question": "...", "answer": "...", ...}},
    // ... 8-10个FAQ
  ]
}}
```

---

## ⚠️ 重要注意事项

1. **内容一致性**: 标题、关键词、Meta、Tags、FAQ应相互协调，使用统一的核心概念
2. **关键词覆盖**: 确保Focus Keyword在标题、Meta Description、FAQ中都有出现
3. **数据准确**: FAQ答案必须基于文章内容，不得杜撰数据
4. **长度控制**: 严格遵守各项长度限制
5. **多样性**: 标题类型多样、FAQ问题类型多样

---

现在请完成所有5个优化任务。
"""

    def _build_full_title(self, article: Article) -> str:
        """构建完整标题"""
        parts = []
        if article.title_prefix:
            parts.append(article.title_prefix)
        parts.append(article.title_main)
        if article.title_suffix:
            parts.append(article.title_suffix)
        return " | ".join(parts)

    def _parse_unified_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析AI响应

        提取：
        - title_suggestions
        - seo_keywords
        - meta_description
        - tags
        - faqs
        """
        import json
        import re

        # 提取JSON代码块
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_text

        try:
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse unified optimization response: {e}")
            raise ValueError("AI响应格式错误")

    async def _store_optimizations(
        self,
        article_id: int,
        result: Dict[str, Any]
    ) -> None:
        """
        分别存储优化结果到对应的表

        Args:
            article_id: 文章ID
            result: AI生成的完整结果
        """

        # 1. 存储标题建议到 title_suggestions 表
        title_data = result.get('title_suggestions', {})
        await self._save_title_suggestions(article_id, title_data)

        # 2. 存储SEO建议到 seo_suggestions 表
        seo_data = {
            'focus_keyword': result.get('seo_keywords', {}).get('focus_keyword'),
            'primary_keywords': result.get('seo_keywords', {}).get('primary_keywords'),
            'secondary_keywords': result.get('seo_keywords', {}).get('secondary_keywords'),
            'keyword_difficulty': result.get('seo_keywords', {}).get('keyword_difficulty'),
            'search_volume_estimate': result.get('seo_keywords', {}).get('search_volume_estimate'),
            'suggested_meta_description': result.get('meta_description', {}).get('suggested_meta_description'),
            'meta_description_improvements': result.get('meta_description', {}).get('meta_description_improvements'),
            'meta_description_score': result.get('meta_description', {}).get('meta_description_score'),
            'suggested_tags': result.get('tags', {}).get('suggested_tags'),
        }
        await self._save_seo_suggestions(article_id, seo_data)

        # 3. 存储FAQ到 article_faqs 表
        faqs = result.get('faqs', [])
        await self._save_faqs(article_id, faqs)

    async def _save_title_suggestions(self, article_id: int, data: Dict) -> None:
        """存储标题建议"""
        # 实现省略...
        pass

    async def _save_seo_suggestions(self, article_id: int, data: Dict) -> None:
        """存储SEO建议"""
        # 实现省略...
        pass

    async def _save_faqs(self, article_id: int, faqs: List[Dict]) -> None:
        """存储FAQ"""
        # 实现省略...
        pass
```

---

## 📊 成本与性能对比

### Token使用量估算

| 方案 | Prompt Tokens | Response Tokens | Total Tokens | 成本估算 |
|------|--------------|----------------|--------------|---------|
| **原方案（两次调用）** | | | | |
| - Step 1标题优化 | ~1,500 | ~1,200 | ~2,700 | $0.02-0.03 |
| - Step 3 SEO+FAQ | ~2,000 | ~3,500 | ~5,500 | $0.08-0.10 |
| **小计** | ~3,500 | ~4,700 | **~8,200** | **$0.10-0.13** |
| **优化方案（一次调用）** | | | | |
| - 统一优化服务 | ~2,500 | ~4,000 | **~6,500** | **$0.06-0.08** |
| **节省** | ↓ ~1,000 | ↓ ~700 | **↓ ~1,700** | **↓ 40-60%** |

*注：基于Claude Sonnet 4.5定价：Input $3/M tokens, Output $15/M tokens*

---

### 响应时间对比

| 方案 | API调用次数 | 平均耗时 |
|------|-----------|---------|
| **原方案（两次调用）** | 2次 | 30-40秒 |
| - Step 1标题优化 | 1次 | 10-15秒 |
| - Step 3 SEO+FAQ | 1次 | 20-25秒 |
| **优化方案（一次调用）** | **1次** | **20-30秒** |
| **节省** | ↓ 1次 | **↓ 30-40%** |

---

## 🔧 实施调整

### API调整

#### 原API（分离）

```http
# Step 1
POST /v1/articles/{id}/generate-title-suggestions

# Step 3
POST /v1/articles/{id}/generate-seo-suggestions
POST /v1/articles/{id}/generate-faqs
```

#### 新API（统一）

```http
# Step 1调用（一次性生成所有）
POST /v1/articles/{id}/generate-all-optimizations
```

**请求体**:
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

**响应**:
```json
{
  "success": true,
  "generation_id": "unified_opt_123",
  "title_suggestions": { ... },
  "seo_suggestions": { ... },
  "tags_suggestions": { ... },
  "faqs": [ ... ],
  "generation_metadata": {
    "total_cost_usd": 0.07,
    "total_tokens": 6500,
    "duration_ms": 25000,
    "savings_vs_separate": {
      "cost_saved_usd": 0.05,
      "time_saved_ms": 12000,
      "savings_percentage": 42
    }
  }
}
```

---

### 数据库调整

**新增字段**（articles表）:
```sql
-- 统一优化生成记录
ALTER TABLE articles ADD COLUMN unified_optimization_generated BOOLEAN DEFAULT FALSE;
ALTER TABLE articles ADD COLUMN unified_optimization_generated_at TIMESTAMP;
ALTER TABLE articles ADD COLUMN unified_optimization_cost DECIMAL(10, 4);
```

**关联设计**:
```
articles
  ├─ title_suggestions (1:1)
  ├─ seo_suggestions (1:1)
  └─ article_faqs (1:N)

所有建议在Step 1统一生成，通过article_id关联
```

---

### 前端调整

#### Step 1（解析确认）

```javascript
// 在解析完成后，调用统一优化服务
const generateAllOptimizations = async (articleId) => {
  const response = await api.post(
    `/v1/articles/${articleId}/generate-all-optimizations`,
    {
      options: {
        include_title: true,
        include_seo: true,
        include_tags: true,
        include_faqs: true,
        faq_target_count: 10
      }
    }
  );

  // 响应包含所有建议，但Step 1只显示标题部分
  return response.data;
};

// Step 1 UI只显示标题建议
<TitleOptimizationCard
  suggestions={optimizations.title_suggestions}
  onConfirm={handleTitleConfirm}
/>
```

#### Step 3（SEO确认）

```javascript
// 从数据库加载已生成的建议（Step 1时已生成）
const loadExistingOptimizations = async (articleId) => {
  // 不调用AI，直接获取缓存结果
  const response = await api.get(
    `/v1/articles/${articleId}/optimizations`
  );

  return response.data; // 返回Step 1生成的建议
};

// Step 3 UI显示SEO和FAQ
<SEOOptimizationCard
  suggestions={optimizations.seo_suggestions}
  onConfirm={handleSEOConfirm}
/>
<FAQCard
  faqs={optimizations.faqs}
  onConfirm={handleFAQConfirm}
/>
```

---

## ✅ 优势总结

### 1. **成本节省** 💰
- Token使用减少 ~1,700个
- 成本降低 **40-60%**（$0.10-0.13 → $0.06-0.08/篇）
- 年处理10,000篇文章，节省 **$500-700**

### 2. **性能提升** ⚡
- API调用减少50%（2次→1次）
- 响应时间缩短30-40%（30-40秒→20-30秒）
- 用户体验更流畅

### 3. **内容一致性** 🎯
- 标题、关键词、Meta、FAQ在同一上下文生成
- 核心概念统一，更协调
- Focus Keyword自然贯穿所有内容

### 4. **架构简化** 🏗️
- 单一AI服务入口
- 减少服务间依赖
- 更易维护和监控

---

## ⚠️ 注意事项

### 1. **Prompt长度**
- 统一Prompt较长（~2,500 tokens）
- 但仍在Claude限制内（200K context）
- 生成内容较多，Response可达4,000 tokens

### 2. **失败处理**
- 如果统一生成失败，可降级为分离调用
- 增加重试逻辑（最多3次）
- 记录失败原因，分析优化点

### 3. **缓存策略**
- Step 1生成后，结果缓存到数据库
- Step 3直接读取，不重新生成
- 如需重新生成，提供"regenerate"选项

### 4. **分步确认**
- 虽然一次生成，但分步确认（Step 1标题，Step 3 SEO）
- 用户体验不变，仍然是4步工作流
- 仅后端优化，前端透明

---

## 📅 实施计划调整

### 原计划

- Step 1标题优化: 17.5小时
- Step 3 SEO+FAQ: 68小时
- **总计**: 85.5小时

### 调整后

- **统一优化服务**: 20小时（后端）
- Step 1 UI（标题部分）: 8小时
- Step 3 UI（SEO+FAQ部分）: 30小时
- 集成测试: 4小时
- 文档更新: 2小时
- **总计**: **64小时** ✅ 节省 21.5小时

---

## 🎯 总结

### 关键变化

| 维度 | 原方案 | 优化方案 | 改进 |
|------|--------|---------|------|
| **AI调用** | 2次（Step 1 + Step 3） | 1次（Step 1统一） | ↓ 50% |
| **成本** | $0.10-0.13/篇 | $0.06-0.08/篇 | ↓ 40-60% |
| **耗时** | 30-40秒 | 20-30秒 | ↓ 30-40% |
| **开发工时** | 85.5小时 | 64小时 | ↓ 25% |

### 用户体验

✅ **不变**: 4步工作流保持不变
✅ **不变**: UI交互体验不变
✅ **提升**: 响应更快，体验更好

### 实施建议

1. ✅ **优先实施统一服务**（架构优势明显）
2. ✅ **保留降级方案**（分离调用作为fallback）
3. ✅ **监控成本和性能**（验证优化效果）
4. ✅ **逐步迭代Prompt**（优化生成质量）

---

**文档版本**: v1.0
**下一步**: 等待用户批准，确认架构调整后开始实施
