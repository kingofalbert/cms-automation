"""Analytics service for publishing metrics and provider comparisons."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Provider, PublishTask, TaskStatus, UploadedFile


class AnalyticsService:
    """Provides aggregated analytics over publishing tasks and assets."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def provider_comparison(
        self,
        time_range: str = "30d",
    ) -> list[dict[str, Any]]:
        """Aggregate metrics per provider."""
        start = self._resolve_time_range(time_range)
        conditions = []
        if start is not None:
            conditions.append(PublishTask.created_at >= start)

        stmt = select(
            PublishTask.provider,
            func.count(PublishTask.id).label("total"),
            func.sum(
                case((PublishTask.status == TaskStatus.COMPLETED, 1), else_=0)
            ).label("completed"),
            func.sum(
                case((PublishTask.status == TaskStatus.FAILED, 1), else_=0)
            ).label("failed"),
            func.avg(PublishTask.duration_seconds).label("avg_duration"),
            func.avg(PublishTask.cost_usd).label("avg_cost"),
            func.sum(PublishTask.cost_usd).label("total_cost"),
        ).group_by(PublishTask.provider)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        rows = result.all()

        metrics: list[dict[str, Any]] = []
        for row in rows:
            total = row.total or 0
            completed = row.completed or 0
            failed = row.failed or 0
            in_progress = max(total - completed - failed, 0)
            success_rate = (completed / total * 100) if total else 0.0

            metrics.append(
                {
                    "provider": row.provider.value if isinstance(row.provider, Provider) else row.provider,
                    "total_tasks": total,
                    "completed_tasks": completed,
                    "failed_tasks": failed,
                    "in_progress_tasks": in_progress,
                    "success_rate": round(success_rate, 2),
                    "avg_duration_seconds": float(row.avg_duration) if row.avg_duration is not None else None,
                    "avg_cost_usd": float(row.avg_cost) if row.avg_cost is not None else None,
                    "total_cost_usd": float(row.total_cost) if row.total_cost is not None else 0.0,
                }
            )

        return metrics

    async def cost_usage(
        self,
        time_range: str = "30d",
    ) -> list[dict[str, Any]]:
        """Summarize cost usage by day."""
        start = self._resolve_time_range(time_range)
        conditions = [PublishTask.cost_usd.isnot(None)]
        if start is not None:
            conditions.append(PublishTask.created_at >= start)

        date_bucket = func.date_trunc("day", PublishTask.created_at).label("bucket")
        stmt = (
            select(
                date_bucket,
                func.sum(PublishTask.cost_usd).label("total_cost"),
                func.avg(PublishTask.cost_usd).label("avg_cost"),
            )
            .where(and_(*conditions))
            .group_by(date_bucket)
            .order_by(date_bucket)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        usage: list[dict[str, Any]] = []
        for row in rows:
            bucket_ts: datetime | None = row.bucket
            usage.append(
                {
                    "date": bucket_ts.date().isoformat() if bucket_ts else None,
                    "total_cost_usd": float(row.total_cost) if row.total_cost is not None else 0.0,
                    "avg_cost_usd": float(row.avg_cost) if row.avg_cost is not None else 0.0,
                }
            )

        return usage

    async def storage_usage(self) -> list[dict[str, Any]]:
        """Aggregate storage consumption by file type."""
        stmt = (
            select(
                UploadedFile.file_type.label("file_type"),
                func.count(UploadedFile.id).label("count"),
                func.sum(UploadedFile.file_size).label("total_bytes"),
            )
            .where(UploadedFile.deleted_at.is_(None))
            .group_by(UploadedFile.file_type)
            .order_by(UploadedFile.file_type)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        usage: list[dict[str, Any]] = []
        for row in rows:
            usage.append(
                {
                    "file_type": row.file_type,
                    "file_count": row.count or 0,
                    "total_bytes": int(row.total_bytes or 0),
                    "total_megabytes": round((row.total_bytes or 0) / (1024 * 1024), 2),
                }
            )

        return usage

    async def recommendations(
        self,
        time_range: str = "30d",
    ) -> dict[str, Any]:
        """Generate heuristic recommendations based on provider performance."""
        metrics = await self.provider_comparison(time_range=time_range)
        if not metrics:
            return {"recommendations": [], "summary": "No publishing data available."}

        # Determine best and worst performers
        best = max(metrics, key=lambda m: (m["success_rate"], -m["avg_cost_usd"] if m["avg_cost_usd"] else 0))
        worst = min(metrics, key=lambda m: m["success_rate"])

        recommendations: list[str] = []
        summary_parts: list[str] = []

        summary_parts.append(
            f"Provider {best['provider']} leads with a {best['success_rate']}% success rate."
        )

        if best["avg_cost_usd"] is not None:
            summary_parts.append(
                f"Average cost is ${best['avg_cost_usd']:.2f} per task for {best['provider']}."
            )

        if worst["success_rate"] < 70:
            recommendations.append(
                f"Investigate failures for {worst['provider']} (success rate {worst['success_rate']}%)."
            )

        high_cost_providers = [
            m for m in metrics if (m["avg_cost_usd"] or 0) > 5 and m["success_rate"] < 90
        ]
        for metric in high_cost_providers:
            recommendations.append(
                f"Consider optimizing costs for {metric['provider']} (avg ${metric['avg_cost_usd']:.2f} per task)."
            )

        if not recommendations:
            recommendations.append("Providers performing within expected thresholds. Continue monitoring.")

        return {
            "summary": " ".join(summary_parts),
            "recommendations": recommendations,
            "metrics": metrics,
        }

    def _resolve_time_range(self, time_range: str) -> datetime | None:
        """Map time range string to starting datetime."""
        if not time_range or time_range == "all":
            return None

        normalized = time_range.lower()
        mapping = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
        }
        days = mapping.get(normalized)
        if days is None:
            raise ValueError(f"Unsupported time range '{time_range}'.")

        return datetime.utcnow() - timedelta(days=days)
