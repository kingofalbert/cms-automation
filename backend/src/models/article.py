"""Article model for generated content."""

from datetime import datetime
from enum import Enum as PyEnum

from typing import List, Optional

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class ArticleStatus(str, PyEnum):
    """Article workflow status."""

    IMPORTED = "imported"
    DRAFT = "draft"
    IN_REVIEW = "in-review"
    SEO_OPTIMIZED = "seo_optimized"
    READY_TO_PUBLISH = "ready_to_publish"
    PUBLISHING = "publishing"
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
        Enum(ArticleStatus, values_callable=lambda x: [e.value for e in x]),
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

    # Article source tracking
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
        index=True,
        comment="Article import source (csv_import, json_import, manual, wordpress_export)",
    )

    # Image management
    featured_image_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to featured image in storage",
    )

    additional_images: Mapped[Optional[List]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Array of additional image paths",
    )

    # WordPress taxonomy
    tags: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        default=list,
        comment="WordPress post tags (3-6 natural categories for internal navigation)",
    )

    categories: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        default=list,
        comment="WordPress post categories (hierarchical taxonomy)",
    )

    proofreading_issues: Mapped[List] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="Combined AI/script proofreading issues",
    )
    critical_issues_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of blocking (F-class) issues",
    )

    # CMS integration
    cms_article_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="CMS platform's article ID",
    )

    published_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        index=True,
        comment="Public URL after publishing to CMS",
    )

    # Publishing
    published_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        index=True,
        comment="Actual publication timestamp",
    )

    # Metadata
    article_metadata: Mapped[dict] = mapped_column(
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

    # SEO metadata (1:1 relationship)
    seo_metadata: Mapped[Optional["SEOMetadata"]] = relationship(
        "SEOMetadata",
        back_populates="article",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Publishing tasks (1:N relationship)
    publish_tasks: Mapped[List["PublishTask"]] = relationship(
        "PublishTask",
        back_populates="article",
        cascade="all, delete-orphan",
    )

    # Uploaded files (1:N relationship)
    uploaded_files: Mapped[List["UploadedFile"]] = relationship(
        "UploadedFile",
        back_populates="article",
        cascade="all, delete-orphan",
        foreign_keys="UploadedFile.article_id",
    )

    # Proofreading relationships (1:N)
    proofreading_histories: Mapped[List["ProofreadingHistory"]] = relationship(
        "ProofreadingHistory",
        back_populates="article",
        cascade="all, delete-orphan",
    )

    proofreading_decisions: Mapped[List["ProofreadingDecision"]] = relationship(
        "ProofreadingDecision",
        back_populates="article",
        cascade="all, delete-orphan",
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

    @property
    def has_seo(self) -> bool:
        """Check if article has SEO metadata."""
        return self.seo_metadata is not None

    @property
    def has_featured_image(self) -> bool:
        """Check if article has a featured image."""
        return self.featured_image_path is not None

    @property
    def image_count(self) -> int:
        """Count total images (featured + additional)."""
        count = 1 if self.featured_image_path else 0
        if self.additional_images:
            count += len(self.additional_images)
        return count

    @property
    def latest_publish_task(self) -> Optional["PublishTask"]:
        """Get the most recent publishing task."""
        if not self.publish_tasks:
            return None
        return max(self.publish_tasks, key=lambda t: t.created_at)

    @property
    def successful_publishes(self) -> int:
        """Count number of successful publishing tasks."""
        if not self.publish_tasks:
            return 0
        return sum(1 for task in self.publish_tasks if task.status == "completed")
