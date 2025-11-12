"""add_raw_html_to_worklist_items

Revision ID: 77fd4b324d80
Revises: 20251110_1000
Create Date: 2025-11-12 18:09:55.561967+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77fd4b324d80'
down_revision: Union[str, None] = '20251110_1000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add raw_html column to worklist_items table.

    This column stores the original HTML content from Google Docs exports,
    which is needed by ArticleParserService to extract images and structure.
    """
    op.add_column(
        'worklist_items',
        sa.Column('raw_html', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Remove raw_html column from worklist_items table."""
    op.drop_column('worklist_items', 'raw_html')
