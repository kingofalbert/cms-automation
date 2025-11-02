"""Worklist models for Google Drive integration."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

try:
    from sqlalchemy.dialects.postgresql import ARRAY, JSONB  # type: ignore
except ImportError:  # pragma: no cover - fallback when dialect missing
    JSONB = None
    ARRAY = None  # type: ignore

JSONType = JSONB if JSONB is not None else JSON


class WorklistStatus(str, PyEnum):
    """Workflow status for synced Drive articles."""

    TO_EVALUATE = "to_evaluate"
    TO_CONFIRM = "to_confirm"
    TO_REVIEW = "to_review"
    TO_REVISE = "to_revise"
    TO_REREVIEW = "to_rereview"
    READY_TO_PUBLISH = "ready_to_publish"
    PUBLISHED = "published"


class WorklistItem(Base, TimestampMixin):
    """Worklist queue item synced from Google Drive."""

    __tablename__ = "worklist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    drive_file_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Google Drive file identifier",
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Worklist document title",
    )
    status: Mapped[WorklistStatus] = mapped_column(
        Enum(WorklistStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=WorklistStatus.TO_EVALUATE,
        index=True,
        comment="Worklist processing status",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Document content (Markdown/HTML)",
    )
    author: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Document author",
    )

    # WordPress taxonomy (parsed from YAML front matter)
    tags: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)) if ARRAY is not None else JSONType,
        nullable=True,
        default=list,
        comment="WordPress post tags (3-6 categories for internal navigation)",
    )

    categories: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)) if ARRAY is not None else JSONType,
        nullable=True,
        default=list,
        comment="WordPress post categories (hierarchical taxonomy)",
    )

    meta_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="SEO meta description (150-160 chars)",
    )

    seo_keywords: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)) if ARRAY is not None else JSONType,
        nullable=True,
        default=list,
        comment="SEO keywords for search engines (1-3 keywords)",
    )

    drive_metadata: Mapped[dict] = mapped_column(
        JSONType,
        nullable=False,
        default=dict,
        comment="Drive metadata (links, owners, custom fields)",
    )
    notes: Mapped[List] = mapped_column(
        JSONType,
        nullable=False,
        default=list,
        comment="Reviewer notes and history",
    )
    article_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("articles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Linked article ID after import",
    )
    synced_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        comment="Last time the record was synced from Drive",
    )

    article: Mapped["Article"] = relationship(
        "Article",
        foreign_keys=[article_id],
        backref="worklist_item",
        uselist=False,
    )

    def mark_status(self, status: WorklistStatus) -> None:
        """Update worklist status and sync timestamp."""
        self.status = status
        self.synced_at = datetime.utcnow()

    def add_note(self, note: dict) -> None:
        """Append reviewer note."""
        notes = list(self.notes or [])
        notes.append(note)
        self.notes = notes
        self.synced_at = datetime.utcnow()
