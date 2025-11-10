"""Verify database migration results."""
import asyncio
import os
import asyncpg


async def verify_migration():
    """Check enum values and data migration."""
    database_url = os.getenv("DATABASE_URL", "")
    # Convert SQLAlchemy URL to asyncpg format
    conn_str = database_url.replace("postgresql+asyncpg://", "postgresql://")

    # Remove query parameters for asyncpg (it handles SSL differently)
    if "?" in conn_str:
        conn_str = conn_str.split("?")[0]

    conn = await asyncpg.connect(conn_str)

    print("✅ 檢查 WorklistStatus enum 值:")
    enum_values = await conn.fetch(
        "SELECT unnest(enum_range(NULL::workliststatus)) as status;"
    )
    for row in enum_values:
        print(f'  - {row["status"]}')

    print("\n✅ 檢查 worklist_items 狀態分佈:")
    status_counts = await conn.fetch(
        "SELECT status, COUNT(*) as count FROM worklist_items GROUP BY status ORDER BY count DESC;"
    )
    if status_counts:
        for row in status_counts:
            print(f'  {row["status"]}: {row["count"]} 筆')
    else:
        print("  (沒有 worklist_items 記錄)")

    print("\n✅ 檢查資料遷移 (under_review → proofreading_review):")
    under_review_count = await conn.fetchval(
        "SELECT COUNT(*) FROM worklist_items WHERE status = $1", "under_review"
    )
    proofreading_review_count = await conn.fetchval(
        "SELECT COUNT(*) FROM worklist_items WHERE status = $1", "proofreading_review"
    )

    print(f"  under_review: {under_review_count} 筆")
    print(f"  proofreading_review: {proofreading_review_count} 筆")

    if under_review_count == 0:
        print(f"\n✅ 資料遷移成功！所有 under_review 記錄已遷移")
    else:
        print(f"\n⚠️  還有 {under_review_count} 筆 under_review 記錄未遷移")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(verify_migration())
