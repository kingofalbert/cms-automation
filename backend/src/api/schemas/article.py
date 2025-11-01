"""Article API schemas."""

from datetime import datetime

from pydantic import Field

from src.api.schemas.base import BaseSchema, TimestampSchema
from src.models import ArticleStatus


class ArticleResponse(TimestampSchema):
    """Schema for article response."""

    id: int
    title: str
    body: str
    status: ArticleStatus
    author_id: int
    cms_article_id: str | None
    published_at: datetime | None
    article_metadata: dict
    formatting: dict
    proofreading_issues: list[dict] = Field(default_factory=list)
    critical_issues_count: int = 0
    tags: list[str] = Field(default_factory=list, description="WordPress post tags (3-6 categories)")
    categories: list[str] = Field(default_factory=list, description="WordPress post categories")


class ArticleListResponse(BaseSchema):
    """Schema for article list response."""

    id: int
    title: str
    status: ArticleStatus
    author_id: int
    created_at: datetime
    published_at: datetime | None


class ArticlePreview(BaseSchema):
    """Schema for article preview (minimal info)."""

    id: int
    title: str
    excerpt: str = Field(..., description="First 200 characters of body")
    status: ArticleStatus
    created_at: datetime
