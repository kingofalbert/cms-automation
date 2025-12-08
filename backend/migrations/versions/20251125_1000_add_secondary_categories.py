"""Add secondary_categories field to articles table.

Phase 11: WordPress Category Taxonomy Enhancement
- primary_category: Single selection for URL structure and breadcrumbs
- secondary_categories: Multiple selection for cross-listing articles

Revision ID: 20251125_1000
Revises: 20251124_0800
Create Date: 2025-11-25 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision: str = '20251125_1000'
down_revision: Union[str, None] = 'f599ccd30336'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add secondary_categories column to articles table."""
    op.add_column(
        'articles',
        sa.Column(
            'secondary_categories',
            ARRAY(sa.String(100)),
            nullable=True,
            comment='WordPress secondary categories (副分類，可多選，用於交叉列表)',
        )
    )


def downgrade() -> None:
    """Remove secondary_categories column from articles table."""
    op.drop_column('articles', 'secondary_categories')
