"""Add index on worklist_items.synced_at for faster sync status queries.

Revision ID: 20251220_1000
Revises: 20251207_1200
Create Date: 2025-12-20 10:00:00.000000

This index is critical for the sync-status endpoint which orders by synced_at DESC.
Without this index, every sync-status query does a full table scan.
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20251220_1000"
down_revision: str | None = "20251207_1200"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create index to accelerate sync status queries."""
    # Index for ORDER BY synced_at DESC queries
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_worklist_items_synced_at
        ON worklist_items (synced_at DESC)
        """
    )


def downgrade() -> None:
    """Drop synced_at index."""
    op.execute("DROP INDEX IF EXISTS ix_worklist_items_synced_at")
