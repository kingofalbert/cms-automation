"""Reset all worklist items to pending status - minimal version."""
import asyncio
from sqlalchemy import text
from src.config.database import get_db_config

async def reset_worklist():
    """Reset all worklist items to pending status."""
    db_config = get_db_config()
    async with db_config.session() as session:
        print("Resetting all worklist items to pending status...")

        # Reset worklist items to pending
        result = await session.execute(text(
            "UPDATE worklist_items SET status = 'pending', notes = '[]'::jsonb"
        ))
        print(f"✓ Reset {result.rowcount} worklist items to pending")

        await session.commit()

        # Show results
        result = await session.execute(text(
            "SELECT id, title, status, article_id FROM worklist_items ORDER BY id"
        ))
        items = result.fetchall()

        print("\n✓ All worklist items reset successfully!\n")
        print("Current worklist status:")
        print("-" * 80)
        for item in items:
            print(f"ID {item[0]}: {item[1][:50]:50} | Status: {item[2]:20} | Article: {item[3]}")
        print("-" * 80)
        print("\nThey will now go through the complete multi-step workflow:")
        print("  pending → parsing → parsing_review → proofreading → proofreading_review")

if __name__ == '__main__':
    asyncio.run(reset_worklist())
