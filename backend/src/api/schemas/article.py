"""Article API schemas."""

from datetime import datetime
from typing import Any

from pydantic import Field

from src.api.schemas.base import BaseSchema, TimestampSchema
from src.models import ArticleStatus


class ArticleImageResponse(BaseSchema):
    """Response schema for article images extracted during parsing."""

    id: int = Field(..., description="Image identifier")
    article_id: int = Field(..., description="Article this image belongs to")
    preview_path: str | None = Field(default=None, description="Path to preview/thumbnail in storage")
    source_path: str | None = Field(default=None, description="Path to downloaded high-res source")
    source_url: str | None = Field(default=None, description='Original "原圖/點此下載" URL from Google Doc')
    caption: str | None = Field(default=None, description="Image caption extracted from document")
    position: int = Field(..., description="Paragraph index (0-based) where image appears")
    image_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Technical metadata: dimensions, file size, format, EXIF"
    )


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


# Proofreading Review Workflow Schemas

class ContentComparison(BaseSchema):
    """Content comparison for review."""

    original: str
    suggested: str | None = None
    changes: dict | None = Field(None, description="Diff data structure")


class MetaComparison(BaseSchema):
    """Meta description comparison."""

    original: str | None = None
    suggested: str | None = None
    reasoning: str | None = None
    score: float | None = Field(None, ge=0, le=1, description="Quality score 0-1")
    length_original: int = 0
    length_suggested: int = 0


class SEOComparison(BaseSchema):
    """SEO keywords comparison."""

    original_keywords: list[str] = Field(default_factory=list)
    suggested_keywords: dict | None = None
    reasoning: str | None = None
    score: float | None = Field(None, ge=0, le=1, description="Quality score 0-1")


class FAQProposal(BaseSchema):
    """FAQ schema proposal variant."""

    questions: list[dict] = Field(default_factory=list, description="FAQ question-answer pairs")
    schema_type: str = Field(..., description="FAQ schema type (e.g., 'FAQPage')")
    score: float | None = None


class ParagraphSuggestion(BaseSchema):
    """Paragraph optimization suggestion."""

    paragraph_index: int
    original_text: str
    suggested_text: str
    reasoning: str
    improvement_type: str = Field(..., description="split/merge/rewrite/reorder")


class ProofreadingDecisionDetail(BaseSchema):
    """Detailed proofreading decision record."""

    issue_id: str
    decision_type: str = Field(..., description="accepted/rejected/modified")
    rationale: str | None = None
    modified_content: str | None = None
    reviewer: str
    decided_at: datetime


class ArticleReviewResponse(BaseSchema):
    """Complete article review data for ProofreadingReviewPage."""

    # Basic info
    id: int
    title: str
    status: ArticleStatus

    # Content comparison
    content: ContentComparison

    # Meta comparison
    meta: MetaComparison

    # SEO comparison
    seo: SEOComparison

    # FAQ proposals
    faq_proposals: list[FAQProposal] = Field(default_factory=list)

    # Paragraph suggestions
    paragraph_suggestions: list[ParagraphSuggestion] = Field(default_factory=list)

    # Proofreading issues
    proofreading_issues: list[dict] = Field(default_factory=list)

    # Existing decisions (hydrate from database)
    existing_decisions: list[ProofreadingDecisionDetail] = Field(default_factory=list)

    # AI metadata
    ai_model_used: str | None = None
    suggested_generated_at: datetime | None = None
    generation_cost: float | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
