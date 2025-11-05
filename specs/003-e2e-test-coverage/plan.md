# Implementation Plan: E2E Test Coverage & Production Regression Testing

**Branch**: `003-e2e-test-coverage` | **Date**: 2025-11-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-e2e-test-coverage/spec.md` and `PLAYWRIGHT_TEST_COVERAGE_ANALYSIS.md`

## Summary

This plan implements comprehensive end-to-end test coverage to address critical gaps identified in production testing. Currently, only 37.5% of application functionality is covered by E2E tests, leaving significant blind spots for regressions, edge cases, and cross-browser issues. This initiative will increase coverage to 85%, implement multi-browser testing, enforce performance budgets, and establish continuous monitoring for production stability.

**Technical Approach**: Expand existing Playwright test infrastructure with systematic coverage of all 16 modules, cross-browser test execution (Chrome, Firefox, Safari), performance validation using Lighthouse CI, and production smoke testing with continuous monitoring. No application code changes required—pure testing enhancement.

**Deliverables**:
- E2E tests for 10 currently untested modules (Article Import, List, Review, Tasks, Comparison, Worklist, Schedule, Tags, Proofreading Rules, Stats)
- Edge case coverage: network errors (timeout, disconnection), file upload failures, XSS/injection attacks, race conditions
- Multi-browser test suite (Chrome, Firefox, Safari) with 100% pass rate
- Performance budget enforcement (LCP < 2.5s, FID < 100ms, CLS < 0.1)
- Production monitoring with hourly smoke tests and alerting
- Complete E2E workflow tests (Import → SEO → Proofreading → Publish)

## Technical Context

**Language/Version**: TypeScript 5.x + Playwright 1.40+
**Primary Dependencies**:
- **Playwright 1.40+**: E2E testing framework with cross-browser support
- **@axe-core/playwright**: Accessibility testing
- **lighthouse**: Performance auditing
- **@playwright/test**: Test runner with parallel execution
- **playwright-core**: Browser automation primitives

**Storage**: Test database (PostgreSQL) with seeding/cleanup scripts
**Testing Stack**:
- **Playwright**: E2E test runner
- **Lighthouse CI**: Performance budgets
- **Axe**: Accessibility validation
- **GitHub Actions**: CI/CD automation

**Target Platform**: Chrome 120+, Firefox 120+, Safari 17+, Edge 120+
**Project Type**: Web application testing (frontend + backend integration)

**Performance Goals**:
- Test suite execution: < 15 minutes (full run with 4 parallel workers)
- CI feedback time: < 20 minutes (from commit to result)
- Flake rate: < 5% (auto-quarantine flaky tests)
- Cross-browser compatibility: 100% pass rate on all browsers

**Constraints**:
- Must not modify application code (testing-only changes)
- Cannot pollute production database (read-only tests, isolated test data)
- Must maintain backward compatibility (existing tests continue passing)
- CI resource limits: 4 parallel workers max (GitHub Actions free tier)
- Test data isolation: Each test uses independent database/browser context

**Scale/Scope**:
- 16 application modules to cover (10 new, 6 enhanced)
- ~150 new test cases to write (currently 147, targeting 300+)
- 3 browsers to support (Chrome, Firefox, Safari)
- 5 critical workflows to validate end-to-end
- Timeline: 21 days (3 weeks) across 3 phases

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Modularity ✅ PASS

**Assessment**: Test suite follows modular design with Page Object Model, test data factories, and reusable fixtures.

- ✅ Clear boundaries: Each test file corresponds to one module/page (e.g., `article-import.spec.ts`)
- ✅ Single responsibility: Tests focus on one user scenario per test case
- ✅ Dependency inversion: Page Object Model abstracts DOM selectors from test logic
- ✅ Independent testing: Tests run in isolated browser contexts with independent test data

**Example**:
```typescript
// ❌ Bad: Direct DOM manipulation in test
test('import article', async ({ page }) => {
  await page.click('button[type="submit"]');
});

