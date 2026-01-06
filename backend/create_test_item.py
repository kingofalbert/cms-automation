"""Create a test worklist item to verify parsing."""
import asyncio
from sqlalchemy import text
from src.config.database import get_db_config
from src.models.worklist import WorklistStatus

async def create_test_item():
    """Create a test item and trigger parsing."""
    db_config = get_db_config()
    async with db_config.session() as session:
        print("Creating test worklist item...")
        
        # Insert a dummy item
        result = await session.execute(text("""
            INSERT INTO worklist_items (
                drive_file_id, 
                title, 
                content, 
                status, 
                metadata, 
                notes,
                synced_at,
                created_at,
                updated_at
            ) VALUES (
                'test_file_id_123', 
                'Test Article for Parsing', 
                '<h1>Test Title</h1><p>This is a test article content.</p>', 
                'pending', 
                '{}'::jsonb, 
                '[]'::jsonb,
                now(),
                now(),
                now()
            ) RETURNING id
        """))
        item_id = result.scalar()
        await session.commit()
        print(f"✓ Created test item ID: {item_id}")
        
        # Trigger parsing (usually happens via sync, but we can simulate or just wait if worker picks up pending)
        # Actually, the pipeline picks up pending items.
        # Let's check if there's a way to trigger it.
        # Usually `process_new_item` is called.
        
        print("Test item created. Worker should pick it up if running.")

if __name__ == '__main__':
    asyncio.run(create_test_item())
