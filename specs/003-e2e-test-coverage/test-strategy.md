# Test Strategy: E2E Test Coverage & Production Regression Testing

**Feature**: `003-e2e-test-coverage`
**Created**: 2025-11-04
**Related Documents**: [spec.md](./spec.md), [plan.md](./plan.md)

## Overview

This document defines the comprehensive testing strategy for achieving 85% E2E test coverage across all application modules, with focus on cross-browser compatibility, performance validation, and production stability.

---

## Testing Principles

### 1. Test Pyramid Alignment

```
                    ▲
                   ╱ ╲
                  ╱   ╲         5% - E2E Workflow Tests
                 ╱     ╲             (This Feature)
                ╱───────╲
               ╱         ╲      25% - E2E Feature Tests
              ╱           ╲          (This Feature)
             ╱─────────────╲
            ╱               ╲   70% - Unit + Integration
           ╱                 ╲       (Separate Effort)
          ╱───────────────────╲
```

**This Feature Scope**: Top 30% of pyramid (E2E tests only)

### 2. Test Independence

- **Isolated Execution**: Each test runs in independent browser context with clean database
- **No Test Ordering**: Tests can run in any order without failures
- **Deterministic Results**: Same test produces same result every run
- **Fast Cleanup**: Database/browser cleanup completes in <1 second

### 3. Readable Test Code

```typescript
// ❌ Bad: Unclear what's being tested
test('test 1', async ({ page }) => {
  await page.click('#btn1');
  expect(await page.locator('.msg').textContent()).toBe('ok');
});

// ✅ Good: Clear intent and expectations
test('article import shows success toast after CSV upload', async ({ page }) => {
  const importPage = new ArticleImportPage(page);

  await importPage.uploadCSV('./fixtures/10-articles.csv');
  await importPage.submit();

  await expect(importPage.successToast).toHaveText('10 articles imported');
});
```

---

## Test Types & Coverage Strategy

### 1. Happy Path Tests (60% of suite)

**Purpose**: Verify core functionality works as designed

**Coverage**:
- All 16 modules have happy path tests
- Every user story acceptance criteria covered
- Basic CRUD operations (Create, Read, Update, Delete)

**Example**:
```typescript
test('import valid CSV file with 100 articles', async ({ page }) => {
  // Covers: Article Import - Happy Path
  const importPage = new ArticleImportPage(page);

  await importPage.goto();
  await importPage.uploadCSV('./fixtures/100-articles.csv');
  await importPage.clickImport();

  // Verify success
  await expect(importPage.progressBar).toBeVisible();
  await expect(importPage.progressBar).toHaveAttribute('aria-valuenow', '100');
  await expect(importPage.successToast).toHaveText('100 articles imported successfully');

  // Verify data integrity
  const articleList = new ArticleListPage(page);
  await articleList.goto();
  const count = await articleList.getArticleCount();
  expect(count).toBe(100);
});
```

### 2. Edge Case Tests (30% of suite)

**Purpose**: Verify error handling, validation, and boundary conditions

**Coverage**:
- Network failures (timeout, disconnection, slow network)
- Invalid input (XSS, SQL injection, malformed data)
- Large data sets (10,000+ records)
- Concurrent operations (race conditions)
- Browser-specific quirks

**Examples**:

#### Network Timeout
```typescript
test('handles API timeout gracefully', async ({ page }) => {
  // Simulate slow network (10s timeout)
  await page.route('**/v1/articles', route => {
    setTimeout(() => route.fulfill({ status: 408 }), 10000);
  });

  const articleList = new ArticleListPage(page);
  await articleList.goto();

  // Verify error handling
  await expect(articleList.errorToast).toHaveText('Request timed out. Please try again.');
  await expect(articleList.retryButton).toBeVisible();
});
```

#### XSS Attack Prevention
```typescript
test('blocks XSS injection in article title', async ({ page }) => {
  const importPage = new ArticleImportPage(page);

  // Attempt XSS injection
  const maliciousCSV = `title,content\n"<script>alert('xss')</script>",Test content`;
  await importPage.uploadCSVContent(maliciousCSV);
  await importPage.clickImport();

  // Verify sanitization
  const articleList = new ArticleListPage(page);
  await articleList.goto();

  const firstArticle = await articleList.getArticleTitle(0);
  expect(firstArticle).not.toContain('<script>');
  expect(firstArticle).toBe(''); // Script tag completely removed
});
```

### 3. Workflow Tests (10% of suite)

**Purpose**: Verify complete user journeys across multiple modules

**Coverage**:
- 5 critical end-to-end workflows
- Multi-step operations with state transitions
- Integration between modules

**Example**:
```typescript
test('complete publish workflow: Import → SEO → Proofreading → Publish', async ({ page }) => {
  // Step 1: Import article
  const importPage = new ArticleImportPage(page);
  await importPage.goto();
  await importPage.uploadCSV('./fixtures/1-article.csv');
  await importPage.clickImport();
  await expect(importPage.successToast).toBeVisible();

  // Step 2: SEO analysis
  const articleList = new ArticleListPage(page);
  await articleList.goto();
  await articleList.selectArticle(0);
  await articleList.clickAnalyzeSEO();

  const seoPage = new SEOAnalyzerPage(page);
  await expect(seoPage.analysisComplete).toBeVisible();
  await expect(seoPage.score).toBeGreaterThan(70);

  // Step 3: Proofreading
  await seoPage.clickProofread();
  const proofreadPage = new ProofreadingPage(page);
  await expect(proofreadPage.issuesFound).toHaveText(/\d+ issues found/);
  await proofreadPage.acceptAllSuggestions();
  await proofreadPage.clickSave();

  // Step 4: Publish to WordPress
  await proofreadPage.clickPublish();
  const publishPage = new PublishTasksPage(page);
  await expect(publishPage.taskStatus).toHaveText('Publishing...');

  // Wait for completion (max 60s)
  await expect(publishPage.taskStatus).toHaveText('Published', { timeout: 60000 });

  // Step 5: Verify live URL
  const liveURL = await publishPage.getLiveURL();
  expect(liveURL).toMatch(/https:\/\/.*\.com\/.*/);

  // Verify article is accessible
  await page.goto(liveURL);
  await expect(page.locator('h1')).toContainText('Article Title');
});
```

---

## Test Execution Strategies

### 1. Parallel Execution

**Configuration**:
```typescript
// playwright.config.ts
export default defineConfig({
  workers: process.env.CI ? 4 : undefined, // 4 workers on CI, auto on local
  fullyParallel: true, // All tests can run in parallel

  // Limit retries to avoid masking flakes
  retries: process.env.CI ? 1 : 0,

  // Fail fast to get quick feedback
  maxFailures: process.env.CI ? 10 : undefined,
});
```

**Parallelization Strategy**:
- Each test file runs in parallel (20 files = 20 parallel executions)
- Tests within file run sequentially (maintain readability)
- Database isolation via unique schema per worker

### 2. Selective Test Execution

**Tags for Filtering**:
```typescript
// Critical tests (run on every PR)
test.describe('@critical Article Import', () => {
  test('uploads CSV successfully', async ({ page }) => {
    // ...
  });
});

// Slow tests (run nightly only)
test.describe('@slow Large Import', () => {
  test('handles 10,000 article CSV', async ({ page }) => {
    test.slow(); // 3x timeout
    // ...
  });
});

// Browser-specific tests
test.describe('@firefox Date Picker', () => {
  test('native date picker works', async ({ page, browserName }) => {
    test.skip(browserName !== 'firefox');
    // ...
  });
});
```

**CI Commands**:
```bash
# PR builds: Critical tests only (fast feedback)
npm run test:e2e -- --grep @critical

# Nightly builds: Full suite including slow tests
npm run test:e2e -- --grep-invert @skip

# Browser-specific runs
npm run test:e2e -- --project firefox --grep @firefox
```

### 3. Test Sharding

**For Large Suites**:
```bash
# Split tests across 4 machines in CI
npx playwright test --shard=1/4  # Machine 1
npx playwright test --shard=2/4  # Machine 2
npx playwright test --shard=3/4  # Machine 3
npx playwright test --shard=4/4  # Machine 4
```

---

## Cross-Browser Testing Matrix

### Browser Support Matrix

| Feature | Chrome 120+ | Firefox 120+ | Safari 17+ | Edge 120+ |
|---------|-------------|--------------|------------|-----------|
| **Happy Path Tests** | ✅ All | ✅ All | ✅ All | ✅ Same as Chrome |
| **Edge Cases** | ✅ All | ✅ Most | ⚠️ Critical only | ✅ Same as Chrome |
| **Workflows** | ✅ All | ✅ All | ✅ Critical only | ✅ Same as Chrome |
| **Performance Tests** | ✅ Lighthouse | ❌ N/A | ❌ N/A | ❌ N/A |

