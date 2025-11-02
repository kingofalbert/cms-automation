"""Worklist API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import (
    PaginatedResponse,
    WorklistItemResponse,
    WorklistStatisticsResponse,
    WorklistStatusUpdateRequest,
    WorklistSyncStatusResponse,
    WorklistSyncTriggerResponse,
)
from src.config.database import get_session
from src.config.logging import get_logger
from src.models import WorklistItem
from src.services.worklist import WorklistService

logger = get_logger(__name__)
router = APIRouter(prefix="/worklist", tags=["Worklist"])

WorklistListResponse = PaginatedResponse[WorklistItemResponse]


@router.get("", response_model=WorklistListResponse)
async def list_worklist_items(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> WorklistListResponse:
    """List worklist items with optional status filtering."""
    service = WorklistService(session)
    try:
        items, total = await service.list_items(
            status=status_filter,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    serialized = [_serialize_item(item) for item in items]
    page = (offset // limit) + 1

    logger.debug(
        "worklist_items_listed",
        count=len(serialized),
        total=total,
        status=status_filter,
    )

    return WorklistListResponse.create(
        items=serialized,
        total=total,
        page=page,
        page_size=limit,
    )


@router.get("/statistics", response_model=WorklistStatisticsResponse)
async def get_worklist_statistics(
    session: AsyncSession = Depends(get_session),
) -> WorklistStatisticsResponse:
    """Return breakdown of worklist statuses."""
    service = WorklistService(session)
    stats = await service.get_statistics()
    total = stats.pop("total", sum(stats.values()))
    return WorklistStatisticsResponse(total=total, breakdown=stats)


@router.get("/sync-status", response_model=WorklistSyncStatusResponse)
async def get_sync_status(
    session: AsyncSession = Depends(get_session),
) -> WorklistSyncStatusResponse:
    """Return latest sync metadata."""
    service = WorklistService(session)
    status_payload = await service.get_sync_status()
    return WorklistSyncStatusResponse(**status_payload)


@router.post("/sync", response_model=WorklistSyncTriggerResponse)
async def trigger_worklist_sync(
    session: AsyncSession = Depends(get_session),
) -> WorklistSyncTriggerResponse:
    """Trigger asynchronous sync with Google Drive."""
    service = WorklistService(session)
    result = await service.trigger_sync()
    return WorklistSyncTriggerResponse(**result)


@router.post("/{item_id}/status", response_model=WorklistItemResponse)
async def update_worklist_status(
    item_id: int,
    payload: WorklistStatusUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> WorklistItemResponse:
    """Update status of a worklist item."""
    service = WorklistService(session)
    try:
        updated = await service.update_status(
            item_id=item_id,
            status=payload.status,
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    logger.info(
        "worklist_status_updated",
        item_id=item_id,
        status=updated.status.value,
    )
    return _serialize_item(updated)


@router.post("/{item_id}/publish", response_model=WorklistItemResponse)
async def publish_worklist_item(
    item_id: int,
    session: AsyncSession = Depends(get_session),
) -> WorklistItemResponse:
    """Placeholder endpoint to initiate publishing from worklist."""
    service = WorklistService(session)
    try:
        updated = await service.update_status(
            item_id=item_id,
            status="ready_to_publish",
            note={"action": "publish", "message": "Publishing triggered from worklist"},
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    logger.info(
        "worklist_publish_triggered",
        item_id=item_id,
        status=updated.status.value,
    )
    return _serialize_item(updated)


def _serialize_item(item: WorklistItem) -> WorklistItemResponse:
    """Convert ORM worklist item to schema."""
    return WorklistItemResponse(
        id=item.id,
        drive_file_id=item.drive_file_id,
        title=item.title,
        status=item.status.value if hasattr(item.status, "value") else item.status,
        author=item.author,
        article_id=item.article_id,
        metadata=item.drive_metadata or {},
        notes=item.notes or [],
        synced_at=item.synced_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )
