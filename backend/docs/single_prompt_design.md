# AI Prompt 架構設計文檔

## 版本信息
- 文档版本: v2.0.0
- 创建日期: 2025-10-27
- 最后更新: 2025-12-07

---

## ⚠️ 重要更新 (v2.0.0)

**架構已調整為分離式設計：**

| 流程 | AI 調用 | 功能 |
|------|---------|------|
| **解析流程** | 1次主調用 + 1次優化調用 | 結構解析 + SEO + FAQ |
| **校對流程** | 1次獨立調用 | 405條規則檢查 |

**關鍵變更：**
- ❌ 解析 Prompt 不再包含校對功能
- ✅ 校對由獨立的 `ProofreadingAnalysisService` 使用專門的 405 條規則 Prompt 處理
- ✅ 解析和校對完全分離，各自優化

---

## 一、方案概述

### 當前架構（v2.0）

**解析流程**（ArticleParserService）：
1. 結構解析（標題、作者、正文、圖片）
2. SEO 優化（Meta、關鍵詞、Tags）
3. 分類選擇（主分類 + 副分類）
4. FAQ 生成

**校對流程**（ProofreadingAnalysisService）：
1. 405條校對規則檢查（A-F類）
2. 發布合規性檢查
3. 確定性規則引擎補充

### 舊方案參考（已棄用）
~~使用**单一综合 Prompt**一次性完成文章的所有分析和优化工作，包括：~~
~~1. 450条校对规则检查（A-F类）~~
~~2. Meta描述优化~~
~~3. SEO关键词提取/优化~~
~~4. FAQ Schema生成（3/5/7问题）~~
~~5. 发布合规性检查~~

### 优势总结
| 维度 | 多次调用 | 单次调用 | 改善 |
|------|---------|---------|------|
| Token成本 | ~4x | ~1x | **节省60-75%** |
| 处理时间 | ~6秒 | ~2.5秒 | **节省58%** |
| 内容一致性 | ❌ 可能不一致 | ✅ 保证一致 | **质量提升** |
| 上下文理解 | ❌ 分散 | ✅ 统一 | **更智能** |

---

## 二、完整 Prompt 设计

### 输入格式

```
用户输入的文章内容（三部分格式）
↓
纽约市政府今天宣布新交通管理政策，将从下月起实施。

据市长办公室发布的声明，新政策旨在缓解市中心交通拥堵问题...

Meta描述：
纽约市政府宣布新交通管理政策，旨在缓解市中心拥堵...

SEO关键词：
纽约交通, 交通政策, 市中心拥堵
```

### 系统 Prompt（完整版）

````markdown
# 角色定义
你是专业的新闻编辑助手，负责对文稿进行全面的校对、优化和SEO增强。

# 任务目标
对输入的文稿进行一次性完整分析，输出所有必需的处理结果。

# 输入格式
文稿分为三个部分：
1. 正文：文章主体内容
2. Meta描述：位于"Meta描述："标记之后
3. SEO关键词：位于"SEO关键词："标记之后

# 处理流程

## 第一步：解析文稿结构
识别并分离三个部分，确保格式正确。

## 第二步：应用450条校对规则
按照以下分类检查文稿：

### A类：用字与用词（~200条规则）
- 错别字检查
- 词汇选用规范
- 专业术语准确性
- 示例规则：
  * A001: "做"vs"作" - "作为"不写"做为"
  * A002: "的"vs"地"vs"得" - 正确使用
  * A003: "以"vs"已"vs"已经" - 时态准确
  * A156: "启用"vs"起用" - 启用设备，起用人员
  * ... (完整规则见附录)

### B类：标点符号（~50条规则）
- 标点使用规范
- 中英文标点混用检查
- 示例规则：
  * B001: 中文内容使用中文标点（，。！？）
  * B002: 引号规则 - 使用「」或""
  * B003: 省略号 - 使用"……"（6个点）
  * B015: 顿号使用 - 并列词语用"、"
  * ... (完整规则见附录)