**Rationale**:
- Chrome: Primary browser (60% of users), full coverage
- Firefox: Secondary browser (25% of users), full coverage
- Safari: Mobile primary (15% of users), critical tests only
- Edge: Chromium-based, same behavior as Chrome

### Browser-Specific Test Patterns

#### Conditional Logic
```typescript
test('date picker interaction', async ({ page, browserName }) => {
  const dateInput = page.locator('input[type="date"]');

  if (browserName === 'webkit') {
    // Safari uses native date picker
    await dateInput.fill('2024-11-04');
  } else {
    // Chrome/Firefox use custom widget
    await dateInput.click();
    await page.locator('.calendar-day[data-date="2024-11-04"]').click();
  }

  // Assertion works the same
  await expect(dateInput).toHaveValue('2024-11-04');
});
```

#### Browser-Specific Skipping
```typescript
test('drag and drop file upload', async ({ page, browserName }) => {
  // Safari doesn't support drag-and-drop file API
  test.skip(browserName === 'webkit', 'Safari drag-and-drop not supported');

  // Test implementation...
});
```

---

## Performance Testing Strategy

### Core Web Vitals Budgets

| Metric | Budget | Current | Target |
|--------|--------|---------|--------|
| **LCP** (Largest Contentful Paint) | < 2.5s | 3.2s | < 2.0s |
| **FID** (First Input Delay) | < 100ms | 120ms | < 80ms |
| **CLS** (Cumulative Layout Shift) | < 0.1 | 0.15 | < 0.05 |
| **TTI** (Time to Interactive) | < 3.8s | 4.5s | < 3.5s |
| **TBT** (Total Blocking Time) | < 300ms | 450ms | < 250ms |

### Performance Test Implementation

```typescript
import { playAudit } from 'playwright-lighthouse';

test('homepage meets performance budgets', async ({ page, browserName }) => {
  // Lighthouse only supports Chromium
  test.skip(browserName !== 'chromium');

  await page.goto('/');

  const report = await playAudit({
    page,
    port: 9222,
    thresholds: {
      performance: 90,
      accessibility: 90,
      'best-practices': 90,
      seo: 90,
    },
  });

  // Core Web Vitals assertions
  const metrics = report.lhr.audits;

  // LCP Budget: 2.5 seconds
  const lcp = metrics['largest-contentful-paint'].numericValue;
  expect(lcp).toBeLessThan(2500);

  // FID Budget: 100 milliseconds
  const fid = metrics['max-potential-fid'].numericValue;
  expect(fid).toBeLessThan(100);

  // CLS Budget: 0.1
  const cls = metrics['cumulative-layout-shift'].numericValue;
  expect(cls).toBeLessThan(0.1);

  // TTI Budget: 3.8 seconds
  const tti = metrics['interactive'].numericValue;
  expect(tti).toBeLessThan(3800);

  // TBT Budget: 300 milliseconds
  const tbt = metrics['total-blocking-time'].numericValue;
  expect(tbt).toBeLessThan(300);

  // Bundle Size Budget: 500KB gzipped
  const transferSize = metrics['total-byte-weight'].numericValue;
  expect(transferSize).toBeLessThan(500 * 1024);
});
```

### Performance Regression Detection

```typescript
// Store baseline metrics
const BASELINE_METRICS = {
  lcp: 2000,
  fid: 80,
  cls: 0.05,
};

test('detects performance regression', async ({ page }) => {
  const metrics = await captureMetrics(page);

  // Fail if any metric regresses by >20%
  expect(metrics.lcp).toBeLessThan(BASELINE_METRICS.lcp * 1.2);
  expect(metrics.fid).toBeLessThan(BASELINE_METRICS.fid * 1.2);
  expect(metrics.cls).toBeLessThan(BASELINE_METRICS.cls * 1.2);
});
```

---

## Flake Detection & Prevention

### What is a Flaky Test?

A test that sometimes passes and sometimes fails without code changes.

**Common Causes**:
- Race conditions (async timing)
- Non-deterministic data (random IDs, timestamps)
- Network instability
- Resource contention (CPU, memory)
- Browser inconsistencies

### Detection Strategy

