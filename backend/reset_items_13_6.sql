-- ============================================================================
-- 重置卡住的文件 (Item 13 和 6)
-- ============================================================================
-- 执行位置: Supabase Dashboard > SQL Editor
-- 链接: https://supabase.com/dashboard/project/twsbhjmlmspjwfystpti
-- ============================================================================

-- 步骤 1: 查看当前状态
SELECT
    id,
    title,
    status,
    created_at,
    updated_at,
    AGE(NOW(), updated_at) as stuck_duration
FROM worklist_items
WHERE id IN (13, 6)
ORDER BY id;

-- 步骤 2: 重置为 pending 状态
-- (这会触发系统重新处理这些文件)
BEGIN;

UPDATE worklist_items
SET
    status = 'pending',
    updated_at = NOW()
WHERE id IN (13, 6);

COMMIT;

-- 步骤 3: 验证重置成功
SELECT
    id,
    title,
    status,
    updated_at,
    updated_at > NOW() - INTERVAL '1 minute' as just_updated
FROM worklist_items
WHERE id IN (13, 6)
ORDER BY id;

-- 预期结果:
-- - status 应该是 'pending'
-- - just_updated 应该是 't' (true)
-- ============================================================================
