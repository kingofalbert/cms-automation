"""Add missing proofreading columns to articles table

Revision ID: 20251105_1300
Revises: add_proofreading_decisions
Create Date: 2025-11-05 13:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251105_1300"
down_revision: str | None = "add_proofreading_decisions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Ensure proofreading columns exist on articles."""
    op.execute(
        "ALTER TABLE articles "
        "ADD COLUMN IF NOT EXISTS proofreading_issues JSONB "
        "NOT NULL DEFAULT '[]'::jsonb"
    )
    op.execute(
        "ALTER TABLE articles "
        "ADD COLUMN IF NOT EXISTS critical_issues_count INTEGER "
        "NOT NULL DEFAULT 0"
    )


def downgrade() -> None:
    """Remove proofreading columns from articles."""
    op.execute("ALTER TABLE articles DROP COLUMN IF EXISTS critical_issues_count")
    op.execute("ALTER TABLE articles DROP COLUMN IF EXISTS proofreading_issues")
