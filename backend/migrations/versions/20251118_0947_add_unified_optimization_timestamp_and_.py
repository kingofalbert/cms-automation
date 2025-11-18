"""Add unified optimization timestamp and cost fields

Revision ID: af50da9ccee0
Revises: b2c3d4e5f6g7
Create Date: 2025-11-18 09:47:12.825587+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af50da9ccee0'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unified_optimization_generated_at column
    op.add_column(
        'articles',
        sa.Column(
            'unified_optimization_generated_at',
            sa.DateTime(),
            nullable=True,
            comment='When unified AI optimizations were generated',
        ),
    )

    # Add unified_optimization_cost column
    op.add_column(
        'articles',
        sa.Column(
            'unified_optimization_cost',
            sa.Numeric(precision=10, scale=6),
            nullable=True,
            comment='Cost in USD for generating all optimizations',
        ),
    )


def downgrade() -> None:
    # Drop columns in reverse order
    op.drop_column('articles', 'unified_optimization_cost')
    op.drop_column('articles', 'unified_optimization_generated_at')
