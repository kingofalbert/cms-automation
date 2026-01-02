"""API routes for article parsing (Phase 7).

This module provides endpoints for:
- Triggering article parsing (AI or heuristic)
- Retrieving parsing results
- Confirming parsed data
- Reviewing and managing parsed images
"""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_session as get_db
from src.models.article import Article
from src.models.article_image import ArticleImage, ArticleImageReview, ImageReviewAction
from src.services.parser import (
    ArticleProcessingService,
    ParsedArticle,
    create_article_processor,
)
from src.services.parser.unified_optimization_service import UnifiedOptimizationService
from src.config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Background Tasks
# ============================================================================


async def generate_optimizations_background(article_id: int) -> None:
    """Background task to generate AI optimization suggestions after parsing.

    This task is triggered automatically after parsing confirmation to:
    1. Generate title optimization suggestions
    2. Generate SEO keywords and meta description
    3. Generate FAQ questions

    Runs asynchronously to avoid blocking the confirmation response.

    Note: Creates its own database session to avoid issues with closed sessions
    after the main request completes.
    """
    from src.db.session import async_session_maker

    try:
        logger.info(f"Starting background optimization generation for article {article_id}")

        # Create a new database session for this background task
        async with async_session_maker() as db_session:
            # Get article from database
            article = await db_session.get(Article, article_id)
            if not article:
                logger.error(f"Article {article_id} not found in background task")
                return

            # Get settings
            settings = get_settings()

            # Create optimization service
            service = UnifiedOptimizationService(
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                db_session=db_session,
            )

            # Generate all optimizations
            result = await service.generate_all_optimizations(
                article=article,
                regenerate=False,  # Don't regenerate if already exists
            )

            logger.info(
                f"Background optimization completed for article {article_id}: "
                f"cost=${result.get('generation_metadata', {}).get('total_cost_usd', 0):.4f}, "
                f"cached={result.get('generation_metadata', {}).get('cached', False)}"
            )

    except Exception as e:
        logger.exception(f"Error generating optimizations in background for article {article_id}: {e}")


# ============================================================================
# Pydantic Schemas
# ============================================================================


class ParseArticleRequest(BaseModel):
    """Request body for parsing an article."""

    use_ai: bool = Field(
        default=True,
        description="Whether to use AI-based parsing (Claude). If False, uses heuristic parsing.",
    )
    download_images: bool = Field(
        default=True,
        description="Whether to download and process images from the article.",
    )
    fallback_to_heuristic: bool = Field(
        default=True,
        description="If AI parsing fails, automatically fall back to heuristic parsing.",
    )


class ParseArticleResponse(BaseModel):
    """Response for article parsing."""

    success: bool
    article_id: int
    parsing_method: str | None = None  # 'ai' or 'heuristic'
    parsing_confidence: float | None = None
    images_processed: int = 0
    duration_ms: float
    warnings: list[str] = []
    errors: list[str] = []


class RelatedArticleSchema(BaseModel):
    """Related article data for internal linking (Phase 12)."""

    article_id: str
    title: str
    title_main: str | None = None
    url: str
    excerpt: str | None = None
    similarity: float
    match_type: str  # 'semantic', 'content', or 'keyword'
    ai_keywords: list[str] = []


class ParsedArticleData(BaseModel):
    """Parsed article data for display/confirmation."""

    # Title components
    title_prefix: str | None = None
    title_main: str
    title_suffix: str | None = None
    full_title: str

    # Author info
    author_line: str | None = None
    author_name: str | None = None

    # Content
    body_html: str
    meta_description: str | None = None
    seo_keywords: list[str] = []

    # Parsing metadata
    parsing_method: str
    parsing_confidence: float
    parsing_confirmed: bool
    has_seo_data: bool

    # Images
    images: list[dict[str, Any]] = []

    # Related articles for internal linking (Phase 12)
    related_articles: list[RelatedArticleSchema] = []

    # FAQ v2.2 Assessment Fields (Phase 13)
    faq_applicable: bool | None = None
    faq_assessment: dict[str, Any] | None = None
    faq_html: str | None = None
    body_html_with_faq: str | None = None  # Combined body + FAQ for publishing

    # Phase 14: Extracted FAQs from original article (for comparison with AI-generated)
    extracted_faqs: list[dict[str, Any]] | None = None
    extracted_faqs_detection_method: str | None = None

    class Config:
        from_attributes = True


