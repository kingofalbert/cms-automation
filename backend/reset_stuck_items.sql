-- ============================================================================
-- Reset Stuck Worklist Items
-- ============================================================================
-- Purpose: Reset stuck items in 'parsing' status back to 'pending'
-- Date: 2025-11-23
-- ============================================================================

-- Step 1: Identify stuck items
SELECT
    id,
    title,
    status,
    created_at,
    updated_at,
    AGE(NOW(), updated_at) as stuck_duration
FROM worklist_items
WHERE status = 'parsing'
AND updated_at < NOW() - INTERVAL '1 hour'
ORDER BY updated_at ASC;

-- Step 2: Reset to pending (UNCOMMENT TO EXECUTE)
-- BEGIN;
--
-- UPDATE worklist_items
-- SET
--     status = 'pending',
--     updated_at = NOW()
-- WHERE status = 'parsing'
-- AND updated_at < NOW() - INTERVAL '1 hour';
--
-- COMMIT;

-- Step 3: Verify reset
SELECT
    id,
    title,
    status,
    updated_at
FROM worklist_items
WHERE id IN (SELECT id FROM worklist_items WHERE status = 'pending')
ORDER BY updated_at DESC
LIMIT 10;

-- ============================================================================
-- Alternative: Reset specific items only
-- ============================================================================

-- Reset items 13 and 6 specifically
-- BEGIN;
--
-- UPDATE worklist_items
-- SET
--     status = 'pending',
--     updated_at = NOW()
-- WHERE id IN (13, 6);
--
-- COMMIT;

-- ============================================================================
-- Monitoring queries
-- ============================================================================

-- Check item progression every few minutes
SELECT
    id,
    title,
    status,
    updated_at,
    EXTRACT(EPOCH FROM (NOW() - updated_at)) / 60 as minutes_since_update
FROM worklist_items
WHERE id IN (13, 6)
ORDER BY id;

-- Check all pending items
SELECT COUNT(*) as pending_count
FROM worklist_items
WHERE status = 'pending';

-- Check all parsing items
SELECT COUNT(*) as parsing_count
FROM worklist_items
WHERE status = 'parsing';

-- Check status distribution
SELECT
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (NOW() - updated_at)) / 3600) as avg_hours_in_status
FROM worklist_items
GROUP BY status
ORDER BY count DESC;