### C类：数字用法（~30条规则）
- 数字书写规范
- 单位使用规范
- 示例规则：
  * C001: 一位数用汉字，多位数用阿拉伯数字
  * C002: 统计数据用阿拉伯数字
  * C003: 金额表达 - "100万元"或"1,000,000元"
  * C012: 百分比 - "15%"或"百分之十五"
  * ... (完整规则见附录)

### D类：人名地名译名（~100条规则）
- 人名翻译规范
- 地名标准写法
- 机构名称准确性
- 示例规则：
  * D001: 常见人名对照表（附录D-1）
  * D002: 世界主要城市译名（附录D-2）
  * D003: 国际组织标准名称（附录D-3）
  * D078: "New York" → "纽约"（不是"纽约市"除非原文有City）
  * ... (完整规则见附录)

### E类：报导用词（~50条规则）
- 新闻用语规范
- 政治正确性
- 敏感词规避
- 示例规则：
  * E001: 避免绝对化表述（"最"、"第一"需证据）
  * E002: 消息来源标注 - "据XX报道"
  * E003: 时间表述准确 - 具体日期优先
  * E025: 避免主观评价 - 使用引语表达观点
  * ... (完整规则见附录)

### F类：发布合规（~20条规则 - WordPress技术要求）
- WordPress格式兼容性
- 富文本标记检查
- SEO技术规范
- 示例规则：
  * F001: 标题长度 30-60字符（SEO最佳）
  * F002: Meta描述 120-160字符
  * F003: 段落长度 ≤ 150字（可读性）
  * F004: 关键词密度 1-3%（不过度）
  * F005: 图片alt属性必填
  * F006: 内部链接至少2个
  * F007: H2/H3标题结构合理
  * F015: 禁止特殊字符可能破坏WordPress编辑器
  * ... (完整规则见附录)

## 第三步：优化Meta描述
基于正文内容和校对结果，生成优化的Meta描述：
- 长度：120-160字符（中文约60-80字）
- 包含主要关键词（自然融入）
- 准确概括文章主题
- 吸引点击（但不标题党）
- 与正文用词保持一致

## 第四步：提取/优化SEO关键词
分析文章内容，提供关键词建议：
- 主关键词：1-2个（核心主题）
- 次关键词：3-5个（相关主题）
- 长尾关键词：2-3个（具体场景）
- 确保关键词：
  * 在正文中自然出现
  * 与Meta描述一致
  * 符合搜索意图
  * 不过度堆砌

## 第五步：生成FAQ Schema
基于文章内容，生成3个版本的FAQ Schema（Schema.org FAQPage格式）：
- 简版：3个问题（核心要点）
- 标准版：5个问题（全面覆盖）
- 完整版：7个问题（深度扩展）

要求：
- 问题自然，符合用户搜索习惯
- 答案直接从正文提取或合理概括（50-150字）
- JSON-LD格式，直接可用于WordPress
- 与正文、Meta、关键词术语一致

## 第六步：发布合规性检查
检查F类规则，判断是否可以发布：
- ✅ 通过：无F类问题
- ⚠️ 警告：有F类建议但不阻止发布
- ❌ 阻止：有严重F类问题必须修复

# 输出格式（JSON结构）

请严格按照以下JSON格式输出结果：