class ConfirmParsingRequest(BaseModel):
    """Request body for confirming parsed article data."""

    confirmed_by: str = Field(..., description="Username or ID of user confirming")
    feedback: str | None = Field(None, description="Optional feedback about parsing quality")


class ImageReviewRequest(BaseModel):
    """Request body for reviewing an image."""

    action: ImageReviewAction = Field(..., description="Action to take on this image")
    new_caption: str | None = Field(None, description="New caption (if action=replace_caption)")
    new_source_url: str | None = Field(
        None, description="New source URL (if action=replace_source)"
    )


# ============================================================================
# Article Parsing Endpoints
# ============================================================================


@router.post(
    "/articles/{article_id}/parse",
    response_model=ParseArticleResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse article content",
    description="Parse an article's raw HTML to extract structured data (title, author, body, SEO, images)",
)
async def parse_article(
    article_id: int,
    request: ParseArticleRequest,
    db: AsyncSession = Depends(get_db),
) -> ParseArticleResponse:
    """Parse an article and extract structured data.

    This endpoint:
    1. Fetches the article's raw HTML from Google Docs
    2. Parses it using AI (Claude) or heuristic methods
    3. Extracts: title, author, body, SEO metadata, images
    4. Downloads and processes images (if requested)
    5. Saves parsed data to database

    The parsed data needs to be confirmed before publishing.
    """
    logger.info(f"Parsing article {article_id} (use_ai={request.use_ai})")

    # Fetch article
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )

    # Check if article has raw HTML
    if not article.raw_html:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article has no raw HTML to parse. Import from Google Docs first.",
        )

    # Get settings
    settings = get_settings()

    # Create article processor
    processor = await create_article_processor(
        use_ai_parsing=request.use_ai,
        anthropic_api_key=settings.ANTHROPIC_API_KEY if request.use_ai else None,
        storage_path=str(settings.IMAGE_STORAGE_PATH),
    )

    try:
        # Process article
        result = await processor.process_article(
            article_id=article_id,
            raw_html=article.raw_html,
            db_session=db,
            download_images=request.download_images,
        )

        if result["success"]:
            logger.info(
                f"Article {article_id} parsed successfully: "
                f"{result['parsing_method']}, {result['images_processed']} images"
            )

            # Update worklist status to parsing_review if article is linked to worklist
            from src.models.worklist import WorklistItem, WorklistStatus
            from sqlalchemy import select

            result_query = await db.execute(
                select(WorklistItem).where(WorklistItem.article_id == article_id)
            )
            worklist_item = result_query.scalar_one_or_none()

            if worklist_item:
                worklist_item.mark_status(WorklistStatus.PARSING_REVIEW)
                worklist_item.add_note(
                    {
                        "message": "文章解析完成，等待人工审核标题、作者、SEO 和图片",
                        "level": "info",
                        "metadata": {
                            "parsing_method": result["parsing_method"],
                            "parsing_confidence": result["parsing_confidence"],
                            "images_processed": result["images_processed"],
                        },
                    }
                )
                await db.commit()
                logger.info(
                    f"Updated worklist item {worklist_item.id} status to PARSING_REVIEW after successful parsing"
                )

            return ParseArticleResponse(
                success=True,
                article_id=article_id,
                parsing_method=result["parsing_method"],
                parsing_confidence=result["parsing_confidence"],
                images_processed=result["images_processed"],
                duration_ms=result["duration_ms"],
                warnings=result.get("warnings", []),
            )
        else:
            logger.error(f"Article {article_id} parsing failed: {result.get('errors', [])}")
            return ParseArticleResponse(
                success=False,
                article_id=article_id,
                duration_ms=result["duration_ms"],
                errors=result.get("errors", []),
            )

    except Exception as e:
        logger.exception(f"Error parsing article {article_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse article: {str(e)}",
        )
    finally:
        await processor.close()


