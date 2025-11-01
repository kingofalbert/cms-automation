"""Integration tests for settings and worklist API routes."""

from datetime import datetime

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.routes import register_routes
from src.models import Base, WorklistItem, WorklistStatus


class DummySettings:
    """Stub configuration for settings service."""

    CMS_TYPE = "wordpress"
    CMS_BASE_URL = "https://example.com"
    CMS_USERNAME = "admin"
    CMS_APPLICATION_PASSWORD = "app-pass"
    CMS_API_TOKEN = "token"


class DummyDriveSettings:
    """Stub configuration for Drive sync."""

    GOOGLE_DRIVE_FOLDER_ID = "folder-123"


@pytest.fixture
async def app_client(monkeypatch):
    """Provide FastAPI test client with in-memory SQLite database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    app = FastAPI()
    register_routes(app)

    async def override_get_session() -> AsyncSession:
        async with session_factory() as session:
            yield session

    from src.config.database import get_session as original_get_session

    app.dependency_overrides[original_get_session] = override_get_session

    monkeypatch.setattr(
        "src.services.settings.service.get_settings",
        lambda: DummySettings(),
    )
    monkeypatch.setattr(
        "src.services.google_drive.sync_service.get_settings",
        lambda: DummyDriveSettings(),
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client, session_factory

    await engine.dispose()


class AuthStub:
    """Stub for CMSAuthHandler."""

    def __init__(self, *args, **kwargs):
        self.called = False

    async def verify_auth(self) -> bool:
        self.called = True
        return True


@pytest.mark.asyncio
async def test_settings_get_and_update(app_client, monkeypatch):
    """Settings endpoints should return default payload and merge updates."""
    client, session_factory = app_client

    # GET defaults
    response = await client.get("/v1/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["provider_config"]["default_provider"] == "hybrid"
    assert data["cms_config"]["base_url"] == DummySettings.CMS_BASE_URL

    # PUT partial update
    payload = {
        "cms_config": {"base_url": "https://cms.test"},
        "cost_limits": {"daily_budget_usd": 15},
    }
    response = await client.put("/v1/settings", json=payload)
    assert response.status_code == 200
    updated = response.json()
    assert updated["cms_config"]["base_url"] == "https://cms.test"
    assert updated["cost_limits"]["daily_budget_usd"] == 15
    assert updated["cms_config"]["application_password"] == DummySettings.CMS_APPLICATION_PASSWORD

    # POST test-connection (successful)
    monkeypatch.setattr(
        "src.services.settings.service.CMSAuthHandler",
        lambda *args, **kwargs: AuthStub(),
    )
    response = await client.post("/v1/settings/test-connection", json={})
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "Connection successful" in result["message"]


@pytest.mark.asyncio
async def test_worklist_endpoints(app_client, monkeypatch):
    """Worklist routes should list items, update status, and trigger sync."""
    client, session_factory = app_client

    async with session_factory() as session:
        item = WorklistItem(
            drive_file_id="file-1",
            title="Draft Doc",
            status=WorklistStatus.TO_EVALUATE,
            content="Content",
            metadata={},
            notes=[],
            synced_at=datetime.utcnow(),
        )
        session.add(item)
        await session.commit()

    response = await client.get("/v1/worklist")
    assert response.status_code == 200
    listed = response.json()
    assert listed["total"] == 1
    assert listed["items"][0]["title"] == "Draft Doc"

    update_payload = {"status": WorklistStatus.TO_REVIEW.value, "note": {"author": "QA"}}
    response = await client.post("/v1/worklist/1/status", json=update_payload)
    assert response.status_code == 200
    updated = response.json()
    assert updated["status"] == WorklistStatus.TO_REVIEW.value
    assert updated["notes"][0]["author"] == "QA"

    class SyncStub:
        def __init__(self, session):
            self.session = session

        async def sync_worklist(self):
            return {"processed": 1, "created": 0, "updated": 1, "skipped": 0, "errors": []}

    monkeypatch.setattr(
        "src.services.worklist.service.GoogleDriveSyncService",
        lambda session: SyncStub(session),
    )

    response = await client.post("/v1/worklist/sync")
    assert response.status_code == 200
    sync_result = response.json()
    assert sync_result["status"] == "completed"
    assert sync_result["summary"]["updated"] == 1

    response = await client.get("/v1/worklist/statistics")
    assert response.status_code == 200
    stats = response.json()
    assert stats["breakdown"][WorklistStatus.TO_REVIEW.value] == 1
