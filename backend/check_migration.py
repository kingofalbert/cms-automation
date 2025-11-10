"""Check migration results using SQLAlchemy."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment
database_url = os.getenv("DATABASE_URL", "")

if not database_url:
    raise ValueError("DATABASE_URL not found in environment")

# Create synchronous engine for quick checks (use psycopg2)
sync_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
# Replace ssl=require with sslmode=require for psycopg2
sync_url = sync_url.replace("?ssl=require", "?sslmode=require")
engine = create_engine(sync_url)

print("✅ Database Migration Verification\n")

with engine.connect() as conn:
    # Check enum values
    print("📊 WorklistStatus enum values:")
    result = conn.execute(text("SELECT unnest(enum_range(NULL::workliststatus)) as status"))
    for row in result:
        print(f"   - {row[0]}")

    # Check status distribution
    print("\n📈 Worklist items status distribution:")
    result = conn.execute(
        text("SELECT status, COUNT(*) as count FROM worklist_items GROUP BY status ORDER BY count DESC")
    )
    rows = result.fetchall()
    if rows:
        for row in rows:
            print(f"   {row[0]}: {row[1]} items")
    else:
        print("   (No worklist items found)")

    # Check for under_review records
    print("\n🔍 Migration check (under_review → proofreading_review):")
    result = conn.execute(
        text("SELECT COUNT(*) FROM worklist_items WHERE status = :status"),
        {"status": "under_review"},
    )
    under_review_count = result.scalar()

    result = conn.execute(
        text("SELECT COUNT(*) FROM worklist_items WHERE status = :status"),
        {"status": "proofreading_review"},
    )
    proofreading_review_count = result.scalar()

    print(f"   under_review: {under_review_count} items")
    print(f"   proofreading_review: {proofreading_review_count} items")

    if under_review_count == 0:
        print("\n✅ Migration SUCCESS! All under_review records migrated")
    else:
        print(f"\n⚠️  Warning: {under_review_count} under_review records not migrated")

print("\n🎉 Migration verification complete!")
