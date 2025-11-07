"""Add index on worklist_items.updated_at for faster ordering.

Revision ID: 20251106_1500
Revises: 20251105_1300
Create Date: 2025-11-06 15:00:00.000000
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20251106_1500"
down_revision: str | None = "20251105_1300"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create index to accelerate sorting by updated_at."""
    op.create_index(
        "ix_worklist_items_updated_at",
        "worklist_items",
        ["updated_at"],
    )


def downgrade() -> None:
    """Drop updated_at index."""
    op.drop_index("ix_worklist_items_updated_at", table_name="worklist_items")
