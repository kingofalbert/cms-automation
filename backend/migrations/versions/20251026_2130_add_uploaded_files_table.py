"""Add uploaded_files table for Google Drive tracking

Revision ID: uploaded_files_v1
Revises: 20251026_1229
Create Date: 2025-10-26 21:30:00.000000+00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'uploaded_files_v1'
down_revision: str | None = '20251026_1229'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create uploaded_files table."""
    op.create_table(
        'uploaded_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False, comment='Original filename'),
        sa.Column('drive_file_id', sa.String(length=255), nullable=False, comment='Google Drive file ID'),
        sa.Column('drive_folder_id', sa.String(length=255), nullable=True, comment='Google Drive folder ID'),
        sa.Column('mime_type', sa.String(length=100), nullable=False, comment='MIME type of file'),
        sa.Column('file_size', sa.BigInteger(), nullable=True, comment='File size in bytes'),
        sa.Column('web_view_link', sa.Text(), nullable=True, comment='Google Drive web view link'),
        sa.Column('web_content_link', sa.Text(), nullable=True, comment='Google Drive direct download link'),
        sa.Column('article_id', sa.Integer(), nullable=True, comment='Associated article ID (for featured/additional images)'),
        sa.Column('file_type', sa.String(length=50), nullable=False, comment='File type (image, document, video, other)'),
        sa.Column('uploaded_by', sa.Integer(), nullable=True, comment='User ID who uploaded the file'),
        sa.Column('file_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional file metadata'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='Soft delete timestamp'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_uploaded_files_article_id'), 'uploaded_files', ['article_id'], unique=False)
    op.create_index(op.f('ix_uploaded_files_drive_file_id'), 'uploaded_files', ['drive_file_id'], unique=True)
    op.create_index(op.f('ix_uploaded_files_file_type'), 'uploaded_files', ['file_type'], unique=False)


def downgrade() -> None:
    """Drop uploaded_files table."""
    op.drop_index(op.f('ix_uploaded_files_file_type'), table_name='uploaded_files')
    op.drop_index(op.f('ix_uploaded_files_drive_file_id'), table_name='uploaded_files')
    op.drop_index(op.f('ix_uploaded_files_article_id'), table_name='uploaded_files')
    op.drop_table('uploaded_files')
