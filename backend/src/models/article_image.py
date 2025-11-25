"""Article image models for Phase 7 structured parsing."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.article import Article


class ArticleImage(Base, TimestampMixin):
    """Image extracted from an article during structured parsing.

    Stores image metadata, file paths, and technical specifications
    for images found in Google Doc articles.
    """

    __tablename__ = "article_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign key to articles
    article_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Article this image belongs to",
    )

    # Image file paths
    preview_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to preview/thumbnail image in storage",
    )

    source_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to downloaded high-resolution source image",
    )

    source_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        comment='Original "原圖/點此下載" URL from Google Doc',
    )

    # Image content
    caption: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Image caption extracted from document",
    )

    # Phase 10: SEO and accessibility fields
    alt_text: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Image alt text for SEO and accessibility (based on caption or AI-generated)",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Image description for WordPress media library",
    )

    # Position in article
    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Paragraph index (0-based) where image should appear in body",
    )

    # Technical specifications (JSONB)
    # Note: Using 'image_metadata' as Python attr name, 'metadata' as DB column name
    # because 'metadata' is reserved by SQLAlchemy
    image_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        name="metadata",  # Database column name
        comment="Technical image metadata: dimensions, file size, format, EXIF",
    )

    # Timestamps inherited from TimestampMixin:
    # created_at, updated_at

    # Relationships
    article: Mapped["Article"] = relationship(
        "Article",
        back_populates="article_images",
    )

    image_reviews: Mapped[list["ArticleImageReview"]] = relationship(
        "ArticleImageReview",
        back_populates="article_image",
        cascade="all, delete-orphan",
        order_by="ArticleImageReview.created_at",
    )

    # Table-level constraints
    __table_args__ = (
        CheckConstraint("position >= 0", name="article_images_positive_position"),
        UniqueConstraint("article_id", "position", name="article_images_unique_position"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ArticleImage(id={self.id}, article_id={self.article_id}, "
            f"position={self.position}, caption='{self.caption[:30] if self.caption else None}...')>"
        )

    @property
    def has_source_url(self) -> bool:
        """Check if image has a source URL."""
        return self.source_url is not None and len(self.source_url) > 0

    @property
    def has_preview(self) -> bool:
        """Check if image has a preview/thumbnail."""
        return self.preview_path is not None and len(self.preview_path) > 0

    @property
    def has_source_file(self) -> bool:
        """Check if image has been downloaded."""
        return self.source_path is not None and len(self.source_path) > 0

    @property
    def image_width(self) -> int | None:
        """Get image width from metadata."""
        if self.image_metadata and "image_technical_specs" in self.image_metadata:
            return self.image_metadata["image_technical_specs"].get("width")
        return None

    @property
    def image_height(self) -> int | None:
        """Get image height from metadata."""
        if self.image_metadata and "image_technical_specs" in self.image_metadata:
            return self.image_metadata["image_technical_specs"].get("height")
        return None

    @property
    def file_size_bytes(self) -> int | None:
        """Get file size from metadata."""
        if self.image_metadata and "image_technical_specs" in self.image_metadata:
            return self.image_metadata["image_technical_specs"].get("file_size_bytes")
        return None

    @property
    def image_format(self) -> str | None:
        """Get image format from metadata."""
        if self.image_metadata and "image_technical_specs" in self.image_metadata:
            return self.image_metadata["image_technical_specs"].get("format")
        return None


class ImageReviewAction(str, PyEnum):
    """Review action types for article images."""

    KEEP = "keep"  # Image is correct, no changes needed
    REMOVE = "remove"  # Remove this image from article
    REPLACE_CAPTION = "replace_caption"  # Caption needs correction
    REPLACE_SOURCE = "replace_source"  # Source URL is incorrect


class ArticleImageReview(Base):
    """Review action taken on an article image during parsing confirmation.

    Tracks user feedback and actions during the parsing confirmation workflow (Step 1).
    """

    __tablename__ = "article_image_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign key to article_images
    article_image_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("article_images.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Image being reviewed",
    )

    # Optional link to worklist (if worklist system is used)
    worklist_item_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="Optional FK to worklist_items table",
    )

    # Review action
    action: Mapped[ImageReviewAction] = mapped_column(
        Enum(ImageReviewAction, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="Action taken: keep|remove|replace_caption|replace_source",
    )

    # Replacement data (conditional based on action)
    new_caption: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Replacement caption if action=replace_caption",
    )

    new_source_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        comment="Replacement source URL if action=replace_source",
    )

    # Review notes
    reviewer_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Notes explaining the review decision or rationale",
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        index=True,
        comment="Timestamp when review was created",
    )

    # Relationships
    article_image: Mapped["ArticleImage"] = relationship(
        "ArticleImage",
        back_populates="image_reviews",
    )

    # Table-level constraints
    __table_args__ = (
        CheckConstraint(
            "action != 'replace_caption' OR new_caption IS NOT NULL",
            name="article_image_reviews_caption_required",
        ),
        CheckConstraint(
            "action != 'replace_source' OR new_source_url IS NOT NULL",
            name="article_image_reviews_source_required",
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ArticleImageReview(id={self.id}, article_image_id={self.article_image_id}, "
            f"action={self.action}, created_at={self.created_at})>"
        )

    @property
    def is_modification(self) -> bool:
        """Check if this review modifies the image (not just keeping it)."""
        return self.action in (
            ImageReviewAction.REMOVE,
            ImageReviewAction.REPLACE_CAPTION,
            ImageReviewAction.REPLACE_SOURCE,
        )

    @property
    def has_replacement_data(self) -> bool:
        """Check if this review includes replacement data."""
        return (self.action == ImageReviewAction.REPLACE_CAPTION and self.new_caption is not None) or (
            self.action == ImageReviewAction.REPLACE_SOURCE and self.new_source_url is not None
        )