```json
{
  "parsed_content": {
    "body": "正文内容",
    "meta_original": "原始Meta描述",
    "keywords_original": ["原始", "关键词"]
  },

  "proofreading_results": {
    "summary": {
      "total_issues": 12,
      "by_category": {
        "A": 3,
        "B": 2,
        "C": 1,
        "D": 2,
        "E": 1,
        "F": 3
      },
      "severity": {
        "critical": 1,
        "major": 4,
        "minor": 7
      }
    },

    "issues": [
      {
        "category": "A",
        "rule_id": "A156",
        "severity": "major",
        "location": {
          "section": "body",
          "paragraph": 2,
          "original_text": "政府将起用新的交通系统"
        },
        "description": "「起用」应为「启用」。起用指任用人员，启用指开始使用设备/系统。",
        "suggestion": "政府将启用新的交通系统",
        "confidence": 0.95
      },
      {
        "category": "B",
        "rule_id": "B001",
        "severity": "minor",
        "location": {
          "section": "body",
          "paragraph": 3,
          "original_text": "根据专家表示,这将..."
        },
        "description": "中文内容使用了英文逗号",
        "suggestion": "根据专家表示，这将...",
        "confidence": 1.0
      },
      {
        "category": "F",
        "rule_id": "F002",
        "severity": "major",
        "location": {
          "section": "meta",
          "original_text": "纽约市政府宣布新交通管理政策，旨在缓解市中心拥堵。"
        },
        "description": "Meta描述长度仅38字符，建议120-160字符以提升SEO效果",
        "suggestion": "纽约市政府宣布新交通管理政策，将从下月起实施，旨在缓解市中心交通拥堵问题。新措施包括增加公交车道、限制私家车进入特定区域、提高停车费用，预计将使通勤时间减少15%并降低空气污染。",
        "confidence": 0.9
      }
    ]
  },

  "optimized_meta": {
    "suggestion": "纽约市政府宣布新交通管理政策，将从下月起实施，旨在缓解市中心交通拥堵问题。新措施包括增加公交车道、限制私家车进入特定区域、提高停车费用，预计将使通勤时间减少15%并降低空气污染。",
    "length": 128,
    "improvements": [
      "扩展至SEO最佳长度（120-160字符）",
      "增加具体措施说明",
      "包含预期效果（减少15%通勤时间）",
      "自然融入主关键词「纽约市」、「交通管理政策」"
    ],
    "keywords_included": ["纽约市", "交通管理政策", "市中心拥堵", "公交车道"]
  },

  "optimized_keywords": {
    "primary": ["纽约交通政策", "市中心拥堵治理"],
    "secondary": ["公交车道", "停车费用", "通勤优化", "空气污染"],
    "longtail": ["纽约市交通管理新措施", "市中心私家车限行", "通勤时间减少方案"],
    "analysis": {
      "original_keywords": ["纽约交通", "交通政策", "市中心拥堵"],
      "changes": [
        "「纽约交通」→「纽约交通政策」（更具体）",
        "新增「公交车道」（文中重要措施）",
        "新增长尾关键词以覆盖更多搜索场景"
      ],
      "keyword_density": {
        "纽约": "0.8%",
        "交通": "2.1%",
        "政策": "1.2%"
      }
    }
  },

  "faq_schema": {
    "version_3": {
      "questions_count": 3,
      "schema": {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
          {
            "@type": "Question",
            "name": "纽约市新交通管理政策何时实施？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "根据市长办公室的声明，新交通管理政策将从下月起正式实施。"
            }
          },
          {
            "@type": "Question",
            "name": "新交通政策包括哪些主要措施？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "主要措施包括三个方面：增加公交车道、限制私家车进入特定区域、提高停车费用。这些措施旨在从多个角度缓解市中心的交通拥堵问题。"
            }
          },
          {
            "@type": "Question",
            "name": "新政策预计会带来什么效果？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "据交通专家表示，这些措施预计将使通勤时间减少15%，同时有效降低空气污染水平，改善市中心的环境质量。"
            }
          }
        ]
      }
    },

    "version_5": {
      "questions_count": 5,
      "schema": {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
          {
            "@type": "Question",
            "name": "纽约市新交通管理政策何时实施？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "根据市长办公室的声明，新交通管理政策将从下月起正式实施。"
            }
          },
          {
            "@type": "Question",
            "name": "新交通政策包括哪些主要措施？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "主要措施包括三个方面：增加公交车道以提升公共交通效率、限制私家车进入特定区域以减少车流量、提高停车费用以鼓励使用公共交通。"
            }
          },
          {
            "@type": "Question",
            "name": "哪些区域会限制私家车进入？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "具体限行区域将主要集中在市中心交通拥堵最严重的地段，详细范围将由交通部门在政策实施前公布。"
            }
          },
          {
            "@type": "Question",
            "name": "新政策对通勤时间有何影响？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "交通专家预测，新政策实施后，市中心的通勤时间预计将减少约15%，这意味着大多数通勤者每天可以节省10-20分钟的通勤时间。"
            }
          },
          {
            "@type": "Question",
            "name": "新政策如何改善空气质量？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "通过限制私家车数量和鼓励使用公共交通，新政策将有效减少汽车尾气排放，从而降低市中心的空气污染水平。"
            }
          }
        ]
      }
    },

    "version_7": {
      "questions_count": 7,
      "schema": {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
          {
            "@type": "Question",
            "name": "纽约市新交通管理政策何时实施？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "根据市长办公室的声明，新交通管理政策将从下月起正式实施。"
            }
          },
          {
            "@type": "Question",
            "name": "新交通政策包括哪些主要措施？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "主要措施包括三个方面：增加公交车道以提升公共交通效率、限制私家车进入特定区域以减少车流量、提高停车费用以鼓励使用公共交通。"
            }
          },
          {
            "@type": "Question",
            "name": "哪些区域会限制私家车进入？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "具体限行区域将主要集中在市中心交通拥堵最严重的地段，详细范围将由交通部门在政策实施前公布。"
            }
          },
          {
            "@type": "Question",
            "name": "新政策对通勤时间有何影响？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "交通专家预测，新政策实施后，市中心的通勤时间预计将减少约15%，这意味着大多数通勤者每天可以节省10-20分钟的通勤时间。"
            }
          },
          {
            "@type": "Question",
            "name": "停车费用会提高多少？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "具体的停车费用调整方案尚未公布，但政府表示将通过价格杠杆来引导市民优先选择公共交通出行。"
            }
          },
          {
            "@type": "Question",
            "name": "新政策如何改善空气质量？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "通过限制私家车数量和鼓励使用公共交通，新政策将有效减少汽车尾气排放，从而降低市中心的空气污染水平。"
            }
          },
          {
            "@type": "Question",
            "name": "市民如何了解更多政策细节？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "市民可以关注市长办公室和交通部门的官方公告，政策实施前将举行公众说明会，详细解释各项措施的具体内容和执行方式。"
            }
          }
        ]
      }
    }
  },

  "compliance_check": {
    "can_publish": true,
    "status": "warning",
    "f_class_issues": [
      {
        "rule_id": "F002",
        "severity": "major",
        "description": "Meta描述长度不足，建议优化",
        "blocks_publish": false
      },
      {
        "rule_id": "F006",
        "severity": "minor",
        "description": "文章缺少内部链接",
        "blocks_publish": false
      }
    ],
    "recommendations": [
      "使用优化后的Meta描述以提升SEO效果",
      "考虑在正文中添加2-3个相关文章的内部链接",
      "建议添加相关图片并填写alt属性"
    ]
  },

  "processing_metadata": {
    "model": "claude-sonnet-4-5-20250929",
    "timestamp": "2025-10-27T10:30:45Z",
    "processing_time_ms": 2341,
    "total_tokens": {
      "input": 2456,
      "output": 1823,
      "total": 4279
    },
    "confidence_score": 0.92
  }
}
```

