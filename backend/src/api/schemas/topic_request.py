"""Topic request API schemas."""

from datetime import datetime

from pydantic import Field

from src.api.schemas.base import BaseSchema, TimestampSchema
from src.models import TopicRequestPriority, TopicRequestStatus


class TopicRequestCreate(BaseSchema):
    """Schema for creating a topic request."""

    title: str = Field(
        ..., min_length=10, max_length=500, description="Article topic title"
    )
    outline: str | None = Field(
        None, max_length=10000, description="Optional structured outline"
    )
    style_tone: str = Field(
        default="professional",
        max_length=50,
        description="Writing style (professional, casual, technical)",
    )
    target_word_count: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Target article word count",
    )
    priority: TopicRequestPriority = Field(
        default=TopicRequestPriority.NORMAL,
        description="Processing priority",
    )


class TopicRequestResponse(TimestampSchema):
    """Schema for topic request response."""

    id: int
    title: str
    outline: str | None
    style_tone: str
    target_word_count: int
    priority: TopicRequestPriority
    submitted_by: int
    status: TopicRequestStatus
    article_id: int | None
    error_message: str | None


class TopicRequestListResponse(BaseSchema):
    """Schema for topic request list response."""

    id: int
    title: str
    status: TopicRequestStatus
    priority: TopicRequestPriority
    created_at: datetime
    article_id: int | None
