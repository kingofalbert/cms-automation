# Article Structured Parsing - Implementation Checklist

**Version**: 1.0
**Created**: 2025-11-08
**Status**: Pre-Implementation
**Feature**: Article Structured Parsing (Phase 7)

---

## Purpose

This checklist ensures all aspects of the Article Structured Parsing feature are properly implemented, tested, and deployed. Use this as a gate-check before each phase milestone.

---

## Pre-Implementation (Week 0)

### Design Review

- [ ] **Technical analysis document reviewed and approved** (`docs/ARTICLE_PARSING_TECHNICAL_ANALYSIS.md`)
- [ ] **SpecKit documents updated and synchronized**:
  - [ ] `spec.md` - User Story 7, FR-088~FR-105
  - [ ] `plan.md` - Phase 7 detailed plan
  - [ ] `data-model.md` - Schema updates
  - [ ] `tasks.md` - Task breakdown T7.1~T7.29
- [ ] **Test plan reviewed and approved** (`docs/ARTICLE_PARSING_TEST_PLAN.md`)
- [ ] **API documentation reviewed** (`docs/API_PARSING_ENDPOINTS.md`)
- [ ] **Team capacity confirmed** (1 backend + 1 frontend for 6 weeks)

### Environment Setup

- [ ] **Development environment ready**:
  - [ ] PostgreSQL 14+ installed
  - [ ] Python 3.11+ with SQLAlchemy 2.0+
  - [ ] Claude 4.5 Sonnet API access confirmed
  - [ ] PIL/Pillow library installed
  - [ ] BeautifulSoup4 installed
- [ ] **Frontend environment ready**:
  - [ ] Node.js 20+ installed
  - [ ] TypeScript 5.x
  - [ ] React 18
  - [ ] Zustand (state management)
  - [ ] Playwright (E2E testing)
- [ ] **Test fixtures prepared**:
  - [ ] 20 diverse Google Doc samples
  - [ ] Sample images (JPEG, PNG, WEBP)
  - [ ] Ground truth labels for accuracy testing

### Open Decisions Resolved

- [ ] **Image storage backend decided**: ☐ Supabase Storage ☐ Google Drive
- [ ] **Image spec KPIs defined** (publishing tolerances for width, aspect ratio)
- [ ] **Legacy articles strategy decided**: ☐ Auto-parse ☐ Manual flag ("legacy-unparsed")

---

## Week 16: Database Schema & Migrations

### Design (T7.1)

- [ ] **ER diagram created** showing `articles` ← `article_images` ← `article_image_reviews`
- [ ] **SQL DDL reviewed** for all new fields and tables
- [ ] **JSONB metadata structure defined** for `article_images.metadata`
- [ ] **Tech lead approval received**

### Migration (T7.2)

- [ ] **Alembic migration file created**: `migrations/versions/20251108_article_parsing.py`
- [ ] **Migration adds 13 new columns to `articles` table**
- [ ] **Migration creates `article_images` table** with CHECK constraint `position >= 0`
- [ ] **Migration creates `article_image_reviews` table** with action ENUM
- [ ] **Indexes created**: `idx_article_images_article_id`, `idx_article_images_position`
- [ ] **Downgrade logic implemented and tested**
- [ ] **Migration idempotent** (safe to run multiple times)

### SQLAlchemy Models (T7.3)

- [ ] **`Article` model extended** with all parsing fields
- [ ] **`ArticleImage` model created** in `backend/src/models/article_image.py`
- [ ] **`ArticleImageReview` model created** in `backend/src/models/article_image_review.py`
- [ ] **Relationships configured**: `article.images`, `article_image.reviews`
- [ ] **Cascade deletes configured** (ON DELETE CASCADE)
- [ ] **Type hints complete** (Pydantic integration ready)

### Migration Testing (T7.4)

- [ ] **Migration executed on dev database** (completes in <5 minutes)
- [ ] **Sample data inserted successfully** (article with parsing fields, images with JSONB metadata)
- [ ] **Indexes verified** with `EXPLAIN ANALYZE`
- [ ] **Downgrade tested and verified** (zero data loss)
- [ ] **Migration log saved**: `logs/migration-20251108.log`

**Checkpoint**: ✅ Database schema complete, migration tested, models ready

