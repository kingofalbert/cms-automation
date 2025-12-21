# Supabase Authentication Setup Guide

## Overview

This document describes the Supabase authentication implementation for CMS Automation.

## What Was Implemented

### Frontend (`frontend/`)

| File | Description |
|------|-------------|
| `src/lib/supabase.ts` | Supabase client singleton |
| `src/contexts/AuthContext.tsx` | Authentication context with hooks |
| `src/components/ProtectedRoute.tsx` | Route guard component |
| `src/pages/LoginPage.tsx` | Login page with email/password and magic link |
| `src/config/routes.ts` | Updated with auth routes and `isPublic` flag |
| `src/routes.tsx` | Updated to wrap protected routes |
| `src/App.tsx` | Wrapped with `AuthProvider` |
| `src/services/api-client.ts` | Uses Supabase session token |

### Backend (`backend/`)

| File | Description |
|------|-------------|
| `src/services/auth/__init__.py` | Auth service exports |
| `src/services/auth/jwt.py` | Supabase JWT verification |
| `src/api/middleware/auth.py` | Authentication middleware |
| `src/config/settings.py` | Added Supabase settings |
| `src/main.py` | Enabled auth middleware |

### Database (`supabase/migrations/`)

| File | Description |
|------|-------------|
| `20250214_create_profiles.sql` | Profiles table with RLS |

## Manual Setup Required

### Step 1: Run Database Migration

1. Go to Supabase Dashboard: https://supabase.com/dashboard/project/twsbhjmlmspjwfystpti
2. Navigate to **SQL Editor**
3. Copy and run the contents of `supabase/migrations/20250214_create_profiles.sql`

### Step 2: Get JWT Secret

1. Go to Supabase Dashboard
2. Navigate to **Settings** > **API**
3. Find **JWT Settings** section
4. Copy the **JWT Secret**
5. Add to `backend/.env`:
   ```
   SUPABASE_JWT_SECRET=your-jwt-secret-here
   ```

### Step 3: Create First Admin User

1. Go to Supabase Dashboard
2. Navigate to **Authentication** > **Users**
3. Click **Add user** > **Create new user**
4. Enter email and password
5. After user is created, run this SQL to make them admin:
   ```sql
   UPDATE public.profiles
   SET role = 'admin'
   WHERE id = (SELECT id FROM auth.users WHERE email = 'admin@example.com');
   ```

### Step 4: Configure Environment Variables

**Frontend** (`frontend/.env`):
```env
VITE_SUPABASE_URL=https://twsbhjmlmspjwfystpti.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci... (already configured)
```

**Backend** (`backend/.env`):
```env
SUPABASE_URL=https://twsbhjmlmspjwfystpti.supabase.co
SUPABASE_JWT_SECRET=your-jwt-secret-here
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci... (already configured)
```

## User Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access, can manage users |
| `editor` | Can edit and publish content (default) |
| `viewer` | Read-only access |

## Authentication Flow

```
1. User visits protected route
   ↓
2. ProtectedRoute checks isAuthenticated
   ↓
3. If not authenticated → Redirect to /login
   ↓
4. User enters credentials
   ↓
5. Supabase validates and returns JWT
   ↓
6. AuthContext stores session
   ↓
7. api-client attaches token to requests
   ↓
8. Backend middleware verifies JWT
   ↓
9. Request proceeds with user context
```

## Testing

### Test Login Flow

1. Start frontend: `npm run dev --prefix frontend`
2. Open http://localhost:3000
3. Should redirect to `/login`
4. Enter credentials
5. Should redirect back to original page

### Test API Authentication

```bash
# Without token - should return 401
curl http://localhost:8000/v1/worklist

# With valid token - should return data
curl -H "Authorization: Bearer <jwt-token>" http://localhost:8000/v1/worklist
```

## Disabling Authentication (Development)

To disable authentication for development:

1. Remove or empty `SUPABASE_JWT_SECRET` in `backend/.env`
2. The middleware will automatically skip auth verification

## Known Issues & Solutions

### React StrictMode + Supabase Lock Deadlock (Fixed 2025-12-20)

**Symptom:** Page stuck on "Loading..." indefinitely in development mode.

**Root Cause:**
- React StrictMode double-mounts components in development
- Supabase client uses `navigator.locks` API for auth state management
- Original `getSession()` call acquires a lock that's never released when React unmounts the component
- This creates a deadlock where subsequent auth operations are blocked

**Solution Applied in `frontend/src/contexts/AuthContext.tsx`:**

1. **Removed direct `getSession()` call** - This was acquiring locks that weren't released properly
2. **Rely solely on `onAuthStateChange`** - Uses `INITIAL_SESSION` event for initial auth state
3. **Use direct REST API for profile fetching** - Avoids Supabase client lock contention
4. **Added `isMountedRef`** - Prevents state updates after component unmount

```typescript
// Current implementation uses direct REST call instead of Supabase client
const response = await fetch(
  `${import.meta.env.VITE_SUPABASE_URL}/rest/v1/profiles?id=eq.${session.user.id}&select=id,display_name,role`,
  {
    headers: {
      'apikey': import.meta.env.VITE_SUPABASE_ANON_KEY,
      'Authorization': `Bearer ${session.access_token}`,
    },
  }
)
```

**Why this works:**
- `onAuthStateChange` fires `INITIAL_SESSION` on page load with the stored session
- Direct REST calls don't acquire the Supabase client's internal locks
- The `isMountedRef` prevents orphaned promises from updating state

---

## Security Notes

1. **Never commit** `.env` files with secrets
2. **JWT Secret** must be kept secure - rotate if compromised
3. **Service Role Key** should only be used server-side
4. Enable **Email Confirmation** in Supabase for production
