"""Generic pipeline task tracking model for async background jobs."""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class PipelineTaskStatus(str, PyEnum):
    """Pipeline task status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineTask(Base):
    """Generic task tracking for async pipeline operations.

    Replaces the in-memory _task_results dict in pipeline_routes.py
    so task state survives Cloud Run instance restarts and works
    across multiple instances.
    """

    __tablename__ = "pipeline_tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, comment="UUID task ID"
    )
    task_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Task type (auto_publish, worklist_sync, etc.)"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PipelineTaskStatus.PENDING.value,
        index=True, comment="Task status"
    )
    input: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Request payload"
    )
    result: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Success result payload"
    )
    error: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Error message on failure"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        comment="When task was created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(), comment="Last update timestamp"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When task finished"
    )

    __table_args__ = (
        Index("idx_pipeline_tasks_type_status", "task_type", "status"),
        Index("idx_pipeline_tasks_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<PipelineTask(id={self.id}, type={self.task_type}, status={self.status})>"
