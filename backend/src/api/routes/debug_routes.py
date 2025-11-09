"""Debug endpoints for troubleshooting."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_session

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("/db-test")
async def test_database_connection(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Test database connection with a simple query."""
    try:
        # Simple query that should be fast
        result = await session.execute(text("SELECT 1 as test"))
        row = result.fetchone()

        return {
            "success": True,
            "message": "Database connection successful",
            "test_result": row[0] if row else None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@router.get("/db-worklist-count")
async def test_worklist_query(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Test a simple worklist query."""
    try:
        result = await session.execute(text("SELECT COUNT(*) FROM worklist_items"))
        count = result.scalar()

        return {
            "success": True,
            "message": "Worklist query successful",
            "count": count,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }
