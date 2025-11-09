"""Create article_images and article_image_reviews tables for Phase 7

Revision ID: 20251108_1700
Revises: 20251108_1600
Create Date: 2025-11-08 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251108_1700'
down_revision = '20251108_1600'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create article_images and article_image_reviews tables for Phase 7 structured parsing.

    This migration creates:
    - article_images: Stores image metadata, paths, and technical specifications
    - article_image_reviews: Tracks user review actions during parsing confirmation
    """

    # ========================================================================
    # 1. CREATE article_images TABLE
    # ========================================================================
    op.create_table(
        'article_images',

        # Primary key
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),

        # Foreign key to articles
        sa.Column(
            'article_id',
            sa.Integer(),
            sa.ForeignKey('articles.id', ondelete='CASCADE'),
            nullable=False,
            comment='Article this image belongs to'
        ),

        # Image file paths
        sa.Column(
            'preview_path',
            sa.String(length=500),
            nullable=True,
            comment='Path to preview/thumbnail image in storage'
        ),

        sa.Column(
            'source_path',
            sa.String(length=500),
            nullable=True,
            comment='Path to downloaded high-resolution source image'
        ),

        sa.Column(
            'source_url',
            sa.String(length=1000),
            nullable=True,
            comment='Original "原圖/點此下載" URL from Google Doc'
        ),

        # Image content
        sa.Column(
            'caption',
            sa.Text(),
            nullable=True,
            comment='Image caption extracted from document'
        ),

        # Position in article
        sa.Column(
            'position',
            sa.Integer(),
            nullable=False,
            comment='Paragraph index (0-based) where image should appear in body'
        ),

        # Technical specifications (JSONB)
        sa.Column(
            'metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Technical image metadata: dimensions, file size, format, EXIF'
        ),

        # Timestamps
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text('NOW()')
        ),

        sa.Column(
            'updated_at',
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text('NOW()')
        ),

        # Constraints
        sa.CheckConstraint(
            'position >= 0',
            name='article_images_positive_position'
        ),

        sa.UniqueConstraint(
            'article_id',
            'position',
            name='article_images_unique_position'
        ),

        comment='Stores structured information about images extracted from articles'
    )

    # Indexes for article_images
    op.create_index(
        'idx_article_images_article_id',
        'article_images',
        ['article_id'],
        unique=False
    )

    op.create_index(
        'idx_article_images_position',
        'article_images',
        ['article_id', 'position'],
        unique=False
    )

    op.create_index(
        'idx_article_images_created_at',
        'article_images',
        [sa.text('created_at DESC')],
        unique=False
    )

    # GIN index for JSONB metadata queries (optional, for advanced filtering)
    op.create_index(
        'idx_article_images_metadata_gin',
        'article_images',
        ['metadata'],
        unique=False,
        postgresql_using='gin'
    )

    # ========================================================================
    # 2. CREATE article_image_reviews TABLE
    # ========================================================================
    op.create_table(
        'article_image_reviews',

        # Primary key
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),

        # Foreign key to article_images
        sa.Column(
            'article_image_id',
            sa.Integer(),
            sa.ForeignKey('article_images.id', ondelete='CASCADE'),
            nullable=False,
            comment='Image being reviewed'
        ),

        # Optional link to worklist (if worklist system is used)
        sa.Column(
            'worklist_item_id',
            sa.Integer(),
            nullable=True,
            comment='Optional FK to worklist_items table'
        ),

        # Review action
        sa.Column(
            'action',
            sa.String(length=20),
            nullable=False,
            comment='Action taken: keep|remove|replace_caption|replace_source'
        ),

        # Replacement data (conditional based on action)
        sa.Column(
            'new_caption',
            sa.Text(),
            nullable=True,
            comment='Replacement caption if action=replace_caption'
        ),

        sa.Column(
            'new_source_url',
            sa.String(length=1000),
            nullable=True,
            comment='Replacement source URL if action=replace_source'
        ),

        # Review notes
        sa.Column(
            'reviewer_notes',
            sa.Text(),
            nullable=True,
            comment='Notes explaining the review decision or rationale'
        ),

        # Timestamp
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text('NOW()')
        ),

        # Constraints
        sa.CheckConstraint(
            "action IN ('keep', 'remove', 'replace_caption', 'replace_source')",
            name='article_image_reviews_valid_action'
        ),

        # If action is 'replace_caption', new_caption must be provided
        sa.CheckConstraint(
            "action != 'replace_caption' OR new_caption IS NOT NULL",
            name='article_image_reviews_caption_required'
        ),

        # If action is 'replace_source', new_source_url must be provided
        sa.CheckConstraint(
            "action != 'replace_source' OR new_source_url IS NOT NULL",
            name='article_image_reviews_source_required'
        ),

        comment='Tracks reviewer feedback and actions on individual images during parsing confirmation'
    )

    # Indexes for article_image_reviews
    op.create_index(
        'idx_article_image_reviews_article_image',
        'article_image_reviews',
        ['article_image_id'],
        unique=False
    )

    op.create_index(
        'idx_article_image_reviews_worklist_item',
        'article_image_reviews',
        ['worklist_item_id'],
        unique=False
    )

    op.create_index(
        'idx_article_image_reviews_action',
        'article_image_reviews',
        ['action'],
        unique=False
    )

    op.create_index(
        'idx_article_image_reviews_created_at',
        'article_image_reviews',
        [sa.text('created_at DESC')],
        unique=False
    )

    # ========================================================================
    # 3. CREATE TRIGGER FOR article_images.updated_at
    # ========================================================================

    # Ensure the update_updated_at_column() function exists
    # (It should already exist from previous migrations, but we define it here for safety)
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Apply trigger to article_images table
    op.execute("""
        CREATE TRIGGER update_article_images_updated_at
            BEFORE UPDATE ON article_images
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Remove article_images and article_image_reviews tables."""

    # Drop trigger first
    op.execute("DROP TRIGGER IF EXISTS update_article_images_updated_at ON article_images;")

    # Drop article_image_reviews table (must drop first due to FK dependency)
    op.drop_index('idx_article_image_reviews_created_at', table_name='article_image_reviews')
    op.drop_index('idx_article_image_reviews_action', table_name='article_image_reviews')
    op.drop_index('idx_article_image_reviews_worklist_item', table_name='article_image_reviews')
    op.drop_index('idx_article_image_reviews_article_image', table_name='article_image_reviews')
    op.drop_table('article_image_reviews')

    # Drop article_images table
    op.drop_index('idx_article_images_metadata_gin', table_name='article_images')
    op.drop_index('idx_article_images_created_at', table_name='article_images')
    op.drop_index('idx_article_images_position', table_name='article_images')
    op.drop_index('idx_article_images_article_id', table_name='article_images')
    op.drop_table('article_images')

    # Note: We don't drop the update_updated_at_column() function as it may be used by other tables