// ✅ Good: Page Object abstraction
test('import article', async ({ page }) => {
  const importPage = new ArticleImportPage(page);
  await importPage.submitForm();
});
```

**Compliance**: Full compliance. Page Object Model enforces modularity.

### II. Observability ✅ PASS

**Assessment**: Test infrastructure provides comprehensive observability for debugging failures, tracking performance, and monitoring production health.

- ✅ Structured logging: Test output uses structured format with context (test name, duration, browser)
- ✅ Performance metrics: Lighthouse CI tracks LCP/FID/CLS, test duration logged
- ✅ Audit trails: Screenshots, videos, and trace files captured for all failures
- ✅ Health checks: Production smoke tests run hourly with alerting

**Test Output Example**:
```json
{
  "test": "Article Import - Large CSV",
  "browser": "chromium",
  "duration": "3.2s",
  "status": "passed",
  "screenshots": ["upload-start.png", "upload-complete.png"],
  "performance": {
    "LCP": "1.8s",
    "FID": "45ms",
    "CLS": "0.05"
  }
}
```

**Compliance**: Full compliance. Observability built into test infrastructure.

### III. Security ✅ PASS

**Assessment**: Test suite validates security controls without introducing vulnerabilities.

- ✅ Authentication: Tests use isolated test accounts (not production credentials)
- ✅ Authorization: Tests verify RBAC enforcement (no privilege escalation)
- ✅ Input validation: XSS/injection attack tests verify sanitization
- ✅ Secret management: Credentials stored in environment variables (never hardcoded)
- ✅ Audit logging: Test actions logged separately from production

**Security Test Examples**:
```typescript
test('blocks XSS injection in article title', async ({ page }) => {
  await importPage.enterTitle('<script>alert("xss")</script>');
  await importPage.submit();

  // Verify script tag is sanitized
  const savedTitle = await articlePage.getTitle();
  expect(savedTitle).not.toContain('<script>');
});

test('prevents SQL injection in search', async ({ page }) => {
  await articleList.search("' OR '1'='1");

  // Verify no database error, query is escaped
  const results = await articleList.getResults();
  expect(results).toHaveLength(0); // No articles match literal string
});
```

**Compliance**: Full compliance. Security testing enhances application security posture.

### IV. Testability ✅ PASS

**Assessment**: Meta-testing—tests are themselves testable through smoke tests, flake detection, and coverage tracking.

- ✅ Contract tests: E2E tests validate user acceptance criteria from spec.md
- ✅ Integration tests: Full workflows tested (Import → SEO → Publish)
- ✅ Unit tests: Test utilities and Page Objects have unit tests
- ✅ Coverage threshold: 85% functional coverage, 70% edge case coverage

**TDD Workflow for Test Development**:
1. **Red**: Write failing test based on user story acceptance criteria
2. **Green**: Verify test fails correctly (app doesn't implement feature yet)
3. **Implement**: Application code added (separate PR)
4. **Refactor**: Optimize test selectors, extract Page Objects
5. **Review**: QA validates test accurately captures user story

**Test for Flaky Tests**:
```typescript
// Automated flake detection
test('detect flaky tests', async () => {
  const results = await runTestSuite(100); // Run 100 times
  const passRate = results.filter(r => r.status === 'passed').length / 100;

  if (passRate < 0.95) {
    quarantineTest('article-import-large-csv');
    notifyTeam('Flaky test detected: pass rate ' + passRate);
  }
});
```

**Compliance**: Full compliance. Testing infrastructure is testable and monitored.

### V. API-First Design ✅ PASS

**Assessment**: Tests interact with application through public APIs (UI as API for E2E tests).

- ✅ OpenAPI specification: Tests validate API contracts defined in backend OpenAPI spec
- ✅ RESTful conventions: API tests follow REST principles (GET, POST, PUT, DELETE)
- ✅ Versioning: Tests target versioned endpoints (/v1/articles)
- ✅ Error format: Tests verify standardized error responses
- ✅ Documentation: Test cases serve as living documentation of API behavior

**API Test Example**:
```typescript
test('GET /v1/articles returns paginated results', async ({ request }) => {
  const response = await request.get('/v1/articles?offset=0&limit=10');

  expect(response.status()).toBe(200);
  const data = await response.json();

  // Verify OpenAPI contract
  expect(data).toMatchSchema({
    type: 'array',
    items: { $ref: '#/components/schemas/Article' },
    maxItems: 10
  });
});
```

**Compliance**: Full compliance. Tests validate API contracts.

### Constitution Compliance Summary

**Status**: ✅ **APPROVED** - Proceed to Phase 0 Research

All principles satisfied. Test infrastructure aligns with project constitution. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/003-e2e-test-coverage/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0: Coverage gap analysis, browser matrix
├── test-strategy.md     # Phase 1: Test architecture, patterns, utilities
├── contracts/           # Phase 1 output
│   ├── page-objects.md  # Page Object Model interfaces
│   └── test-data.md     # Test data factory schemas
└── tasks.md             # Phase 2: Detailed task breakdown
```

