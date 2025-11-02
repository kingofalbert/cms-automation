# CMS自动化系统 - 文章校对功能需求文档

**版本:** 3.1.0
**创建日期:** 2025-10-26
**更新日期:** 2025-10-27
**参考标准:**
- 《大纪元、新唐人总部写作风格指南》(2023/11/08版)
- 《WordPress 上稿要求细节》

**v3.1.0 更新说明:**
- 实现方式更新为单一Prompt综合分析架构
- 详见 `single_prompt_design.md` 和 `article_proofreading_seo_workflow.md` v2.0

---

## 目录

- [1. 功能概述](#1-功能概述)
- [2. 校对规则分类](#2-校对规则分类)
- [3. 后端服务设计](#3-后端服务设计)
- [4. 数据结构定义](#4-数据结构定义)
- [5. API接口设计](#5-api接口设计)
- [6. 校对规则详细定义](#6-校对规则详细定义)
- [7. 实现优先级](#7-实现优先级)

---

## 1. 功能概述

### 1.1 目标

在AI生成文章后、SEO分析前，自动对文章内容进行规范化校对，确保：
- 用字统一准确
- 标点符号规范
- 数字格式正确
- 用词得体规范
- 译名统一标准
- **发布合规检查（图片规格、标题层级、版权授权等）**

### 1.2 工作流程

```
AI生成文章 → 语言校对 → 发布合规检查 → 修正/标注 → SEO分析 → 发布
```

### 1.3 核心功能

1. **自动检测**：识别文章中不符合规范的内容
2. **自动修正**：对明确的错误进行自动修正
3. **标注提示**：对需要人工判断的问题进行标注
4. **批量处理**：支持同时校对多篇文章
5. **规则配置**：支持启用/禁用特定校对规则
6. **发布前验证**：强制检查技术合规性，不满足则阻止发布

---

## 2. 校对规则分类

### 2.1 一级分类

| 分类ID | 分类名称 | 规则数量 | 优先级 | 说明 |
|--------|---------|---------|--------|------|
| A | 用字与用词 | ~200条 | 高 | 语言规范 |
| B | 标点符号 | ~50条 | 高 | 语言规范 |
| C | 数字用法 | ~30条 | 中 | 语言规范 |
| D | 人名地名译名 | ~100条 | 中 | 语言规范 |
| E | 报导用词 | ~50条 | 高 | 语言规范 |
| **F** | **发布合规** | **~20条** | **极高** | **技术合规（强制）** |

**总规则数量：约450条**

### 2.2 二级分类

#### A. 用字与用词
- A1: 统一用字（正体/异体字选择）
- A2: 易混淆字（形似字、音近字）
- A3: 常见错字（错别字）
- A4: 报导用词（贬义词、网络用语、党文化用词）
- A5: 台湾/大陆常用词差异

#### B. 标点符号
- B1: 句末标点（句号、问号、感叹号）
- B2: 句内标点（逗号、顿号、分号）
- B3: 引号用法（位置、嵌套）
- B4: 括号用法（类型、位置）
- B5: 书名号用法
- B6: 全角/半角符号
- B7: 连接号（短横线、长横线、波浪线）
- B8: 省略号
- B9: 破折号

#### C. 数字用法
- C1: 阿拉伯数字场景
- C2: 中文数字场景
- C3: 分节号使用
- C4: 日期时间格式
- C5: 计量单位
- C6: 货币格式

#### D. 人名地名译名
- D1: 大陆译名标准
- D2: 原文名标注
- D3: 国家译名
- D4: 人名用字（里/裡、于/於等）

#### E. 报导用词规范
- E1: 禁用词（贬义词、粗俗词）
- E2: 替换词（网络流行语→规范用语）
- E3: 党文化用词替换
- E4: 敬称规范

#### **F. 发布合规检查（WordPress技术要求）**
- **F1: 图片规格与格式（强制）**
- **F2: 标题层级与SEO（强制）**
- **F3: 授权与版权合规（强制）**
- **F4: 后台操作规范**
- **F5: 上稿前检查清单**
- **F6: 机器可检规则**

---

## 3. 后端服务设计

### 3.1 服务架构

```
ProofreadingService (主服务)
│
├── RuleEngine (规则引擎)
│   ├── CharacterRuleEngine (用字规则 - A类)
│   ├── PunctuationRuleEngine (标点规则 - B类)
│   ├── NumberRuleEngine (数字规则 - C类)
│   ├── TranslationRuleEngine (译名规则 - D类)
│   ├── TermRuleEngine (用词规则 - E类)
│   └── ValidationRuleEngine (发布合规 - F类) ⭐新增
│
├── RuleLoader (规则加载器)
│   ├── JSONRuleLoader
│   └── DatabaseRuleLoader
│
├── ProofreadingResult (结果处理)
│   ├── AutoCorrection (自动修正)
│   ├── ManualReview (人工审核标注)
│   └── PublishBlocker (发布阻断) ⭐新增
│
└── ProofreadingCache (缓存层)
```

### 3.2 核心类设计

```python
# 1. 校对服务主类
class ProofreadingService:
    """文章校对服务"""

    def __init__(self):
        self.rule_engines: List[BaseRuleEngine] = []
        self.rule_loader: RuleLoader = None
        self.cache: ProofreadingCache = None

    async def proofread_article(
        self,
        article_id: int,
        content: str,
        config: ProofreadingConfig,
        article_metadata: Optional[ArticleMetadata] = None  # ⭐新增：用于F类规则
    ) -> ProofreadingResult:
        """校对单篇文章"""
        pass

    async def proofread_batch(
        self,
        articles: List[Dict],
        config: ProofreadingConfig
    ) -> List[ProofreadingResult]:
        """批量校对文章"""
        pass

    async def validate_publish_ready(
        self,
        article_id: int,
        article_metadata: ArticleMetadata
    ) -> PublishValidationResult:
        """
        ⭐新增：发布前强制验证
        检查F类规则，确保满足发布条件
        """
        pass


# 2. 规则引擎基类
class BaseRuleEngine(ABC):
    """规则引擎基类"""

    @abstractmethod
    async def check(self, text: str, context: Optional[Dict] = None) -> List[ProofreadingIssue]:
        """检查文本并返回问题列表"""
        pass

    @abstractmethod
    async def auto_correct(self, text: str) -> str:
        """自动修正文本"""
        pass


# 3. ⭐新增：发布验证规则引擎
class ValidationRuleEngine(BaseRuleEngine):
    """
    发布合规验证引擎（F类规则）
    检查图片规格、标题层级、版权授权等技术要求
    """

    async def validate_featured_image(self, image_metadata: Dict) -> List[ValidationIssue]:
        """验证特色图片"""
        pass

    async def validate_article_images(self, images: List[Dict]) -> List[ValidationIssue]:
        """验证文章插图"""
        pass

    async def validate_heading_hierarchy(self, html_content: str) -> List[ValidationIssue]:
        """验证标题层级（仅H2/H3）"""
        pass

    async def validate_copyright(self, media_items: List[Dict]) -> List[ValidationIssue]:
        """验证版权授权"""
        pass


# 4. 校对问题类
class ProofreadingIssue:
    """校对发现的问题"""

    rule_id: str              # 规则ID
    rule_category: str        # 规则分类 (A1, B2, F1, etc.)
    severity: str             # 严重程度 (critical/error/warning/info) ⭐新增critical级别
    position: Tuple[int, int] # 问题位置 (start, end)
    original_text: str        # 原始文本
    suggested_text: str       # 建议修正
    reason: str               # 问题说明
    can_auto_correct: bool    # 是否可自动修正
    confidence: float         # 置信度 (0-1)
    blocks_publish: bool = False  # ⭐新增：是否阻止发布（F类规则）


# 5. ⭐新增：发布验证结果
class PublishValidationResult:
    """发布前验证结果"""

    can_publish: bool                     # 是否可以发布
    validation_issues: List[ValidationIssue]  # 验证问题列表
    critical_issues: List[ValidationIssue]    # 阻止发布的严重问题
    warnings: List[ValidationIssue]           # 警告（不阻止发布）
    checklist_status: Dict[str, bool]         # 检查清单状态


# 6. 校对结果类
class ProofreadingResult:
    """校对结果"""

    article_id: int
    original_content: str
    corrected_content: str
    issues: List[ProofreadingIssue]
    auto_corrected_count: int
    manual_review_count: int
    statistics: Dict[str, int]
    processing_time: float
    publish_validation: Optional[PublishValidationResult] = None  # ⭐新增


# 7. ⭐新增：文章元数据（用于F类规则验证）
class ArticleMetadata(BaseModel):
    """文章元数据"""

    article_id: int
    title: str
    html_content: str  # 包含HTML标签的内容

    # 图片信息
    featured_image: Optional[ImageMetadata] = None
    article_images: List[ImageMetadata] = []

    # 社交媒体
    needs_social: bool = False
    social_images: Dict[str, ImageMetadata] = {}  # {"facebook_700_359": ImageMetadata}

    # 发布设置
    is_featured: bool = False  # 是否置顶
    publish_date: Optional[datetime] = None


class ImageMetadata(BaseModel):
    """图片元数据"""

    image_id: int
    file_path: str
    file_format: str  # jpg, jpeg, png, etc.
    width: int
    height: int
    file_size: int

    # 版权信息
    source: Optional[str] = None  # 来源
    photographer: Optional[str] = None  # 摄影者
    license_info: Optional[str] = None  # 授权信息
    license_expiry: Optional[datetime] = None

    # 裁剪信息
    has_crops: bool = False
    crop_versions: List[str] = []  # ["mobile", "tablet", "desktop"]

    # 特殊标记
    allow_png: bool = False
    allow_reason: Optional[str] = None
```

### 3.3 数据库表设计

#### 3.3.1 proofreading_rules 表（校对规则）

```sql
CREATE TABLE proofreading_rules (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(20) UNIQUE NOT NULL,  -- 如 A1-001, F1-001
    category VARCHAR(10) NOT NULL,         -- A1, B2, F1, etc.
    rule_type VARCHAR(30) NOT NULL,        -- character/punctuation/number/translation/term/validation ⭐新增validation
    name VARCHAR(200) NOT NULL,
    description TEXT,
    pattern TEXT,                          -- 正则表达式模式
    original_text VARCHAR(100),            -- 原始文本（字符替换规则）
    replacement_text VARCHAR(100),         -- 替换文本
    can_auto_correct BOOLEAN DEFAULT false,
    severity VARCHAR(20) DEFAULT 'warning', -- critical/error/warning/info ⭐新增critical
    priority INTEGER DEFAULT 50,           -- 优先级 1-100
    enabled BOOLEAN DEFAULT true,
    blocks_publish BOOLEAN DEFAULT false,  -- ⭐新增：是否阻止发布
    validation_function VARCHAR(100),      -- ⭐新增：验证函数名（F类规则）
    examples JSONB,                        -- 示例
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rules_category ON proofreading_rules(category);
CREATE INDEX idx_rules_enabled ON proofreading_rules(enabled);
CREATE INDEX idx_rules_blocks_publish ON proofreading_rules(blocks_publish);  -- ⭐新增
```

#### 3.3.2 proofreading_history 表（校对历史）

```sql
CREATE TABLE proofreading_history (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id),
    original_content TEXT,
    corrected_content TEXT,
    issues_found INTEGER DEFAULT 0,
    auto_corrected INTEGER DEFAULT 0,
    manual_review_needed INTEGER DEFAULT 0,
    processing_time FLOAT,
    issues_detail JSONB,               -- 详细问题列表
    statistics JSONB,                  -- 统计信息
    publish_validation JSONB,          -- ⭐新增：发布验证结果
    can_publish BOOLEAN DEFAULT true,  -- ⭐新增：是否可发布
    accepted_count INTEGER DEFAULT 0,  -- ⭐新增：用户接受的建议数
    rejected_count INTEGER DEFAULT 0,  -- ⭐新增：用户拒绝的建议数
    modified_count INTEGER DEFAULT 0,  -- ⭐新增：用户部分采纳的建议数
    pending_feedback_count INTEGER DEFAULT 0,   -- ⭐新增：待处理的反馈决策
    feedback_completed_count INTEGER DEFAULT 0, -- ⭐新增：已用于规则/Prompt 调优的决策
    last_feedback_processed_at TIMESTAMP,       -- ⭐新增：最近一次反馈处理时间
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_proofreading_article ON proofreading_history(article_id);
CREATE INDEX idx_proofreading_date ON proofreading_history(created_at);
CREATE INDEX idx_proofreading_can_publish ON proofreading_history(can_publish);  -- ⭐新增
CREATE INDEX idx_proofreading_feedback_pending ON proofreading_history(pending_feedback_count);
```

#### 3.3.3 proofreading_config 表（校对配置）

```sql
CREATE TABLE proofreading_config (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    enabled_rules JSONB,               -- 启用的规则ID列表
    auto_correct_enabled BOOLEAN DEFAULT true,
    confidence_threshold FLOAT DEFAULT 0.8,
    enforce_publish_validation BOOLEAN DEFAULT true,  -- ⭐新增：强制发布验证
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 3.3.4 proofreading_decisions 表（用户决策记录）

```sql
CREATE TABLE proofreading_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    history_id INTEGER REFERENCES proofreading_history(id) ON DELETE CASCADE,
    suggestion_id UUID NOT NULL,
    suggestion_type VARCHAR(30) NOT NULL,       -- proofreading/seo/tag/segmentation/other
    rule_id VARCHAR(20),
    original_text TEXT,
    suggested_text TEXT,
    final_text TEXT,
    decision VARCHAR(20) NOT NULL,              -- accepted/rejected/modified
    feedback_option_id INTEGER REFERENCES feedback_options(id),
    feedback_text TEXT,
    decided_by INTEGER REFERENCES users(id),
    decided_at TIMESTAMP DEFAULT NOW(),
    feedback_status VARCHAR(20) DEFAULT 'pending',     -- pending/in_progress/completed/failed
    feedback_processed_at TIMESTAMP,
    tuning_batch_id UUID,
    prompt_or_rule_version VARCHAR(50),
    metadata JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX idx_decisions_history ON proofreading_decisions(history_id);
CREATE INDEX idx_decisions_suggestion ON proofreading_decisions(suggestion_id);
CREATE INDEX idx_decisions_feedback_status ON proofreading_decisions(feedback_status, decided_at);
```

#### 3.3.5 feedback_tuning_jobs 表（可选，调优批次追踪）

```sql
CREATE TABLE feedback_tuning_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL,              -- e.g. prompt_iteration, script_rule_update
    status VARCHAR(20) NOT NULL,                -- pending/running/completed/failed
    target_version VARCHAR(50),
    payload JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT
);
```

---

## 4. 数据结构定义

### 4.1 配置模型

```python
class ProofreadingConfig(BaseModel):
    """校对配置"""

    # 基本配置
    enabled: bool = True
    auto_correct_enabled: bool = True
    confidence_threshold: float = 0.8

    # 规则配置
    enabled_categories: List[str] = ["A", "B", "C", "D", "E", "F"]  # ⭐新增"F"
    disabled_rules: List[str] = []

    # 处理选项
    skip_quoted_text: bool = False      # 跳过引用文本
    skip_code_blocks: bool = True       # 跳过代码块
    preserve_proper_nouns: bool = True  # 保留专有名词

    # 输出选项
    include_suggestions: bool = True
    include_examples: bool = False
    highlight_changes: bool = True

    # ⭐新增：发布验证配置
    enforce_publish_validation: bool = True  # 强制发布验证
    block_publish_on_critical: bool = True   # 遇到critical问题时阻止发布


class ProofreadingStatistics(BaseModel):
    """校对统计"""

    total_issues: int = 0
    by_category: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    auto_corrected: int = 0
    manual_review: int = 0
    critical_issues: int = 0  # ⭐新增
    blocks_publish: bool = False  # ⭐新增
    processing_time: float = 0.0
```

### 4.2 请求/响应模型

```python
class ProofreadingRequest(BaseModel):
    """校对请求"""

    article_id: Optional[int] = None
    content: str
    config: Optional[ProofreadingConfig] = None
    metadata: Optional[ArticleMetadata] = None  # ⭐新增：用于F类规则

    # 选项
    return_corrected: bool = True
    return_issues: bool = True
    apply_corrections: bool = False  # 是否直接应用修正
    validate_publish: bool = True    # ⭐新增：是否执行发布验证


class ProofreadingResponse(BaseModel):
    """校对响应"""

    success: bool
    article_id: Optional[int] = None
    original_content: str
    corrected_content: Optional[str] = None
    issues: List[ProofreadingIssue]
    statistics: ProofreadingStatistics
    processing_time: float
    warnings: List[str] = []
    publish_validation: Optional[PublishValidationResult] = None  # ⭐新增
    can_publish: bool = True  # ⭐新增
```

### 4.3 用户决策模型 ⭐新增

```python
class DecisionFeedbackStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class ProofreadingDecision(BaseModel):
    """用户对建议的决策记录"""

    decision_id: UUID
    history_id: int
    suggestion_id: UUID
    suggestion_type: str
    rule_id: Optional[str] = None
    original_text: str
    suggested_text: Optional[str] = None
    final_text: Optional[str] = None
    decision: Literal["accepted", "rejected", "modified"]
    feedback_option_id: Optional[int] = None
    feedback_text: Optional[str] = None
    decided_by: int
    decided_at: datetime
    feedback_status: DecisionFeedbackStatus = DecisionFeedbackStatus.pending
    feedback_processed_at: Optional[datetime] = None
    tuning_batch_id: Optional[UUID] = None
    prompt_or_rule_version: Optional[str] = None


class ProofreadingDecisionInput(BaseModel):
    """前端提交的单条决策"""

    suggestion_id: UUID
    suggestion_type: str
    decision: Literal["accepted", "rejected", "modified"]
    final_text: Optional[str] = None
    feedback_option_id: Optional[int] = None
    feedback_text: Optional[str] = None


class UserDecisionPayload(BaseModel):
    """批量提交用户决策"""

    history_id: int
    decisions: List[ProofreadingDecisionInput]
```

> **说明**：上述“反馈状态”字段用于跟踪客户反馈在内部“脚本/Prompt 调优”流程中的处理进度。系统并不会触发机器学习模型训练；而是在运营/语言质量团队审查拒绝原因后，更新 deterministic 规则或 Prompt。完成调优后，将 `feedback_status` 更新为 `completed` 并记录批次与版本。

---

## 5. API接口设计

### 5.1 RESTful API

#### 5.1.1 校对单篇文章

```
POST /api/v1/proofreading/check
```

**请求体:**
```json
{
  "article_id": 123,
  "content": "文章内容...",
  "metadata": {
    "article_id": 123,
    "title": "文章标题",
    "html_content": "<h2>小标题</h2><p>内容...</p>",
    "featured_image": {
      "image_id": 456,
      "file_path": "/uploads/image.jpg",
      "file_format": "jpg",
      "width": 1200,
      "height": 800,
      "source": "Getty Images",
      "photographer": "John Doe",
      "has_crops": true,
      "crop_versions": ["mobile", "tablet", "desktop"]
    },
    "article_images": [...],
    "needs_social": true,
    "is_featured": false
  },
  "config": {
    "auto_correct_enabled": true,
    "confidence_threshold": 0.8,
    "enabled_categories": ["A", "B", "C", "F"],
    "enforce_publish_validation": true
  },
  "return_corrected": true,
  "apply_corrections": false,
  "validate_publish": true
}
```

**响应:**
```json
{
  "success": true,
  "article_id": 123,
  "original_content": "原始内容...",
  "corrected_content": "修正后内容...",
  "issues": [
    {
      "rule_id": "A1-001",
      "rule_category": "A1",
      "severity": "warning",
      "position": [10, 12],
      "original_text": "錶",
      "suggested_text": "表",
      "reason": "电表、水表应使用'表'，手表应使用'錶'",
      "can_auto_correct": true,
      "confidence": 0.95,
      "blocks_publish": false
    },
    {
      "rule_id": "F1-001",
      "rule_category": "F1",
      "severity": "critical",
      "position": null,
      "original_text": null,
      "suggested_text": null,
      "reason": "特色图片宽高比不符合要求：当前1.2，要求>1.2（横图）",
      "can_auto_correct": false,
      "confidence": 1.0,
      "blocks_publish": true
    }
  ],
  "statistics": {
    "total_issues": 15,
    "by_category": {
      "A1": 8,
      "B2": 5,
      "C1": 2,
      "F1": 1
    },
    "by_severity": {
      "critical": 1,
      "error": 2,
      "warning": 10,
      "info": 2
    },
    "auto_corrected": 12,
    "manual_review": 3,
    "critical_issues": 1,
    "blocks_publish": true
  },
  "processing_time": 0.35,
  "publish_validation": {
    "can_publish": false,
    "validation_issues": [
      {
        "issue_type": "featured_image_ratio",
        "severity": "critical",
        "message": "特色图片宽高比不符合要求",
        "current_value": "1.2",
        "required_value": ">1.2",
        "fix_suggestion": "请裁剪图片或更换横图"
      }
    ],
    "critical_issues": [
      {...}
    ],
    "warnings": [],
    "checklist_status": {
      "featured_image_is_landscape": false,
      "featured_image_has_crops": true,
      "images_correct_format": true,
      "headings_h2_h3_only": true,
      "all_media_has_source": true,
      "social_media_ready": false
    }
  },
  "can_publish": false
}
```

#### 5.1.2 批量校对

```
POST /api/v1/proofreading/check-batch
```

**请求体:**
```json
{
  "articles": [
    {
      "article_id": 123,
      "content": "文章1内容...",
      "metadata": {...}
    },
    {
      "article_id": 124,
      "content": "文章2内容...",
      "metadata": {...}
    }
  ],
  "config": {
    "auto_correct_enabled": true,
    "enforce_publish_validation": true
  }
}
```

#### 5.1.3 发布前验证（⭐新增）

```
POST /api/v1/proofreading/validate-publish
```

**说明:** 专门用于发布前的强制验证，只执行F类规则检查

**请求体:**
```json
{
  "article_id": 123,
  "metadata": {
    "article_id": 123,
    "html_content": "...",
    "featured_image": {...},
    "article_images": [...],
    "needs_social": true,
    "is_featured": true
  }
}
```

**响应:**
```json
{
  "can_publish": false,
  "validation_issues": [...],
  "critical_issues": [...],
  "checklist_status": {...}
}
```

#### 5.1.4 获取校对规则

```
GET /api/v1/proofreading/rules?category=A1&enabled=true&blocks_publish=true
```

#### 5.1.5 更新校对配置

```
PUT /api/v1/proofreading/config
```

#### 5.1.6 获取校对历史

```
GET /api/v1/proofreading/history/{article_id}
```

#### 5.1.7 提交用户决策（⭐新增）

```
POST /api/v1/proofreading/decisions
```

**说明:** 批量提交同一 `history_id` 下的建议决策（接受/拒绝/部分采纳），用于记录用户反馈以支撑脚本/Prompt 调优。

**请求体:**
```json
{
  "history_id": 456,
  "decisions": [
    {
      "suggestion_id": "78c0f2d6-6d4a-4a7a-9d9d-8f2e1d8b5c01",
      "suggestion_type": "proofreading",
      "decision": "accepted"
    },
    {
      "suggestion_id": "a1b2c3d4-5566-7788-9900-aabbccddeeff",
      "suggestion_type": "seo",
      "decision": "rejected",
      "feedback_option_id": 3,
      "feedback_text": "关键词建议与文章主题不符",
      "final_text": "保留原句"
    }
  ]
}
```

**响应:**
```json
{
  "history_id": 456,
  "accepted_count": 12,
  "rejected_count": 3,
  "modified_count": 1,
  "pending_feedback_count": 4
}
```

#### 5.1.8 获取用户决策（⭐新增）

```
GET /api/v1/proofreading/decisions?history_id=456
```

**说明:** 返回指定历史记录下所有决策及反馈处理状态，供前端回显或运营查看。

**响应示例:**
```json
{
  "history_id": 456,
  "decisions": [
    {
      "decision_id": "f9c4c6d1-3b6a-4a8a-9012-0d9f7a6b5c3d",
      "suggestion_id": "78c0f2d6-6d4a-4a7a-9d9d-8f2e1d8b5c01",
      "suggestion_type": "proofreading",
      "decision": "accepted",
      "feedback_status": "completed",
      "feedback_processed_at": "2025-11-12T03:12:45Z",
      "prompt_or_rule_version": "proofread-prompt-v12"
    }
  ]
}
```

---

## 6. 校对规则详细定义

### 6.1 A类：用字与用词规则

#### A1: 统一用字规则（共约50条）

##### A1-001: 表/錶
- **原文:** 錶
- **修正:** 表
- **应用场景:** 电表、水表
- **反例:** 手錶（应保持）
- **置信度:** 0.95
- **自动修正:** 是

##### A1-002: 并/併
- **原文:** 併
- **修正:** 并
- **应用场景:** 连接词
- **示例:** "经济并（不是併）不景气"
- **置信度:** 0.9
- **自动修正:** 是

##### A1-003: 布/佈
- **原文:** 佈
- **修正:** 布
- **应用场景:** 公布、宣布、遍布、分布、颁布
- **例外:** 佈道（保持）
- **置信度:** 0.9
- **自动修正:** 是

##### A1-004: 的/地/得
- **规则:**
  - 名词前用"的"（坚定的信念）
  - 动词前用"地"（踊跃地发问）
  - 动词后、副词/形容词前用"得"（跑得快、玩得很开心）
- **例外:** "似的"不改为"似地"
- **置信度:** 0.85（需要语法分析）
- **自动修正:** 部分可以

##### A1-005: 台/臺
- **原文:** 臺
- **修正:** 台
- **应用场景:** 台湾、舞台
- **说明:** 网站用台，报纸用臺
- **置信度:** 1.0（网站环境）
- **自动修正:** 是

##### A1-006: 裡/裏
- **统一使用:** 裡
- **应用场景:** 裡面
- **置信度:** 1.0
- **自动修正:** 是

##### A1-007: 里/裡（人名地名）
- **规则:** 人名地名翻译时用"里、禮"，不用"裡、裏"
- **示例:** 金里奇（不是金裡奇）
- **置信度:** 0.95
- **自动修正:** 需要命名实体识别

##### A1-008: 了解/瞭解
- **统一使用:** 了解、了然
- **说明:**
  - "了"：明白、懂得（与心有关）
  - "瞭"：与眼睛有关（简单明瞭、瞭望）
- **置信度:** 0.85
- **自动修正:** 部分可以

##### A1-009: 煉功/練功
- **规则:**
  - 煉法轮功法
  - 練其它功
  - 法轮功为"他"而非"它"
- **置信度:** 1.0
- **自动修正:** 是

##### A1-010: 占/佔
- **统一使用:** 占
- **应用场景:** 占据、占有、独占、侵占、占中
- **说明:** 法律统一用语
- **置信度:** 0.9
- **自动修正:** 是

**A1类还包括约40条类似规则...**

#### A2: 易混淆字规则（共约30条）

##### A2-001: 複/覆/復
- **複:** 重複、複雜、複合、繁複、複診、複習（重叠）
- **覆:** 反覆、回覆、覆核（翻转、回应）
- **復:** 復原、恢復、復合、康復（回到原样）
- **置信度:** 0.8（需要语义分析）
- **自动修正:** 部分可以

##### A2-002: 形/型
- **形:** 形象、形式、形態、體形（外表、form）
- **型:** 典型、類型、模型、體型、造型（样式、类型）
- **示例:**
  - 體形：身體、建築等的形狀
  - 體型：側重指比例，只指人或動物
- **置信度:** 0.75
- **自动修正:** 否（需人工判断）

##### A2-003: 遊/游
- **遊:** 遊行、遊覽、旅遊、遊艇、遊輪、導遊、交遊、遊刃有餘、遊說、遊手好閒、遊戲（与行走有关的消遣、娱乐、观赏景物或交往）
- **游:** 游泳、游資、游擊、氣若游絲、優游自在（与在水上的活动有关；飘荡不定）
- **置信度:** 0.85
- **自动修正:** 部分可以

##### A2-004: 它/牠/他
- **统一使用:** 它
- **说明:**
  - 台湾用"牠"指动物第三人称
  - 统一用"它"（非人的事物）
  - "他"只用于人（大法用此字）
- **置信度:** 0.9
- **自动修正:** 是

##### A2-005: 你/妳
- **统一使用:** 你
- **说明:** 台湾用"妳"指女性第二人称，统一用"你"
- **置信度:** 1.0
- **自动修正:** 是

**A2类还包括约25条类似规则...**

#### A3: 常见错字规则（共约40条）

##### A3-001: 關懷備至/關懷倍至
- **正确:** 備至
- **错误:** 倍至
- **说明:**
  - "備"：尽、皆，完全、非常
  - "倍"：更加
- **置信度:** 1.0
- **自动修正:** 是

##### A3-002: 可見一斑/可見一般
- **正确:** 一斑
- **错误:** 一般
- **说明:** 一斑指豹子身上的一个斑点
- **置信度:** 1.0
- **自动修正:** 是

##### A3-003: 按部就班/按步就班
- **正确:** 按部就班
- **错误:** 按步就班
- **说明:** 部、班原都是人事组织的单位
- **置信度:** 1.0
- **自动修正:** 是

##### A3-004: 莫名其妙/莫明其妙
- **正确:** 莫名其妙
- **错误:** 莫明其妙
- **说明:** 名：形容、以言语表达
- **置信度:** 1.0
- **自动修正:** 是

**A3类还包括约36条类似规则...**

#### A4: 报导用词规则（共约30条）

##### A4-001: 贬义词 - 趋之若鹜
- **问题:** 贬义词不当使用
- **说明:** 像成群的鸭子一样跑来跑去，带有冲动和盲从性
- **建议替换:** 纷纷前往、踊跃参加
- **严重程度:** warning
- **自动修正:** 否（需人工判断语境）

##### A4-002: 贬义词 - 蜂拥而至
- **问题:** 贬义词不当使用
- **说明:** 像蜜蜂一样聚集，带有冲动和盲从性
- **建议替换:** 纷纷到来、大批抵达
- **严重程度:** warning
- **自动修正:** 否

##### A4-003: 贬义词 - 粉墨登场
- **问题:** 贬义词不当使用
- **说明:** 在大陆已变为比喻坏人经过一番打扮公开亮相
- **建议替换:** 登台演出、亮相
- **严重程度:** warning
- **自动修正:** 否

##### A4-004: 不当用词 - 緋聞
- **问题:** 用词不当
- **说明:** 大陆指桃色新闻，即跟不伦关系有关的新闻
- **建议替换:** 传恋曲、谱恋曲
- **严重程度:** warning
- **自动修正:** 否

##### A4-005: 不当用词 - 聲稱/宣稱/稱
- **问题:** 含不认同之意
- **说明:** 含不认同此人所说之意；已证伪的传言可用"爆料称"
- **建议替换:** 表示、指出
- **严重程度:** warning
- **自动修正:** 否

##### A4-006: 网络流行语 - 吐槽
- **建议替换:** 调侃、挖苦、揶揄
- **严重程度:** info
- **自动修正:** 可以

##### A4-007: 网络流行语 - 同框
- **建议替换:** 合影、合照
- **严重程度:** info
- **自动修正:** 可以

##### A4-008: 网络流行语 - 劈腿
- **建议替换:** 移情别恋
- **严重程度:** info
- **自动修正:** 可以

##### A4-009: 网络流行语 - Po文
- **建议替换:** 发帖、发文
- **严重程度:** info
- **自动修正:** 可以

##### A4-010: 党文化用词 - 十一國慶長假
- **建议替换:** 十一長假
- **严重程度:** warning
- **自动修正:** 是

##### A4-011: 党文化用词 - 春節
- **建议替换:** 中國新年
- **严重程度:** warning
- **自动修正:** 是

##### A4-012: 党文化用词 - 陰曆/農曆
- **建议替换:** 黃曆、皇曆
- **严重程度:** warning
- **自动修正:** 是

##### A4-013: 党文化用词 - 和諧
- **建议替换:** 諧和、調協
- **严重程度:** warning
- **自动修正:** 可以

##### A4-014: 粗俗用词检测
- **检测词汇:** 老公（非直接引言不用）、土豪、壁咚、男神、女神、颜值等
- **严重程度:** warning
- **自动修正:** 否（需人工判断）

**A4类还包括约16条类似规则...**

### 6.2 B类：标点符号规则

#### B1: 句末标点规则（约5条）

##### B1-001: 句号缺失
- **检测:** 陈述句末尾缺少句号
- **修正:** 添加句号
- **例外:** 标题、图说（词组或人名时）
- **置信度:** 0.9
- **自动修正:** 是

##### B1-002: 图说句号
- **规则:** 图说中整句后要有句号；图说为词组或人名时，大陆习惯不加句号
- **置信度:** 0.95
- **自动修正:** 可配置

##### B1-003: 问号后不加句号
- **检测:** 问号后错误添加句号
- **修正:** 删除多余句号
- **置信度:** 1.0
- **自动修正:** 是

#### B2: 逗号规则（约8条）

##### B2-001: 逗号使用过多
- **检测:** 一句话连用超过4个逗号
- **建议:** 考虑拆分为多句或使用分号
- **严重程度:** info
- **自动修正:** 否

##### B2-002: 全角/半角逗号混用
- **检测:** 中文段落中使用半角逗号 `,`
- **修正:** 改为全角逗号 `，`
- **例外:**
  - 数字的千位分隔（2,000）
  - 英文之间（Houston, Texas）
- **置信度:** 0.95
- **自动修正:** 是

##### B2-003: 引言逗号位置
- **规则:** 直接引言句末若为逗号，则放在引号外
- **示例:**
  - 正确：美国总统川普表示，「------，------」，------。
  - 错误：美国总统川普表示，「------，------，」------。
- **置信度:** 0.85
- **自动修正:** 是

#### B3: 引号规则（约12条）

##### B3-001: 引号类型
- **外引号:** 「」
- **内引号:** 『』
- **英文单引号:** 'xxx'（注意转换后可能变成『』）
- **英文双引号:** "xxx"（不能用左右不分的"xxx"）
- **置信度:** 0.9
- **自动修正:** 是

##### B3-002: 引号嵌套
- **规则:** 在外引号「」里的引述要用『』
- **示例:** 他站起来问：「老师，『倒楣』的『楣』是什么意思？」
- **置信度:** 0.95
- **自动修正:** 是

##### B3-003: 完整句子引号内句号
- **规则:** 完整句子的句号要在引号内
- **示例:**
  - 正确：他表示：「XXXXXX。」
  - 错误：他表示：「XXXXXX」。
- **置信度:** 0.9
- **自动修正:** 是

##### B3-004: 部分引言引号外句号
- **规则:** 部分引言如果并非完整句，句末的逗号或句号应放在引号之外
- **示例:**
  - 正确：他表示，「------」，------。
  - 错误：他表示，「------。」，------。
- **置信度:** 0.85
- **自动修正:** 部分可以

##### B3-005: 连续引言标点
- **规则:** 同一个引述来源，连续两段以上引言，前面各段只加前引号，最后一段前后引号都加
- **示例:**
  ```
  他表示：
  「……，……。
  「……，……。
  「……，……。」
  ```
- **置信度:** 0.8
- **自动修正:** 是

##### B3-006: 专有名词引号
- **规则:**
  - 引述句子、专有名词如疫苗型号用「」
  - 网站、网络媒体或广播电视媒体名称的简称可用「」
- **示例:** 「六四」学生领袖、「4·25」万人上访、「希望之声」、「法广」
- **置信度:** 0.85
- **自动修正:** 否（需判断是否为专有名词）

#### B4: 顿号规则（约5条）

##### B4-001: 顿号基本用法
- **规则:** 连续短语之间用顿号
- **示例:**
  - 短语1、短语2和短语3
  - 短语1、短语2与短语3
  - 短语1、短语2或短语3
- **置信度:** 0.9
- **自动修正:** 部分可以

##### B4-002: 连接词前不用顿号
- **规则:** 以及、抑或、包括等词语前不用顿号
- **示例:** 短语1、短语2以及（抑或、包括）短语3
- **置信度:** 0.95
- **自动修正:** 是

##### B4-003: 书名号引号间不加顿号
- **规则:** 连续罗列的书名号和引号之间可不加顿号
- **置信度:** 0.9
- **自动修正:** 可配置

##### B4-004: 约数不加顿号
- **规则:** 二三十人、七八十年代不加顿号；70、80年代要加
- **置信度:** 0.95
- **自动修正:** 是

##### B4-005: 固定词组不加顿号
- **规则:** 约定俗成连为一体的词语不要套用顿号
- **示例:** 习江斗、习马会（不加顿号）
- **置信度:** 0.8
- **自动修正:** 否（需要词典支持）

#### B5: 括号规则（约6条）

##### B5-001: 圆括号用法
- **规则:** 用于补充说明
- **中文段落:** 必须使用全角（）
- **英文段落:** 使用半角 ()
- **置信度:** 1.0
- **自动修正:** 是

##### B5-002: 方括号用法
- **规则:** 套用两重括号时，方形在外，圆形在内
- **示例:** [本文材料取自追查迫害法轮功国际组织（简称追查国际）。]
- **置信度:** 0.95
- **自动修正:** 是

##### B5-003: 六角括号用法
- **规则:** 用来标示公文编号中的发文年份，作者国籍、朝代等
- **示例:** 〔本文材料取自...〕
- **置信度:** 0.9
- **自动修正:** 否

##### B5-004: 括号内句号位置
- **规则:**
  - 括一个非独立语素，逗、句号在后括号之外
  - 括一整句话，句号在后括号内
- **置信度:** 0.85
- **自动修正:** 是

#### B6: 书名号规则（约4条）

##### B6-001: 双书名号用法
- **规则:** 纸质媒体名及作品名用《》
- **适用:** 书名、篇章、歌曲名、影剧名、影视广播节目及栏目名、文件名、字画名等
- **示例:** 《大纪元时报》、《九评共产党》、《人民日报》
- **置信度:** 0.9
- **自动修正:** 部分可以

##### B6-002: 单书名号用法
- **规则:** 〈〉仅套在双书名号中使用
- **示例:** 《论屈原〈九歌〉》
- **注意:** word符号栏里有，勿写成大于、小于号
- **置信度:** 1.0
- **自动修正:** 是

##### B6-003: 非纸质媒体不加书名号
- **规则:** 中央社、法新社、美联社等新闻通讯社，中广、法广、希望之声、新唐人电视台等非纸质媒体不加《》
- **置信度:** 0.95
- **自动修正:** 否（需要媒体类型判断）

##### B6-004: 英文作品名翻译
- **规则:** 英文名字外不需加中文的书名号，可以将英文名字翻译成中文，再套书名号
- **置信度:** 0.8
- **自动修正:** 否

#### B7: 连接号规则（约4条）

##### B7-001: 短横线用法
- **符号:** −（减号）或 —（破折号的一半）
- **用途:** 连接西人的双名或复姓
- **示例:** 让−雅克·阿诺（Jean-Jacques Annaud）
- **置信度:** 0.95
- **自动修正:** 是

##### B7-002: 一字线用法
- **符号:** —
- **用途:** 时间地域起止
- **示例:**
  - 沈括（1031—1095）
  - 荷马（约前9世纪—前8世纪）
  - 上海—北京特快
- **置信度:** 0.95
- **自动修正:** 是

##### B7-003: 浪纹线用法
- **符号:** ～
- **用途:** 表示数值范围
- **示例:** 四～五寸高、第6～8章、10万～200万投资、54%～89%
- **注意:** 会产生歧义时，前面的亿、万、%、前等不可省略
- **置信度:** 0.9
- **自动修正:** 可以

##### B7-004: 中文语句不用半角短横
- **规则:** 中文语句里不用半角短横 `-`
- **修正:** 改为 `−` 或 `—`
- **置信度:** 1.0
- **自动修正:** 是

#### B8: 下圆点规则（约2条）

##### B8-001: 阿拉伯数字序号后用下圆点
- **规则:** 用于阿拉伯数字表示的项目符号，后空一格
- **示例:**
  ```
  1. 第一项；
  2. 第二项；
  3. 第三项。
  ```
- **注意:** 阿拉伯数字序号后勿用顿号
- **置信度:** 1.0
- **自动修正:** 是

##### B8-002: 西文名字略写
- **规则:** 前面的下点后不空格，最后一个略写后空半字
- **示例:** J.R.R. Tolkien
- **置信度:** 0.95
- **自动修正:** 是

#### B9: 间隔号规则（约3条）

##### B9-001: 外国人名间隔号
- **符号:** ·（中圆点）
- **用法:** 外国人名之间
- **示例:** 达·芬奇
- **注意:** 其它形式圆点显示非大即小，或会被转换成下圆点
- **置信度:** 1.0
- **自动修正:** 是

##### B9-002: 书名与篇章名间隔号
- **用法:** 书名与篇（章、卷）名之间的分界
- **示例:** 《三国志·蜀志·诸葛亮传》
- **置信度:** 0.95
- **自动修正:** 是

##### B9-003: 汉字时间事件间隔号
- **规则:**
  - 汉字时间命名事件，涉及1、11、12月者
  - 阿数时间命名的全部事件，中间有0者除外
- **示例:**
  - 一一·一○案件、一·二九运动（九一一事件）
  - 3·15国际消费者权益日、9·11、6·4事件
- **注意:** 610办公室、709大抓捕，均不加中圆点
- **置信度:** 0.9
- **自动修正:** 是

#### B10: 省略号规则（约3条）

##### B10-001: 省略号格式
- **符号:** ……（6个点）
- **输入:** shift+6
- **注意:**
  - 不要连打六个下圆点
  - 不要用英文半角的三个点
- **置信度:** 1.0
- **自动修正:** 是

##### B10-002: 省略号后不加句号
- **规则:** 省略号之前的句子应保留句号，省略号后不再加句号或逗号
- **置信度:** 1.0
- **自动修正:** 是

##### B10-003: 省略号与等等不同用
- **规则:** 「……」不要跟"等等"同时用
- **置信度:** 1.0
- **自动修正:** 是

#### B11: 破折号规则（约2条）

##### B11-001: 破折号格式
- **符号:** ——（两个全角）
- **输入:** shift + -（中文输入）
- **错误:** 不能使用 `--` 或 `─`
- **置信度:** 1.0
- **自动修正:** 是

#### B12: 冒号规则（约3条）

##### B12-001: 直接引言前冒号
- **规则:** 引述句子前使用冒号
- **示例:** 他说：「快一点！」
- **置信度:** 0.9
- **自动修正:** 可以

##### B12-002: 间接引言前不用冒号
- **规则:** 间接引言前一般无需使用冒号，多用逗号
- **示例:** 他表示「一定如此」。
- **置信度:** 0.85
- **自动修正:** 可以

##### B12-003: 比号用半角
- **符号:** :（半角冒号）
- **用途:** 比分、比例、钟点或小时
- **示例:** 1:5、20:30
- **注意:** 20:30后面不加「分」
- **置信度:** 1.0
- **自动修正:** 是

### 6.3 C类：数字用法规则

#### C1: 阿拉伯数字场景（约10条）

##### C1-001: 统计数据用阿数
- **适用:** 百分比、金额、人数、比数等
- **示例:** 80%、3.59%、6亿3,944万2,789元、639,442,789人、100万人、1:3
- **置信度:** 0.95
- **自动修正:** 是

##### C1-002: 计量值用阿数
- **适用:** 公制计量单位
- **示例:** 150公分、35公斤、30摄氏度、2万元、5角、35立方公尺、7.36公顷、土地1.5笔、15分钟、14页
- **置信度:** 0.95
- **自动修正:** 是

##### C1-003: 日期时间用阿数
- **格式:**
  - 日期：2024年10月26日（全球版用公历年）
  - 时间：7时50分、20:30
- **例外:** 地方新闻版可用民国年
- **置信度:** 1.0
- **自动修正:** 是

##### C1-004: 序数用阿数
- **示例:** 第4届第6会期、第6阶段、第1优先、第9名、第4季、第5会议室、第6次会议记录、第7组
- **置信度:** 0.95
- **自动修正:** 是

##### C1-005: 代码编号用阿数
- **示例:** ISBN 988-133-005-1、M234567890、附表（件）1、院台秘字第09300867号
- **置信度:** 1.0
- **自动修正:** 否

##### C1-006: 半角全角判断
- **规则:** 阿拉伯数字用半角，不用全角书写
- **示例:**
  - 正确：3月2日
  - 错误：３月２日
- **置信度:** 1.0
- **自动修正:** 是

##### C1-007: 分节号使用
- **规则:**
  - 仅四位数不分节不算错，文内统一即可
  - 五位数以上，每三位数必须加逗号分节
  - 一篇文章内如果四位和四位以上数字都有，应该统一加半角逗号
- **示例:** 2,000或2000、15,000、1,234,567
- **置信度:** 0.9
- **自动修正:** 可配置

##### C1-008: 六位以上数字建议
- **规则:** 六位以上非整数，最好以四位为一单位加万或亿字，以方便报纸排版
- **示例:**
  - 推荐：67万5,000、2亿零234万3,450
  - 也可：675,000、202,343,450
- **置信度:** 0.8
- **自动修正:** 可配置

##### C1-009: 五位整数建议
- **规则:** 推荐用数字加汉字
- **示例:** 1万、2万、1.5万元（15,000元）
- **置信度:** 0.8
- **自动修正:** 可配置

##### C1-010: 五位非整数
- **规则:** 中间不要加万字
- **示例:** 12,235（不写 1万2,235）
- **置信度:** 0.9
- **自动修正:** 可配置

#### C2: 中文数字场景（约8条）

##### C2-001: 描述性用语用汉字
- **示例:** 在两个重要场合、第二项、第三天、最后一个、上下五千年、两岸关系、三五成群
- **置信度:** 0.85
- **自动修正:** 部分可以

##### C2-002: 专有名词用汉字
- **适用:** 地名、书名、人名、店名、头衔等
- **示例:** 八国外长会议、六方会谈、九一八事变、六四事件、八丈长的布、三尺二寸
- **置信度:** 0.9
- **自动修正:** 否（需要命名实体识别）

##### C2-003: 成语用汉字
- **示例:** 接二连三、七上八下、七寸
- **置信度:** 1.0
- **自动修正:** 否（需要成语词典）

##### C2-004: 约数用汉字
- **示例:** 六千多人、约三百位、七八十年
- **注意:** 也可与相邻的前后文统一用阿数
- **置信度:** 0.8
- **自动修正:** 可配置

##### C2-005: 几字前数字用汉字
- **规则:** "几"字前的数字一定用汉字
- **示例:** 二十几岁
- **置信度:** 1.0
- **自动修正:** 是

##### C2-006: 整数1至10灵活处理
- **规则:** 可照顾到上下文，求得局部体例上的一致
- **示例:** 船难已造成6人死亡、32人受伤、二百多人失踪
- **置信度:** 0.7
- **自动修正:** 否

##### C2-007: 中国传统计量单位
- **规则:** 中国传统计量单位数值应用汉字
- **示例:** 身长五丈、六两银子
- **置信度:** 0.95
- **自动修正:** 是

##### C2-008: 非公历纪年用汉字
- **规则:** 非公历纪年一般使用汉字，后应括注公历纪年
- **示例:** 秦王政二十四年（公元前223年）
- **注意:** 生卒年如都是公元前，卒年之前的前字不可省略
- **置信度:** 0.95
- **自动修正:** 部分可以

#### C3: 货币格式规则（约3条）

##### C3-001: 货币数值用阿数
- **规则:** 货币数值用阿拉伯数字
- **示例:** 8,500万（美元）
- **置信度:** 1.0
- **自动修正:** 是

##### C3-002: 首次出现写清单位
- **规则:** 首次出现时应写清货币单位
- **示例:** 8,500万（美元，下同）
- **置信度:** 0.9
- **自动修正:** 否

##### C3-003: 非主流货币换算
- **规则:** 非美元、人民币的货币数值，应括注换算
- **示例:** XX新台币（约合XX美元）
- **置信度:** 0.85
- **自动修正:** 否（需要汇率API）

#### C4: 特殊数字规则（约3条）

##### C4-001: 四位整数
- **规则:** 内文中以数字处理，如：2,000、3,000，不写2千，3千；标题用数字和汉字都可以
- **置信度:** 0.9
- **自动修正:** 可配置

##### C4-002: 二至三位数字
- **规则:** 以阿拉伯数字表示
- **示例:** 235人、500人（不写5百人）
- **置信度:** 0.95
- **自动修正:** 是

##### C4-003: 非整数1至10
- **规则:** 可照顾到上下文，求得局部体例上的一致
- **置信度:** 0.7
- **自动修正:** 否

### 6.4 D类：人名地名译名规则

#### D1: 译名标准规则（约5条）

##### D1-001: 使用大陆译名
- **规则:** 人名、地名以大陆译名为准
- **示例:**
  - 奥巴马（不写作欧巴马）
  - 意大利（不写作义大利）
  - 基地组织（不写作盖达组织）
  - 戛纳影展（不写作坎城影展）
- **置信度:** 1.0
- **自动修正:** 需要译名词典

##### D1-001-exceptions: 特殊情况例外
- **例外:**
  - 工商宣传稿
  - 地方性新闻
  - 必须使用特殊译名的情况
- **规则:** 「类别重点」以上新闻，均使用大陆译名

##### D1-002: 原文名标注
- **规则:** 原文名只在首次出现时加括，后勿重复
- **示例:** 达·芬奇（Leonardo da Vinci）……后文直接用达·芬奇
- **注意:** 如导语字数有限放不下原文名，可放在后面首次出现处
- **置信度:** 0.9
- **自动修正:** 部分可以

##### D1-003: 名人不须括原文
- **规则:** 名人、大明星、元首及国名、货币、首都等不须括原文
- **置信度:** 0.85
- **自动修正:** 否（需要知名度判断）

##### D1-004: 原文拼写保留标记
- **规则:** 原文姓名拼写要保留字母上标（如è é ä）
- **注意:** 后台转换后不变成方块
- **示例:** 找不到时可拷贝带方块的西文字符整体搜索
- **置信度:** 0.9
- **自动修正:** 否

##### D1-005: 中央社新闻特殊处理
- **规则:**
  - 内文台湾译名的姓名间加中圆点
  - 后括注原文和大陆译名
  - 标题用大陆译名
- **示例:** 杰布‧布殊（Jeb Bush，陆译布什）
- **置信度:** 0.9
- **自动修正:** 需要来源判断

#### D2: 人名用字规则（约8条）

##### D2-001: 姓名用字-里/礼
- **规则:** 人名地名翻译时，用「里、礼」，不用「裡、裏」
- **原因:** 减少阅读时的误会
- **置信度:** 0.95
- **自动修正:** 需要命名实体识别

##### D2-002: 姓名用字-布
- **保持字形:** 布
- **示例:** 金里奇、布什
- **置信度:** 1.0
- **自动修正:** 需要译名词典

##### D2-003: 姓名用字-范（姓）
- **保持字形:** 范
- **示例:** 范德比尔特
- **置信度:** 1.0
- **自动修正:** 需要译名词典

##### D2-004: 姓名用字-松/藤
- **保持字形:** 松、藤
- **示例:** 藤原
- **置信度:** 1.0
- **自动修正:** 需要译名词典

##### D2-005: 姓名用字-于（姓）
- **保持字形:** 于
- **注意:** 於姓少见
- **示例:** 茅于轾（不是茅於轾）
- **置信度:** 0.95
- **自动修正:** 需要命名实体识别

##### D2-006: 姓名用字-游（姓）
- **保持字形:** 游
- **置信度:** 1.0
- **自动修正:** 需要命名实体识别

##### D2-007: 姓名用字-钟（姓）
- **保持字形:** 钟
- **置信度:** 1.0
- **自动修正:** 需要命名实体识别

##### D2-008: 宁/甯两姓
- **区别:**
  - 宁（二声）
  - 甯（四声）
- **置信度:** 0.9
- **自动修正:** 需要读音判断

#### D3: 地名译名规则（约3条）

##### D3-001: 郡与县区分
- **美国:** County译成县
- **英国和澳洲:** Shire译作郡
- **爱尔兰和挪威:** County译作郡（一级行政区）
- **置信度:** 1.0
- **自动修正:** 需要国家判断

##### D3-002: 地名翻译原则
- **规则:** 除神韵报导外，译名在七个汉字以内的地名应翻译
- **搜索不到:** 按照准确读音进行音节标准化音译
- **置信度:** 0.8
- **自动修正:** 否

##### D3-003: 国家译名标准
- **参考:** 附表：国家译名对照表（见文档末尾）
- **置信度:** 1.0
- **自动修正:** 需要国家译名词典

#### D4: 机构媒体名规则（约4条）

##### D4-001: 广为人知的外国机构
- **标题:** 优先使用中文略称，英文缩写也可使用
- **可用缩写:** UN、WHO、WTO、FIFA、NBA、CIA、FBI、BBC、CNN等
- **导言:** 宜出现完整中文名称（英文缩写）
- **示例:** 世界卫生组织（WHO）
- **置信度:** 0.9
- **自动修正:** 需要机构词典

##### D4-002: 一般外国机构缩写
- **规则:** 避免英文缩写入标
- **示例:** AAA（美国汽车协会）、WEF（世界经济论坛）
- **处理:** 文中第一次括注原文时，可先写英文全称
- **置信度:** 0.85
- **自动修正:** 否

##### D4-003: 外媒名称翻译
- **规则:** 应尽量翻译
- **示例:**
  - 《综艺》（Variety）杂志
  - 《名利场》（Vanity Fair，台译：浮华世界）杂志
- **注意:** 能对应到媒体名的，不用网站名
- **置信度:** 0.8
- **自动修正:** 需要媒体名词典

##### D4-004: 中文媒体名
- **规则:** 首次出现一般用全称
- **示例:** 新唐人电视台、法国广播电台、希望之声国际广播电台
- **后文简称:** 新唐人、法广、希望之声等
- **是否加引号:** 根据前后语境决定，以不产生歧义为准
- **置信度:** 0.9
- **自动修正:** 部分可以

### 6.5 E类：特殊规范规则

#### E1: 图片规范（约3条）

##### E1-001: 图片来源格式
- **规则:**
  - 全西文用半角符号和括号
  - 中文版权信息用全角
- **示例:**
  - (Fraser Harrison/Getty Images)
  - (AFP/Getty Images)
  - (Tom Blake/Flickr)
- **注意:** 首字要大写，摄影者前不加「摄影：」
- **置信度:** 1.0
- **自动修正:** 是

##### E1-002: 新唐人图片
- **规则:** 新唐人电视台的图片，不加「提供」，只写：（新唐人电视台）
- **置信度:** 1.0
- **自动修正:** 是

##### E1-003: 图说标点
- **规则:** 图说中整句后要有句号；图说为词组或人名时，大陆习惯不加句号
- **置信度:** 0.9
- **自动修正:** 可配置

#### E2: 法轮功相关规范（约2条）

##### E2-001: 大法用字
- **特殊用字:**
  - 煉功（不是練功）
  - 他（不是它）
- **其他用字:**
  - 暂时不改：部份、成度、的/地/得统一为的、决等
  - 除非本手册列出
- **置信度:** 1.0
- **自动修正:** 是

##### E2-002: 大法书籍写法
- **规则:** 不按大法书写法
- **示例:** 七·二○（我们写作7·20）
- **置信度:** 1.0
- **自动修正:** 否

#### E3: 年代表示（约2条）

##### E3-001: 年代简写处理
- **规则:** 89年，看语境及所指，应改为民国89年、2000年或1989年
- **注意:** 去年不用特别改为具体年份
- **置信度:** 0.7
- **自动修正:** 否（需要语境判断）

##### E3-002: 公元前纪年
- **规则:** 生卒年如都是公元前，卒年之前的前字不可省略
- **示例:** （公元前236—前183）
- **置信度:** 1.0
- **自动修正:** 是

---

## 6.6 F类：发布合规与呈现检查（⭐新增 - WordPress技术要求）

> **重要说明：** 本节为 CMS 上稿侧的**强制规范**，用于补足语言校对之外的「图片规格/封面裁剪/标题层级/授权合规/后台操作」要求。若与其他条款冲突，以本节为准（以利正确呈现与 SEO）。

> **参考标准：** 《WordPress 上稿要求细节》（2025-10-27）

### F1: 图片规格与格式（强制）

#### F1-001: 通用图片宽度规范
- **规则ID:** F1-001
- **严重程度:** critical
- **阻止发布:** 是
- **规则说明:**
  - 橫圖：**寬 600 px**
  - 方圖、竪圖：**寬 450 px**
  - 特例規格（版位/模組需要時）：橫/方 **寬 450 px**；竪圖 **寬 300 px**
- **验证方法:** 检查每张插图的宽度是否符合规范
- **错误提示:** "图片宽度不符合规范：当前{width}px，要求{required_width}px"
- **修复建议:** "请使用图片编辑工具调整图片宽度，或在WordPress后台裁剪图片"
- **置信度:** 1.0
- **可自动修正:** 否（需人工裁剪）

#### F1-002: 特色图片必须横图
- **规则ID:** F1-002
- **严重程度:** critical
- **阻止发布:** 是
- **规则说明:**
  - 封面/特色图片（Featured Image）**必须使用橫圖**
  - 宽高比要求：**width / height > 1.2**
  - **不得加白邊**
  - **避免大頭照**
- **验证方法:**
  ```python
  aspect_ratio = featured_image.width / featured_image.height
  if aspect_ratio <= 1.2:
      return ValidationIssue(...)
  ```
- **错误提示:** "特色图片不符合横图要求：当前宽高比{ratio}，要求>1.2"
- **修复建议:** "请更换为横向图片或裁剪当前图片"
- **置信度:** 1.0
- **可自动修正:** 否

#### F1-003: 特色图片裁剪要求
- **规则ID:** F1-003
- **严重程度:** critical
- **阻止发布:** 是
- **规则说明:**
  - 上傳特色圖片后，**務必逐一完成裁剪**（按各裝置/版位要求裁切）
  - 确保各列表頁與行動端不變形、不截斷主體
  - 必需的裁剪版本：mobile, tablet, desktop
- **验证方法:** 检查 `featured_image.has_crops` 和 `featured_image.crop_versions`
- **错误提示:** "特色图片缺少必需的裁剪版本：{missing_crops}"
- **修复建议:** "请在WordPress媒体库中为特色图片生成所有裁剪版本"
- **置信度:** 1.0
- **可自动修正:** 否

#### F1-004: 置顶文章图片分辨率要求
- **规则ID:** F1-004
- **严重程度:** error
- **阻止发布:** 是（如果文章标记为置顶）
- **规则说明:**
  - 置頂用圖（若用作置頂/主視覺）原圖建議 **不低於 700×400 px**
  - 确保在首页置顶位置显示清晰
- **验证方法:**
  ```python
  if article.is_featured:
      if featured_image.width < 700 or featured_image.height < 400:
          return ValidationIssue(...)
  ```
- **错误提示:** "置顶文章的特色图片分辨率不足：当前{width}×{height}，要求≥700×400"
- **修复建议:** "请上传更高分辨率的图片（至少700×400像素）"
- **置信度:** 1.0
- **可自动修正:** 否

#### F1-005: 图片格式统一JPG/JPEG
- **规则ID:** F1-005
- **严重程度:** warning
- **阻止发布:** 否（但强烈建议修正）
- **规则说明:**
  - 靜態圖一律使用 **JPG/JPEG**
  - **勿使用 PNG**（除非確有透明/特效需求並在備註說明）
- **验证方法:**
  ```python
  for image in article_images:
      if image.file_format.lower() == 'png':
          if not image.allow_png or not image.allow_reason:
              return ValidationIssue(...)
  ```
- **错误提示:** "图片使用PNG格式但未说明原因：{image_path}"
- **修复建议:** "请转换为JPG格式，或在图片元数据中标记allow_png=true并说明原因"
- **置信度:** 0.95
- **可自动修正:** 否

#### F1-006: 社交媒体推广图尺寸
- **规则ID:** F1-006
- **严重程度:** warning
- **阻止发布:** 否
- **规则说明:**
  - 如文章需社媒分享素材，請另備 **Facebook_700_359** 尺寸版本
  - 规格：700px × 359px
- **验证方法:**
  ```python
  if article.needs_social:
      if 'facebook_700_359' not in article.social_images:
          return ValidationIssue(...)
      else:
          fb_image = article.social_images['facebook_700_359']
          if fb_image.width != 700 or fb_image.height != 359:
              return ValidationIssue(...)
  ```
- **错误提示:** "文章需要社交媒体素材但缺少Facebook_700_359尺寸图片"
- **修复建议:** "请上传700×359像素的Facebook分享图片"
- **置信度:** 1.0
- **可自动修正:** 否

#### F1-007: 图片来源与图说
- **规则ID:** F1-007
- **严重程度:** warning
- **阻止发布:** 否
- **规则说明:**
  - 图片来源與圖說依照 E1 節之「圖片來源格式與圖說標點」處理
  - 同時需符合 F3 節「授權與合規」流程
- **参考规则:** E1-001, E1-002, E1-003, F3-001
- **置信度:** 0.9
- **可自动修正:** 否

#### F1-008: 上稿前图片质量检查
- **规则ID:** F1-008
- **严重程度:** critical
- **阻止发布:** 是
- **规则说明:**
  - 若圖片不符合像素與比例要求，應先行裁切或更換
  - **不可強行上稿**
- **综合验证:** 执行 F1-001 至 F1-006 的所有检查
- **错误提示:** "文章存在{count}个图片质量问题，必须修正后才能发布"
- **置信度:** 1.0
- **可自动修正:** 否

### F2: 标题层级与SEO（强制）

#### F2-001: 小标只能使用H2
- **规则ID:** F2-001
- **严重程度:** error
- **阻止发布:** 是
- **规则说明:**
  - 文章內 **小標一律使用 H2**
  - 其下級再使用 **H3**
  - 不允许使用 H1、H4、H5、H6
- **验证方法:**
  ```python
  import re
  from bs4 import BeautifulSoup

  soup = BeautifulSoup(html_content, 'html.parser')
  invalid_headings = soup.find_all(['h1', 'h4', 'h5', 'h6'])
  if invalid_headings:
      return ValidationIssue(...)
  ```
- **错误提示:** "文章使用了不允许的标题层级：{heading_tags}，只允许H2和H3"
- **修复建议:** "请将所有H1/H4/H5/H6标题修改为H2或H3"
- **置信度:** 1.0
- **可自动修正:** 可以（将H1/H4+转换为H2/H3）

#### F2-002: 禁止用加粗代替标题
- **规则ID:** F2-002
- **严重程度:** error
- **阻止发布:** 是
- **规则说明:**
  - **禁止**以僅加粗（bold）或放大字體替代標題層級
  - 必须使用 `<h2>` 和 `<h3>` HTML标签
  - 不能使用 `<strong>` 或 `<b>` 标签模拟标题
- **验证方法:**
  ```python
  # 检测疑似标题的加粗文本（独占一行且较短）
  suspicious_bolds = []
  for strong in soup.find_all(['strong', 'b']):
      text = strong.get_text().strip()
      parent = strong.parent
      # 如果加粗文本独占一段且长度<30字，可能是误用
      if parent.name == 'p' and len(parent.get_text().strip()) == len(text) and len(text) < 30:
          suspicious_bolds.append(text)
  ```
- **错误提示:** "检测到可能用加粗替代标题的文本：{text}"
- **修复建议:** "请将该文本修改为H2或H3标题"
- **置信度:** 0.8
- **可自动修正:** 否（需人工判断）

#### F2-003: 标题层级清晰
- **规则ID:** F2-003
- **严重程度:** warning
- **阻止发布:** 否
- **规则说明:**
  - 編輯時請檢查 HTML 結構，確保層級清晰
  - H3 必须在 H2 之后出现
  - 有助於**可讀性**與 **SEO**
- **验证方法:**
  ```python
  headings = soup.find_all(['h2', 'h3'])
  current_level = 2
  for heading in headings:
      level = int(heading.name[1])
      if level == 3 and current_level != 2:
          return ValidationIssue("H3出现时前面没有H2")
      current_level = level
  ```
- **错误提示:** "标题层级结构不清晰：H3出现在H2之前"
- **修复建议:** "请确保H3标题只出现在H2标题的下级"
- **置信度:** 0.9
- **可自动修正:** 否

### F3: 授权与版权合规（强制）

#### F3-001: 仅使用已授权素材
- **规则ID:** F3-001
- **严重程度:** critical
- **阻止发布:** 是
- **规则说明:**
  - **僅使用擁有明確授權**的圖片/影音素材
  - **嚴禁**未經許可擷取、盜鏈或使用來歷不明之素材
- **验证方法:**
  ```python
  for image in article_images + [featured_image]:
      if not image.license_info and not image.source:
          return ValidationIssue(...)
  ```
- **错误提示:** "图片缺少授权信息：{image_path}"
- **修复建议:** "请在后台填写图片来源和授权信息"
- **置信度:** 1.0
- **可自动修正:** 否

#### F3-002: 填写来源与摄影者
- **规则ID:** F3-002
- **严重程度:** critical
- **阻止发布:** 是
- **规则说明:**
  - 上稿前需在後台：
    - 上傳或關聯**授權憑證**（或記錄授權來源、授權條款/到期日）
    - 正確填寫 **來源/攝影者（或機構）** 欄位
  - 體例遵循 E1-001 等規範
- **验证方法:**
  ```python
  for image in article_images + [featured_image]:
      if not image.source and not image.photographer:
          return ValidationIssue(...)
  ```
- **错误提示:** "图片未填写来源或摄影者：{image_path}"
- **修复建议:** "请在WordPress媒体库中填写来源/摄影者字段"
- **置信度:** 1.0
- **可自动修正:** 否

#### F3-003: 合作方素材标示
- **规则ID:** F3-003
- **严重程度:** error
- **阻止发布:** 是
- **规则说明:**
  - 如為合作方（例：新唐人）之素材，請依既定寫法與授權約定標示
  - 参考：E1-002（新唐人图片）
- **验证方法:**
  ```python
  # 检查来源是否在合作方白名单中
  PARTNER_WHITELIST = ["新唐人电视台", "大纪元", "希望之声"]
  for image in article_images + [featured_image]:
      if image.source in PARTNER_WHITELIST:
          # 验证格式是否正确
          if not validate_partner_source_format(image.source):
              return ValidationIssue(...)
  ```
- **错误提示:** "合作方素材来源格式不正确：{source}"
- **修复建议:** "请按照规范格式填写：（新唐人电视台）"
- **置信度:** 1.0
- **可自动修正:** 可以

#### F3-004: 授权到期检查
- **规则ID:** F3-004
- **严重程度:** warning
- **阻止发布:** 可配置
- **规则说明:**
  - 检查素材授权是否到期
  - 任何疑義請暫緩發佈，先向版權管理窗口確認
- **验证方法:**
  ```python
  from datetime import datetime
  for image in article_images + [featured_image]:
      if image.license_expiry:
          if image.license_expiry < datetime.now():
              return ValidationIssue(...)
  ```
- **错误提示:** "图片授权已过期：{image_path}，到期日：{expiry_date}"
- **修复建议:** "请联系版权管理窗口更新授权或更换图片"
- **置信度:** 1.0
- **可自动修正:** 否

### F4: 后台操作与教材（强烈建议）

#### F4-001: 熟悉后台操作教材
- **规则ID:** F4-001
- **严重程度:** info
- **阻止发布:** 否
- **规则说明:**
  - 編輯/上稿人員應熟悉內部**後台操作教材**與**教學影片**
  - 連結見內部知識庫或《WordPress 上稿要求細節》附件清單
- **建议功能:**
  - 在后台工作流中提供：
    - 「查看最新圖片規格」快捷連結
    - 「查看標題層級示例」快捷連結
    - 「一鍵檢查」功能（執行 F 類所有規則）
- **置信度:** N/A
- **可自动修正:** N/A

### F5: 上稿前最终检查清单（Minimum-Ship Checklist）

#### F5-001: 发布前强制检查清单
- **规则ID:** F5-001
- **严重程度:** critical
- **阻止发布:** 是（任一项未通过）
- **检查清单:**
  - [ ] 特色圖為**橫圖**、**已完成各尺寸裁剪**、無白邊/無大頭照（F1-002, F1-003）
  - [ ] 置頂/主視覺用圖原始尺寸 **≥ 700×400 px**（如適用）（F1-004）
  - [ ] 文章插圖符合像素規範（橫600/方與竪450；特例：橫/方450，竪300）（F1-001）
  - [ ] **JPG/JPEG** 格式（除透明/特效必要情形且已說明）（F1-005）
  - [ ] 社群所需素材已備 **Facebook_700_359** 尺寸（如適用）（F1-006）
  - [ ] 內文小標皆為 **H2**；其下級為 **H3**；無以樣式冒充標題層級情形（F2-001, F2-002）
  - [ ] 所有媒體素材皆有**授權**；已在後台填寫來源/攝影者等欄位；引用體例正確（F3-001, F3-002）
  - [ ] 已查閱並遵循最新版後台操作教材/教學影片（F4-001）

**响应格式:**
```json
{
  "checklist_status": {
    "featured_image_is_landscape": true,
    "featured_image_has_crops": true,
    "featured_image_no_borders": true,
    "featured_image_resolution_adequate": true,
    "images_correct_width": false,  // ❌ 发现问题
    "images_correct_format": true,
    "social_media_ready": true,
    "headings_h2_h3_only": true,
    "no_bold_as_heading": true,
    "all_media_has_license": true,
    "all_media_has_source": true,
    "partner_sources_correct_format": true
  },
  "can_publish": false,  // 因为 images_correct_width = false
  "failed_checks": [
    {
      "check_name": "images_correct_width",
      "reason": "插图宽度不符合规范：image3.jpg 当前宽度800px，要求600px",
      "fix_suggestion": "请裁剪 image3.jpg 至宽度600px"
    }
  ]
}
```

### F6: 机器可检规则（供工具实现）

> **说明：** 供 CMS/CI 腳本或校對插件使用，未通過則阻止發佈（可在 PR/上稿流程做自動核查）。

#### F6-001: 特色图检查（自动化）
- **规则ID:** F6-001
- **验证逻辑:**
  ```python
  def validate_featured_image(featured_image: ImageMetadata) -> List[ValidationIssue]:
      issues = []

      # 1. 检查宽高比
      aspect_ratio = featured_image.width / featured_image.height
      if aspect_ratio <= 1.2:
          issues.append(ValidationIssue(
              issue_type="featured_image_ratio",
              severity="critical",
              message=f"特色图片宽高比不符合横图要求：当前{aspect_ratio:.2f}，要求>1.2",
              blocks_publish=True
          ))

      # 2. 检查文件格式
      if featured_image.file_format.lower() not in ['jpg', 'jpeg']:
          issues.append(ValidationIssue(
              issue_type="featured_image_format",
              severity="critical",
              message=f"特色图片格式必须为JPG/JPEG：当前{featured_image.file_format}",
              blocks_publish=True
          ))

      # 3. 检查裁剪版本
      required_crops = ['mobile', 'tablet', 'desktop']
      missing_crops = [c for c in required_crops if c not in featured_image.crop_versions]
      if missing_crops:
          issues.append(ValidationIssue(
              issue_type="featured_image_crops",
              severity="critical",
              message=f"特色图片缺少必需的裁剪版本：{', '.join(missing_crops)}",
              blocks_publish=True
          ))

      return issues
  ```

#### F6-002: 插图规格检查（自动化）
- **规则ID:** F6-002
- **验证逻辑:**
  ```python
  def validate_article_images(images: List[ImageMetadata]) -> List[ValidationIssue]:
      issues = []

      for idx, image in enumerate(images):
          # 1. 检查宽度规范
          width = image.width
          height = image.height
          aspect_ratio = width / height

          # 判断图片类型
          if aspect_ratio > 1.2:  # 横图
              required_width = 600
          elif 0.8 <= aspect_ratio <= 1.2:  # 方图
              required_width = 450
          else:  # 竖图
              required_width = 450

          if width != required_width:
              issues.append(ValidationIssue(
                  issue_type="image_width_incorrect",
                  severity="critical",
                  message=f"图片{idx+1}宽度不符：当前{width}px，要求{required_width}px",
                  blocks_publish=True
              ))

          # 2. 检查PNG使用
          if image.file_format.lower() == 'png':
              if not image.allow_png or not image.allow_reason:
                  issues.append(ValidationIssue(
                      issue_type="png_not_allowed",
                      severity="warning",
                      message=f"图片{idx+1}使用PNG格式但未说明原因",
                      blocks_publish=False
                  ))

      return issues
  ```

#### F6-003: 社群素材检查（自动化）
- **规则ID:** F6-003
- **验证逻辑:**
  ```python
  def validate_social_media(article: ArticleMetadata) -> List[ValidationIssue]:
      issues = []

      if article.needs_social:
          # 检查是否存在Facebook_700_359
          if 'facebook_700_359' not in article.social_images:
              issues.append(ValidationIssue(
                  issue_type="missing_social_media",
                  severity="warning",
                  message="文章需要社交媒体素材但缺少Facebook_700_359图片",
                  blocks_publish=False
              ))
          else:
              fb_image = article.social_images['facebook_700_359']
              if fb_image.width != 700 or fb_image.height != 359:
                  issues.append(ValidationIssue(
                      issue_type="social_media_size_incorrect",
                      severity="warning",
                      message=f"Facebook图片尺寸不正确：当前{fb_image.width}×{fb_image.height}，要求700×359",
                      blocks_publish=False
                  ))

      return issues
  ```

#### F6-004: 标题层级检查（自动化）
- **规则ID:** F6-004
- **验证逻辑:**
  ```python
  def validate_heading_hierarchy(html_content: str) -> List[ValidationIssue]:
      issues = []
      from bs4 import BeautifulSoup

      soup = BeautifulSoup(html_content, 'html.parser')

      # 1. 检查是否只有H2/H3
      invalid_headings = soup.find_all(['h1', 'h4', 'h5', 'h6'])
      if invalid_headings:
          heading_tags = [h.name for h in invalid_headings]
          issues.append(ValidationIssue(
              issue_type="invalid_heading_tags",
              severity="error",
              message=f"文章使用了不允许的标题层级：{', '.join(set(heading_tags))}",
              blocks_publish=True
          ))

      # 2. 检查是否用<strong>代替标题
      for strong in soup.find_all(['strong', 'b']):
          text = strong.get_text().strip()
          parent = strong.parent
          if parent.name == 'p' and len(parent.get_text().strip()) == len(text) and len(text) < 30:
              issues.append(ValidationIssue(
                  issue_type="bold_as_heading",
                  severity="error",
                  message=f"检测到可能用加粗替代标题的文本：{text}",
                  blocks_publish=True
              ))

      return issues
  ```

#### F6-005: 来源与授权检查（自动化）
- **规则ID:** F6-005
- **验证逻辑:**
  ```python
  def validate_copyright(media_items: List[ImageMetadata]) -> List[ValidationIssue]:
      issues = []

      PARTNER_WHITELIST = ["新唐人电视台", "大纪元", "希望之声", "Getty Images", "AFP"]

      for idx, media in enumerate(media_items):
          # 1. 检查是否有来源
          if not media.source and not media.photographer:
              issues.append(ValidationIssue(
                  issue_type="missing_source",
                  severity="critical",
                  message=f"媒体{idx+1}缺少来源或摄影者信息",
                  blocks_publish=True
              ))

          # 2. 检查合作方格式
          if media.source in PARTNER_WHITELIST:
              # 验证格式
              if media.source == "新唐人电视台":
                  expected_format = "（新唐人电视台）"
                  if media.source != expected_format:
                      issues.append(ValidationIssue(
                          issue_type="partner_source_format",
                          severity="warning",
                          message=f"合作方来源格式不规范：应为{expected_format}",
                          blocks_publish=False
                      ))

          # 3. 检查授权到期
          if media.license_expiry:
              from datetime import datetime
              if media.license_expiry < datetime.now():
                  issues.append(ValidationIssue(
                      issue_type="license_expired",
                      severity="error",
                      message=f"媒体{idx+1}授权已过期：{media.license_expiry}",
                      blocks_publish=True
                  ))

      return issues
  ```

#### F6-006: 发布阻断条件（自动化）
- **规则ID:** F6-006
- **验证逻辑:**
  ```python
  def can_publish(validation_result: PublishValidationResult) -> bool:
      """
      综合判断是否可以发布
      任一强制规则不满足则禁止发布，并给出明确错误讯息与修复建议
      """
      # 检查是否有critical级别的问题
      critical_issues = [
          issue for issue in validation_result.validation_issues
          if issue.severity == 'critical' and issue.blocks_publish
      ]

      if critical_issues:
          return False

      # 检查是否有error级别且阻止发布的问题
      blocking_errors = [
          issue for issue in validation_result.validation_issues
          if issue.severity == 'error' and issue.blocks_publish
      ]

      if blocking_errors:
          return False

      return True
  ```

---

## 7. 实现优先级

### 7.1 第一阶段（MVP - 最小可行产品）

**目标:** 实现基础校对功能，覆盖最常见、最明确的规则

#### 高优先级规则（约80条）
1. **A1类 - 统一用字**（30条）
   - 表/錶、并/併、布/佈、的/地/得等
   - 可以用简单字典映射实现
   - 错误率低，自动修正安全

2. **A3类 - 常见错字**（30条）
   - 備至/倍至、一斑/一般等
   - 简单字符串替换
   - 错误率低

3. **B2类 - 全角半角**（10条）
   - 中文段落标点必须全角
   - 简单正则检测

4. **C1类 - 基础数字规则**（10条）
   - 分节号、半角全角判断
   - 规则明确

**预计开发时间:** 1周

### 7.2 第二阶段（核心功能）

**目标:** 实现主要校对规则，提升准确性

#### 中优先级规则（约140条）
1. **A2类 - 易混淆字**（25条）
   - 需要语义分析，部分可自动修正

2. **A4类 - 报导用词**（30条）
   - 贬义词、网络用语、党文化用词检测

3. **B3类 - 引号规则**（12条）
   - 引号类型、嵌套、位置判断

4. **B5类 - 书名号规则**（4条）

5. **C2类 - 中文数字场景**（8条）

6. **D1类 - 译名标准**（5条，基础实现）

7. **⭐F1类 - 图片规格**（8条）
   - 图片宽度检查
   - 特色图片横图验证
   - 裁剪版本检查
   - 格式JPG/JPEG验证

8. **⭐F2类 - 标题层级**（3条）
   - H2/H3层级检查
   - 禁止加粗代替标题

**预计开发时间:** 2周

### 7.3 第三阶段（高级功能）

**目标:** 完善所有规则，提升智能化水平

#### 低优先级规则（约120条）
1. **A5类 - 台湾/大陆词差异**（动态配置）
2. **D类完整实现** - 译名规则（需要大型词典）
3. **E类特殊规范** - 图片、法轮功等
4. **智能语义判断** - 需要NLP技术
5. **⭐F3类 - 授权合规**（4条）
   - 授权信息验证
   - 来源摄影者检查
   - 合作方格式验证
   - 授权到期检查

**预计开发时间:** 3周

### 7.4 第四阶段（优化与扩展）

**目标:** 性能优化、用户体验提升

1. 缓存优化
2. 批量处理性能优化
3. 前端交互界面
4. 人工审核工作流
5. 规则管理后台
6. **⭐发布前强制验证流程**
7. **⭐CI/CD集成（自动阻断不合规发布）**

**预计开发时间:** 2周

### 7.5 文稿解析和版本管理（⭐新增 - v3.0.0）

**目标:** 实现文章三部分解析和多版本管理系统

#### 7.5.1 文稿格式解析

**功能需求:**
1. **三部分结构识别**
   - 正文内容（主体）
   - Meta描述（标记：`Meta描述:`）
   - SEO关键词（标记：`SEO关键词:`）

2. **固定标记检测**
   - 严格匹配固定标记（中文全角冒号）
   - 支持标记顺序灵活
   - 处理不完整文稿（缺少Meta或关键词）

3. **格式验证**
   - 检测格式异常并警告
   - 验证Meta长度（建议150-160字符）
   - 验证关键词数量（建议3-8个）

**相关文档:** 详见 `article_proofreading_seo_workflow.md` 第3节

**预计开发时间:** 3天

#### 7.5.2 三版本管理系统

**版本定义:**
1. **原始版本（Original）**
   - 用户输入的原始内容
   - 永久保存，不可修改
   - 包含：正文、Meta描述、SEO关键词

2. **建议版本（Suggested）**
   - AI校对和优化后的内容
   - 系统生成，不可修改
   - 包含：优化后的三部分 + 校对问题 + 段落建议 + FAQ Schema方案

3. **最终版本（Final）**
   - 用户审核确认的发布版本
   - 用户可编辑
   - 包含：最终三部分 + 用户选择记录 + FAQ Schema

**数据库扩展字段:**
```sql
-- 原始版本
original_content TEXT
original_meta_description TEXT
original_seo_keywords JSONB

-- 建议版本
suggested_content TEXT
suggested_meta_description TEXT
suggested_seo_keywords JSONB
paragraph_suggestions JSONB
faq_schema_proposals JSONB
proofreading_issues JSONB

-- 最终版本
final_content TEXT
final_meta_description TEXT
final_seo_keywords JSONB
final_faq_schema JSONB
user_accepted_suggestions JSONB
user_manual_edits JSONB
```

**相关文档:** 详见 `database_schema_updates.md`

**预计开发时间:** 1周

#### 7.5.3 版本状态机

**状态流转:**
```
pending → parsing → analyzing → suggested →
user_reviewing ↔ user_editing → confirmed →
publishing → published
```

**状态定义:**
- `pending`: 待处理
- `parsing`: 解析中
- `analyzing`: 校对分析中
- `suggested`: 已生成建议
- `user_reviewing`: 用户审核中
- `user_editing`: 用户编辑中
- `confirmed`: 已确认
- `publishing`: 发布中
- `published`: 已发布

**预计开发时间:** 2天

### 7.6 结构化数据生成（⭐新增 - v3.0.0）

**目标:** 实现FAQ Schema自动生成，提升SEO效果

#### 7.6.1 FAQ Schema生成器

**核心功能:**
1. **AI问题生成**
   - 基于5W1H原则（What, Who, When, Where, Why, How）
   - 分析用户搜索意图
   - 按重要性排序

2. **AI答案提取**
   - 从文章中提取相关段落
   - 概括和改写答案
   - 控制答案长度（50-400字）

3. **多方案生成**
   - 简洁版：3个问答
   - 标准版：5个问答
   - 详细版：7个问答

4. **Schema.org格式输出**
   - 生成标准JSON-LD格式
   - 符合Google Rich Results要求
   - 自动验证格式正确性

**相关文档:** 详见 `structured_data_faq_schema.md`

**预计开发时间:** 1周

#### 7.6.2 FAQ编辑器UI

**界面功能:**
1. **方案选择**
   - 单选：3问答/5问答/7问答/不使用
   - 方案对比视图
   - SEO评分显示

2. **问答编辑**
   - 逐项编辑问题和答案
   - 添加/删除问答
   - 调整顺序（拖拽）

3. **质量检查**
   - 实时字数统计
   - 质量评分显示
   - 优化建议提示

4. **JSON-LD预览**
   - 代码高亮显示
   - 一键复制
   - 在线验证链接

**相关文档:** 详见 `structured_data_faq_schema.md` 第6节

**预计开发时间:** 1周

#### 7.6.3 WordPress集成

**集成方式:**
1. **Post Meta存储**
   ```php
   add_post_meta($post_id, 'faq_schema', json_encode($faq_data));
   ```

2. **JSON-LD注入**
   - 在`<head>`标签中注入
   - 使用`application/ld+json`类型

3. **HTML展示（可选）**
   - 在文章末尾显示FAQ区块
   - 使用Accordion折叠样式
   - 移动端友好

**相关文档:** 详见 `structured_data_faq_schema.md` 第7节

**预计开发时间:** 3天

#### 7.6.4 SEO价值

**预期效果:**
- 搜索结果点击率提升：**25-35%**
- Featured Snippet展示率提升：**3-5倍**
- 移动搜索曝光率提升：**40%**
- 语音搜索覆盖率提升：**显著**

**相关文档:** 详见 `structured_data_faq_schema.md` 第3节

---

## 8. 技术实现建议

### 8.1 核心技术栈

```python
# 字符串处理
import re
from typing import List, Dict, Tuple, Optional

# 中文分词（用于语义分析）
import jieba

# HTML解析（⭐新增：用于F类规则）
from bs4 import BeautifulSoup

# 图片处理（⭐新增：用于F类规则）
from PIL import Image

# NLP（可选，用于高级语义判断）
from transformers import AutoTokenizer, AutoModel

# 数据库
from sqlalchemy.orm import Session
from sqlalchemy import select

# 缓存
import redis

# 日期时间（⭐新增：用于授权到期检查）
from datetime import datetime
```

### 8.2 规则存储方式

**方案1: JSON文件**（推荐用于开发阶段）
```json
{
  "rule_id": "A1-001",
  "category": "A1",
  "name": "表/錶统一",
  "pattern": "(?<![手錶])[電水].*錶",
  "replacement": {
    "from": "錶",
    "to": "表"
  },
  "can_auto_correct": true,
  "confidence": 0.95,
  "examples": [
    {
      "wrong": "電錶",
      "correct": "電表"
    }
  ]
}
```

**⭐新增：F类规则示例**
```json
{
  "rule_id": "F1-002",
  "category": "F1",
  "rule_type": "validation",
  "name": "特色图片必须横图",
  "description": "特色图片宽高比必须>1.2",
  "severity": "critical",
  "blocks_publish": true,
  "validation_function": "validate_featured_image_ratio",
  "can_auto_correct": false,
  "examples": [
    {
      "valid": {"width": 1200, "height": 800, "ratio": 1.5},
      "invalid": {"width": 800, "height": 800, "ratio": 1.0}
    }
  ]
}
```

**方案2: 数据库**（推荐用于生产环境）
- 灵活配置
- 支持动态启用/禁用
- 支持规则版本管理

### 8.3 处理流程

```python
async def proofread_article(
    content: str,
    config: ProofreadingConfig,
    metadata: Optional[ArticleMetadata] = None  # ⭐新增
):
    # 1. 预处理
    text = preprocess_text(content)

    # 2. 分段处理（避免跨段误判）
    paragraphs = split_paragraphs(text)

    all_issues = []
    corrected_text = text

    # 3. 语言校对（A-E类规则）
    for para in paragraphs:
        for engine in language_rule_engines:
            if engine.category in config.enabled_categories:
                issues = await engine.check(para)
                all_issues.extend(issues)

                # 4. 自动修正（如果启用且置信度足够）
                if config.auto_correct_enabled:
                    for issue in issues:
                        if issue.can_auto_correct and issue.confidence >= config.confidence_threshold:
                            corrected_text = apply_correction(corrected_text, issue)

    # ⭐5. 发布合规验证（F类规则）
    publish_validation = None
    if config.enforce_publish_validation and metadata:
        validation_engine = ValidationRuleEngine()
        publish_validation = await validation_engine.validate(metadata)
        all_issues.extend(publish_validation.validation_issues)

    # 6. 生成结果
    result = ProofreadingResult(
        original_content=content,
        corrected_content=corrected_text,
        issues=all_issues,
        statistics=calculate_statistics(all_issues),
        publish_validation=publish_validation,
        can_publish=publish_validation.can_publish if publish_validation else True
    )

    return result
```

### 8.4 性能优化建议

1. **规则缓存:** 将编译后的正则表达式缓存
2. **分批处理:** 长文章分段处理
3. **并行检测:** 多个规则引擎并行运行
4. **增量校对:** 只校对修改的部分
5. **索引优化:** 数据库查询优化
6. **⭐图片元数据缓存:** 避免重复读取图片信息
7. **⭐HTML解析缓存:** 缓存BeautifulSoup解析结果

### 8.5 测试策略

1. **单元测试:** 每个规则独立测试
2. **集成测试:** 完整文章校对测试
3. **性能测试:** 大批量文章处理
4. **准确性测试:** 对比人工校对结果
5. **⭐发布验证测试:** 测试各种不合规场景
6. **⭐阻断机制测试:** 验证发布阻断功能

---

## 9. 前端交互需求（待补充）

> 注：此部分待后续补充详细需求

### 9.1 基本交互

1. 文章编辑器集成
2. 实时标注问题位置
3. 一键修正功能
4. 问题列表展示

### 9.2 高级功能

1. 规则配置界面
2. 校对历史查看
3. 统计报表
4. 人工审核工作流

### 9.3 ⭐发布验证交互（新增）

1. **发布前检查界面**
   - 显示发布检查清单（F5-001）
   - 标记未通过的检查项
   - 提供修复建议和快捷操作

2. **发布阻断提示**
   - 清晰显示阻止发布的原因
   - 提供逐项修复指引
   - 修复后自动重新验证

3. **图片管理界面**
   - 批量查看图片规格
   - 一键裁剪功能
   - 授权信息快速填写

4. **标题层级可视化**
   - 显示文章大纲（H2/H3结构）
   - 高亮不符合规范的标题
   - 一键转换功能

---

## 10. 附录

### 10.1 国家译名对照表

| 英文 | 大陆标准 | 台湾 |
|------|---------|------|
| Azerbaijan | 阿塞拜疆 | 亚塞拜然 |
| Barbados | 巴巴多斯 | 巴贝多 |
| Belize | 伯利兹 | 贝里斯 |
| Benin | 贝宁 | 贝南 |
| Bermuda | 百慕大 | 百慕达 |
| Bosnia and Herzegovina | 波黑 | 波希尼亚及赫塞哥维那 |
| Botswana | 博茨瓦纳 | 波札那 |
| Burundi | 布隆迪 | 蒲隆地 |
| Cape Verde | 佛得角 | 维德角岛 |
| Chad | 乍得 | 查德 |
| Cook Islands | 库克群岛 | 科克群岛 |
| Costa Rica | 哥斯达黎加 | 哥斯大黎加 |
| Côte d'Ivoire | 科特迪瓦 | 象牙海岸 |
| Croatia | 克罗地亚 | 克罗埃西亚 |
| Eritrea | 厄立特里亚 | 厄利垂亚 |
| Ethiopia | 埃塞俄比亚 | 衣索匹亚 |
| Gabon | 加蓬 | 加彭 |
| Georgia | 格鲁吉亚 | 乔治亚 |
| Ghana | 加纳 | 迦纳 |
| Grenada | 格林纳达 | 格瑞那达 |
| Guatemala | 危地马拉 | 瓜地马拉 |
| Guyana | 圭亚那 | 盖亚那 |
| Maldives | 马尔代夫 | 马尔地夫 |
| Mali | 马里 | 马利 |
| Mauritania | 毛里塔尼亚 | 茅利塔尼亚 |
| Mauritius | 毛里求斯 | 模里西斯 |
| Nauru | 瑙鲁 | 诺鲁 |
| New Zealand | 新西兰 | 纽西兰 |
| Niger | 尼日尔 | 尼日 |
| Nigeria | 尼日利亚 | 奈及利亚 |
| Papua New Guinea | 巴布亚新几内亚 | 巴布亚纽几内亚 |
| Qatar | 卡塔尔 | 卡达 |
| Rwanda | 卢旺达 | 卢安达 |

### 10.2 参考资源

1. **中华民国教育部国语辞典:** https://dict.revised.moe.edu.tw/
2. **雅虎奇摩知识搜寻:** http://tw.search.yahoo.com/kp
3. **谷歌搜寻:** http://www.google.com.tw/
4. **标点符号特殊用法例析:** https://bit.ly/30GetL3
5. **正简体转换小贴士:** https://bit.ly/3xbJzGe
6. **大纪元英汉翻译风格指南:** 内部文档
7. **⭐《WordPress 上稿要求细节》:** 内部文档（2025-10-27）

---

**文档结束**

---

## 版本历史

### v3.0.0（2025-10-26）

**重大更新：文章校对+SEO优化完整工作流**

#### 新增功能
- ✅ **文稿格式解析**（7.5.1）
  - 三部分结构识别（正文、Meta描述、SEO关键词）
  - 固定标记检测（`Meta描述:` `SEO关键词:`）
  - 不完整文稿处理

- ✅ **三版本管理系统**（7.5.2）
  - 原始版本（Original）：永久保存用户输入
  - 建议版本（Suggested）：AI优化后的内容
  - 最终版本（Final）：用户确认的发布版本

- ✅ **版本状态机**（7.5.3）
  - 9个状态：pending → parsing → analyzing → suggested → user_reviewing ↔ user_editing → confirmed → publishing → published
  - 完整状态转换管理

- ✅ **FAQ Schema生成器**（7.6.1）
  - AI驱动的问答生成（基于5W1H原则）
  - 多方案生成（3/5/7问答）
  - Schema.org标准JSON-LD输出

- ✅ **FAQ编辑器UI**（7.6.2）
  - 方案选择和对比
  - 问答逐项编辑
  - 质量检查和JSON-LD预览

- ✅ **WordPress集成**（7.6.3）
  - Post Meta存储
  - JSON-LD自动注入
  - HTML FAQ区块展示

#### 数据库扩展
- 原始版本字段：`original_content`, `original_meta_description`, `original_seo_keywords`
- 建议版本字段：`suggested_content`, `suggested_meta_description`, `suggested_seo_keywords`, `paragraph_suggestions`, `faq_schema_proposals`, `proofreading_issues`
- 最终版本字段：`final_content`, `final_meta_description`, `final_seo_keywords`, `final_faq_schema`, `user_accepted_suggestions`, `user_manual_edits`
- 状态字段：`proofreading_status`

#### 配套文档
- 📄 `article_proofreading_seo_workflow.md`（3000行）- 完整工作流需求
- 📄 `structured_data_faq_schema.md`（800行）- FAQ Schema专项文档
- 📄 `database_schema_updates.md` - 数据库模型扩展说明

#### SEO价值预期
- 搜索结果点击率提升：**25-35%**
- Featured Snippet展示率提升：**3-5倍**
- 移动搜索曝光率提升：**40%**

---

### v2.0.0（2025-10-27）

**重大更新：发布合规与呈现检查**

#### 新增功能
- ✅ 新增 F 类规则：发布合规与呈现检查（20条规则）
- ✅ 更新规则分类：从 A-E 扩展到 A-F
- ✅ 更新总规则数：从约430条增加到约450条
- ✅ 新增 ValidationRuleEngine 发布验证引擎
- ✅ 新增 PublishValidationResult 发布验证结果模型
- ✅ 新增 ArticleMetadata 和 ImageMetadata 元数据模型

#### 系统增强
- ✅ 更新 API 设计：支持发布前强制验证
- ✅ 更新数据库表设计：支持发布阻断标记
- ✅ 更新实现优先级：将F类规则纳入第二和第三阶段
- ✅ 完全无遗漏地整合了v2版本的所有内容

---

**下一步行动:**
1. ✅ 完成v3.0.0需求文档集
2. 审核和批准需求文档
3. 开始后端服务开发：
   - ArticleParser（文稿解析器）
   - ProofreadingEngine（校对引擎）
   - FAQSchemaGenerator（FAQ生成器）
   - 三版本数据库模型
4. 开始前端UI开发：
   - 对比审核页面
   - FAQ编辑器
   - Diff高亮组件
5. 集成测试和优化
