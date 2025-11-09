# Article Structured Parsing - Test Plan

**Document Version**: 1.0
**Created**: 2025-11-08
**Status**: Active
**Feature**: Article Structured Parsing (Phase 7)
**Test Environment**: Development, Staging, Production

---

## 1. Test Overview

### 1.1 Scope

This test plan covers comprehensive testing for the Article Structured Parsing feature, including:
- Unit tests for parsing logic
- Integration tests for API endpoints
- End-to-end tests for UI workflow
- Accuracy validation tests
- Performance tests
- Edge case and regression tests

### 1.2 Test Objectives

- ✅ Verify parsing accuracy ≥90% across all fields
- ✅ Verify parsing completes in ≤20 seconds for typical articles
- ✅ Verify 100% of images have complete metadata
- ✅ Verify Step 1 UI displays all parsed fields correctly
- ✅ Verify Step 2 blocking logic works 100%
- ✅ Achieve test coverage ≥85% (backend), ≥80% (frontend)

### 1.3 Test Strategy

| Test Level | Tools | Coverage Target | Priority |
|------------|-------|-----------------|----------|
| Unit Tests | pytest, Jest/Vitest | ≥85% backend, ≥80% frontend | P0 |
| Integration Tests | pytest (API), Playwright (E2E) | All critical paths | P0 |
| Accuracy Tests | pytest + ground truth dataset | ≥90% accuracy | P0 |
| Performance Tests | pytest + profiling | ≤20s parsing latency | P1 |
| Edge Case Tests | pytest, Jest/Vitest | All known edge cases | P1 |
| Regression Tests | Continuous (CI/CD) | Zero regressions | P0 |

---

## 2. Unit Tests

### 2.1 Backend Unit Tests

#### 2.1.1 ArticleParserService Tests

**File**: `backend/tests/unit/services/parser/test_article_parser.py`

**Test Cases**:

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| UP-001 | Parse 3-line title | HTML with 3-line title | title_prefix, title_main, title_suffix all populated | P0 |
| UP-002 | Parse 2-line title | HTML with 2-line title | title_main, title_suffix populated, prefix=None | P0 |
| UP-003 | Parse 1-line title | HTML with 1-line title | title_main populated, prefix/suffix=None | P0 |
| UP-004 | Parse inline title with ｜ separator | "前標｜主標｜副標" | Correct split into 3 parts | P0 |
| UP-005 | Parse author "文／XXX" | HTML with "文／張三" | author_line="文／張三", author_name="張三" | P0 |
| UP-006 | Parse author "撰稿／XXX" | HTML with "撰稿／李四" | author_line="撰稿／李四", author_name="李四" | P0 |
| UP-007 | Missing author | HTML without author | author_line=None, author_name=None | P0 |
| UP-008 | Parse 5 images | HTML with 5 image blocks | 5 ImageRecord instances | P0 |
| UP-009 | Parse 0 images | HTML without images | Empty array | P0 |
| UP-010 | Parse meta description | HTML with "Meta Description：..." | meta_description extracted | P0 |
| UP-011 | Parse SEO keywords | HTML with "關鍵詞：A, B, C" | seo_keywords=["A", "B", "C"] | P0 |
| UP-012 | Parse tags | HTML with "Tags：X, Y" | tags=["X", "Y"] | P0 |
| UP-013 | Clean body HTML | HTML with headers/images/meta | body_html without extracted elements | P0 |
| UP-014 | Sanitize XSS | HTML with `<script>` tag | Script tag removed | P0 |
| UP-015 | Preserve semantic tags | HTML with H1, p, ul | Tags preserved in body_html | P0 |

**Mocking Strategy**:
- Mock Claude API responses with fixture data
- Mock HTTP downloads for images
- Mock storage backend (Supabase/Google Drive)

**Coverage Target**: ≥85%

---

#### 2.1.2 ImageProcessor Tests

**File**: `backend/tests/unit/services/media/test_image_processor.py`

**Test Cases**:

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| UIP-001 | Extract specs from JPEG | JPEG image file | Complete metadata (width, height, size, MIME, EXIF) | P0 |
| UIP-002 | Extract specs from PNG | PNG image file | Complete metadata (no EXIF) | P0 |
| UIP-003 | Extract specs from WEBP | WEBP image file | Complete metadata | P0 |
| UIP-004 | Calculate aspect ratio | 1920x1080 image | aspect_ratio="16:9" | P0 |
| UIP-005 | Calculate aspect ratio | 1000x1000 image | aspect_ratio="1:1" | P0 |
| UIP-006 | Handle corrupt image | Corrupt JPEG | Logs error, metadata=None | P1 |
| UIP-007 | Extract EXIF date | JPEG with EXIF | exif_date="2025-11-08T10:30:00Z" | P1 |
| UIP-008 | Missing EXIF date | JPEG without EXIF | exif_date=None | P1 |

