"""
Production Database Migration Script
Applies critical P0 migrations to fix parsing status issues
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from src.config.settings import get_settings

async def check_current_version():
    """Check current migration version."""
    settings = get_settings()
    engine = create_async_engine(str(settings.DATABASE_URL), echo=True)

    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("SELECT version_num FROM alembic_version")
            )
            version = result.scalar_one_or_none()
            print(f"\n✓ Current migration version: {version}")
            return version
    except Exception as e:
        print(f"\n✗ Error checking version: {e}")
        return None
    finally:
        await engine.dispose()


async def check_enum_values():
    """Check existing WorklistStatus enum values."""
    settings = get_settings()
    engine = create_async_engine(str(settings.DATABASE_URL), echo=False)

    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("""
                    SELECT unnest(enum_range(NULL::workliststatus))::text as status
                    ORDER BY status
                """)
            )
            statuses = [row[0] for row in result]
            print(f"\n✓ Existing WorklistStatus values: {statuses}")

            missing = []
            required = ['parsing', 'parsing_review', 'proofreading_review']
            for status in required:
                if status not in statuses:
                    missing.append(status)

            if missing:
                print(f"⚠️  Missing status values: {missing}")
            else:
                print("✓ All required status values exist")

            return missing
    except Exception as e:
        print(f"\n✗ Error checking enum values: {e}")
        return None
    finally:
        await engine.dispose()


async def check_raw_html_column():
    """Check if raw_html column exists."""
    settings = get_settings()
    engine = create_async_engine(str(settings.DATABASE_URL), echo=False)

    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'worklist_items'
                    AND column_name = 'raw_html'
                """)
            )
            exists = result.scalar_one_or_none()

            if exists:
                print("\n✓ raw_html column exists")
                return True
            else:
                print("\n⚠️  raw_html column does NOT exist")
                return False
    except Exception as e:
        print(f"\n✗ Error checking raw_html column: {e}")
        return None
    finally:
        await engine.dispose()


async def apply_enum_migration():
    """Add missing enum values to WorklistStatus."""
    settings = get_settings()
    engine = create_async_engine(str(settings.DATABASE_URL), echo=True)

    try:
        print("\n🔧 Adding missing enum values to WorklistStatus...")

        # PostgreSQL requires ALTER TYPE to be in its own transaction
        async with engine.begin() as conn:
            await conn.execute(
                text("ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'parsing'")
            )
            await conn.commit()

        async with engine.begin() as conn:
            await conn.execute(
                text("ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'parsing_review'")
            )
            await conn.commit()

        async with engine.begin() as conn:
            await conn.execute(
                text("ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'proofreading_review'")
            )
            await conn.commit()

        print("✓ Successfully added enum values")

        # Update alembic version
        async with engine.begin() as conn:
            await conn.execute(
                text("UPDATE alembic_version SET version_num = '20251110_1000'")
            )
            print("✓ Updated alembic version to 20251110_1000")

        return True
    except Exception as e:
        print(f"\n✗ Error applying enum migration: {e}")
        return False
    finally:
        await engine.dispose()


async def apply_raw_html_migration():
    """Add raw_html column to worklist_items."""
    settings = get_settings()
    engine = create_async_engine(str(settings.DATABASE_URL), echo=True)

    try:
        print("\n🔧 Adding raw_html column to worklist_items...")

        async with engine.begin() as conn:
            await conn.execute(
                text("ALTER TABLE worklist_items ADD COLUMN IF NOT EXISTS raw_html TEXT")
            )
            print("✓ Successfully added raw_html column")

        # Update alembic version
        async with engine.begin() as conn:
            await conn.execute(
                text("UPDATE alembic_version SET version_num = '77fd4b324d80'")
            )
            print("✓ Updated alembic version to 77fd4b324d80")

        return True
    except Exception as e:
        print(f"\n✗ Error applying raw_html migration: {e}")
        return False
    finally:
        await engine.dispose()


async def verify_migrations():
    """Verify all migrations were applied successfully."""
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)

    # Check version
    version = await check_current_version()

    # Check enum values
    missing_enums = await check_enum_values()

    # Check raw_html column
    has_raw_html = await check_raw_html_column()

    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)

    all_good = True

    if version == '77fd4b324d80':
        print("✓ Migration version: 77fd4b324d80 (correct)")
    else:
        print(f"⚠️  Migration version: {version} (expected 77fd4b324d80)")
        all_good = False

    if not missing_enums:
        print("✓ WorklistStatus enum: All required values present")
    else:
        print(f"✗ WorklistStatus enum: Missing {missing_enums}")
        all_good = False

    if has_raw_html:
        print("✓ raw_html column: Exists")
    else:
        print("✗ raw_html column: Missing")
        all_good = False

    print("="*60)

    if all_good:
        print("\n🎉 ALL MIGRATIONS SUCCESSFULLY APPLIED!")
    else:
        print("\n⚠️  Some migrations may need attention")

    return all_good


async def main():
    """Main migration flow."""
    print("="*60)
    print("CMS PRODUCTION DATABASE MIGRATION")
    print("Priority: P0 (Critical)")
    print("="*60)

    # Step 1: Check current state
    print("\n📋 Step 1: Checking current database state...")
    current_version = await check_current_version()
    missing_enums = await check_enum_values()
    has_raw_html = await check_raw_html_column()

    # Step 2: Determine what needs to be applied
    needs_enum = missing_enums is not None and len(missing_enums) > 0
    needs_raw_html = has_raw_html is False

    if not needs_enum and has_raw_html:
        print("\n✓ All migrations already applied!")
        await verify_migrations()
        return 0

    # Step 3: Apply migrations
    print("\n📋 Step 2: Applying required migrations...")

    if needs_enum:
        print("\n→ Applying migration: 20251110_1000 (WorklistStatus enum)")
        success = await apply_enum_migration()
        if not success:
            print("\n✗ Failed to apply enum migration")
            return 1

    if needs_raw_html:
        print("\n→ Applying migration: 77fd4b324d80 (raw_html column)")
        success = await apply_raw_html_migration()
        if not success:
            print("\n✗ Failed to apply raw_html migration")
            return 1

    # Step 4: Verify
    print("\n📋 Step 3: Verifying migrations...")
    success = await verify_migrations()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
