# SEO Title Feature - Deployment Guide

## Overview

This guide covers deploying the SEO Title feature from development to production environments. The feature adds SEO Title optimization capabilities separate from H1 titles.

## Prerequisites

### Required Access
- [ ] Production database access (PostgreSQL)
- [ ] Backend deployment permissions (Cloud Run / server SSH)
- [ ] Frontend deployment permissions (GCS bucket / CDN)
- [ ] WordPress admin access (Yoast SEO configuration)

### Required Tools
```bash
# Backend
poetry --version    # Python dependency management
alembic --version   # Database migrations
psql --version      # PostgreSQL client

# Frontend
node --version      # v18+
npm --version       # v9+

# Cloud (if applicable)
gcloud --version    # Google Cloud SDK
```

### Environment Variables

**Backend (.env or Cloud Run environment):**
```bash
# Existing
DATABASE_URL=postgresql://...
CMS_BASE_URL=https://your-wordpress-site.com
CMS_USERNAME=your-wp-admin
CMS_APPLICATION_PASSWORD=xxxx xxxx xxxx xxxx

# Optional - SEO Plugin Selection (default: yoast)
CMS_SEO_PLUGIN=yoast  # or rankmath, aioseo
```

**Frontend (.env):**
```bash
REACT_APP_API_URL=https://your-backend-api.com/api/v1
```

## Pre-Deployment Checklist

### 1. Code Review
- [ ] All Phase 1-5 changes merged to main branch
- [ ] No merge conflicts
- [ ] All tests pass locally
  ```bash
  cd backend
  poetry run python test_seo_title_api.py
  ```

### 2. Database Backup
```bash
# Backup production database
pg_dump "$PRODUCTION_DATABASE_URL" > \
  backup_pre_seo_title_$(date +%Y%m%d_%H%M%S).sql

# Verify backup file created
ls -lh backup_pre_seo_title_*.sql
```

### 3. Migration Dry Run
```bash
# Connect to production database (READ-ONLY)
psql "$PRODUCTION_DATABASE_URL" -c "SELECT version();"

# Check current migration version
cd backend
poetry run alembic current

# Show pending migrations
poetry run alembic history
```

### 4. Dependency Check
```bash
# Backend dependencies
cd backend
poetry check
poetry install --no-dev  # Verify production install works

# Frontend dependencies
cd frontend
npm ci  # Clean install from package-lock.json
npm run build  # Verify build succeeds
```

## Deployment Steps

### Step 1: Deploy Database Migrations

**1.1 Connect to Production Database**
```bash
# Set production database URL
export DATABASE_URL="$PRODUCTION_DATABASE_URL"

# Verify connection
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM articles;"
```

**1.2 Run Migrations**
```bash
cd backend

# Dry run - show SQL that will execute
poetry run alembic upgrade head --sql > migration_preview.sql
cat migration_preview.sql

# Execute migrations
poetry run alembic upgrade head

# Verify migration applied
poetry run alembic current
# Expected output: 20251114_1401 (head)
```

**1.3 Verify Database Changes**
```bash
# Check articles table columns
psql "$DATABASE_URL" -c "
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'articles'
  AND column_name LIKE 'seo_title%'
ORDER BY ordinal_position;
"

# Expected output:
#  column_name        | data_type         | is_nullable
# --------------------+-------------------+-------------
#  seo_title          | character varying | YES
#  seo_title_extracted| boolean           | NO
#  seo_title_source   | character varying | YES

# Check title_suggestions table
psql "$DATABASE_URL" -c "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'title_suggestions'
  AND column_name = 'suggested_seo_titles';
"

# Expected: suggested_seo_titles | jsonb
```

**1.4 Verify Data Migration**
```bash
# Check if existing articles have seo_title populated
psql "$DATABASE_URL" -c "
SELECT
  COUNT(*) as total_articles,
  COUNT(seo_title) as with_seo_title,
  COUNT(CASE WHEN seo_title_source = 'migrated' THEN 1 END) as migrated
FROM articles;
"

# Expected: All existing articles should have seo_title = title_main, source = 'migrated'
```

