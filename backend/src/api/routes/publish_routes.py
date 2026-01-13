"""Publishing workflow API routes."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ClauseElement

from src.api.schemas.publishing import (
    PublishRequest,
    PublishResult,
    PublishTaskResponse,
    Screenshot,
)
from src.config.database import get_session
from src.config.logging import get_logger
from src.models import Article, Provider, PublishTask, TaskStatus

logger = get_logger(__name__)
router = APIRouter(prefix="/publish", tags=["Publishing"])


@router.post(
    "/submit/{article_id}",
    response_model=PublishResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_publish_task(
    article_id: int,
    request: PublishRequest,
    session: AsyncSession = Depends(get_session),
) -> PublishResult:
    """Submit a new publishing task for the specified article."""
    provider = _parse_provider(request.provider)

    article = await session.get(Article, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )

    task = PublishTask(
        article_id=article_id,
        provider=provider,
        status=TaskStatus.PENDING,
        current_step=TaskStatus.PENDING.value,
        progress=0,
        completed_steps=0,
    )

    session.add(task)

    try:
        await session.flush()

        # Try Celery first, fallback to sync execution if broker unavailable
        celery_task_id = None
        use_sync = False

        try:
            from src.workers.tasks.publishing import publish_article_task

            celery_task = publish_article_task.delay(
                publish_task_id=task.id,
                article_id=article_id,
                provider=provider.value,
                options=request.options.model_dump(mode="json", exclude_none=True),
            )
            celery_task_id = celery_task.id
            task.task_id = celery_task_id
            logger.info(
                "publish_task_submitted_celery",
                task_id=task.id,
                article_id=article_id,
                provider=provider.value,
                celery_task_id=celery_task_id,
            )
        except Exception as celery_exc:
            # Celery broker unavailable, fallback to sync execution
            logger.warning(
                "celery_unavailable_fallback_sync",
                task_id=task.id,
                article_id=article_id,
                error=str(celery_exc),
            )
            use_sync = True
            task.task_id = f"sync-{task.id}"

        session.add(task)
        await session.commit()

        # If Celery failed, execute synchronously
        if use_sync:
            from src.services.publishing import PublishingOrchestrator

            logger.info(
                "publish_task_executing_sync",
                task_id=task.id,
                article_id=article_id,
                provider=provider.value,
            )

            orchestrator = PublishingOrchestrator()
            try:
                result = await orchestrator.publish_article(
                    publish_task_id=task.id,
                    article_id=article_id,
                    provider=provider,
                    options=request.options.model_dump(mode="json", exclude_none=True),
                )
                logger.info(
                    "publish_task_completed_sync",
                    task_id=task.id,
                    article_id=article_id,
                    result=result.get("success"),
                )
                return PublishResult(
                    task_id=task.task_id,
                    status="completed",
                    message="Publishing completed successfully (sync mode).",
                )
            except Exception as sync_exc:
                logger.error(
                    "publish_task_failed_sync",
                    task_id=task.id,
                    article_id=article_id,
                    error=str(sync_exc),
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Publishing failed: {str(sync_exc)[:200]}",
                ) from sync_exc

        return PublishResult(
            task_id=celery_task_id,
            status=task.status.value,
            message="Publishing task submitted successfully.",
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - propagate as HTTP error
        await session.rollback()
        logger.error(
            "publish_task_submission_failed",
            article_id=article_id,
            provider=request.provider,
            error=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit publishing task.",
        ) from exc


@router.get("/tasks/{task_id}/status", response_model=PublishTaskResponse)
async def get_publish_task_status(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> PublishTaskResponse:
    """Get the status of a specific publishing task."""
    task = await _fetch_publish_task(session, task_id)
    return _serialize_publish_task(task)


@router.get("/tasks", response_model=dict)
async def list_publish_tasks(
    status_filter: str | None = Query(default=None, alias="status"),
    provider_filter: str | None = Query(default=None, alias="provider"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """List publishing tasks with optional filters and pagination."""
    provider = _parse_provider(provider_filter) if provider_filter else None
    task_status = _parse_status(status_filter) if status_filter else None

    filters = _build_filters(provider, task_status)

    base_query = (
        select(PublishTask)
        .options(selectinload(PublishTask.article))
        .order_by(PublishTask.created_at.desc())
    )
    if filters is not None:
        base_query = base_query.where(filters)

    result = await session.execute(
        base_query.offset(offset).limit(limit)
    )
    tasks: Sequence[PublishTask] = result.scalars().all()

    count_query = select(func.count()).select_from(PublishTask)
    if filters is not None:
        count_query = count_query.where(filters)
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    items = [
        _serialize_publish_task(task).model_dump(mode="json")
        for task in tasks
    ]

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post(
    "/tasks/{task_id}/retry",
    response_model=PublishResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_publish_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> PublishResult:
    """Retry a failed publishing task."""
    task = await _fetch_publish_task(session, task_id)

    if not task.can_retry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot be retried.",
        )

    try:
        task.increment_retry()

        # Lazy import to avoid circular dependency
        from src.workers.tasks.publishing import retry_publish_article_task

        celery_task = retry_publish_article_task.delay(
            publish_task_id=task.id,
            article_id=task.article_id,
            provider=task.provider.value,
        )

        task.task_id = celery_task.id
        session.add(task)

        await session.commit()

        logger.info(
            "publish_task_retry_started",
            task_id=task.id,
            article_id=task.article_id,
            retry_count=task.retry_count,
            celery_task_id=celery_task.id,
        )

        return PublishResult(
            task_id=celery_task.id,
            status=task.status.value,
            message="Publishing task retry started.",
        )
    except Exception as exc:  # noqa: BLE001 - propagate as HTTP error
        await session.rollback()
        logger.error(
            "publish_task_retry_failed",
            task_id=task.id,
            error=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry publishing task.",
        ) from exc


async def _fetch_publish_task(session: AsyncSession, identifier: str) -> PublishTask:
    """Fetch a publish task using Celery task ID or database ID."""
    query = (
        select(PublishTask)
        .options(selectinload(PublishTask.article))
        .where(PublishTask.task_id == identifier)
    )

    result = await session.execute(query)
    task = result.scalar_one_or_none()

    if not task and identifier.isdigit():
        fallback_query = (
            select(PublishTask)
            .options(selectinload(PublishTask.article))
            .where(PublishTask.id == int(identifier))
        )
        fallback_result = await session.execute(fallback_query)
        task = fallback_result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Publish task {identifier} not found.",
        )

    return task


def _parse_provider(provider: str | None) -> Provider | None:
    """Parse provider string into Provider enum."""
    if provider is None:
        return None

    try:
        return Provider(provider.lower())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider '{provider}'.",
        ) from exc


def _parse_status(status_value: str | None) -> TaskStatus | None:
    """Parse status string into TaskStatus enum."""
    if status_value is None:
        return None

    try:
        return TaskStatus(status_value.lower())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{status_value}'.",
        ) from exc


def _build_filters(
    provider: Provider | None, status: TaskStatus | None
) -> ClauseElement | None:
    """Build SQLAlchemy filters for querying tasks."""
    conditions: list = []

    if provider is not None:
        conditions.append(PublishTask.provider == provider)

    if status is not None:
        conditions.append(PublishTask.status == status)

    if not conditions:
        return None

    return and_(*conditions)


def _serialize_publish_task(task: PublishTask) -> PublishTaskResponse:
    """Convert ORM publish task into API schema."""
    duration = task.duration_seconds
    if duration is None and task.started_at and not task.is_complete:
        duration = int((datetime.utcnow() - task.started_at).total_seconds())

    screenshots = _serialize_screenshots(task.screenshots or [])

    return PublishTaskResponse(
        id=task.id,
        article_id=task.article_id,
        article_title=task.article_title,
        provider=task.provider.value,
        status=task.status.value,
        progress=task.progress,
        current_step=task.current_step,
        total_steps=task.total_steps,
        completed_steps=task.completed_steps,
        screenshots=screenshots,
        error_message=task.error_message,
        started_at=task.started_at,
        completed_at=task.completed_at,
        duration=duration,
        cost=task.cost_usd,
    )


def _serialize_screenshots(screenshots: Iterable[dict]) -> list[Screenshot]:
    """Normalize screenshot metadata."""
    serialized: list[Screenshot] = []

    for item in screenshots:
        if not isinstance(item, dict):
            continue

        image_url = item.get("image_url") or item.get("url")
        timestamp = item.get("timestamp")
        step = item.get("step")

        if not image_url or not timestamp or not step:
            continue

        serialized.append(
            Screenshot(
                step=step,
                timestamp=timestamp,
                image_url=image_url,
                description=item.get("description"),
            )
        )

    return serialized
