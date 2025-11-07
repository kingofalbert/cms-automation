-- Migration: Add index on worklist_items.updated_at for faster ordering
-- Revision ID: 20251106_1500
-- Create Date: 2025-11-06 15:00:00.000000
--
-- This migration adds an index to the worklist_items.updated_at column
-- to accelerate sorting queries when fetching worklist items.
--
-- Performance Impact:
-- - Speeds up queries that ORDER BY updated_at
-- - Improves response time for the worklist page load
-- - Small storage overhead for the index

-- Create index to accelerate sorting by updated_at
CREATE INDEX IF NOT EXISTS ix_worklist_items_updated_at ON worklist_items (updated_at);

-- Verify index was created
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'worklist_items' AND indexname = 'ix_worklist_items_updated_at';
