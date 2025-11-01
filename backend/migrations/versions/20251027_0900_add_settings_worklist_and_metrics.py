"""Add settings, worklist, and provider metrics tables plus publish task upgrades

Revision ID: 20251027_0900
Revises: uploaded_files_v1
Create Date: 2025-10-27 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20251027_0900"
down_revision: Union[str, None] = "uploaded_files_v1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create new tables and align enums/columns with updated models."""
    # ------------------------------------------------------------------
    # Update provider enum values
    # ------------------------------------------------------------------
    op.execute(
        """
        UPDATE publish_tasks
        SET provider = 'computer_use'
        WHERE provider IN ('anthropic', 'gemini');
        """
    )

    op.execute("ALTER TYPE provider_enum RENAME TO provider_enum_old;")
    op.execute(
        "CREATE TYPE provider_enum AS ENUM ('playwright', 'computer_use', 'hybrid');"
    )
    op.execute("ALTER TABLE publish_tasks ALTER COLUMN provider DROP DEFAULT;")
    op.execute(
        """
        ALTER TABLE publish_tasks
        ALTER COLUMN provider
        TYPE provider_enum
        USING provider::text::provider_enum;
        """
    )
    op.execute(
        "ALTER TABLE publish_tasks ALTER COLUMN provider SET DEFAULT 'playwright';"
    )
    op.execute("DROP TYPE provider_enum_old;")

    # ------------------------------------------------------------------
    # Update task status enum values
    # ------------------------------------------------------------------
    op.execute(
        """
        UPDATE publish_tasks
        SET status = 'publishing'
        WHERE status = 'running';
        """
    )

    op.execute("ALTER TYPE task_status_enum RENAME TO task_status_enum_old;")
    op.execute(
        """
        CREATE TYPE task_status_enum AS ENUM (
            'idle',
            'pending',
            'initializing',
            'logging_in',
            'creating_post',
            'uploading_images',
            'configuring_seo',
            'publishing',
            'completed',
            'failed'
        );
        """
    )
    op.execute("ALTER TABLE publish_tasks ALTER COLUMN status DROP DEFAULT;")
    op.execute(
        """
        ALTER TABLE publish_tasks
        ALTER COLUMN status
        TYPE task_status_enum
        USING status::text::task_status_enum;
        """
    )
    op.execute("ALTER TABLE publish_tasks ALTER COLUMN status SET DEFAULT 'pending';")
    op.execute("DROP TYPE task_status_enum_old;")

    # ------------------------------------------------------------------
    # Add progress tracking columns to publish_tasks
    # ------------------------------------------------------------------
    op.add_column(
        "publish_tasks",
        sa.Column(
        "progress",
        sa.Integer(),
        nullable=False,
        server_default=sa.text("0"),
        comment="Task progress percentage (0-100)",
    ),
)
    op.add_column(
        "publish_tasks",
        sa.Column(
        "current_step",
        sa.String(length=100),
        nullable=False,
        server_default=sa.text("'pending'"),
        comment="Current step description",
    ),
)
    op.add_column(
        "publish_tasks",
        sa.Column(
        "total_steps",
        sa.Integer(),
        nullable=False,
        server_default=sa.text("7"),
        comment="Total number of steps in publishing workflow",
    ),
)
    op.add_column(
        "publish_tasks",
        sa.Column(
        "completed_steps",
        sa.Integer(),
        nullable=False,
        server_default=sa.text("0"),
        comment="Number of completed steps",
    ),
)

    # Populate new columns for existing rows
    op.execute(
        """
        UPDATE publish_tasks
        SET progress = 0,
            current_step = status::text,
            total_steps = 7,
            completed_steps = CASE
                WHEN status IN ('completed', 'failed') THEN 7
                WHEN status = 'pending' THEN 0
                ELSE 1
            END;
        """
    )

    # Add new check constraints
    op.create_check_constraint(
        "progress_range_check",
        "publish_tasks",
        "progress >= 0 AND progress <= 100",
    )
    op.create_check_constraint(
        "completed_steps_non_negative_check",
        "publish_tasks",
        "completed_steps >= 0",
    )
    op.create_check_constraint(
        "total_steps_positive_check",
        "publish_tasks",
        "total_steps > 0",
    )
    op.create_check_constraint(
        "completed_steps_not_exceed_total_check",
        "publish_tasks",
        "completed_steps <= total_steps",
    )

    # ------------------------------------------------------------------
    # Create app_settings table
    # ------------------------------------------------------------------
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column(
            "provider_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Publishing provider configuration (playwright/computer_use/hybrid)",
        ),
        sa.Column(
            "cms_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="CMS connection details and preferences",
        ),
        sa.Column(
            "cost_limits",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Cost thresholds and budgeting rules",
        ),
        sa.Column(
            "screenshot_retention",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Screenshot retention policies (count, duration)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Last update timestamp",
        ),
        sa.CheckConstraint("id = 1", name="app_settings_singleton_check"),
    )

    # ------------------------------------------------------------------
    # Create provider_metrics table
    # ------------------------------------------------------------------
    op.create_table(
        "provider_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "provider",
            sa.Enum(name="provider_enum"),
            nullable=False,
        ),
        sa.Column(
            "date",
            sa.Date(),
            nullable=False,
            comment="Metric date (UTC). Partition key.",
        ),
        sa.Column(
        "total_tasks",
        sa.Integer(),
        nullable=False,
        server_default=sa.text("0"),
        comment="Total tasks executed during interval",
    ),
        sa.Column(
        "successful_tasks",
        sa.Integer(),
        nullable=False,
        server_default=sa.text("0"),
        comment="Total successful tasks",
    ),
        sa.Column(
        "failed_tasks",
        sa.Integer(),
        nullable=False,
        server_default=sa.text("0"),
        comment="Total failed tasks",
    ),
        sa.Column(
        "success_rate",
        sa.Float(),
        nullable=False,
        server_default=sa.text("0"),
        comment="Success rate percentage (0-100)",
    ),
        sa.Column(
            "avg_duration_seconds",
            sa.Float(),
            nullable=True,
            comment="Average task duration (seconds)",
        ),
        sa.Column(
            "avg_cost_usd",
            sa.Float(),
            nullable=True,
            comment="Average cost per task (USD)",
        ),
        sa.Column(
            "total_cost_usd",
            sa.Float(),
            nullable=True,
            comment="Total cost for provider (USD)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Record creation timestamp",
        ),
        sa.UniqueConstraint("provider", "date", name="uq_provider_metrics_provider_date"),
    )
    op.create_index(
        "ix_provider_metrics_date",
        "provider_metrics",
        ["date"],
    )
    op.create_index(
        "ix_provider_metrics_provider",
        "provider_metrics",
        ["provider"],
    )

    # ------------------------------------------------------------------
    # Create worklist_items table
    # ------------------------------------------------------------------
    op.create_table(
        "worklist_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "drive_file_id",
            sa.String(length=255),
            nullable=False,
            comment="Google Drive file identifier",
        ),
        sa.Column(
            "title",
            sa.String(length=500),
            nullable=False,
            comment="Worklist document title",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "to_evaluate",
                "to_confirm",
                "to_review",
                "to_revise",
                "to_rereview",
                "ready_to_publish",
                "published",
                name="workliststatus",
            ),
            nullable=False,
            server_default="to_evaluate",
            comment="Worklist processing status",
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
            comment="Document content (Markdown/HTML)",
        ),
        sa.Column(
            "author",
            sa.String(length=255),
            nullable=True,
            comment="Document author",
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Drive metadata (links, owners, custom fields)",
        ),
        sa.Column(
            "notes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
            comment="Reviewer notes and history",
        ),
        sa.Column(
            "article_id",
            sa.Integer(),
            sa.ForeignKey("articles.id", ondelete="SET NULL"),
            nullable=True,
            comment="Linked article ID after import",
        ),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Last time the record was synced from Drive",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Record creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Record last update timestamp",
        ),
    )

    op.create_index(
        "ix_worklist_items_drive_file_id",
        "worklist_items",
        ["drive_file_id"],
        unique=True,
    )
    op.create_index(
        "ix_worklist_items_status",
        "worklist_items",
        ["status"],
    )
    op.create_index(
        "ix_worklist_items_article_id",
        "worklist_items",
        ["article_id"],
    )


