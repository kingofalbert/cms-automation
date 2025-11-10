"""Extend worklist status with parsing and proofreading review states.

Revision ID: 20251110_1000
Revises: 20251108_1800
Create Date: 2025-11-10 10:00:00.000000

Extended 9-state workflow:
- Added: parsing, parsing_review, proofreading_review
- Deprecated: under_review (mapped to proofreading_review)
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20251110_1000"
down_revision = "20251108_1800"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add new status values to WorklistStatus enum.

    SQLite doesn't support ALTER TYPE for enums, so we handle this differently
    depending on the database backend.

    For PostgreSQL: ALTER TYPE to add new values
    For SQLite: The enum is just a string constraint, values are validated in Python
    """
    # Check if we're using PostgreSQL (has native ENUM type)
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        # Add new enum values to existing WorklistStatus type
        op.execute("ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'parsing'")
        op.execute("ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'parsing_review'")
        op.execute("ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'proofreading_review'")

    # Migrate existing 'under_review' records to 'proofreading_review'
    op.execute(
        """
        UPDATE worklist_items
        SET status = 'proofreading_review'
        WHERE status = 'under_review'
        """
    )


def downgrade() -> None:
    """Revert proofreading_review back to under_review.

    Note: Cannot remove enum values in PostgreSQL once added.
    This migration only reverts the data, not the enum type.
    """
    # Revert data migration
    op.execute(
        """
        UPDATE worklist_items
        SET status = 'under_review'
        WHERE status = 'proofreading_review'
        """
    )

    # Note: We cannot remove enum values from PostgreSQL ENUM types
    # The new enum values (parsing, parsing_review, proofreading_review) will remain in the type
    # but won't be used after downgrade
