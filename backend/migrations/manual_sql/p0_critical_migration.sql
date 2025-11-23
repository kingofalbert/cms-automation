-- ============================================================================
-- CMS Production Database Migration - P0 (Critical)
-- ============================================================================
-- Purpose: Fix parsing status issues in production
-- Priority: P0 - Critical
-- Date: 2025-11-23
-- ============================================================================

-- Step 1: Check current migration version
SELECT version_num FROM alembic_version;

-- Step 2: Check existing WorklistStatus enum values
SELECT unnest(enum_range(NULL::workliststatus))::text as status ORDER BY status;

-- Step 3: Check if raw_html column exists
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'worklist_items'
AND column_name = 'raw_html';

-- ============================================================================
-- MIGRATION 1: Add missing enum values to WorklistStatus
-- ============================================================================
-- These values are required for the parsing workflow to work

-- Add 'parsing' status
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'workliststatus' AND e.enumlabel = 'parsing'
    ) THEN
        ALTER TYPE workliststatus ADD VALUE 'parsing';
        RAISE NOTICE 'Added enum value: parsing';
    ELSE
        RAISE NOTICE 'Enum value already exists: parsing';
    END IF;
END
$$;

-- Commit the enum change
COMMIT;

-- Add 'parsing_review' status (separate transaction)
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'workliststatus' AND e.enumlabel = 'parsing_review'
    ) THEN
        ALTER TYPE workliststatus ADD VALUE 'parsing_review';
        RAISE NOTICE 'Added enum value: parsing_review';
    ELSE
        RAISE NOTICE 'Enum value already exists: parsing_review';
    END IF;
END
$$;
COMMIT;

-- Add 'proofreading_review' status (separate transaction)
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'workliststatus' AND e.enumlabel = 'proofreading_review'
    ) THEN
        ALTER TYPE workliststatus ADD VALUE 'proofreading_review';
        RAISE NOTICE 'Added enum value: proofreading_review';
    ELSE
        RAISE NOTICE 'Enum value already exists: proofreading_review';
    END IF;
END
$$;
COMMIT;

-- Update alembic version for enum migration
BEGIN;
UPDATE alembic_version SET version_num = '20251110_1000'
WHERE version_num < '20251110_1000' OR version_num = '20251108_1800';
COMMIT;

-- ============================================================================
-- MIGRATION 2: Add raw_html column to worklist_items
-- ============================================================================
-- This column stores the original HTML content from Google Docs exports

BEGIN;

-- Add raw_html column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'worklist_items' AND column_name = 'raw_html'
    ) THEN
        ALTER TABLE worklist_items ADD COLUMN raw_html TEXT;
        RAISE NOTICE 'Added column: raw_html';
    ELSE
        RAISE NOTICE 'Column already exists: raw_html';
    END IF;
END
$$;

COMMIT;

-- Update alembic version for raw_html migration
BEGIN;
UPDATE alembic_version SET version_num = '77fd4b324d80'
WHERE version_num = '20251110_1000' OR version_num < '77fd4b324d80';
COMMIT;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify migration version
SELECT 'Migration Version:' as check_type, version_num as result FROM alembic_version;

-- Verify enum values exist
SELECT 'WorklistStatus Enum:' as check_type, unnest(enum_range(NULL::workliststatus))::text as result
ORDER BY result;

-- Verify raw_html column exists
SELECT 'Column Check:' as check_type,
       CASE
           WHEN EXISTS (
               SELECT 1 FROM information_schema.columns
               WHERE table_name = 'worklist_items' AND column_name = 'raw_html'
           ) THEN 'raw_html column EXISTS ✓'
           ELSE 'raw_html column MISSING ✗'
       END as result;

-- Check any stuck items in parsing status
SELECT 'Stuck Items:' as check_type, COUNT(*) as result
FROM worklist_items
WHERE status = 'pending'
AND created_at < NOW() - INTERVAL '1 hour';

-- ============================================================================
-- NOTES
-- ============================================================================
--
-- Expected results after migration:
-- 1. Migration version should be: 77fd4b324d80
-- 2. WorklistStatus enum should include: parsing, parsing_review, proofreading_review
-- 3. worklist_items table should have raw_html column (TEXT)
--
-- If any issues occur, check:
-- - Database logs for specific error messages
-- - Alembic version table for current version
-- - Enum values using: SELECT unnest(enum_range(NULL::workliststatus))::text
--
-- ============================================================================
