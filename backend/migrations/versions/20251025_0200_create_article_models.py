"""Create article generation models

Revision ID: 20251025_0200
Revises: 20251025_0100
Create Date: 2025-10-25 02:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20251025_0200"
down_revision: Union[str, None] = "20251025_0100"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tables for article generation (User Story 1)."""

    # Create articles table
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False, comment="Article headline"),
        sa.Column("body", sa.Text(), nullable=False, comment="Full article content"),
        sa.Column(
            "status",
            sa.Enum("draft", "in-review", "scheduled", "published", "failed", name="articlestatus"),
            nullable=False,
            server_default="draft",
            comment="Workflow status",
        ),
        sa.Column("author_id", sa.Integer(), nullable=False, comment="User who initiated generation"),
        sa.Column("cms_article_id", sa.String(length=255), nullable=True, comment="CMS platform's article ID"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True, comment="Actual publication timestamp"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}", comment="CMS-specific metadata"),
        sa.Column("formatting", postgresql.JSONB(), nullable=False, server_default="{}", comment="Formatting preferences"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cms_article_id"),
    )

    # Create indexes for articles
    op.create_index("idx_articles_status", "articles", ["status"])
    op.create_index("idx_articles_author", "articles", ["author_id"])
    op.create_index("idx_articles_published", "articles", ["published_at"], postgresql_where=sa.text("published_at IS NOT NULL"))
    op.create_index("idx_articles_metadata", "articles", ["metadata"], postgresql_using="gin")

    # Create topic_requests table
    op.create_table(
        "topic_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("topic_description", sa.Text(), nullable=False, comment="User-provided topic or outline"),
        sa.Column("outline", sa.Text(), nullable=True, comment="Optional structured outline"),
        sa.Column("style_tone", sa.String(length=50), nullable=False, server_default="professional", comment="Requested writing style"),
        sa.Column("target_word_count", sa.Integer(), nullable=False, server_default="1000", comment="Desired article length"),
        sa.Column(
            "priority",
            sa.Enum("urgent", "normal", "low", name="topicrequestpriority"),
            nullable=False,
            server_default="normal",
            comment="Processing priority",
        ),
        sa.Column("submitted_by", sa.Integer(), nullable=False, comment="User ID who submitted request"),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "completed", "failed", "cancelled", name="topicrequeststatus"),
            nullable=False,
            server_default="pending",
            comment="Request processing status",
        ),
        sa.Column("article_id", sa.Integer(), nullable=True, comment="Foreign key to generated article"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="Error details if generation fails"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("article_id"),
    )

    # Create indexes for topic_requests
    op.create_index("idx_topic_requests_status", "topic_requests", ["status"])
    op.create_index("idx_topic_requests_submitted", "topic_requests", ["created_at"])
    op.create_index("idx_topic_requests_priority", "topic_requests", ["priority", "created_at"])

    # Create topic_embeddings table for semantic similarity
    op.create_table(
        "topic_embeddings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False, comment="Article reference"),
        sa.Column("topic_text", sa.Text(), nullable=False, comment="Original topic description"),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=False, comment="Vector embedding"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("article_id"),
    )

    # Create index for article_id lookup
    op.create_index("idx_topic_embeddings_article", "topic_embeddings", ["article_id"])


def downgrade() -> None:
    """Drop article generation tables."""
    op.drop_index("idx_topic_embeddings_article", table_name="topic_embeddings")
    op.drop_table("topic_embeddings")

    op.drop_index("idx_topic_requests_priority", table_name="topic_requests")
    op.drop_index("idx_topic_requests_submitted", table_name="topic_requests")
    op.drop_index("idx_topic_requests_status", table_name="topic_requests")
    op.drop_table("topic_requests")

    op.drop_index("idx_articles_metadata", table_name="articles", postgresql_using="gin")
    op.drop_index("idx_articles_published", table_name="articles")
    op.drop_index("idx_articles_author", table_name="articles")
    op.drop_index("idx_articles_status", table_name="articles")
    op.drop_table("articles")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS articlestatus")
    op.execute("DROP TYPE IF EXISTS topicrequestpriority")
    op.execute("DROP TYPE IF EXISTS topicrequeststatus")
