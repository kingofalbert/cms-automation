# Tasks: E2E Test Coverage & Production Regression Testing

**Feature**: 003-e2e-test-coverage
**Version**: 1.0.0
**Created**: 2025-11-04
**Status**: Ready for Implementation
**Related Documents**: [spec.md](./spec.md) | [plan.md](./plan.md) | [test-strategy.md](./test-strategy.md)

---

## Task Format Legend

```
- [ ] T### [P] [US#] Description with exact file path
```

**Components**:
- `- [ ]` Checkbox for task completion
- `T###` Sequential task ID (T001, T002, etc.)
- `[P]` Parallelizable marker (ONLY if no blocking dependencies)
- `[US#]` User story label ([US1], [US2], etc.) - OMIT for setup/foundational/polish tasks
- Description with exact file path to modified/created file

---

## Summary

**Total Estimated Duration**: 21 days (3 weeks)
**Total Tasks**: 245 tasks across 9 phases
**Priority Breakdown**:
- P0 (Critical): 120 tasks - Core module testing (Days 1-15)
- P1 (High): 85 tasks - Edge cases + Workflows (Days 16-21)
- P2 (Medium): 25 tasks - Performance + Polish
- Setup/Infrastructure: 15 tasks

**Success Criteria**:
- 85% functional coverage achieved (14/16 modules tested)
- 70% edge case coverage (network, security, performance)
- Cross-browser tests pass on Chrome, Firefox, Safari
- Performance budgets enforced (LCP < 2.5s, FID < 100ms, CLS < 0.1)
- Production smoke tests running hourly
- CI/CD pipeline executing on all PRs
- Test suite completes in < 15 minutes
- Flake rate < 5%

---

## Phase 0: Project Setup & Infrastructure (Days 1-2)

**Goal**: Set up test infrastructure, Page Object Model foundation, and test utilities