@router.get(
    "/articles/{article_id}/parsing-result",
    response_model=ParsedArticleData,
    summary="Get parsed article data",
    description="Retrieve the parsed data for an article (for review/confirmation)",
)
async def get_parsing_result(
    article_id: int,
    db: AsyncSession = Depends(get_db),
) -> ParsedArticleData:
    """Get parsed article data for review.

    Returns the structured data extracted from the article,
    including title components, author, body HTML, SEO metadata,
    and processed images.
    """
    # Fetch article with images
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    stmt = select(Article).where(Article.id == article_id).options(selectinload(Article.article_images))
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )

    # Check if article has been parsed
    if not article.title_main:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article has not been parsed yet. Call /parse first.",
        )

    # Build full title
    full_title_parts = []
    if article.title_prefix:
        full_title_parts.append(article.title_prefix)
    full_title_parts.append(article.title_main)
    if article.title_suffix:
        full_title_parts.append(article.title_suffix)
    full_title = " ".join(full_title_parts)

    # Format images
    images = [
        {
            "id": img.id,
            "position": img.position,
            "source_url": img.source_url,
            "preview_path": img.preview_path,
            "caption": img.caption,
            "width": img.image_width,
            "height": img.image_height,
            "format": img.image_format,
        }
        for img in sorted(article.article_images, key=lambda x: x.position)
    ]

    # Format related articles (Phase 12)
    related_articles = []
    if article.related_articles:
        for ra in article.related_articles:
            related_articles.append(
                RelatedArticleSchema(
                    article_id=ra.get("article_id", ""),
                    title=ra.get("title", ""),
                    title_main=ra.get("title_main"),
                    url=ra.get("url", ""),
                    excerpt=ra.get("excerpt"),
                    similarity=ra.get("similarity", 0.0),
                    match_type=ra.get("match_type", "keyword"),
                    ai_keywords=ra.get("ai_keywords", []),
                )
            )

    # Build combined body + FAQ for publishing
    body_html_with_faq = article.body_html or ""
    if article.faq_html and article.faq_applicable:
        body_html_with_faq = f"{body_html_with_faq}\n\n{article.faq_html}"

    return ParsedArticleData(
        title_prefix=article.title_prefix,
        title_main=article.title_main,
        title_suffix=article.title_suffix,
        full_title=full_title,
        author_line=article.author_line,
        author_name=article.author_name,
        body_html=article.body_html or "",
        meta_description=article.meta_description,
        seo_keywords=article.seo_keywords or [],
        parsing_method=article.parsing_method or "unknown",
        parsing_confidence=article.parsing_confidence or 0.0,
        parsing_confirmed=article.parsing_confirmed,
        has_seo_data=bool(article.meta_description or article.seo_keywords),
        images=images,
        related_articles=related_articles,
        # FAQ v2.2 fields
        faq_applicable=article.faq_applicable,
        faq_assessment=article.faq_assessment,
        faq_html=article.faq_html,
        body_html_with_faq=body_html_with_faq,
        # Phase 14: Extracted FAQs for comparison
        extracted_faqs=article.extracted_faqs,
        extracted_faqs_detection_method=article.extracted_faqs_detection_method,
    )


