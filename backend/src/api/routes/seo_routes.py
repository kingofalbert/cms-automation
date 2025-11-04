"""SEO analysis API routes."""


from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status

from src.api.schemas.seo_analysis import (
    SEOAnalysisBatchResponse,
    SEOAnalysisSingleResponse,
    SEOTaskStatusResponse,
)
from src.config.logging import get_logger
from src.workers.celery_app import celery_app

router = APIRouter()
logger = get_logger(__name__)


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
