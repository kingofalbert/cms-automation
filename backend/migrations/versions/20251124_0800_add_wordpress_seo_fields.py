"""add_wordpress_seo_fields

Revision ID: f599ccd30336
Revises: e498bbc20225
Create Date: 2025-11-24 08:00:00.000000+00:00

Phase 10: WordPress Field Mapping
Add fields for WordPress primary category, Yoast SEO focus keyword,
and image alt_text/description for accessibility and SEO.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f599ccd30336'
down_revision: Union[str, None] = 'e498bbc20225'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add WordPress SEO fields to articles and article_images tables.

    Articles table:
    - primary_category: WordPress primary category (from candidate list)
    - focus_keyword: Yoast SEO focus keyword

    Article_images table:
    - alt_text: Image alt text for SEO and accessibility
    - description: Image description for WordPress media library
    """
    # Add primary_category to articles
    op.add_column(
        'articles',
        sa.Column(
            'primary_category',
            sa.String(length=100),
            nullable=True,
            comment='WordPress primary category (from candidate list)'
        )
    )

    # Add index on primary_category for filtering
    op.create_index(
        'ix_articles_primary_category',
        'articles',
        ['primary_category']
    )

    # Add focus_keyword to articles
    op.add_column(
        'articles',
        sa.Column(
            'focus_keyword',
            sa.String(length=100),
            nullable=True,
            comment='Yoast SEO focus keyword (from seo_keywords or AI recommended)'
        )
    )

    # Add alt_text to article_images
    op.add_column(
        'article_images',
        sa.Column(
            'alt_text',
            sa.String(length=500),
            nullable=True,
            comment='Image alt text for SEO and accessibility'
        )
    )

    # Add description to article_images
    op.add_column(
        'article_images',
        sa.Column(
            'description',
            sa.Text(),
            nullable=True,
            comment='Image description for WordPress media library'
        )
    )

    # Auto-populate alt_text from caption for existing images
    op.execute("""
        UPDATE article_images
        SET alt_text = LEFT(caption, 500)
        WHERE caption IS NOT NULL AND alt_text IS NULL
    """)

    # Auto-populate focus_keyword from first seo_keyword for existing articles
    op.execute("""
        UPDATE articles
        SET focus_keyword = seo_keywords[1]
        WHERE seo_keywords IS NOT NULL
          AND array_length(seo_keywords, 1) > 0
          AND focus_keyword IS NULL
    """)


def downgrade() -> None:
    """Remove WordPress SEO fields."""
    op.drop_column('article_images', 'description')
    op.drop_column('article_images', 'alt_text')
    op.drop_column('articles', 'focus_keyword')
    op.drop_index('ix_articles_primary_category', table_name='articles')
    op.drop_column('articles', 'primary_category')
