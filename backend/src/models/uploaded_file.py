"""Uploaded file model for tracking Google Drive uploads."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.article import Article


class UploadedFile(Base, TimestampMixin):
    """Track uploaded files in Google Drive.

    Stores metadata about files uploaded to Google Drive, including
    Drive file IDs, public URLs, and associations with articles.
    """

    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # File identification
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Original filename",
    )

    # Google Drive metadata
    drive_file_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Google Drive file ID",
    )

    drive_folder_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Google Drive folder ID",
    )

    # File properties
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="application/octet-stream",
        comment="MIME type of file",
    )

    file_size: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="File size in bytes",
    )

    # Access URLs
    web_view_link: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Google Drive web view link",
    )

    web_content_link: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Google Drive direct download link",
    )

    # Association with article (optional)
    article_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Associated article ID (for featured/additional images)",
    )

    # File type classification
    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="other",
        index=True,
        comment="File type (image, document, video, other)",
    )

    # Upload context
    uploaded_by: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="User ID who uploaded the file",
    )

    # Additional metadata (JSONB for flexibility)
    file_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Additional file metadata",
    )

    # Soft delete support
    deleted_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="Soft delete timestamp",
    )

    # Relationships
    article: Mapped[Optional["Article"]] = relationship(
        "Article",
        foreign_keys=[article_id],
        back_populates="uploaded_files",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<UploadedFile(id={self.id}, filename='{self.filename}', drive_id='{self.drive_file_id}')>"

    @property
    def is_image(self) -> bool:
        """Check if file is an image."""
        return self.file_type == "image" or self.mime_type.startswith("image/")

    @property
    def public_url(self) -> str | None:
        """Get public URL for file access."""
        return self.web_content_link or self.web_view_link

    def mark_deleted(self) -> None:
        """Mark file as deleted (soft delete)."""
        self.deleted_at = datetime.utcnow()