### Step 2: Deploy Backend API

#### Option A: Google Cloud Run

**2.1 Prepare Deployment**
```bash
cd backend

# Ensure Dockerfile includes all changes
git pull origin main

# Check if migration files are in repo
ls migrations/versions/*seo_title*.py
```

**2.2 Build and Deploy**
```bash
# Set project and region
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region YOUR_REGION

# Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/cms-backend:seo-title

# Deploy to Cloud Run
gcloud run deploy cms-backend \
  --image gcr.io/YOUR_PROJECT_ID/cms-backend:seo-title \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL="$DATABASE_URL" \
  --set-env-vars CMS_BASE_URL="https://your-wordpress.com" \
  --set-env-vars CMS_USERNAME="admin" \
  --set-secrets CMS_APPLICATION_PASSWORD=cms-wp-password:latest

# Get deployed URL
gcloud run services describe cms-backend --format='value(status.url)'
```

**2.3 Verify Deployment**
```bash
BACKEND_URL=$(gcloud run services describe cms-backend --format='value(status.url)')

# Health check
curl "$BACKEND_URL/health"

# Check API endpoint exists
curl -X OPTIONS "$BACKEND_URL/api/v1/optimization/articles/1/select-seo-title"
# Expected: 200 OK (or 405 Method Not Allowed is fine, means endpoint exists)
```

#### Option B: Traditional Server

**2.1 Deploy Code**
```bash
# SSH to production server
ssh user@your-server.com

# Pull latest code
cd /var/www/cms_automation/backend
git pull origin main

# Install dependencies
poetry install --no-dev

# Run migrations
poetry run alembic upgrade head
```

**2.2 Restart Service**
```bash
# Systemd
sudo systemctl restart cms-backend.service
sudo systemctl status cms-backend.service

# Or PM2
pm2 restart cms-backend
pm2 logs cms-backend --lines 50

# Or Docker
docker-compose down
docker-compose up -d --build
```

**2.3 Verify**
```bash
# Check logs
tail -f /var/log/cms-backend/app.log

# Test API
curl http://localhost:8000/health
```

### Step 3: Deploy Frontend

**3.1 Update Environment Variables**
```bash
cd frontend

# Create production .env file
cat > .env.production << EOF
REACT_APP_API_URL=https://your-backend-api.com/api/v1
REACT_APP_ENVIRONMENT=production
EOF
```

**3.2 Build Frontend**
```bash
# Install dependencies
npm ci

# Build for production
NODE_ENV=production npm run build

# Verify build output
ls -lh dist/
# Should contain: index.html, assets/, etc.
```

**3.3 Deploy to GCS (Google Cloud Storage)**
```bash
# Set bucket name
BUCKET_NAME="cms-automation-frontend-2025"

# Sync build to GCS
gsutil -m rsync -r -d dist/ "gs://$BUCKET_NAME/"

# Set cache headers
gsutil -m setmeta -h "Cache-Control:public, max-age=3600" \
  "gs://$BUCKET_NAME/assets/**"

# Verify files uploaded
gsutil ls -lh "gs://$BUCKET_NAME/"
```

**3.4 Clear CDN Cache (if using Cloud CDN)**
```bash
# Invalidate all cached files
gcloud compute url-maps invalidate-cdn-cache cms-frontend-lb \
  --path "/*" \
  --async

# Or specific files only
gcloud compute url-maps invalidate-cdn-cache cms-frontend-lb \
  --path "/index.html" \
  --path "/assets/main.*.js" \
  --async
```

**3.5 Verify Frontend Deployment**
```bash
# Open in browser
open "https://your-frontend-domain.com"

# Check build version (in browser console)
# Should show latest commit hash or version number

# Test SEOTitleSelectionCard component
# 1. Navigate to Article Review page
# 2. Verify SEO Title card appears
# 3. Check for console errors
```

### Step 4: WordPress Configuration

**4.1 Verify Yoast SEO Plugin**
```bash
# Login to WordPress admin
open "https://your-wordpress.com/wp-admin"

# Navigate to: Plugins > Installed Plugins
# Verify: "Yoast SEO" is installed and activated
# Version: 15.0+ recommended
```

**4.2 Test SEO Field Selectors**

Create a test article manually and inspect Yoast SEO fields:

```javascript
// In browser console on WordPress editor page
document.querySelector("input[name='yoast_wpseo_title']")
// Should return: <input> element

document.querySelector("textarea[name='yoast_wpseo_metadesc']")
// Should return: <textarea> element
```

If selectors don't match, update backend config:

```python
# backend/src/services/providers/playwright_wordpress_publisher.py
# Update selectors to match your Yoast version
"seo_title_field": "input[name='yoast_wpseo_title']"  # Adjust if needed
```

**4.3 Configure WordPress API (if not already done)**
```bash
# Navigate to: Users > Profile > Application Passwords
# Create new application password: "CMS Automation"
# Copy generated password (format: xxxx xxxx xxxx xxxx)

# Update backend environment variable
gcloud secrets create cms-wp-password \
  --data-file=- <<< "YOUR_APPLICATION_PASSWORD"

# Or for traditional server
# Add to .env: CMS_APPLICATION_PASSWORD=xxxx xxxx xxxx xxxx
```

### Step 5: End-to-End Verification

**5.1 Test Complete Workflow**

```bash
# Test script for E2E verification
cat > test_e2e_seo_title.sh << 'EOF'
#!/bin/bash
set -e

BACKEND_URL="https://your-backend-api.com"
ARTICLE_ID=1  # Use an actual article ID

echo "=== Step 1: Check article data ==="
curl -s "$BACKEND_URL/api/v1/articles/$ARTICLE_ID" | jq '.seo_title, .seo_title_source'

echo -e "\n=== Step 2: Get optimizations ==="
curl -s "$BACKEND_URL/api/v1/optimization/articles/$ARTICLE_ID/optimizations" \
  | jq '.title_suggestions.seo_title_suggestions.variants[0]'

echo -e "\n=== Step 3: Select SEO Title (variant) ==="
VARIANT_ID=$(curl -s "$BACKEND_URL/api/v1/optimization/articles/$ARTICLE_ID/optimizations" \
  | jq -r '.title_suggestions.seo_title_suggestions.variants[0].id')

curl -X POST "$BACKEND_URL/api/v1/optimization/articles/$ARTICLE_ID/select-seo-title" \
  -H "Content-Type: application/json" \
  -d "{\"variant_id\": \"$VARIANT_ID\"}" \
  | jq '.'

echo -e "\n=== Step 4: Verify update ==="
curl -s "$BACKEND_URL/api/v1/articles/$ARTICLE_ID" | jq '{
  seo_title: .seo_title,
  seo_title_source: .seo_title_source,
  updated_at: .updated_at
}'

echo -e "\n✅ E2E test completed"
EOF

chmod +x test_e2e_seo_title.sh
./test_e2e_seo_title.sh
```

**5.2 Test WordPress Publishing**

```bash
# Create test publish task
curl -X POST "$BACKEND_URL/api/v1/publish/submit/$ARTICLE_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "playwright",
    "publish_mode": "draft"
  }' | jq '.task_id'

# Monitor task progress
TASK_ID=<from_above>
watch -n 2 "curl -s $BACKEND_URL/api/v1/publish/tasks/$TASK_ID | jq '.status, .progress'"

# Check logs for SEO Title configuration
# Look for: "seo_title_configured" and "using_optimized_seo_title"
```

**5.3 Verify in WordPress**

