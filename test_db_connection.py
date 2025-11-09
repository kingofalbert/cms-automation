#!/usr/bin/env python3
"""Test database connection directly."""
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine

async def test_connection():
    """Test database connection."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)

    print(f"🔗 Connecting to database...")
    print(f"   Host: {database_url.split('@')[1].split('/')[0] if '@' in database_url else 'unknown'}")

    try:
        engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            connect_args={
                "timeout": 10,
                "command_timeout": 10,
            }
        )

        print("📡 Testing connection...")
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1 as test")
            row = result.fetchone()
            print(f"✅ Database connection successful!")
            print(f"   Test query result: {row[0]}")

        print("\n📊 Testing worklist query...")
        async with engine.connect() as conn:
            result = await conn.execute("SELECT COUNT(*) FROM worklist_items")
            count = result.fetchone()[0]
            print(f"✅ Worklist query successful!")
            print(f"   Total worklist items: {count}")

        await engine.dispose()
        print("\n🎉 All tests passed!")

    except Exception as e:
        print(f"\n❌ Connection failed: {type(e).__name__}")
        print(f"   Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_connection())
