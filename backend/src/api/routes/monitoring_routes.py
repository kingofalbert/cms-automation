"""Monitoring endpoints for publishing tasks."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import (
    ExecutionLogEntry,
    PaginatedResponse,
    PublishTaskResponse,
    TaskFilters,
    TaskStatistics,
)
from src.api.routes.publish_routes import _serialize_publish_task
from src.config.database import get_session
from src.config.logging import get_logger
from src.services.monitoring import TaskMonitoringService

logger = get_logger(__name__)
router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

TaskListResponse = PaginatedResponse[PublishTaskResponse]
LogListResponse = PaginatedResponse[ExecutionLogEntry]


@router.get("/tasks", response_model=TaskListResponse)
async def list_monitoring_tasks(
    status_filter: str | None = Query(default=None, alias="status"),
    provider_filter: str | None = Query(default=None, alias="provider"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> TaskListResponse:
    """List publishing tasks with advanced monitoring filters."""
    service = TaskMonitoringService(session)
    filters = TaskFilters(
        status=status_filter,
        provider=provider_filter,
        limit=limit,
        offset=offset,
    )
    tasks, total = await service.list_tasks(filters)

    items = [_serialize_publish_task(task) for task in tasks]
    page = (offset // limit) + 1 if limit else 1

    logger.debug(
        "monitoring_tasks_listed",
        count=len(items),
        total=total,
        status=status_filter,
        provider=provider_filter,
    )

    return TaskListResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=limit,
    )


@router.get("/statistics", response_model=TaskStatistics)
async def get_task_statistics(
    provider_filter: str | None = Query(default=None, alias="provider"),
    session: AsyncSession = Depends(get_session),
) -> TaskStatistics:
    """Return aggregate publishing statistics."""
    service = TaskMonitoringService(session)
    try:
        stats = await service.get_statistics(provider_filter)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    logger.debug(
        "monitoring_statistics_generated",
        provider=provider_filter,
        totals=stats.model_dump(),
    )

    return stats


@router.get("/tasks/{task_identifier}/logs", response_model=LogListResponse)
async def get_task_logs(
    task_identifier: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> LogListResponse:
    """Retrieve execution logs for a publishing task."""
    service = TaskMonitoringService(session)

    try:
        task = await service.get_task_by_identifier(task_identifier)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    entries, total = await service.get_task_logs(task.id, limit=limit, offset=offset)

    page = (offset // limit) + 1 if limit else 1

    logger.debug(
        "monitoring_task_logs_retrieved",
        task_id=task.id,
        celery_task_id=task.task_id,
        count=len(entries),
    )

    return LogListResponse.create(
        items=entries,
        total=total,
        page=page,
        page_size=limit,
    )