### Test Code (repository)

**Selected Structure**: E2E test suite (Playwright)

```text
frontend/
├── playwright.config.ts          # Test runner configuration
├── e2e/                          # E2E test files
│   ├── article-import.spec.ts    # [NEW] Article import tests
│   ├── article-list.spec.ts      # [NEW] Article list tests
│   ├── article-review.spec.ts    # [NEW] Article review tests
│   ├── publish-tasks.spec.ts     # [NEW] Publish task monitoring
│   ├── provider-comparison.spec.ts # [NEW] Provider comparison
│   ├── worklist.spec.ts          # [NEW] Worklist management
│   ├── schedule.spec.ts          # [NEW] Schedule management
│   ├── tags.spec.ts              # [NEW] Tag management
│   ├── proofreading-rules.spec.ts # [NEW] Rule management
│   ├── proofreading-stats.spec.ts # [NEW] Statistics dashboard
│   ├── workflows/                # [NEW] End-to-end workflows
│   │   ├── complete-publish.spec.ts
│   │   └── batch-import.spec.ts
│   ├── edge-cases/               # [NEW] Edge case scenarios
│   │   ├── network-errors.spec.ts
│   │   ├── file-upload.spec.ts
│   │   ├── security.spec.ts
│   │   └── performance.spec.ts
│   └── cross-browser/            # [NEW] Browser-specific tests
│       ├── firefox.spec.ts
│       └── safari.spec.ts
├── tests/
│   ├── page-objects/             # [NEW] Page Object Model
│   │   ├── ArticleImportPage.ts
│   │   ├── ArticleListPage.ts
│   │   ├── ArticleReviewPage.ts
│   │   └── ...
│   ├── fixtures/                 # [NEW] Test fixtures
│   │   ├── test-data.ts
│   │   ├── mock-api.ts
│   │   └── browser-contexts.ts
│   └── utils/                    # [NEW] Test utilities
│       ├── test-data-factory.ts
│       ├── performance-helpers.ts
│       └── screenshot-comparison.ts
└── .github/
    └── workflows/
        └── e2e-tests.yml          # [ENHANCED] CI pipeline
```

**File Organization Rationale**:
- **Separate directories for test types**: `e2e/` for E2E, `edge-cases/` for edge scenarios, `workflows/` for complete journeys
- **Page Objects centralized**: `tests/page-objects/` for reusable abstractions
- **Shared fixtures**: `tests/fixtures/` for common setup (data, mocks, contexts)
- **Utilities isolated**: `tests/utils/` for helper functions (data factories, performance)

## Architecture & Design

### Test Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline (GitHub Actions)            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Chromium   │  │  Firefox    │  │   Safari    │          │
│  │   Tests     │  │   Tests     │  │   Tests     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│         │                 │                 │                 │
│         └─────────────────┴─────────────────┘                │
│                          │                                    │
│                 ┌────────▼────────┐                          │
│                 │  Test Reporter  │                          │
│                 │  (HTML/JSON)    │                          │
│                 └─────────────────┘                          │
└──────────────────────────────────────────────────────────────┘
                          │
                          │ Results
                          ▼
