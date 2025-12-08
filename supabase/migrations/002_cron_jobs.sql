-- ============================================================
-- Internal Link System - Cron Jobs Configuration
-- Version: 2.0
-- Date: 2025-12-07
--
-- V2 Changes:
-- - Renamed extract-keywords to parse-articles (unified AI parsing)
-- - Processing flow: scraped -> parsed -> embedded -> ready
--
-- NOTE: pg_cron requires Supabase Pro plan or self-hosted instance
-- For free tier, use external schedulers (GitHub Actions, Vercel Cron, etc.)
-- ============================================================

-- ============================================================
-- IMPORTANT: Replace 'your-project' with your actual Supabase project ID
-- Replace the service_role_key with your actual key
-- ============================================================

-- Store service role key in a secure configuration
-- This should be done via Supabase Dashboard > SQL Editor
-- DO NOT commit actual keys to version control!

-- Example (replace with actual values in Supabase Dashboard):
-- alter database postgres set app.settings.service_role_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
-- alter database postgres set app.settings.supabase_url = 'https://your-project.supabase.co';

-- ============================================================
-- Cron Job 1: Daily Article Scraping (2:00 AM UTC)
-- ============================================================

select cron.schedule(
    'daily-scrape-health-articles',
    '0 2 * * *',  -- Every day at 2:00 AM UTC
    $$
    select net.http_post(
        url := current_setting('app.settings.supabase_url') || '/functions/v1/scrape-health-articles',
        headers := jsonb_build_object(
            'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key'),
            'Content-Type', 'application/json'
        ),
        body := '{"incrementalOnly": true, "maxPages": 10}'::jsonb,
        timeout_milliseconds := 300000  -- 5 minute timeout
    );
    $$
);

-- ============================================================
-- Cron Job 2: AI Article Parsing (2:30 AM UTC)
-- V2: Renamed from extract-keywords to parse-articles
-- Now handles: title decomposition, keywords, author cleaning, category validation
-- ============================================================

select cron.schedule(
    'daily-parse-articles',
    '30 2 * * *',  -- Every day at 2:30 AM UTC
    $$
    select net.http_post(
        url := current_setting('app.settings.supabase_url') || '/functions/v1/parse-articles',
        headers := jsonb_build_object(
            'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key'),
            'Content-Type', 'application/json'
        ),
        body := '{"batchSize": 10}'::jsonb,  -- Smaller batch for AI parsing
        timeout_milliseconds := 180000  -- 3 minute timeout (AI takes longer)
    );
    $$
);

-- ============================================================
-- Cron Job 3: Embedding Generation (3:00 AM UTC)
-- ============================================================

select cron.schedule(
    'daily-generate-embeddings',
    '0 3 * * *',  -- Every day at 3:00 AM UTC
    $$
    select net.http_post(
        url := current_setting('app.settings.supabase_url') || '/functions/v1/generate-embeddings',
        headers := jsonb_build_object(
            'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key'),
            'Content-Type', 'application/json'
        ),
        body := '{"batchSize": 100}'::jsonb,
        timeout_milliseconds := 180000  -- 3 minute timeout
    );
    $$
);

-- ============================================================
-- Additional Helper Jobs
-- ============================================================

-- Weekly cleanup of old job records (keep last 30 days)
select cron.schedule(
    'weekly-cleanup-old-jobs',
    '0 4 * * 0',  -- Every Sunday at 4:00 AM UTC
    $$
    delete from public.scrape_jobs
    where started_at < now() - interval '30 days';
    $$
);

-- ============================================================
-- Management Queries
-- ============================================================

-- View all scheduled jobs
-- select * from cron.job;

-- View job execution history
-- select * from cron.job_run_details order by start_time desc limit 20;

-- Unschedule a job
-- select cron.unschedule('daily-scrape-health-articles');

-- Manually trigger a job (for testing)
-- select cron.schedule('manual-scrape-test', 'now', $$
--     select net.http_post(
--         url := current_setting('app.settings.supabase_url') || '/functions/v1/scrape-health-articles',
--         headers := jsonb_build_object(
--             'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key'),
--             'Content-Type', 'application/json'
--         ),
--         body := '{"incrementalOnly": false, "maxPages": 2}'::jsonb,
--         timeout_milliseconds := 60000
--     );
-- $$);

-- ============================================================
-- Alternative: External Scheduler Setup (for Free Tier)
-- ============================================================

-- If using Supabase Free tier without pg_cron, set up external schedulers:
--
-- Option 1: GitHub Actions
-- Create .github/workflows/internal-links-cron.yml:
-- ```yaml
-- name: Internal Links Daily Processing
-- on:
--   schedule:
--     - cron: '0 2 * * *'  # 2 AM UTC
--   workflow_dispatch:
--
-- jobs:
--   process:
--     runs-on: ubuntu-latest
--     steps:
--       - name: Scrape Articles
--         run: |
--           curl -X POST "${{ secrets.SUPABASE_URL }}/functions/v1/scrape-health-articles" \
--             -H "Authorization: Bearer ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}" \
--             -H "Content-Type: application/json" \
--             -d '{"incrementalOnly": true}'
--       - name: Wait 30 minutes
--         run: sleep 1800
--       - name: Parse Articles (AI Enhancement)
--         run: |
--           curl -X POST "${{ secrets.SUPABASE_URL }}/functions/v1/parse-articles" \
--             -H "Authorization: Bearer ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}" \
--             -H "Content-Type: application/json" \
--             -d '{"batchSize": 10}'
--       - name: Wait 30 minutes
--         run: sleep 1800
--       - name: Generate Embeddings
--         run: |
--           curl -X POST "${{ secrets.SUPABASE_URL }}/functions/v1/generate-embeddings" \
--             -H "Authorization: Bearer ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}" \
--             -H "Content-Type: application/json" \
--             -d '{"batchSize": 100}'
-- ```
--
-- Option 2: Vercel Cron
-- Add to vercel.json:
-- ```json
-- {
--   "crons": [
--     {
--       "path": "/api/cron/scrape",
--       "schedule": "0 2 * * *"
--     }
--   ]
-- }
-- ```
