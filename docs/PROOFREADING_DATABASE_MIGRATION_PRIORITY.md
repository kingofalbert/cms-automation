# 校对功能数据库迁移优先级分析

**创建日期**: 2025-11-02
**分析范围**: 校对系统优化的数据库支持需求
**目的**: 确定在UI实施前必须完成的数据库迁移任务

---

## 执行摘要

根据对 **FUTURE_DIRECTIONS.md** 和 **tasks.md** 的分析，校对功能优化需要以下数据库支持：

**🔴 高优先级（UI实施前必须完成）**:
- ✅ **Phase 7 - T7.1**: 校对决策与反馈数据库迁移（已规划）

**🟡 中优先级（功能迭代时实施）**:
- **Phase 8 - T8.5**: 规则管理数据库支持（建议新增）

**🟢 低优先级（长期优化）**:
- 性能优化索引
- 历史数据分区

---

## 1. 当前数据库现状

### 1.1 现有校对相关字段

**Article 模型** (`backend/src/models/article.py`):

```python
class Article(Base, TimestampMixin):
    # ... 其他字段 ...

    # 校对结果存储
    proofreading_issues: Mapped[List] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="Combined AI/script proofreading issues",
    )

    # 严重问题计数
    critical_issues_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of blocking (F-class) issues",
    )
```

**数据结构示例**:
```json
{
  "proofreading_issues": [
    {
      "rule_id": "A4-001",
      "type": "word_choice",
      "severity": "warning",
      "original": "趋之若鹜",
      "suggestion": "纷纷前往",
      "position": {"start": 45, "end": 49},
      "confidence": 0.95,
      "source": "deterministic"
    }
  ],
  "critical_issues_count": 0
}
```

### 1.2 缺失的数据库支持

❌ **用户决策记录表** - 不存在
❌ **规则管理表** - 不存在
❌ **反馈调优任务表** - 不存在
❌ **规则覆盖率统计表** - 不存在

---

## 2. Phase 7: 校对反馈系统数据库迁移 🔴

### 2.1 任务信息

**任务ID**: T7.1 [US2][P0] Proofreading 决策与反馈调优批次迁移

**来源**: `/specs/001-cms-automation/tasks.md:4073`

**预计工时**: 10 小时

**依赖**: T2A.5 ProofreadingAnalysisService（已完成）

**状态**: ⏸️ Not Started

### 2.2 需要创建的数据库表

#### 表 1: `proofreading_decisions` (校对决策表)

**用途**: 记录用户对每条校对建议的决策（接受/拒绝/修改）

**Schema**:
```sql
CREATE TABLE proofreading_decisions (
    id SERIAL PRIMARY KEY,

    -- 关联信息
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    suggestion_id VARCHAR(100) NOT NULL,  -- 对应 proofreading_issues 中的某条建议
    proofreading_history_id INTEGER,      -- 可选：关联到某次校对历史记录

    -- 决策信息
    decision_type VARCHAR(20) NOT NULL,   -- 'accepted' | 'rejected' | 'modified'
    decision_rationale TEXT,              -- 可选：决策理由
    modified_content TEXT,                -- 仅当 decision_type='modified' 时使用

    -- 反馈信息
    feedback_provided BOOLEAN DEFAULT FALSE,
    feedback_category VARCHAR(50),        -- 预设反馈类别
    feedback_notes TEXT,                  -- 用户自定义反馈
    feedback_status VARCHAR(20) DEFAULT 'pending',  -- 'pending' | 'in_progress' | 'completed' | 'failed'

    -- 规则相关
    rule_id VARCHAR(20) NOT NULL,         -- 触发的规则 ID
    rule_category VARCHAR(10),            -- A/B/C/D/E/F

    -- 审计字段
    decided_by INTEGER NOT NULL REFERENCES users(id),
    decided_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- 索引
    INDEX idx_article_id (article_id),
    INDEX idx_rule_id (rule_id),
    INDEX idx_feedback_status (feedback_status),
    INDEX idx_decided_at (decided_at),

    -- 唯一约束：同一文章的同一建议只能有一条决策
    UNIQUE (article_id, suggestion_id)
);
```

**重要字段说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `decision_type` | enum | ✅ | accepted（完全接受）/ rejected（拒绝）/ modified（修改后接受） |
| `feedback_status` | enum | ✅ | pending（待处理）/ in_progress（处理中）/ completed（已完成）/ failed（失败） |
| `feedback_provided` | boolean | ✅ | 是否提供了反馈（用于统计用户参与度） |
| `modified_content` | text | ❌ | 仅当用户修改建议后记录修改后的内容 |

