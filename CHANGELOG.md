# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added

#### View Original Google Doc Feature (2025-12-25)

Added ability for operators to open the original Google Doc in a new browser window during article review.

**Problem Solved:**
- During parsing and proofreading stages, operators could not see the original Google Doc content
- This made it difficult to verify if AI suggestions were accurate or reasonable
- Operators had to manually search for the source document in Google Drive

**Implementation:**
1. **ArticleReviewModal Header Button**
   - Added "查看原文" button in the modal header (always visible during review)
   - Uses `drive_metadata.webViewLink` from worklist item data
   - Opens in new browser window with `target="_blank"`

2. **WorklistTable Row Button**
   - Added "View Original" button (ExternalLink icon) in the table actions column
   - Uses `webViewLink` if available, falls back to constructing URL from `drive_file_id`
   - Allows quick access from the worklist without opening the review modal

**Files Changed:**
- `frontend/src/components/ArticleReview/ArticleReviewModal.tsx` - Added header button
- `frontend/src/components/Worklist/WorklistTable.tsx` - Added row action button
- `frontend/src/types/worklist.ts` - Added `drive_metadata` to `WorklistItem`
- `frontend/src/i18n/locales/zh-TW.json` - Added translation key
- `frontend/src/i18n/locales/en-US.json` - Added translation key

### Fixed

#### Placeholder UI Cleanup (2025-12-25)

Removed or fixed non-functional placeholder UI elements across the application.

**Changes:**

1. **WorklistTable - Removed Non-functional Reject Buttons**
   - Removed reject buttons from parsing_review and proofreading_review status rows
   - These buttons had no implementation (just empty TODO comments)
   - Review buttons remain functional and navigate to appropriate review pages

2. **TitleReviewSection - Removed Mock AI Optimization**
   - Removed fake "AI 优化标题" button that returned hardcoded mock suggestions
   - Added helpful text pointing users to real AI suggestions in SEOTitleSelectionCard
   - Added "reset to original" functionality for title editing

3. **ArticleSEOConfirmationPage - Implemented Real API**
   - Connected the confirm button to actual `seoAPI.update()` endpoint
   - Meta description now saves to database
   - Added error handling with visual feedback
   - Tags and FAQs stored in `manual_overrides` for future use

4. **ProofreadingRulesSection - Added "Coming Soon" State**
   - Replaced hidden/empty content with explicit "統計功能開發中" notice
   - Clear explanation that statistics APIs are not yet implemented
   - Quick action buttons still functional for rule management

5. **Added Toast Notifications**
   - ContentComparisonCard: Shows "已複製到剪貼簿" on copy
   - ParsingReviewPanel: Shows success/error toast for SEO Title selection

**Files Changed:**
- `frontend/src/components/Worklist/WorklistTable.tsx`
- `frontend/src/components/ArticleReview/TitleReviewSection.tsx`
- `frontend/src/pages/ArticleSEOConfirmationPage.tsx`
- `frontend/src/components/Settings/ProofreadingRulesSection.tsx`
- `frontend/src/components/ArticleReview/ContentComparisonCard.tsx`
- `frontend/src/components/ArticleReview/ParsingReviewPanel.tsx`

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
