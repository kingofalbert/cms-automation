"""Schemas for publishing API."""

from datetime import datetime
from typing import List, Optional

from pydantic import Field

from src.api.schemas.base import BaseSchema


class PublishOptions(BaseSchema):
    """Publishing options provided by the client."""

    seo_optimization: bool = Field(
        default=True, description="Run SEO optimization steps during publishing"
    )
    publish_immediately: bool = Field(
        default=True,
        description="Publish immediately instead of scheduling for later",
    )
    tags: Optional[List[str]] = Field(
        default=None, description="Tags to assign to the article"
    )
    categories: Optional[List[str]] = Field(
        default=None, description="Categories to assign to the article"
    )


class PublishRequest(BaseSchema):
    """Request payload for submitting a publishing task."""

    provider: str = Field(
        ...,
        pattern=r"^(playwright|computer_use|hybrid)$",
        description="Publishing provider to use",
    )
    options: PublishOptions = Field(
        default_factory=PublishOptions,
        description="Publishing configuration options",
    )


class PublishResult(BaseSchema):
    """Response returned after submitting a publishing task."""

    task_id: str = Field(..., description="Identifier of the publishing task")
    status: str = Field(..., description="Initial task status")
    message: str = Field(..., description="Status message for the submission")


class Screenshot(BaseSchema):
    """Metadata describing a captured publishing screenshot."""

    step: str = Field(..., description="Workflow step name for the screenshot")
    timestamp: datetime = Field(
        ..., description="Timestamp when screenshot was captured"
    )
    image_url: str = Field(..., description="Location of the screenshot image")
    description: Optional[str] = Field(
        default=None, description="Optional description for the screenshot"
    )


class PublishTaskResponse(BaseSchema):
    """Detailed representation of a publishing task."""

    id: int = Field(..., description="Database identifier for the task")
    article_id: int = Field(..., description="Associated article identifier")
    article_title: str = Field(..., description="Title of the associated article")
    provider: str = Field(..., description="Publishing provider name")
    status: str = Field(..., description="Current task status")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    current_step: str = Field(..., description="Current workflow step")
    total_steps: int = Field(..., ge=1, description="Total workflow steps")
    completed_steps: int = Field(
        ..., ge=0, description="Number of completed workflow steps"
    )
    screenshots: List[Screenshot] = Field(
        default_factory=list, description="Captured screenshots for the task"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message when task fails"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Timestamp when task execution started"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Timestamp when task execution finished"
    )
    duration: Optional[int] = Field(
        default=None, description="Total execution duration in seconds"
    )
    cost: Optional[float] = Field(
        default=None, ge=0, description="Cost in USD for this task"
    )
