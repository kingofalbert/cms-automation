#!/usr/bin/env python3
"""Deep clean all tables and ENUM types from Supabase database."""
import asyncio
import asyncpg

async def deep_clean():
    """Remove all tables and ENUM types."""
    conn = await asyncpg.connect(
        'postgresql://postgres.twsbhjmlmspjwfystpti:Xieping890$@aws-1-us-east-1.pooler.supabase.com:5432/postgres'
    )

    print("🧹 Starting deep clean of Supabase database...")

    # Drop all tables in public schema
    tables = await conn.fetch('''
        SELECT tablename FROM pg_tables WHERE schemaname = 'public'
    ''')

    print(f"\n📋 Dropping {len(tables)} tables...")
    for table in tables:
        table_name = table['tablename']
        await conn.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
        print(f"  ✅ Dropped table: {table_name}")

    # Drop all ENUM types in public schema
    types = await conn.fetch('''
        SELECT typname FROM pg_type
        WHERE typtype = 'e'
        AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    ''')

    print(f"\n🔢 Dropping {len(types)} ENUM types...")
    for t in types:
        type_name = t['typname']
        await conn.execute(f"DROP TYPE IF EXISTS {type_name} CASCADE")
        print(f"  ✅ Dropped ENUM type: {type_name}")

    # Verify database is clean
    remaining_tables = await conn.fetch('''
        SELECT tablename FROM pg_tables WHERE schemaname = 'public'
    ''')

    remaining_types = await conn.fetch('''
        SELECT typname FROM pg_type
        WHERE typtype = 'e'
        AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    ''')

    print(f"\n✅ Deep clean complete!")
    print(f"   Remaining tables: {len(remaining_tables)}")
    print(f"   Remaining ENUM types: {len(remaining_types)}")

    if len(remaining_tables) == 0 and len(remaining_types) == 0:
        print("   ✅ Database is completely clean!")
    else:
        print("   ⚠️  Some objects remain:")
        if remaining_tables:
            for t in remaining_tables:
                print(f"      - Table: {t['tablename']}")
        if remaining_types:
            for t in remaining_types:
                print(f"      - ENUM: {t['typname']}")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(deep_clean())