**Test Fixtures**:
- Sample images: `backend/tests/fixtures/sample_images/`
  - `sample.jpg` (1920x1080, with EXIF)
  - `sample.png` (800x600, no EXIF)
  - `sample.webp` (1000x1000)
  - `corrupt.jpg` (intentionally corrupt)

**Coverage Target**: ≥90%

---

### 2.2 Frontend Unit Tests

#### 2.2.1 Parsing Confirmation Store Tests

**File**: `frontend/src/stores/useParsingConfirmationStore.test.ts`

**Test Cases**:

| Test ID | Test Case | Action | Expected State Change | Priority |
|---------|-----------|--------|------------------------|----------|
| UFP-001 | Update title fields | `updateTitleFields({title_main: "New Title"})` | Store.title_main updated | P0 |
| UFP-002 | Update author | `updateAuthor({author_name: "New Author"})` | Store.author_name updated | P0 |
| UFP-003 | Update meta/SEO | `updateMetaSEO({meta_description: "New Desc"})` | Store.meta_description updated | P0 |
| UFP-004 | Add image review | `addImageReview({action: 'remove', ...})` | Image review added to store | P0 |
| UFP-005 | Confirm parsing (success) | `confirmParsing()` | API called, isConfirmed=true | P0 |
| UFP-006 | Confirm parsing (error) | `confirmParsing()` (API fails) | Error state set, isConfirmed=false | P1 |

**Coverage Target**: ≥80%

---

#### 2.2.2 Component Tests

**Files**: Various `*.test.tsx` files

**Test Cases**:

| Test ID | Component | Test Case | Assertion | Priority |
|---------|-----------|-----------|-----------|----------|
| UFC-001 | StepIndicator | Render two steps | Both steps visible | P0 |
| UFC-002 | StepIndicator | Step 1 active | Step 1 highlighted | P0 |
| UFC-003 | StepIndicator | Click Step 2 (not confirmed) | Blocked, warning shown | P0 |
| UFC-004 | StructuredHeadersCard | Render three fields | All fields visible | P0 |
| UFC-005 | StructuredHeadersCard | Character counter | Counter updates on input | P0 |
| UFC-006 | StructuredHeadersCard | Validation (title_main <5 chars) | Error message shown | P0 |
| UFC-007 | AuthorInfoCard | Display author_line | Read-only field shows value | P0 |
| UFC-008 | AuthorInfoCard | Edit author_name | Input editable, auto-saves | P0 |
| UFC-009 | ImageGalleryCard | Render 5 images | Grid shows 5 items | P0 |
| UFC-010 | ImageSpecsTable | Width out of range | Red warning displayed | P0 |
| UFC-011 | ImageSpecsTable | Aspect ratio non-standard | Amber warning displayed | P0 |
| UFC-012 | MetaSEOCard | Meta description >160 chars | Advisory warning shown | P0 |
| UFC-013 | BodyHTMLPreviewCard | Render HTML | Sanitized HTML displayed | P0 |
| UFC-014 | ConfirmationActions | Click confirm | API called, toast shown | P0 |

**Coverage Target**: ≥80%

---

## 3. Integration Tests

### 3.1 API Integration Tests

#### 3.1.1 Worklist API Tests

**File**: `backend/tests/integration/api/test_worklist_detail.py`

**Test Cases**:

| Test ID | Test Case | Request | Expected Response | Priority |
|---------|-----------|---------|-------------------|----------|
| IAP-001 | Get worklist item detail | GET /v1/worklist/123 | 200, all parsing fields present | P0 |
| IAP-002 | Verify images array | GET /v1/worklist/123 | images[] with 5 items, each has metadata | P0 |
| IAP-003 | Verify confirmation state | GET /v1/worklist/123 | parsing_confirmed, parsing_confirmed_at fields | P0 |

**File**: `backend/tests/integration/api/test_parsing_confirmation.py`

**Test Cases**:

| Test ID | Test Case | Request | Expected Response | Priority |
|---------|-----------|---------|-------------------|----------|
| IAP-004 | Confirm parsing (success) | POST /v1/worklist/123/confirm-parsing | 200, confirmation timestamp returned | P0 |
| IAP-005 | Confirm parsing (validation error) | POST with invalid image_reviews action | 400, validation error message | P1 |
| IAP-006 | Verify database update | POST /v1/worklist/123/confirm-parsing | Database: parsing_confirmed=true | P0 |
| IAP-007 | Verify image reviews created | POST with image_reviews[] | Database: article_image_reviews records created | P0 |

---

#### 3.1.2 Google Drive Sync Integration Tests

**File**: `backend/tests/integration/services/test_google_drive_parsing.py`

**Test Cases**:

| Test ID | Test Case | Action | Expected Result | Priority |
|---------|-----------|--------|-----------------|----------|
| IGD-001 | Import Google Doc → Parse | Sync service processes new doc | Article created with parsed fields | P0 |
| IGD-002 | Verify images created | Sync service processes doc with 3 images | 3 article_images records created | P0 |
| IGD-003 | Verify status set | Sync service completes | current_status='pending' | P0 |
| IGD-004 | Handle parsing error | Sync service encounters malformed HTML | Error logged, status='failed' | P1 |

---

### 3.2 End-to-End Tests

#### 3.2.1 Parsing Confirmation Workflow

**File**: `frontend/e2e/parsing-confirmation-workflow.spec.ts`

**Test Cases**:

| Test ID | Test Case | Steps | Expected Outcome | Priority |
|---------|-----------|-------|------------------|----------|
| E2E-001 | Full workflow (happy path) | 1. Import Google Doc<br>2. Open Proofreading Review<br>3. Verify Step 1 displays parsed fields<br>4. Edit title<br>5. Confirm parsing<br>6. Access Step 2 | All steps complete successfully | P0 |
| E2E-002 | Step 2 blocking | 1. Open review page<br>2. Attempt to access Step 2 without confirming | Warning alert shown, Step 2 blocked | P0 |
| E2E-003 | Return to Step 1 after confirmation | 1. Confirm parsing<br>2. Access Step 2<br>3. Return to Step 1<br>4. Edit field | Edits allowed, saved successfully | P1 |
| E2E-004 | Image review actions | 1. Open Step 1<br>2. Select "Remove" for image<br>3. Add reviewer notes<br>4. Confirm | Image review saved to database | P1 |

**Performance Metrics**:
- Test completes in <90 seconds
- Page loads in <2 seconds
- API calls complete in <500ms

---

## 4. Accuracy Validation Tests

### 4.1 Parsing Accuracy Test Suite

**File**: `backend/tests/accuracy/test_parsing_accuracy.py`

**Test Dataset**: 20 diverse Google Docs

**Dataset Composition**:

| Category | Count | Description |
|----------|-------|-------------|
| 1-line titles | 5 | Simple titles, no prefix/suffix |
| 2-line titles | 7 | Main + suffix |
| 3-line titles | 8 | Prefix + main + suffix |
| 0 images | 3 | No images in doc |
| 1-5 images | 10 | Typical image count |
| 6-10 images | 7 | High image count |
| With meta blocks | 12 | Has Meta Description/Keywords/Tags |
| Without meta blocks | 8 | Missing meta blocks |

**Ground Truth**:
- Manual verification by domain expert
- Stored in `backend/tests/fixtures/accuracy/ground_truth.json`

**Accuracy Metrics**:

