"""Optimization API schemas for unified AI optimization service."""

from datetime import datetime

from pydantic import Field

from src.api.schemas.base import BaseSchema


# ============================================================================
# Request Schemas
# ============================================================================


class OptimizationOptions(BaseSchema):
    """Options for optimization generation."""

    include_title: bool = Field(True, description="Generate title optimization suggestions")
    include_seo: bool = Field(True, description="Generate SEO keywords suggestions")
    include_tags: bool = Field(True, description="Generate tags recommendations")
    include_faqs: bool = Field(True, description="Generate FAQ questions and answers")
    faq_target_count: int = Field(
        10, ge=3, le=15, description="Target number of FAQs to generate (3-15)"
    )


class GenerateOptimizationsRequest(BaseSchema):
    """Request to generate unified optimizations."""

    regenerate: bool = Field(
        False, description="Force regeneration even if optimizations already exist"
    )
    options: OptimizationOptions = Field(
        default_factory=OptimizationOptions, description="Optimization generation options"
    )


# ============================================================================
# Title Suggestions Schemas
# ============================================================================


class TitleCharacterCount(BaseSchema):
    """Character count for title components."""

    prefix: int = Field(..., description="Prefix character count")
    main: int = Field(..., description="Main title character count")
    suffix: int = Field(..., description="Suffix character count")
    total: int = Field(..., description="Total title character count")


class TitleOptionData(BaseSchema):
    """Single title optimization option."""

    id: str = Field(..., description="Option identifier (e.g., 'option_1')")
    title_prefix: str | None = Field(None, description="Optimized title prefix (2-6 chars)")
    title_main: str = Field(..., description="Optimized main title (15-30 chars)")
    title_suffix: str | None = Field(None, description="Optimized title suffix (4-12 chars)")
    full_title: str = Field(..., description="Complete title with separators")
    score: int = Field(..., ge=0, le=100, description="Quality score (0-100)")
    strengths: list[str] = Field(
        default_factory=list, description="Key strengths of this title option"
    )
    type: str = Field(
        ...,
        description="Title type: data_driven, authority_backed, how_to, comprehensive_guide, question_based",
    )
    recommendation: str = Field(..., description="Why this option is recommended")
    character_count: TitleCharacterCount


class SEOTitleVariant(BaseSchema):
    """Single SEO Title suggestion variant."""

    id: str = Field(..., description="Variant identifier (e.g., 'seo_variant_1')")
    seo_title: str = Field(..., max_length=200, description="SEO Title suggestion (~30 chars)")
    reasoning: str = Field(..., description="Why this SEO Title was suggested")
    keywords_focus: list[str] = Field(
        default_factory=list, description="Keywords emphasized in this variant"
    )
    character_count: int = Field(..., description="Character count of SEO Title")


class SEOTitleSuggestionsData(BaseSchema):
    """SEO Title suggestions (for <title> tag, separate from H1)."""

    variants: list[SEOTitleVariant] = Field(
        default_factory=list, description="2-3 SEO Title variants"
    )
    original_seo_title: str | None = Field(
        None, description="Original SEO Title if extracted from document"
    )
    notes: list[str] = Field(default_factory=list, description="Notes about SEO Title optimization")


class TitleSuggestionsData(BaseSchema):
    """Title optimization suggestions response (H1 + SEO Title)."""

    suggested_title_sets: list[TitleOptionData] = Field(
        ..., description="2-3 H1 title optimization options"
    )
    optimization_notes: list[str] = Field(
        default_factory=list, description="General H1 title optimization notes"
    )
    seo_title_suggestions: SEOTitleSuggestionsData | None = Field(
        None, description="SEO Title suggestions (for <title> tag)"
    )


# ============================================================================
# SEO Suggestions Schemas
# ============================================================================


class SEOKeywordsData(BaseSchema):
    """SEO keywords optimization data."""

    focus_keyword: str | None = Field(None, description="Primary SEO keyword (1)")
    focus_keyword_rationale: str | None = Field(
        None, description="Explanation for focus keyword choice"
    )
    primary_keywords: list[str] = Field(default_factory=list, description="Primary keywords (3-5)")
    secondary_keywords: list[str] = Field(
        default_factory=list, description="Secondary keywords (5-10)"
    )
    keyword_difficulty: dict | None = Field(None, description="Keyword difficulty scores")
    search_volume_estimate: dict | None = Field(None, description="Estimated search volumes")


class MetaDescriptionData(BaseSchema):
    """Meta description optimization data."""

    original_meta_description: str | None = Field(None, description="Original meta description")
    suggested_meta_description: str | None = Field(
        None, description="AI-optimized meta description (150-160 chars)"
    )
    meta_description_improvements: list[str] = Field(
        default_factory=list, description="List of improvements made"
    )
    meta_description_score: int | None = Field(
        None, ge=0, le=100, description="Quality score (0-100)"
    )


