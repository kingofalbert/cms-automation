"""change_suggested_seo_keywords_to_array

Revision ID: 9b8622d858cf
Revises: af50da9ccee0
Create Date: 2025-11-20 00:06:32.571398+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b8622d858cf'
down_revision: Union[str, None] = 'af50da9ccee0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change suggested_seo_keywords from JSONB to ARRAY(String)
    # First, create a temporary column
    op.add_column('articles', sa.Column('suggested_seo_keywords_temp', sa.ARRAY(sa.String()), nullable=True))

    # Copy data: if JSONB contains an array, use it; if it's a dict with a "keywords" key, extract it
    op.execute("""
        UPDATE articles
        SET suggested_seo_keywords_temp =
            CASE
                WHEN jsonb_typeof(suggested_seo_keywords) = 'array' THEN
                    ARRAY(SELECT jsonb_array_elements_text(suggested_seo_keywords))
                WHEN suggested_seo_keywords ? 'keywords' THEN
                    ARRAY(SELECT jsonb_array_elements_text(suggested_seo_keywords->'keywords'))
                ELSE NULL
            END
        WHERE suggested_seo_keywords IS NOT NULL
    """)

    # Drop old column and rename new one
    op.drop_column('articles', 'suggested_seo_keywords')
    op.alter_column('articles', 'suggested_seo_keywords_temp', new_column_name='suggested_seo_keywords')


def downgrade() -> None:
    # Reverse: change from ARRAY back to JSONB
    op.add_column('articles', sa.Column('suggested_seo_keywords_temp', sa.dialects.postgresql.JSONB(), nullable=True))

    # Convert array to JSONB array
    op.execute("""
        UPDATE articles
        SET suggested_seo_keywords_temp = to_jsonb(suggested_seo_keywords)
        WHERE suggested_seo_keywords IS NOT NULL
    """)

    op.drop_column('articles', 'suggested_seo_keywords')
    op.alter_column('articles', 'suggested_seo_keywords_temp', new_column_name='suggested_seo_keywords')
