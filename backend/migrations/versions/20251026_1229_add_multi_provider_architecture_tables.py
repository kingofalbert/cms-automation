"""Add multi-provider architecture tables (seo_metadata, publish_tasks, execution_logs)

Revision ID: 20251026_1229
Revises: 20251026_0232
Create Date: 2025-10-26 12:29:00.000000

This migration adds support for:
- SEO metadata generation and storage
- Multi-provider Computer Use publishing (Anthropic, Gemini, Playwright)
- Execution logging with partitioning
- Enhanced article tracking (source, images, published_url)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, JSONB

# revision identifiers, used by Alembic.
revision: str = "20251026_1229"
down_revision: Union[str, None] = "3824f61361b3"  # Previous: rename_metadata_to_article_metadata
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add multi-provider architecture tables and extend articles table."""

    # =========================================================================
    # 1. Extend articles table with new fields
    # =========================================================================

    # Add source field to track article origin
    op.add_column(
        'articles',
        sa.Column(
            'source',
            sa.String(50),
            nullable=False,
            server_default='manual',
            comment='Article import source (csv_import, json_import, manual, wordpress_export)'
        )
    )

    # Add featured image path
    op.add_column(
        'articles',
        sa.Column(
            'featured_image_path',
            sa.String(500),
            nullable=True,
            comment='Path to featured image in storage'
        )
    )

    # Add additional images (JSONB array of image paths)
    op.add_column(
        'articles',
        sa.Column(
            'additional_images',
            JSONB,
            nullable=True,
            server_default='[]',
            comment='Array of additional image paths'
        )
    )

    # Add published URL (after CMS publishing)
    op.add_column(
        'articles',
        sa.Column(
            'published_url',
            sa.String(500),
            nullable=True,
            comment='Public URL after publishing to CMS'
        )
    )

    # Update status enum to include SEO statuses
    op.execute("""
        ALTER TYPE articlestatus ADD VALUE IF NOT EXISTS 'imported';
        ALTER TYPE articlestatus ADD VALUE IF NOT EXISTS 'seo_optimized';
        ALTER TYPE articlestatus ADD VALUE IF NOT EXISTS 'ready_to_publish';
        ALTER TYPE articlestatus ADD VALUE IF NOT EXISTS 'publishing';
    """)

    # Create indexes for new fields
    op.create_index('idx_articles_source', 'articles', ['source'])
    op.create_index('idx_articles_published_url', 'articles', ['published_url'])

    # =========================================================================
    # 2. Create seo_metadata table
    # =========================================================================

    op.create_table(
        'seo_metadata',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'article_id',
            sa.Integer(),
            sa.ForeignKey('articles.id', ondelete='CASCADE'),
            unique=True,
            nullable=False,
            comment='Reference to article (1:1 relationship)'
        ),

        # SEO fields
        sa.Column(
            'meta_title',
            sa.String(60),
            nullable=False,
            comment='SEO meta title (50-60 chars)'
        ),
        sa.Column(
            'meta_description',
            sa.String(160),
            nullable=False,
            comment='SEO meta description (150-160 chars)'
        ),
        sa.Column(
            'focus_keyword',
            sa.String(100),
            nullable=False,
            comment='Primary focus keyword for SEO'
        ),
        sa.Column(
            'primary_keywords',
            ARRAY(sa.String(100)),
            nullable=True,
            comment='3-5 primary keywords'
        ),
        sa.Column(
            'secondary_keywords',
            ARRAY(sa.String(100)),
            nullable=True,
            comment='5-10 secondary keywords'
        ),
        sa.Column(
            'keyword_density',
            JSONB,
            nullable=True,
            server_default='{}',
            comment='Keyword -> {count, density} mapping'
        ),

        # Readability and scoring
        sa.Column(
            'readability_score',
            sa.Float(),
            nullable=True,
            comment='Flesch Reading Ease score (0-100)'
        ),
        sa.Column(
            'seo_score',
            sa.Float(),
            nullable=True,
            comment='Overall SEO score (0-100)'
        ),
        sa.Column(
            'optimization_recommendations',
            JSONB,
            nullable=True,
            server_default='[]',
            comment='Array of optimization suggestions'
        ),

        # Manual overrides
        sa.Column(
            'manual_overrides',
            JSONB,
            nullable=True,
            server_default='{}',
            comment='User-edited fields tracking'
        ),

        # Generation metadata
        sa.Column(
            'generated_by',
            sa.String(50),
            nullable=True,
            server_default='claude-3-5-haiku-20241022',
            comment='AI model used for generation'
        ),
        sa.Column(
            'generation_cost',
            sa.Float(),
            nullable=True,
            comment='Cost in USD for SEO analysis'
        ),
        sa.Column(
            'generation_tokens',
            sa.Integer(),
            nullable=True,
            comment='Total tokens used (input + output)'
        ),
        sa.Column(
            'error_message',
            sa.Text(),
            nullable=True,
            comment='Error message if analysis failed'
        ),

        # Timestamps
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
            comment='When SEO analysis was created'
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
            comment='When SEO metadata was last updated'
        ),

        # Constraints
        sa.CheckConstraint(
            'char_length(meta_title) >= 50 AND char_length(meta_title) <= 60',
            name='meta_title_length_check'
        ),
        sa.CheckConstraint(
            'char_length(meta_description) >= 150 AND char_length(meta_description) <= 160',
            name='meta_description_length_check'
        ),
        sa.CheckConstraint(
            'array_length(primary_keywords, 1) >= 3 AND array_length(primary_keywords, 1) <= 5',
            name='primary_keywords_count_check'
        ),
        sa.CheckConstraint(
            'array_length(secondary_keywords, 1) >= 5 AND array_length(secondary_keywords, 1) <= 10',
            name='secondary_keywords_count_check'
        ),
        sa.CheckConstraint(
            'readability_score IS NULL OR (readability_score >= 0 AND readability_score <= 100)',
            name='readability_score_range_check'
        ),
        sa.CheckConstraint(
            'seo_score IS NULL OR (seo_score >= 0 AND seo_score <= 100)',
            name='seo_score_range_check'
        ),
    )

    # Create indexes for seo_metadata
    op.create_index('idx_seo_metadata_article_id', 'seo_metadata', ['article_id'])
    op.create_index('idx_seo_metadata_focus_keyword', 'seo_metadata', ['focus_keyword'])
    op.create_index('idx_seo_metadata_seo_score', 'seo_metadata', ['seo_score'])

    # =========================================================================
    # 3. Create publish_tasks table
    # =========================================================================


    op.create_table(
        'publish_tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'article_id',
            sa.Integer(),
            sa.ForeignKey('articles.id', ondelete='CASCADE'),
            nullable=False,
            comment='Reference to article'
        ),

        # Task identification
        sa.Column(
            'task_id',
            sa.String(100),
            unique=True,
            nullable=True,
            comment='Celery task ID for async tracking'
        ),

        # Provider configuration (using String, will be altered to ENUM after table creation)
        sa.Column(
            'provider',
            sa.String(20),
            nullable=False,
            server_default='playwright',
            comment='Computer Use provider (anthropic, gemini, playwright)'
        ),
        sa.Column(
            'cms_type',
            sa.String(50),
            nullable=False,
            server_default='wordpress',
            comment='Target CMS type (wordpress, drupal, etc.)'
        ),
        sa.Column(
            'cms_url',
            sa.String(500),
            nullable=True,
            comment='Target CMS URL'
        ),

        # Task status and control (using String, will be altered to ENUM after table creation)
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='pending',
            comment='Task execution status'
        ),
        sa.Column(
            'retry_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Number of retry attempts'
        ),
        sa.Column(
            'max_retries',
            sa.Integer(),
            nullable=False,
            server_default='3',
            comment='Maximum retry attempts allowed'
        ),
        sa.Column(
            'error_message',
            sa.Text(),
            nullable=True,
            comment='Error message if task failed'
        ),

        # Execution metadata
        sa.Column(
            'session_id',
            sa.String(100),
            nullable=True,
            comment='Computer Use session ID'
        ),
        sa.Column(
            'screenshots',
            JSONB,
            nullable=True,
            server_default='[]',
            comment='Array of screenshot metadata {url, step, timestamp}'
        ),
        sa.Column(
            'cost_usd',
            sa.Float(),
            nullable=True,
            comment='Cost in USD for this publishing task'
        ),

        # Timing
        sa.Column(
            'started_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When task execution started'
        ),
        sa.Column(
            'completed_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When task completed (success or failure)'
        ),
        sa.Column(
            'duration_seconds',
            sa.Integer(),
            nullable=True,
            comment='Total execution duration in seconds'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
            comment='When task was created'
        ),

        # Constraints
        sa.CheckConstraint(
            'retry_count <= max_retries',
            name='retry_count_check'
        ),
        sa.CheckConstraint(
            'duration_seconds IS NULL OR duration_seconds >= 0',
            name='duration_positive_check'
        ),
        sa.CheckConstraint(
            'cost_usd IS NULL OR cost_usd >= 0',
            name='cost_positive_check'
        ),
    )

    # Create indexes for publish_tasks
    op.create_index('idx_publish_tasks_article_id', 'publish_tasks', ['article_id'])
    op.create_index('idx_publish_tasks_task_id', 'publish_tasks', ['task_id'])
    op.create_index('idx_publish_tasks_provider', 'publish_tasks', ['provider'])
    op.create_index('idx_publish_tasks_status', 'publish_tasks', ['status'])
    op.create_index('idx_publish_tasks_created_at', 'publish_tasks', ['created_at'])

    # Now alter columns to use ENUM types (create types first if they don't exist)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE provider_enum AS ENUM ('anthropic', 'gemini', 'playwright');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE task_status_enum AS ENUM ('pending', 'running', 'completed', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Alter columns to use the enum types (drop default first, then alter type, then re-add default)
    op.execute("""
        ALTER TABLE publish_tasks
        ALTER COLUMN provider DROP DEFAULT,
        ALTER COLUMN provider TYPE provider_enum USING provider::provider_enum,
        ALTER COLUMN provider SET DEFAULT 'playwright'::provider_enum;
    """)

    op.execute("""
        ALTER TABLE publish_tasks
        ALTER COLUMN status DROP DEFAULT,
        ALTER COLUMN status TYPE task_status_enum USING status::task_status_enum,
        ALTER COLUMN status SET DEFAULT 'pending'::task_status_enum;
    """)

    # =========================================================================
    # 4. Create execution_logs table (with monthly partitioning)
    # =========================================================================

    # Create log level enum first
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE log_level_enum AS ENUM ('DEBUG', 'INFO', 'WARNING', 'ERROR');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create parent partitioned table
    op.execute("""
        CREATE TABLE execution_logs (
            id BIGSERIAL,
            task_id INTEGER NOT NULL REFERENCES publish_tasks(id) ON DELETE CASCADE,
            log_level log_level_enum NOT NULL DEFAULT 'INFO',
            step_name VARCHAR(100),
            message TEXT,
            details JSONB DEFAULT '{}',
            action_type VARCHAR(50),
            action_target VARCHAR(200),
            action_result VARCHAR(50),
            screenshot_url VARCHAR(500),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            PRIMARY KEY (id, created_at)
        ) PARTITION BY RANGE (created_at);
    """)

    # Create first partition (current month)
    op.execute("""
        CREATE TABLE execution_logs_2025_10 PARTITION OF execution_logs
        FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
    """)

    # Create next month partition
    op.execute("""
        CREATE TABLE execution_logs_2025_11 PARTITION OF execution_logs
        FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
    """)

    # Create indexes on parent table (will be inherited by partitions)
    op.create_index('idx_execution_logs_task_id', 'execution_logs', ['task_id'])
    op.create_index('idx_execution_logs_created_at', 'execution_logs', ['created_at'])
    op.create_index('idx_execution_logs_log_level', 'execution_logs', ['log_level'])

    # Create function to auto-create partitions
    op.execute("""
        CREATE OR REPLACE FUNCTION create_execution_logs_partition()
        RETURNS void AS $$
        DECLARE
            partition_date DATE;
            partition_name TEXT;
            start_date TEXT;
            end_date TEXT;
        BEGIN
            -- Get first day of next month
            partition_date := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month');
            partition_name := 'execution_logs_' || TO_CHAR(partition_date, 'YYYY_MM');
            start_date := TO_CHAR(partition_date, 'YYYY-MM-DD');
            end_date := TO_CHAR(partition_date + INTERVAL '1 month', 'YYYY-MM-DD');

            -- Create partition if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM pg_class WHERE relname = partition_name
            ) THEN
                EXECUTE format(
                    'CREATE TABLE %I PARTITION OF execution_logs FOR VALUES FROM (%L) TO (%L)',
                    partition_name, start_date, end_date
                );
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # =========================================================================
    # 5. Create database triggers for auto-updates
    # =========================================================================

    # Trigger to update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Apply trigger to seo_metadata
    op.execute("""
        CREATE TRIGGER update_seo_metadata_updated_at
        BEFORE UPDATE ON seo_metadata
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

    # Trigger to update article status when SEO is created
    op.execute("""
        CREATE OR REPLACE FUNCTION update_article_status_on_seo()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE articles
            SET status = 'seo_optimized'
            WHERE id = NEW.article_id
            AND status = 'imported';
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER update_article_status_on_seo_insert
        AFTER INSERT ON seo_metadata
        FOR EACH ROW
        EXECUTE FUNCTION update_article_status_on_seo();
    """)

    # Trigger to update article status when publishing completes
    op.execute("""
        CREATE OR REPLACE FUNCTION update_article_status_on_publish()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
                UPDATE articles
                SET status = 'published',
                    published_at = NEW.completed_at
                WHERE id = NEW.article_id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER update_article_status_on_publish_complete
        AFTER UPDATE ON publish_tasks
        FOR EACH ROW
        EXECUTE FUNCTION update_article_status_on_publish();
    """)


def downgrade() -> None:
    """Rollback multi-provider architecture changes."""

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_article_status_on_publish_complete ON publish_tasks")
    op.execute("DROP TRIGGER IF EXISTS update_article_status_on_seo_insert ON seo_metadata")
    op.execute("DROP TRIGGER IF EXISTS update_seo_metadata_updated_at ON seo_metadata")

    # Drop trigger functions
    op.execute("DROP FUNCTION IF EXISTS update_article_status_on_publish()")
    op.execute("DROP FUNCTION IF EXISTS update_article_status_on_seo()")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    op.execute("DROP FUNCTION IF EXISTS create_execution_logs_partition()")

    # Drop tables
    op.execute("DROP TABLE IF EXISTS execution_logs CASCADE")
    op.drop_table('publish_tasks')
    op.drop_table('seo_metadata')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS log_level_enum")
    op.execute("DROP TYPE IF EXISTS task_status_enum")
    op.execute("DROP TYPE IF EXISTS provider_enum")

    # Drop articles table indexes
    op.drop_index('idx_articles_published_url', 'articles')
    op.drop_index('idx_articles_source', 'articles')

    # Remove articles table columns
    op.drop_column('articles', 'published_url')
    op.drop_column('articles', 'additional_images')
    op.drop_column('articles', 'featured_image_path')
    op.drop_column('articles', 'source')

    # Note: Cannot remove enum values added to articlestatus
    # This is a PostgreSQL limitation - enum values cannot be dropped
