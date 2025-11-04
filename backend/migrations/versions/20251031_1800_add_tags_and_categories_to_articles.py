"""Add tags and categories to articles table

Revision ID: 20251031_1800
Revises: 20251027_0900
Create Date: 2025-10-31 18:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20251031_1800"
down_revision: str | None = "20251027_0900"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add tags and categories columns to articles table."""
    # Add tags column (ARRAY of VARCHAR)
    op.add_column(
        'articles',
        sa.Column(
            'tags',
            postgresql.ARRAY(sa.String(length=100)),
            nullable=True,
            comment='WordPress post tags (3-6 natural categories for internal navigation)'
        )
    )

    # Add categories column (ARRAY of VARCHAR)
    op.add_column(
        'articles',
        sa.Column(
            'categories',
            postgresql.ARRAY(sa.String(length=100)),
            nullable=True,
            comment='WordPress post categories (hierarchical taxonomy)'
        )
    )


def downgrade() -> None:
    """Remove tags and categories columns from articles table."""
    op.drop_column('articles', 'categories')
    op.drop_column('articles', 'tags')