# 特殊说明

## 术语一致性原则
在生成所有内容时，必须保持术语的一致性：
- 如果正文使用"纽约市"，则Meta、关键词、FAQ中也使用"纽约市"
- 如果正文使用具体数字"15%"，则其他部分也使用相同表述
- 机构名称、人名、地名必须完全一致

## 置信度评分
每个校对问题都需要提供置信度（0.0-1.0）：
- 1.0：完全确定（如标点符号错误）
- 0.9-0.99：非常确定（如常见错别字）
- 0.8-0.89：比较确定（如用词不当）
- 0.7-0.79：有一定把握（如风格建议）
- <0.7：不确定，需要人工判断

## 严重程度分类
- **critical**: 必须修复才能发布（F类严重问题）
- **major**: 强烈建议修复（影响质量或SEO）
- **minor**: 可选修复（优化建议）

# 输出要求
1. 必须输出完整的JSON结构，不得省略任何字段
2. 所有文本内容必须正确转义JSON特殊字符
3. FAQ Schema必须是有效的JSON-LD格式
4. 置信度和严重程度必须合理评估
5. 保持所有内容的术语一致性
````

---

## 三、后端实现代码

### 3.1 服务层实现

```python
# backend/src/services/proofreading/service.py

from typing import Dict, Any
from anthropic import AsyncAnthropic

from src.services.proofreading.ai_prompt_builder import ProofreadingPromptBuilder
from src.services.proofreading.deterministic_engine import DeterministicRuleEngine
from src.services.proofreading.merger import ProofreadingResultMerger
from src.services.proofreading.models import ArticlePayload, ProofreadingResult


class ProofreadingAnalysisService:
    """
    单一 Prompt + 程序化校验的统一服务。

    责任：
    1. 构建系统/用户 Prompt，并调用 Claude Messages API（单次调用）。
    2. 解析 AI 返回的 JSON，转换为 ProofreadingResult。
    3. 运行 DeterministicRuleEngine（F 类强制 + 高置信度规则）。
    4. 使用 ProofreadingResultMerger 合并 AI 与脚本结果，统一统计。
    """

    def __init__(self):
        self.manifest = load_default_manifest()
        self.prompt_builder = ProofreadingPromptBuilder(self.manifest)
        self.rule_engine = DeterministicRuleEngine()
        self.merger = ProofreadingResultMerger()
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL

    async def analyze_article(self, payload: ArticlePayload) -> ProofreadingResult:
        prompt_bundle = self.prompt_builder.build_prompt(payload)
        ai_response = await self.client.messages.create(
            model=self.model,
            temperature=0.2,
            max_tokens=settings.ANTHROPIC_MAX_TOKENS,
            messages=[
                {"role": "system", "content": prompt_bundle["system"]},
                {"role": "user", "content": prompt_bundle["user"]},
            ],
        )

        ai_result = self._parse_ai_response(ai_response)
        script_issues = self.rule_engine.run(payload)
        merged = self.merger.merge(ai_result, script_issues)

        merged.processing_metadata.rule_manifest_version = self.manifest.version
        merged.processing_metadata.script_engine_version = self.rule_engine.VERSION
        return merged
```

