"""API routes for unified AI optimization (Phase 7).

This module provides endpoints for:
- Generating unified optimization suggestions (title + SEO + FAQ in one call)
- Retrieving cached optimization results
- Checking optimization status
- Deleting/regenerating optimizations

Cost savings: 40-60% vs separate API calls
Time savings: 30-40% vs separate API calls
"""

import logging
from typing import Any

from anthropic import AsyncAnthropic
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_session as get_db
from src.api.schemas.optimization import (
    GenerateOptimizationsRequest,
    OptimizationError,
    OptimizationStatusResponse,
    OptimizationsResponse,
    SelectSEOTitleRequest,
    SelectSEOTitleResponse,
)
from src.config.settings import get_settings
from src.models.article import Article
from src.models.article_faq import ArticleFAQ
from src.models.seo_suggestions import SEOSuggestion
from src.models.title_suggestions import TitleSuggestion
from src.services.parser.unified_optimization_service import UnifiedOptimizationService

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Dependency Injection
# ============================================================================


async def get_anthropic_client() -> AsyncAnthropic:
    """Get Anthropic client instance."""
    settings = get_settings()
    return AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


async def get_optimization_service(
    db: AsyncSession = Depends(get_db),
    anthropic_client: AsyncAnthropic = Depends(get_anthropic_client),
) -> UnifiedOptimizationService:
    """Get UnifiedOptimizationService instance."""
    return UnifiedOptimizationService(anthropic_client=anthropic_client, db_session=db)


# ============================================================================
# Helper Functions
# ============================================================================


async def _get_article_or_404(article_id: int, db: AsyncSession) -> Article:
    """Get article by ID or raise 404."""
    stmt = select(Article).where(Article.id == article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Article {article_id} not found"
        )

    return article


