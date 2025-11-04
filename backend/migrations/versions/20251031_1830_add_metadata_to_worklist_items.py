"""Add tags, categories, meta_description, and seo_keywords to worklist_items

Revision ID: 20251031_1830
Revises: 20251031_1800
Create Date: 2025-10-31 18:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20251031_1830"
down_revision: str | None = "20251031_1800"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add WordPress taxonomy and SEO metadata columns to worklist_items table."""
    # Add tags column (ARRAY of VARCHAR)
    op.add_column(
        'worklist_items',
        sa.Column(
            'tags',
            postgresql.ARRAY(sa.String(length=100)),
            nullable=True,
            comment='WordPress post tags (3-6 categories for internal navigation)'
        )
    )

    # Add categories column (ARRAY of VARCHAR)
    op.add_column(
        'worklist_items',
        sa.Column(
            'categories',
            postgresql.ARRAY(sa.String(length=100)),
            nullable=True,
            comment='WordPress post categories (hierarchical taxonomy)'
        )
    )

    # Add meta_description column (TEXT)
    op.add_column(
        'worklist_items',
        sa.Column(
            'meta_description',
            sa.Text(),
            nullable=True,
            comment='SEO meta description (150-160 chars)'
        )
    )

    # Add seo_keywords column (ARRAY of VARCHAR)
    op.add_column(
        'worklist_items',
        sa.Column(
            'seo_keywords',
            postgresql.ARRAY(sa.String(length=100)),
            nullable=True,
            comment='SEO keywords for search engines (1-3 keywords)'
        )
    )


def downgrade() -> None:
    """Remove WordPress taxonomy and SEO metadata columns from worklist_items table."""
    op.drop_column('worklist_items', 'seo_keywords')
    op.drop_column('worklist_items', 'meta_description')
    op.drop_column('worklist_items', 'categories')
    op.drop_column('worklist_items', 'tags')
