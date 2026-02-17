"""Pipeline automation endpoints for Google Apps Script integration."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_session
from src.config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Pipeline Automation"])


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------


class AutoPublishRequest(BaseModel):
    google_doc_url: str = Field(..., description="Full Google Docs URL")
    sheet_row: int | None = Field(default=None, description="Row number in Google Sheet")


class AutoPublishResponse(BaseModel):
    task_id: str
    status: str  # "queued" | "completed" | "failed"
    message: str
    result: dict[str, Any] | None = None


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # "pending" | "processing" | "completed" | "failed"
    result: dict[str, Any] | None = None
    error: str | None = None


class CleanupRequest(BaseModel):
    worklist_item_id: int = Field(..., description="ID of the published worklist item to clean up")


class CleanupResponse(BaseModel):
    success: bool
    freed_bytes_estimate: int = Field(default=0, description="Estimated bytes freed")
    message: str = ""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/auto-publish",
    response_model=AutoPublishResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def auto_publish(
    payload: AutoPublishRequest,
    session: AsyncSession = Depends(get_session),
) -> AutoPublishResponse:
    """Trigger the auto-publish pipeline for a Google Doc.

    Tries to queue a Celery task. Falls back to synchronous execution
    if Celery is unavailable.
    """
    google_doc_url = payload.google_doc_url
    sheet_row = payload.sheet_row

    logger.info(
        "auto_publish_requested",
        google_doc_url=google_doc_url,
        sheet_row=sheet_row,
    )

    # Try Celery first
    try:
        from src.workers.tasks.auto_publish import auto_publish_task

        async_result = auto_publish_task.delay(
            google_doc_url=google_doc_url,
            sheet_row=sheet_row,
        )

        logger.info(
            "auto_publish_queued",
            celery_task_id=async_result.id,
            google_doc_url=google_doc_url,
        )

        return AutoPublishResponse(
            task_id=async_result.id,
            status="queued",
            message="Task queued for processing",
        )
    except Exception as celery_err:
        logger.warning(
            "celery_unavailable_falling_back_to_sync",
            error=str(celery_err),
        )

    # Fallback: synchronous execution
    task_id = str(uuid.uuid4())
    try:
        from src.services.worklist.auto_publish import AutoPublishService

        service = AutoPublishService(session)
        result = await service.process_google_doc(
            google_doc_url=google_doc_url,
            sheet_row=sheet_row,
        )

        return AutoPublishResponse(
            task_id=task_id,
            status="completed",
            message="Processed synchronously (Celery unavailable)",
            result=result,
        )
    except Exception as exc:
        logger.error(
            "auto_publish_sync_failed",
            error=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auto-publish failed: {exc}",
        ) from exc


@router.get(
    "/auto-publish/{task_id}/status",
    response_model=TaskStatusResponse,
)
async def get_auto_publish_status(task_id: str) -> TaskStatusResponse:
    """Poll the status of an auto-publish task."""

    # Try Celery result backend
    try:
        from src.workers.celery_app import celery_app

        async_result = celery_app.AsyncResult(task_id)

        if async_result.state == "PENDING":
            return TaskStatusResponse(
                task_id=task_id,
                status="pending",
            )
        elif async_result.state in ("STARTED", "RETRY"):
            return TaskStatusResponse(
                task_id=task_id,
                status="processing",
            )
        elif async_result.state == "SUCCESS":
            return TaskStatusResponse(
                task_id=task_id,
                status="completed",
                result=async_result.result,
            )
        elif async_result.state == "FAILURE":
            return TaskStatusResponse(
                task_id=task_id,
                status="failed",
                error=str(async_result.result),
            )
        else:
            return TaskStatusResponse(
                task_id=task_id,
                status="processing",
            )
    except Exception as exc:
        logger.warning(
            "celery_status_check_failed",
            task_id=task_id,
            error=str(exc),
        )
        return TaskStatusResponse(
            task_id=task_id,
            status="pending",
            error="Unable to check task status (Celery may be unavailable)",
        )


@router.post(
    "/cleanup",
    response_model=CleanupResponse,
)
async def cleanup_published_item(
    payload: CleanupRequest,
    session: AsyncSession = Depends(get_session),
) -> CleanupResponse:
    """Clean up large text fields from a published worklist item to free Supabase storage.

    Called by GAS after confirming a task has completed successfully.
    Only works on items with status 'published'.
    """
    worklist_item_id = payload.worklist_item_id

    logger.info(
        "cleanup_requested",
        worklist_item_id=worklist_item_id,
    )

    try:
        from src.services.worklist.auto_publish import AutoPublishService

        service = AutoPublishService(session)
        freed = await service.cleanup_published_item(worklist_item_id)

        return CleanupResponse(
            success=True,
            freed_bytes_estimate=freed,
            message=f"Cleaned up worklist item {worklist_item_id}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            "cleanup_failed",
            worklist_item_id=worklist_item_id,
            error=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {exc}",
        ) from exc
