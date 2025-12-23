"""Add FAQ v2.2 assessment and HTML fields.

Revision ID: faq_v2_assessment
Revises: (auto-detect)
Create Date: 2025-12-22

This migration adds:
1. FAQ applicability assessment fields to articles table
2. FAQ HTML field for visible content
3. Safety warning field to article_faqs table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'faq_v2_assessment'
down_revision = None  # Will be auto-detected
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add FAQ v2.2 fields."""
    # Add fields to articles table
    op.add_column(
        'articles',
        sa.Column('faq_applicable', sa.Boolean(), nullable=True,
                  comment='Whether FAQ is applicable for this article')
    )
    op.add_column(
        'articles',
        sa.Column('faq_assessment', JSONB(), nullable=True,
                  comment='FAQ applicability assessment (reason, pain_points)')
    )
    op.add_column(
        'articles',
        sa.Column('faq_editorial_notes', JSONB(), nullable=True,
                  comment='FAQ editorial notes (longtail keywords, multimedia)')
    )
    op.add_column(
        'articles',
        sa.Column('faq_html', sa.Text(), nullable=True,
                  comment='Generated FAQ HTML section for article body')
    )

    # Add safety_warning field to article_faqs table
    op.add_column(
        'article_faqs',
        sa.Column('safety_warning', sa.Boolean(), nullable=False,
                  server_default='false',
                  comment='YMYL safety warning flag')
    )


def downgrade() -> None:
    """Remove FAQ v2.2 fields."""
    op.drop_column('article_faqs', 'safety_warning')
    op.drop_column('articles', 'faq_html')
    op.drop_column('articles', 'faq_editorial_notes')
    op.drop_column('articles', 'faq_assessment')
    op.drop_column('articles', 'faq_applicable')