> 📌 **关键变化**
> - PromptBuilder 生成 system/user 双段指令，附带规则清单表格与输出 schema。
> - DeterministicRuleEngine 暂含 B2-002、F1-002、F2-001 等可程序化规则，可持续扩展。
> - ProofreadingResultMerger 统一去重、冲突处理，并输出 `source_breakdown`（ai/script/merged）。

#### 3.1.1 合并策略摘要

| 情况 | 处理策略 |
|------|----------|
| 只 AI 命中 | 保留 AI issue，`source=ai`，标记 `confidence<0.7` 时在 UI 上要求人工复核 |
| 只脚本命中 | 保留脚本 issue，`source=script`，若 `blocks_publish=true` 则直接阻断 |
| 双方命中同一 rule_id | 以脚本结果为准，`source=merged`，但保留 AI 提供的语境说明/建议 |
| AI 输出缺少 rule_id | 直接丢弃并记录 `proofreading_ai_issue_parse_failed` 日志 |
| AI 提供 rule_coverage | 存储至 `processing_metadata.notes['ai_rule_coverage']`，用于回归对比 |

> ⚠️ 所有合并结果最终写入 `articles.proofreading_issues`。F 类 `blocks_publish` 将同步更新 `critical_issues_count`。

### 3.2 API端点实现

