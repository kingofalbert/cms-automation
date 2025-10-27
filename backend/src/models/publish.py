"""Publishing task models for Computer Use automation."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, List, Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Provider(str, PyEnum):
    """Computer Use provider types."""

    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    PLAYWRIGHT = "playwright"


class TaskStatus(str, PyEnum):
    """Publishing task status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class LogLevel(str, PyEnum):
    """Execution log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class PublishTask(Base):
    """Publishing task record for Computer Use automation.

    Tracks the entire publishing workflow:
    - Provider selection (Anthropic, Gemini, Playwright)
    - Task execution status
    - Screenshots captured during publishing
    - Cost tracking
    - Retry logic

    One-to-many relationship with Article (an article can have multiple publish attempts).
    """

    __tablename__ = "publish_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign key to articles
    article_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to article",
    )

    # Task identification
    task_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        comment="Celery task ID for async tracking",
    )

    # Provider configuration
    provider: Mapped[Provider] = mapped_column(
        Enum(Provider, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=Provider.PLAYWRIGHT,
        index=True,
        comment="Computer Use provider (anthropic, gemini, playwright)",
    )

    cms_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="wordpress",
        comment="Target CMS type (wordpress, drupal, etc.)",
    )

    cms_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Target CMS URL",
    )

    # Task status and control
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True,
        comment="Task execution status",
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of retry attempts",
    )

    max_retries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="Maximum retry attempts allowed",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if task failed",
    )

    # Execution metadata
    session_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Computer Use session ID",
    )

    # Screenshots array: [{url: str, step: str, timestamp: str, description: str}]
    screenshots: Mapped[Optional[List]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Array of screenshot metadata {url, step, timestamp}",
    )

    cost_usd: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Cost in USD for this publishing task",
    )

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="When task execution started",
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="When task completed (success or failure)",
    )

    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total execution duration in seconds",
    )

    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="When task was created",
    )

    # Relationships
    article: Mapped["Article"] = relationship(
        "Article",
        back_populates="publish_tasks",
        foreign_keys=[article_id],
    )

    execution_logs: Mapped[List["ExecutionLog"]] = relationship(
        "ExecutionLog",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "retry_count <= max_retries",
            name="retry_count_check",
        ),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="duration_positive_check",
        ),
        CheckConstraint(
            "cost_usd IS NULL OR cost_usd >= 0",
            name="cost_positive_check",
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<PublishTask(id={self.id}, article_id={self.article_id}, "
            f"provider={self.provider}, status={self.status})>"
        )

    @property
    def is_complete(self) -> bool:
        """Check if task has completed (success or failure)."""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries

    @property
    def screenshot_count(self) -> int:
        """Count number of screenshots captured."""
        return len(self.screenshots) if self.screenshots else 0

    @property
    def is_free(self) -> bool:
        """Check if this task used a free provider (Playwright)."""
        return self.provider == Provider.PLAYWRIGHT

    def add_screenshot(
        self,
        url: str,
        step: str,
        description: Optional[str] = None,
    ) -> None:
        """Add a screenshot to the task.

        Args:
            url: URL or path to the screenshot
            step: Step name (e.g., "login", "editor_loaded", "published")
            description: Optional description of what the screenshot shows
        """
        if not self.screenshots:
            self.screenshots = []

        screenshot_data = {
            "url": url,
            "step": step,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if description:
            screenshot_data["description"] = description

        self.screenshots.append(screenshot_data)

    def mark_started(self) -> None:
        """Mark task as started (sets status and started_at)."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self, cost_usd: Optional[float] = None) -> None:
        """Mark task as completed successfully.

        Args:
            cost_usd: Optional cost in USD for the task
        """
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        if cost_usd is not None:
            self.cost_usd = cost_usd

    def mark_failed(self, error_message: str) -> None:
        """Mark task as failed with error message.

        Args:
            error_message: Description of the failure
        """
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())

    def increment_retry(self) -> None:
        """Increment retry counter (called before retry attempt)."""
        self.retry_count += 1
        self.status = TaskStatus.PENDING


class ExecutionLog(Base):
    """Execution log entry for detailed Computer Use tracking.

    Partitioned by month for performance (parent table with child partitions).
    Each log entry captures a single action or event during publishing.

    Many-to-one relationship with PublishTask.
    """

    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Foreign key to publish_tasks
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("publish_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to publish task",
    )

    # Log metadata
    log_level: Mapped[LogLevel] = mapped_column(
        Enum(LogLevel, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=LogLevel.INFO,
        index=True,
        comment="Log severity level",
    )

    step_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Publishing step name",
    )

    message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Log message",
    )

    # Structured details (JSONB for flexibility)
    details: Mapped[Optional[Dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Additional structured log data",
    )

    # Action tracking
    action_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Action type (navigate, click, type, upload, screenshot)",
    )

    action_target: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Target element (CSS selector, URL, etc.)",
    )

    action_result: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Action result (success, failed, timeout)",
    )

    screenshot_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Associated screenshot URL",
    )

    # Timestamp (primary key component for partitioning)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        index=True,
        primary_key=True,
        comment="When log entry was created (partition key)",
    )

    # Relationships
    task: Mapped["PublishTask"] = relationship(
        "PublishTask",
        back_populates="execution_logs",
        foreign_keys=[task_id],
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ExecutionLog(id={self.id}, task_id={self.task_id}, "
            f"level={self.log_level}, step='{self.step_name}')>"
        )

    @classmethod
    def create_log(
        cls,
        task_id: int,
        message: str,
        level: LogLevel = LogLevel.INFO,
        step_name: Optional[str] = None,
        action_type: Optional[str] = None,
        action_target: Optional[str] = None,
        action_result: Optional[str] = None,
        screenshot_url: Optional[str] = None,
        details: Optional[Dict] = None,
    ) -> "ExecutionLog":
        """Factory method to create a log entry.

        Args:
            task_id: ID of the publishing task
            message: Log message
            level: Log level (default: INFO)
            step_name: Publishing step name
            action_type: Type of action performed
            action_target: Target of the action
            action_result: Result of the action
            screenshot_url: URL of associated screenshot
            details: Additional structured data

        Returns:
            ExecutionLog instance
        """
        return cls(
            task_id=task_id,
            message=message,
            log_level=level,
            step_name=step_name,
            action_type=action_type,
            action_target=action_target,
            action_result=action_result,
            screenshot_url=screenshot_url,
            details=details or {},
        )
