# Supabase Auth Schema & Policies

This folder tracks database changes that cannot be represented via Alembic because they live inside Supabase’s managed Postgres (`auth` schema, RLS policies, triggers, etc.). Apply the SQL files in chronological order using **Supabase SQL Editor** or the CLI:

```bash
supabase db execute --file supabase/migrations/20250214_create_profiles.sql
```

## 2025-02-14 – Profiles + RLS (`20250214_create_profiles.sql`)

Adds the `user_role` enum, `public.profiles` table, timestamp triggers, automatic profile provisioning for new `auth.users`, and row-level-security policies that:

1. Allow each user to `SELECT` only their own profile.
2. Restrict `INSERT/UPDATE/DELETE` to accounts with `role = 'admin'`.
3. Provide an `is_admin(uuid)` helper for FastAPI and Postgres policies to reuse.

After applying the SQL:

1. Promote at least one user to `admin` by updating `public.profiles`.
2. Verify RLS via Supabase Dashboard (`SELECT * FROM public.profiles` as different users).
3. Ensure the backend `.env` contains `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_KEY`.
