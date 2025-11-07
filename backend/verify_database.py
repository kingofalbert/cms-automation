#!/usr/bin/env python3
"""Verify database tables in Supabase."""
import asyncio
import asyncpg

async def verify_database():
    # Connect to Supabase
    conn = await asyncpg.connect(
        'postgresql://postgres.twsbhjmlmspjwfystpti:Xieping890$@aws-1-us-east-1.pooler.supabase.com:5432/postgres'
    )

    print("✅ Connected to Supabase database")
    print()

    # Check all tables in public schema
    tables = await conn.fetch("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)

    print(f"📋 Found {len(tables)} tables in 'public' schema:")
    for table in tables:
        print(f"  - {table['table_name']}")
    print()

    # Check if worklist_items exists
    worklist_exists = await conn.fetchval("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'worklist_items'
        );
    """)

    if worklist_exists:
        print("✅ worklist_items table exists")

        # Check columns
        columns = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'worklist_items'
            ORDER BY ordinal_position;
        """)

        print(f"\n📊 worklist_items has {len(columns)} columns:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']}")
    else:
        print("❌ worklist_items table NOT found")
        print("   Migrations may not have run or ran against wrong database")

    # Check alembic version
    alembic_version = await conn.fetchval("""
        SELECT version_num FROM alembic_version LIMIT 1;
    """)

    if alembic_version:
        print(f"\n✅ Alembic migration version: {alembic_version}")
    else:
        print("\n❌ No alembic_version table found - migrations never ran")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(verify_database())
