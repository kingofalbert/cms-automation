# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Fixed

#### React StrictMode + Supabase Auth Lock Deadlock (2025-12-20)

Fixed a critical issue where the application would get stuck on "Loading..." indefinitely in development mode.

**Root Cause:**
- React StrictMode double-mounts components in development
- Supabase client uses `navigator.locks` API for auth state management
- The original `getSession()` call acquired a lock that was never released when React unmounted the component during double-mount cycle
- This created a deadlock blocking all subsequent auth operations

**Solution Applied (`frontend/src/contexts/AuthContext.tsx`):**
1. Removed direct `getSession()` call - was acquiring locks that weren't released properly
2. Now relies solely on `onAuthStateChange` with `INITIAL_SESSION` event for initial auth state
3. Uses direct REST API for profile fetching to avoid Supabase client lock contention
4. Added `isMountedRef` to prevent state updates after component unmount

**Files Changed:**
- `frontend/src/contexts/AuthContext.tsx`
- `docs/SUPABASE_AUTH_SETUP.md` - Added troubleshooting section
- `specs/005-supabase-user-auth/README.md` - Documented the fix
- `frontend/README.md` - Added troubleshooting guide

### Verified

#### Phase 13: Enhanced Image Review - E2E Verification (2025-12-20)

Completed end-to-end browser testing of the Phase 13 Enhanced Image Review feature.

**Verified Features:**
- Image Review Section header shows correct counts (e.g., "圖片審核 (1 張圖片：1 置頂 + 0 正文)")
- FeaturedBadge component renders correctly with detection method tooltip
- Image metadata display (Original link, Caption, Alt Text) works properly
- Epoch Times standards comparison (Resolution, File size, Format) displays correctly
- Warning/success badges show appropriate status
- Featured vs Content image separation logic works correctly

**Files Updated:**
- `specs/013-enhanced-image-review/README.md` - Updated to v1.2, marked as E2E verified
- `frontend/README.md` - Enhanced documentation for Image Review Section

---

## Previous Releases

### Phase 13: Enhanced Image Review (Initial Implementation)

- Added FeaturedBadge component with detection method display
- Implemented featured image detection (置頂圖片) with multiple detection methods:
  - `manual` - User manually set as featured
  - `caption_keyword` - Caption contains 置頂/封面 etc.
  - `position_before_body` - First image before content starts
  - `position_legacy` - Migrated from old position=0 logic
- Added Epoch Times image standards comparison
- Image separation logic for 置頂 vs 正文 images

### Phase 5: Supabase Authentication (Initial Implementation - 2025-02-14)

- Integrated Supabase Auth for user authentication
- Added login page with email/password and magic link options
- Implemented protected routes with `ProtectedRoute` component
- Backend JWT verification middleware
- User roles: admin, editor, viewer