---

## Week 17-18: Backend Parsing Engine

### ArticleParserService Skeleton (T7.5)

- [ ] **Service file created**: `backend/src/services/parser/article_parser.py`
- [ ] **Dataclasses defined**: `backend/src/services/parser/types.py`
  - [ ] `ParsedArticle`
  - [ ] `HeaderFields`
  - [ ] `AuthorFields`
  - [ ] `ImageRecord`
  - [ ] `MetaSEOFields`
- [ ] **Main method signature**: `parse_document(raw_html: str, article_id: int) -> ParsedArticle`
- [ ] **Dependency injection** (Anthropic client, storage service)
- [ ] **Unit test skeleton created**

### Header Parsing (T7.6)

- [ ] **`_parse_header()` method implemented**
- [ ] **Claude prompt template created**: `backend/src/services/parser/prompts/title_parsing.txt`
- [ ] **Regex fallback logic** for inline separators (｜, —, ：)
- [ ] **Unit tests pass** (10+ title variations)
- [ ] **AI parsing accuracy ≥90%** on test set

### Author Extraction (T7.7)

- [ ] **`_extract_author()` method implemented**
- [ ] **Claude prompt template created**: `backend/src/services/parser/prompts/author_extraction.txt`
- [ ] **Cleaning logic** strips prefixes and whitespace
- [ ] **Unit tests pass** (8+ author variations)
- [ ] **AI extraction accuracy ≥95%**

### Image Extraction (T7.8)

- [ ] **`_extract_images()` method implemented**
- [ ] **DOM parsing logic** (BeautifulSoup)
- [ ] **Image download with retry logic** (3 retries)
- [ ] **Position tracking** (paragraph index)
- [ ] **Integration with ImageProcessor** service
- [ ] **Unit tests pass** (5+ image extraction scenarios)

### ImageProcessor Service (T7.9)

- [ ] **Service file created**: `backend/src/services/media/image_processor.py`
- [ ] **`download_and_process()` method** with HTTP download
- [ ] **`extract_specs()` method** using PIL/Pillow
- [ ] **Storage backend integration** (Supabase Storage or Google Drive)
- [ ] **Handles corrupt images gracefully**
- [ ] **Unit tests pass** (JPEG, PNG, WEBP samples)
- [ ] **Specs accuracy 100%** (PIL can read all supported formats)

### Meta/SEO Extraction (T7.10)

- [ ] **`_extract_meta_seo()` method implemented**
- [ ] **Claude prompt template created**: `backend/src/services/parser/prompts/meta_seo_extraction.txt`
- [ ] **Array parsing logic** (comma/newline separated)
- [ ] **DOM stripping after extraction**
- [ ] **Unit tests pass** (6+ meta extraction scenarios)

### Body HTML Cleaning (T7.11)

- [ ] **`_clean_body_html()` method implemented**
- [ ] **Bleach configuration** (whitelist: H1, H2, p, ul, ol, strong, em, a)
- [ ] **DOM manipulation** removes extracted nodes
- [ ] **XSS prevention verified**
- [ ] **Unit tests pass** with complex HTML samples

### Unit Tests (T7.12)

- [ ] **Test coverage ≥85%** for `article_parser.py`
- [ ] **Test coverage ≥90%** for `image_processor.py`
- [ ] **All edge cases covered** (missing author, no images, malformed titles, corrupt images)
- [ ] **Mocked Claude responses** with varied structures
- [ ] **Tests run in <30 seconds**
- [ ] **All tests passing** ✅

**Checkpoint**: ✅ Backend parsing engine complete, unit tests passing, coverage ≥85%

---

## Week 19: API & Integration

### Worklist API Extension (T7.13)

- [ ] **Pydantic model updated**: `WorklistItemDetailResponse`
- [ ] **API route extended**: `backend/src/api/routes/worklist.py`
- [ ] **Response includes all parsing fields**
- [ ] **`images[]` array** includes: id, paths, caption, position, metadata
- [ ] **Pydantic validation passes**
- [ ] **Integration test verifies response schema**

### Parsing Confirmation Endpoint (T7.14)

- [ ] **New API route created**: `POST /v1/worklist/:id/confirm-parsing`
- [ ] **Pydantic model created**: `ParsingConfirmationRequest`
- [ ] **Database update logic** (parsing_confirmed, parsing_confirmed_at, parsing_confirmed_by)
- [ ] **Image reviews creation logic**
- [ ] **Validates image_reviews actions**: keep, remove, replace_caption, replace_source
- [ ] **Integration test passes** (verifies database updates)

### Google Drive Sync Integration (T7.15)

- [ ] **`GoogleDriveSyncService.process_new_document()` updated**
- [ ] **Calls `ArticleParserService.parse_document()`** after download
- [ ] **Creates article with all structured fields**
- [ ] **Creates `article_images` records** (bulk insert)
- [ ] **Sets `current_status = 'pending'`**
- [ ] **Handles parsing errors gracefully** (logs error, sets status='failed')
- [ ] **Integration test passes**: Google Doc → Parsed Article → Images created
- [ ] **Parsing completes in ≤20 seconds** for typical article

**Checkpoint**: ✅ API endpoints implemented, Google Drive integration complete

---

## Week 20-21: Frontend Step 1 UI

### Step Indicator (T7.16)

- [ ] **Component file created**: `frontend/src/components/Proofreading/StepIndicator.tsx`
- [ ] **Displays two steps** with labels (zh-TW, en-US)
- [ ] **Highlights current step**
- [ ] **Shows completed steps** with checkmark
- [ ] **Step 2 blocked** if Step 1 not confirmed
- [ ] **Component tests pass**

### Structured Headers Card (T7.17)

- [ ] **Component file created**: `frontend/src/components/Proofreading/StructuredHeadersCard.tsx`
- [ ] **Three input fields** (可選前標, 主標題*, 可選副標)
- [ ] **Character counters** update in real-time
- [ ] **Validation error** shown if title_main < 5 chars
- [ ] **Auto-save on blur** (debounced 500ms)
- [ ] **Displays save status** (saving, saved, error)
- [ ] **Component tests pass**

### Author Info Card (T7.18)

- [ ] **Component file created**: `frontend/src/components/Proofreading/AuthorInfoCard.tsx`
- [ ] **Author line read-only field**
- [ ] **Author name editable field**
- [ ] **Auto-save on blur**
- [ ] **Handles missing author gracefully** ("未檢測到作者")
- [ ] **Component tests pass**

### Image Gallery Card (T7.19)

- [ ] **Component file created**: `frontend/src/components/Proofreading/ImageGalleryCard.tsx`
- [ ] **Grid layout** (responsive, 2-3 columns on desktop, 1 on mobile)
- [ ] **Each item shows**: preview, caption (editable), source link, specs table
- [ ] **Specs table highlights** out-of-range values
- [ ] **Action buttons**: Keep, Remove, Replace Caption, Replace Source
- [ ] **Replace actions** show inline inputs
- [ ] **Reviewer notes textarea**
- [ ] **Auto-save actions on selection**
- [ ] **Component tests pass**

### Image Specs Table (T7.20)

- [ ] **Component file created**: `frontend/src/components/Proofreading/ImageSpecsTable.tsx`
- [ ] **Displays all specs**: Width, Height, Aspect Ratio, File Size, Format, EXIF Date
- [ ] **Width warning** if <800px or >3000px (red)
- [ ] **Aspect ratio warning** if non-standard (amber)
- [ ] **Tooltips explain thresholds**
- [ ] **Component tests pass**

### Meta/SEO Card (T7.21)

- [ ] **Component file created**: `frontend/src/components/Proofreading/MetaSEOCard.tsx`
- [ ] **Meta description textarea** with character counter
- [ ] **Warning if >160 chars** (advisory, not blocking)
- [ ] **SEO keywords tag input** (add with Enter/comma, remove with X)
- [ ] **Tags tag input**
- [ ] **Auto-save on blur** (debounced 500ms)
- [ ] **Component tests pass**

### Body HTML Preview Card (T7.22)

- [ ] **Component file created**: `frontend/src/components/Proofreading/BodyHTMLPreviewCard.tsx`
- [ ] **Renders sanitized HTML safely** (DOMPurify or similar)
- [ ] **Preserves semantic structure** (H1, H2, p, ul, ol, strong, em, a)
- [ ] **Scrollable container**
- [ ] **Component tests pass**

