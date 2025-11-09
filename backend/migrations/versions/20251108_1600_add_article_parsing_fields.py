"""Add article parsing fields for Phase 7 structured parsing

Revision ID: 20251108_1600
Revises: 20251107_1500
Create Date: 2025-11-08 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251108_1600'
down_revision = '20251107_1500'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add Phase 7 article structured parsing fields to articles table.

    This migration adds fields to support:
    - Title decomposition (prefix, main, suffix)
    - Author extraction (raw line and cleaned name)
    - Cleaned body HTML
    - SEO metadata extraction (meta description, keywords)
    - Parsing confirmation workflow
    """

    # ========================================================================
    # Title Decomposition Fields
    # ========================================================================
    op.add_column(
        'articles',
        sa.Column(
            'title_prefix',
            sa.String(length=200),
            nullable=True,
            comment='First part of title (optional), e.g., "【專題報導】"'
        )
    )

    op.add_column(
        'articles',
        sa.Column(
            'title_main',
            sa.String(length=500),
            nullable=True,  # Initially nullable to handle existing articles
            comment='Main title (required for new articles), e.g., "2024年醫療保健創新趨勢"'
        )
    )

    op.add_column(
        'articles',
        sa.Column(
            'title_suffix',
            sa.String(length=200),
            nullable=True,
            comment='Subtitle/suffix (optional), e.g., "從AI診斷到遠距醫療"'
        )
    )

    # ========================================================================
    # Author Information Fields
    # ========================================================================
    op.add_column(
        'articles',
        sa.Column(
            'author_line',
            sa.String(length=300),
            nullable=True,
            comment='Raw author line from document, e.g., "文／張三｜編輯／李四"'
        )
    )

    op.add_column(
        'articles',
        sa.Column(
            'author_name',
            sa.String(length=100),
            nullable=True,
            comment='Cleaned author name extracted from author_line, e.g., "張三"'
        )
    )

    # ========================================================================
    # Cleaned Body Content
    # ========================================================================
    op.add_column(
        'articles',
        sa.Column(
            'body_html',
            sa.Text(),
            nullable=True,
            comment='Sanitized body HTML with headers/images/meta removed, ready for publishing'
        )
    )

    # ========================================================================
    # SEO and Metadata Fields
    # ========================================================================
    op.add_column(
        'articles',
        sa.Column(
            'meta_description',
            sa.Text(),
            nullable=True,
            comment='Extracted meta description for SEO (150-160 chars recommended)'
        )
    )

    op.add_column(
        'articles',
        sa.Column(
            'seo_keywords',
            postgresql.ARRAY(sa.Text()),
            nullable=True,
            comment='Array of SEO keywords extracted from content'
        )
    )

    # Note: 'tags' TEXT[] already exists in the schema, so we skip it

    # ========================================================================
    # Parsing Confirmation Workflow Fields
    # ========================================================================
    op.add_column(
        'articles',
        sa.Column(
            'parsing_confirmed',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('FALSE'),
            comment='Whether parsing has been reviewed and confirmed by user (Step 1)'
        )
    )

    op.add_column(
        'articles',
        sa.Column(
            'parsing_confirmed_at',
            sa.TIMESTAMP(),
            nullable=True,
            comment='Timestamp when parsing was confirmed'
        )
    )

    op.add_column(
        'articles',
        sa.Column(
            'parsing_confirmed_by',
            sa.String(length=100),
            nullable=True,
            comment='User ID or identifier who confirmed the parsing'
        )
    )

    op.add_column(
        'articles',
        sa.Column(
            'parsing_feedback',
            sa.Text(),
            nullable=True,
            comment='User feedback on parsing quality during confirmation'
        )
    )

    # ========================================================================
    # Indexes for Parsing Queries
    # ========================================================================

    # Partial index for unparsed articles (WHERE parsing_confirmed = FALSE)
    op.create_index(
        'idx_articles_parsing_confirmed',
        'articles',
        ['parsing_confirmed'],
        unique=False,
        postgresql_where=sa.text('parsing_confirmed = FALSE')
    )

    # Index for recent parsing confirmations
    op.create_index(
        'idx_articles_parsing_confirmed_at',
        'articles',
        [sa.text('parsing_confirmed_at DESC')],
        unique=False
    )

    # ========================================================================
    # Data Migration for Existing Articles
    # ========================================================================

    # Backfill title_main from existing title field
    op.execute("""
        UPDATE articles
        SET title_main = title
        WHERE title_main IS NULL AND title IS NOT NULL;
    """)

    # Backfill body_html from existing body field
    op.execute("""
        UPDATE articles
        SET body_html = body
        WHERE body_html IS NULL AND body IS NOT NULL;
    """)

    # Mark existing articles as already parsed (skip parsing confirmation)
    op.execute("""
        UPDATE articles
        SET
            parsing_confirmed = TRUE,
            parsing_confirmed_at = NOW(),
            parsing_confirmed_by = 'system_migration',
            parsing_feedback = 'Pre-Phase 7 article, parsing not applicable'
        WHERE parsing_confirmed = FALSE
          AND status IN ('published', 'ready_to_publish', 'seo_optimized');
    """)


def downgrade() -> None:
    """Remove Phase 7 article parsing fields from articles table."""

    # Drop indexes
    op.drop_index('idx_articles_parsing_confirmed_at', table_name='articles')
    op.drop_index('idx_articles_parsing_confirmed', table_name='articles')

    # Drop parsing confirmation fields
    op.drop_column('articles', 'parsing_feedback')
    op.drop_column('articles', 'parsing_confirmed_by')
    op.drop_column('articles', 'parsing_confirmed_at')
    op.drop_column('articles', 'parsing_confirmed')

    # Drop SEO fields
    op.drop_column('articles', 'seo_keywords')
    op.drop_column('articles', 'meta_description')

    # Drop body content field
    op.drop_column('articles', 'body_html')

    # Drop author fields
    op.drop_column('articles', 'author_name')
    op.drop_column('articles', 'author_line')

    # Drop title decomposition fields
    op.drop_column('articles', 'title_suffix')
    op.drop_column('articles', 'title_main')
    op.drop_column('articles', 'title_prefix')
