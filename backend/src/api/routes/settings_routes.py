"""Settings management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import (
    ConnectionTestRequest,
    ConnectionTestResponse,
    SettingsResponse,
    SettingsUpdateRequest,
)
from src.config.database import get_session
from src.config.logging import get_logger
from src.models import AppSettings
from src.services.settings import SettingsService

logger = get_logger(__name__)
router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsResponse)
async def get_app_settings(
    session: AsyncSession = Depends(get_session),
) -> SettingsResponse:
    """Fetch stored application settings."""
    service = SettingsService(session)
    settings = await service.get_settings()
    return _serialize_settings(settings)


@router.put("", response_model=SettingsResponse)
async def update_app_settings(
    payload: SettingsUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> SettingsResponse:
    """Apply partial update to application settings."""
    service = SettingsService(session)
    updated = await service.update_settings(payload.model_dump(exclude_none=True))

    logger.info("app_settings_updated", updated_at=updated.updated_at.isoformat())
    return _serialize_settings(updated)


@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_cms_connection(
    payload: ConnectionTestRequest,
    session: AsyncSession = Depends(get_session),
) -> ConnectionTestResponse:
    """Test CMS connectivity using stored or supplied credentials."""
    service = SettingsService(session)
    result = await service.test_connection(payload.model_dump(exclude_none=True))

    logger.info(
        "cms_connection_test_completed",
        success=result["success"],
        cms_type=result.get("details", {}).get("cms_type"),
    )
    return ConnectionTestResponse(**result)


def _serialize_settings(settings: AppSettings) -> SettingsResponse:
    """Convert ORM entity into API schema."""
    return SettingsResponse(
        provider_config=dict(settings.provider_config or {}),
        cms_config=dict(settings.cms_config or {}),
        cost_limits=dict(settings.cost_limits or {}),
        screenshot_retention=dict(settings.screenshot_retention or {}),
        updated_at=settings.updated_at,
    )