#### Automatic Flake Detection
```typescript
// Run tests 10 times to detect flakes
// CI: .github/workflows/flake-detection.yml
test('flake detection run', async () => {
  const results = [];

  for (let i = 0; i < 10; i++) {
    const result = await runTest('article-import.spec.ts');
    results.push(result.status);
  }

  const passCount = results.filter(s => s === 'passed').length;
  const passRate = passCount / 10;

  if (passRate > 0 && passRate < 0.95) {
    // Flaky test detected!
    quarantineTest('article-import.spec.ts');
    notifyTeam(`Flaky test: ${passRate * 100}% pass rate`);
  }
});
```

### Prevention Strategies

#### 1. Explicit Waits (not implicit)
```typescript
// ❌ Bad: Implicit wait (flaky)
test('article loads', async ({ page }) => {
  await page.goto('/articles/1');
  await page.waitForTimeout(1000); // Arbitrary wait
  expect(await page.locator('h1').textContent()).toBe('Article Title');
});

// ✅ Good: Explicit wait for condition
test('article loads', async ({ page }) => {
  await page.goto('/articles/1');
  await page.waitForSelector('h1', { state: 'visible' });
  await expect(page.locator('h1')).toHaveText('Article Title');
});
```

#### 2. Deterministic Test Data
```typescript
// ❌ Bad: Non-deterministic data (flaky)
test('sorts articles by date', async ({ page }) => {
  const articles = ArticleFactory.createBatch(10); // Random dates
  await db.seed('articles', articles);

  const list = new ArticleListPage(page);
  await list.goto();
  await list.sortByDate();

  // Flaky: Random dates may already be sorted
  expect(await list.getArticleDate(0)).toBeGreaterThan(await list.getArticleDate(1));
});

// ✅ Good: Deterministic data
test('sorts articles by date', async ({ page }) => {
  const articles = [
    ArticleFactory.create({ created_at: '2024-01-01' }),
    ArticleFactory.create({ created_at: '2024-06-01' }),
    ArticleFactory.create({ created_at: '2024-12-01' }),
  ];
  await db.seed('articles', articles);

  const list = new ArticleListPage(page);
  await list.goto();
  await list.sortByDate('desc');

  // Reliable: Known order
  await expect(list.getArticleDate(0)).toBe('2024-12-01');
  await expect(list.getArticleDate(1)).toBe('2024-06-01');
  await expect(list.getArticleDate(2)).toBe('2024-01-01');
});
```

#### 3. Network Stability
```typescript
// ✅ Good: Wait for network idle before assertions
test('article list loads completely', async ({ page }) => {
  await page.goto('/articles');
  await page.waitForLoadState('networkidle'); // Wait for all requests

  const count = await page.locator('tr').count();
  expect(count).toBeGreaterThan(0);
});
```

### Quarantine System

```typescript
// .playwright/quarantined-tests.json
{
  "quarantined": [
    {
      "test": "article-import.spec.ts > import large CSV",
      "reason": "Flaky: 60% pass rate",
      "quarantinedAt": "2024-11-04",
      "issue": "https://github.com/org/repo/issues/123"
    }
  ]
}

// Skip quarantined tests in CI
test.beforeEach(async ({}, testInfo) => {
  const quarantined = JSON.parse(fs.readFileSync('.playwright/quarantined-tests.json'));

  if (quarantined.quarantined.some(t => testInfo.titlePath.includes(t.test))) {
    test.skip(true, 'Test quarantined due to flakiness');
  }
});
```

---

## Test Data Management

### Strategies

#### 1. Database Snapshots
```typescript
// Create snapshot before test suite
test.beforeAll(async () => {
  await db.createSnapshot('clean-state');
});

// Restore snapshot before each test
test.beforeEach(async () => {
  await db.restoreSnapshot('clean-state');
});
```

#### 2. Test Data Factories
```typescript
// tests/utils/test-data-factory.ts
import { faker } from '@faker-js/faker';

export class ArticleFactory {
  static create(overrides?: Partial<Article>): Article {
    return {
      id: faker.datatype.uuid(),
      title: faker.lorem.sentence(),
      content: faker.lorem.paragraphs(5),
      status: 'draft',
      created_at: faker.date.past().toISOString(),
      author: faker.person.fullName(),
      ...overrides,
    };
  }

  static createBatch(count: number, overrides?: Partial<Article>): Article[] {
    return Array.from({ length: count }, () => this.create(overrides));
  }

  static createCSV(articles: Article[]): string {
    return Papa.unparse(articles, {
      columns: ['title', 'content', 'author'],
    });
  }
}

// Usage
const articles = ArticleFactory.createBatch(100, { status: 'published' });
```

