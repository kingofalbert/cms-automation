"""Add pipeline_tasks table for async task tracking.

Revision ID: add_pipeline_tasks
Revises: widen_source_url_to_text
Create Date: 2026-03-10

Replaces in-memory _task_results dict with persistent DB storage so task
state survives Cloud Run restarts and works across multiple instances.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = "add_pipeline_tasks"
down_revision = "widen_source_url_to_text"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pipeline_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_type", sa.String(50), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("input", JSONB, nullable=True),
        sa.Column("result", JSONB, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_pipeline_tasks_type_status", "pipeline_tasks", ["task_type", "status"])
    op.create_index("idx_pipeline_tasks_created_at", "pipeline_tasks", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_pipeline_tasks_created_at", table_name="pipeline_tasks")
    op.drop_index("idx_pipeline_tasks_type_status", table_name="pipeline_tasks")
    op.drop_table("pipeline_tasks")
