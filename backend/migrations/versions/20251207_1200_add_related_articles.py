"""Add related_articles field to articles table.

Phase 12: Internal Link Recommendations
- related_articles: JSONB field storing AI-recommended related articles
- Integrates with Supabase health_articles database for internal linking

Revision ID: 20251207_1200
Revises: 20251125_1000
Create Date: 2025-12-07 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '20251207_1200'
down_revision: Union[str, None] = '20251125_1000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add related_articles column to articles table."""
    op.add_column(
        'articles',
        sa.Column(
            'related_articles',
            JSONB,
            nullable=True,
            server_default='[]',
            comment='AI-recommended related articles for internal linking (from Supabase health_articles)',
        )
    )


def downgrade() -> None:
    """Remove related_articles column from articles table."""
    op.drop_column('articles', 'related_articles')
