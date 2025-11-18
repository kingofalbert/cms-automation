"""Schemas for worklist API."""

from datetime import datetime
from typing import Any

from pydantic import Field

from src.api.schemas.base import BaseSchema
from src.api.schemas.article import ArticleImageResponse


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


class WorklistStatusHistoryEntry(BaseSchema):
    """Serialized status history timeline for linked article."""

    old_status: str | None = Field(default=None, description="Previous article status")
    new_status: str = Field(..., description="New article status")
    changed_by: str | None = Field(default=None, description="Actor that triggered the change")
    change_reason: str | None = Field(default=None, description="Why the status changed")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Timestamp of the transition")


class WorklistItemDetailResponse(WorklistItemResponse):
    """Detailed worklist payload for the drawer / review page."""

    content: str = Field(..., description="Full document body")
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    meta_description: str | None = Field(default=None)
    seo_keywords: list[str] = Field(default_factory=list)
    article_status: str | None = Field(default=None, description="Current linked article status")
    article_status_history: list[WorklistStatusHistoryEntry] = Field(
        default_factory=list,
        description="Timeline of article status transitions",
    )
    drive_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Raw Google Drive metadata snapshot"
    )
    proofreading_issues: list[dict[str, Any]] = Field(
        default_factory=list, description="Proofreading issues with decision status"
    )
    proofreading_stats: dict[str, int] | None = Field(
        default=None, description="Statistics about proofreading issues"
    )

    # Phase 7: Article parsing fields (HOTFIX-PARSE-004)
    title_main: str | None = Field(default=None, description="Parsed main title")
    title_prefix: str | None = Field(default=None, description="Parsed title prefix")
    title_suffix: str | None = Field(default=None, description="Parsed title suffix")
    author_name: str | None = Field(default=None, description="Parsed author name")
    author_line: str | None = Field(default=None, description="Full author line text")
    parsing_confirmed: bool = Field(default=False, description="Whether parsing has been confirmed")
    parsing_confirmed_at: datetime | None = Field(default=None, description="When parsing was confirmed")

    # Phase 7: Article images
    article_images: list[ArticleImageResponse] = Field(
        default_factory=list,
        description="Images extracted from article during parsing"
    )


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
