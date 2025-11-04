"""API schemas for SEO analysis tasks."""


from pydantic import Field

from src.api.schemas.base import BaseSchema


class SEOAnalysisSingleResponse(BaseSchema):
    """Schema for single article SEO analysis response."""

    task_id: str = Field(..., description="Celery task ID")
    message: str = Field(..., description="Status message")
    article_id: int = Field(..., description="Article ID being analyzed")
    status_url: str = Field(..., description="URL to check task status")


class SEOAnalysisBatchResponse(BaseSchema):
    """Schema for batch SEO analysis response."""

    task_id: str = Field(..., description="Celery task ID")
    message: str = Field(..., description="Status message")
    limit: int | None = Field(None, description="Limit on articles to process")
    status_url: str = Field(..., description="URL to check task status")


class SEOTaskStatusResponse(BaseSchema):
    """Schema for SEO task status check."""

    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status (PENDING, STARTED, SUCCESS, FAILURE)")
    result: dict | None = Field(None, description="Task result if completed")
    error: str | None = Field(None, description="Error message if failed")


class SEOSingleResult(BaseSchema):
    """Schema for single article SEO analysis result."""

    article_id: int
    seo_id: int
    focus_keyword: str
    seo_score: float
    readability_score: float | None
    status: str


class SEOBatchResult(BaseSchema):
    """Schema for batch SEO analysis result."""

    successful_count: int
    failed_count: int
    total_count: int
    errors: list[str]
    status: str
