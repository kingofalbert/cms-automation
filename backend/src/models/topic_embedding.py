"""TopicEmbedding model for semantic similarity detection."""

from sqlalchemy import Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class TopicEmbedding(Base, TimestampMixin):
    """Vector embedding for topic semantic similarity."""

    __tablename__ = "topic_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Article reference
    article_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Article reference",
    )

    # Topic text for embedding
    topic_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Original topic description used for embedding",
    )

    # Vector embedding (using pgvector extension)
    # Note: We use ARRAY for SQLAlchemy compatibility, but this will be
    # a vector column in the actual database through pgvector
    embedding: Mapped[list[float]] = mapped_column(
        ARRAY(Float),
        nullable=False,
        comment="Vector embedding for semantic similarity",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<TopicEmbedding(id={self.id}, article_id={self.article_id}, dim={len(self.embedding) if self.embedding else 0})>"

    @property
    def dimensions(self) -> int:
        """Get embedding vector dimensions."""
        return len(self.embedding) if self.embedding else 0
