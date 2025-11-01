"""Tests for GoogleDriveSyncService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.models import Base, WorklistItem
from src.services.google_drive.sync_service import GoogleDriveSyncService


class DummySettings:
    """Stub settings supplying Drive folder."""

    GOOGLE_DRIVE_FOLDER_ID = "drive-folder"


class StubDriveStorage:
    """Minimal Google Drive storage stub."""

    def __init__(self):
        self.iteration = 0

    async def list_files(self, folder_id=None, max_results=100):
        return [
            {
                "id": "file-123",
                "mimeType": "text/plain",
                "name": "Example",
                "webViewLink": "https://drive/file-123",
                "createdTime": "2025-10-26T00:00:00Z",
            }
        ]

    async def download_file(self, file_id: str) -> bytes:
        self.iteration += 1
        if self.iteration == 1:
            return b"My Title\nInitial body content."
        return b"My Title Updated\nRefined body content."


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
    """Patch get_settings for sync service."""
    monkeypatch.setattr(
        "src.services.google_drive.sync_service.get_settings",
        lambda: DummySettings(),
    )


@pytest.mark.asyncio
async def test_sync_worklist_creates_and_updates_items(monkeypatch, db_session: AsyncSession):
    """Drive sync should create new worklist items and update existing ones."""

    async def fake_create_google_drive_storage():
        return StubDriveStorage()

    monkeypatch.setattr(
        "src.services.google_drive.sync_service.create_google_drive_storage",
        fake_create_google_drive_storage,
    )

    service = GoogleDriveSyncService(db_session)

    summary_first = await service.sync_worklist()
    assert summary_first["created"] == 1
    assert summary_first["updated"] == 0

    # Item should exist with initial title/content
    item = await db_session.get(WorklistItem, 1)
    assert item is not None
    assert item.title == "My Title"
    assert "Initial body content." in item.content
    initial_synced_at = item.synced_at

    # Second sync should update existing record
    summary_second = await service.sync_worklist()
    assert summary_second["created"] == 0
    assert summary_second["updated"] == 1

    refreshed = await db_session.get(WorklistItem, 1)
    assert refreshed.title == "My Title Updated"
    assert "Refined body content." in refreshed.content
    assert refreshed.synced_at >= initial_synced_at
