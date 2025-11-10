# Database Migration Guide - Worklist Status Extension

## Migration: 20251110_1000_extend_worklist_status

### Overview
Extends the worklist status workflow from 7 states to 9 states, adding:
- `parsing` - Article parsing in progress
- `parsing_review` - Review parsing results (title, author, SEO, images)
- `proofreading_review` - Review proofreading issues

And migrates existing `under_review` records to `proofreading_review`.

### Prerequisites
1. Backend code deployed with updated WorklistStatus enum
2. Database backup created
3. Production database credentials available

### Running the Migration

#### Option 1: Using Alembic (Recommended for Development/Staging)

```bash
# Navigate to backend directory
cd backend

# Check current migration status
alembic current

# Show pending migrations
alembic history

# Run the migration
alembic upgrade head

# Verify migration applied
alembic current
```

#### Option 2: Direct SQL (For Production with Supabase)

If you prefer to run the migration manually or need to inspect before applying:

```sql
-- 1. Add new enum values to WorklistStatus type (PostgreSQL only)
ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'parsing';
ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'parsing_review';
ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'proofreading_review';

-- 2. Migrate existing data
UPDATE worklist_items
SET status = 'proofreading_review'
WHERE status = 'under_review';

-- 3. Verify migration
SELECT status, COUNT(*) as count
FROM worklist_items
GROUP BY status
ORDER BY count DESC;
```

#### Option 3: Using Cloud Run Deployment

If the backend is deployed on Cloud Run, you can run migrations as part of deployment:

```bash
# SSH into Cloud Run instance or use Cloud Shell
gcloud run services update cms-automation-backend \
  --region=us-east1 \
  --command="alembic upgrade head"
```

### Verification

After running the migration, verify:

1. **Check enum values** (PostgreSQL):
```sql
SELECT unnest(enum_range(NULL::workliststatus)) as status;
```

Expected output:
```
pending
parsing
parsing_review
proofreading
proofreading_review
under_review
ready_to_publish
publishing
published
failed
```

2. **Check data migration**:
```sql
SELECT status, COUNT(*) as count
FROM worklist_items
GROUP BY status;
```

Expected: No records with `under_review` status (all migrated to `proofreading_review`)

3. **Check application logs**:
- Watch for any errors related to status enum validation
- Verify new status values are being set correctly

### Rollback

If you need to rollback:

```bash
# Rollback one migration
alembic downgrade -1

# Or rollback to specific revision
alembic downgrade 20251108_1800
```

**Note**: PostgreSQL enum types cannot have values removed once added. The rollback
only reverts the data (`proofreading_review` → `under_review`), not the enum type itself.

### Production Deployment Checklist

- [ ] Backup database before migration
- [ ] Test migration on staging environment first
- [ ] Deploy backend code with updated enum (commit 7630c53)
- [ ] Run database migration
- [ ] Deploy frontend code with new routing logic (commit ecdcb43)
- [ ] Verify worklist items show correct review buttons
- [ ] Test full workflow: parsing → parsing_review → proofreading → proofreading_review

### Troubleshooting

**Error: "invalid input value for enum workliststatus"**
- Ensure backend code is deployed before running migration
- Check that all status values in code match database enum

**Error: "column status cannot be cast automatically"**
- This shouldn't happen as we're only adding enum values, not changing column type
- If occurs, check PostgreSQL version and enum handling

**Data not migrated**:
- Verify migration script was executed successfully
- Check alembic_version table to confirm migration was recorded
