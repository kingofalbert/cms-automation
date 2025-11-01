"""Schemas for analytics API responses."""

from typing import List, Optional

from pydantic import Field

from src.api.schemas.base import BaseSchema


class ProviderMetric(BaseSchema):
    """Aggregated provider metrics."""

    provider: str = Field(..., description="Provider identifier")
    total_tasks: int = Field(..., ge=0, description="Total tasks observed")
    completed_tasks: int = Field(..., ge=0, description="Successful tasks")
    failed_tasks: int = Field(..., ge=0, description="Failed tasks")
    in_progress_tasks: int = Field(..., ge=0, description="In-progress tasks")
    success_rate: float = Field(..., ge=0.0, le=100.0, description="Success rate percent")
    avg_duration_seconds: Optional[float] = Field(
        default=None, ge=0.0, description="Average task duration (seconds)"
    )
    avg_cost_usd: Optional[float] = Field(
        default=None, ge=0.0, description="Average cost per task (USD)"
    )
    total_cost_usd: float = Field(..., ge=0.0, description="Total cost (USD)")


class CostUsageEntry(BaseSchema):
    """Daily cost usage metrics."""

    date: str | None = Field(
        default=None, description="ISO date representing the usage bucket"
    )
    total_cost_usd: float = Field(..., ge=0.0, description="Total cost in USD")
    avg_cost_usd: float = Field(..., ge=0.0, description="Average cost in USD")


class StorageUsageEntry(BaseSchema):
    """Storage consumption details for uploaded assets."""

    file_type: str = Field(..., description="File type classification")
    file_count: int = Field(..., ge=0, description="Number of files")
    total_bytes: int = Field(..., ge=0, description="Total bytes consumed")
    total_megabytes: float = Field(
        ..., ge=0.0, description="Total megabytes consumed (rounded)"
    )


class RecommendationsResponse(BaseSchema):
    """Recommendation payload summarizing provider performance insights."""

    summary: str = Field(..., description="High-level summary statement")
    recommendations: List[str] = Field(
        default_factory=list, description="List of actionable recommendations"
    )
    metrics: List[ProviderMetric] = Field(
        default_factory=list, description="Underlying provider metrics"
    )
