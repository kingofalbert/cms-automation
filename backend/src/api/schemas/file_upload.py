"""Schemas for file upload operations."""

from datetime import datetime

from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """Response after successful file upload."""

    file_id: int = Field(description="Database file ID")
    drive_file_id: str = Field(description="Google Drive file ID")
    filename: str = Field(description="Original filename")
    file_type: str = Field(description="File type classification (image, document, video, other)")
    mime_type: str = Field(description="MIME type")
    file_size: int | None = Field(None, description="File size in bytes")
    web_view_link: str | None = Field(None, description="Google Drive web view link")
    web_content_link: str | None = Field(None, description="Google Drive direct download link")
    public_url: str | None = Field(None, description="Public access URL")
    article_id: int | None = Field(None, description="Associated article ID")
    created_at: datetime = Field(description="Upload timestamp")

    class Config:
        from_attributes = True


class FileMetadataResponse(BaseModel):
    """File metadata response."""

    file_id: int
    filename: str
    drive_file_id: str
    drive_folder_id: str | None = None
    mime_type: str
    file_size: int | None = None
    file_type: str
    web_view_link: str | None = None
    web_content_link: str | None = None
    public_url: str | None = None
    article_id: int | None = None
    uploaded_by: int | None = None
    file_metadata: dict | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @property
    def is_image(self) -> bool:
        """Check if file is an image."""
        return self.file_type == "image" or self.mime_type.startswith("image/")


class FileListResponse(BaseModel):
    """Response for file listing."""

    files: list[FileMetadataResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class BulkUploadResponse(BaseModel):
    """Response for bulk file upload."""

    successful_uploads: list[FileUploadResponse]
    failed_uploads: list[dict]
    total_uploaded: int
    total_failed: int


class FileDeleteResponse(BaseModel):
    """Response after file deletion."""

    file_id: int
    drive_file_id: str
    deleted: bool
    message: str
