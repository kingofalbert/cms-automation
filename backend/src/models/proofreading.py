"""Proofreading decision and feedback models."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class DecisionType(str, PyEnum):
    """用户决策类型."""

    ACCEPTED = "accepted"      # 完全接受建议
    REJECTED = "rejected"      # 拒绝建议
    MODIFIED = "modified"      # 修改后接受


class FeedbackStatus(str, PyEnum):
    """反馈处理状态."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TuningJobType(str, PyEnum):
    """调优任务类型."""

    RULE_TUNING = "rule_tuning"
    PROMPT_OPTIMIZATION = "prompt_optimization"
    BATCH_ANALYSIS = "batch_analysis"


class TuningJobStatus(str, PyEnum):
    """调优任务状态."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProofreadingHistory(Base):
    """校对执行历史记录."""

    __tablename__ = "proofreading_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 关联信息
    article_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联的文章ID",
    )

    # 执行信息
    executed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="执行时间",
    )
    execution_duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="执行耗时（毫秒）",
    )
    engine_version: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="引擎版本号",
    )

    # 问题统计
    total_issues_found: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="发现的问题总数",
    )
    critical_issues_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="严重问题数量",
    )
    warning_issues_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="警告问题数量",
    )
    info_issues_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="提示问题数量",
    )

    # 决策统计
    accepted_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="接受的建议数量",
    )
    rejected_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="拒绝的建议数量",
    )
    modified_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="修改的建议数量",
    )
    pending_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="待处理的建议数量",
    )

    # 反馈统计
    feedback_provided_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="提供反馈的数量",
    )
    pending_feedback_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="待处理反馈的数量",
    )

    # 分引擎统计
    deterministic_issues_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="确定性引擎发现的问题数",
    )
    ai_issues_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="AI引擎发现的问题数",
    )

    # 结果快照
    issues_snapshot: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="校对问题的完整快照",
    )
    config_snapshot: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="校对配置快照",
    )

    # 审计字段
    executed_by: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="执行者用户ID",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )

    # 关系
    article: Mapped["Article"] = relationship(
        "Article",
        back_populates="proofreading_histories"
    )
    decisions: Mapped[list["ProofreadingDecision"]] = relationship(
        "ProofreadingDecision",
        back_populates="history",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ProofreadingHistory("
            f"id={self.id}, "
            f"article_id={self.article_id}, "
            f"executed_at={self.executed_at}, "
            f"issues={self.total_issues_found})>"
        )

    def update_decision_stats(self) -> None:
        """更新决策统计数据."""
        self.accepted_count = sum(
            1 for d in self.decisions
            if d.decision_type == DecisionType.ACCEPTED
        )
        self.rejected_count = sum(
            1 for d in self.decisions
            if d.decision_type == DecisionType.REJECTED
        )
        self.modified_count = sum(
            1 for d in self.decisions
            if d.decision_type == DecisionType.MODIFIED
        )
        self.pending_count = self.total_issues_found - (
            self.accepted_count + self.rejected_count + self.modified_count
        )

        # 更新反馈统计
        self.feedback_provided_count = sum(
            1 for d in self.decisions if d.feedback_provided
        )
        self.pending_feedback_count = sum(
            1 for d in self.decisions
            if d.feedback_provided and d.feedback_status == FeedbackStatus.PENDING
        )


class ProofreadingDecision(Base, TimestampMixin):
    """校对决策记录."""

    __tablename__ = "proofreading_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 关联信息
    article_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联的文章ID",
    )
    suggestion_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="建议的唯一标识符",
    )
    proofreading_history_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("proofreading_history.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联的校对历史ID",
    )

    # 决策核心数据
    decision_type: Mapped[DecisionType] = mapped_column(
        Enum(DecisionType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="决策类型",
    )
    decision_rationale: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="决策理由",
    )
    modified_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="修改后的内容",
    )

    # 原始建议信息（快照）
    original_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="原始文本",
    )
    suggested_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="建议文本",
    )
    rule_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="触发的规则ID",
    )
    rule_category: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="规则类别",
    )
    issue_position: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="问题位置信息",
    )

    # 反馈数据
    feedback_provided: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否提供了反馈",
    )
    feedback_category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="反馈类别",
    )
    feedback_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="反馈备注",
    )
    feedback_status: Mapped[FeedbackStatus] = mapped_column(
        Enum(FeedbackStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=FeedbackStatus.PENDING,
        index=True,
        comment="反馈状态",
    )

    # 审计字段
    decided_by: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="决策者用户ID",
    )
    decided_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="决策时间",
    )

    # 关系
    article: Mapped["Article"] = relationship(
        "Article",
        back_populates="proofreading_decisions"
    )
    history: Mapped[Optional["ProofreadingHistory"]] = relationship(
        "ProofreadingHistory",
        back_populates="decisions"
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ProofreadingDecision("
            f"id={self.id}, "
            f"article_id={self.article_id}, "
            f"suggestion_id={self.suggestion_id}, "
            f"decision={self.decision_type.value})>"
        )

    @property
    def is_accepted(self) -> bool:
        """检查是否接受建议."""
        return self.decision_type == DecisionType.ACCEPTED

    @property
    def is_rejected(self) -> bool:
        """检查是否拒绝建议."""
        return self.decision_type == DecisionType.REJECTED

    @property
    def is_modified(self) -> bool:
        """检查是否修改建议."""
        return self.decision_type == DecisionType.MODIFIED

    @property
    def has_feedback(self) -> bool:
        """检查是否有反馈."""
        return self.feedback_provided

    @property
    def feedback_pending(self) -> bool:
        """检查反馈是否待处理."""
        return self.has_feedback and self.feedback_status == FeedbackStatus.PENDING


class FeedbackTuningJob(Base):
    """反馈调优任务."""

    __tablename__ = "feedback_tuning_jobs"

    __table_args__ = (
        CheckConstraint(
            "progress_percent >= 0 AND progress_percent <= 100",
            name="chk_progress_percent"
        ),
        CheckConstraint(
            "end_date >= start_date",
            name="chk_date_range"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 任务定义
    job_type: Mapped[TuningJobType] = mapped_column(
        Enum(TuningJobType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="任务类型",
    )
    job_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="任务名称",
    )
    job_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="任务描述",
    )

    # 处理范围
    target_rule_ids: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text),
        nullable=True,
        comment="目标规则ID列表",
    )
    target_categories: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text),
        nullable=True,
        comment="目标规则类别列表",
    )
    start_date: Mapped[datetime] = mapped_column(
        Date,
        nullable=False,
        comment="开始日期",
    )
    end_date: Mapped[datetime] = mapped_column(
        Date,
        nullable=False,
        comment="结束日期",
    )

    # 处理统计
    total_decisions_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="总决策数量",
    )
    processed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="已处理数量",
    )

    # 任务状态
    status: Mapped[TuningJobStatus] = mapped_column(
        Enum(TuningJobStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TuningJobStatus.PENDING,
        index=True,
        comment="任务状态",
    )
    progress_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="进度百分比",
    )

    # 执行结果
    results: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="分析结果",
    )
    recommendations: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="优化建议",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="错误消息",
    )
    error_details: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="错误详情",
    )

    # 时间戳
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="创建者用户ID",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="创建时间",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="开始时间",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="完成时间",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<FeedbackTuningJob("
            f"id={self.id}, "
            f"type={self.job_type.value}, "
            f"status={self.status.value}, "
            f"progress={self.progress_percent}%)>"
        )

    @property
    def is_pending(self) -> bool:
        """检查是否待执行."""
        return self.status == TuningJobStatus.PENDING

    @property
    def is_running(self) -> bool:
        """检查是否执行中."""
        return self.status == TuningJobStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        """检查是否已完成."""
        return self.status == TuningJobStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """检查是否失败."""
        return self.status == TuningJobStatus.FAILED

    @property
    def duration_seconds(self) -> int | None:
        """计算执行时长（秒）."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None

    def update_progress(self, processed: int) -> None:
        """更新处理进度."""
        self.processed_count = processed
        if self.total_decisions_count > 0:
            self.progress_percent = min(
                100,
                int((processed / self.total_decisions_count) * 100)
            )

    def mark_started(self) -> None:
        """标记任务开始."""
        self.status = TuningJobStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self, results: dict, recommendations: dict) -> None:
        """标记任务完成."""
        self.status = TuningJobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percent = 100
        self.results = results
        self.recommendations = recommendations

    def mark_failed(self, error_message: str, error_details: dict | None = None) -> None:
        """标记任务失败."""
        self.status = TuningJobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_details = error_details or {}