| Field | Target Accuracy | Measurement Method |
|-------|-----------------|-------------------|
| Title (overall) | ≥90% | Exact match for prefix/main/suffix |
| Author | ≥95% | Exact match for author_name |
| Images (detection) | ≥90% | Correct count detected |
| Images (metadata) | 100% | All downloaded images have complete metadata |
| Meta description | ≥85% | Exact match |
| SEO keywords | ≥85% | Set equality (order doesn't matter) |
| Tags | ≥85% | Set equality |

**Test Cases**:

| Test ID | Test Case | Metrics | Priority |
|---------|-----------|---------|----------|
| ACC-001 | Parse 20 test docs | Overall accuracy ≥90% | P0 |
| ACC-002 | Measure title accuracy | Title accuracy ≥90% | P0 |
| ACC-003 | Measure author accuracy | Author accuracy ≥95% | P0 |
| ACC-004 | Measure image detection | Image detection ≥90% | P0 |
| ACC-005 | Verify image metadata | 100% of images have complete metadata | P0 |
| ACC-006 | Generate accuracy report | JSON report with per-field accuracy | P0 |

**Deliverable**: `docs/parsing-accuracy-report.json`

---

## 5. Performance Tests

### 5.1 Parsing Latency Tests

**File**: `backend/tests/performance/test_parsing_performance.py`

**Test Cases**:

| Test ID | Test Case | Input | Target Latency | Priority |
|---------|-----------|-------|----------------|----------|
| PERF-001 | Typical article (1500 words, 5 images) | Fixture: `typical_article.html` | ≤20 seconds (95th percentile) | P0 |
| PERF-002 | Small article (500 words, 1 image) | Fixture: `small_article.html` | ≤10 seconds | P1 |
| PERF-003 | Large article (3000 words, 10 images) | Fixture: `large_article.html` | ≤40 seconds | P1 |

**Profiling**:
- Identify bottlenecks using Python profiling tools
- Measure time spent in: AI parsing, image download, specs extraction, DOM cleaning

**Deliverable**: `docs/parsing-performance-benchmarks.md`

---

### 5.2 API Response Time Tests

**Test Cases**:

| Test ID | Endpoint | Target Response Time | Priority |
|---------|----------|----------------------|----------|
| PERF-004 | GET /v1/worklist/:id | <500ms | P0 |
| PERF-005 | POST /v1/worklist/:id/confirm-parsing | <300ms | P0 |

---

## 6. Edge Case & Regression Tests

### 6.1 Edge Cases

**File**: `backend/tests/edge_cases/test_parsing_edge_cases.py`

**Test Cases**:

| Test ID | Test Case | Input | Expected Behavior | Priority |
|---------|-----------|-------|-------------------|----------|
| EDGE-001 | Missing author | HTML without author line | author_line=None, author_name=None, no error | P0 |
| EDGE-002 | 0 images | HTML without images | Empty images array, no error | P0 |
| EDGE-003 | Malformed HTML | Invalid HTML structure | Parsing doesn't crash, logs error, partial result returned | P0 |
| EDGE-004 | Image download 403 | Source URL returns 403 | Retries 3x, logs error, saves partial result | P1 |
| EDGE-005 | Image download timeout | Source URL times out | Retries 3x, logs error, saves partial result | P1 |
| EDGE-006 | Corrupt image | Image file corrupt (PIL can't read) | Logs error, metadata=None for that image | P1 |
| EDGE-007 | Missing meta blocks | No "Meta Description：" block | meta_description=None, no error | P0 |
| EDGE-008 | Extremely long title (>500 chars) | Title exceeds VARCHAR limit | Truncated to 500 chars, warning logged | P1 |
| EDGE-009 | Special characters in title | Title with emoji, symbols | Correctly stored, no encoding errors | P1 |
| EDGE-010 | Multiple author lines | HTML with multiple "文／" lines | First match extracted, others ignored | P1 |

**Coverage**: All known edge cases have regression tests

---

### 6.2 Regression Tests

**Strategy**: All bug fixes must include regression tests

**Test Cases**:

| Test ID | Bug Description | Regression Test | Priority |
|---------|-----------------|-----------------|----------|
| REG-001 | [Bug to be discovered] | Test that bug doesn't recur | P0 |
| REG-002 | [Bug to be discovered] | Test that bug doesn't recur | P0 |

**Deliverable**: `docs/parsing-bug-fixes-log.md` (tracks all bugs and corresponding regression tests)

---

## 7. Test Execution Plan

### 7.1 Test Environment Setup

**Development Environment**:
- Local PostgreSQL database
- Mocked Claude API (fixture responses)
- Mocked storage backend
- Sample Google Doc fixtures

**Staging Environment**:
- Staging PostgreSQL database
- Real Claude API (limited usage)
- Staging storage backend (Supabase/Google Drive)
- Real Google Docs for integration testing

**Production Environment**:
- Production database
- Real Claude API
- Production storage backend
- Monitoring and alerting enabled

---

### 7.2 Test Schedule

| Phase | Tests | Duration | Dependencies |
|-------|-------|----------|--------------|
| Week 16 | Database migration tests (T7.4) | 2 hours | Alembic migration complete |
| Week 17-18 | Backend unit tests (UP-001 to UP-015, UIP-001 to UIP-008) | 8 hours | Parsing services implemented |
| Week 19 | API integration tests (IAP-001 to IAP-007, IGD-001 to IGD-004) | 4 hours | API endpoints implemented |
| Week 20-21 | Frontend unit tests (UFP-001 to UFP-006, UFC-001 to UFC-014) | 10 hours | UI components implemented |
| Week 21 | E2E tests (E2E-001 to E2E-004) | 8 hours | Full workflow implemented |
| Week 21 | Accuracy tests (ACC-001 to ACC-006) | 8 hours | Parsing service complete |
| Week 21 | Performance tests (PERF-001 to PERF-005) | 4 hours | Parsing service complete |
| Week 21 | Edge case tests (EDGE-001 to EDGE-010) | 4 hours | Bug fixes complete |

**Total Test Effort**: ~48 hours (included in Phase 7 estimates)

---

### 7.3 Continuous Integration

**CI Pipeline** (GitHub Actions / Jenkins):

```yaml
# .github/workflows/parsing-tests.yml
name: Article Parsing Tests

on:
  pull_request:
    paths:
      - 'backend/src/services/parser/**'
      - 'backend/src/services/media/**'
      - 'backend/src/models/article_image.py'
      - 'frontend/src/components/Proofreading/**'
      - 'frontend/src/stores/useParsingConfirmationStore.ts'

jobs:
  backend-unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      - name: Run unit tests
        run: |
          cd backend
          pytest tests/unit/services/parser/ -v --cov=src/services/parser --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd frontend && npm install
      - name: Run unit tests
        run: cd frontend && npm run test:unit -- --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Run API integration tests
        run: |
          cd backend
          pytest tests/integration/api/test_parsing_confirmation.py -v

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
      - name: Install Playwright
        run: cd frontend && npx playwright install
      - name: Run E2E tests
        run: cd frontend && npx playwright test e2e/parsing-confirmation-workflow.spec.ts
      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-screenshots
          path: frontend/e2e-results/
```

---

### 7.4 Test Reporting

**Coverage Reports**:
- Backend: Codecov integration
- Frontend: Codecov integration
- Target: ≥85% backend, ≥80% frontend

**Test Results Dashboard**:
- All tests visible in CI/CD pipeline
- Slack notifications on failures
- Test trend tracking over time

**Accuracy Reports**:
- Generated after every accuracy test run
- Stored in `docs/parsing-accuracy-report.json`
- Reviewed by team weekly

---

## 8. Success Criteria

### 8.1 Test Completion Criteria

- [ ] All P0 unit tests passing (100%)
- [ ] All P0 integration tests passing (100%)
- [ ] All P0 E2E tests passing (100%)
- [ ] Code coverage ≥85% (backend), ≥80% (frontend)
- [ ] Parsing accuracy ≥90% across all fields
- [ ] Parsing latency ≤20 seconds (95th percentile)
- [ ] All P0 edge cases handled gracefully
- [ ] Zero high-priority bugs remaining

### 8.2 Release Readiness Criteria

- [ ] All tests passing in CI/CD pipeline
- [ ] Performance benchmarks meet targets
- [ ] Accuracy report generated and reviewed
- [ ] Bug fixes log complete with regression tests
- [ ] Test documentation complete
- [ ] Team sign-off on test results

---

## 9. Risk Management

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| AI parsing accuracy <90% | Medium | High | Extensive test dataset; iterative prompt engineering; fallback heuristics |
| Test execution time too long (>10 min) | Medium | Medium | Parallel test execution; mock external services; optimize fixtures |
| Flaky E2E tests | Medium | Medium | Stable selectors; wait strategies; retry logic; deterministic test data |
| Low test coverage | Low | High | Enforce coverage thresholds in CI; code review checks coverage |
| Missing edge cases | Medium | Medium | Bug bash sessions; production monitoring; user feedback loop |

---

## 10. Appendix

### 10.1 Test Fixtures Location

- Backend: `backend/tests/fixtures/`
  - `sample_titles.json` - Title parsing variations
  - `sample_images/` - JPEG, PNG, WEBP samples
  - `accuracy/` - 20 Google Doc samples + ground truth
  - `performance/` - Typical, small, large article fixtures
- Frontend: `frontend/e2e/fixtures/`
  - `sample-google-doc.html` - E2E test input

### 10.2 Tools & Dependencies

**Backend Testing**:
- pytest 7.x
- pytest-cov (coverage)
- pytest-asyncio (async tests)
- pytest-mock (mocking)
- factory_boy (test factories)

**Frontend Testing**:
- Vitest (unit tests)
- @testing-library/react (component tests)
- Playwright (E2E tests)

**Performance Testing**:
- pytest-benchmark
- Python profiling (`cProfile`, `line_profiler`)

---

**Document Owner**: QA Lead
**Review Cycle**: After each test phase completion
**Contact**: qa-lead@example.com

---

**Status**: ✅ Test plan complete, ready for execution
