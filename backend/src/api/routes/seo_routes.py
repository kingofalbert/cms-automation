"""SEO analysis API routes."""

from datetime import datetime
from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.seo_analysis import (
    SEOAnalysisBatchResponse,
    SEOAnalysisSingleResponse,
    SEOTaskStatusResponse,
)
from src.config.database import get_session as get_db
from src.config.logging import get_logger
from src.models.article import Article
from src.models.seo import SEOMetadata
from src.workers.celery_app import celery_app

router = APIRouter()
logger = get_logger(__name__)


# ============================================================================
# Pydantic Schemas for SEO CRUD
# ============================================================================


class SEOMetadataResponse(BaseModel):
    """Response model for SEO metadata."""

    id: int
    article_id: int
    meta_title: str | None = None
    meta_description: str | None = None
    focus_keyword: str | None = None
    primary_keywords: list[str] | None = None
    secondary_keywords: list[str] | None = None
    keyword_density: dict[str, Any] | None = None
    readability_score: float | None = None
    seo_score: float | None = None
    optimization_recommendations: list[Any] | None = None
    manual_overrides: dict[str, Any] | None = None
    generated_by: str | None = None
    generation_cost: float | None = None
    generation_tokens: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class SEOUpdateRequest(BaseModel):
    """Request model for updating SEO metadata."""

    meta_title: str | None = Field(None, description="SEO meta title")
    meta_description: str | None = Field(None, description="SEO meta description")
    focus_keyword: str | None = Field(None, description="Primary focus keyword")
    primary_keywords: list[str] | None = Field(None, description="Primary keywords")
    secondary_keywords: list[str] | None = Field(None, description="Secondary keywords")
    manual_overrides: dict[str, Any] | None = Field(None, description="Manual override tracking")


# ============================================================================
# SEO CRUD Endpoints
# ============================================================================


@router.get("/seo/articles/{article_id}", response_model=SEOMetadataResponse)
async def get_seo_metadata(
    article_id: int,
    db: AsyncSession = Depends(get_db),
) -> SEOMetadataResponse:
    """Get SEO metadata for an article.

    Args:
        article_id: ID of the article
        db: Database session

    Returns:
        SEO metadata for the article

    Raises:
        404: Article or SEO metadata not found
    """
    logger.info(f"GET /seo/articles/{article_id}")

    # Verify article exists
    stmt = select(Article).where(Article.id == article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )

    # Get SEO metadata
    stmt = select(SEOMetadata).where(SEOMetadata.article_id == article_id)
    result = await db.execute(stmt)
    seo_metadata = result.scalar_one_or_none()

    if not seo_metadata:
        # Return empty/default SEO metadata if not exists
        # Create a minimal response with article_id
        return SEOMetadataResponse(
            id=0,
            article_id=article_id,
            meta_title=article.seo_title or article.title,
            meta_description=article.meta_description,
            focus_keyword=None,
            primary_keywords=article.seo_keywords or [],
            secondary_keywords=[],
            keyword_density={},
            readability_score=None,
            seo_score=None,
            optimization_recommendations=[],
            manual_overrides={},
            generated_by=None,
            generation_cost=None,
            generation_tokens=None,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )

    return SEOMetadataResponse.model_validate(seo_metadata)


