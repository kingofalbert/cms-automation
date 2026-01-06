"""Reset stuck parsing items to pending status."""
import asyncio
from sqlalchemy import text
from src.config.database import get_db_config

async def reset_stuck_items():
    """Reset items stuck in parsing status to pending."""
    db_config = get_db_config()
    async with db_config.session() as session:
        print("Checking alembic version...")
        result = await session.execute(text("SELECT * FROM alembic_version"))
        version = result.scalar()
        print("Alembic version:", version)

        print("Checking database tables in all schemas...")
        result = await session.execute(text(
            "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog')"
        ))
        tables = result.fetchall()
        table_info = [f"{t[0]}.{t[1]}" for t in tables]
        print("Tables found:", table_info)

        print("Listing all worklist items:")
        result = await session.execute(text(
            "SELECT id, title, status FROM worklist_items ORDER BY id"
        ))
        items = result.fetchall()
        for item in items:
            print(f" - ID {item[0]}: {item[1][:30]}... | Status: {item[2]}")

if __name__ == '__main__':
    asyncio.run(reset_stuck_items())
