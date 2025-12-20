"""Pydantic models for article parsing service (Phase 7).

Phase 12: Added RelatedArticle model for internal link recommendations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RelatedArticle(BaseModel):
    """Related article recommendation for internal linking (Phase 12).

    Represents an article from the health article database that is semantically
    related to the current article being processed.
    """

    article_id: str = Field(
        ...,
        description="Unique article identifier (e.g., n12345678)",
    )
    title: str = Field(
        ...,
        description="Full article title",
    )
    title_main: str | None = Field(
        None,
        description="Main title component (without prefix/suffix)",
    )
    url: str = Field(
        ...,
        description="Original article URL",
    )
    excerpt: str | None = Field(
        None,
        description="Article excerpt/summary",
    )
    similarity: float = Field(
        ...,
        ge=0,
        le=1,
        description="Similarity score (0-1)",
    )
    match_type: str = Field(
        ...,
        description="Match type: semantic, content, or keyword",
    )
    ai_keywords: list[str] = Field(
        default_factory=list,
        description="AI-extracted keywords from the related article",
    )

    class Config:
        """Pydantic configuration."""

        extra = "allow"  # Allow additional fields for extensibility


class ImageMetadata(BaseModel):
    """Technical metadata for an image."""

    width: int | None = Field(None, description="Image width in pixels")
    height: int | None = Field(None, description="Image height in pixels")
    aspect_ratio: str | None = Field(None, description="Aspect ratio (e.g., '16:9')")
    file_size_bytes: int | None = Field(None, description="File size in bytes")
    mime_type: str | None = Field(None, description="MIME type")
    format: str | None = Field(None, description="Image format (JPEG, PNG, etc.)")
    color_mode: str | None = Field(None, description="Color mode (RGB, RGBA, etc.)")
    has_transparency: bool | None = Field(None, description="Whether image has alpha channel")

    class Config:
        """Pydantic configuration."""

        extra = "allow"  # Allow additional fields for extensibility


class ParsedImage(BaseModel):
    """Parsed image data from article."""

    position: int = Field(..., ge=0, description="Paragraph index (0-based) where image appears")
    preview_path: str | None = Field(None, description="Path to preview/thumbnail")
    source_path: str | None = Field(None, description="Path to downloaded source")
    source_url: str | None = Field(None, description='Original "原圖" URL from doc')
    caption: str | None = Field(None, description="Image caption")
    alt_text: str | None = Field(None, description="Alt text for accessibility (defaults to caption)")
    description: str | None = Field(None, description="Image description for WordPress media library")
    metadata: ImageMetadata | None = Field(default=None, description="Technical image specs")

    # Phase 13: Featured image detection fields
    is_featured: bool = Field(
        default=False,
        description="Whether this is the featured/cover image (置頂圖片)"
    )
    image_type: str = Field(
        default="content",
        description="Image type: featured (置頂) / content (正文) / inline (行內)"
    )
    detection_method: str | None = Field(
        default=None,
        description="How featured status was detected: caption_keyword / position_before_body / manual / none"
    )

    # Compatibility attributes for proofreading engine
    @property
    def id(self) -> str | None:
        """ID property for compatibility with proofreading engine."""
        return self.source_url

    @property
    def path(self) -> str | None:
        """Path property for compatibility with proofreading engine."""
        return self.source_path or self.preview_path

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: int) -> int:
        """Validate position is non-negative."""
        if v < 0:
            raise ValueError("Position must be non-negative")
        return v


class ParsedArticle(BaseModel):
    """Complete parsed article data structure."""

    # Title decomposition
    title_prefix: str | None = Field(
        None,
        max_length=200,
        description='First part of title (optional), e.g., "【專題報導】"',
    )
    title_main: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description='Main title (required), e.g., "2024年醫療保健創新趨勢"',
    )
    title_suffix: str | None = Field(
        None,
        max_length=200,
        description='Subtitle/suffix (optional), e.g., "從AI診斷到遠距醫療"',
    )

    # Author information
    author_line: str | None = Field(
        None,
        max_length=300,
        description='Raw author line, e.g., "文／張三｜編輯／李四"',
    )
    author_name: str | None = Field(
        None,
        max_length=100,
        description='Cleaned author name, e.g., "張三"',
    )

    # Body content
    body_html: str = Field(
        ...,
        description="Sanitized body HTML (headers/images/meta removed)",
    )

    # SEO and metadata
    meta_description: str | None = Field(
        None,
        description="Extracted meta description for SEO (150-160 chars)",
    )
    seo_keywords: list[str] = Field(
        default_factory=list,
        description="Array of SEO keywords",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Content tags/categories",
    )

    # Phase 10: WordPress taxonomy
    primary_category: str | None = Field(
        None,
        max_length=100,
        description="WordPress primary category (主分類，決定URL結構和麵包屑導航)",
    )
    # Phase 11: Secondary categories for cross-listing
    secondary_categories: list[str] = Field(
        default_factory=list,
        description="WordPress secondary categories (副分類，可多選，用於交叉列表)",
    )
    focus_keyword: str | None = Field(
        None,
        max_length=100,
        description="Yoast SEO focus keyword (from seo_keywords or AI recommended)",
    )

    # Phase 9: SEO Title (separate from H1 title)
    seo_title: str | None = Field(
        None,
        max_length=200,
        description='SEO Title Tag (30字左右，用於<title>標籤)',
    )
    seo_title_extracted: bool = Field(
        default=False,
        description='是否從原文中提取了標記的 SEO Title',
    )
    seo_title_source: str | None = Field(
        None,
        description='SEO Title 來源：extracted/ai_generated/migrated',
    )

    # Images
    images: list[ParsedImage] = Field(
        default_factory=list,
        description="Extracted images with positions",
    )

    # Phase 7.5: Unified AI Parsing - SEO Suggestions
    suggested_titles: list[dict[str, Any]] | None = Field(
        None,
        description="AI-generated title suggestions (2-3 variations)",
    )
    suggested_meta_description: str | None = Field(
        None,
        description="AI-generated meta description suggestion",
    )
    suggested_seo_keywords: list[str] | None = Field(
        None,
        description="AI-generated SEO keyword suggestions",
    )

    # Phase 7.5: Unified AI Parsing - Proofreading
    proofreading_issues: list[dict[str, Any]] | None = Field(
        None,
        description="AI-detected proofreading issues",
    )
    proofreading_stats: dict[str, Any] | None = Field(
        None,
        description="Proofreading statistics (total_issues, by severity, etc.)",
    )

    # Phase 7.5: Unified AI Parsing - FAQ Generation
    faqs: list[dict[str, Any]] | None = Field(
        None,
        description="AI-generated FAQ list (6-8 questions)",
    )

    # Phase 12: Internal Link Recommendations
    related_articles: list[RelatedArticle] = Field(
        default_factory=list,
        description="AI-recommended related articles for internal linking",
    )

    # Parsing metadata
    parsing_method: str = Field(
        ...,
        description='Parsing method used: "ai" or "heuristic"',
    )
    parsing_confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1) of parsing quality",
    )
    parsing_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When parsing occurred",
    )

    @field_validator("title_main")
    @classmethod
    def validate_title_main(cls, v: str) -> str:
        """Validate title_main is not empty."""
        if not v or not v.strip():
            raise ValueError("title_main cannot be empty")
        return v.strip()

    @field_validator("seo_keywords", "tags")
    @classmethod
    def validate_keyword_lists(cls, v: list[str]) -> list[str]:
        """Validate keyword lists don't contain empty strings."""
        return [kw.strip() for kw in v if kw and kw.strip()]

    @property
    def full_title(self) -> str:
        """Construct full title from components."""
        parts = []
        if self.title_prefix:
            parts.append(self.title_prefix.strip())
        parts.append(self.title_main.strip())
        if self.title_suffix:
            parts.append(self.title_suffix.strip())
        return " ".join(parts)

    @property
    def image_count(self) -> int:
        """Get total number of images."""
        return len(self.images)

    @property
    def has_seo_data(self) -> bool:
        """Check if article has SEO metadata."""
        return bool(self.meta_description or self.seo_keywords)


class ParsingError(BaseModel):
    """Error information from parsing attempt."""

    error_type: str = Field(..., description="Error type/category")
    error_message: str = Field(..., description="Error message")
    field_name: str | None = Field(None, description="Field that caused error (if applicable)")
    suggestion: str | None = Field(None, description="Suggestion for fixing the error")


class ParsingResult(BaseModel):
    """Result wrapper for parsing operation."""

    success: bool = Field(..., description="Whether parsing succeeded")
    parsed_article: ParsedArticle | None = Field(None, description="Parsed article data")
    errors: list[ParsingError] = Field(default_factory=list, description="Errors encountered")
    warnings: list[str] = Field(default_factory=list, description="Non-critical warnings")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (timing, retries, etc.)",
    )

    @property
    def has_errors(self) -> bool:
        """Check if parsing had errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if parsing had warnings."""
        return len(self.warnings) > 0