### Confirmation Actions & State (T7.23)

- [ ] **Zustand store created**: `frontend/src/stores/useParsingConfirmationStore.ts`
- [ ] **Store actions implemented**: updateTitleFields, updateAuthor, updateMetaSEO, addImageReview, confirmParsing
- [ ] **Confirmation button component**: `ConfirmationActions.tsx`
- [ ] **`confirmParsing()` calls** `POST /v1/worklist/:id/confirm-parsing`
- [ ] **Success**: shows toast, unlocks Step 2, redirects
- [ ] **Error**: shows error toast, keeps Step 1 active
- [ ] **"Needs fix" toggle** blocks confirmation and Step 2
- [ ] **Store tests pass** with mock API

### Step 2 Blocking Logic (T7.24)

- [ ] **Blocking logic implemented** in `ProofreadingReviewPage.tsx`
- [ ] **Warning alert component**: `Step2BlockingAlert.tsx`
- [ ] **Step 2 tab disabled** if `parsing_confirmed === false`
- [ ] **Warning alert shows** "請先完成解析確認"
- [ ] **"返回 Step 1" button** in alert
- [ ] **Step 2 unlocked** after confirmation
- [ ] **State persists** across page reloads (fetch from API)
- [ ] **Component tests pass**

### i18n Support (T7.25)

- [ ] **Locale files updated**: `frontend/src/locales/zh-TW.json`, `en-US.json`
- [ ] **All parsing UI strings** use `t('proofreading.parsing.*')`
- [ ] **zh-TW translations complete and accurate**
- [ ] **en-US translations complete and accurate**
- [ ] **Language switch works** without page reload
- [ ] **No hardcoded strings** in components
- [ ] **i18n tests pass**

**Checkpoint**: ✅ Frontend Step 1 UI complete, all components tested, i18n support added

---

## Week 21: Integration & Testing

### E2E Workflow Test (T7.26)

- [ ] **E2E test spec created**: `frontend/e2e/parsing-confirmation-workflow.spec.ts`
- [ ] **Test imports Google Doc**
- [ ] **Verifies parsing completes** (all fields populated)
- [ ] **Opens Proofreading Review page**
- [ ] **Verifies Step 1 UI** displays all parsed fields
- [ ] **Edits title, author, meta fields**
- [ ] **Confirms parsing**
- [ ] **Verifies Step 2 unlocked**
- [ ] **Accesses Step 2 successfully**
- [ ] **Returns to Step 1** (edit allowed)
- [ ] **Test passes in <90 seconds**
- [ ] **Screenshots captured** at key steps

### Parsing Accuracy Validation (T7.27)

- [ ] **Test suite created**: `backend/tests/accuracy/test_parsing_accuracy.py`
- [ ] **20 diverse test documents prepared** (1-3 line titles, 0-10 images, with/without meta)
- [ ] **Ground truth labels verified**: `backend/tests/fixtures/accuracy/ground_truth.json`
- [ ] **Accuracy measured per field**:
  - [ ] Title accuracy ≥90%
  - [ ] Author accuracy ≥95%
  - [ ] Image detection ≥90%
  - [ ] Meta extraction ≥85%
- [ ] **Overall accuracy ≥90%**
- [ ] **Failure cases documented** with root cause analysis
- [ ] **Accuracy report generated**: `docs/parsing-accuracy-report.json`

### Performance Testing (T7.28)

- [ ] **Performance test script created**: `backend/tests/performance/test_parsing_performance.py`
- [ ] **Typical article (1500 words, 5 images)**: ≤20 seconds (95th percentile)
- [ ] **Small article (500 words, 1 image)**: ≤10 seconds
- [ ] **Large article (3000 words, 10 images)**: ≤40 seconds
- [ ] **Performance bottlenecks identified** (profiling)
- [ ] **Benchmark report created**: `docs/parsing-performance-benchmarks.md`

### Bug Fixes & Edge Cases (T7.29)

