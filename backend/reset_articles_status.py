"""Reset all articles to pending status for testing multi-step workflow."""
import asyncio
from sqlalchemy import text
from src.config.database import get_db_config

async def reset_articles():
    """Reset all worklist items to pending status and clear article data."""
    db_config = get_db_config()
    async with db_config.session() as session:
        print("Resetting all worklist items to pending status...")

        # Reset worklist items to pending
        await session.execute(text(
            "UPDATE worklist_items SET status = 'pending', notes = '[]'::jsonb"
        ))
        print("✓ Reset all worklist items to pending")

        # Delete proofreading issues
        result = await session.execute(text(
            "DELETE FROM proofreading_issues WHERE article_id IN (SELECT article_id FROM worklist_items WHERE article_id IS NOT NULL)"
        ))
        print(f"Deleted {result.rowcount} proofreading issues")

        # Delete article images
        result = await session.execute(text(
            "DELETE FROM article_images WHERE article_id IN (SELECT article_id FROM worklist_items WHERE article_id IS NOT NULL)"
        ))
        print(f"Deleted {result.rowcount} article images")

        # Delete title suggestions
        result = await session.execute(text(
            "DELETE FROM title_suggestions WHERE article_id IN (SELECT article_id FROM worklist_items WHERE article_id IS NOT NULL)"
        ))
        print(f"Deleted {result.rowcount} title suggestions")

        # Delete SEO suggestions
        result = await session.execute(text(
            "DELETE FROM seo_suggestions WHERE article_id IN (SELECT article_id FROM worklist_items WHERE article_id IS NOT NULL)"
        ))
        print(f"Deleted {result.rowcount} SEO suggestions")

        # Delete FAQs
        result = await session.execute(text(
            "DELETE FROM article_faqs WHERE article_id IN (SELECT article_id FROM worklist_items WHERE article_id IS NOT NULL)"
        ))
        print(f"Deleted {result.rowcount} FAQs")

        await session.commit()

        # Show results
        result = await session.execute(text(
            "SELECT id, title, status, article_id FROM worklist_items ORDER BY id"
        ))
        items = result.fetchall()

        print("\n✓ All articles reset successfully!\n")
        print("Current worklist status:")
        print("-" * 80)
        for item in items:
            print(f"ID {item[0]}: {item[1][:50]:50} | Status: {item[2]:20} | Article: {item[3]}")
        print("-" * 80)
        print("\nThey will now go through the complete multi-step workflow:")
        print("  pending → parsing → parsing_review → proofreading → proofreading_review")

if __name__ == '__main__':
    asyncio.run(reset_articles())
