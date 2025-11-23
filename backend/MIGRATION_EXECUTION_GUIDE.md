# Production Database Migration - Execution Guide

**Date**: 2025-11-23
**Priority**: 🔴 P0 - Critical
**Estimated Time**: 5-10 minutes

---

## 📋 Quick Summary

This guide provides **3 different methods** to execute the critical database migrations needed to fix the parsing status issue in production.

**What needs to be migrated:**
1. ✅ Add `parsing`, `parsing_review`, `proofreading_review` to WorklistStatus enum
2. ✅ Add `raw_html` TEXT column to `worklist_items` table

---

## 🎯 Choose Your Method

### Method 1: Direct SQL via Supabase Dashboard (Recommended - Fastest)

**Best for**: Quick execution, no command line needed

#### Steps:

1. **Open Supabase Dashboard**
   - Go to: https://supabase.com/dashboard/project/twsbhjmlmspjwfystpti
   - Navigate to: SQL Editor

2. **Run the Migration SQL**
   - Copy the contents of: `backend/migrations/manual_sql/p0_critical_migration.sql`
   - Paste into the SQL Editor
   - Click "Run" button

3. **Verify Results**
   - Check the output shows:
     - ✅ "Added enum value" or "already exists" for all 3 status values
     - ✅ "Added column: raw_html" or "already exists"
     - ✅ Migration version: 77fd4b324d80
     - ✅ raw_html column EXISTS ✓

**Time**: ~2 minutes

---

### Method 2: Using psql from Command Line

**Best for**: Database administrators familiar with PostgreSQL

#### Prerequisites:
- PostgreSQL client (`psql`) installed
- Database connection credentials

#### Steps:

1. **Set Database URL**
   ```bash
   export DATABASE_URL="postgresql://postgres.twsbhjmlmspjwfystpti:Xieping890$@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
   ```

2. **Connect and Run Migration**
   ```bash
   cd /home/kingofalbert/projects/CMS/backend
   psql $DATABASE_URL -f migrations/manual_sql/p0_critical_migration.sql
   ```

3. **Verify**
   ```bash
   psql $DATABASE_URL -c "SELECT version_num FROM alembic_version;"
   psql $DATABASE_URL -c "SELECT unnest(enum_range(NULL::workliststatus))::text as status ORDER BY status;"
   ```

**Time**: ~3 minutes

---

### Method 3: Using Python Script (via Cloud Run)

**Best for**: Running directly on the production server

#### Steps:

1. **Connect to Cloud Run Instance**
   ```bash
   gcloud run services proxy cms-automation-backend \
     --project=cmsupload-476323 \
     --region=us-east1
   ```

2. **Access Container Shell**
   ```bash
   gcloud run services execute cms-automation-backend \
     --project=cmsupload-476323 \
     --region=us-east1 \
     --command=/bin/bash
   ```

3. **Run Migration Script**
   ```bash
   cd /app
   python run_production_migration.py
   ```

4. **Check Output**
   - Should see: "🎉 ALL MIGRATIONS SUCCESSFULLY APPLIED!"

**Time**: ~5 minutes

---

### Method 4: Using Alembic (If Connection Works)

**Best for**: Standard migration workflow

#### Steps:

1. **Check Current Version**
   ```bash
   cd /home/kingofalbert/projects/CMS/backend
   source .venv/bin/activate
   alembic current
   ```

2. **Upgrade to Target Version**
   ```bash
   alembic upgrade 20251110_1000  # Add enum values
   alembic upgrade 77fd4b324d80   # Add raw_html column
   ```

3. **Verify**
   ```bash
   alembic current
   # Should show: 77fd4b324d80 or higher
   ```

**Note**: This method may fail if there are connection issues from WSL.

**Time**: ~3 minutes

---

## ✅ Post-Migration Verification

After running the migration using **any** method above, verify success:

### 1. Check Migration Version

