"""TopicRequest model for article generation requests."""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class TopicRequestStatus(str, PyEnum):
    """TopicRequest processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TopicRequestPriority(str, PyEnum):
    """TopicRequest priority levels."""

    URGENT = "urgent"
    NORMAL = "normal"
    LOW = "low"


class TopicRequest(Base, TimestampMixin):
    """Article generation request from content manager."""

    __tablename__ = "topic_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Topic information
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Topic title",
    )
    outline: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional structured outline (JSON or Markdown)",
    )

    # Generation parameters
    style_tone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="professional",
        comment="Requested writing style",
    )
    target_word_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1000,
        comment="Desired article length",
    )
    priority: Mapped[TopicRequestPriority] = mapped_column(
        Enum(TopicRequestPriority, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TopicRequestPriority.NORMAL,
        comment="Processing priority",
    )

    # Tracking information
    submitted_by: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="User ID who submitted request",
    )
    status: Mapped[TopicRequestStatus] = mapped_column(
        Enum(TopicRequestStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TopicRequestStatus.PENDING,
        index=True,
        comment="Request processing status",
    )

    # Result tracking
    article_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("articles.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        comment="Foreign key to generated article",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error details if generation fails",
    )

    # Relationships
    article: Mapped["Article"] = relationship(
        "Article",
        back_populates="topic_request",
        foreign_keys=[article_id],
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<TopicRequest(id={self.id}, status={self.status}, title='{self.title[:50] if len(self.title) > 50 else self.title}')>"
