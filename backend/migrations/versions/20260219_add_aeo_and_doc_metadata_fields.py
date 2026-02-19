"""Add AEO and document metadata fields to articles.

Revision ID: aeo_doc_metadata_fields
Revises: wordpress_draft_fields
Create Date: 2026-02-19

Phase 15: Add fields for document metadata sections:
1. aeo_type - AEO type (定義解說型, 步驟操作型, etc.)
2. aeo_paragraph - AEO first paragraph for search engine answer boxes
3. seo_title_variants - SEO title variants (資訊型/懸念型)
4. doc_proofreading_suggestions - Proofreading suggestions from 校對結果 section
5. doc_image_alt_texts - Image alt texts from 圖片 Alt Text section
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'aeo_doc_metadata_fields'
down_revision = 'wordpress_draft_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add AEO and document metadata fields to articles table."""
    op.add_column(
        'articles',
        sa.Column('aeo_type', sa.String(50), nullable=True,
                  comment='AEO type from document (e.g., 定義解說型, 步驟操作型, 列表型)')
    )
    op.add_column(
        'articles',
        sa.Column('aeo_paragraph', sa.Text(), nullable=True,
                  comment='AEO first paragraph optimized for search engine answer boxes')
    )
    op.add_column(
        'articles',
        sa.Column('seo_title_variants', JSONB(), nullable=True,
                  comment="SEO title variants from doc [{type: '資訊型', title: '...'}, ...]")
    )
    op.add_column(
        'articles',
        sa.Column('doc_proofreading_suggestions', JSONB(), nullable=True,
                  comment="Proofreading suggestions from document's 校對結果 section")
    )
    op.add_column(
        'articles',
        sa.Column('doc_image_alt_texts', JSONB(), nullable=True,
                  comment="Image alt texts from document's 圖片 Alt Text section with Drive links")
    )


def downgrade() -> None:
    """Remove AEO and document metadata fields."""
    op.drop_column('articles', 'doc_image_alt_texts')
    op.drop_column('articles', 'doc_proofreading_suggestions')
    op.drop_column('articles', 'seo_title_variants')
    op.drop_column('articles', 'aeo_paragraph')
    op.drop_column('articles', 'aeo_type')
