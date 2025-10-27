"""API schemas for article import."""

from typing import Any, Optional

from pydantic import Field

from src.api.schemas.base import BaseSchema


class ImportErrorSchema(BaseSchema):
    """Schema for individual import error."""

    row_number: int = Field(..., description="Row number that failed")
    error_message: str = Field(..., description="Error description")
    raw_data: dict[str, Any] = Field(default_factory=dict, description="Raw data that failed")


class ImportResultSchema(BaseSchema):
    """Schema for import result."""

    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status (pending, running, completed, failed)")
    total_records: int = Field(..., description="Total records in file")
    successful_imports: int = Field(..., description="Number of successful imports")
    failed_imports: int = Field(..., description="Number of failed imports")
    success_rate: float = Field(..., description="Success rate percentage")
    imported_article_ids: list[int] = Field(
        default_factory=list,
        description="List of imported article IDs",
    )
    errors: list[ImportErrorSchema] = Field(
        default_factory=list,
        description="List of import errors",
    )


class ImportTaskStatusSchema(BaseSchema):
    """Schema for import task status check."""

    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status (PENDING, STARTED, SUCCESS, FAILURE)")
    result: Optional[ImportResultSchema] = Field(None, description="Task result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")


class ImportInitiateResponse(BaseSchema):
    """Schema for import initiation response."""

    task_id: str = Field(..., description="Celery task ID for tracking")
    message: str = Field(..., description="Status message")
    status_url: str = Field(..., description="URL to check task status")
