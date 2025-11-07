"""Worklist service for Drive-synced documents."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import defer, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import get_logger
from src.models import (
    Article,
    ArticleStatus,
    ArticleStatusHistory,
    WorklistItem,
    WorklistStatus,
)
from src.services.google_drive import GoogleDriveSyncService

logger = get_logger(__name__)


class WorklistService:
    """Provide worklist querying, status management, and sync helpers."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_items(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[WorklistItem], int]:
        """List worklist items filtered by status with pagination."""
        query = (
            select(WorklistItem)
            .options(defer(WorklistItem.content))
            .order_by(WorklistItem.updated_at.desc())
        )
        count_query = select(func.count()).select_from(WorklistItem)

        if status:
            try:
                status_enum = WorklistStatus(status)
            except ValueError:
                raise ValueError(f"Invalid worklist status '{status}'.") from None

            query = query.where(WorklistItem.status == status_enum)
            count_query = count_query.where(WorklistItem.status == status_enum)

        result = await self.session.execute(query.offset(offset).limit(limit))
        items = list(result.scalars().all())

        total = await self.session.execute(count_query)
        total_count = int(total.scalar_one())

        return items, total_count

    async def get_statistics(self) -> dict[str, int]:
        """Return counts per status for worklist dashboard."""
        stmt = (
            select(
                WorklistItem.status,
                func.count(WorklistItem.id),
            )
            .group_by(WorklistItem.status)
            .order_by(WorklistItem.status)
        )

        result = await self.session.execute(stmt)
        stats = {status.value: count for status, count in result.all()}
        stats["total"] = sum(stats.values())
        return stats

    async def get_sync_status(self) -> dict[str, Any]:
        """Provide basic sync status information."""
        latest_stmt = (
            select(WorklistItem.synced_at)
            .order_by(WorklistItem.synced_at.desc())
            .limit(1)
        )
        latest_result = await self.session.execute(latest_stmt)
        latest_synced = latest_result.scalar_one_or_none()

        total_stmt = select(func.count()).select_from(WorklistItem)
        total = await self.session.execute(total_stmt)

        return {
            "last_synced_at": latest_synced,
            "total_items": int(total.scalar_one()),
        }

    async def update_status(
        self,
        item_id: int,
        status: str,
        note: dict[str, Any] | None = None,
    ) -> WorklistItem:
        """Update worklist item status and optionally append note."""
        item = await self.session.get(WorklistItem, item_id)
        if not item:
            raise ValueError(f"Worklist item {item_id} not found.")

        try:
            status_enum = WorklistStatus(status)
        except ValueError:
            raise ValueError(f"Invalid worklist status '{status}'.") from None

        item.mark_status(status_enum)
        if note:
            item.add_note({**note, "timestamp": datetime.utcnow().isoformat()})

        await self._sync_article_status(item, status_enum, note)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def get_item(self, item_id: int) -> WorklistItem:
        """Fetch a single worklist item with related article/status history."""
        stmt = (
            select(WorklistItem)
            .where(WorklistItem.id == item_id)
            .options(
                selectinload(WorklistItem.article).selectinload(
                    Article.status_history
                )
            )
        )
        result = await self.session.execute(stmt)
        item = result.scalars().first()
        if not item:
            raise ValueError(f"Worklist item {item_id} not found.")
        return item

    async def link_article(self, item_id: int, article_id: int) -> WorklistItem:
        """Associate worklist item with existing article."""
        item = await self.session.get(WorklistItem, item_id)
        if not item:
            raise ValueError(f"Worklist item {item_id} not found.")

        article = await self.session.get(Article, article_id)
        if not article:
            raise ValueError(f"Article {article_id} not found.")

        item.article_id = article_id
        item.synced_at = datetime.utcnow()
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def trigger_sync(self) -> dict[str, Any]:
        """Synchronously trigger Google Drive sync."""
        sync_service = GoogleDriveSyncService(self.session)
        try:
            summary = await sync_service.sync_worklist()
            return {
                "status": "completed",
                "message": "Worklist synchronization finished.",
                "queued_at": datetime.utcnow().isoformat(),
                "summary": summary,
            }
        except Exception as exc:
            logger.error("worklist_sync_failed", error=str(exc), exc_info=True)
            return {
                "status": "error",
                "message": "Worklist synchronization failed.",
                "queued_at": datetime.utcnow().isoformat(),
                "error": str(exc),
            }

    async def _sync_article_status(
        self,
        item: WorklistItem,
        worklist_status: WorklistStatus,
        note: dict[str, Any] | None = None,
    ) -> None:
        """Update linked article status + history to mirror worklist state."""
        if not item.article_id:
            return

        article = await self.session.get(Article, item.article_id)
        if not article:
            return

        target_status = WORKLIST_TO_ARTICLE_STATUS.get(worklist_status)
        if not target_status or article.status == target_status:
            return

        note_payload = note or {}
        history = ArticleStatusHistory(
            article_id=article.id,
            old_status=article.status.value if article.status else None,
            new_status=target_status.value,
            changed_by="system",
            change_reason=note_payload.get("message") or "worklist_status_update",
            metadata=note_payload,
        )
        article.status = target_status
        self.session.add_all([article, history])
WORKLIST_TO_ARTICLE_STATUS: dict[WorklistStatus, ArticleStatus] = {
    WorklistStatus.PENDING: ArticleStatus.IMPORTED,
    WorklistStatus.PROOFREADING: ArticleStatus.IN_REVIEW,
    WorklistStatus.UNDER_REVIEW: ArticleStatus.IN_REVIEW,
    WorklistStatus.READY_TO_PUBLISH: ArticleStatus.READY_TO_PUBLISH,
    WorklistStatus.PUBLISHING: ArticleStatus.PUBLISHING,
    WorklistStatus.PUBLISHED: ArticleStatus.PUBLISHED,
    WorklistStatus.FAILED: ArticleStatus.FAILED,
}
