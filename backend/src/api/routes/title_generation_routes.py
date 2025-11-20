"""
Title Generation API Routes

独立的标题生成API端点，与统一解析器分离。
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.config.database import get_session as get_db
from src.services.title_generator import TitleGeneratorService, TitleGenerationResult
from src.models.article import Article
from src.models.worklist import WorklistItem

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["title_generation"],
)


class GenerateTitlesRequest(BaseModel):
    """Request model for title generation"""
    worklist_id: Optional[int] = Field(None, description="Worklist item ID to generate titles for")
    article_id: Optional[int] = Field(None, description="Article ID to generate titles for")
    title: Optional[str] = Field(None, description="Manual title input")
    content: Optional[str] = Field(None, description="Manual content input")


class GenerateTitlesResponse(BaseModel):
    """Response model for title generation"""
    success: bool
    suggested_titles: list[dict]
    error: Optional[str] = None
    source: str = Field(..., description="Source of generation: worklist, article, or manual")


@router.post("/generate-titles", response_model=GenerateTitlesResponse)
async def generate_titles(
    request: GenerateTitlesRequest,
    db: AsyncSession = Depends(get_db)
) -> GenerateTitlesResponse:
    """
    Generate SEO-optimized title suggestions

    This is an independent API that:
    1. Can work with worklist items, articles, or manual input
    2. Uses a focused prompt for better success rate
    3. Has fallback generation to ensure output
    4. Updates the database if worklist_id is provided

    Priority:
    1. worklist_id (fetches from worklist)
    2. article_id (fetches from article)
    3. manual input (title + content)
    """

    try:
        title = None
        content = None
        source = "manual"

        # Priority 1: Worklist ID
        if request.worklist_id:
            logger.info(f"Generating titles for worklist item {request.worklist_id}")

            worklist_item = await db.get(WorklistItem, request.worklist_id)
            if not worklist_item:
                raise HTTPException(status_code=404, detail=f"Worklist item {request.worklist_id} not found")

            # Get associated article
            if worklist_item.article_id:
                article = await db.get(Article, worklist_item.article_id)
                if article:
                    title = article.title or worklist_item.title
                    content = article.body_html or article.body or ""
                    source = "worklist"

            if not title:
                title = worklist_item.title
                content = worklist_item.meta.get("description", "") if worklist_item.meta else ""

        # Priority 2: Article ID
        elif request.article_id:
            logger.info(f"Generating titles for article {request.article_id}")

            article = await db.get(Article, request.article_id)
            if not article:
                raise HTTPException(status_code=404, detail=f"Article {request.article_id} not found")

            title = article.title
            content = article.body_html or article.body or ""
            source = "article"

        # Priority 3: Manual input
        elif request.title and request.content:
            logger.info("Generating titles from manual input")
            title = request.title
            content = request.content
            source = "manual"

        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either worklist_id, article_id, or both title and content"
            )

        # Initialize service
        if not settings.ANTHROPIC_API_KEY:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

        service = TitleGeneratorService(api_key=settings.ANTHROPIC_API_KEY)

        # Generate titles
        result: TitleGenerationResult = await service.generate_titles(
            article_title=title,
            article_content=content
        )

        # Update database if worklist_id provided and generation successful
        if request.worklist_id and result.success and result.suggested_titles:
            logger.info(f"Updating worklist item {request.worklist_id} with generated titles")

            worklist_item = await db.get(WorklistItem, request.worklist_id)
            if worklist_item and worklist_item.article_id:
                article = await db.get(Article, worklist_item.article_id)
                if article:
                    article.suggested_titles = result.suggested_titles
                    await db.commit()
                    logger.info(f"Updated article {article.id} with {len(result.suggested_titles)} titles")

        return GenerateTitlesResponse(
            success=result.success,
            suggested_titles=result.suggested_titles,
            error=result.error,
            source=source
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Title generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Title generation failed: {str(e)}")


@router.post("/worklist/{worklist_id}/generate-titles", response_model=GenerateTitlesResponse)
async def generate_titles_for_worklist(
    worklist_id: int,
    db: AsyncSession = Depends(get_db)
) -> GenerateTitlesResponse:
    """
    Convenience endpoint: Generate titles for a specific worklist item

    This is a shortcut for the main generate-titles endpoint.
    """

    return await generate_titles(
        request=GenerateTitlesRequest(worklist_id=worklist_id),
        db=db
    )


@router.get("/title-generation/health")
async def health_check():
    """Health check for title generation service"""

    return {
        "status": "healthy",
        "service": "title_generation",
        "version": "1.0.0",
        "features": [
            "worklist_integration",
            "article_integration",
            "manual_input",
            "fallback_generation"
        ]
    }