"""SEO metadata schemas."""

from pydantic import Field, field_validator

from src.api.schemas.base import BaseSchema


class SEOMetadata(BaseSchema):
    """Schema for SEO metadata."""

    meta_title: str = Field(
        ...,
        min_length=10,
        max_length=60,
        description="SEO optimized title (10-60 characters)",
    )
    meta_description: str = Field(
        ...,
        min_length=10,
        max_length=160,
        description="SEO meta description (10-160 characters)",
    )
    focus_keyword: str = Field(
        "",
        max_length=100,
        description="Primary focus keyword for SEO",
    )
    keywords: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Additional related keywords",
    )
    canonical_url: str | None = Field(
        default=None,
        description="Canonical URL for the article",
    )
    og_title: str | None = Field(
        default=None,
        max_length=70,
        description="Open Graph title for social media",
    )
    og_description: str | None = Field(
        default=None,
        max_length=200,
        description="Open Graph description",
    )
    og_image: str | None = Field(
        default=None,
        description="Open Graph image URL",
    )
    schema_type: str = Field(
        default="Article",
        description="Schema.org type (Article, BlogPosting, etc.)",
    )
    readability_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Flesch-Kincaid readability score",
    )
    seo_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Overall SEO optimization score",
    )

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: list[str]) -> list[str]:
        """Validate keywords are not empty strings."""
        return [k.strip() for k in v if k.strip()]

    @field_validator("meta_title")
    @classmethod
    def validate_meta_title_length(cls, v: str) -> str:
        """Log warning if meta title is shorter than optimal range."""
        if len(v) < 50:
            import logging
            logging.getLogger(__name__).warning(
                "Meta title is %d chars (optimal: 50-60). Proceeding anyway.", len(v)
            )
        return v

    @field_validator("meta_description")
    @classmethod
    def validate_meta_description_length(cls, v: str) -> str:
        """Log warning if meta description is shorter than optimal range."""
        if len(v) < 120:
            import logging
            logging.getLogger(__name__).warning(
                "Meta description is %d chars (optimal: 120-160). Proceeding anyway.", len(v)
            )
        return v


class ComputerUseMetadata(BaseSchema):
    """Schema for Computer Use operation metadata."""

    session_id: str | None = Field(
        default=None,
        description="Computer Use session ID",
    )
    attempts: int = Field(
        default=0,
        ge=0,
        description="Number of attempts to publish via Computer Use",
    )
    last_attempt_at: str | None = Field(
        default=None,
        description="ISO timestamp of last attempt",
    )
    status: str = Field(
        default="pending",
        description="Status: pending, in_progress, completed, failed",
    )
    screenshots: list[str] = Field(
        default_factory=list,
        description="URLs of operation screenshots",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Error messages from failed attempts",
    )
    execution_time_seconds: float | None = Field(
        default=None,
        ge=0.0,
        description="Total execution time in seconds",
    )


class ArticleMetadataSchema(BaseSchema):
    """Complete article metadata schema including SEO and Computer Use data."""

    seo: SEOMetadata | None = Field(
        default=None,
        description="SEO optimization data",
    )
    computer_use: ComputerUseMetadata | None = Field(
        default=None,
        description="Computer Use operation metadata",
    )
    cost_usd: float | None = Field(
        default=None,
        ge=0.0,
        description="Total API cost in USD",
    )
    model: str | None = Field(
        default=None,
        description="AI model used for generation",
    )
    input_tokens: int | None = Field(
        default=None,
        ge=0,
        description="Input tokens used",
    )
    output_tokens: int | None = Field(
        default=None,
        ge=0,
        description="Output tokens generated",
    )


class SEOAnalysisRequest(BaseSchema):
    """Request schema for SEO analysis."""

    title: str = Field(..., min_length=10, max_length=500)
    body: str = Field(..., min_length=100)
    target_keyword: str | None = Field(default=None, description="Optional target keyword")


class SEOAnalysisResponse(BaseSchema):
    """Response schema for SEO analysis."""

    seo_data: SEOMetadata
    suggestions: list[str] = Field(
        default_factory=list,
        description="SEO improvement suggestions",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="SEO warnings or issues",
    )