#### 表 2: `feedback_tuning_jobs` (反馈调优任务表) - 可选

**用途**: 批量处理反馈数据，用于规则调优和AI prompt优化

**Schema**:
```sql
CREATE TABLE feedback_tuning_jobs (
    id SERIAL PRIMARY KEY,

    -- 任务信息
    job_type VARCHAR(30) NOT NULL,        -- 'rule_tuning' | 'prompt_optimization' | 'batch_analysis'
    target_rule_ids TEXT[],               -- 目标规则 ID 数组
    target_categories TEXT[],             -- 目标规则类别数组

    -- 处理范围
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    decision_count INTEGER DEFAULT 0,     -- 处理的决策数量

    -- 任务状态
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending' | 'running' | 'completed' | 'failed'
    progress_percent INTEGER DEFAULT 0,

    -- 结果
    results JSONB,                        -- 分析结果和建议
    error_message TEXT,

    -- 审计
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

#### 表 3: 扩展 `proofreading_history` (校对历史表)

**注意**: 此表可能不存在，需要检查当前数据库。如果不存在，建议创建：

```sql
CREATE TABLE proofreading_history (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,

    -- 校对执行信息
    executed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    execution_duration_ms INTEGER,

    -- 规则统计
    total_issues_found INTEGER DEFAULT 0,
    accepted_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    modified_count INTEGER DEFAULT 0,
    pending_count INTEGER DEFAULT 0,

    -- 反馈统计
    feedback_provided_count INTEGER DEFAULT 0,
    pending_feedback_count INTEGER DEFAULT 0,

    -- 分引擎统计
    deterministic_issues_count INTEGER DEFAULT 0,
    ai_issues_count INTEGER DEFAULT 0,

    -- 结果快照
    issues_snapshot JSONB,  -- 原始校对结果的快照

    INDEX idx_article_id (article_id),
    INDEX idx_executed_at (executed_at)
);
```

### 2.3 为什么必须在UI实施前完成？

**原因 1: 前端UI依赖这些表**

Phase 7的前端任务 **T7.4** (决策交互与反馈 UI) 需要调用以下API：

```typescript
// 前端需要的API接口
POST /api/v1/proofreading/decisions      // 提交决策
GET /api/v1/proofreading/decisions       // 查询决策历史
PATCH /api/v1/proofreading/decisions/{id}/feedback-status  // 更新反馈状态
```

这些API全部依赖 `proofreading_decisions` 表。

**原因 2: 数据完整性**

如果先实施UI，用户开始使用校对功能，但决策数据无法保存：
- ❌ 用户决策丢失
- ❌ 无法追踪规则有效性
- ❌ 无法进行后续的规则优化

**原因 3: 后端API开发顺序**

根据tasks.md，后端开发顺序为：
```
T7.1 数据库迁移 → T7.2 决策写入服务 → T7.3 决策 API → T7.4 前端 UI
```

如果跳过T7.1直接实施UI，会导致前端无法正常工作。

### 2.4 迁移实施计划

**Step 1: 创建 Alembic 迁移脚本** (3小时)

```bash
cd /Users/albertking/ES/cms_automation/backend
poetry run alembic revision -m "add_proofreading_decisions_and_feedback_tables"
```

**迁移文件内容**:
```python
# backend/migrations/versions/20251102_add_proofreading_decisions.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # 创建 proofreading_decisions 表
    op.create_table(
        'proofreading_decisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('suggestion_id', sa.String(100), nullable=False),
        sa.Column('proofreading_history_id', sa.Integer(), nullable=True),
        sa.Column('decision_type', sa.String(20), nullable=False),
        sa.Column('decision_rationale', sa.Text(), nullable=True),
        sa.Column('modified_content', sa.Text(), nullable=True),
        sa.Column('feedback_provided', sa.Boolean(), server_default='false'),
        sa.Column('feedback_category', sa.String(50), nullable=True),
        sa.Column('feedback_notes', sa.Text(), nullable=True),
        sa.Column('feedback_status', sa.String(20), server_default='pending'),
        sa.Column('rule_id', sa.String(20), nullable=False),
        sa.Column('rule_category', sa.String(10), nullable=True),
        sa.Column('decided_by', sa.Integer(), nullable=False),
        sa.Column('decided_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('article_id', 'suggestion_id', name='uq_article_suggestion')
    )

    # 创建索引
    op.create_index('idx_proofreading_decisions_article_id', 'proofreading_decisions', ['article_id'])
    op.create_index('idx_proofreading_decisions_rule_id', 'proofreading_decisions', ['rule_id'])
    op.create_index('idx_proofreading_decisions_feedback_status', 'proofreading_decisions', ['feedback_status'])
    op.create_index('idx_proofreading_decisions_decided_at', 'proofreading_decisions', ['decided_at'])

    # 创建 feedback_tuning_jobs 表（可选）
    op.create_table(
        'feedback_tuning_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(30), nullable=False),
        sa.Column('target_rule_ids', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('target_categories', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('decision_count', sa.Integer(), server_default='0'),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('progress_percent', sa.Integer(), server_default='0'),
        sa.Column('results', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()')),
        sa.Column('started_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_feedback_tuning_jobs_status', 'feedback_tuning_jobs', ['status'])
    op.create_index('idx_feedback_tuning_jobs_created_at', 'feedback_tuning_jobs', ['created_at'])

    # 检查是否存在 proofreading_history 表，如果不存在则创建
    # （此处省略，需根据实际情况判断）

def downgrade():
    op.drop_index('idx_feedback_tuning_jobs_created_at', 'feedback_tuning_jobs')
    op.drop_index('idx_feedback_tuning_jobs_status', 'feedback_tuning_jobs')
    op.drop_table('feedback_tuning_jobs')

    op.drop_index('idx_proofreading_decisions_decided_at', 'proofreading_decisions')
    op.drop_index('idx_proofreading_decisions_feedback_status', 'proofreading_decisions')
    op.drop_index('idx_proofreading_decisions_rule_id', 'proofreading_decisions')
    op.drop_index('idx_proofreading_decisions_article_id', 'proofreading_decisions')
    op.drop_table('proofreading_decisions')
```

**Step 2: 创建 ORM 模型** (2小时)

```python
# backend/src/models/proofreading.py

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class DecisionType(str, PyEnum):
    """用户决策类型"""
    ACCEPTED = "accepted"      # 完全接受建议
    REJECTED = "rejected"      # 拒绝建议
    MODIFIED = "modified"      # 修改后接受


class FeedbackStatus(str, PyEnum):
    """反馈处理状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ProofreadingDecision(Base, TimestampMixin):
    """校对决策记录"""

    __tablename__ = "proofreading_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 关联
    article_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    suggestion_id: Mapped[str] = mapped_column(String(100), nullable=False)
    proofreading_history_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 决策
    decision_type: Mapped[DecisionType] = mapped_column(
        Enum(DecisionType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    decision_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    modified_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 反馈
    feedback_provided: Mapped[bool] = mapped_column(Boolean, default=False)
    feedback_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    feedback_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback_status: Mapped[FeedbackStatus] = mapped_column(
        Enum(FeedbackStatus, values_callable=lambda x: [e.value for e in x]),
        default=FeedbackStatus.PENDING,
        index=True,
    )

    # 规则
    rule_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    rule_category: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # 审计
    decided_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)

    # 关系
    article: Mapped["Article"] = relationship("Article", backref="proofreading_decisions")


class TuningJobType(str, PyEnum):
    """调优任务类型"""
    RULE_TUNING = "rule_tuning"
    PROMPT_OPTIMIZATION = "prompt_optimization"
    BATCH_ANALYSIS = "batch_analysis"


class TuningJobStatus(str, PyEnum):
    """调优任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FeedbackTuningJob(Base):
    """反馈调优任务"""

    __tablename__ = "feedback_tuning_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 任务信息
    job_type: Mapped[TuningJobType] = mapped_column(
        Enum(TuningJobType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    target_rule_ids: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    target_categories: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)

    # 处理范围
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    decision_count: Mapped[int] = mapped_column(Integer, default=0)

    # 状态
    status: Mapped[TuningJobStatus] = mapped_column(
        Enum(TuningJobStatus, values_callable=lambda x: [e.value for e in x]),
        default=TuningJobStatus.PENDING,
        index=True,
    )
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)

    # 结果
    results: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 审计
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
```

**Step 3: 更新模型 __init__.py** (15分钟)

```python
# backend/src/models/__init__.py

# ... 现有导入 ...
from src.models.proofreading import (
    DecisionType,
    FeedbackStatus,
    ProofreadingDecision,
    TuningJobType,
    TuningJobStatus,
    FeedbackTuningJob,
)
```

**Step 4: 运行迁移** (30分钟)

```bash
# 检查迁移脚本
poetry run alembic check

# 生成SQL预览
poetry run alembic upgrade head --sql

# 执行迁移（开发环境）
poetry run alembic upgrade head

# 验证表创建
poetry run python -c "
from src.models import ProofreadingDecision, FeedbackTuningJob
from src.config.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
print('Tables:', inspector.get_table_names())
print('proofreading_decisions columns:', [c['name'] for c in inspector.get_columns('proofreading_decisions')])
"
```

**Step 5: 创建测试** (2小时)

```python
# backend/tests/models/test_proofreading_models.py

import pytest
from datetime import datetime, date
from src.models.proofreading import (
    ProofreadingDecision,
    DecisionType,
    FeedbackStatus,
    FeedbackTuningJob,
    TuningJobType,
)

def test_create_proofreading_decision(db_session):
    decision = ProofreadingDecision(
        article_id=1,
        suggestion_id="sugg-001",
        decision_type=DecisionType.ACCEPTED,
        rule_id="A4-001",
        decided_by=1,
    )
    db_session.add(decision)
    db_session.commit()

    assert decision.id is not None
    assert decision.feedback_status == FeedbackStatus.PENDING
    assert decision.feedback_provided == False

# ... 更多测试
```

**Step 6: 文档更新** (2小时)

创建 `backend/docs/database_schema_updates.md` 文档说明新增表结构和使用方式。

### 2.5 验收标准

- [ ] 迁移脚本在空数据库上成功运行
- [ ] 迁移脚本在包含现有数据的数据库上成功运行
- [ ] Rollback功能测试通过
- [ ] ORM模型可以正确创建和查询记录
- [ ] 所有索引和外键约束正常工作
- [ ] 唯一约束 (article_id, suggestion_id) 正确阻止重复决策
- [ ] 单元测试覆盖率 ≥ 90%

---

## 3. Phase 8: 规则管理数据库支持 🟡

### 3.1 任务信息

**任务ID**: T8.5 [P3] Rule Management Backend & UI

**来源**: `/specs/001-cms-automation/tasks.md:4351`

**预计工时**: 120-160 hours (3-4 weeks)

**依赖**: T8.4 (实现缺失的高优先级规则)

**状态**: ⏸️ Not Started

### 3.2 问题分析

**当前问题**: T8.5任务描述中提到需要"Rule management REST API"和"Admin UI"，但**没有明确说明是否需要数据库表**。

**两种实现方案**:

#### 方案 A: 基于文件的规则管理（当前方案）

**优点**:
- ✅ 规则定义直接在代码中 (`rule_specs.py`)
- ✅ 版本控制容易（Git）
- ✅ 部署简单（代码即规则）
- ✅ 开发快速

**缺点**:
- ❌ 无法动态管理规则优先级
- ❌ 无法追踪规则变更历史
- ❌ 无法支持A/B测试
- ❌ 管理界面功能受限

**适用场景**: MVP阶段，规则变更不频繁

#### 方案 B: 基于数据库的规则管理（建议方案）

**优点**:
- ✅ 支持动态启用/禁用规则
- ✅ 支持规则优先级调整
- ✅ 可追踪规则变更历史
- ✅ 支持A/B测试和灰度发布
- ✅ 管理界面功能丰富

**缺点**:
- ❌ 需要额外的数据库表
- ❌ 需要同步机制（DB ↔ 代码）
- ❌ 部署复杂度增加

**适用场景**: 生产环境，需要灵活管理规则

### 3.3 建议的数据库表设计

如果选择方案B，需要创建以下表：

#### 表 1: `proofreading_rules` (规则定义表)

```sql
CREATE TABLE proofreading_rules (
    id SERIAL PRIMARY KEY,

    -- 规则标识
    rule_id VARCHAR(20) NOT NULL UNIQUE,  -- 例如: A1-001
    catalog_rule_id VARCHAR(20),          -- 映射到 catalog.json

    -- 规则分类
    category VARCHAR(10) NOT NULL,        -- A/B/C/D/E/F
    subcategory VARCHAR(10),              -- A1/A2/B1/D1 等

    -- 规则内容
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    patterns JSONB,                       -- 匹配模式数组
    correction TEXT,                      -- 修正建议
    examples JSONB,                       -- 正确/错误示例

    -- 规则配置
    enabled BOOLEAN DEFAULT TRUE,         -- 是否启用
    priority INTEGER DEFAULT 100,         -- 优先级（数字越小越高）
    confidence REAL DEFAULT 0.9,          -- 置信度
    severity VARCHAR(20) DEFAULT 'warning',  -- 'critical' | 'warning' | 'info'

    -- 实现状态
    implementation_status VARCHAR(20) DEFAULT 'not_started',  -- 'implemented' | 'planned' | 'not_started'
    implemented_as VARCHAR(50),           -- 实现方式: 'deterministic' | 'ai' | 'hybrid'
    implementation_notes TEXT,

    -- 统计数据
    detection_count INTEGER DEFAULT 0,    -- 被触发次数
    accepted_count INTEGER DEFAULT 0,     -- 被接受次数
    rejected_count INTEGER DEFAULT 0,     -- 被拒绝次数
    effectiveness_rate REAL,              -- 有效率 (accepted/detected)

    -- 审计
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    last_modified_by INTEGER REFERENCES users(id),

    -- 索引
    INDEX idx_category (category),
    INDEX idx_enabled (enabled),
    INDEX idx_priority (priority),
    INDEX idx_implementation_status (implementation_status)
);
```

#### 表 2: `rule_change_history` (规则变更历史表)

```sql
CREATE TABLE rule_change_history (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(20) NOT NULL REFERENCES proofreading_rules(rule_id),

    -- 变更信息
    change_type VARCHAR(20) NOT NULL,     -- 'created' | 'updated' | 'disabled' | 'deleted'
    field_changed VARCHAR(50),            -- 哪个字段变更了
    old_value TEXT,
    new_value TEXT,
    change_reason TEXT,

    -- 审计
    changed_by INTEGER REFERENCES users(id),
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_rule_id (rule_id),
    INDEX idx_changed_at (changed_at)
);
```

#### 表 3: `rule_coverage_snapshots` (规则覆盖率快照表)

```sql
CREATE TABLE rule_coverage_snapshots (
    id SERIAL PRIMARY KEY,

    -- 快照时间
    snapshot_date DATE NOT NULL UNIQUE,

    -- 覆盖率统计
    total_planned_rules INTEGER NOT NULL,
    implemented_rules INTEGER NOT NULL,
    rule_objects_count INTEGER NOT NULL,
    detection_points_count INTEGER NOT NULL,
    coverage_percentage REAL,

    -- 分类统计
    category_stats JSONB,  -- 每个类别的详细统计

    -- 审计
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_snapshot_date (snapshot_date)
);
```

### 3.4 实施建议

**建议**: 在Phase 8实施前（约2-3个月后），再评估是否需要数据库支持。

**理由**:
1. **当前MVP阶段** - 方案A（基于文件）足够
2. **规则变更不频繁** - 大部分规则是稳定的
3. **开发效率** - 避免过早优化
4. **Phase 7优先** - T7.1的数据库迁移更紧急

**如果需要提前准备**:
- 在Phase 7迁移时，可以预留表结构
- 创建基础的CRUD API，但不立即使用
- 等到真正需要动态管理规则时再切换

---

## 4. 优先级总结与建议

### 4.1 数据库迁移优先级矩阵

| 任务 | 优先级 | 紧急度 | UI依赖 | 预计工时 | 建议时间 |
|------|--------|--------|--------|----------|----------|
| **T7.1 校对决策表** | 🔴 高 | 🔴 高 | ✅ 是 | 10h | **立即** |
| **T8.5 规则管理表** | 🟡 中 | 🟢 低 | ❌ 否 | 20h | 2-3个月后 |
| 性能优化索引 | 🟢 低 | 🟢 低 | ❌ 否 | 4h | 6个月后 |

### 4.2 明确建议

**在UI实施前必须完成**:

✅ **T7.1: Proofreading 决策与反馈调优批次迁移**
- **原因**: Phase 7的前端UI (T7.4) 直接依赖此数据库表
- **影响**: 不完成此迁移，前端无法保存用户决策
- **工时**: 10小时
- **紧急度**: 🔴 高

**可以延后实施**:

⏸️ **T8.5: Rule Management Backend & UI 数据库支持**
- **原因**:
  - 当前基于文件的规则管理已足够
  - 此任务依赖T8.4（实现缺失规则），还需4-6周
  - Phase 8整体优先级为 [P3]，属于未来工作
- **建议时机**: Phase 8实施时（预计2-3个月后）
- **工时**: 20小时（如需数据库支持）

### 4.3 实施时间线

```
Week 1 (当前)
├─ ✅ 修复后端依赖问题
├─ ✅ 启动Module 1 UI测试
└─ ⏸️ 准备T7.1数据库迁移设计

Week 2
├─ 🔴 实施T7.1数据库迁移
├─ 🔴 创建ORM模型和测试
└─ 🔴 运行迁移并验证

Week 3-4
├─ 实施T7.2 (决策写入服务)
├─ 实施T7.3 (决策API)
└─ 实施T7.4 (决策交互UI)

Week 16-17 (2-3个月后)
├─ 评估是否需要T8.5数据库支持
├─ 如需要，实施规则管理表
└─ 开发规则管理UI

```

---

## 5. 风险评估

### 5.1 不实施T7.1的风险

| 风险 | 影响 | 概率 | 严重性 |
|------|------|------|--------|
| 用户决策数据丢失 | 无法追踪规则有效性 | 🔴 高 | 🔴 严重 |
| 前端UI无法正常工作 | 阻塞Phase 7开发 | 🔴 高 | 🔴 严重 |
| 无法进行规则优化 | 影响产品迭代 | 🟡 中 | 🟡 中等 |
| 用户体验差 | 决策无反馈，不知道是否成功 | 🔴 高 | 🟡 中等 |

**结论**: **必须在UI实施前完成T7.1**

### 5.2 延后T8.5的风险

| 风险 | 影响 | 概率 | 严重性 |
|------|------|------|--------|
| 规则管理灵活性不足 | 需要代码变更才能调整规则 | 🟢 低 | 🟢 轻微 |
| 无法动态启用/禁用规则 | 需要重新部署 | 🟢 低 | 🟢 轻微 |
| A/B测试不便 | 增加测试成本 | 🟢 低 | 🟢 轻微 |

**结论**: **可以延后，风险可控**

---

## 6. 行动计划

### 6.1 立即行动（本周）

**优先级1**: 完成T7.1数据库迁移设计
- [ ] 详细设计三张表的Schema
- [ ] 评审Schema设计（与团队讨论）
- [ ] 准备迁移脚本草稿

**优先级2**: 修复后端环境问题
- [ ] 安装Playwright等缺失依赖
- [ ] 启动后端服务器并验证

### 6.2 下周行动

**实施T7.1数据库迁移**:
- [ ] 创建Alembic迁移脚本
- [ ] 创建ORM模型
- [ ] 编写单元测试
- [ ] 在开发环境运行迁移
- [ ] 验证所有功能正常

### 6.3 后续行动（2-4周内）

**实施T7.2-T7.4（依赖T7.1）**:
- 开发决策写入服务
- 开发决策API
- 开发前端决策交互UI

### 6.4 长期行动（2-3个月后）

**评估T8.5数据库需求**:
- 评估规则管理的实际需求
- 如需要，实施规则管理数据库表
- 否则，继续使用基于文件的方案

---

## 7. 总结

### 7.1 核心结论

**问题**: 针对校对功能，提出了一些有关后续优化所需的算法和规则的建议。优化规则的实施需要各种需求的支持，包括前端的需求，这些都需要有数据库的支持。请检查一下昨天安排的这方面的任务，是否有数据库的迁移方面应该在UI实施前优先实施的任务。

**答案**: **是的，有1个数据库迁移任务必须在UI实施前完成**：

✅ **T7.1: Proofreading 决策与反馈调优批次迁移**
- 创建 `proofreading_decisions` 表
- 创建 `feedback_tuning_jobs` 表（可选）
- 扩展 `proofreading_history` 表（如果存在）

**必须完成的原因**:
1. Phase 7的前端UI (T7.4) 直接依赖这些表
2. 用户决策数据需要持久化存储
3. 后续的规则优化依赖这些数据

**可以延后的任务**:
- T8.5 规则管理数据库支持（Phase 8，2-3个月后评估）

### 7.2 下一步行动

**推荐顺序**:
```
1. 修复后端环境（Playwright等依赖）         [本周]
2. 设计并实施T7.1数据库迁移                  [下周]
3. 继续Module 1 UI测试                       [下周]
4. 实施T7.2-T7.4（决策服务和UI）             [2-4周内]
5. 评估T8.5数据库需求                        [2-3个月后]
```

---

**文档版本**: 1.0
**最后更新**: 2025-11-02
**审核状态**: 待审核
**相关文档**:
- `/docs/FUTURE_DIRECTIONS.md`
- `/specs/001-cms-automation/tasks.md`
- `/backend/src/models/article.py`
