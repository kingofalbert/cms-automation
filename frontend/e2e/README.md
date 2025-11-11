# E2E Testing Guide for Phase 8

## Overview

This directory contains comprehensive end-to-end tests for the Phase 8 Article Review workflow. The tests validate the complete user journey from opening the review modal to navigating through all review steps.

## Test Files

### `phase8-article-review-workflow.spec.ts`
Comprehensive E2E tests covering:
- **Modal behavior**: Opening, closing, keyboard shortcuts
- **Parsing Review step**: Title editing, AI optimization, SEO validation
- **Proofreading Review step**: Comparison cards, diff views
- **Progress Stepper**: Navigation between steps, completion tracking
- **Keyboard shortcuts**: Ctrl+S (save), Escape (close)
- **Complete workflow**: End-to-end user journey
- **Error handling**: Missing data, validation
- **Performance**: Modal open time, navigation speed

## Prerequisites

### 1. Local Development Environment Required

The E2E tests **cannot run against the production GCS deployment** because:
- Production is a static site without backend API
- Tests require a running backend with test data
- Tests need authenticated API access

### 2. Required Setup

Before running E2E tests, you need:

1. **Backend server running** with test database
2. **Frontend dev server** running on `localhost:3000`
3. **Test data** populated in the database (at least one worklist item)
4. **Environment variables** configured:
   ```bash
   export TEST_LOCAL=1
   ```

### 3. Full Setup Commands

```bash
# Terminal 1: Start backend
cd backend
source .env
python -m uvicorn main:app --reload

# Terminal 2: Start frontend dev server
cd frontend
npm run dev

# Terminal 3: Run E2E tests
cd frontend
TEST_LOCAL=1 npx playwright test e2e/phase8-article-review-workflow.spec.ts
```

## Running Tests

### Run all Phase 8 E2E tests
```bash
TEST_LOCAL=1 npx playwright test e2e/phase8-article-review-workflow.spec.ts
```

### Run specific test suite
```bash
TEST_LOCAL=1 npx playwright test e2e/phase8-article-review-workflow.spec.ts -g "Article Review Modal"
```

### Run in headed mode (watch browser)
```bash
TEST_LOCAL=1 npx playwright test e2e/phase8-article-review-workflow.spec.ts --headed
```

### Debug mode
```bash
TEST_LOCAL=1 npx playwright test e2e/phase8-article-review-workflow.spec.ts --debug
```

## Test Data Requirements

The tests expect:
- At least **1 worklist item** in `parsing_review` or later status
- Item should have:
  - `title` field populated
  - `content` field populated
  - Optional: `proofreading_issues` array for proofreading tests

### Creating Test Data

Use the backend API or database seeding:

```python
# Example: Create test worklist item
from backend.services.worklist import create_worklist_item

await create_worklist_item({
    "url": "https://example.com/test-article",
    "title": "Test Article for E2E",
    "content": "Test content here...",
    "status": "parsing_review"
})
```

## Test Structure

### Helper Functions

- `openArticleReviewModal(page)`: Opens the review modal from worklist
- `navigateToStep(page, stepName)`: Navigates to specific review step

### Test Organization

Tests are organized into describe blocks:
1. **Phase 8: Article Review Modal** - Modal behavior
2. **Phase 8: Parsing Review Step** - First review step
3. **Phase 8: Progress Stepper Navigation** - Step navigation
4. **Phase 8: Keyboard Shortcuts** - Keyboard interactions
5. **Phase 8: Proofreading Review Step** - Second review step
6. **Phase 8: Complete Workflow** - End-to-end scenarios
7. **Phase 8: Error Handling** - Error cases
8. **Phase 8: Performance** - Performance benchmarks

## Debugging Failed Tests

### View test results
```bash
npx playwright show-report
```

### Check screenshots
Failed tests automatically capture screenshots:
```
test-results/[test-name]/test-failed-1.png
```

### Watch videos
Failed tests record videos:
```
test-results/[test-name]/video.webm
```

### View traces
```bash
npx playwright show-trace test-results/[test-name]/trace.zip
```

## Known Limitations

1. **Production deployment**: Cannot test against GCS static hosting
2. **Authentication**: Tests assume unauthenticated access (development mode)
3. **Bilingual support**: Tests check for both Chinese and English text
4. **Performance tests**: May vary based on system performance

## CI/CD Integration

For CI/CD pipelines, ensure:

1. Backend runs in test mode with seeded data
2. Frontend builds and serves on expected port
3. Set `TEST_LOCAL=1` environment variable
4. Use `--workers=1` for sequential test execution
5. Increase timeouts for slower CI environments

Example GitHub Actions:
```yaml
- name: Run E2E Tests
  env:
    TEST_LOCAL: 1
  run: |
    npm run test:e2e -- --workers=1
```

## Troubleshooting

### "Timeout waiting for table tbody tr"
- **Cause**: No worklist items in database
- **Fix**: Seed test data before running tests

### "Access denied" error in browser
- **Cause**: Testing against production GCS URL
- **Fix**: Set `TEST_LOCAL=1` and start local dev server

### Modal doesn't open
- **Cause**: Frontend not fully loaded or no data
- **Fix**: Check network tab, ensure API returns data

### Tests pass locally but fail in CI
- **Cause**: Timing issues or missing test data
- **Fix**: Increase timeouts, verify data seeding in CI

## Contributing

When adding new E2E tests:
1. Use existing helper functions
2. Add bilingual text matching (Chinese/English)
3. Include appropriate timeouts and waits
4. Add descriptive test names
5. Group related tests in describe blocks
6. Add assertions for both success and error cases

## Resources

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Phase 8 Implementation Plan](/specs/001-cms-automation/plan.md)
- [UI Implementation Tasks](/specs/001-cms-automation/UI_IMPLEMENTATION_TASKS.md)
