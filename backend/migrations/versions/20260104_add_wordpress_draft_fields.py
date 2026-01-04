"""Add WordPress draft tracking fields to worklist_items.

Revision ID: wordpress_draft_fields
Revises: extracted_faqs_fields
Create Date: 2026-01-04

This migration adds fields to track WordPress draft uploads:
1. wordpress_draft_url - URL of the WordPress draft
2. wordpress_draft_uploaded_at - Timestamp when draft was uploaded
3. wordpress_post_id - WordPress post ID
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'wordpress_draft_fields'
down_revision = 'extracted_faqs_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add WordPress draft tracking fields to worklist_items table."""
    op.add_column(
        'worklist_items',
        sa.Column('wordpress_draft_url', sa.String(500), nullable=True,
                  comment='WordPress draft editor URL after upload')
    )
    op.add_column(
        'worklist_items',
        sa.Column('wordpress_draft_uploaded_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Timestamp when draft was uploaded to WordPress')
    )
    op.add_column(
        'worklist_items',
        sa.Column('wordpress_post_id', sa.Integer(), nullable=True,
                  comment='WordPress post ID')
    )


def downgrade() -> None:
    """Remove WordPress draft tracking fields."""
    op.drop_column('worklist_items', 'wordpress_post_id')
    op.drop_column('worklist_items', 'wordpress_draft_uploaded_at')
    op.drop_column('worklist_items', 'wordpress_draft_url')
