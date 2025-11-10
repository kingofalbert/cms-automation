# Deployment Checklist - Worklist Status Extension

## Overview
This checklist guides you through deploying the extended worklist status workflow to production.

**Commits**:
- Frontend: `ecdcb43` - feat(workflow): Extend worklist status with parsing review states
- Backend: `7630c53` - feat(backend): Extend worklist status with parsing review states
- Migration Guide: `29ac5f3` - docs: Add database migration guide

**Change Summary**:
- Extended workflow from 7 to 9 states
- Added: `parsing`, `parsing_review`, `proofreading_review`
- Migrated: `under_review` → `proofreading_review`
- Smart routing: Different buttons for parsing vs proofreading review

---

## Pre-Deployment

### 1. Code Review
- [ ] Review frontend changes (commit `ecdcb43`)
  - WorklistStatus type extension
  - Smart routing logic in WorklistTable
  - WorklistDetailDrawer review buttons
  - Status badge configurations
  - Translations (zh-TW, en-US)
  
- [ ] Review backend changes (commit `7630c53`)
  - WorklistStatus enum extension
  - Pipeline service status updates
  - Parsing API route modifications
  - Database migration script

### 2. Testing (Local/Staging)
- [ ] Test frontend build: `npm run build` (should succeed with only Phase 7 warnings)
- [ ] Test backend migrations:
  ```bash
  cd backend
  alembic current
  alembic upgrade head
  alembic current  # Verify new revision
  ```
- [ ] Test worklist status flow:
  1. Create test article in `pending` status
  2. Trigger parsing → Verify status changes to `parsing_review`
  3. Confirm parsing → Verify status changes to `proofreading`
  4. After proofreading → Verify status changes to `proofreading_review`
  5. Complete review → Verify status changes to `ready_to_publish`

### 3. Database Backup
- [ ] Create production database backup
  ```bash
  # For Supabase, use dashboard or CLI
  supabase db dump > backup_before_migration_$(date +%Y%m%d_%H%M%S).sql
  ```
- [ ] Verify backup integrity
- [ ] Store backup in secure location

---

## Deployment Steps

### Step 1: Deploy Backend (Code + Migration)

#### 1.1 Deploy Backend Code
```bash
# Pull latest changes
git pull origin main

# Deploy to Cloud Run (or your backend hosting)
gcloud run deploy cms-automation-backend \
  --source . \
  --region us-east1 \
  --platform managed
```

#### 1.2 Run Database Migration

**Option A: Using Cloud SQL Proxy (Recommended)**
```bash
# Connect to production database
cloud_sql_proxy -instances=PROJECT:REGION:INSTANCE=tcp:5432

# In another terminal, run migration
cd backend
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dbname"
alembic upgrade head
```

**Option B: Direct SQL in Supabase Dashboard**
```sql
-- 1. Add new enum values
ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'parsing';
ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'parsing_review';
ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'proofreading_review';

-- 2. Migrate data
UPDATE worklist_items
SET status = 'proofreading_review'
WHERE status = 'under_review';

-- 3. Verify
SELECT status, COUNT(*) FROM worklist_items GROUP BY status;
```

#### 1.3 Verify Backend Deployment
- [ ] Check backend health endpoint: `GET /health`
- [ ] Check backend logs for errors
- [ ] Test API endpoint: `GET /v1/worklist`
  - Verify status values are returned correctly
  - Check for new `parsing_review` and `proofreading_review` statuses

---

### Step 2: Deploy Frontend

#### 2.1 Build Frontend
```bash
cd frontend
npm install
npm run build
```

**Expected**: Build should succeed (ignore Phase 7 TypeScript warnings for ArticleParsingPage variants)

#### 2.2 Deploy to GCS
```bash
# Sync to Google Cloud Storage bucket
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-cmsupload-476323/

# Verify deployment
gsutil ls -lh gs://cms-automation-frontend-cmsupload-476323/index.html
```

#### 2.3 Clear CDN Cache (if applicable)
```bash
gcloud compute url-maps invalidate-cdn-cache LOAD_BALANCER_NAME \
  --path "/*" \
  --async
```

---

### Step 3: Verification

