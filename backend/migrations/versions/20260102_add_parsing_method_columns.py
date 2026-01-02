"""Add missing parsing_method and parsing_confidence columns

Revision ID: 20260102_parsing_method
Revises: extracted_faqs_fields
Create Date: 2026-01-02 12:00:00.000000

These columns were defined in the Article model but never had a migration created.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260102_parsing_method'
down_revision = 'extracted_faqs_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add parsing_method and parsing_confidence columns to articles table."""

    # Add parsing_method column
    op.add_column(
        'articles',
        sa.Column(
            'parsing_method',
            sa.String(length=20),
            nullable=True,
            comment="Parsing method used: 'ai' or 'heuristic'"
        )
    )

    # Add parsing_confidence column
    op.add_column(
        'articles',
        sa.Column(
            'parsing_confidence',
            sa.Float(),
            nullable=True,
            comment="Confidence score of parsing (0.0-1.0)"
        )
    )


def downgrade() -> None:
    """Remove parsing_method and parsing_confidence columns."""
    op.drop_column('articles', 'parsing_confidence')
    op.drop_column('articles', 'parsing_method')