@router.post(
    "/articles/{article_id}/confirm-parsing",
    status_code=status.HTTP_200_OK,
    summary="Confirm parsed article data",
    description="Confirm that the parsed data is correct and ready for publishing. Automatically triggers AI optimization generation.",
)
async def confirm_parsing(
    article_id: int,
    request: ConfirmParsingRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Confirm that parsed article data is correct.

    This marks the article as ready for the next stage (publishing).
    After confirmation, the parsed data is locked and changes require re-parsing.

    **Auto-triggers optimization generation** (Phase 7):
    After confirmation, automatically generates AI optimization suggestions
    (title options, SEO keywords, meta description, tags, FAQs) in the background.
    """
    from datetime import datetime

    # Fetch article
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )

    # Check if article has been parsed
    if not article.title_main:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article has not been parsed yet. Nothing to confirm.",
        )

    # Mark as confirmed
    article.parsing_confirmed = True
    article.parsing_confirmed_at = datetime.utcnow()
    article.parsing_confirmed_by = request.confirmed_by
    article.parsing_feedback = request.feedback

    # Update worklist status if article is linked to worklist
    from src.models.worklist import WorklistItem, WorklistStatus
    from sqlalchemy import select

    result = await db.execute(
        select(WorklistItem).where(WorklistItem.article_id == article_id)
    )
    worklist_item = result.scalar_one_or_none()

    if worklist_item:
        worklist_item.mark_status(WorklistStatus.PROOFREADING)
        worklist_item.add_note(
            {
                "message": "解析审核已完成，开始自动校对",
                "level": "info",
                "metadata": {
                    "parsing_confirmed_by": request.confirmed_by,
                    "parsing_confirmed_at": datetime.utcnow().isoformat(),
                },
            }
        )
        logger.info(
            f"Updated worklist item {worklist_item.id} status to PROOFREADING after parsing confirmation"
        )

    await db.commit()

    logger.info(
        f"Article {article_id} parsing confirmed by {request.confirmed_by}",
        extra={"article_id": article_id, "confirmed_by": request.confirmed_by},
    )

    # Trigger optimization generation in background (Phase 7)
    # This generates title/SEO/FAQ suggestions without blocking the response
    background_tasks.add_task(
        generate_optimizations_background,
        article_id=article_id,
    )
    logger.info(f"Scheduled background optimization generation for article {article_id}")

    return {
        "success": True,
        "article_id": article_id,
        "confirmed_at": article.parsing_confirmed_at.isoformat(),
        "confirmed_by": article.parsing_confirmed_by,
        "optimization_scheduled": True,  # Indicate that optimization generation was triggered
    }


# ============================================================================
# Image Review Endpoints
# ============================================================================


@router.post(
    "/articles/{article_id}/images/{image_id}/review",
    status_code=status.HTTP_200_OK,
    summary="Review and manage a parsed image",
    description="Take action on a parsed image (keep, remove, or replace)",
)
async def review_image(
    article_id: int,
    image_id: int,
    request: ImageReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Review a parsed image and take action.

    Actions:
    - keep: Keep the image as-is
    - remove: Remove the image from the article
    - replace_caption: Update the image caption
    - replace_source: Replace the image with a different source URL
    """
    # Fetch image
    image = await db.get(ArticleImage, image_id)
    if not image or image.article_id != article_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} not found for article {article_id}",
        )

    # Validate action-specific requirements
    if request.action == ImageReviewAction.REPLACE_CAPTION and not request.new_caption:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="new_caption is required when action=replace_caption",
        )

    if request.action == ImageReviewAction.REPLACE_SOURCE and not request.new_source_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="new_source_url is required when action=replace_source",
        )

    # Create review record
    review = ArticleImageReview(
        article_image_id=image_id,
        action=request.action,
        new_caption=request.new_caption,
        new_source_url=request.new_source_url,
    )
    db.add(review)

    # Apply action
    if request.action == ImageReviewAction.REMOVE:
        await db.delete(image)
        logger.info(f"Removed image {image_id} from article {article_id}")

    elif request.action == ImageReviewAction.REPLACE_CAPTION:
        image.caption = request.new_caption
        logger.info(f"Updated caption for image {image_id}")

    elif request.action == ImageReviewAction.REPLACE_SOURCE:
        # TODO: Re-download image from new source
        image.source_url = request.new_source_url
        logger.info(f"Updated source URL for image {image_id}")

    await db.commit()

    return {
        "success": True,
        "image_id": image_id,
        "action": request.action.value,
        "review_id": review.id,
    }


@router.get(
    "/articles/{article_id}/images",
    summary="List all images for an article",
    description="Get all parsed images for an article, ordered by position",
)
async def list_article_images(
    article_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List all images for an article."""
    from sqlalchemy import select

    # Fetch images
    stmt = (
        select(ArticleImage)
        .where(ArticleImage.article_id == article_id)
        .order_by(ArticleImage.position)
    )
    result = await db.execute(stmt)
    images = result.scalars().all()

    return [
        {
            "id": img.id,
            "position": img.position,
            "source_url": img.source_url,
            "preview_path": img.preview_path,
            "caption": img.caption,
            "width": img.image_width,
            "height": img.image_height,
            "format": img.image_format,
            "file_size_bytes": img.file_size_bytes,
        }
        for img in images
    ]
