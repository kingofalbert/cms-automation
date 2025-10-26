"""rename_metadata_to_article_metadata

Revision ID: 3824f61361b3
Revises: 20251025_0200
Create Date: 2025-10-26 02:32:00.118500+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3824f61361b3'
down_revision: Union[str, None] = '20251025_0200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename column metadata to article_metadata in articles table
    op.alter_column(
        'articles',
        'metadata',
        new_column_name='article_metadata',
    )


def downgrade() -> None:
    # Rename column back to metadata
    op.alter_column(
        'articles',
        'article_metadata',
        new_column_name='metadata',
    )
