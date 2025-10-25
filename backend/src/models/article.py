"""Article model for generated content."""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class ArticleStatus(str, PyEnum):
    """Article workflow status."""

    DRAFT = "draft"
    IN_REVIEW = "in-review"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class Article(Base, TimestampMixin):
    """Generated article content."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Content
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Article headline",
    )
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full article content (Markdown or HTML)",
    )

    # Status and workflow
    status: Mapped[ArticleStatus] = mapped_column(
        Enum(ArticleStatus),
        nullable=False,
        default=ArticleStatus.DRAFT,
        index=True,
        comment="Workflow status",
    )

    # Authorship
    author_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="User who initiated generation",
    )

    # CMS integration
    cms_article_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="CMS platform's article ID",
    )

    # Publishing
    published_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        index=True,
        comment="Actual publication timestamp",
    )

    # Metadata
    metadata: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="CMS-specific metadata (featured image, excerpt, etc.)",
    )
    formatting: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Formatting preferences (headings, lists, code blocks)",
    )

    # Relationships
    topic_request: Mapped["TopicRequest"] = relationship(
        "TopicRequest",
        back_populates="article",
        foreign_keys="TopicRequest.article_id",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Article(id={self.id}, status={self.status}, title='{self.title[:50]}...')>"

    @property
    def word_count(self) -> int:
        """Calculate approximate word count of article body."""
        return len(self.body.split())

    @property
    def is_published(self) -> bool:
        """Check if article is published."""
        return self.status == ArticleStatus.PUBLISHED and self.published_at is not None
