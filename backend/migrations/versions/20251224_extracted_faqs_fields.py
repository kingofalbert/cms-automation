"""Add extracted FAQs fields for FAQ comparison feature.

Revision ID: extracted_faqs_fields
Revises: faq_v2_assessment
Create Date: 2025-12-24

This migration adds:
1. extracted_faqs JSONB field to store FAQs extracted from original article HTML
2. extracted_faqs_detection_method to track how FAQs were detected
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'extracted_faqs_fields'
down_revision = 'faq_v2_assessment'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add extracted FAQs fields to articles table."""
    op.add_column(
        'articles',
        sa.Column('extracted_faqs', JSONB(), nullable=True,
                  comment='FAQs extracted from existing article HTML')
    )
    op.add_column(
        'articles',
        sa.Column('extracted_faqs_detection_method', sa.String(50), nullable=True,
                  comment='How extracted FAQs were detected: text_markers, html_comment, css_class, etc.')
    )


def downgrade() -> None:
    """Remove extracted FAQs fields."""
    op.drop_column('articles', 'extracted_faqs_detection_method')
    op.drop_column('articles', 'extracted_faqs')
