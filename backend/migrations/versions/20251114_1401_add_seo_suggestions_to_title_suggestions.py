"""add_seo_suggestions_to_title_suggestions

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-11-14 14:01:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add suggested_seo_titles field to title_suggestions table.

    This migration adds a JSONB column to store AI-generated SEO Title suggestions (2-3 variants).
    We also update the comment on suggested_title_sets to clarify it's for H1 titles.

    JSONB structure:
    {
      "variants": [
        {
          "id": "seo_variant_1",
          "seo_title": "2024年AI醫療創新趨勢",
          "reasoning": "聚焦核心關鍵字...",
          "keywords_focus": ["AI醫療", "創新", "2024"],
          "character_count": 12
        },
        ...
      ],
      "original_seo_title": "2024年醫療保健創新趨勢",
      "notes": ["SEO Title 建議保持在 30 字以內", ...]
    }
    """
    # Add suggested_seo_titles column
    op.add_column(
        'title_suggestions',
        sa.Column(
            'suggested_seo_titles',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='AI生成的 SEO Title 建議 (2-3 個選項，30字左右，用於<title>標籤)'
        )
    )

    # Update comment on suggested_title_sets to clarify it's for H1 titles
    # Note: Alembic doesn't directly support updating column comments,
    # so we use raw SQL
    op.execute("""
        COMMENT ON COLUMN title_suggestions.suggested_title_sets IS
        'AI生成的 H1 標題建議 (prefix + main + suffix 組合，用於頁面內容)'
    """)


def downgrade() -> None:
    """Remove suggested_seo_titles field from title_suggestions table."""
    # Restore original comment
    op.execute("""
        COMMENT ON COLUMN title_suggestions.suggested_title_sets IS
        'AI生成的標題建議'
    """)

    # Drop the new column
    op.drop_column('title_suggestions', 'suggested_seo_titles')