class TagSuggestion(BaseSchema):
    """Single tag suggestion."""

    tag: str = Field(..., description="Tag name")
    relevance: float = Field(..., ge=0, le=1, description="Relevance score (0-1)")
    type: str = Field(..., description="Tag type: primary, secondary, trending")


class TagsData(BaseSchema):
    """Tags recommendations data."""

    suggested_tags: list[TagSuggestion] = Field(default_factory=list, description="6-8 tag suggestions")
    recommended_tag_count: str | None = Field(None, description="Recommendation for tag count")
    tag_strategy: str | None = Field(None, description="Tag selection strategy explanation")


class SEOSuggestionsData(BaseSchema):
    """Complete SEO suggestions data."""

    seo_keywords: SEOKeywordsData
    meta_description: MetaDescriptionData
    tags: TagsData


# ============================================================================
# FAQ Schemas
# ============================================================================


class FAQData(BaseSchema):
    """Single FAQ question and answer."""

    question: str = Field(..., description="FAQ question")
    answer: str = Field(..., description="FAQ answer (50-150 chars recommended)")
    question_type: str | None = Field(
        None, description="Question type: factual, how_to, comparison, definition"
    )
    search_intent: str | None = Field(
        None, description="Search intent: informational, navigational, transactional"
    )
    keywords_covered: list[str] = Field(
        default_factory=list, description="Keywords naturally covered in this FAQ"
    )
    confidence: float | None = Field(None, ge=0, le=1, description="AI confidence score (0-1)")


# ============================================================================
# Generation Metadata Schemas
# ============================================================================


class SavingsData(BaseSchema):
    """Savings compared to separate API calls."""

    original_tokens: int = Field(..., description="Tokens if using separate calls")
    original_cost_usd: float = Field(..., description="Cost if using separate calls")
    original_duration_ms: int = Field(..., description="Duration if using separate calls")
    saved_tokens: int = Field(..., description="Tokens saved")
    saved_cost_usd: float = Field(..., description="Cost saved (USD)")
    saved_duration_ms: int = Field(..., description="Time saved (ms)")
    cost_savings_percentage: float = Field(..., description="Cost savings percentage")
    time_savings_percentage: float = Field(..., description="Time savings percentage")


class GenerationMetadata(BaseSchema):
    """Metadata about the optimization generation."""

    total_cost_usd: float | None = Field(None, description="Total API cost (USD)")
    total_tokens: int | None = Field(None, description="Total tokens used")
    input_tokens: int | None = Field(None, description="Input tokens")
    output_tokens: int | None = Field(None, description="Output tokens")
    duration_ms: int | None = Field(None, description="Generation duration (ms)")
    savings_vs_separate: SavingsData | None = Field(
        None, description="Savings compared to separate API calls"
    )
    cached: bool = Field(False, description="Whether results were loaded from cache")
    message: str | None = Field(None, description="Additional message")


# ============================================================================
# Response Schemas
# ============================================================================


class OptimizationsResponse(BaseSchema):
    """Complete optimizations response."""

    title_suggestions: TitleSuggestionsData
    seo_suggestions: SEOSuggestionsData
    faqs: list[FAQData]
    generation_metadata: GenerationMetadata


class OptimizationStatusResponse(BaseSchema):
    """Status of optimization generation for an article."""

    article_id: int
    generated: bool = Field(..., description="Whether optimizations have been generated")
    generated_at: datetime | None = Field(None, description="When optimizations were generated")
    cost_usd: float | None = Field(None, description="Cost of generation (USD)")
    has_title_suggestions: bool = False
    has_seo_suggestions: bool = False
    has_faqs: bool = False
    faq_count: int = 0


# ============================================================================
# Error Response Schemas
# ============================================================================


class OptimizationError(BaseSchema):
    """Error response for optimization operations."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict | None = Field(None, description="Additional error details")


# ============================================================================
# SEO Title Selection Schemas (Phase 9)
# ============================================================================


class SelectSEOTitleRequest(BaseSchema):
    """Request to select and apply an SEO Title for an article."""

    variant_id: str | None = Field(
        None,
        description="ID of the selected SEO Title variant (e.g., 'seo_variant_1'). Null for custom.",
    )
    custom_seo_title: str | None = Field(
        None,
        max_length=200,
        description="Custom SEO Title provided by user (if variant_id is None)",
    )


class SelectSEOTitleResponse(BaseSchema):
    """Response after selecting and applying SEO Title."""

    article_id: int = Field(..., description="Article ID")
    seo_title: str = Field(..., description="SEO Title that was applied")
    seo_title_source: str = Field(
        ...,
        description="Source of SEO Title: extracted/ai_generated/user_input",
    )
    previous_seo_title: str | None = Field(None, description="Previous SEO Title (if any)")
    updated_at: datetime = Field(..., description="When the update occurred")
