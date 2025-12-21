"""Image Alt Text and Description Generation API Routes

Phase 13: Enhanced Image Review
Provides endpoints for generating AI-suggested alt text and descriptions for images.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.config.logging import get_logger
from src.models.article_image import ArticleImage
from src.models.worklist import WorklistItem
from src.services.image_alt_generator import (
    GenerationMethod,
    ImageType,
    get_image_alt_generator_service,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/images", tags=["Image Alt Generation"])


# === Request/Response Schemas ===


class ImageAltGenerateRequest(BaseModel):
    """Request for generating image alt text"""
    use_vision: bool = Field(
        default=True,
        description="Whether to use vision analysis (recommended for best results)"
    )


class ImageAltSuggestionResponse(BaseModel):
    """Response containing alt text and description suggestions"""
    image_id: int

    # Original parsed content
    parsed_alt_text: str | None = Field(
        default=None,
        description="Original alt text from document parsing"
    )
    parsed_caption: str | None = Field(
        default=None,
        description="Original caption (圖說) from document parsing"
    )
    parsed_description: str | None = Field(
        default=None,
        description="Original description from document parsing"
    )

    # AI suggestions
    suggested_alt_text: str = Field(
        description="AI-generated alt text suggestion"
    )
    suggested_alt_text_confidence: float = Field(
        ge=0,
        le=1,
        description="Confidence score for alt text (0-1)"
    )
    suggested_description: str = Field(
        description="AI-generated description suggestion"
    )
    suggested_description_confidence: float = Field(
        ge=0,
        le=1,
        description="Confidence score for description (0-1)"
    )

    # Image analysis results
    image_type: str = Field(
        default="unknown",
        description="Detected image type: 'infographic' (has embedded text), 'photo' (no text), or 'unknown'"
    )
    detected_text: str | None = Field(
        default=None,
        description="Text extracted from the image via OCR (only for infographic images)"
    )

    # Generation metadata
    generation_method: str = Field(
        description="Method used: 'vision_infographic', 'vision_photo', 'vision', 'context', or 'failed'"
    )
    model_used: str = Field(
        description="AI model used for generation"
    )
    tokens_used: int = Field(
        description="Number of tokens used"
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if generation failed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "image_id": 123,
                "parsed_alt_text": None,
                "parsed_caption": "習近平會見外國領導人",
                "parsed_description": None,
                "suggested_alt_text": "信息圖顯示：「中美貿易戰最新進展」標題，配有兩國國旗和關稅數據圖表",
                "suggested_alt_text_confidence": 0.95,
                "suggested_description": "信息圖展示中美貿易戰最新進展，包含標題「中美貿易戰最新進展」，下方為兩國國旗圖示，以及關稅變化的折線圖和數據表格。",
                "suggested_description_confidence": 0.92,
                "image_type": "infographic",
                "detected_text": "中美貿易戰最新進展\n關稅調整時間表\n2024年3月15日生效",
                "generation_method": "vision_infographic",
                "model_used": "gpt-4o",
                "tokens_used": 650,
                "error_message": None
            }
        }


class BatchImageAltRequest(BaseModel):
    """Request for batch generating alt text for multiple images"""
    image_ids: list[int] = Field(
        description="List of image IDs to generate suggestions for"
    )
    use_vision: bool = Field(
        default=True,
        description="Whether to use vision analysis"
    )


class BatchImageAltResponse(BaseModel):
    """Response containing multiple image alt suggestions"""
    suggestions: list[ImageAltSuggestionResponse]
    total_tokens_used: int
    successful_count: int
    failed_count: int


# === API Endpoints ===


@router.post(
    "/{image_id}/generate-alt",
    response_model=ImageAltSuggestionResponse,
    summary="Generate alt text and description for an image",
    description="""
    Generate AI-suggested alt text and description for a specific image.

    Uses GPT-4o vision when the image is accessible, falls back to
    context-based generation when image cannot be fetched.

    The response includes:
    - Original parsed content (if any)
    - AI suggestions with confidence scores
    - Generation method used (vision vs context)
    """
)
async def generate_image_alt(
    image_id: int,
    request: ImageAltGenerateRequest = ImageAltGenerateRequest(),
    db: AsyncSession = Depends(get_db)
) -> ImageAltSuggestionResponse:
    """Generate alt text and description suggestions for an image"""

    # Fetch image from database
    result = await db.execute(
        select(ArticleImage).where(ArticleImage.id == image_id)
    )
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")

    # Fetch article for context
    article = image.article
    if not article:
        raise HTTPException(
            status_code=404,
            detail=f"Article not found for image {image_id}"
        )

    # Determine image URL (prefer preview_path, fall back to source_url)
    image_url = None
    if image.preview_path:
        # Convert local path to accessible URL if needed
        # For now, use preview_path directly or construct URL
        image_url = image.preview_path
    elif image.source_url:
        image_url = image.source_url

    # Build article context
    article_context = {
        "title": article.title or "",
        "excerpt": article.body_text[:500] if article.body_text else "",
        "position": image.position or 0,
        "is_featured": image.position == 0  # First image is typically featured
    }

    # Generate suggestions
    service = get_image_alt_generator_service()
    suggestion = await service.generate_suggestions(
        image_id=image_id,
        image_url=image_url,
        article_context=article_context,
        parsed_alt_text=image.alt_text,
        parsed_caption=image.caption,
        parsed_description=image.description,
        use_vision=request.use_vision
    )

    logger.info(
        "image_alt_generated",
        image_id=image_id,
        method=suggestion.generation_method.value,
        tokens=suggestion.tokens_used
    )

    return ImageAltSuggestionResponse(
        image_id=suggestion.image_id,
        parsed_alt_text=suggestion.parsed_alt_text,
        parsed_caption=suggestion.parsed_caption,
        parsed_description=suggestion.parsed_description,
        suggested_alt_text=suggestion.suggested_alt_text,
        suggested_alt_text_confidence=suggestion.suggested_alt_text_confidence,
        suggested_description=suggestion.suggested_description,
        suggested_description_confidence=suggestion.suggested_description_confidence,
        image_type=suggestion.image_type.value,
        detected_text=suggestion.detected_text,
        generation_method=suggestion.generation_method.value,
        model_used=suggestion.model_used,
        tokens_used=suggestion.tokens_used,
        error_message=suggestion.error_message
    )


@router.post(
    "/worklist/{worklist_item_id}/generate-all-alt",
    response_model=BatchImageAltResponse,
    summary="Generate alt text for all images in a worklist item",
    description="""
    Batch generate AI-suggested alt text and descriptions for all images
    associated with a worklist item's article.
    """
)
async def generate_all_image_alt(
    worklist_item_id: int,
    request: BatchImageAltRequest = BatchImageAltRequest(image_ids=[]),
    db: AsyncSession = Depends(get_db)
) -> BatchImageAltResponse:
    """Generate alt text for all images in a worklist item"""

    # Fetch worklist item
    result = await db.execute(
        select(WorklistItem).where(WorklistItem.id == worklist_item_id)
    )
    worklist_item = result.scalar_one_or_none()

    if not worklist_item or not worklist_item.article_id:
        raise HTTPException(
            status_code=404,
            detail=f"Worklist item {worklist_item_id} not found or has no article"
        )

    # Fetch all images for the article
    result = await db.execute(
        select(ArticleImage)
        .where(ArticleImage.article_id == worklist_item.article_id)
        .order_by(ArticleImage.position)
    )
    images = result.scalars().all()

    if not images:
        return BatchImageAltResponse(
            suggestions=[],
            total_tokens_used=0,
            successful_count=0,
            failed_count=0
        )

    # Fetch article for context
    article = worklist_item.article
    article_context_base = {
        "title": article.title or "",
        "excerpt": article.body_text[:500] if article.body_text else ""
    }

    # Generate suggestions for each image
    service = get_image_alt_generator_service()
    suggestions = []
    total_tokens = 0
    successful = 0
    failed = 0

    for image in images:
        # Determine image URL
        image_url = image.preview_path or image.source_url

        # Build context for this image
        article_context = {
            **article_context_base,
            "position": image.position or 0,
            "is_featured": image.position == 0
        }

        suggestion = await service.generate_suggestions(
            image_id=image.id,
            image_url=image_url,
            article_context=article_context,
            parsed_alt_text=image.alt_text,
            parsed_caption=image.caption,
            parsed_description=image.description,
            use_vision=request.use_vision
        )

        total_tokens += suggestion.tokens_used

        if suggestion.generation_method == GenerationMethod.FAILED:
            failed += 1
        else:
            successful += 1

        suggestions.append(ImageAltSuggestionResponse(
            image_id=suggestion.image_id,
            parsed_alt_text=suggestion.parsed_alt_text,
            parsed_caption=suggestion.parsed_caption,
            parsed_description=suggestion.parsed_description,
            suggested_alt_text=suggestion.suggested_alt_text,
            suggested_alt_text_confidence=suggestion.suggested_alt_text_confidence,
            suggested_description=suggestion.suggested_description,
            suggested_description_confidence=suggestion.suggested_description_confidence,
            image_type=suggestion.image_type.value,
            detected_text=suggestion.detected_text,
            generation_method=suggestion.generation_method.value,
            model_used=suggestion.model_used,
            tokens_used=suggestion.tokens_used,
            error_message=suggestion.error_message
        ))

    logger.info(
        "batch_image_alt_generated",
        worklist_item_id=worklist_item_id,
        total_images=len(images),
        successful=successful,
        failed=failed,
        total_tokens=total_tokens
    )

    return BatchImageAltResponse(
        suggestions=suggestions,
        total_tokens_used=total_tokens,
        successful_count=successful,
        failed_count=failed
    )


@router.patch(
    "/{image_id}/alt",
    summary="Update image alt text and description",
    description="Update the alt text and/or description for an image"
)
async def update_image_alt(
    image_id: int,
    alt_text: str | None = Query(default=None, description="New alt text"),
    description: str | None = Query(default=None, description="New description"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Update image alt text and description"""

    result = await db.execute(
        select(ArticleImage).where(ArticleImage.id == image_id)
    )
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")

    updated_fields = []

    if alt_text is not None:
        image.alt_text = alt_text
        updated_fields.append("alt_text")

    if description is not None:
        image.description = description
        updated_fields.append("description")

    if updated_fields:
        await db.commit()
        logger.info(
            "image_alt_updated",
            image_id=image_id,
            fields=updated_fields
        )

    return {
        "image_id": image_id,
        "updated_fields": updated_fields,
        "alt_text": image.alt_text,
        "description": image.description
    }
