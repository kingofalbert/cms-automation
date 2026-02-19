"""Add raw_html column to articles table.

Revision ID: add_raw_html_to_articles
Revises: aeo_doc_metadata_fields
Create Date: 2026-02-19

P0 Fix: Article model needs raw_html field to store original Google Docs HTML.
Without this, POST /v1/articles/{id}/parse fails with AttributeError.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_raw_html_to_articles'
down_revision = 'aeo_doc_metadata_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add raw_html column to articles table."""
    op.add_column(
        'articles',
        sa.Column('raw_html', sa.Text(), nullable=True,
                  comment='Original HTML from Google Docs export (for parser with images)')
    )


def downgrade() -> None:
    """Remove raw_html column from articles table."""
    op.drop_column('articles', 'raw_html')