```python
# backend/app/api/v1/articles.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from src.services.proofreading import ProofreadingAnalysisService
from app.models.article import Article, ArticleVersion
from app.schemas.article import ArticleAnalysisResponse
import json

router = APIRouter()

@router.post("/{article_id}/analyze", response_model=ArticleAnalysisResponse)
async def analyze_article(
    article_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    分析文章 - 单一 Prompt 完成所有处理

    工作流程：
    1. 验证文章存在且属于当前用户
    2. 调用 AI 服务进行综合分析（单次调用）
    3. 保存所有分析结果到数据库
    4. 返回完整结果给前端
    """

    # 1. 获取文章
    article = db.query(Article).filter(
        Article.id == article_id,
        Article.author_id == current_user.id
    ).first()

    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 2. 调用分析服务（单一 Prompt）
    analysis_service = ProofreadingAnalysisService()

    try:
        result = await analysis_service.analyze_article(
            article_content=article.content,
            article_id=article_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI分析失败: {str(e)}"
        )

    # 3. 保存分析结果到数据库
    _save_analysis_results(db, article, result)

    # 4. 后台任务：更新文章状态
    background_tasks.add_task(
        _update_article_status,
        db=db,
        article_id=article_id,
        can_publish=result['compliance_check']['can_publish']
    )

    return ArticleAnalysisResponse(**result)


def _save_analysis_results(
    db: Session,
    article: Article,
    result: Dict[str, Any]
):
    """
    保存所有分析结果到数据库
    """

    # 创建建议版本（包含所有优化内容）
    suggested_version = ArticleVersion(
        article_id=article.id,
        version_type='suggested',
        content=_build_suggested_content(article.content, result),
        meta_description=result['optimized_meta']['suggestion'],
        seo_keywords=result['optimized_keywords']['primary'] +
                     result['optimized_keywords']['secondary'],
        faq_schema_3=json.dumps(result['faq_schema']['version_3']['schema']),
        faq_schema_5=json.dumps(result['faq_schema']['version_5']['schema']),
        faq_schema_7=json.dumps(result['faq_schema']['version_7']['schema']),
        proofreading_issues=json.dumps(result['proofreading_results']['issues']),
        compliance_status=result['compliance_check']['status'],
        ai_metadata=json.dumps(result['processing_metadata'])
    )

    db.add(suggested_version)

    # 更新文章状态
    article.status = 'under_review'
    article.has_suggestions = True
    article.total_issues = result['proofreading_results']['summary']['total_issues']

    db.commit()


def _build_suggested_content(
    original_content: str,
    result: Dict[str, Any]
) -> str:
    """
    基于校对建议构建建议版本的正文
    应用所有major和critical级别的修改
    """

    content = original_content

    # 按位置倒序排列（避免位置偏移）
    issues = sorted(
        [i for i in result['proofreading_results']['issues']
         if i['severity'] in ['critical', 'major']],
        key=lambda x: x['location'].get('paragraph', 0),
        reverse=True
    )

    for issue in issues:
        if 'suggestion' in issue and issue['location']['section'] == 'body':
            content = content.replace(
                issue['location']['original_text'],
                issue['suggestion']
            )

    return content


def _update_article_status(
    db: Session,
    article_id: int,
    can_publish: bool
):
    """
    后台任务：更新文章发布状态
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    if article:
        article.can_publish = can_publish
        db.commit()
```

---

## 四、前端实现

### 4.1 API调用（单次请求）

```typescript
// frontend/src/services/articleApi.ts

import axios from 'axios';

export interface AnalysisResult {
  parsed_content: {
    body: string;
    meta_original: string;
    keywords_original: string[];
  };
  proofreading_results: {
    summary: {
      total_issues: number;
      by_category: Record<string, number>;
      severity: Record<string, number>;
    };
    issues: ProofreadingIssue[];
  };
  optimized_meta: {
    suggestion: string;
    length: number;
    improvements: string[];
    keywords_included: string[];
  };
  optimized_keywords: {
    primary: string[];
    secondary: string[];
    longtail: string[];
    analysis: any;
  };
  faq_schema: {
    version_3: FAQSchema;
    version_5: FAQSchema;
    version_7: FAQSchema;
  };
  compliance_check: {
    can_publish: boolean;
    status: 'pass' | 'warning' | 'blocked';
    f_class_issues: any[];
    recommendations: string[];
  };
  processing_metadata: {
    processing_time_ms: number;
    total_tokens: {
      input: number;
      output: number;
      total: number;
    };
  };
}

/**
 * 分析文章 - 单次API调用获取所有结果
 */
export async function analyzeArticle(articleId: number): Promise<AnalysisResult> {
  const response = await axios.post<AnalysisResult>(
    `/api/v1/articles/${articleId}/analyze`
  );

  return response.data;
}
```

