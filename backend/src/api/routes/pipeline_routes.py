"""Pipeline automation endpoints for Google Apps Script integration."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db_config, get_session
from src.config.logging import get_logger
from src.models.pipeline_task import PipelineTask

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

    Creates a DB-tracked task and runs the pipeline in a background
    asyncio task.  Returns 202 immediately.
    """
    google_doc_url = payload.google_doc_url
    sheet_row = payload.sheet_row

    logger.info(
        "auto_publish_requested",
        google_doc_url=google_doc_url,
        sheet_row=sheet_row,
    )

    # Persist task record in DB so status survives instance restarts
    task_id = str(uuid.uuid4())
    task = PipelineTask(
        id=task_id,
        task_type="auto_publish",
        status="processing",
        input={"google_doc_url": google_doc_url, "sheet_row": sheet_row},
    )
    session.add(task)
    await session.commit()

    async def _run_pipeline(tid: str, doc_url: str, row: int | None) -> None:
        """Execute the auto-publish pipeline in the background."""
        db_config = get_db_config()
        try:
            from src.services.worklist.auto_publish import AutoPublishService

            service = AutoPublishService(session=None)  # type: ignore[arg-type]
            result = await service.process_google_doc(
                google_doc_url=doc_url,
                sheet_row=row,
            )
            async with db_config.session() as s:
                t = await s.get(PipelineTask, tid)
                if t:
                    t.status = "completed"
                    t.result = result
                    t.completed_at = datetime.now(UTC)
                    await s.commit()
            logger.info("auto_publish_background_completed", task_id=tid)
        except Exception as exc:
            logger.error(
                "auto_publish_background_failed",
                task_id=tid,
                error=str(exc),
                exc_info=True,
            )
            try:
                async with db_config.session() as s:
                    t = await s.get(PipelineTask, tid)
                    if t:
                        t.status = "failed"
                        t.error = str(exc) or repr(exc) or type(exc).__name__
                        t.completed_at = datetime.now(UTC)
                        await s.commit()
            except Exception:
                logger.error("pipeline_task_status_update_failed", task_id=tid, exc_info=True)

    asyncio.create_task(_run_pipeline(task_id, google_doc_url, sheet_row))

    logger.info(
        "auto_publish_background_task_created",
        task_id=task_id,
        google_doc_url=google_doc_url,
    )

    return AutoPublishResponse(
        task_id=task_id,
        status="queued",
        message="Task queued for background processing",
    )


@router.get(
    "/auto-publish/{task_id}/status",
    response_model=TaskStatusResponse,
)
async def get_auto_publish_status(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> TaskStatusResponse:
    """Poll the status of an auto-publish task.

    Returns a terminal "expired" status for unknown task IDs so that
    external callers (e.g. GAS) can stop polling gracefully instead of
    retrying indefinitely on 404.
    """
    task = await session.get(PipelineTask, task_id)
    if not task:
        return TaskStatusResponse(
            task_id=task_id,
            status="expired",
            error="Task not found or expired",
        )

    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        result=task.result,
        error=task.error,
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