┌──────────────────────────────────────────────────────────────┐
│              Production Monitoring Dashboard                  │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │   Hourly Smoke Tests │  │  Performance Budgets  │         │
│  │   (Production)       │  │  (LCP/FID/CLS)        │         │
│  └──────────────────────┘  └──────────────────────┘         │
│                                                               │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │   Flake Detection    │  │   Coverage Tracking   │         │
│  │   (<5% threshold)    │  │   (85% target)        │         │
│  └──────────────────────┘  └──────────────────────┘         │
└──────────────────────────────────────────────────────────────┘
```

### Test Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     E2E Test Layers                          │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Workflow Tests (End-to-End)                       │
│  ┌───────────────────────────────────────────────┐          │
│  │ Import → SEO → Proofreading → Publish        │          │
│  │ Batch operations, multi-step validation      │          │
│  └───────────────────────────────────────────────┘          │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Feature Tests (Page-Level)                        │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐    │
│  │ Article Import│ │ Article List  │ │ Publish Tasks │    │
│  │ - CSV upload  │ │ - Pagination  │ │ - Monitoring  │    │
│  │ - Validation  │ │ - Filtering   │ │ - Retry       │    │
│  └───────────────┘ └───────────────┘ └───────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Component Tests (UI Elements)                     │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐    │
│  │ File Upload   │ │ Data Table    │ │ Status Badge  │    │
│  │ Form Input    │ │ Modal Dialog  │ │ Toast Alert   │    │
│  └───────────────┘ └───────────────┘ └───────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: API Tests (Backend Integration)                   │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐    │
│  │ GET /articles │ │ POST /import  │ │ PUT /settings │    │
│  │ Pagination    │ │ File handling │ │ Validation    │    │
│  └───────────────┘ └───────────────┘ └───────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Page Object Model Pattern

**Rationale**: Separate test logic from DOM selectors for maintainability

```typescript
// page-objects/ArticleImportPage.ts
export class ArticleImportPage {
  constructor(private page: Page) {}

  // Locators (centralized selectors)
  private get csvUploadInput() {
    return this.page.locator('input[type="file"]');
  }

  private get submitButton() {
    return this.page.locator('button[type="submit"]');
  }

  private get progressBar() {
    return this.page.locator('[role="progressbar"]');
  }

  // Actions (reusable operations)
  async uploadCSV(filePath: string) {
    await this.csvUploadInput.setInputFiles(filePath);
  }

  async submitForm() {
    await this.submitButton.click();
  }

  async waitForCompletion() {
    await this.progressBar.waitFor({ state: 'hidden' });
  }

  // Assertions (readable expectations)
  async assertUploadSuccess() {
    const toast = this.page.locator('.toast-success');
    await expect(toast).toContainText('Import completed');
  }
}

// Usage in test
test('import CSV with 100 articles', async ({ page }) => {
  const importPage = new ArticleImportPage(page);

  await importPage.uploadCSV('./fixtures/100-articles.csv');
  await importPage.submitForm();
  await importPage.waitForCompletion();
  await importPage.assertUploadSuccess();
});
```

### Test Data Factory Pattern

**Rationale**: Generate realistic test data with minimal code

```typescript
// utils/test-data-factory.ts
export class ArticleFactory {
  static createArticle(overrides?: Partial<Article>): Article {
    return {
      id: faker.datatype.uuid(),
      title: faker.lorem.sentence(),
      content: faker.lorem.paragraphs(5),
      status: 'draft',
      created_at: faker.date.past().toISOString(),
      ...overrides
    };
  }

  static createBatch(count: number): Article[] {
    return Array.from({ length: count }, () => this.createArticle());
  }

  static createCSV(articles: Article[]): string {
    // Convert articles to CSV format
    return Papa.unparse(articles);
  }
}

// Usage in test
test('import large CSV', async ({ page }) => {
  const articles = ArticleFactory.createBatch(1000);
  const csvContent = ArticleFactory.createCSV(articles);

  await fs.writeFile('./fixtures/temp.csv', csvContent);

  const importPage = new ArticleImportPage(page);
  await importPage.uploadCSV('./fixtures/temp.csv');
  // ...
});
```

### Cross-Browser Testing Strategy

**Configuration**:
```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 13'] },
    },
  ],

  // Run critical tests on all browsers
  grep: /@critical/,

  // Run full suite on Chromium only for non-critical tests
  // (saves CI time while maintaining cross-browser coverage)
});
```

**Conditional Logic for Browser Quirks**:
```typescript
test('date picker works cross-browser', async ({ page, browserName }) => {
  const datePicker = page.locator('input[type="date"]');

  if (browserName === 'webkit') {
    // Safari uses native date picker, different interaction
    await datePicker.fill('2024-11-04');
  } else {
    // Chrome/Firefox use custom widget
    await datePicker.click();
    await page.locator('.calendar-day[data-date="2024-11-04"]').click();
  }

  // Assertion works the same across browsers
  await expect(datePicker).toHaveValue('2024-11-04');
});
```

### Performance Testing Integration

**Lighthouse CI Integration**:
```typescript
// e2e/edge-cases/performance.spec.ts
import { playAudit } from 'playwright-lighthouse';

