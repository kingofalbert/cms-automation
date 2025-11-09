"""Add unified optimization tables for Phase 7 AI optimization

Revision ID: 20251108_1800
Revises: 20251108_1700
Create Date: 2025-11-08 18:00:00.000000

This migration creates tables for the unified AI optimization service:
- title_suggestions: Stores AI-generated title optimization suggestions
- seo_suggestions: Stores SEO keywords, meta description, and tags recommendations
- article_faqs: Stores FAQ questions and answers for AI search optimization

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251108_1800'
down_revision = '20251108_1700'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create unified optimization tables for AI-generated suggestions.

    This migration implements the unified optimization architecture that generates
    all suggestions (title + SEO + FAQ) in a single AI API call, saving 40-60% cost.

    Tables created:
    1. title_suggestions: Title optimization (3-part structure: prefix/main/suffix)
    2. seo_suggestions: SEO keywords (focus/primary/secondary), meta description, tags
    3. article_faqs: FAQ questions and answers (8-10 per article)

    Also adds tracking fields to articles table for optimization generation metadata.
    """

    # ========================================================================
    # Table 1: title_suggestions
    # ========================================================================
    op.create_table(
        'title_suggestions',
        # Primary key
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),

        # Foreign key to articles
        sa.Column(
            'article_id',
            sa.Integer(),
            nullable=False,
            comment='Reference to article for which suggestions were generated'
        ),

        # Original title components
        sa.Column(
            'original_title_prefix',
            sa.String(length=200),
            nullable=True,
            comment='Original title prefix (if exists), e.g., "深度解析"'
        ),
        sa.Column(
            'original_title_main',
            sa.String(length=500),
            nullable=False,
            comment='Original main title'
        ),
        sa.Column(
            'original_title_suffix',
            sa.String(length=200),
            nullable=True,
            comment='Original title suffix (if exists), e.g., "权威指南"'
        ),

        # AI-generated suggestions (JSONB for flexibility)
        sa.Column(
            'suggested_title_sets',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment='Array of 2-3 title optimization options with scores and types'
        ),

        # Optimization notes
        sa.Column(
            'optimization_notes',
            postgresql.ARRAY(sa.Text()),
            nullable=True,
            comment='General optimization notes from AI'
        ),

        # Metadata
        sa.Column(
            'generated_at',
            sa.TIMESTAMP(),
            server_default=sa.text('NOW()'),
            nullable=False,
            comment='When these suggestions were generated'
        ),
        sa.Column(
            'generated_by',
            sa.String(length=100),
            server_default=sa.text("'unified_optimization_service'"),
            nullable=False,
            comment='Service or user who generated suggestions'
        ),

        # Constraints
        sa.ForeignKeyConstraint(
            ['article_id'],
            ['articles.id'],
            name='fk_title_suggestions_article_id',
            ondelete='CASCADE'
        ),
        sa.UniqueConstraint(
            'article_id',
            name='uq_title_suggestions_article_id'
        )
    )

    # Indexes for title_suggestions
    op.create_index(
        'idx_title_suggestions_article_id',
        'title_suggestions',
        ['article_id'],
        unique=False
    )
    op.create_index(
        'idx_title_suggestions_generated_at',
        'title_suggestions',
        [sa.text('generated_at DESC')],
        unique=False
    )

    # ========================================================================
    # Table 2: seo_suggestions
    # ========================================================================
    op.create_table(
        'seo_suggestions',
        # Primary key
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),

        # Foreign key to articles
        sa.Column(
            'article_id',
            sa.Integer(),
            nullable=False,
            comment='Reference to article for which SEO suggestions were generated'
        ),

        # Focus keyword (main SEO keyword)
        sa.Column(
            'focus_keyword',
            sa.String(length=100),
            nullable=True,
            comment='Primary SEO keyword (1)'
        ),
        sa.Column(
            'focus_keyword_rationale',
            sa.Text(),
            nullable=True,
            comment='AI explanation for why this focus keyword was chosen'
        ),

        # Primary and secondary keywords
        sa.Column(
            'primary_keywords',
            postgresql.ARRAY(sa.Text()),
            nullable=True,
            comment='Primary keywords (3-5)'
        ),
        sa.Column(
            'secondary_keywords',
            postgresql.ARRAY(sa.Text()),
            nullable=True,
            comment='Secondary keywords (5-10)'
        ),

        # Keyword difficulty and search volume estimates
        sa.Column(
            'keyword_difficulty',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Difficulty scores for keywords'
        ),
        sa.Column(
            'search_volume_estimate',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Estimated search volume for keywords'
        ),

        # Meta description
        sa.Column(
            'suggested_meta_description',
            sa.Text(),
            nullable=True,
            comment='AI-optimized meta description (150-160 chars)'
        ),
        sa.Column(
            'meta_description_improvements',
            postgresql.ARRAY(sa.Text()),
            nullable=True,
            comment='List of improvements made to meta description'
        ),
        sa.Column(
            'meta_description_score',
            sa.Integer(),
            nullable=True,
            comment='Quality score for meta description (0-100)'
        ),

        # Tags
        sa.Column(
            'suggested_tags',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Array of suggested tags with relevance scores'
        ),
        sa.Column(
            'tag_strategy',
            sa.Text(),
            nullable=True,
            comment='AI strategy explanation for tag recommendations'
        ),

        # Metadata
        sa.Column(
            'generated_at',
            sa.TIMESTAMP(),
            server_default=sa.text('NOW()'),
            nullable=False,
            comment='When these SEO suggestions were generated'
        ),

        # Constraints
        sa.ForeignKeyConstraint(
            ['article_id'],
            ['articles.id'],
            name='fk_seo_suggestions_article_id',
            ondelete='CASCADE'
        ),
        sa.UniqueConstraint(
            'article_id',
            name='uq_seo_suggestions_article_id'
        )
    )

    # Indexes for seo_suggestions
    op.create_index(
        'idx_seo_suggestions_article_id',
        'seo_suggestions',
        ['article_id'],
        unique=False
    )
    op.create_index(
        'idx_seo_suggestions_focus_keyword',
        'seo_suggestions',
        ['focus_keyword'],
        unique=False
    )

    # ========================================================================
    # Table 3: article_faqs
    # ========================================================================
    op.create_table(
        'article_faqs',
        # Primary key
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),

        # Foreign key to articles
        sa.Column(
            'article_id',
            sa.Integer(),
            nullable=False,
            comment='Reference to article for which FAQ was generated'
        ),

        # FAQ content
        sa.Column(
            'question',
            sa.Text(),
            nullable=False,
            comment='FAQ question'
        ),
        sa.Column(
            'answer',
            sa.Text(),
            nullable=False,
            comment='FAQ answer (50-150 characters recommended)'
        ),

        # FAQ classification
        sa.Column(
            'question_type',
            sa.String(length=20),
            nullable=True,
            comment='Type: factual, how_to, comparison, definition'
        ),
        sa.Column(
            'search_intent',
            sa.String(length=20),
            nullable=True,
            comment='Intent: informational, navigational, transactional'
        ),

        # Keywords covered by this FAQ
        sa.Column(
            'keywords_covered',
            postgresql.ARRAY(sa.Text()),
            nullable=True,
            comment='Keywords naturally covered in this FAQ'
        ),

        # Confidence score
        sa.Column(
            'confidence',
            sa.DECIMAL(precision=3, scale=2),
            nullable=True,
            comment='AI confidence score for this FAQ (0.00-1.00)'
        ),

        # Position and status
        sa.Column(
            'position',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('0'),
            comment='Display order (0-based index)'
        ),
        sa.Column(
            'status',
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'draft'"),
            comment='Status: draft, approved, rejected, published'
        ),

        # Metadata
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text('NOW()'),
            nullable=False,
            comment='When this FAQ was created'
        ),

        # Constraints
        sa.ForeignKeyConstraint(
            ['article_id'],
            ['articles.id'],
            name='fk_article_faqs_article_id',
            ondelete='CASCADE'
        )
    )

    # Indexes for article_faqs
    op.create_index(
        'idx_article_faqs_article_id',
        'article_faqs',
        ['article_id'],
        unique=False
    )
    op.create_index(
        'idx_article_faqs_status',
        'article_faqs',
        ['status'],
        unique=False
    )
    op.create_index(
        'idx_article_faqs_position',
        'article_faqs',
        ['article_id', 'position'],
        unique=False
    )

    # ========================================================================
    # Add unified optimization tracking fields to articles table
    # ========================================================================
    op.add_column(
        'articles',
        sa.Column(
            'unified_optimization_generated',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('FALSE'),
            comment='Whether unified optimization (title+SEO+FAQ) has been generated'
        )
    )

    op.add_column(
        'articles',
        sa.Column(
            'unified_optimization_generated_at',
            sa.TIMESTAMP(),
            nullable=True,
            comment='When unified optimization was generated'
        )
    )

    op.add_column(
        'articles',
        sa.Column(
            'unified_optimization_cost',
            sa.DECIMAL(precision=10, scale=4),
            nullable=True,
            comment='Cost in USD for generating unified optimization'
        )
    )

    # Index for articles with/without optimization
    op.create_index(
        'idx_articles_unified_optimization_generated',
        'articles',
        ['unified_optimization_generated'],
        unique=False,
        postgresql_where=sa.text('unified_optimization_generated = FALSE')
    )


def downgrade() -> None:
    """Remove unified optimization tables and fields."""

    # Drop index from articles table
    op.drop_index(
        'idx_articles_unified_optimization_generated',
        table_name='articles'
    )

    # Drop columns from articles table
    op.drop_column('articles', 'unified_optimization_cost')
    op.drop_column('articles', 'unified_optimization_generated_at')
    op.drop_column('articles', 'unified_optimization_generated')

    # Drop article_faqs table
    op.drop_index('idx_article_faqs_position', table_name='article_faqs')
    op.drop_index('idx_article_faqs_status', table_name='article_faqs')
    op.drop_index('idx_article_faqs_article_id', table_name='article_faqs')
    op.drop_table('article_faqs')

    # Drop seo_suggestions table
    op.drop_index('idx_seo_suggestions_focus_keyword', table_name='seo_suggestions')
    op.drop_index('idx_seo_suggestions_article_id', table_name='seo_suggestions')
    op.drop_table('seo_suggestions')

    # Drop title_suggestions table
    op.drop_index('idx_title_suggestions_generated_at', table_name='title_suggestions')
    op.drop_index('idx_title_suggestions_article_id', table_name='title_suggestions')
    op.drop_table('title_suggestions')
