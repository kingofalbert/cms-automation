"""Add article suggested fields for proofreading workflow

Revision ID: 20251107_1500
Revises: 20251107_1000
Create Date: 2025-11-07 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251107_1500'
down_revision = '20251107_1000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add 14 suggested_* fields to articles table for proofreading review workflow."""

    # Content optimization fields
    op.add_column('articles', sa.Column('suggested_content', sa.Text(), nullable=True, comment='AI-optimized article content'))
    op.add_column('articles', sa.Column('suggested_content_changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Diff data structure for content changes'))

    # Meta description suggestion fields
    op.add_column('articles', sa.Column('suggested_meta_description', sa.Text(), nullable=True, comment='AI-suggested meta description'))
    op.add_column('articles', sa.Column('suggested_meta_reasoning', sa.Text(), nullable=True, comment='AI reasoning for meta description suggestion'))
    op.add_column('articles', sa.Column('suggested_meta_score', sa.Float(), nullable=True, comment='Meta description quality score (0-1)'))

    # SEO keywords suggestion fields
    op.add_column('articles', sa.Column('suggested_seo_keywords', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='AI-suggested SEO keywords array'))
    op.add_column('articles', sa.Column('suggested_keywords_reasoning', sa.Text(), nullable=True, comment='AI reasoning for SEO keywords'))
    op.add_column('articles', sa.Column('suggested_keywords_score', sa.Float(), nullable=True, comment='SEO keywords quality score (0-1)'))

    # Paragraph and structure suggestion fields
    op.add_column('articles', sa.Column('paragraph_suggestions', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Paragraph optimization suggestions'))
    op.add_column('articles', sa.Column('paragraph_split_suggestions', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Paragraph splitting recommendations'))

    # FAQ schema proposal field
    op.add_column('articles', sa.Column('faq_schema_proposals', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Multiple FAQ schema variants for review'))

    # AI generation metadata fields
    op.add_column('articles', sa.Column('suggested_generated_at', sa.DateTime(), nullable=True, comment='Timestamp when AI suggestions were generated'))
    op.add_column('articles', sa.Column('ai_model_used', sa.String(length=100), nullable=True, comment='AI model identifier used for suggestions'))
    op.add_column('articles', sa.Column('generation_cost', sa.Numeric(precision=10, scale=4), nullable=True, comment='API cost for generating suggestions (USD)'))


def downgrade() -> None:
    """Remove the suggested_* fields from articles table."""

    op.drop_column('articles', 'generation_cost')
    op.drop_column('articles', 'ai_model_used')
    op.drop_column('articles', 'suggested_generated_at')
    op.drop_column('articles', 'faq_schema_proposals')
    op.drop_column('articles', 'paragraph_split_suggestions')
    op.drop_column('articles', 'paragraph_suggestions')
    op.drop_column('articles', 'suggested_keywords_score')
    op.drop_column('articles', 'suggested_keywords_reasoning')
    op.drop_column('articles', 'suggested_seo_keywords')
    op.drop_column('articles', 'suggested_meta_score')
    op.drop_column('articles', 'suggested_meta_reasoning')
    op.drop_column('articles', 'suggested_meta_description')
    op.drop_column('articles', 'suggested_content_changes')
    op.drop_column('articles', 'suggested_content')
