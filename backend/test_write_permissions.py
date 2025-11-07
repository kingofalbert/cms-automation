#!/usr/bin/env python3
"""Test if we can write to Supabase database."""
import asyncio
import asyncpg

async def test_write():
    """Test basic write operations."""
    conn = await asyncpg.connect(
        'postgresql://postgres.twsbhjmlmspjwfystpti:Xieping890$@aws-1-us-east-1.pooler.supabase.com:5432/postgres'
    )

    print("✅ Connected to Supabase")

    try:
        # Try to create a simple test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL
            );
        """)
        print("✅ Successfully created test_table")

        # Insert a row
        await conn.execute("INSERT INTO test_table (name) VALUES ('test')")
        print("✅ Successfully inserted row")

        # Verify it exists
        count = await conn.fetchval("SELECT COUNT(*) FROM test_table")
        print(f"✅ Table has {count} row(s)")

        # Check all tables
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' ORDER BY table_name;
        """)
        print(f"\n📋 All tables in database:")
        for table in tables:
            print(f"  - {table['table_name']}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(test_write())