test('homepage meets performance budgets', async ({ page, browserName }) => {
  test.skip(browserName !== 'chromium', 'Lighthouse only supports Chromium');

  await page.goto('/');

  const result = await playAudit({
    page,
    thresholds: {
      performance: 90,
      accessibility: 90,
      'best-practices': 90,
      seo: 90,
    },
    reports: {
      formats: { html: true, json: true },
      directory: './lighthouse-reports',
    },
  });

  // Custom Core Web Vitals checks
  const metrics = result.lhr.audits;
  expect(metrics['largest-contentful-paint'].numericValue).toBeLessThan(2500); // 2.5s
  expect(metrics['max-potential-fid'].numericValue).toBeLessThan(100); // 100ms
  expect(metrics['cumulative-layout-shift'].numericValue).toBeLessThan(0.1); // 0.1
});
```

### Flake Detection & Quarantine

**Automatic Flake Detection**:
```typescript
// .github/workflows/e2e-tests.yml
- name: Run E2E Tests
  run: npx playwright test --repeat-each=3 --retries=0

- name: Analyze Flakes
  run: |
    node scripts/detect-flakes.js

# scripts/detect-flakes.js
const results = JSON.parse(fs.readFileSync('./test-results.json'));

const flakes = results.tests.filter(test => {
  const runs = test.runs;
  const passCount = runs.filter(r => r.status === 'passed').length;
  const passRate = passCount / runs.length;

  return passRate > 0 && passRate < 0.95; // Passed sometimes but not reliably
});

if (flakes.length > 0) {
  // Quarantine flaky tests
  fs.writeFileSync('.playwright/quarantined-tests.json', JSON.stringify(flakes));

  // Send alert
  await sendSlackAlert(`🚨 ${flakes.length} flaky tests detected`);
}
```

## Phase Breakdown

### Phase 0: Research & Analysis (2 days)

**Objective**: Analyze current test coverage, identify gaps, and establish baseline metrics.

**Deliverables**:
- `research.md`: Coverage gap analysis with prioritized test scenarios
- Browser compatibility matrix (Chrome/Firefox/Safari support matrix)
- Performance baseline report (current LCP/FID/CLS values)
- Flaky test audit (identify existing unstable tests)

**Tasks**:
1. Run coverage analysis on existing 147 tests
2. Map untested modules (10 modules with 0% coverage)
3. Document edge cases per module (network, security, performance)
4. Establish performance baselines (Lighthouse on all pages)
5. Audit existing tests for flakiness (run 10x, track pass rate)

**Success Criteria**:
- [ ] Coverage report generated with module-level breakdown
- [ ] All 10 untested modules documented with test scenarios
- [ ] Performance baseline captured for 16 pages
- [ ] Flaky tests identified and tracked (<5% flake rate)

### Phase 1: Test Architecture & Design (3 days)

**Objective**: Design test architecture, create Page Object Model, and establish patterns.

**Deliverables**:
- `test-strategy.md`: Testing patterns, architecture decisions, conventions
- `contracts/page-objects.md`: Page Object interfaces for all 16 modules
- `contracts/test-data.md`: Test data factory schemas and fixtures
- Reusable test utilities (data factories, performance helpers)

**Tasks**:
1. Design Page Object Model hierarchy
2. Create test data factories for all models (Article, Task, Rule, etc.)
3. Implement cross-browser conditional logic patterns
4. Design performance testing integration (Lighthouse CI)
5. Establish flake detection automation

**Success Criteria**:
- [ ] Page Object Model designed for all 16 modules
- [ ] Test data factories implemented with faker.js
- [ ] Cross-browser test patterns documented
- [ ] Performance testing utilities created
- [ ] Flake detection pipeline configured

### Phase 2: Core Module Testing (8 days)

**Objective**: Implement E2E tests for all 10 untested modules plus enhance 6 existing modules.

**Deliverables**:
- E2E tests for 10 new modules (Article Import, List, Review, Tasks, Comparison, Worklist, Schedule, Tags, Rules, Stats)
- Enhanced tests for 6 existing modules (API, Generator, Navigation, Settings, Production, Basic)
- Edge case tests (network, security, performance)
- Cross-browser tests for critical paths

**Tasks** (per module):
1. Implement Page Object Model
2. Write happy path tests (80% scenarios)
3. Write edge case tests (network errors, validation, security)
4. Add cross-browser tests (@critical tag)
5. Integrate performance checks

**Module Breakdown** (8 days total):
- Days 1-2: Article Import + Article List
- Days 3-4: Article Review + Publish Tasks
- Days 5-6: Worklist + Schedule + Tags
- Days 7-8: Proofreading Rules + Stats + Provider Comparison

**Success Criteria**:
- [ ] All 10 modules have E2E tests (100% coverage)
- [ ] Edge cases covered (network, security, performance)
- [ ] Cross-browser tests pass on Chrome, Firefox, Safari
- [ ] Performance budgets enforced on all pages

### Phase 3: Workflow Tests & Production Monitoring (8 days)

**Objective**: Implement end-to-end workflow tests, production monitoring, and CI/CD integration.

**Deliverables**:
- 5 complete workflow tests (Import → Publish, Batch operations, etc.)
- Production smoke tests (hourly execution)
- CI/CD pipeline with multi-browser matrix
- Monitoring dashboard for test results
- Alert system for failures

**Tasks**:
1. Implement 5 critical workflows (Import → SEO → Publish, etc.)
2. Create production smoke test suite (read-only)
3. Configure CI/CD pipeline (GitHub Actions)
4. Set up monitoring dashboard (test results, performance trends)
5. Implement alerting (Slack, email)

**Workflow Tests**:
1. Complete publish flow: Import CSV → SEO → Proofread → Publish
2. Batch import: 1000 articles → validation → import
3. Concurrent publishing: 10 articles in parallel
4. Error recovery: Network failure → retry → success
5. Security validation: XSS/injection attempts → blocked

**Success Criteria**:
- [ ] 5 critical workflows tested end-to-end
- [ ] Production smoke tests running hourly
- [ ] CI/CD pipeline executing on all PRs
- [ ] Monitoring dashboard deployed
- [ ] Alert system functional (Slack notifications)

## Implementation Schedule

```
Week 1 (Days 1-5):
├─ Day 1-2: Phase 0 - Research & Analysis
│   ├─ Coverage gap analysis
│   ├─ Browser compatibility matrix
│   └─ Performance baseline
├─ Day 3-5: Phase 1 - Architecture & Design
│   ├─ Page Object Model design
│   ├─ Test data factories
│   └─ Utilities and patterns