1. Login to WordPress admin
2. Navigate to: Posts > All Posts
3. Find the published draft article
4. Open for editing
5. Scroll to Yoast SEO panel
6. Verify:
   - [ ] SEO Title field is filled with `article.seo_title`
   - [ ] Post Title (H1) is `article.title`
   - [ ] Meta Description is filled

**5.4 Frontend Integration Test**

1. Open frontend: `https://your-frontend-domain.com`
2. Navigate to an article in review
3. Verify SEOTitleSelectionCard displays:
   - [ ] Current SEO Title (if any)
   - [ ] Original extracted title (if applicable)
   - [ ] AI-generated variants (if optimizations run)
   - [ ] Custom input option
4. Select an AI variant
5. Verify success message appears
6. Refresh page - SEO Title should persist

## Post-Deployment Validation

### 1. Database Health Check
```sql
-- Check SEO Title distribution
SELECT
  seo_title_source,
  COUNT(*) as count,
  ROUND(AVG(LENGTH(seo_title)), 1) as avg_length
FROM articles
WHERE seo_title IS NOT NULL
GROUP BY seo_title_source
ORDER BY count DESC;

-- Expected results:
-- seo_title_source | count | avg_length
-- -----------------+-------+------------
-- migrated         | 1000  | 35.2
-- ai_generated     | 50    | 28.5
-- user_input       | 20    | 32.1
-- extracted        | 10    | 29.8
```

### 2. API Monitoring
```bash
# Check API response times
curl -w "@-" -o /dev/null -s "$BACKEND_URL/api/v1/articles/1" <<< '
time_namelookup:  %{time_namelookup}\n
time_connect:     %{time_connect}\n
time_appconnect:  %{time_appconnect}\n
time_pretransfer: %{time_pretransfer}\n
time_starttransfer: %{time_starttransfer}\n
time_total:       %{time_total}\n
'

# Expected: time_total < 1 second
```

### 3. Error Monitoring
```bash
# Cloud Run (GCP)
gcloud logging read "resource.type=cloud_run_revision \
  AND severity>=ERROR \
  AND textPayload=~'seo_title'" \
  --limit 50 \
  --format json

# Traditional server
grep -i "seo_title.*error" /var/log/cms-backend/app.log | tail -20
```

### 4. Frontend Analytics
```javascript
// Add to frontend analytics tracking
window.analytics?.track('SEO Title Selected', {
  source: 'ai_generated',  // or 'user_input', 'extracted'
  article_id: 123,
  character_count: 28
});

// Monitor in Google Analytics or your analytics platform
```

## Rollback Procedures

### Scenario 1: Database Migration Failed

**Symptoms:** Migration error, database inconsistency

**Rollback:**
```bash
cd backend

# Downgrade migration
poetry run alembic downgrade -1  # Go back one version
# Or specific revision
poetry run alembic downgrade 20251114_1400  # Before SEO Title migrations

# Verify rollback
poetry run alembic current

# Restore from backup if needed
psql "$DATABASE_URL" < backup_pre_seo_title_<timestamp>.sql
```

### Scenario 2: Backend Deploy Failed

**Symptoms:** API errors, 500 responses, service won't start

**Rollback Cloud Run:**
```bash
# List revisions
gcloud run revisions list --service cms-backend

# Rollback to previous revision
PREVIOUS_REVISION="cms-backend-00042-xyz"  # From list above
gcloud run services update-traffic cms-backend \
  --to-revisions $PREVIOUS_REVISION=100

# Verify rollback
curl "$BACKEND_URL/health"
```

**Rollback Traditional Server:**
```bash
ssh user@your-server.com
cd /var/www/cms_automation/backend

# Git rollback
git log --oneline -10  # Find previous commit
git reset --hard <previous-commit-hash>

# Reinstall dependencies
poetry install --no-dev

# Downgrade migrations
poetry run alembic downgrade -1

# Restart service
sudo systemctl restart cms-backend.service
```

### Scenario 3: Frontend Issues

**Symptoms:** UI broken, component errors, blank page