### 4.2 前端UI组件

```typescript
// frontend/src/components/ArticleAnalysis.tsx

import React, { useState } from 'react';
import { analyzeArticle, AnalysisResult } from '@/services/articleApi';
import { LoadingSpinner } from './LoadingSpinner';
import { ProofreadingResults } from './ProofreadingResults';
import { MetaOptimization } from './MetaOptimization';
import { KeywordsOptimization } from './KeywordsOptimization';
import { FAQSchemaSelector } from './FAQSchemaSelector';
import { ComplianceCheck } from './ComplianceCheck';

interface Props {
  articleId: number;
  onComplete: (result: AnalysisResult) => void;
}

export function ArticleAnalysis({ articleId, onComplete }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);

    try {
      // 单次 API 调用获取所有结果
      const analysisResult = await analyzeArticle(articleId);

      setResult(analysisResult);
      onComplete(analysisResult);

    } catch (err: any) {
      setError(err.message || '分析失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="analysis-loading">
        <LoadingSpinner />
        <p>AI正在进行综合分析...</p>
        <p className="text-sm text-gray-500">
          正在检查450条校对规则、优化Meta描述、提取关键词、生成FAQ...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analysis-error">
        <p>❌ {error}</p>
        <button onClick={handleAnalyze}>重试</button>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="analysis-prompt">
        <button
          onClick={handleAnalyze}
          className="btn-primary"
        >
          开始AI分析
        </button>
        <p className="text-sm text-gray-600">
          AI将一次性完成：校对检查、Meta优化、关键词提取、FAQ生成
        </p>
      </div>
    );
  }

  return (
    <div className="analysis-results">
      {/* 处理信息 */}
      <div className="processing-info">
        <p>
          ✅ 分析完成
          （耗时 {result.processing_metadata.processing_time_ms}ms，
          消耗 {result.processing_metadata.total_tokens.total} tokens）
        </p>
      </div>

      {/* 合规性检查 */}
      <ComplianceCheck data={result.compliance_check} />

      {/* 校对结果 */}
      <ProofreadingResults
        summary={result.proofreading_results.summary}
        issues={result.proofreading_results.issues}
      />

      {/* Meta优化 */}
      <MetaOptimization
        original={result.parsed_content.meta_original}
        optimized={result.optimized_meta}
      />

      {/* 关键词优化 */}
      <KeywordsOptimization
        original={result.parsed_content.keywords_original}
        optimized={result.optimized_keywords}
      />

      {/* FAQ Schema选择 */}
      <FAQSchemaSelector
        schemas={result.faq_schema}
      />
    </div>
  );
}
```

---

## 五、成本与性能分析

### 5.1 Token使用对比

**示例文章**（500字正文 + Meta + 关键词）

#### 多次调用方案：
```
第1次（校对）:
  Input: 500字文章 + 450条规则 (~3000 tokens)
  Output: 校对结果 (~800 tokens)

第2次（Meta优化）:
  Input: 500字文章 + Meta优化Prompt (~1200 tokens)
  Output: 优化Meta (~150 tokens)

第3次（关键词）:
  Input: 500字文章 + 关键词Prompt (~1200 tokens)
  Output: 关键词列表 (~200 tokens)

第4次（FAQ）:
  Input: 500字文章 + FAQ Prompt (~1500 tokens)
  Output: 3个FAQ版本 (~1500 tokens)

总计:
  Input: 6900 tokens
  Output: 2650 tokens
  Total: 9550 tokens

成本 (Claude 3.5 Sonnet):
  Input: 6900 × $0.003/1K = $0.0207
  Output: 2650 × $0.015/1K = $0.0398
  Total: $0.0605/文章
```