@router.put("/seo/articles/{article_id}", response_model=SEOMetadataResponse)
async def update_seo_metadata(
    article_id: int,
    request: SEOUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> SEOMetadataResponse:
    """Update SEO metadata for an article.

    This endpoint allows updating SEO fields and tracking manual overrides.
    It primarily updates the Article's fields directly to avoid strict
    SEOMetadata table constraints.

    Args:
        article_id: ID of the article
        request: SEO update request with fields to update
        db: Database session

    Returns:
        Updated SEO metadata response

    Raises:
        404: Article not found
    """
    logger.info(f"PUT /seo/articles/{article_id}")

    # Verify article exists
    stmt = select(Article).where(Article.id == article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )

    # Update article fields directly (more flexible than SEOMetadata table)
    if request.meta_description is not None:
        article.meta_description = request.meta_description

    if request.meta_title is not None:
        article.seo_title = request.meta_title

    if request.primary_keywords is not None:
        article.seo_keywords = request.primary_keywords

    # Store manual_overrides in article_metadata
    if request.manual_overrides is not None:
        existing_metadata = dict(article.article_metadata) if article.article_metadata else {}
        existing_metadata["seo_manual_overrides"] = request.manual_overrides
        article.article_metadata = existing_metadata

    article.updated_at = datetime.utcnow()

    # Also update SEOMetadata if it exists (but don't create if not)
    stmt = select(SEOMetadata).where(SEOMetadata.article_id == article_id)
    result = await db.execute(stmt)
    seo_metadata = result.scalar_one_or_none()

    if seo_metadata:
        # Update SEO metadata record with non-null values
        if request.meta_title is not None:
            # Ensure title length is within constraints (50-60 chars)
            title = request.meta_title
            if len(title) < 50:
                title = title + " " * (50 - len(title))  # Pad if too short
            elif len(title) > 60:
                title = title[:60]  # Truncate if too long
            seo_metadata.meta_title = title

        if request.meta_description is not None:
            # Ensure description length is within constraints (150-160 chars)
            desc = request.meta_description
            if len(desc) < 150:
                desc = desc + " " * (150 - len(desc))  # Pad if too short
            elif len(desc) > 160:
                desc = desc[:160]  # Truncate if too long
            seo_metadata.meta_description = desc

        if request.focus_keyword is not None:
            seo_metadata.focus_keyword = request.focus_keyword

        if request.primary_keywords is not None:
            seo_metadata.primary_keywords = request.primary_keywords

        if request.secondary_keywords is not None:
            seo_metadata.secondary_keywords = request.secondary_keywords

        if request.manual_overrides is not None:
            existing_overrides = seo_metadata.manual_overrides or {}
            existing_overrides.update(request.manual_overrides)
            seo_metadata.manual_overrides = existing_overrides

    await db.commit()

    logger.info(f"Updated SEO data for article {article_id}")

    # Return a response based on the updated article
    return SEOMetadataResponse(
        id=seo_metadata.id if seo_metadata else 0,
        article_id=article_id,
        meta_title=article.seo_title or article.title,
        meta_description=article.meta_description,
        focus_keyword=seo_metadata.focus_keyword if seo_metadata else None,
        primary_keywords=article.seo_keywords or [],
        secondary_keywords=seo_metadata.secondary_keywords if seo_metadata else [],
        keyword_density=seo_metadata.keyword_density if seo_metadata else {},
        readability_score=seo_metadata.readability_score if seo_metadata else None,
        seo_score=seo_metadata.seo_score if seo_metadata else None,
        optimization_recommendations=seo_metadata.optimization_recommendations if seo_metadata else [],
        manual_overrides=article.article_metadata.get("seo_manual_overrides", {}) if article.article_metadata else {},
        generated_by=seo_metadata.generated_by if seo_metadata else None,
        generation_cost=seo_metadata.generation_cost if seo_metadata else None,
        generation_tokens=seo_metadata.generation_tokens if seo_metadata else None,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


@router.delete("/seo/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seo_metadata(
    article_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete SEO metadata for an article.

    Args:
        article_id: ID of the article
        db: Database session

    Raises:
        404: Article or SEO metadata not found
    """
    logger.info(f"DELETE /seo/articles/{article_id}")

    # Get SEO metadata
    stmt = select(SEOMetadata).where(SEOMetadata.article_id == article_id)
    result = await db.execute(stmt)
    seo_metadata = result.scalar_one_or_none()

    if not seo_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SEO metadata for article {article_id} not found",
        )

    await db.delete(seo_metadata)
    await db.commit()

    logger.info(f"Deleted SEO metadata for article {article_id}")


@router.post("/seo/analyze/{article_id}", response_model=SEOAnalysisSingleResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_article_seo(article_id: int) -> SEOAnalysisSingleResponse:
    """Analyze SEO for a single article.

    Queues an asynchronous task to analyze the article and generate SEO metadata.

    Args:
        article_id: Article ID to analyze

    Returns:
        SEOAnalysisSingleResponse with task_id for tracking

    Raises:
        HTTPException: If task queuing fails
    """
    try:
        # Lazy import to avoid circular dependency
        from src.workers.tasks import analyze_seo_single_task

        task = analyze_seo_single_task.delay(article_id)

        logger.info(
            "seo_analysis_task_queued",
            task_id=task.id,
            article_id=article_id,
        )

        return SEOAnalysisSingleResponse(
            task_id=task.id,
            message=f"SEO analysis task queued for article {article_id}",
            article_id=article_id,
            status_url=f"/v1/seo/status/{task.id}",
        )

    except Exception as e:
        logger.error(
            "seo_analysis_task_queue_failed",
            article_id=article_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue SEO analysis task: {str(e)}",
        ) from e


@router.post("/seo/analyze-batch", response_model=SEOAnalysisBatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_batch_seo(limit: int | None = None) -> SEOAnalysisBatchResponse:
    """Analyze SEO for all imported articles without SEO metadata.

    Queues an asynchronous task to batch analyze articles.

    Args:
        limit: Optional limit on number of articles to process

    Returns:
        SEOAnalysisBatchResponse with task_id for tracking

    Raises:
        HTTPException: If task queuing fails
    """
    try:
        # Lazy import to avoid circular dependency
        from src.workers.tasks import analyze_seo_batch_task

        task = analyze_seo_batch_task.delay(limit)

        logger.info(
            "seo_batch_analysis_task_queued",
            task_id=task.id,
            limit=limit,
        )

        return SEOAnalysisBatchResponse(
            task_id=task.id,
            message=f"Batch SEO analysis task queued{f' (limit: {limit})' if limit else ''}",
            limit=limit,
            status_url=f"/v1/seo/status/{task.id}",
        )

    except Exception as e:
        logger.error(
            "seo_batch_analysis_task_queue_failed",
            limit=limit,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue batch SEO analysis task: {str(e)}",
        ) from e


@router.get("/seo/status/{task_id}", response_model=SEOTaskStatusResponse)
async def get_seo_task_status(task_id: str) -> SEOTaskStatusResponse:
    """Get status of SEO analysis task.

    Args:
        task_id: Celery task ID

    Returns:
        SEOTaskStatusResponse with task status and result

    Raises:
        HTTPException: If task not found or status check fails
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        # Map Celery states to our status
        status_map = {
            "PENDING": "pending",
            "STARTED": "running",
            "SUCCESS": "completed",
            "FAILURE": "failed",
            "RETRY": "running",
            "REVOKED": "failed",
        }

        status_value = status_map.get(task_result.state, "unknown")

        response = SEOTaskStatusResponse(
            task_id=task_id,
            status=status_value,
        )

        # Add result if completed
        if task_result.state == "SUCCESS":
            result_data = task_result.result
            if result_data:
                response.result = result_data

        # Add error if failed
        elif task_result.state == "FAILURE":
            response.error = str(task_result.result)

        logger.debug(
            "seo_task_status_checked",
            task_id=task_id,
            status=status_value,
        )

        return response

    except Exception as e:
        logger.error(
            "seo_task_status_check_failed",
            task_id=task_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check task status: {str(e)}",
        ) from e


@router.delete("/seo/task/{task_id}")
async def cancel_seo_task(task_id: str) -> dict[str, str]:
    """Cancel a running SEO analysis task.

    Args:
        task_id: Celery task ID

    Returns:
        dict with cancellation status

    Raises:
        HTTPException: If task cannot be cancelled
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        if task_result.state in ["SUCCESS", "FAILURE"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel {task_result.state.lower()} task",
            )

        # Revoke the task
        task_result.revoke(terminate=True)

        logger.info("seo_task_cancelled", task_id=task_id)

        return {
            "message": f"SEO analysis task {task_id} cancelled",
            "status": "cancelled",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "seo_task_cancel_failed",
            task_id=task_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}",
        ) from e