Week 2 (Days 6-10):
├─ Day 6-7: Article Import + Article List tests
├─ Day 8-9: Article Review + Publish Tasks tests
└─ Day 10: Worklist + Schedule tests

Week 3 (Days 11-15):
├─ Day 11: Tags + Proofreading Rules tests
├─ Day 12-13: Stats + Provider Comparison + Edge cases
├─ Day 14-15: Workflow tests (Import → Publish, Batch)

Week 4 (Days 16-21):
├─ Day 16-17: Remaining workflows (Concurrent, Error recovery, Security)
├─ Day 18-19: Production monitoring + CI/CD integration
├─ Day 20: Testing, refinement, flake fixes
└─ Day 21: Documentation, handoff, deployment
```

**Total Duration**: 21 days (3 weeks)

**Milestones**:
- Day 5: Architecture approved ✅
- Day 10: 50% module coverage ✅
- Day 15: 85% module coverage ✅
- Day 21: Production monitoring live ✅

## Testing Strategy

### Test Prioritization Matrix

| Priority | Scope | Browsers | Coverage |
|----------|-------|----------|----------|
| P0 - Critical | Happy paths, data loss scenarios | Chrome, Firefox, Safari | 100% |
| P1 - High | Edge cases, error handling | Chrome, Firefox | 90% |
| P2 - Medium | Advanced features, corner cases | Chrome only | 70% |
| P3 - Low | Nice-to-haves, future enhancements | Chrome only | 50% |

### Test Execution Strategy

**Local Development**:
```bash
# Run all tests (Chromium only, fast)
npm run test:e2e

# Run specific module
npm run test:e2e -- article-import

# Run with UI (debugging)
npm run test:e2e -- --ui

