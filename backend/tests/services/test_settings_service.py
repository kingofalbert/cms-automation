"""Tests for SettingsService."""

import sqlalchemy as sa
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.models import AppSettings, Base
from src.services.settings.service import SettingsService


class DummySettings:
    """Stub settings object for tests."""

    CMS_TYPE = "wordpress"
    CMS_BASE_URL = "https://example.com"
    CMS_USERNAME = "admin"
    CMS_APPLICATION_PASSWORD = "app-pass"
    CMS_API_TOKEN = "token"


@pytest.fixture
async def db_session():
    """Provide an async SQLAlchemy session with in-memory SQLite."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch):
    """Ensure services use deterministic settings during tests."""
    monkeypatch.setattr(
        "src.services.settings.service.get_settings",
        lambda: DummySettings(),
    )


class DummyCMSAuth:
    """Stub CMS auth handler returning predetermined results."""

    def __init__(self, cms_type, base_url, credentials):
        self.cms_type = cms_type
        self.base_url = base_url
        self.credentials = credentials
        self.verify_called = False

    async def verify_auth(self) -> bool:
        self.verify_called = True
        return True


@pytest.mark.asyncio
async def test_get_settings_creates_default_record(db_session: AsyncSession):
    """get_settings should create singleton record with defaults when empty."""
    service = SettingsService(db_session)

    settings = await service.get_settings()

    assert settings.id == 1
    assert settings.provider_config["default_provider"] == "hybrid"
    assert settings.cms_config["base_url"] == DummySettings.CMS_BASE_URL

    # Subsequent calls should reuse existing record without duplication
    settings_again = await service.get_settings()
    assert settings_again.id == settings.id
    total_settings = await db_session.scalar(
        sa.select(sa.func.count()).select_from(AppSettings)
    )
    assert total_settings == 1


@pytest.mark.asyncio
async def test_update_settings_merges_payload(db_session: AsyncSession):
    """Partial updates should merge dictionaries without losing existing keys."""
    service = SettingsService(db_session)
    await service.get_settings()

    payload = {
        "cms_config": {"base_url": "https://cms.example.com", "username": "editor"},
        "cost_limits": {"daily_budget_usd": 25.0},
    }
    updated = await service.update_settings(payload)

    assert updated.cms_config["base_url"] == "https://cms.example.com"
    assert updated.cms_config["application_password"] == DummySettings.CMS_APPLICATION_PASSWORD
    assert updated.cost_limits["daily_budget_usd"] == 25.0
    # ensure timestamp updated
    assert updated.updated_at is not None


@pytest.mark.asyncio
async def test_test_connection_success(monkeypatch, db_session: AsyncSession):
    """Connection test returns success when auth handler verifies credentials."""
    service = SettingsService(db_session)
    await service.get_settings()

    auth_stub = DummyCMSAuth("wordpress", DummySettings.CMS_BASE_URL, {})
    monkeypatch.setattr(
        "src.services.settings.service.CMSAuthHandler",
        lambda *args, **kwargs: auth_stub,
    )

    result = await service.test_connection({})

    assert result["success"] is True
    assert "Connection successful" in result["message"]
    assert result["details"]["cms_type"] == "wordpress"


@pytest.mark.asyncio
async def test_test_connection_missing_credentials(db_session: AsyncSession):
    """Connection test should fail gracefully when credentials are missing."""
    service = SettingsService(db_session)
    await service.get_settings()

    result = await service.test_connection({"cms_type": "wordpress", "base_url": "https://example.com"})

    assert result["success"] is False
    assert "application password" in result["message"]