#### 3. Fixture Files
```text
frontend/tests/fixtures/
├── articles/
│   ├── 10-articles.csv
│   ├── 100-articles.csv
│   ├── 1000-articles.csv
│   └── malicious.csv (XSS test data)
├── users/
│   └── test-users.json
└── images/
    ├── test-image-1mb.jpg
    └── test-image-10mb.jpg
```

---

## Production Testing Strategy

### Read-Only Smoke Tests

**Goals**:
- Verify production is healthy
- Catch deployment issues immediately
- Monitor performance in real environment

**Constraints**:
- Read-only operations (no mutations)
- Isolated test accounts
- Low overhead (< 1% of traffic)

**Implementation**:
```typescript
// e2e/production-smoke.spec.ts
const IS_PRODUCTION = process.env.ENV === 'production';

test.describe('Production Smoke Tests', () => {
  test.beforeEach(async ({}, testInfo) => {
    // Only run on production
    test.skip(!IS_PRODUCTION, 'Production-only test');
  });

  test('homepage loads successfully', async ({ page }) => {
    await page.goto('https://cms-automation.com');

    // Verify critical elements
    await expect(page.locator('nav')).toBeVisible();
    await expect(page.locator('h1')).toBeVisible();

    // Performance check
    const metrics = await page.evaluate(() => JSON.stringify(performance.timing));
    const timing = JSON.parse(metrics);
    const loadTime = timing.loadEventEnd - timing.navigationStart;
    expect(loadTime).toBeLessThan(3000); // 3s budget
  });

  test('API health check', async ({ request }) => {
    const response = await request.get('https://api.cms-automation.com/health');

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data.status).toBe('healthy');
    expect(data.database).toBe('connected');
  });
});
```

### Continuous Monitoring

**Hourly Cron Job**:
```yaml
# .github/workflows/production-smoke.yml
name: Production Smoke Tests

on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:  # Manual trigger

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run smoke tests
        run: npx playwright test e2e/production-smoke.spec.ts
        env:
          ENV: production

      - name: Send alert on failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "🚨 Production smoke tests failed!",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "Production health check detected issues. <https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }}|View Details>"
                  }
                }
              ]
            }
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on:
  pull_request:
  push:
    branches: [main, develop]

jobs:
  test:
    timeout-minutes: 20
    runs-on: ubuntu-latest

    strategy:
      fail-fast: false
      matrix:
        browser: [chromium, firefox, webkit]
        shard: [1, 2, 3, 4]

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps ${{ matrix.browser }}

      - name: Run E2E tests
        run: npx playwright test --project ${{ matrix.browser }} --shard ${{ matrix.shard }}/4
        env:
          TEST_ENV: staging

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report-${{ matrix.browser }}-${{ matrix.shard }}
          path: playwright-report/

      - name: Upload performance reports
        if: matrix.browser == 'chromium'
        uses: actions/upload-artifact@v3
        with:
          name: lighthouse-reports
          path: lighthouse-reports/
```

### Test Result Reporting

```typescript
// playwright.config.ts
export default defineConfig({
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results.json' }],
    ['junit', { outputFile: 'junit.xml' }],
    ['github'],  // GitHub Actions annotations
  ],
});
```

---

## Accessibility Testing Integration

### Axe Integration

```typescript
import AxeBuilder from '@axe-core/playwright';

test('homepage has no accessibility violations', async ({ page }) => {
  await page.goto('/');

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});

test('article import form is accessible', async ({ page }) => {
  const importPage = new ArticleImportPage(page);
  await importPage.goto();

  const results = await new AxeBuilder({ page })
    .include('.import-form')
    .analyze();

  // Check specific violations
  const criticalViolations = results.violations.filter(
    v => v.impact === 'critical' || v.impact === 'serious'
  );

  expect(criticalViolations).toHaveLength(0);
});
```

---

## Summary

This test strategy provides:
- **Comprehensive Coverage**: 85% functional, 70% edge cases
- **Cross-Browser Support**: Chrome, Firefox, Safari
- **Performance Validation**: Core Web Vitals budgets enforced
- **Production Monitoring**: Hourly smoke tests with alerting
- **Flake Prevention**: Automatic detection and quarantine
- **CI/CD Integration**: Parallel execution with matrix builds

**Next Steps**: Implement tasks defined in [tasks.md](./tasks.md)