```sql
SELECT version_num FROM alembic_version;
```

**Expected**: `77fd4b324d80` or higher

### 2. Check Enum Values

```sql
SELECT unnest(enum_range(NULL::workliststatus))::text as status
ORDER BY status;
```

**Expected to see**:
- `parsing`
- `parsing_review`
- `proofreading_review`
- ... (and other existing values)

### 3. Check Column Exists

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'worklist_items'
AND column_name = 'raw_html';
```

**Expected**:
```
column_name | data_type
------------+----------
raw_html    | text
```

### 4. Test Parsing Workflow

1. Go to your Worklist page in the frontend
2. Trigger a Google Drive sync (if available)
3. Watch for a new file to be imported
4. Verify it transitions through: `pending` → `parsing` → `parsing_review`
5. Should NOT get stuck in `parsing` anymore

### 5. Check Application Logs

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend AND severity>=ERROR" \
  --limit 20 \
  --format json
```

**Expected**: No more errors like:
- ❌ `invalid input value for enum workliststatus: "parsing"`
- ❌ `column "raw_html" does not exist`

---

## 🔧 Troubleshooting

### Issue: "enum value already exists"

**Solution**: This is normal! It means the migration was already partially applied. Continue with the next steps.

### Issue: "column already exists"

**Solution**: Also normal! Just verify the migration version is updated:

```sql
UPDATE alembic_version SET version_num = '77fd4b324d80';
```

### Issue: Connection timeout from WSL

**Solution**: Use Method 1 (Supabase Dashboard) or Method 3 (Cloud Run) instead.

### Issue: Files still stuck in parsing

**Solution**:
1. Check if migrations were applied (run verification queries)
2. Restart the Cloud Run service to pick up new schema:
   ```bash
   gcloud run services update cms-automation-backend \
     --project=cmsupload-476323 \
     --region=us-east1
   ```
3. Check for other errors in logs

---

## 📊 Expected Impact

### Execution Time
- **Migration**: 30-60 seconds
- **Downtime**: 0 (migrations run online)
- **Lock Time**: Minimal (ADD COLUMN is fast)

### Risk Assessment
- **Risk Level**: 🟡 Low-Medium
- **Rollback**: ⚠️ Possible but not recommended (may lose data)
- **Data Loss**: 🟢 Very Low (only adding fields)

---

## 🚨 Rollback (Emergency Only)

If you need to rollback (not recommended):

```sql
-- Revert migration version
UPDATE alembic_version SET version_num = '20251108_1800';

-- Drop raw_html column
ALTER TABLE worklist_items DROP COLUMN IF EXISTS raw_html;

-- Note: Cannot remove enum values from PostgreSQL
-- The enum values will remain but won't be used
```

⚠️ **Warning**: Rolling back may cause data loss and won't actually remove enum values.

---

## 📝 Execution Checklist

- [ ] Backup database (optional but recommended)
- [ ] Choose execution method (1-4)
- [ ] Run migration
- [ ] Verify migration version is `77fd4b324d80` or higher
- [ ] Verify enum values include `parsing`, `parsing_review`, `proofreading_review`
- [ ] Verify `raw_html` column exists in `worklist_items`
- [ ] Test parsing workflow with a new file
- [ ] Check application logs for errors
- [ ] Monitor for 30 minutes after migration
- [ ] Update this document with execution date/time

---

## 📅 Execution Record

**Executed by**: _____________________
**Date**: _____________________
**Time**: _____________________
**Method used**: _____________________
**Migration version after**: _____________________
**Verification passed**: ☐ Yes  ☐ No
**Notes**: _____________________

---

## 🔗 Related Documents

- `DATABASE_MIGRATION_REQUIRED.md` - Original requirements analysis
- `migrations/manual_sql/p0_critical_migration.sql` - SQL migration script
- `run_production_migration.py` - Python migration script

---

**Need help?** Check the application logs or contact the development team.
