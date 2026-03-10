"""Pipeline automation endpoints for Google Apps Script integration."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db_config, get_session
from src.config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Pipeline Automation"])

# ---------------------------------------------------------------------------
# In-memory task tracking for the async fallback path (when Celery is down).
# Maps task_id -> {"status": ..., "result": ..., "error": ...}
# Entries are kept until the next deployment (Cloud Run instance recycle).
# ---------------------------------------------------------------------------
_task_results: dict[str, dict[str, Any]] = {}


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

    # Try Celery first, with a hard 3s wall-clock timeout.
    # Even with socket_connect_timeout=2, nested retries in kombu/celery
    # could compound.  This ensures we fall back to asyncio quickly.
    try:
        from src.workers.tasks.auto_publish import auto_publish_task

        async_result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: auto_publish_task.delay(
                    google_doc_url=google_doc_url,
                    sheet_row=sheet_row,
                ),
            ),
            timeout=3.0,
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

    # Fallback: run pipeline in a background asyncio.Task so the HTTP
    # response returns immediately (202) instead of blocking for 240s+.
    task_id = str(uuid.uuid4())
    _task_results[task_id] = {"status": "processing"}

    async def _run_pipeline(tid: str, doc_url: str, row: int | None) -> None:
        """Execute the auto-publish pipeline in the background.

        process_google_doc() manages its own short-lived DB sessions
        for each phase, so we don't need to hold a long-lived session
        here.  The service instance only needs settings, not a session.
        """
        try:
            from src.services.worklist.auto_publish import AutoPublishService

            # AutoPublishService.process_google_doc() now manages its own
            # sessions internally.  Pass a dummy session=None; the method
            # ignores self.session entirely.
            service = AutoPublishService(session=None)  # type: ignore[arg-type]
            result = await service.process_google_doc(
                google_doc_url=doc_url,
                sheet_row=row,
            )
            _task_results[tid] = {"status": "completed", "result": result}
            logger.info("auto_publish_background_completed", task_id=tid)
        except Exception as exc:
            logger.error(
                "auto_publish_background_failed",
                task_id=tid,
                error=str(exc),
                exc_info=True,
            )
            _task_results[tid] = {
                "status": "failed",
                "error": str(exc) or repr(exc) or type(exc).__name__,
            }

    asyncio.create_task(_run_pipeline(task_id, google_doc_url, sheet_row))

    logger.info(
        "auto_publish_background_task_created",
        task_id=task_id,
        google_doc_url=google_doc_url,
    )

    return AutoPublishResponse(
        task_id=task_id,
        status="queued",
        message="Task queued for background processing (Celery unavailable)",
    )


@router.get(
    "/auto-publish/{task_id}/status",
    response_model=TaskStatusResponse,
)
async def get_auto_publish_status(task_id: str) -> TaskStatusResponse:
    """Poll the status of an auto-publish task."""

    # 1. Check in-memory results first (background asyncio.Task fallback)
    if task_id in _task_results:
        entry = _task_results[task_id]
        return TaskStatusResponse(
            task_id=task_id,
            status=entry.get("status", "processing"),
            result=entry.get("result"),
            error=entry.get("error"),
        )

    # 2. Try Celery result backend
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
