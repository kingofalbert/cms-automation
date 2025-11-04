"""Schemas for worklist API."""

from datetime import datetime
from typing import Any

from pydantic import Field

from src.api.schemas.base import BaseSchema


class WorklistItemResponse(BaseSchema):
    """Serialized worklist item."""

    id: int = Field(..., description="Worklist item identifier")
    drive_file_id: str = Field(..., description="Google Drive file ID")
    title: str = Field(..., description="Document title")
    status: str = Field(..., description="Worklist status")
    author: str | None = Field(default=None, description="Document author")
    article_id: int | None = Field(
        default=None, description="Linked article ID if available"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata captured during sync"
    )
    notes: list[dict[str, Any]] = Field(
        default_factory=list, description="Reviewer notes and history"
    )
    synced_at: datetime = Field(..., description="Last sync timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class WorklistStatisticsResponse(BaseSchema):
    """Aggregated worklist statistics."""

    total: int = Field(..., ge=0, description="Total items in worklist")
    breakdown: dict[str, int] = Field(
        default_factory=dict, description="Counts per status"
    )


class WorklistSyncStatusResponse(BaseSchema):
    """Synchronization status payload."""

    last_synced_at: datetime | None = Field(
        default=None, description="Timestamp of most recent sync"
    )
    total_items: int = Field(..., ge=0, description="Total worklist items")


class WorklistStatusUpdateRequest(BaseSchema):
    """Request payload to update worklist status."""

    status: str = Field(..., description="Target worklist status")
    note: dict[str, Any] | None = Field(
        default=None, description="Reviewer note to append"
    )


class WorklistSyncTriggerResponse(BaseSchema):
    """Response payload when triggering a sync."""

    status: str = Field(..., description="Sync queue status")
    message: str = Field(..., description="Status message")
    queued_at: str = Field(..., description="ISO timestamp when sync was queued")
    summary: dict[str, Any] | None = Field(
        default=None, description="Synchronization summary details"
    )
    error: str | None = Field(
        default=None, description="Error message when sync fails"
    )
