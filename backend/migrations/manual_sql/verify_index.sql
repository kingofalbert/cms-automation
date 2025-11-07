-- Verify that the index was created successfully
-- Run this in Supabase SQL Editor to confirm

SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'worklist_items'
  AND indexname = 'ix_worklist_items_updated_at';

-- Expected result:
-- Should return 1 row showing:
-- - schemaname: public
-- - tablename: worklist_items
-- - indexname: ix_worklist_items_updated_at
-- - indexdef: CREATE INDEX ix_worklist_items_updated_at ON public.worklist_items USING btree (updated_at)

-- Additional check: View all indexes on worklist_items table
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'worklist_items'
ORDER BY indexname;
