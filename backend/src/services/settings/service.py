"""Settings management service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.config.logging import get_logger
from src.models import AppSettings
from src.services.cms_adapter.auth import CMSAuthHandler

logger = get_logger(__name__)


class SettingsService:
    """Encapsulates persistence and validation for application settings."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_settings(self) -> AppSettings:
        """Load settings record, creating defaults if missing."""
        return await self._ensure_settings()

    async def update_settings(self, updates: Dict[str, Dict[str, Any]]) -> AppSettings:
        """Apply partial settings update."""
        settings = await self._ensure_settings()
        changed = False

        if (provider_config := updates.get("provider_config")) is not None:
            settings.provider_config = self._merge_dict(
                settings.provider_config, provider_config
            )
            changed = True

        if (cms_config := updates.get("cms_config")) is not None:
            settings.cms_config = self._merge_dict(settings.cms_config, cms_config)
            changed = True

        if (cost_limits := updates.get("cost_limits")) is not None:
            settings.cost_limits = self._merge_dict(
                settings.cost_limits, cost_limits
            )
            changed = True

        if (
            screenshot_retention := updates.get("screenshot_retention")
        ) is not None:
            settings.screenshot_retention = self._merge_dict(
                settings.screenshot_retention, screenshot_retention
            )
            changed = True

        if changed:
            settings.updated_at = datetime.utcnow()
            self.session.add(settings)
            await self.session.commit()
            await self.session.refresh(settings)

        return settings

    async def test_connection(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Test CMS connectivity using stored or supplied credentials."""
        settings = await self._ensure_settings()
        cms_config = dict(settings.cms_config or {})

        cms_type = (payload.get("cms_type") or cms_config.get("cms_type") or "wordpress").lower()
        base_url = payload.get("base_url") or cms_config.get("base_url")
        username = payload.get("username") or cms_config.get("username")
        application_password = payload.get("application_password") or cms_config.get(
            "application_password"
        )
        api_token = payload.get("api_token") or cms_config.get("api_token")

        if not base_url:
            return {
                "success": False,
                "message": "CMS base URL is required for connection testing.",
                "details": {"cms_type": cms_type},
            }

        credentials: Dict[str, Any]
        if cms_type == "wordpress":
            if not username or not application_password:
                return {
                    "success": False,
                    "message": "WordPress username and application password are required.",
                    "details": {"cms_type": cms_type},
                }
            credentials = {
                "username": username,
                "application_password": application_password,
            }
        else:
            if not api_token:
                return {
                    "success": False,
                    "message": "API token is required for the selected CMS type.",
                    "details": {"cms_type": cms_type},
                }
            credentials = {"api_token": api_token}

        handler = CMSAuthHandler(cms_type, base_url.rstrip("/"), credentials)

        try:
            success = await handler.verify_auth()
            message = (
                "Connection successful." if success else "Authentication failed."
            )
            return {
                "success": success,
                "message": message,
                "details": {"cms_type": cms_type, "base_url": base_url},
            }
        except Exception as exc:  # noqa: BLE001 - propagate detailed error
            logger.error(
                "settings_connection_test_failed",
                cms_type=cms_type,
                base_url=base_url,
                error=str(exc),
                exc_info=True,
            )
            return {
                "success": False,
                "message": "Connection test failed.",
                "details": {
                    "cms_type": cms_type,
                    "base_url": base_url,
                    "error": str(exc),
                },
            }

    async def _ensure_settings(self) -> AppSettings:
        """Fetch existing settings or create defaults."""
        result = await self.session.execute(select(AppSettings))
        settings = result.scalars().first()

        if settings:
            return settings

        defaults = self._default_payload()
        settings = AppSettings(**defaults)
        self.session.add(settings)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings

    def _default_payload(self) -> Dict[str, Any]:
        """Construct default settings record."""
        env_settings = get_settings()

        provider_config = {
            "default_provider": "hybrid",
            "providers": {
                "playwright": {"enabled": True},
                "computer_use": {"enabled": True},
                "hybrid": {"strategy": "auto"},
            },
        }

        cms_config = {
            "cms_type": env_settings.CMS_TYPE,
            "base_url": env_settings.CMS_BASE_URL,
            "username": env_settings.CMS_USERNAME,
            "application_password": env_settings.CMS_APPLICATION_PASSWORD,
            "api_token": env_settings.CMS_API_TOKEN,
        }

        cost_limits = {
            "daily_budget_usd": 50.0,
            "monthly_budget_usd": 1000.0,
            "alert_threshold": 0.8,
        }

        screenshot_retention = {
            "retention_days": 30,
            "max_per_task": 20,
        }

        return {
            "id": 1,
            "provider_config": provider_config,
            "cms_config": cms_config,
            "cost_limits": cost_limits,
            "screenshot_retention": screenshot_retention,
            "updated_at": datetime.utcnow(),
        }

    def _merge_dict(
        self, existing: Dict[str, Any] | None, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge update dictionary into existing configuration."""
        merged: Dict[str, Any] = dict(existing or {})
        merged.update(updates)
        return merged