**Duration**: 2 days
**No [US#] labels in this phase**

### 0.1 Dependencies & Configuration (Day 1 Morning)

- [ ] T001 [P] Install Playwright dependencies in frontend/package.json (@playwright/test, playwright)
- [ ] T002 [P] Install Lighthouse CI in frontend/package.json (playwright-lighthouse)
- [ ] T003 [P] Install Axe accessibility testing in frontend/package.json (@axe-core/playwright)
- [ ] T004 [P] Install faker.js for test data in frontend/package.json (@faker-js/faker)
- [ ] T005 [P] Install PapaParse for CSV handling in frontend/package.json (papaparse, @types/papaparse)
- [ ] T006 Update Playwright config to support 3 browsers at frontend/playwright.config.ts
- [ ] T007 Add performance test configuration (Lighthouse thresholds) at frontend/playwright.config.ts
- [ ] T008 Configure test sharding (4 workers) at frontend/playwright.config.ts
- [ ] T009 Add test timeout and retry configuration at frontend/playwright.config.ts
- [ ] T010 Configure screenshot and video capture settings at frontend/playwright.config.ts

### 0.2 Directory Structure (Day 1 Afternoon)

- [ ] T011 [P] Create page-objects directory at frontend/tests/page-objects/
- [ ] T012 [P] Create fixtures directory at frontend/tests/fixtures/
- [ ] T013 [P] Create utils directory at frontend/tests/utils/
- [ ] T014 [P] Create edge-cases test directory at frontend/e2e/edge-cases/
- [ ] T015 [P] Create workflows test directory at frontend/e2e/workflows/
- [ ] T016 [P] Create cross-browser test directory at frontend/e2e/cross-browser/

### 0.3 Base Test Utilities (Day 2 Morning)

- [ ] T017 [P] Create test data factory for Article model at frontend/tests/utils/test-data-factory.ts
- [ ] T018 [P] Create test data factory for Task model at frontend/tests/utils/test-data-factory.ts
- [ ] T019 [P] Create test data factory for Rule model at frontend/tests/utils/test-data-factory.ts
- [ ] T020 [P] Create test data factory for User model at frontend/tests/utils/test-data-factory.ts
- [ ] T021 [P] Create CSV generator utility at frontend/tests/utils/csv-generator.ts
- [ ] T022 [P] Create JSON generator utility at frontend/tests/utils/json-generator.ts
- [ ] T023 [P] Create performance measurement helper at frontend/tests/utils/performance-helpers.ts
- [ ] T024 [P] Create screenshot comparison utility at frontend/tests/utils/screenshot-comparison.ts
- [ ] T025 [P] Create network mock utility at frontend/tests/fixtures/mock-api.ts
- [ ] T026 [P] Create browser context fixture at frontend/tests/fixtures/browser-contexts.ts

### 0.4 Base Page Objects (Day 2 Afternoon)

- [ ] T027 [P] Create base PageObject class with common methods at frontend/tests/page-objects/BasePage.ts
- [ ] T028 [P] Implement waitForLoadComplete method in BasePage
- [ ] T029 [P] Implement captureScreenshot method in BasePage
- [ ] T030 [P] Implement assertNoConsoleErrors method in BasePage
- [ ] T031 Create Navigation Page Object with menu methods at frontend/tests/page-objects/NavigationPage.ts

---

## Phase 1: Article Import Module (P0) (Days 3-4)

**Goal**: Implement comprehensive E2E tests for Article Import functionality

**Priority**: P0 - Critical (currently 0% coverage)
**User Story**: US1 - Article Import Edge Cases
**Duration**: 2 days

### 1.1 Page Object Model (Day 3 Morning)

- [ ] T032 [P] [US1] Create ArticleImportPage class at frontend/tests/page-objects/ArticleImportPage.ts
- [ ] T033 [P] [US1] Implement locators (file input, submit button, progress bar) in ArticleImportPage
- [ ] T034 [P] [US1] Implement uploadCSV method in ArticleImportPage
- [ ] T035 [P] [US1] Implement uploadJSON method in ArticleImportPage
- [ ] T036 [P] [US1] Implement submitForm method in ArticleImportPage
- [ ] T037 [P] [US1] Implement waitForCompletion method in ArticleImportPage
- [ ] T038 [P] [US1] Implement assertUploadSuccess method in ArticleImportPage
- [ ] T039 [P] [US1] Implement getErrorMessage method in ArticleImportPage

### 1.2 Happy Path Tests (Day 3 Afternoon)

- [ ] T040 [US1] Create article-import.spec.ts test file at frontend/e2e/article-import.spec.ts
- [ ] T041 [US1] Write test: Upload CSV with 10 articles (basic import) at frontend/e2e/article-import.spec.ts
- [ ] T042 [US1] Write test: Upload CSV with 100 articles (medium batch) at frontend/e2e/article-import.spec.ts
- [ ] T043 [US1] Write test: Upload JSON with 50 articles at frontend/e2e/article-import.spec.ts
- [ ] T044 [US1] Write test: Manual article creation via form at frontend/e2e/article-import.spec.ts
- [ ] T045 [US1] Write test: Verify import history table updates at frontend/e2e/article-import.spec.ts

### 1.3 Edge Case Tests (Day 4 Morning)

- [ ] T046 [US1] Write test: Upload CSV with XSS injection attempts at frontend/e2e/article-import.spec.ts
- [ ] T047 [US1] Write test: Upload CSV with SQL injection attempts at frontend/e2e/article-import.spec.ts
- [ ] T048 [US1] Write test: Upload malformed CSV (invalid UTF-8) at frontend/e2e/article-import.spec.ts
- [ ] T049 [US1] Write test: Upload large CSV (1000+ articles) at frontend/e2e/article-import.spec.ts
- [ ] T050 [US1] Write test: Upload empty CSV file at frontend/e2e/article-import.spec.ts
- [ ] T051 [US1] Write test: Upload CSV with missing required fields at frontend/e2e/article-import.spec.ts
- [ ] T052 [US1] Write test: Network failure during upload (retry logic) at frontend/e2e/article-import.spec.ts

### 1.4 Google Drive Integration Tests (Day 4 Afternoon)

- [ ] T053 [US1] Write test: Google Drive file picker opens at frontend/e2e/article-import.spec.ts
- [ ] T054 [US1] Write test: Select file from Google Drive at frontend/e2e/article-import.spec.ts
- [ ] T055 [US1] Write test: Network interruption during Drive sync at frontend/e2e/article-import.spec.ts
- [ ] T056 [US1] Write test: Google Drive authentication flow at frontend/e2e/article-import.spec.ts

---

## Phase 2: Article List Module (P0) (Days 5-6)

**Goal**: Implement E2E tests for Article List with performance validation

**Priority**: P0 - Critical (currently 0% coverage)
**User Story**: US2 - Article List Performance & UX
**Duration**: 2 days

### 2.1 Page Object Model (Day 5 Morning)

- [ ] T057 [P] [US2] Create ArticleListPage class at frontend/tests/page-objects/ArticleListPage.ts
- [ ] T058 [P] [US2] Implement locators (table, pagination, search, filters) in ArticleListPage
- [ ] T059 [P] [US2] Implement getArticleCount method in ArticleListPage
- [ ] T060 [P] [US2] Implement searchArticles method in ArticleListPage
- [ ] T061 [P] [US2] Implement filterByStatus method in ArticleListPage
- [ ] T062 [P] [US2] Implement sortByColumn method in ArticleListPage
- [ ] T063 [P] [US2] Implement selectArticle method in ArticleListPage
- [ ] T064 [P] [US2] Implement goToPage method (pagination) in ArticleListPage

### 2.2 Happy Path Tests (Day 5 Afternoon)

- [ ] T065 [US2] Create article-list.spec.ts test file at frontend/e2e/article-list.spec.ts
- [ ] T066 [US2] Write test: Display article list with 50 items at frontend/e2e/article-list.spec.ts
- [ ] T067 [US2] Write test: Pagination works correctly (navigate to page 2) at frontend/e2e/article-list.spec.ts
- [ ] T068 [US2] Write test: Search by article title at frontend/e2e/article-list.spec.ts
- [ ] T069 [US2] Write test: Filter by status (draft/published) at frontend/e2e/article-list.spec.ts
- [ ] T070 [US2] Write test: Sort by date (ascending/descending) at frontend/e2e/article-list.spec.ts
- [ ] T071 [US2] Write test: Select article and navigate to review at frontend/e2e/article-list.spec.ts

### 2.3 Performance Tests (Day 6 Morning)

- [ ] T072 [US2] Write test: Load 1,000 articles (virtual scroll performance) at frontend/e2e/edge-cases/performance.spec.ts
- [ ] T073 [US2] Write test: Measure LCP < 2.5s on article list page at frontend/e2e/edge-cases/performance.spec.ts
- [ ] T074 [US2] Write test: Verify smooth scrolling (60fps) at frontend/e2e/edge-cases/performance.spec.ts
- [ ] T075 [US2] Write test: Image lazy loading (load 500px before viewport) at frontend/e2e/edge-cases/performance.spec.ts

### 2.4 Real-Time Updates Tests (Day 6 Afternoon)

- [ ] T076 [US2] Write test: WebSocket real-time update when new article published at frontend/e2e/article-list.spec.ts
- [ ] T077 [US2] Write test: WebSocket fallback to polling on disconnection at frontend/e2e/article-list.spec.ts
- [ ] T078 [US2] Write test: Maintain scroll position on list update at frontend/e2e/article-list.spec.ts

---

## Phase 3: Article Review Module (P0) (Days 7-8)

**Goal**: Implement E2E tests for Article Review workflow

**Priority**: P0 - Critical (currently 0% coverage)
**User Story**: Related to US1 (content management)
**Duration**: 2 days

### 3.1 Page Object Model (Day 7 Morning)

- [ ] T079 [P] Create ArticleReviewPage class at frontend/tests/page-objects/ArticleReviewPage.ts
- [ ] T080 [P] Implement locators (content editor, SEO panel, proofreading results) in ArticleReviewPage
- [ ] T081 [P] Implement getArticleContent method in ArticleReviewPage
- [ ] T082 [P] Implement editContent method in ArticleReviewPage
- [ ] T083 [P] Implement getSEOScore method in ArticleReviewPage
- [ ] T084 [P] Implement getProofreadingIssues method in ArticleReviewPage
- [ ] T085 [P] Implement saveDraft method in ArticleReviewPage
- [ ] T086 [P] Implement submitForApproval method in ArticleReviewPage

### 3.2 Happy Path Tests (Day 7 Afternoon)

- [ ] T087 Create article-review.spec.ts test file at frontend/e2e/article-review.spec.ts
- [ ] T088 Write test: Load article for review at frontend/e2e/article-review.spec.ts
- [ ] T089 Write test: Edit article content and save draft at frontend/e2e/article-review.spec.ts
- [ ] T090 Write test: View SEO optimization suggestions at frontend/e2e/article-review.spec.ts
- [ ] T091 Write test: View proofreading issues at frontend/e2e/article-review.spec.ts
- [ ] T092 Write test: Accept proofreading suggestion at frontend/e2e/article-review.spec.ts
- [ ] T093 Write test: Submit article for approval at frontend/e2e/article-review.spec.ts

### 3.3 Edge Case Tests (Day 8)

- [ ] T094 Write test: Auto-save triggers every 30 seconds at frontend/e2e/article-review.spec.ts
- [ ] T095 Write test: Network failure during auto-save (retry logic) at frontend/e2e/article-review.spec.ts
- [ ] T096 Write test: Concurrent edit conflict detection at frontend/e2e/article-review.spec.ts
- [ ] T097 Write test: Unsaved changes warning on navigation at frontend/e2e/article-review.spec.ts

---

## Phase 4: Publish Tasks Module (P0) (Days 9-10)

**Goal**: Implement E2E tests for Publish Task monitoring

**Priority**: P0 - Critical (currently 0% coverage)
**User Story**: US3 - Publish Tasks Real-Time Monitoring
**Duration**: 2 days

### 4.1 Page Object Model (Day 9 Morning)

- [ ] T098 [P] [US3] Create PublishTasksPage class at frontend/tests/page-objects/PublishTasksPage.ts
- [ ] T099 [P] [US3] Implement locators (task list, progress bar, status badges) in PublishTasksPage
- [ ] T100 [P] [US3] Implement getTaskStatus method in PublishTasksPage
- [ ] T101 [P] [US3] Implement getOverallProgress method in PublishTasksPage
- [ ] T102 [P] [US3] Implement retryFailedTasks method in PublishTasksPage
- [ ] T103 [P] [US3] Implement cancelBatch method in PublishTasksPage
- [ ] T104 [P] [US3] Implement getErrorDetails method in PublishTasksPage

### 4.2 Happy Path Tests (Day 9 Afternoon)

- [ ] T105 [US3] Create publish-tasks.spec.ts test file at frontend/e2e/publish-tasks.spec.ts
- [ ] T106 [US3] Write test: Display task list with 10 publishing tasks at frontend/e2e/publish-tasks.spec.ts
- [ ] T107 [US3] Write test: Real-time progress updates (0% → 100%) at frontend/e2e/publish-tasks.spec.ts
- [ ] T108 [US3] Write test: Task status changes (queued → publishing → published) at frontend/e2e/publish-tasks.spec.ts
- [ ] T109 [US3] Write test: Overall progress indicator updates at frontend/e2e/publish-tasks.spec.ts

### 4.3 Error Handling Tests (Day 10 Morning)

- [ ] T110 [US3] Write test: Failed task shows error badge and details at frontend/e2e/publish-tasks.spec.ts
- [ ] T111 [US3] Write test: Retry failed tasks (exponential backoff) at frontend/e2e/publish-tasks.spec.ts
- [ ] T112 [US3] Write test: Batch cancel stops all pending tasks at frontend/e2e/publish-tasks.spec.ts
- [ ] T113 [US3] Write test: Error toast notification on failures at frontend/e2e/publish-tasks.spec.ts

### 4.4 WebSocket Tests (Day 10 Afternoon)

- [ ] T114 [US3] Write test: WebSocket real-time updates work at frontend/e2e/publish-tasks.spec.ts
- [ ] T115 [US3] Write test: WebSocket disconnection → polling fallback at frontend/e2e/publish-tasks.spec.ts
- [ ] T116 [US3] Write test: WebSocket reconnection resumes live updates at frontend/e2e/publish-tasks.spec.ts

---

## Phase 5: Remaining Core Modules (P0) (Days 11-13)

**Goal**: Complete E2E tests for Worklist, Schedule, Tags, Provider Comparison

**Priority**: P0 - Critical
**Duration**: 3 days

### 5.1 Worklist Module (Day 11)

- [ ] T117 [P] Create WorklistPage class at frontend/tests/page-objects/WorklistPage.ts
- [ ] T118 [P] Implement locators (worklist table, status badges, filters) in WorklistPage
- [ ] T119 [P] Implement getWorklistItems method in WorklistPage
- [ ] T120 [P] Implement filterByPriority method in WorklistPage
- [ ] T121 [P] Implement markAsComplete method in WorklistPage
- [ ] T122 Create worklist.spec.ts test file at frontend/e2e/worklist.spec.ts
- [ ] T123 Write test: Display worklist with 20 items at frontend/e2e/worklist.spec.ts
- [ ] T124 Write test: Filter by priority (high/medium/low) at frontend/e2e/worklist.spec.ts
- [ ] T125 Write test: Mark item as complete at frontend/e2e/worklist.spec.ts
- [ ] T126 Write test: Sort by priority at frontend/e2e/worklist.spec.ts

### 5.2 Schedule Manager Module (Day 12 Morning)

- [ ] T127 [P] Create ScheduleManagerPage class at frontend/tests/page-objects/ScheduleManagerPage.ts
- [ ] T128 [P] Implement locators (calendar, schedule forms, modals) in ScheduleManagerPage
- [ ] T129 [P] Implement createSchedule method in ScheduleManagerPage
- [ ] T130 [P] Implement editSchedule method in ScheduleManagerPage
- [ ] T131 [P] Implement deleteSchedule method in ScheduleManagerPage
- [ ] T132 Create schedule.spec.ts test file at frontend/e2e/schedule.spec.ts
- [ ] T133 Write test: Create new schedule with date/time at frontend/e2e/schedule.spec.ts
- [ ] T134 Write test: Edit existing schedule at frontend/e2e/schedule.spec.ts
- [ ] T135 Write test: Delete schedule at frontend/e2e/schedule.spec.ts
- [ ] T136 Write test: Conflict detection (overlapping schedules) at frontend/e2e/schedule.spec.ts

### 5.3 Tags Module (Day 12 Afternoon)

- [ ] T137 [P] Create TagsPage class at frontend/tests/page-objects/TagsPage.ts
- [ ] T138 [P] Implement locators (tag list, create form, search) in TagsPage
- [ ] T139 [P] Implement createTag method in TagsPage
- [ ] T140 [P] Implement editTag method in TagsPage
- [ ] T141 [P] Implement deleteTag method in TagsPage
- [ ] T142 [P] Implement searchTags method in TagsPage
- [ ] T143 Create tags.spec.ts test file at frontend/e2e/tags.spec.ts
- [ ] T144 Write test: Create new tag at frontend/e2e/tags.spec.ts
- [ ] T145 Write test: Edit tag name at frontend/e2e/tags.spec.ts
- [ ] T146 Write test: Delete tag at frontend/e2e/tags.spec.ts
- [ ] T147 Write test: Search tags by name at frontend/e2e/tags.spec.ts

### 5.4 Provider Comparison Module (Day 13)

- [ ] T148 [P] Create ProviderComparisonPage class at frontend/tests/page-objects/ProviderComparisonPage.ts
- [ ] T149 [P] Implement locators (charts, comparison table, filters) in ProviderComparisonPage
- [ ] T150 [P] Implement getPerformanceChart method in ProviderComparisonPage
- [ ] T151 [P] Implement getCostComparison method in ProviderComparisonPage
- [ ] T152 [P] Implement filterByDateRange method in ProviderComparisonPage
- [ ] T153 Create provider-comparison.spec.ts test file at frontend/e2e/provider-comparison.spec.ts
- [ ] T154 Write test: Display performance comparison chart at frontend/e2e/provider-comparison.spec.ts
- [ ] T155 Write test: Show cost breakdown by provider at frontend/e2e/provider-comparison.spec.ts
- [ ] T156 Write test: Filter comparison by date range at frontend/e2e/provider-comparison.spec.ts
- [ ] T157 Write test: Recommendation card displays at frontend/e2e/provider-comparison.spec.ts

---

## Phase 6: Proofreading Modules (P0) (Days 14-15)

**Goal**: Implement E2E tests for Proofreading Rules and Stats

**Priority**: P0 - Critical
**Duration**: 2 days

### 6.1 Proofreading Rules Module (Day 14)

- [ ] T158 [P] Create ProofreadingRulesPage class at frontend/tests/page-objects/ProofreadingRulesPage.ts
- [ ] T159 [P] Implement locators (rule list, editor, test panel) in ProofreadingRulesPage
- [ ] T160 [P] Implement getRuleDrafts method in ProofreadingRulesPage
- [ ] T161 [P] Implement createRule method in ProofreadingRulesPage
- [ ] T162 [P] Implement editRule method in ProofreadingRulesPage
- [ ] T163 [P] Implement testRule method in ProofreadingRulesPage
- [ ] T164 [P] Implement publishRule method in ProofreadingRulesPage
- [ ] T165 Create proofreading-rules.spec.ts test file at frontend/e2e/proofreading-rules.spec.ts
- [ ] T166 Write test: Display rule draft list at frontend/e2e/proofreading-rules.spec.ts
- [ ] T167 Write test: Create new rule via natural language editor at frontend/e2e/proofreading-rules.spec.ts
- [ ] T168 Write test: Edit rule and see code preview update at frontend/e2e/proofreading-rules.spec.ts
- [ ] T169 Write test: Test rule against sample text at frontend/e2e/proofreading-rules.spec.ts
- [ ] T170 Write test: Publish rule to production at frontend/e2e/proofreading-rules.spec.ts

### 6.2 Proofreading Stats Module (Day 15)

- [ ] T171 [P] Create ProofreadingStatsPage class at frontend/tests/page-objects/ProofreadingStatsPage.ts
- [ ] T172 [P] Implement locators (charts, metrics, filters) in ProofreadingStatsPage
- [ ] T173 [P] Implement getRuleUsageChart method in ProofreadingStatsPage
- [ ] T174 [P] Implement getEffectivenessMetrics method in ProofreadingStatsPage
- [ ] T175 [P] Implement filterByTimeRange method in ProofreadingStatsPage
- [ ] T176 Create proofreading-stats.spec.ts test file at frontend/e2e/proofreading-stats.spec.ts
- [ ] T177 Write test: Display rule usage frequency chart at frontend/e2e/proofreading-stats.spec.ts
- [ ] T178 Write test: Show effectiveness metrics at frontend/e2e/proofreading-stats.spec.ts
- [ ] T179 Write test: Filter stats by time range (7d/30d/90d) at frontend/e2e/proofreading-stats.spec.ts

---

## Phase 7: Edge Cases & Security (P1) (Days 16-17)

**Goal**: Comprehensive edge case and security testing

**Priority**: P1 - High
**Duration**: 2 days

### 7.1 Network Error Tests (Day 16 Morning)

- [ ] T180 [P] Create network-errors.spec.ts test file at frontend/e2e/edge-cases/network-errors.spec.ts
- [ ] T181 Write test: API timeout (10s) handling at frontend/e2e/edge-cases/network-errors.spec.ts
- [ ] T182 Write test: Network disconnection during page load at frontend/e2e/edge-cases/network-errors.spec.ts
- [ ] T183 Write test: Slow network (3G simulation) at frontend/e2e/edge-cases/network-errors.spec.ts
- [ ] T184 Write test: 500 Server Error handling at frontend/e2e/edge-cases/network-errors.spec.ts
- [ ] T185 Write test: 503 Service Unavailable handling at frontend/e2e/edge-cases/network-errors.spec.ts
- [ ] T186 Write test: Retry logic with exponential backoff at frontend/e2e/edge-cases/network-errors.spec.ts

### 7.2 File Upload Edge Cases (Day 16 Afternoon)

- [ ] T187 [P] Create file-upload.spec.ts test file at frontend/e2e/edge-cases/file-upload.spec.ts
- [ ] T188 Write test: Upload file larger than 100MB at frontend/e2e/edge-cases/file-upload.spec.ts
- [ ] T189 Write test: Upload invalid file type (.exe) at frontend/e2e/edge-cases/file-upload.spec.ts
- [ ] T190 Write test: Upload corrupted CSV file at frontend/e2e/edge-cases/file-upload.spec.ts
- [ ] T191 Write test: Upload progress tracking (0-100%) at frontend/e2e/edge-cases/file-upload.spec.ts
- [ ] T192 Write test: Cancel upload mid-way at frontend/e2e/edge-cases/file-upload.spec.ts
- [ ] T193 Write test: Network failure during upload (resume) at frontend/e2e/edge-cases/file-upload.spec.ts

### 7.3 Security Tests (Day 17)

- [ ] T194 [P] [US4] Create security.spec.ts test file at frontend/e2e/edge-cases/security.spec.ts
- [ ] T195 [US4] Write test: XSS injection in article title blocked at frontend/e2e/edge-cases/security.spec.ts
- [ ] T196 [US4] Write test: XSS injection in article content blocked at frontend/e2e/edge-cases/security.spec.ts
- [ ] T197 [US4] Write test: SQL injection in search blocked at frontend/e2e/edge-cases/security.spec.ts
- [ ] T198 [US4] Write test: SQL injection in filter blocked at frontend/e2e/edge-cases/security.spec.ts
- [ ] T199 [US4] Write test: WordPress URL validation (no javascript:) at frontend/e2e/edge-cases/security.spec.ts
- [ ] T200 [US4] Write test: API key masked in UI at frontend/e2e/edge-cases/security.spec.ts
- [ ] T201 [US4] Write test: Password never logged in console at frontend/e2e/edge-cases/security.spec.ts
- [ ] T202 [US4] Write test: 100,000 character input rejected at frontend/e2e/edge-cases/security.spec.ts

---

## Phase 8: Workflows & Cross-Browser (P1) (Days 18-19)

**Goal**: End-to-end workflow tests and cross-browser validation

**Priority**: P1 - High
**Duration**: 2 days

### 8.1 Critical Workflows (Day 18)

- [ ] T203 [P] [US7] Create complete-publish.spec.ts test file at frontend/e2e/workflows/complete-publish.spec.ts
- [ ] T204 [US7] Write workflow: Import CSV → SEO → Proofread → Publish at frontend/e2e/workflows/complete-publish.spec.ts
- [ ] T205 [US7] Write workflow: Batch import 1000 articles → validate → import at frontend/e2e/workflows/batch-import.spec.ts
- [ ] T206 [US7] Create concurrent-publish.spec.ts test file at frontend/e2e/workflows/concurrent-publish.spec.ts
- [ ] T207 [US7] Write workflow: 10 concurrent publish tasks at frontend/e2e/workflows/concurrent-publish.spec.ts
- [ ] T208 [US7] Create error-recovery.spec.ts test file at frontend/e2e/workflows/error-recovery.spec.ts
- [ ] T209 [US7] Write workflow: Network failure → retry → success at frontend/e2e/workflows/error-recovery.spec.ts

### 8.2 Cross-Browser Tests (Day 19)

- [ ] T210 [P] [US5] Create firefox.spec.ts test file at frontend/e2e/cross-browser/firefox.spec.ts
- [ ] T211 [US5] Write test: Navigation menu works in Firefox at frontend/e2e/cross-browser/firefox.spec.ts
- [ ] T212 [US5] Write test: Article import works in Firefox at frontend/e2e/cross-browser/firefox.spec.ts
- [ ] T213 [US5] Write test: Date picker works in Firefox at frontend/e2e/cross-browser/firefox.spec.ts
- [ ] T214 [P] [US5] Create safari.spec.ts test file at frontend/e2e/cross-browser/safari.spec.ts
- [ ] T215 [US5] Write test: Navigation menu works in Safari at frontend/e2e/cross-browser/safari.spec.ts
- [ ] T216 [US5] Write test: Article import works in Safari at frontend/e2e/cross-browser/safari.spec.ts
- [ ] T217 [US5] Write test: WebSocket fallback works in Safari at frontend/e2e/cross-browser/safari.spec.ts

---

## Phase 9: Production Monitoring & CI/CD (P1) (Days 20-21)

**Goal**: Set up production monitoring, CI/CD pipeline, and performance budgets

**Priority**: P1 - High
**Duration**: 2 days

### 9.1 Production Smoke Tests (Day 20 Morning)

- [ ] T218 [P] Create production-smoke.spec.ts test file at frontend/e2e/production-smoke.spec.ts
- [ ] T219 Write test: Homepage loads successfully at frontend/e2e/production-smoke.spec.ts
- [ ] T220 Write test: API health check passes at frontend/e2e/production-smoke.spec.ts
- [ ] T221 Write test: Navigation menu renders at frontend/e2e/production-smoke.spec.ts
- [ ] T222 Write test: Settings page accessible at frontend/e2e/production-smoke.spec.ts

### 9.2 Performance Budget Tests (Day 20 Afternoon)

- [ ] T223 [P] [US6] Enhance performance.spec.ts with Lighthouse CI at frontend/e2e/edge-cases/performance.spec.ts
- [ ] T224 [US6] Write test: Homepage LCP < 2.5s at frontend/e2e/edge-cases/performance.spec.ts
- [ ] T225 [US6] Write test: Homepage FID < 100ms at frontend/e2e/edge-cases/performance.spec.ts
- [ ] T226 [US6] Write test: Homepage CLS < 0.1 at frontend/e2e/edge-cases/performance.spec.ts
- [ ] T227 [US6] Write test: Article list page LCP < 2.5s at frontend/e2e/edge-cases/performance.spec.ts
- [ ] T228 [US6] Write test: Bundle size < 500KB gzipped at frontend/e2e/edge-cases/performance.spec.ts

### 9.3 CI/CD Integration (Day 21 Morning)

- [ ] T229 Create GitHub Actions workflow at .github/workflows/e2e-tests.yml
- [ ] T230 Configure multi-browser matrix (Chrome, Firefox, Safari) in workflow
- [ ] T231 Add test sharding configuration (4 shards) in workflow
- [ ] T232 Configure Lighthouse CI in workflow
- [ ] T233 Add test result artifact upload in workflow
- [ ] T234 Add performance report upload in workflow

### 9.4 Monitoring & Alerting (Day 21 Afternoon)

- [ ] T235 Create hourly cron job for production smoke tests at .github/workflows/production-monitoring.yml
- [ ] T236 Add Slack notification on test failure at .github/workflows/production-monitoring.yml
- [ ] T237 Create flake detection script at frontend/scripts/detect-flakes.js
- [ ] T238 Integrate flake detection in CI workflow
- [ ] T239 Create quarantine system for flaky tests at .playwright/quarantined-tests.json
- [ ] T240 Create test coverage dashboard (HTML report) configuration
- [ ] T241 Add coverage tracking to CI workflow
- [ ] T242 Create performance trend dashboard configuration

### 9.5 Documentation (Day 21)

- [ ] T243 Create test execution guide at frontend/tests/README.md
- [ ] T244 Document Page Object Model patterns at frontend/tests/page-objects/README.md
- [ ] T245 Create troubleshooting guide for flaky tests at frontend/tests/TROUBLESHOOTING.md

---

## Task Dependencies

### Critical Path (Must Complete in Order)
1. Phase 0 (Setup) → All other phases
2. Phase 0.3 (Test Utilities) → Phase 1-6 (Module Tests)
3. Phase 0.4 (Base Page Objects) → Phase 1-6 (Module Tests)
4. Phase 1-6 (Module Tests) → Phase 7-8 (Edge Cases, Workflows)
5. Phase 7-8 → Phase 9 (Production Monitoring)

### Parallelizable Phases
- Phase 1-6 modules can be implemented in parallel (different developers)
- Phase 7 edge case tests can run in parallel (network, file, security)
- Phase 8 workflow tests can run in parallel

---

## Acceptance Criteria Checklist

### Coverage Metrics
- [ ] 85% functional coverage achieved (14/16 modules tested)
- [ ] 70% edge case coverage (network, security, performance)
- [ ] 95% critical path coverage (all P0 workflows)

### Quality Metrics
- [ ] Cross-browser tests pass on Chrome, Firefox, Safari (100% pass rate)
- [ ] Performance budgets enforced (LCP < 2.5s, FID < 100ms, CLS < 0.1)
- [ ] Flake rate < 5% with automatic quarantine
- [ ] Test suite completes in < 15 minutes (full run)

### Production Monitoring
- [ ] Production smoke tests running hourly
- [ ] Slack alerts configured for failures
- [ ] Monitoring dashboard deployed
- [ ] Performance trend tracking active

### CI/CD Integration
- [ ] GitHub Actions workflow executing on all PRs
- [ ] Multi-browser matrix configured (3 browsers)
- [ ] Test result artifacts uploaded
- [ ] Coverage reports generated

### Documentation
- [ ] Test execution guide complete
- [ ] Page Object Model patterns documented
- [ ] Troubleshooting guide published

---

## Related Documents

- [spec.md](./spec.md) - Feature specification with user stories
- [plan.md](./plan.md) - Implementation strategy and architecture
- [test-strategy.md](./test-strategy.md) - Testing patterns and methodologies
- `/PLAYWRIGHT_TEST_COVERAGE_ANALYSIS.md` - Current coverage analysis
- [contracts/page-objects.md](./contracts/page-objects.md) - Page Object interfaces (to be created)
- [contracts/test-data.md](./contracts/test-data.md) - Test data schemas (to be created)
