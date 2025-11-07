"""Align worklist statuses with UX flow and add article status history."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20251107_1000"
down_revision: str | None = "20251106_1500"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


NEW_STATUSES = (
    "pending",
    "proofreading",
    "under_review",
    "ready_to_publish",
    "publishing",
    "published",
    "failed",
)

OLD_STATUSES = (
    "to_evaluate",
    "to_confirm",
    "to_review",
    "to_revise",
    "to_rereview",
    "ready_to_publish",
    "published",
)

STATUS_MAPPING = {
    "to_evaluate": "pending",
    "to_confirm": "proofreading",
    "to_review": "under_review",
    "to_revise": "under_review",
    "to_rereview": "under_review",
    "ready_to_publish": "ready_to_publish",
    "published": "published",
}

REVERSE_STATUS_MAPPING = {
    "pending": "to_evaluate",
    "proofreading": "to_confirm",
    "under_review": "to_review",
    "ready_to_publish": "ready_to_publish",
    "publishing": "to_review",
    "published": "published",
    "failed": "to_revise",
}


def upgrade() -> None:
    """Apply new worklist enum and create article_status_history table."""
    bind = op.get_bind()

    # Temporarily cast status to text and drop the old enum type
    # First remove the default constraint
    op.execute("ALTER TABLE worklist_items ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE worklist_items ALTER COLUMN status TYPE TEXT USING status::text"
    )
    op.execute("DROP TYPE IF EXISTS workliststatus CASCADE")

    # Apply value mapping to align with new enum members
    for old_value, new_value in STATUS_MAPPING.items():
        op.execute(
            sa.text(
                "UPDATE worklist_items SET status=:new_status WHERE status=:old_status"
            ).bindparams(new_status=new_value, old_status=old_value)
        )

    # Create the new enum and cast the column back
    new_enum = sa.Enum(*NEW_STATUSES, name="workliststatus")
    new_enum.create(bind, checkfirst=True)

    op.execute(
        "ALTER TABLE worklist_items "
        "ALTER COLUMN status TYPE workliststatus USING status::workliststatus"
    )
    op.execute(
        "ALTER TABLE worklist_items ALTER COLUMN status "
        "SET DEFAULT 'pending'::workliststatus"
    )

    # Create article_status_history table
    op.create_table(
        "article_status_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("articles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("old_status", sa.String(length=50), nullable=True),
        sa.Column("new_status", sa.String(length=50), nullable=False),
        sa.Column("changed_by", sa.String(length=100), nullable=True),
        sa.Column("change_reason", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            nullable=False,
            default=datetime.utcnow,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )
    op.create_index(
        "ix_article_status_history_article_id",
        "article_status_history",
        ["article_id"],
    )
    op.create_index(
        "ix_article_status_history_created_at",
        "article_status_history",
        ["created_at"],
    )


def downgrade() -> None:
    """Revert enum and remove article_status_history table."""
    bind = op.get_bind()

    op.drop_index(
        "ix_article_status_history_created_at", table_name="article_status_history"
    )
    op.drop_index(
        "ix_article_status_history_article_id", table_name="article_status_history"
    )
    op.drop_table("article_status_history")

    op.execute(
        "ALTER TABLE worklist_items ALTER COLUMN status TYPE TEXT USING status::text"
    )
    op.execute("DROP TYPE IF EXISTS workliststatus")

    # Map values back to old enum
    for new_value, old_value in REVERSE_STATUS_MAPPING.items():
        op.execute(
            sa.text(
                "UPDATE worklist_items SET status=:old_status WHERE status=:new_status"
            ).bindparams(new_status=new_value, old_status=old_value)
        )

    old_enum = sa.Enum(*OLD_STATUSES, name="workliststatus")
    old_enum.create(bind, checkfirst=True)

    op.execute(
        "ALTER TABLE worklist_items "
        "ALTER COLUMN status TYPE workliststatus USING status::workliststatus"
    )
    op.execute(
        "ALTER TABLE worklist_items ALTER COLUMN status "
        "SET DEFAULT 'to_evaluate'::workliststatus"
    )
