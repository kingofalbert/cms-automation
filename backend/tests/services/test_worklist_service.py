"""Tests for WorklistService."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.models import Base, WorklistItem, WorklistStatus
from src.services.worklist.service import WorklistService


class DummyDriveSettings:
    """Stub settings for drive sync."""

    GOOGLE_DRIVE_FOLDER_ID = "folder-123"


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
def patch_drive_settings(monkeypatch):
    """Patch get_settings used by Google Drive sync service."""
    monkeypatch.setattr(
        "src.services.google_drive.sync_service.get_settings",
        lambda: DummyDriveSettings(),
    )


@pytest.mark.asyncio
async def test_list_items_filters_by_status(db_session: AsyncSession):
    """WorklistService.list_items should filter by status and paginate."""
    items = [
        WorklistItem(
            drive_file_id=f"file-{idx}",
            title=f"Doc {idx}",
            status=WorklistStatus.TO_EVALUATE if idx % 2 == 0 else WorklistStatus.TO_REVIEW,
            content="Body",
            metadata={},
            notes=[],
            synced_at=datetime.utcnow() - timedelta(minutes=idx),
        )
        for idx in range(6)
    ]
    db_session.add_all(items)
    await db_session.commit()

    service = WorklistService(db_session)

    filtered, total = await service.list_items(status=WorklistStatus.TO_REVIEW.value, limit=10, offset=0)

    assert total == 3
    assert all(item.status == WorklistStatus.TO_REVIEW for item in filtered)


@pytest.mark.asyncio
async def test_update_status_appends_note(db_session: AsyncSession):
    """Updating status should append reviewer note with timestamp."""
    item = WorklistItem(
        drive_file_id="file-1",
        title="Doc 1",
        status=WorklistStatus.TO_EVALUATE,
        content="Body",
        metadata={},
        notes=[],
        synced_at=datetime.utcnow(),
    )
    db_session.add(item)
    await db_session.commit()

    service = WorklistService(db_session)
    updated = await service.update_status(
        item_id=item.id,
        status=WorklistStatus.TO_CONFIRM.value,
        note={"author": "reviewer", "comment": "Looks good"},
    )

    assert updated.status == WorklistStatus.TO_CONFIRM
    assert len(updated.notes) == 1
    assert updated.notes[0]["author"] == "reviewer"
    assert "timestamp" in updated.notes[0]


class DummySyncService:
    """Stub Google Drive sync returning synthetic summary."""

    def __init__(self, session):
        self.session = session
        self.called = False

    async def sync_worklist(self):
        self.called = True
        return {"processed": 2, "created": 2, "updated": 0, "skipped": 0, "errors": []}


@pytest.mark.asyncio
async def test_trigger_sync_returns_summary(monkeypatch, db_session: AsyncSession):
    """trigger_sync should return summary from Drive sync service."""
    dummy_sync = DummySyncService(db_session)
    monkeypatch.setattr(
        "src.services.worklist.service.GoogleDriveSyncService",
        lambda session: dummy_sync,
    )

    service = WorklistService(db_session)
    response = await service.trigger_sync()

    assert response["status"] == "completed"
    assert response["summary"]["processed"] == 2
    assert dummy_sync.called is True