- [ ] **Missing author handled gracefully** (author_line=null, author_name=null)
- [ ] **0 images handled gracefully** (empty array)
- [ ] **Malformed HTML handled** (parsing doesn't crash, logs error)
- [ ] **Image download failures handled** (retries 3x, saves partial result)
- [ ] **Corrupt images handled** (PIL can't read → logs error, metadata=null)
- [ ] **Missing meta blocks handled** (returns None/empty arrays)
- [ ] **All edge cases have regression tests**
- [ ] **Bug fixes log created**: `docs/parsing-bug-fixes-log.md`

**Checkpoint**: ✅ All tests passing, accuracy ≥90%, performance ≤20s

---

## Deployment Preparation

### Code Quality

- [ ] **Backend code coverage ≥85%**
- [ ] **Frontend code coverage ≥80%**
- [ ] **All linting rules passed** (pylint, eslint)
- [ ] **Type checking passed** (mypy, tsc)
- [ ] **Security scan passed** (Bandit, npm audit)
- [ ] **No high/critical vulnerabilities**

### Documentation

- [ ] **API documentation complete** (`docs/API_PARSING_ENDPOINTS.md`)
- [ ] **Test plan complete** (`docs/ARTICLE_PARSING_TEST_PLAN.md`)
- [ ] **README updated** with parsing feature overview
- [ ] **Deployment guide updated** with migration steps

### Deployment Checklist

- [ ] **Staging deployment successful**:
  - [ ] Migration executed on staging database
  - [ ] Parsing service operational
  - [ ] Step 1 UI accessible
  - [ ] E2E tests passing on staging
- [ ] **Production deployment plan reviewed**:
  - [ ] Backup database before migration
  - [ ] Rollback plan prepared
  - [ ] Downtime window scheduled (<5 minutes)
  - [ ] Stakeholders notified
- [ ] **Monitoring configured**:
  - [ ] Parsing latency metrics
  - [ ] Parsing accuracy metrics
  - [ ] Error rate alerts
  - [ ] Image download success rate

---

## Post-Deployment

### Verification

- [ ] **Production migration successful** (zero data loss)
- [ ] **All services operational**:
  - [ ] Google Drive sync with parsing
  - [ ] Worklist API returning parsing fields
  - [ ] Step 1 UI loading correctly
- [ ] **E2E test passes on production**
- [ ] **Monitoring dashboards showing data**

### User Acceptance Testing

- [ ] **Test with 10 real Google Docs** from production drive
- [ ] **Verify parsing accuracy** with domain experts
- [ ] **Verify Step 1 UI usability** with reviewers
- [ ] **Collect user feedback** and log issues

### Handoff

- [ ] **Product team trained** on Step 1 UI workflow
- [ ] **Support team briefed** on common issues
- [ ] **Runbook created** for operational tasks:
  - [ ] Reprocessing failed parses
  - [ ] Manually correcting parsing errors
  - [ ] Monitoring accuracy metrics
- [ ] **Feature announcement sent** to users

---

## Success Metrics (30-Day Observation)

### Quantitative Metrics

- [ ] **Parsing accuracy maintained ≥90%** (measured weekly)
- [ ] **Parsing latency maintained ≤20s** (95th percentile)
- [ ] **Image metadata completeness 100%** (all downloaded images)
- [ ] **Step 1 confirmation rate ≥95%** (users don't abandon workflow)
- [ ] **Step 2 access rate ≥90%** after Step 1 confirmation
- [ ] **Zero critical bugs** reported
- [ ] **<5% failed parses** (excluding network/timeout issues)

### Qualitative Metrics

- [ ] **User satisfaction ≥4/5** (from reviewer surveys)
- [ ] **No major usability complaints** about Step 1 UI
- [ ] **Product team reports time savings** in quality review process
- [ ] **No accuracy regression** compared to manual processes

---

## Sign-Off

### Technical Sign-Off

- [ ] **Backend Lead**: ________________________ Date: __________
- [ ] **Frontend Lead**: ________________________ Date: __________
- [ ] **QA Lead**: ________________________ Date: __________
- [ ] **DevOps Lead**: ________________________ Date: __________

### Business Sign-Off

- [ ] **Product Manager**: ________________________ Date: __________
- [ ] **Content Manager**: ________________________ Date: __________

---

**Status**: ⏳ Awaiting Implementation

**Last Updated**: 2025-11-08

**Document Owner**: Project Manager

---

## Notes

Use this checklist as a living document throughout Phase 7 implementation. Update checkboxes as tasks complete and add notes for any blockers or deviations from plan.
