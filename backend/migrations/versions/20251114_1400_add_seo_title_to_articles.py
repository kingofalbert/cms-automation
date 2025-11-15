"""add_seo_title_to_articles

Revision ID: a1b2c3d4e5f6
Revises: 77fd4b324d80
Create Date: 2025-11-14 14:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '77fd4b324d80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add SEO Title fields to articles table.

    This migration adds three new columns to support SEO Title functionality:
    1. seo_title: The SEO-optimized title for search engines (max 200 chars, ~30 Chinese chars)
    2. seo_title_extracted: Boolean flag indicating if SEO title was extracted from original document
    3. seo_title_source: Source of the SEO title (extracted/ai_generated/user_input/migrated)

    For existing articles, we migrate title_main to seo_title with source='migrated'.
    """
    # Add seo_title column
    op.add_column(
        'articles',
        sa.Column(
            'seo_title',
            sa.String(length=200),
            nullable=True,
            comment='SEO Title Tag (30字左右，用於<title>標籤和搜尋結果顯示)'
        )
    )

    # Add seo_title_extracted column
    op.add_column(
        'articles',
        sa.Column(
            'seo_title_extracted',
            sa.Boolean(),
            nullable=False,
            server_default='false',
            comment='是否從原文中提取了標記的 SEO Title'
        )
    )

    # Add seo_title_source column
    op.add_column(
        'articles',
        sa.Column(
            'seo_title_source',
            sa.String(length=50),
            nullable=True,
            comment='SEO Title 來源：extracted/ai_generated/user_input/migrated'
        )
    )

    # Migrate existing data: copy title_main to seo_title
    op.execute("""
        UPDATE articles
        SET seo_title = title_main,
            seo_title_source = 'migrated'
        WHERE title_main IS NOT NULL AND seo_title IS NULL
    """)


def downgrade() -> None:
    """Remove SEO Title fields from articles table."""
    op.drop_column('articles', 'seo_title_source')
    op.drop_column('articles', 'seo_title_extracted')
    op.drop_column('articles', 'seo_title')
