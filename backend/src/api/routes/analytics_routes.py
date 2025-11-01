"""Analytics API routes for provider comparison and resource usage."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import (
    CostUsageEntry,
    ProviderMetric,
    RecommendationsResponse,
    StorageUsageEntry,
)
from src.config.database import get_session
from src.config.logging import get_logger
from src.services.analytics.service import AnalyticsService

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/provider-comparison", response_model=list[ProviderMetric])
async def get_provider_comparison(
    time_range: str = Query(default="30d", pattern="^(7d|30d|90d|all)$"),
    session: AsyncSession = Depends(get_session),
) -> list[ProviderMetric]:
    """Compare provider performance metrics for the given time window."""
    service = AnalyticsService(session)

    try:
        metrics = await service.provider_comparison(time_range=time_range)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    logger.debug(
        "analytics_provider_comparison_generated",
        time_range=time_range,
        provider_count=len(metrics),
    )

    return [ProviderMetric(**metric) for metric in metrics]


@router.get("/cost-usage", response_model=list[CostUsageEntry])
async def get_cost_usage(
    time_range: str = Query(default="30d", pattern="^(7d|30d|90d|all)$"),
    session: AsyncSession = Depends(get_session),
) -> list[CostUsageEntry]:
    """Return daily cost usage for publishing tasks within a time window."""
    service = AnalyticsService(session)
    try:
        usage = await service.cost_usage(time_range=time_range)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    logger.debug(
        "analytics_cost_usage_generated",
        time_range=time_range,
        buckets=len(usage),
    )

    return [CostUsageEntry(**entry) for entry in usage]


@router.get("/storage-usage", response_model=list[StorageUsageEntry])
async def get_storage_usage(
    session: AsyncSession = Depends(get_session),
) -> list[StorageUsageEntry]:
    """Summarize storage consumption grouped by file type."""
    service = AnalyticsService(session)
    usage = await service.storage_usage()

    logger.debug(
        "analytics_storage_usage_generated",
        groups=len(usage),
    )

    return [StorageUsageEntry(**entry) for entry in usage]


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    time_range: str = Query(default="30d", pattern="^(7d|30d|90d|all)$"),
    session: AsyncSession = Depends(get_session),
) -> RecommendationsResponse:
    """Provide heuristic recommendations based on provider performance."""
    service = AnalyticsService(session)
    try:
        recommendations = await service.recommendations(time_range=time_range)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    logger.debug(
        "analytics_recommendations_generated",
        time_range=time_range,
        recommendation_count=len(recommendations.get("recommendations", [])),
    )

    return RecommendationsResponse(**recommendations)