#### 3.1 Verify Database Migration
- [ ] Connect to production database
- [ ] Check enum values:
  ```sql
  SELECT unnest(enum_range(NULL::workliststatus));
  ```
  Expected: All 10 values (including 3 new ones)

- [ ] Check data migration:
  ```sql
  SELECT status, COUNT(*) FROM worklist_items GROUP BY status;
  ```
  Expected: Zero `under_review` records

#### 3.2 Verify Backend API
- [ ] Test worklist API: `GET /v1/worklist`
  - Check status values match new enum
  - Verify no errors in response

- [ ] Test parsing API: `POST /v1/articles/{id}/parse`
  - Confirm worklist status updates to `parsing_review`

- [ ] Test confirm parsing API: `POST /v1/articles/{id}/confirm-parsing`
  - Confirm worklist status updates to `proofreading`

#### 3.3 Verify Frontend UI

**Test Scenario 1: Parsing Review**
- [ ] Navigate to Worklist page
- [ ] Find article with `parsing_review` status
- [ ] Verify "审核解析" button is displayed
- [ ] Click button → Verify routes to `/articles/{article_id}/parsing`
- [ ] Verify ArticleParsingPage loads correctly

**Test Scenario 2: Proofreading Review**
- [ ] Find article with `proofreading_review` status
- [ ] Verify "审核校对" button is displayed
- [ ] Click button → Verify routes to `/worklist/{id}/review`
- [ ] Verify ProofreadingReviewPage loads correctly

**Test Scenario 3: Backward Compatibility**
- [ ] If any `under_review` records exist (shouldn't after migration)
- [ ] Verify "审核校对" button still works
- [ ] Verify routes to correct proofreading review page

**Test Scenario 4: Status Badges**
- [ ] Check status badges display correctly:
  - `parsing` → "解析中" (blue/info badge)
  - `parsing_review` → "解析审核中" (blue/info badge)
  - `proofreading_review` → "校对审核中" (blue/info badge)

#### 3.4 End-to-End Workflow Test
- [ ] Create new article in Worklist
- [ ] Trigger article parsing
  - Verify status: `pending` → `parsing` → `parsing_review`
  - Verify "审核解析" button appears
  
- [ ] Click "审核解析", review parsing results
- [ ] Confirm parsing
  - Verify status: `parsing_review` → `proofreading`
  
- [ ] Wait for auto-proofreading to complete
  - Verify status: `proofreading` → `proofreading_review`
  - Verify "审核校对" button appears
  
- [ ] Click "审核校对", review proofreading issues
- [ ] Complete review
  - Verify status: `proofreading_review` → `ready_to_publish`

---

## Post-Deployment

### Monitoring
- [ ] Monitor backend logs for 24 hours
  - Watch for enum validation errors
  - Check for unexpected status transitions
  
- [ ] Monitor frontend analytics
  - Track button click rates for review actions
  - Verify no client-side errors

- [ ] User feedback
  - Confirm users can access both review types
  - Verify no confusion about which review button to click

### Rollback Plan (If Needed)

**Backend Rollback**:
```bash
# Rollback code deployment
gcloud run services update cms-automation-backend \
  --image PREVIOUS_IMAGE

# Rollback database (data only, enum values stay)
cd backend
alembic downgrade -1
```

**Frontend Rollback**:
```bash
# Restore previous build from git
git checkout ced83f5  # Previous commit before workflow extension
cd frontend
npm run build
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-cmsupload-476323/
```

---

## Success Criteria

✅ All checklist items completed
✅ Database migration applied successfully
✅ Backend API returns new status values
✅ Frontend displays correct review buttons based on status
✅ Routing works correctly for both review types
✅ Backward compatibility maintained (if any `under_review` records)
✅ No errors in backend logs
✅ No errors in browser console
✅ End-to-end workflow test passes

---

## Contacts

**Technical Lead**: Albert King
**Repository**: https://github.com/kingofalbert/cms-automation
**Documentation**: 
- Frontend: `frontend/README.md`
- Backend: `backend/MIGRATION_GUIDE.md`
- Migration Script: `backend/migrations/versions/20251110_1000_extend_worklist_status.py`

---

Generated: 2025-11-10
Last Updated: 2025-11-10
