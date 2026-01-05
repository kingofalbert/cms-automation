#!/usr/bin/env python3
"""Backfill word_count in drive_metadata for existing worklist items.

Run this one-time script after deploying the word_count fix to populate
word_count for items that were synced before the fix was deployed.

Usage:
    poetry run python scripts/backfill_word_count.py
"""

import asyncio
import json
import os
import sys

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async def backfill_word_counts():
    """Backfill word_count for all worklist items missing it."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    # Convert postgres:// to postgresql+asyncpg:// and handle SSL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Remove sslmode from URL and use ssl=require for asyncpg
    if "sslmode=" in database_url:
        database_url = database_url.split("?")[0] + "?ssl=require"

    print(f"Connecting to database...")
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get all worklist items with content
        result = await session.execute(
            text("""
                SELECT id, title, content, metadata
                FROM worklist_items
                WHERE content IS NOT NULL AND content != ''
            """)
        )
        items = result.fetchall()
        print(f"Found {len(items)} items to process")

        updated_count = 0
        for item in items:
            item_id, title, content, metadata = item
            metadata = metadata or {}

            # Skip if word_count already exists
            if "word_count" in metadata:
                continue

            # Calculate word count
            word_count = len(content.split())
            metadata["word_count"] = word_count
            metadata["estimated_reading_time"] = max(1, round(word_count / 200))

            # Update the item (convert dict to JSON string for asyncpg)
            await session.execute(
                text("""
                    UPDATE worklist_items
                    SET metadata = :metadata::jsonb
                    WHERE id = :id
                """),
                {"id": item_id, "metadata": json.dumps(metadata)}
            )
            updated_count += 1
            print(f"  Updated item {item_id}: {title[:50]}... ({word_count} words)")

        await session.commit()
        print(f"\nBackfill complete! Updated {updated_count} items.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(backfill_word_counts())
