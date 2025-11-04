"""Analytics models for provider performance metrics."""

from datetime import date, datetime

from sqlalchemy import Date, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.publish import Provider


class ProviderMetrics(Base):
    """Aggregated provider performance metrics (partitioned by date)."""

    __tablename__ = "provider_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[Provider] = mapped_column(
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Metric date (UTC). Partition key.",
    )
    total_tasks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total tasks executed during interval",
    )
    successful_tasks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total successful tasks",
    )
    failed_tasks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total failed tasks",
    )
    success_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Success rate percentage (0-100)",
    )
    avg_duration_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Average task duration (seconds)",
    )
    avg_cost_usd: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Average cost per task (USD)",
    )
    total_cost_usd: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Total cost for provider (USD)",
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        comment="Record creation timestamp",
    )

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return (
            f"<ProviderMetrics(provider={self.provider}, date={self.date}, "
            f"total_tasks={self.total_tasks})>"
        )