async def _build_optimizations_response(
    article_id: int, db: AsyncSession, cached: bool = True
) -> dict[str, Any]:
    """Build optimizations response from database."""
    # Load title suggestions
    stmt = select(TitleSuggestion).where(TitleSuggestion.article_id == article_id)
    result = await db.execute(stmt)
    title_suggestion = result.scalar_one_or_none()

    # Load SEO suggestions
    stmt = select(SEOSuggestion).where(SEOSuggestion.article_id == article_id)
    result = await db.execute(stmt)
    seo_suggestion = result.scalar_one_or_none()

    # Load FAQs
    stmt = select(ArticleFAQ).where(ArticleFAQ.article_id == article_id).order_by(ArticleFAQ.position)
    result = await db.execute(stmt)
    faqs = result.scalars().all()

    if not title_suggestion and not seo_suggestion and not faqs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No optimizations found for article {article_id}. Please generate them first.",
        )

    return {
        "title_suggestions": {
            "suggested_title_sets": title_suggestion.suggested_title_sets if title_suggestion else [],
            "optimization_notes": title_suggestion.optimization_notes if title_suggestion else [],
            "seo_title_suggestions": title_suggestion.suggested_seo_titles if title_suggestion else None,
        },
        "seo_suggestions": {
            "seo_keywords": {
                "focus_keyword": seo_suggestion.focus_keyword if seo_suggestion else None,
                "focus_keyword_rationale": (
                    seo_suggestion.focus_keyword_rationale if seo_suggestion else None
                ),
                "primary_keywords": seo_suggestion.primary_keywords if seo_suggestion else [],
                "secondary_keywords": seo_suggestion.secondary_keywords if seo_suggestion else [],
                "keyword_difficulty": seo_suggestion.keyword_difficulty if seo_suggestion else None,
                "search_volume_estimate": (
                    seo_suggestion.search_volume_estimate if seo_suggestion else None
                ),
            },
            "meta_description": {
                "suggested_meta_description": (
                    seo_suggestion.suggested_meta_description if seo_suggestion else None
                ),
                "meta_description_improvements": (
                    seo_suggestion.meta_description_improvements if seo_suggestion else []
                ),
                "meta_description_score": (
                    seo_suggestion.meta_description_score if seo_suggestion else None
                ),
            },
            "tags": {
                "suggested_tags": seo_suggestion.suggested_tags if seo_suggestion else [],
                "tag_strategy": seo_suggestion.tag_strategy if seo_suggestion else None,
            },
        },
        "faqs": [
            {
                "question": faq.question,
                "answer": faq.answer,
                "question_type": faq.question_type.value if faq.question_type else None,
                "search_intent": faq.search_intent.value if faq.search_intent else None,
                "keywords_covered": faq.keywords_covered or [],
                "confidence": float(faq.confidence) if faq.confidence else None,
            }
            for faq in faqs
        ],
        "generation_metadata": {
            "cached": cached,
            "message": "Loaded from cache" if cached else "Freshly generated",
        },
    }


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/articles/{article_id}/generate-all-optimizations",
    response_model=OptimizationsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate all AI optimization suggestions",
    description="""Generate title + SEO + FAQ suggestions in a single AI call.

    **Cost savings**: 40-60% compared to separate calls
    **Time savings**: 30-40% compared to separate calls

    This endpoint calls Claude API once to generate:
    - Title optimization (2-3 options with 3-part structure)
    - SEO keywords (focus/primary/secondary)
    - Meta description optimization
    - Tags recommendations (6-8)
    - FAQ generation (8-10 questions)

    Results are cached in database for instant retrieval in Step 3.
    """,
)
async def generate_all_optimizations(
    article_id: int,
    request: GenerateOptimizationsRequest,
    db: AsyncSession = Depends(get_db),
    service: UnifiedOptimizationService = Depends(get_optimization_service),
) -> OptimizationsResponse:
    """Generate unified optimization suggestions for an article.

    Args:
        article_id: ID of article to optimize
        request: Generation request with options
        db: Database session
        service: UnifiedOptimizationService instance

    Returns:
        Complete optimization results (title/SEO/FAQ)

    Raises:
        404: Article not found
        409: Optimizations already exist (use regenerate=true to override)
        400: Article not parsed or invalid state
        500: AI API error or database error
    """
    logger.info(f"POST /articles/{article_id}/generate-all-optimizations")

    # Get article
    article = await _get_article_or_404(article_id, db)

    # Check if already generated (unless regenerate=true)
    if not request.regenerate and article.unified_optimization_generated:
        logger.info(f"Article {article_id} already has optimizations, returning cached")
        # Return cached results
        cached_result = await _build_optimizations_response(article_id, db, cached=True)
        return OptimizationsResponse(**cached_result)

    # Validate article state
    if not article.body and not article.body_html:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article has no content to optimize. Please ensure article has body or body_html.",
        )

    # Generate optimizations
    try:
        result = await service.generate_all_optimizations(
            article=article, regenerate=request.regenerate
        )
        logger.info(
            f"Successfully generated optimizations for article {article_id}: "
            f"{result['generation_metadata'].get('total_cost_usd', 0):.4f} USD"
        )
        return OptimizationsResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error generating optimizations for article {article_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except RuntimeError as e:
        logger.error(f"Runtime error generating optimizations for article {article_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate optimizations: {str(e)}",
        )

    except Exception as e:
        logger.exception(f"Unexpected error generating optimizations for article {article_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating optimizations",
        )


@router.get(
    "/articles/{article_id}/optimizations",
    response_model=OptimizationsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get cached optimization suggestions",
    description="""Retrieve previously generated optimization suggestions from cache.

    No AI API call is made - results are loaded instantly from database.
    Use this endpoint in Step 3 to display SEO + FAQ suggestions.
    """,
)
async def get_optimizations(
    article_id: int,
    db: AsyncSession = Depends(get_db),
) -> OptimizationsResponse:
    """Get cached optimization suggestions for an article.

    Args:
        article_id: ID of article
        db: Database session

    Returns:
        Cached optimization results

    Raises:
        404: Article not found or no optimizations generated
    """
    logger.info(f"GET /articles/{article_id}/optimizations")

    # Verify article exists
    await _get_article_or_404(article_id, db)

    # Load cached optimizations
    try:
        cached_result = await _build_optimizations_response(article_id, db, cached=True)
        return OptimizationsResponse(**cached_result)

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Error loading optimizations for article {article_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load optimization suggestions",
        )


@router.get(
    "/articles/{article_id}/optimization-status",
    response_model=OptimizationStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check optimization generation status",
    description="Check whether optimizations have been generated for an article and get metadata.",
)
async def get_optimization_status(
    article_id: int,
    db: AsyncSession = Depends(get_db),
) -> OptimizationStatusResponse:
    """Get optimization generation status for an article.

    Args:
        article_id: ID of article
        db: Database session

    Returns:
        Optimization status metadata

    Raises:
        404: Article not found
    """
    logger.info(f"GET /articles/{article_id}/optimization-status")

    # Get article
    article = await _get_article_or_404(article_id, db)

    # Count optimizations
    stmt = select(TitleSuggestion).where(TitleSuggestion.article_id == article_id)
    result = await db.execute(stmt)
    has_title = result.scalar_one_or_none() is not None

    stmt = select(SEOSuggestion).where(SEOSuggestion.article_id == article_id)
    result = await db.execute(stmt)
    has_seo = result.scalar_one_or_none() is not None

    stmt = select(ArticleFAQ).where(ArticleFAQ.article_id == article_id)
    result = await db.execute(stmt)
    faq_count = len(result.scalars().all())

    return OptimizationStatusResponse(
        article_id=article_id,
        generated=article.unified_optimization_generated,
        generated_at=article.unified_optimization_generated_at,
        cost_usd=float(article.unified_optimization_cost) if article.unified_optimization_cost else None,
        has_title_suggestions=has_title,
        has_seo_suggestions=has_seo,
        has_faqs=faq_count > 0,
        faq_count=faq_count,
    )


@router.delete(
    "/articles/{article_id}/optimizations",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete cached optimization suggestions",
    description="""Delete all cached optimization suggestions for an article.

    This will remove:
    - Title suggestions
    - SEO suggestions
    - All FAQs

    Use this before regenerating optimizations with different parameters.
    """,
)
async def delete_optimizations(
    article_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete all optimization suggestions for an article.

    Args:
        article_id: ID of article
        db: Database session

    Raises:
        404: Article not found
    """
    logger.info(f"DELETE /articles/{article_id}/optimizations")

    # Verify article exists
    article = await _get_article_or_404(article_id, db)

    # Delete optimizations (cascade will handle related records)
    from sqlalchemy import delete

    # Title suggestions
    stmt = delete(TitleSuggestion).where(TitleSuggestion.article_id == article_id)
    await db.execute(stmt)

    # SEO suggestions
    stmt = delete(SEOSuggestion).where(SEOSuggestion.article_id == article_id)
    await db.execute(stmt)

    # FAQs
    stmt = delete(ArticleFAQ).where(ArticleFAQ.article_id == article_id)
    await db.execute(stmt)

    # Update article metadata
    article.unified_optimization_generated = False
    article.unified_optimization_generated_at = None
    article.unified_optimization_cost = None

    await db.commit()

    logger.info(f"Successfully deleted optimizations for article {article_id}")


# ============================================================================
# SEO Title Selection (Phase 9)
# ============================================================================


@router.post(
    "/articles/{article_id}/select-seo-title",
    response_model=SelectSEOTitleResponse,
    status_code=status.HTTP_200_OK,
    summary="Select and apply SEO Title for article",
    description="""Select an SEO Title from AI-generated variants or provide a custom one.

    This endpoint allows the user to:
    1. Select one of the AI-generated SEO Title variants (by variant_id)
    2. Provide a custom SEO Title (by custom_seo_title)

    The selected SEO Title will be applied to the article's seo_title field.
    """,
)
async def select_seo_title(
    article_id: int,
    request: SelectSEOTitleRequest,
    db: AsyncSession = Depends(get_db),
) -> SelectSEOTitleResponse:
    """Select and apply an SEO Title for an article.

    Args:
        article_id: ID of article
        request: Selection request with variant_id or custom_seo_title
        db: Database session

    Returns:
        Response with applied SEO Title

    Raises:
        404: Article not found or title_suggestions not found
        400: Invalid request (both variant_id and custom_seo_title provided, or neither)
        422: Selected variant_id not found in suggestions
    """
    from datetime import datetime

    logger.info(f"POST /articles/{article_id}/select-seo-title")

    # Validate request
    if request.variant_id and request.custom_seo_title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot provide both variant_id and custom_seo_title. Please choose one.",
        )

    if not request.variant_id and not request.custom_seo_title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either variant_id or custom_seo_title.",
        )

    # Get article
    article = await _get_article_or_404(article_id, db)

    # Store previous SEO Title
    previous_seo_title = article.seo_title

    # Determine SEO Title and source
    if request.variant_id:
        # User selected an AI-generated variant
        # Load title suggestions to find the variant
        stmt = select(TitleSuggestion).where(TitleSuggestion.article_id == article_id)
        result = await db.execute(stmt)
        title_suggestion = result.scalar_one_or_none()

        if not title_suggestion or not title_suggestion.suggested_seo_titles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No SEO Title suggestions found for article {article_id}. "
                "Please generate optimizations first.",
            )

        # Find the selected variant
        suggested_seo_titles = title_suggestion.suggested_seo_titles
        variants = suggested_seo_titles.get("variants", [])
        selected_variant = next((v for v in variants if v.get("id") == request.variant_id), None)

        if not selected_variant:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Variant ID '{request.variant_id}' not found in SEO Title suggestions.",
            )

        seo_title = selected_variant.get("seo_title")
        seo_title_source = "ai_generated"

    else:
        # User provided custom SEO Title
        seo_title = request.custom_seo_title
        seo_title_source = "user_input"

    # Update article
    article.seo_title = seo_title
    article.seo_title_source = seo_title_source
    article.updated_at = datetime.utcnow()

    await db.commit()

    logger.info(
        f"Successfully applied SEO Title for article {article_id}: "
        f"'{seo_title}' (source: {seo_title_source})"
    )

    return SelectSEOTitleResponse(
        article_id=article_id,
        seo_title=seo_title,
        seo_title_source=seo_title_source,
        previous_seo_title=previous_seo_title,
        updated_at=article.updated_at,
    )