def downgrade() -> None:
    """Revert the new tables and enum/column changes."""
    # Drop worklist table and indexes
    op.drop_index("ix_worklist_items_article_id", table_name="worklist_items")
    op.drop_index("ix_worklist_items_status", table_name="worklist_items")
    op.drop_index("ix_worklist_items_drive_file_id", table_name="worklist_items")
    op.drop_table("worklist_items")
    op.execute("DROP TYPE IF EXISTS workliststatus;")

    # Drop provider metrics table and index
    op.drop_index("ix_provider_metrics_provider", table_name="provider_metrics")
    op.drop_index("ix_provider_metrics_date", table_name="provider_metrics")
    op.drop_table("provider_metrics")

    # Drop app settings table
    op.drop_table("app_settings")

    # Remove publish_tasks constraints
    op.drop_constraint(
        "completed_steps_not_exceed_total_check", "publish_tasks", type_="check"
    )
    op.drop_constraint("total_steps_positive_check", "publish_tasks", type_="check")
    op.drop_constraint(
        "completed_steps_non_negative_check", "publish_tasks", type_="check"
    )
    op.drop_constraint("progress_range_check", "publish_tasks", type_="check")

    # Drop progress columns
    op.drop_column("publish_tasks", "completed_steps")
    op.drop_column("publish_tasks", "total_steps")
    op.drop_column("publish_tasks", "current_step")
    op.drop_column("publish_tasks", "progress")

    # Restore task status enum
    op.execute("ALTER TYPE task_status_enum RENAME TO task_status_enum_new;")
    op.execute(
        """
        CREATE TYPE task_status_enum AS ENUM ('pending', 'running', 'completed', 'failed');
        """
    )
    op.execute("ALTER TABLE publish_tasks ALTER COLUMN status DROP DEFAULT;")
    op.execute(
        """
        ALTER TABLE publish_tasks
        ALTER COLUMN status
        TYPE task_status_enum
        USING CASE status
            WHEN 'publishing' THEN 'running'
            WHEN 'pending' THEN 'pending'
            WHEN 'completed' THEN 'completed'
            WHEN 'failed' THEN 'failed'
            ELSE 'pending'
        END::task_status_enum;
        """
    )
    op.execute("ALTER TABLE publish_tasks ALTER COLUMN status SET DEFAULT 'pending';")
    op.execute("DROP TYPE task_status_enum_new;")

    # Restore provider enum
    op.execute("ALTER TYPE provider_enum RENAME TO provider_enum_new;")
    op.execute(
        "CREATE TYPE provider_enum AS ENUM ('anthropic', 'gemini', 'playwright');"
    )
    op.execute("ALTER TABLE publish_tasks ALTER COLUMN provider DROP DEFAULT;")
    op.execute(
        """
        ALTER TABLE publish_tasks
        ALTER COLUMN provider
        TYPE provider_enum
        USING CASE provider
            WHEN 'computer_use' THEN 'anthropic'
            WHEN 'hybrid' THEN 'playwright'
            ELSE provider
        END::provider_enum;
        """
    )
    op.execute(
        "ALTER TABLE publish_tasks ALTER COLUMN provider SET DEFAULT 'playwright';"
    )
    op.execute("DROP TYPE provider_enum_new;")