# Run in headed mode (watch browser)
npm run test:e2e -- --headed
```

**CI/CD**:
```bash
# Full suite, all browsers, parallel
npm run test:e2e:ci

# Critical tests only (@critical tag)
npm run test:e2e:critical

# Production smoke tests (hourly cron)
npm run test:e2e:smoke
```

### Test Data Management

**Strategy**:
1. **Database Seeding**: Each test starts with clean DB snapshot
2. **Fixtures**: Static test data in `fixtures/` directory
3. **Factories**: Dynamic data generation using faker.js
4. **Cleanup**: Automatic cleanup after each test

**Example**:
```typescript
test.beforeEach(async ({ page }) => {
  // Restore database to clean state
  await db.restoreSnapshot('clean-state');

  // Seed test data
  const articles = ArticleFactory.createBatch(10);
  await db.seed('articles', articles);
});

test.afterEach(async ({ page }) => {
  // Cleanup test data
  await db.cleanup('test-*');
});
```

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Flaky tests degrade CI reliability** | High | Automatic flake detection, quarantine system, retry logic |
| **Production tests pollute data** | Critical | Read-only queries, isolated test accounts, transaction rollbacks |
| **Slow tests block deploys** | High | Parallel execution (4 workers), smart test selection, critical-only runs |
| **Cross-browser failures increase maintenance** | Medium | Page Object abstraction, conditional logic, browser-specific test skipping |
| **Test data setup bottleneck** | Medium | Database snapshots, test data factories, parallel seeding |

## Success Metrics

### Coverage Metrics
- **Functional Coverage**: 85% (14/16 modules) ✅ Target
- **Edge Case Coverage**: 70% (network, security, performance) ✅ Target
- **Critical Path Coverage**: 95% (all P0 workflows) ✅ Target

### Quality Metrics
- **Production Incidents**: Reduce by 80% (10/month → 2/month)
- **Regression Bugs**: < 1 per release (from current 5/release)
- **Bug Detection Time**: 95% caught in CI (before code review)

### Performance Metrics
- **Test Suite Speed**: < 15 minutes (full run)
- **CI Feedback Time**: < 20 minutes (commit to result)
- **Flake Rate**: < 5% (auto-quarantine above threshold)

### Developer Experience
- **Developer Confidence**: 90%+ confidence in deploy (survey)
- **False Positives**: < 2% (tests failing when app is correct)
- **Documentation Quality**: 100% tests have clear descriptions

## Acceptance Criteria (Feature Complete)

- [ ] **All 10 uncovered modules have E2E tests** (Article Import, List, Review, Tasks, Comparison, Worklist, Schedule, Tags, Proofreading Rules, Stats)
- [ ] **Edge cases covered** (network errors, file upload failures, XSS/injection, race conditions)
- [ ] **Cross-browser tests pass** on Chrome, Firefox, Safari with 100% pass rate
- [ ] **Performance budgets enforced** (LCP < 2.5s, FID < 100ms, CLS < 0.1)
- [ ] **Full E2E workflow tests** (Import → SEO → Proofreading → Publish)
- [ ] **CI pipeline runs tests** automatically on all PRs with multi-browser matrix
- [ ] **Test suite completes** in < 15 minutes (full run with 4 parallel workers)
- [ ] **Flake rate < 5%** with automatic quarantine system
- [ ] **Test documentation complete** (runbooks, troubleshooting guides)
- [ ] **Production smoke tests** run hourly with Slack alerts
- [ ] **Monitoring dashboard** deployed with test results, performance trends
- [ ] **85% functional coverage** achieved (14/16 modules)
- [ ] **70% edge case coverage** achieved
- [ ] **95% critical path coverage** achieved (all P0 workflows)

## Related Documents

- [spec.md](./spec.md) - Feature specification with user stories
- [tasks.md](./tasks.md) - Detailed task breakdown
- [research.md](./research.md) - Coverage gap analysis (Phase 0 output)
- [test-strategy.md](./test-strategy.md) - Testing patterns (Phase 1 output)
- [contracts/page-objects.md](./contracts/page-objects.md) - Page Object interfaces
- [contracts/test-data.md](./contracts/test-data.md) - Test data schemas
- `/PLAYWRIGHT_TEST_COVERAGE_ANALYSIS.md` - Current coverage analysis
