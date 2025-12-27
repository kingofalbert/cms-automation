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
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_session as get_db
from sqlalchemy import delete

from src.api.schemas.optimization import (
    ApplyCategoryRequest,
    CategoryRecommendationRequest,
    CategoryRecommendationResponse,
    FAQItem,
    GenerateOptimizationsRequest,
    OptimizationError,
    OptimizationStatusResponse,
    OptimizationsResponse,
    SelectSEOTitleRequest,
    SelectSEOTitleResponse,
    UpdateFAQsRequest,
    UpdateFAQsResponse,
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

    # Load FAQs - ONLY return DRAFT FAQs as AI suggestions
    # APPROVED FAQs are user-selected and stored separately in article metadata
    stmt = select(ArticleFAQ).where(
        ArticleFAQ.article_id == article_id,
        ArticleFAQ.status == "draft"
    ).order_by(ArticleFAQ.position)
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
                "question_type": faq.question_type,  # Already a string
                "search_intent": faq.search_intent,  # Already a string
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
        # Validate response structure before returning
        try:
            return OptimizationsResponse(**result)
        except Exception as validation_error:
            logger.error(
                f"Response validation failed for article {article_id}: {validation_error}. "
                f"Result keys: {result.keys()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Response validation failed: {str(validation_error)}",
            )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is

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
        # Include actual error message for debugging
        error_message = f"{type(e).__name__}: {str(e)}"
        logger.exception(f"Unexpected error generating optimizations for article {article_id}: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization generation failed: {error_message}",
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


# ============================================================================
# Category Recommendation (Phase 11)
# ============================================================================

# WordPress category mapping (Chinese name -> slug)
WORDPRESS_CATEGORIES = {
    "食療養生": "food-therapy",
    "中醫寶典": "tcm",
    "心靈正念": "mindfulness",
    "醫師專欄": "doctor-column",
    "健康新聞": "health-news",
    "健康生活": "healthy-living",
    "醫療科技": "medical-tech",
    "精選內容": "featured",
    "診室外的醫話": "doctor-stories",
    "每日呵護": "daily-care",
}

# Category descriptions for AI context
CATEGORY_DESCRIPTIONS = {
    "食療養生": "食物療法、營養補充、養生食譜、飲食調理",
    "中醫寶典": "傳統中醫知識、穴位按摩、中藥材介紹、經絡理論",
    "心靈正念": "心理健康、冥想打坐、情緒管理、壓力調適",
    "醫師專欄": "醫生撰寫的專業文章、臨床經驗分享、醫療見解",
    "健康新聞": "最新醫療研究、健康趨勢、疾病報導、公共衛生新聞",
    "健康生活": "日常保健、運動健身、睡眠品質、生活習慣改善",
    "醫療科技": "醫療創新、新藥研發、醫療設備、數位醫療",
    "精選內容": "編輯推薦的優質文章、熱門話題、深度報導",
    "診室外的醫話": "醫生的人文關懷、醫患故事、行醫感悟",
    "每日呵護": "日常小貼士、簡單養生方法、即時可用的健康建議",
}


@router.post(
    "/articles/{article_id}/recommend-category",
    response_model=CategoryRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI category recommendation",
    description="""Analyze article content and recommend the best WordPress category.

    Returns:
    - Recommended primary category (Chinese name)
    - AI confidence score (0-1)
    - Reasoning for the recommendation
    - Alternative categories with their scores
    """,
)
async def recommend_category(
    article_id: int,
    request: CategoryRecommendationRequest = CategoryRecommendationRequest(),
    db: AsyncSession = Depends(get_db),
    anthropic_client: AsyncAnthropic = Depends(get_anthropic_client),
) -> CategoryRecommendationResponse:
    """Get AI-powered category recommendation for an article.

    Args:
        article_id: ID of article to analyze
        request: Request options (force_regenerate)
        db: Database session
        anthropic_client: Anthropic API client

    Returns:
        Category recommendation with confidence and reasoning

    Raises:
        404: Article not found
        400: Article has no content to analyze
        500: AI API error
    """
    import json
    from datetime import datetime

    logger.info(f"POST /articles/{article_id}/recommend-category")

    # Get article
    article = await _get_article_or_404(article_id, db)

    # Check if we have cached recommendation (stored in article_metadata)
    cached_recommendation = article.article_metadata.get("category_recommendation")
    if cached_recommendation and not request.force_regenerate:
        logger.info(f"Returning cached category recommendation for article {article_id}")
        return CategoryRecommendationResponse(
            article_id=article_id,
            primary_category=cached_recommendation["primary_category"],
            confidence=cached_recommendation["confidence"],
            reasoning=cached_recommendation["reasoning"],
            alternative_categories=cached_recommendation.get("alternative_categories"),
            content_analysis=cached_recommendation.get("content_analysis"),
            cached=True,
        )

    # Validate article has content
    content = article.body_html or article.body
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article has no content to analyze. Please ensure article has body content.",
        )

    # Prepare content for analysis (truncate if too long)
    title = article.title_main or article.title
    content_preview = content[:3000] if len(content) > 3000 else content
    keywords = article.seo_keywords or []
    tags = article.tags or []

    # Build category options string
    category_options = "\n".join(
        [f"- {name}: {desc}" for name, desc in CATEGORY_DESCRIPTIONS.items()]
    )

    # Call Claude API for category recommendation
    prompt = f"""你是一位專業的健康醫療內容編輯，需要為以下文章選擇最適合的 WordPress 主分類。

## 文章信息
**標題**: {title}
**關鍵詞**: {', '.join(keywords) if keywords else '無'}
**標籤**: {', '.join(tags) if tags else '無'}

**內容摘要**:
{content_preview}

## 可選分類
{category_options}

## 任務
請分析文章內容，選擇最匹配的主分類。

## 輸出格式（JSON）
```json
{{
  "primary_category": "分類名稱（中文）",
  "confidence": 0.95,
  "reasoning": "選擇這個分類的原因（50-100字）",
  "content_analysis": "文章內容簡析（30-50字）",
  "alternative_categories": [
    {{"category": "備選分類1", "confidence": 0.7, "reason": "原因"}},
    {{"category": "備選分類2", "confidence": 0.5, "reason": "原因"}}
  ]
}}
```

請直接返回 JSON，不要包含其他文字。"""

    try:
        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        response_text = response.content[0].text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)

        # Validate primary_category is in our list
        primary_cat = result.get("primary_category", "")
        if primary_cat not in WORDPRESS_CATEGORIES:
            # Try to find closest match
            logger.warning(f"AI returned invalid category '{primary_cat}', defaulting to '健康新聞'")
            primary_cat = "健康新聞"
            result["primary_category"] = primary_cat
            result["confidence"] = max(0.5, result.get("confidence", 0.5) - 0.2)

        # Cache the recommendation in article metadata
        category_recommendation = {
            "primary_category": result["primary_category"],
            "confidence": result.get("confidence", 0.8),
            "reasoning": result.get("reasoning", "AI 分析推薦"),
            "content_analysis": result.get("content_analysis"),
            "alternative_categories": result.get("alternative_categories"),
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Update article metadata with recommendation
        updated_metadata = dict(article.article_metadata)
        updated_metadata["category_recommendation"] = category_recommendation
        article.article_metadata = updated_metadata
        article.updated_at = datetime.utcnow()
        await db.commit()

        logger.info(
            f"Generated category recommendation for article {article_id}: "
            f"{result['primary_category']} (confidence: {result.get('confidence', 0.8):.2f})"
        )

        return CategoryRecommendationResponse(
            article_id=article_id,
            primary_category=result["primary_category"],
            confidence=result.get("confidence", 0.8),
            reasoning=result.get("reasoning", "AI 分析推薦"),
            alternative_categories=result.get("alternative_categories"),
            content_analysis=result.get("content_analysis"),
            cached=False,
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response for article {article_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse AI category recommendation: {str(e)}",
        )

    except Exception as e:
        logger.exception(f"Error generating category recommendation for article {article_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate category recommendation: {str(e)}",
        )


@router.post(
    "/articles/{article_id}/apply-category",
    status_code=status.HTTP_200_OK,
    summary="Apply category selection to article",
    description="Apply primary and secondary categories to an article.",
)
async def apply_category(
    article_id: int,
    request: ApplyCategoryRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Apply category selection to an article.

    Args:
        article_id: ID of article
        request: Category selection request
        db: Database session

    Returns:
        Success response with applied categories

    Raises:
        404: Article not found
        400: Invalid category
    """
    from datetime import datetime

    logger.info(f"POST /articles/{article_id}/apply-category")

    # Get article
    article = await _get_article_or_404(article_id, db)

    # Validate primary category
    if request.primary_category not in WORDPRESS_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid primary category: {request.primary_category}. "
            f"Valid categories: {', '.join(WORDPRESS_CATEGORIES.keys())}",
        )

    # Validate secondary categories
    if request.secondary_categories:
        if len(request.secondary_categories) > 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 3 secondary categories allowed.",
            )
        for cat in request.secondary_categories:
            if cat not in WORDPRESS_CATEGORIES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid secondary category: {cat}",
                )
            if cat == request.primary_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Secondary category cannot be the same as primary category.",
                )

    # Apply categories
    previous_primary = article.primary_category
    previous_secondary = article.secondary_categories

    article.primary_category = request.primary_category
    article.secondary_categories = request.secondary_categories or []
    article.updated_at = datetime.utcnow()

    await db.commit()

    logger.info(
        f"Applied categories for article {article_id}: "
        f"primary={request.primary_category}, secondary={request.secondary_categories}"
    )

    return {
        "article_id": article_id,
        "primary_category": article.primary_category,
        "secondary_categories": article.secondary_categories,
        "previous_primary_category": previous_primary,
        "previous_secondary_categories": previous_secondary,
        "source": request.source,
        "updated_at": article.updated_at.isoformat(),
    }


# ============================================================================
# FAQ Update (Phase 13 v2.3)
# ============================================================================


def _generate_faq_html_from_items(faqs: list[FAQItem], disclaimer_required: bool = True) -> str:
    """Generate FAQ HTML section with Schema.org Microdata from FAQ items.

    Creates a visible FAQ section with embedded Schema.org FAQPage markup,
    which satisfies Google's requirement that structured data must match
    visible content on the page.

    Args:
        faqs: List of FAQ items to render
        disclaimer_required: Whether to add medical disclaimer

    Returns:
        HTML string for FAQ section with Schema.org Microdata
    """
    if not faqs:
        return ""

    # Helper function to escape HTML
    def escape_html(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    html_parts = [
        # FAQPage schema wrapper - Google requires visible content to match structured data
        '<section class="faq-section" id="faq" itemscope itemtype="https://schema.org/FAQPage">',
        '  <h2 class="faq-title">常見問題</h2>',
        '  <div class="faq-list">',
    ]

    for i, faq in enumerate(faqs, 1):
        question = escape_html(faq.question)
        answer = escape_html(faq.answer)
        has_warning = faq.safety_warning

        # Each Q&A pair with Schema.org Question/Answer markup
        html_parts.append(f'    <div class="faq-item" id="faq-{i}" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">')
        html_parts.append(f'      <h3 class="faq-question" itemprop="name">{question}</h3>')

        if has_warning:
            html_parts.append('      <div class="faq-answer faq-warning" itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">')
            html_parts.append('        <span class="warning-icon">⚠️</span>')
            html_parts.append(f'        <p itemprop="text">{answer}</p>')
            html_parts.append('      </div>')
        else:
            html_parts.append('      <div class="faq-answer" itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">')
            html_parts.append(f'        <p itemprop="text">{answer}</p>')
            html_parts.append('      </div>')

        html_parts.append('    </div>')

    html_parts.append('  </div>')

    # Add disclaimer for health articles (outside schema markup)
    if disclaimer_required:
        html_parts.append('  <div class="faq-disclaimer">')
        html_parts.append('    <p>以上資訊僅供參考，不構成醫療建議。如有健康問題，請諮詢專業醫師。</p>')
        html_parts.append('  </div>')

    html_parts.append('</section>')

    return '\n'.join(html_parts)


@router.put(
    "/articles/{article_id}/faqs",
    response_model=UpdateFAQsResponse,
    status_code=status.HTTP_200_OK,
    summary="Update selected FAQs for an article",
    description="""Update the FAQs for an article based on user selection.

    This endpoint allows users to:
    1. Select which AI-generated FAQs to keep
    2. Edit FAQ content before saving
    3. Remove unwanted FAQs (pass empty list)

    The faq_html will be regenerated based on the selected FAQs.
    This ensures that only user-approved FAQs appear in the published article.
    """,
)
async def update_article_faqs(
    article_id: int,
    request: UpdateFAQsRequest,
    db: AsyncSession = Depends(get_db),
) -> UpdateFAQsResponse:
    """Update FAQs for an article based on user selection.

    Args:
        article_id: ID of article
        request: Update request with selected FAQs
        db: Database session

    Returns:
        Response with updated FAQ count and regenerated HTML

    Raises:
        404: Article not found
    """
    from datetime import datetime

    logger.info(f"PUT /articles/{article_id}/faqs - Updating {len(request.faqs)} FAQs")

    # Get article
    article = await _get_article_or_404(article_id, db)

    # Count existing FAQs
    stmt = select(ArticleFAQ).where(ArticleFAQ.article_id == article_id)
    result = await db.execute(stmt)
    existing_faqs = result.scalars().all()
    previous_faq_count = len(existing_faqs)

    # BUGFIX: Only delete APPROVED FAQs, keep DRAFT (original AI suggestions) intact
    # This ensures AI suggestions are preserved when user saves their selection
    stmt = delete(ArticleFAQ).where(
        ArticleFAQ.article_id == article_id,
        ArticleFAQ.status == "approved"
    )
    await db.execute(stmt)

    # Insert new FAQs as approved
    new_faq_html = None
    if request.faqs:
        for i, faq_item in enumerate(request.faqs, 1):
            new_faq = ArticleFAQ(
                article_id=article_id,
                question=faq_item.question,
                answer=faq_item.answer,
                question_type=faq_item.question_type,
                search_intent=faq_item.search_intent,
                keywords_covered=faq_item.keywords_covered or [],
                position=i,
                status="approved",  # User-selected FAQs are automatically approved
                safety_warning=faq_item.safety_warning,
            )
            db.add(new_faq)

        # Regenerate faq_html if requested
        if request.regenerate_html:
            # Check if any FAQ has safety warning to determine if disclaimer needed
            has_safety_warnings = any(f.safety_warning for f in request.faqs)
            new_faq_html = _generate_faq_html_from_items(
                request.faqs,
                disclaimer_required=has_safety_warnings or article.faq_editorial_notes.get("disclaimer_required", False) if article.faq_editorial_notes else has_safety_warnings
            )
            article.faq_html = new_faq_html
    else:
        # No FAQs selected - clear faq_html
        article.faq_html = None
        article.faq_applicable = False

    article.updated_at = datetime.utcnow()
    await db.commit()

    logger.info(
        f"Updated FAQs for article {article_id}: "
        f"{previous_faq_count} -> {len(request.faqs)} FAQs"
    )

    return UpdateFAQsResponse(
        article_id=article_id,
        faq_count=len(request.faqs),
        faq_html=new_faq_html,
        previous_faq_count=previous_faq_count,
        updated_at=article.updated_at.isoformat(),
    )


# ============================================================================
# FAQ Render Preview (for preview before saving)
# ============================================================================


class RenderFAQsRequest(BaseModel):
    """Request model for FAQ HTML preview rendering."""

    faqs: list[FAQItem] = Field(
        ...,
        description="List of FAQs to render",
    )
    include_disclaimer: bool = Field(
        default=True,
        description="Whether to include medical disclaimer",
    )
    section_title: str = Field(
        default="常見問題",
        description="Title for the FAQ section",
    )


class RenderFAQsResponse(BaseModel):
    """Response model for FAQ HTML preview rendering."""

    faq_html: str = Field(
        ...,
        description="Generated FAQ HTML with Schema.org Microdata",
    )
    faq_count: int = Field(
        ...,
        description="Number of FAQs rendered",
    )
    schema_type: str = Field(
        default="FAQPage",
        description="Schema.org type used",
    )


@router.post(
    "/articles/faqs/render",
    response_model=RenderFAQsResponse,
    status_code=status.HTTP_200_OK,
    summary="Preview FAQ HTML without saving",
    description="""Generate FAQ HTML with Schema.org Microdata for preview.

    This endpoint allows users to:
    1. Preview how FAQs will look before saving
    2. Test different FAQ combinations
    3. Get the HTML for external use

    **No database changes are made** - this is purely for preview/rendering.

    The generated HTML includes:
    - Schema.org FAQPage Microdata (for Google rich snippets)
    - Visible FAQ section (required by Google's structured data policy)
    - Optional medical disclaimer
    """,
)
async def render_faqs_preview(
    request: RenderFAQsRequest,
) -> RenderFAQsResponse:
    """Render FAQ HTML for preview without saving to database.

    Args:
        request: Render request with FAQs to preview

    Returns:
        Response with generated FAQ HTML
    """
    logger.info(f"POST /articles/faqs/render - Rendering {len(request.faqs)} FAQs for preview")

    if not request.faqs:
        return RenderFAQsResponse(
            faq_html="",
            faq_count=0,
            schema_type="FAQPage",
        )

    # Generate FAQ HTML with Schema.org Microdata
    faq_html = _generate_faq_html_from_items(
        request.faqs,
        disclaimer_required=request.include_disclaimer,
    )

    return RenderFAQsResponse(
        faq_html=faq_html,
        faq_count=len(request.faqs),
        schema_type="FAQPage",
    )
