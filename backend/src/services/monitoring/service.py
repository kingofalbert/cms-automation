"""Service utilities for publishing task monitoring."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.schemas.monitoring import ExecutionLogEntry, TaskFilters, TaskStatistics
from src.models import ExecutionLog, Provider, PublishTask, TaskStatus


class TaskMonitoringService:
    """Provide read-only access to publishing task metrics and logs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_tasks(
        self,
        filters: TaskFilters,
    ) -> tuple[list[PublishTask], int]:
        """Return filtered publishing tasks with total count."""
        conditions = []

        if filters.provider:
            provider = self._parse_provider(filters.provider)
            conditions.append(PublishTask.provider == provider)

        if filters.status:
            status_condition = self._build_status_filter(filters.status)
            if status_condition is not None:
                conditions.append(status_condition)

        stmt = (
            select(PublishTask)
            .options(selectinload(PublishTask.article))
            .order_by(PublishTask.created_at.desc())
        )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        total_stmt = select(func.count()).select_from(PublishTask)
        if conditions:
            total_stmt = total_stmt.where(and_(*conditions))

        result = await self.session.execute(
            stmt.offset(filters.offset).limit(filters.limit)
        )
        tasks = list(result.scalars().all())

        total_result = await self.session.execute(total_stmt)
        total = int(total_result.scalar_one())

        return tasks, total

    async def get_statistics(
        self,
        provider: str | None = None,
    ) -> TaskStatistics:
        """Calculate aggregate statistics for publishing tasks."""
        conditions = []

        if provider:
            provider_enum = self._parse_provider(provider)
            conditions.append(PublishTask.provider == provider_enum)

        total_expr = func.count(PublishTask.id)
        completed_expr = func.count().filter(PublishTask.status == TaskStatus.COMPLETED)
        failed_expr = func.count().filter(PublishTask.status == TaskStatus.FAILED)

        in_progress_expr = func.count().filter(
            PublishTask.status.in_(
                [
                    TaskStatus.PENDING,
                    TaskStatus.INITIALIZING,
                    TaskStatus.LOGGING_IN,
                    TaskStatus.CREATING_POST,
                    TaskStatus.UPLOADING_IMAGES,
                    TaskStatus.CONFIGURING_SEO,
                    TaskStatus.PUBLISHING,
                ]
            )
        )

        stmt = select(
            total_expr.label("total"),
            completed_expr.label("completed"),
            failed_expr.label("failed"),
            in_progress_expr.label("in_progress"),
        )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        row = result.one()

        return TaskStatistics(
            total=row.total or 0,
            completed=row.completed or 0,
            failed=row.failed or 0,
            in_progress=row.in_progress or 0,
        )

    async def get_task_by_identifier(self, identifier: str) -> PublishTask:
        """Fetch task by numeric ID or associated Celery task ID."""
        stmt = (
            select(PublishTask)
            .options(selectinload(PublishTask.article))
            .where(PublishTask.task_id == identifier)
        )
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()

        if task:
            return task

        if identifier.isdigit():
            stmt = (
                select(PublishTask)
                .options(selectinload(PublishTask.article))
                .where(PublishTask.id == int(identifier))
            )
            result = await self.session.execute(stmt)
            task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"Publish task {identifier} not found")

        return task

    async def get_task_logs(
        self,
        task_id: int,
        limit: int = 200,
        offset: int = 0,
    ) -> tuple[list[ExecutionLogEntry], int]:
        """Retrieve execution logs for a task."""
        stmt = (
            select(ExecutionLog)
            .where(ExecutionLog.task_id == task_id)
            .order_by(ExecutionLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        logs: Sequence[ExecutionLog] = result.scalars().all()

        count_stmt = select(func.count()).where(ExecutionLog.task_id == task_id)
        total_result = await self.session.execute(count_stmt)
        total = int(total_result.scalar_one())

        entries = [
            ExecutionLogEntry(
                id=log.id,
                task_id=log.task_id,
                created_at=log.created_at,
                log_level=log.log_level.value if log.log_level else None,
                step_name=log.step_name,
                message=log.message,
                action_type=log.action_type,
                action_target=log.action_target,
                action_result=log.action_result,
                screenshot_url=log.screenshot_url,
                details=log.details,
            )
            for log in logs
        ]

        return entries, total

    def _parse_provider(self, provider: str) -> Provider:
        try:
            return Provider(provider.lower())
        except ValueError as exc:
            raise ValueError(f"Invalid provider '{provider}'") from exc

    def _build_status_filter(self, status_value: str):
        normalized = status_value.lower()
        if normalized == "completed":
            return PublishTask.status == TaskStatus.COMPLETED
        if normalized == "failed":
            return PublishTask.status == TaskStatus.FAILED
        if normalized in {"pending", "queued"}:
            return PublishTask.status == TaskStatus.PENDING
        if normalized == "in_progress":
            return PublishTask.status.in_(
                [
                    TaskStatus.INITIALIZING,
                    TaskStatus.LOGGING_IN,
                    TaskStatus.CREATING_POST,
                    TaskStatus.UPLOADING_IMAGES,
                    TaskStatus.CONFIGURING_SEO,
                    TaskStatus.PUBLISHING,
                ]
            )
        if normalized in {status.value for status in TaskStatus}:
            return PublishTask.status == TaskStatus(normalized)
        return None