#### 单次调用方案：
```
第1次（综合分析）:
  Input: 500字文章 + 综合Prompt (~3500 tokens)
  Output: 完整JSON结果 (~2800 tokens)

总计:
  Input: 3500 tokens
  Output: 2800 tokens
  Total: 6300 tokens

成本 (Claude 3.5 Sonnet):
  Input: 3500 × $0.003/1K = $0.0105
  Output: 2800 × $0.015/1K = $0.0420
  Total: $0.0525/文章
```

**节省**: $0.0080/文章 (13.2%) + 处理时间减少58%

### 5.2 大规模使用成本预估

| 每日文章量 | 多次调用成本 | 单次调用成本 | 每月节省 |
|-----------|------------|------------|---------|
| 10篇 | $18.15 | $15.75 | $72 |
| 50篇 | $90.75 | $78.75 | $360 |
| 100篇 | $181.50 | $157.50 | $720 |
| 500篇 | $907.50 | $787.50 | $3,600 |

### 5.3 性能对比

| 指标 | 多次调用 | 单次调用 | 改善 |
|-----|---------|---------|------|
| API请求次数 | 4次 | 1次 | -75% |
| 总延迟（串行） | ~6秒 | ~2.5秒 | -58% |
| Token使用 | 9,550 | 6,300 | -34% |
| 成本/文章 | $0.0605 | $0.0525 | -13% |
| 术语一致性 | ❌ 不保证 | ✅ 保证 | 质量提升 |

---

## 六、实施建议

### 6.1 开发步骤

1. **第一阶段：Prompt设计与测试**（1-2天）
   - 完善系统Prompt模板
   - 用真实文章测试输出质量
   - 调整JSON结构确保可解析
   - 验证术语一致性

2. **第二阶段：后端实现**（2-3天）
   - 实现 ProofreadingAnalysisService
   - 创建API端点
   - 数据库保存逻辑
   - 错误处理和重试机制

3. **第三阶段：前端集成**（2-3天）
   - API调用封装
   - UI组件开发
   - 加载状态和错误处理
   - 结果展示优化

4. **第四阶段：测试与优化**（2-3天）
   - 单元测试
   - 集成测试
   - 性能测试
   - 用户验收测试

### 6.2 风险与缓解

| 风险 | 缓解措施 |
|-----|---------|
| AI输出格式不稳定 | 1. 使用低温度(0.3) 2. Prompt中强调JSON格式 3. 多次测试验证 |
| 单次Token超限 | 1. 监控输入长度 2. 超长文章分段处理 3. 设置max_tokens=8192 |
| 解析JSON失败 | 1. 容错解析逻辑 2. 提取JSON代码块 3. 失败重试机制 |
| 处理时间过长 | 1. 异步处理 2. 前端显示进度 3. 超时重试 |

### 6.3 监控指标

需要监控的关键指标：
- 平均处理时间
- Token使用量
- API成功率
- JSON解析成功率
- 用户满意度（采纳建议的比例）
- 成本/文章

---

## 七、总结

### 优势确认

✅ **Token效率**: 节省34% token使用
✅ **成本降低**: 节省13%+ 直接成本
✅ **速度提升**: 处理时间减少58%
✅ **一致性保证**: 术语自动保持一致
✅ **开发简化**: 单一API端点，逻辑更清晰
✅ **维护便利**: Prompt集中管理，易于版本控制

### 关键成功因素

1. **Prompt质量**: 必须清晰、完整、结构化
2. **JSON格式**: 严格定义输出格式，便于解析
3. **错误处理**: 完善的容错和重试机制
4. **性能监控**: 持续监控优化效果

### 下一步行动

1. 审核并确认Prompt设计
2. 准备5-10篇真实文章作为测试数据
3. 开始后端服务实现
4. 逐步迭代优化

---

## 附录

### A. 完整规则列表（简版）

详细的450条规则见独立文档：`proofreading_rules_v3.0.0.md`

### B. 示例文章与输出

见独立文档：`analysis_examples.md`

### C. API文档

见独立文档：`api_reference.md`

---

**文档结束**
