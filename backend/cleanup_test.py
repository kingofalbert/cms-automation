#!/usr/bin/env python3
"""Clean up test table."""
import asyncio
import asyncpg

async def cleanup():
    conn = await asyncpg.connect(
        'postgresql://postgres.twsbhjmlmspjwfystpti:Xieping890$@aws-1-us-east-1.pooler.supabase.com:5432/postgres'
    )
    await conn.execute("DROP TABLE IF EXISTS test_table CASCADE")
    print("✅ Cleaned up test_table")
    await conn.close()

if __name__ == '__main__':
    asyncio.run(cleanup())
