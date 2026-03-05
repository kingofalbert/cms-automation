"""Widen article_images.source_url from VARCHAR(1000) to TEXT.

Revision ID: widen_source_url_to_text
Revises: add_raw_html_to_articles
Create Date: 2026-03-03

Fix: base64 data URIs from Google Docs inline images can exceed VARCHAR(1000),
causing StringDataRightTruncationError on INSERT.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'widen_source_url_to_text'
down_revision = 'add_raw_html_to_articles'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Widen source_url to TEXT."""
    op.alter_column(
        'article_images',
        'source_url',
        type_=sa.Text(),
        existing_type=sa.String(1000),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Revert source_url to VARCHAR(1000)."""
    op.alter_column(
        'article_images',
        'source_url',
        type_=sa.String(1000),
        existing_type=sa.Text(),
        existing_nullable=True,
    )
