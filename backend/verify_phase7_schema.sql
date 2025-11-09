-- Verification script for Phase 7 database schema
-- Run this in Supabase SQL Editor to verify migrations

-- 1. Check articles table for Phase 7 fields
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'articles'
AND column_name IN (
    'title_prefix', 'title_main', 'title_suffix',
    'author_line', 'author_name', 'body_html',
    'meta_description', 'seo_keywords',
    'parsing_confirmed', 'parsing_confirmed_at', 'parsing_confirmed_by', 'parsing_feedback'
)
ORDER BY column_name;

-- 2. Verify article_images table exists
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'article_images'
ORDER BY ordinal_position;

-- 3. Verify article_image_reviews table exists
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'article_image_reviews'
ORDER BY ordinal_position;

-- 4. Check indexes
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE tablename IN ('articles', 'article_images', 'article_image_reviews')
AND indexname LIKE '%parsing%' OR indexname LIKE '%article_image%'
ORDER BY tablename, indexname;

-- 5. Check current Alembic version
SELECT version_num FROM alembic_version;

-- Expected result: 20251108_1700
