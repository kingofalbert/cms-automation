# Deployment Automation Guide

## Overview

This guide explains the automated deployment options available for the CMS Automation backend, including automatic database migration execution.

---

## Quick Start

### 1. Automated Deployment Script (Fastest) ⭐

**For production deployment**:
```bash
cd backend
export PRODUCTION_DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"
./deploy.sh production
```

**For staging deployment**:
```bash
cd backend
export STAGING_DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"
./deploy.sh staging
```

**What it does**:
1. Runs database migration (`alembic upgrade head`)
2. Deploys backend to Cloud Run
3. Verifies deployment health
4. Reports success/failure

---

## Available Automation Options

### Option 1: Deployment Script (deploy.sh)

**Best for**: Manual deployments with full control

**Features**:
- ✅ Automatic migration execution
- ✅ Environment-specific configuration (staging/production)
- ✅ Pre-deployment migration status check
- ✅ Post-deployment verification
- ✅ Health check endpoint testing
- ✅ Error handling with early exit

**Usage**:
```bash
# Setup environment
export PRODUCTION_DATABASE_URL="your-database-url"

# Run deployment
cd backend
./deploy.sh production
```

**Script Location**: `backend/deploy.sh`

---

### Option 2: GitHub Actions CI/CD

**Best for**: Automated deployments on every push to main

**Features**:
- ✅ Triggers automatically on code push
- ✅ Runs migrations before deployment
- ✅ Zero manual intervention
- ✅ Deployment history tracking
- ✅ Rollback capability

**Setup**:
1. Add secrets to GitHub repository:
   - `DATABASE_URL`: Production database connection string

2. Push to main branch:
```bash
git push origin main
```

3. Monitor deployment in GitHub Actions tab

**Workflow File**: `.github/workflows/deploy-backend.yml`

---

### Option 3: Cloud Run with Migration Command

**Best for**: Ensuring migrations run on every Cloud Run deployment

**Features**:
- ✅ Migration runs before server starts
- ✅ Deployment fails if migration fails
- ✅ No separate migration step needed
- ✅ Atomic deployment (all or nothing)

**Usage**:
```bash
gcloud run deploy cms-automation-backend \
  --source . \
  --region us-east1 \
  --platform managed \
  --command="sh,-c,alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8080"
```

**Note**: Requires Cloud SQL proxy configuration for database access during deployment.

---

## Comparison Table

| Method | Automation Level | Effort | Best For |
|--------|-----------------|--------|----------|
| **deploy.sh script** | Semi-automated | Low | One-time deployments |
| **GitHub Actions** | Fully automated | Medium | Continuous deployment |
| **Cloud Run command** | Fully automated | Low | Simple deployments |
| **Manual (Alembic)** | Manual | High | Fine-grained control |

---

## Environment Configuration

### Required Environment Variables

**For production**:
```bash
export PRODUCTION_DATABASE_URL="postgresql+asyncpg://user:pass@prod-host:5432/cms_automation"
```

**For staging**:
```bash
export STAGING_DATABASE_URL="postgresql+asyncpg://user:pass@staging-host:5432/cms_automation_staging"
```

### Database URL Format

**Supabase**:
```
postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres
```

**Cloud SQL (with proxy)**:
```
postgresql+asyncpg://user:password@localhost:5432/dbname
```

---

## Migration Safety

All automation methods include these safety measures:

1. **Pre-deployment checks**:
   - Verify migration status before applying
   - Check database connectivity

2. **Atomic operations**:
   - Migration succeeds or deployment fails
   - No partial deployments

3. **Verification steps**:
   - Post-migration status check
   - Enum value validation
   - Data migration verification

4. **Rollback capability**:
   - All methods support `alembic downgrade -1`
   - Can revert to previous state if needed

---

## Troubleshooting

### Error: "Could not connect to database"

**Cause**: Database URL incorrect or database unreachable

**Solution**:
```bash
# Test database connection
psql "$PRODUCTION_DATABASE_URL"

# Or use Python
python -c "from sqlalchemy import create_engine; engine = create_engine('$PRODUCTION_DATABASE_URL'); print('Connected!')"
```

### Error: "Migration already applied"

**Cause**: Migration script already ran

**Solution**:
```bash
# Check current migration status
alembic current

# Show migration history
alembic history

# If needed, mark migration as applied without running
alembic stamp head
```

### Error: "Enum value already exists"

**Cause**: PostgreSQL enum values cannot be added twice

**Solution**: This is expected behavior. The migration uses `IF NOT EXISTS` to handle this gracefully. No action needed.

---

## Best Practices

### 1. Test in Staging First

Always test deployments in staging before production:

```bash
# Deploy to staging
./deploy.sh staging

# Verify everything works
# Then deploy to production
./deploy.sh production
```

### 2. Backup Before Migration

Create database backup before running migrations:

```bash
# For Supabase
supabase db dump > backup_$(date +%Y%m%d_%H%M%S).sql

# For Cloud SQL
gcloud sql export sql INSTANCE_NAME gs://BUCKET/backup.sql \
  --database=DATABASE_NAME
```

### 3. Monitor Deployment

Watch logs during deployment:

```bash
# Cloud Run logs
gcloud run services logs tail cms-automation-backend \
  --region=us-east1

# Migration logs
alembic upgrade head --sql > migration.sql  # Preview SQL
```

### 4. Verify After Deployment

Run verification checklist after deployment:

```bash
# Check backend health
curl https://your-backend-url.run.app/health

# Check database migration
psql "$DATABASE_URL" -c "SELECT unnest(enum_range(NULL::workliststatus));"

# Check data migration
psql "$DATABASE_URL" -c "SELECT status, COUNT(*) FROM worklist_items GROUP BY status;"
```

---

## Summary

**Answer to "能自动运行数据库迁移吗？"**:

**Yes!** You have 3 automated options:

1. **✅ deploy.sh script** (Recommended): One-command deployment with automatic migration
2. **✅ GitHub Actions**: Fully automated CI/CD on every push
3. **✅ Cloud Run command**: Migration runs automatically on deployment

**Quickest Option**:
```bash
cd backend
export PRODUCTION_DATABASE_URL="your-database-url"
./deploy.sh production
```

This runs the migration automatically before deploying the backend, with built-in verification and error handling.

---

## Additional Resources

- **Deployment Checklist**: `DEPLOYMENT_CHECKLIST.md`
- **Migration Guide**: `backend/MIGRATION_GUIDE.md`
- **Migration Script**: `backend/migrations/versions/20251110_1000_extend_worklist_status.py`
- **Deploy Script**: `backend/deploy.sh`
- **GitHub Workflow**: `.github/workflows/deploy-backend.yml`

---

Generated: 2025-11-10
