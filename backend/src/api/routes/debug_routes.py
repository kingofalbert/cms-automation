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


@router.get("/db-table-sizes")
async def get_table_sizes(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get size of all tables in the database."""
    try:
        # Query to get table sizes in PostgreSQL
        query = text("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as total_size,
                pg_total_relation_size(schemaname || '.' || tablename) as total_bytes,
                pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) as table_size,
                pg_relation_size(schemaname || '.' || tablename) as table_bytes,
                pg_size_pretty(pg_indexes_size(schemaname || '.' || tablename)) as index_size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC
        """)
        result = await session.execute(query)
        rows = result.fetchall()

        tables = []
        total_bytes = 0
        for row in rows:
            tables.append({
                "table": row[1],
                "total_size": row[2],
                "total_bytes": row[3],
                "table_size": row[4],
                "index_size": row[6],
            })
            total_bytes += row[3]

        # Get database size
        db_size_result = await session.execute(
            text("SELECT pg_size_pretty(pg_database_size(current_database())), pg_database_size(current_database())")
        )
        db_size_row = db_size_result.fetchone()

        return {
            "success": True,
            "database_size": db_size_row[0] if db_size_row else "unknown",
            "database_bytes": db_size_row[1] if db_size_row else 0,
            "tables_total_bytes": total_bytes,
            "tables": tables,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@router.get("/db-column-sizes/{table_name}")
async def get_column_sizes(
    table_name: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get estimated size of each column in a table."""
    # Whitelist of allowed tables for safety
    allowed_tables = {"worklist_items", "articles", "health_articles", "proofreading_decisions"}
    if table_name not in allowed_tables:
        return {
            "success": False,
            "error": f"Table '{table_name}' not in allowed list: {allowed_tables}",
        }

    try:
        # Get column information and estimate sizes
        query = text(f"""
            SELECT
                column_name,
                data_type,
                pg_size_pretty(
                    COALESCE(
                        SUM(pg_column_size({table_name}.*::text)),
                        0
                    )
                ) as estimated_size,
                COALESCE(SUM(pg_column_size({table_name}.*::text)), 0) as estimated_bytes
            FROM information_schema.columns
            CROSS JOIN {table_name}
            WHERE table_name = :table_name AND table_schema = 'public'
            GROUP BY column_name, data_type
            ORDER BY estimated_bytes DESC
            LIMIT 20
        """)

        # Simpler approach: get avg size per column
        simple_query = text(f"""
            SELECT
                'total_rows' as info,
                COUNT(*) as value
            FROM {table_name}
            UNION ALL
            SELECT
                'avg_row_size',
                AVG(pg_column_size({table_name}.*))::bigint
            FROM {table_name}
        """)
        result = await session.execute(simple_query)
        rows = result.fetchall()

        info = {row[0]: row[1] for row in rows}

        return {
            "success": True,
            "table": table_name,
            "total_rows": info.get("total_rows", 0),
            "avg_row_size_bytes": info.get("avg_row_size", 0),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@router.post("/db-vacuum/{table_name}")
async def vacuum_table(
    table_name: str,
    full: bool = True,
) -> dict:
    """Run VACUUM on a table to reclaim dead space.

    VACUUM FULL rewrites the entire table and reclaims all space but requires exclusive lock.
    Regular VACUUM only marks space as reusable without returning it to OS.
    """
    from sqlalchemy import create_engine
    from src.config import get_settings

    # Whitelist of allowed tables for safety
    allowed_tables = {"worklist_items", "articles", "health_articles", "proofreading_decisions"}
    if table_name not in allowed_tables:
        return {
            "success": False,
            "error": f"Table '{table_name}' not in allowed list: {allowed_tables}",
        }

    try:
        settings = get_settings()
        # Create sync engine for VACUUM (needs autocommit)
        db_url = str(settings.DATABASE_URL)
        sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        engine = create_engine(sync_url, isolation_level="AUTOCOMMIT")

        with engine.connect() as conn:
            # Get size before vacuum
            result = conn.execute(text(f"SELECT pg_total_relation_size('{table_name}')"))
            before_bytes = result.scalar()

            # Run VACUUM
            vacuum_cmd = f"VACUUM FULL {table_name}" if full else f"VACUUM {table_name}"
            conn.execute(text(vacuum_cmd))

            # Get size after vacuum
            result = conn.execute(text(f"SELECT pg_total_relation_size('{table_name}')"))
            after_bytes = result.scalar()

        engine.dispose()

        freed_bytes = before_bytes - after_bytes

        return {
            "success": True,
            "table": table_name,
            "vacuum_type": "FULL" if full else "regular",
            "before_bytes": before_bytes,
            "after_bytes": after_bytes,
            "freed_bytes": freed_bytes,
            "before_size": f"{before_bytes / 1024 / 1024:.2f} MB",
            "after_size": f"{after_bytes / 1024 / 1024:.2f} MB",
            "freed_size": f"{freed_bytes / 1024 / 1024:.2f} MB",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@router.get("/db-worklist-detail-sizes")
async def get_worklist_detail_sizes(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get detailed size breakdown for each worklist item."""
    try:
        query = text("""
            SELECT
                id,
                title,
                status,
                LENGTH(content) as content_len,
                LENGTH(raw_html) as raw_html_len,
                LENGTH(notes::text) as notes_len,
                LENGTH(metadata::text) as metadata_len,
                pg_column_size(content) as content_bytes,
                pg_column_size(raw_html) as raw_html_bytes,
                pg_column_size(notes) as notes_bytes,
                pg_column_size(metadata) as metadata_bytes,
                pg_column_size(worklist_items.*) as total_row_bytes
            FROM worklist_items
            ORDER BY pg_column_size(worklist_items.*) DESC
        """)
        result = await session.execute(query)
        rows = result.fetchall()

        items = []
        for row in rows:
            items.append({
                "id": row[0],
                "title": row[1][:50] if row[1] else None,
                "status": row[2],
                "content_len": row[3],
                "raw_html_len": row[4],
                "notes_len": row[5],
                "metadata_len": row[6],
                "content_bytes": row[7],
                "raw_html_bytes": row[8],
                "notes_bytes": row[9],
                "metadata_bytes": row[10],
                "total_row_bytes": row[11],
            })

        return {
            "success": True,
            "items": items,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@router.get("/db-bloat-check")
async def check_database_bloat(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Check for database bloat and dead tuples."""
    try:
        # Check for bloat using pgstattuple extension or estimate
        bloat_query = text("""
            SELECT
                schemaname,
                relname as table_name,
                n_live_tup as live_tuples,
                n_dead_tup as dead_tuples,
                n_mod_since_analyze as mods_since_analyze,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                pg_size_pretty(pg_total_relation_size(schemaname || '.' || relname)) as total_size,
                pg_total_relation_size(schemaname || '.' || relname) as total_bytes
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY n_dead_tup DESC
            LIMIT 20
        """)
        result = await session.execute(bloat_query)
        rows = result.fetchall()

        tables = []
        for row in rows:
            tables.append({
                "table": row[1],
                "live_tuples": row[2],
                "dead_tuples": row[3],
                "mods_since_analyze": row[4],
                "last_vacuum": str(row[5]) if row[5] else None,
                "last_autovacuum": str(row[6]) if row[6] else None,
                "total_size": row[8],
                "total_bytes": row[9],
            })

        # Check TOAST table sizes
        toast_query = text("""
            SELECT
                c.relname as table_name,
                pg_size_pretty(pg_total_relation_size(c.reltoastrelid)) as toast_size,
                pg_total_relation_size(c.reltoastrelid) as toast_bytes
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.reltoastrelid != 0
            ORDER BY pg_total_relation_size(c.reltoastrelid) DESC
            LIMIT 10
        """)
        toast_result = await session.execute(toast_query)
        toast_rows = toast_result.fetchall()

        toast_tables = []
        for row in toast_rows:
            toast_tables.append({
                "table": row[0],
                "toast_size": row[1],
                "toast_bytes": row[2],
            })

        return {
            "success": True,
            "tables": tables,
            "toast_tables": toast_tables,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }
