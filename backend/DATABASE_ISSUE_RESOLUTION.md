# Database Connectivity Issue - Complete Resolution

**Date**: 2025-11-07
**Status**: ✅ RESOLVED
**Impact**: Production database timeouts completely fixed

---

## Problem Summary

After clearing browser cache, the homepage and worklist pages were extremely slow or not loading at all. Database-related API endpoints were timing out after 10+ seconds.

### Symptoms
- Frontend loaded normally (768ms)
- Non-database endpoints (`/`, `/health`) worked fine
- All database-related endpoints timed out (>10 seconds)
- Error: `MaxClientsInSessionMode: max clients reached - in Session mode max clients are limited to pool_size`

---

## Root Cause Analysis

### Discovery Process

1. **Created Playwright diagnostic tests** to measure frontend performance
   - Result: Frontend loads fast, but NO API calls being made

2. **Added debug endpoints** to test database connectivity from Cloud Run
   - `/debug/db-test` - Simple `SELECT 1` query
   - `/debug/db-worklist-count` - Test worklist table query

3. **Deployed debug endpoints** and tested
   - Result: **15.3 second timeout** with error:
     ```
     MaxClientsInSessionMode: max clients reached - in Session mode
     max clients are limited to pool_size
     ```

### Root Cause

**Supabase connection pooler was configured in Session mode (port 5432) instead of Transaction mode (port 6543).**

#### About Supabase Pooler Modes

| Mode | Port | Max Clients | Use Case |
|------|------|-------------|----------|
| **Session** | 5432 | Limited to `pool_size` (15-20) | Long-lived connections, single-tenant apps |
| **Transaction** | 6543 | Much higher limits (1000+) | Multi-instance apps like Cloud Run |

#### Why Session Mode Failed

- Cloud Run auto-scales to multiple instances
- Each instance creates its own connection pool (pool_size = 20)
- Multiple instances × 20 connections = Exceeds Session mode limit
- Result: New connections rejected with `MaxClientsInSessionMode` error

---

## Solution Implemented

### 1. Update DATABASE_URL Secret

Changed Supabase connection pooler from Session mode to Transaction mode:

```bash
# Before (Session mode - port 5432)
postgresql+asyncpg://postgres.xxx:password@aws-1-us-east-1.pooler.supabase.com:5432/postgres

# After (Transaction mode - port 6543)
postgresql+asyncpg://postgres.xxx:password@aws-1-us-east-1.pooler.supabase.com:6543/postgres
```

**Script**: `scripts/fix-supabase-pooler.sh`

### 2. Redeploy Backend

Updated Cloud Run service to use the new DATABASE_URL:

```bash
gcloud run services update cms-automation-backend \
  --region=us-east1 \
  --update-secrets="DATABASE_URL=cms-automation-prod-DATABASE_URL:latest"
```

---

## Results

### Performance Comparison

| Endpoint | Before | After | Improvement |
|----------|--------|-------|-------------|
| `/debug/db-test` | 15.3s (timeout) | **0.327s** | **47x faster** |
| `/debug/db-worklist-count` | Timeout | **0.267s** | **∞** (was failing) |
| `/v1/worklist` (full API) | Timeout | **0.632s** | **∞** (was failing) |

### Verification Tests

All endpoints now working correctly:

1. **Database connection test**: ✅ 327ms
   ```json
   {
     "success": true,
     "message": "Database connection successful",
     "test_result": 1
   }
   ```

2. **Worklist count query**: ✅ 267ms
   ```json
   {
     "success": true,
     "message": "Worklist query successful",
     "count": 3
   }
   ```

3. **Full worklist API**: ✅ 632ms
   - Successfully returned 3 worklist items with complete data
   - No timeouts or errors

---

## Additional Improvements

### Migrated to Google Artifact Registry

As part of this fix, we also migrated from deprecated Google Container Registry (GCR) to Artifact Registry (GAR):

**Changes made:**
- Created Artifact Registry repository: `us-east1-docker.pkg.dev/cmsupload-476323/cms-backend`
- Updated deployment script to use new image URL format
- Configured Docker authentication: `gcloud auth configure-docker us-east1-docker.pkg.dev`
- Fixed PROJECT_ID from `cms-automation-prod` to `cmsupload-476323`

**Files modified:**
- `scripts/deployment/deploy-prod.sh` - Updated to use Artifact Registry URLs

---

## Files Created/Modified

### Created Files
1. `src/api/routes/debug_routes.py` - Debug endpoints for database testing
2. `scripts/fix-supabase-pooler.sh` - Script to update DATABASE_URL
3. `DATABASE_ISSUE_RESOLUTION.md` - This document
4. `DATABASE_TIMEOUT_DIAGNOSIS.md` - Initial diagnosis notes

### Modified Files
1. `src/api/routes/__init__.py` - Added debug_routes registration
2. `scripts/deployment/deploy-prod.sh` - Migrated to Artifact Registry

### Secret Updates
- `cms-automation-prod-DATABASE_URL` - Updated to version 4 (Transaction mode)

---

## Deployment History

| Revision | Change | Status |
|----------|--------|--------|
| 00032-fjr | Initial debug endpoints deployment | ⚠️ Failed (GCR deprecated) |
| 00033-7cr | Migrated to Artifact Registry | ✅ Success (but DB still timeout) |
| 00034-blh | Updated DATABASE_URL to Transaction mode | ✅ Success + DB fixed |

---

## Prevention Measures

### For Future Deployments

1. **Always use Transaction mode** for Supabase pooler with Cloud Run
   - Port 6543 (not 5432)
   - Handles multiple instances correctly

2. **Monitor connection pool metrics**
   ```bash
   # Check current connections
   gcloud run logs read cms-automation-backend --region us-east1 | grep "pool"
   ```

3. **Use debug endpoints** for quick diagnosis
   - `/debug/db-test` - Basic connectivity
   - `/debug/db-worklist-count` - Table query test

### Configuration Checklist

- [x] Supabase pooler: **Transaction mode (port 6543)**
- [x] SQLAlchemy pool_size: 20 (appropriate for Transaction mode)
- [x] Cloud Run min_instances: 1 (always warm)
- [x] Database connection timeout: 30 seconds
- [x] Pool pre-ping: Enabled

---

## References

- [Supabase Connection Pooling Docs](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Google Cloud Run Best Practices](https://cloud.google.com/run/docs/tips/general)
- [SQLAlchemy Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)

---

## Contact

For questions about this fix, refer to:
- This document: `backend/DATABASE_ISSUE_RESOLUTION.md`
- Debug endpoints: `/debug/db-test`, `/debug/db-worklist-count`
- Fix script: `scripts/fix-supabase-pooler.sh`