**Rollback GCS:**
```bash
# List previous versions (if versioning enabled)
gsutil ls -a "gs://$BUCKET_NAME/"

# Restore previous version
PREVIOUS_VERSION="gs://$BUCKET_NAME/index.html#1234567890"
gsutil cp $PREVIOUS_VERSION "gs://$BUCKET_NAME/index.html"

# Or re-deploy from git
git checkout <previous-commit>
npm run build
gsutil -m rsync -r -d dist/ "gs://$BUCKET_NAME/"

# Clear CDN cache
gcloud compute url-maps invalidate-cdn-cache cms-frontend-lb --path "/*"
```

### Scenario 4: WordPress Integration Broken

**Symptoms:** SEO fields not filling, Playwright errors

**Quick Fix:**
```bash
# Disable SEO field configuration temporarily
# Update environment variable
gcloud run services update cms-backend \
  --set-env-vars SKIP_SEO_CONFIGURATION=true

# Or in code, add safety check
# backend/src/services/providers/playwright_wordpress_publisher.py
async def _step_configure_seo(self, seo_data: SEOMetadata) -> None:
    if os.getenv("SKIP_SEO_CONFIGURATION") == "true":
        logger.warning("SEO configuration skipped via environment variable")
        return
    # ... rest of method
```

**Long-term Fix:**
- Update Yoast SEO selectors to match current version
- Test in staging environment first
- Redeploy with fix

## Monitoring and Alerts

### Key Metrics to Monitor

**1. SEO Title Usage**
```sql
-- Daily query to track adoption
SELECT
  DATE(updated_at) as date,
  seo_title_source,
  COUNT(*) as articles_updated
FROM articles
WHERE updated_at >= CURRENT_DATE - INTERVAL '7 days'
  AND seo_title_source IS NOT NULL
GROUP BY DATE(updated_at), seo_title_source
ORDER BY date DESC;
```

**2. API Errors**
```bash
# Alert if > 10 errors in 5 minutes
gcloud logging read "
  resource.type=cloud_run_revision
  AND severity>=ERROR
  AND (textPayload=~'select-seo-title' OR jsonPayload.message=~'seo_title')
  AND timestamp>='$(date -u -d '5 minutes ago' '+%Y-%m-%dT%H:%M:%SZ')'
" --limit 1000 --format json | jq length
```

**3. WordPress Publishing Success Rate**
```sql
-- Track SEO Title configuration success
SELECT
  DATE(created_at) as date,
  COUNT(*) as total_tasks,
  COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful,
  ROUND(
    100.0 * COUNT(CASE WHEN status = 'completed' THEN 1 END) / COUNT(*),
    2
  ) as success_rate
FROM publish_tasks
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
  AND provider = 'playwright'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Recommended Alerts

**1. Cloud Monitoring (GCP) Alerts**
```bash
# Create alert for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="SEO Title API Errors" \
  --condition-display-name="Error rate > 5%" \
  --condition-expression='
    resource.type="cloud_run_revision" AND
    severity="ERROR" AND
    textPayload=~"select-seo-title"
  ' \
  --condition-threshold-value=0.05 \
  --condition-duration=300s
```

**2. Database Query Performance**
```sql
-- Monitor slow queries
SELECT
  query,
  calls,
  mean_exec_time,
  max_exec_time
FROM pg_stat_statements
WHERE query LIKE '%seo_title%'
  AND mean_exec_time > 100  -- ms
ORDER BY mean_exec_time DESC;
```

**3. Frontend Error Tracking**

Integrate with Sentry or similar:

```typescript
// frontend/src/components/ArticleReview/SEOTitleSelectionCard.tsx
import * as Sentry from "@sentry/react";

const handleSelectSeoTitle = async () => {
  try {
    // ... API call
  } catch (error) {
    Sentry.captureException(error, {
      tags: { feature: 'seo_title_selection' },
      extra: { articleId, selectedVariantId }
    });
    onError?.(error.message);
  }
};
```

## Maintenance

### Regular Tasks

**Weekly:**
- [ ] Review SEO Title usage metrics
- [ ] Check error logs for "seo_title" related issues
- [ ] Verify WordPress publishing success rate

**Monthly:**
- [ ] Analyze SEO Title length distribution
- [ ] Review AI variant selection vs custom input ratio
- [ ] Database cleanup (remove old suggested_seo_titles if storage limited)

**Quarterly:**
- [ ] Update Yoast SEO plugin and verify selector compatibility
- [ ] Review and optimize JSONB queries if performance degrades
- [ ] A/B test SEO Title effectiveness (if analytics integrated)

### Database Maintenance

**Cleanup Old Suggestions (Optional):**
```sql
-- Remove SEO suggestions older than 6 months for completed articles
UPDATE title_suggestions
SET suggested_seo_titles = NULL
WHERE article_id IN (
  SELECT id FROM articles
  WHERE status = 'published'
    AND published_at < CURRENT_DATE - INTERVAL '6 months'
);
```

**Vacuum JSONB Columns:**
```sql
-- Reclaim space after cleanup
VACUUM ANALYZE title_suggestions;
```

## Troubleshooting Common Issues

### Issue: "Migration already applied" error

**Cause:** Migration run multiple times or manual table changes

**Fix:**
```bash
# Mark migration as applied without running
poetry run alembic stamp head

# Or specific revision
poetry run alembic stamp 20251114_1401
```

### Issue: Yoast SEO fields not filling

**Diagnosis:**
```bash
# Check Playwright logs
gcloud logging read "
  resource.type=cloud_run_revision
  AND textPayload=~'seo_title_configured'
" --limit 10

# Check for selector errors
gcloud logging read "
  resource.type=cloud_run_revision
  AND severity=WARNING
  AND textPayload=~'seo_configuration_failed'
" --limit 10
```

**Fix:**
1. Verify Yoast SEO version compatibility
2. Inspect WordPress editor page source for correct selectors
3. Update `seo_title_field` in playwright_wordpress_publisher.py
4. Redeploy backend

### Issue: Frontend 404 on API calls

**Diagnosis:**
```bash
# Check CORS configuration
curl -I -X OPTIONS "$BACKEND_URL/api/v1/optimization/articles/1/select-seo-title" \
  -H "Origin: https://your-frontend-domain.com"

# Should return:
# Access-Control-Allow-Origin: https://your-frontend-domain.com
# Access-Control-Allow-Methods: POST, OPTIONS
```

**Fix:**
```python
# backend/src/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Success Criteria

### Deployment Successful When:

- [ ] All database migrations applied successfully
- [ ] Backend API `/select-seo-title` endpoint returns 200 OK
- [ ] Frontend SEOTitleSelectionCard renders without errors
- [ ] WordPress publishing fills Yoast SEO Title field
- [ ] Logs show "using_optimized_seo_title" and "seo_title_configured"
- [ ] No increase in error rate compared to baseline
- [ ] Published articles have correct SEO Title in page source

### Performance Benchmarks:

- [ ] `/select-seo-title` API response time < 500ms
- [ ] Frontend component load time < 200ms
- [ ] WordPress SEO field filling adds < 2s to publish time
- [ ] Database queries on `seo_title` columns < 100ms

## Support and Escalation

### Contact Information

**Technical Issues:**
- Backend API: [backend-team@example.com]
- Frontend: [frontend-team@example.com]
- Database: [dba-team@example.com]
- DevOps: [devops-team@example.com]

**Escalation Path:**
1. Check this deployment guide and main documentation
2. Review logs and error messages
3. Contact technical team via email/Slack
4. If critical (site down), page on-call engineer

---

**Document Version:** 1.0
**Last Updated:** 2025-11-14
**Deployment Date:** [TO BE FILLED]
**Deployed By:** [TO BE FILLED]
