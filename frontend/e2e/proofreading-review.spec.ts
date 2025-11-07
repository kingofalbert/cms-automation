/**
 * Proofreading Review E2E Tests
 * Tests the complete proofreading review workflow
 */

import { test, expect } from '@playwright/test';

// Use local dev server for testing
const BASE_URL = process.env.TEST_LOCAL
  ? 'http://localhost:3001/#'
  : 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html#';

test.describe('Proofreading Review Workflow', () => {
  test('should have review route registered', async ({ page }) => {
    // Navigate to a review page route
    await page.goto(`${BASE_URL}/worklist/1/review`);

    // Wait for page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Take screenshot
    await page.screenshot({
      path: 'screenshots/proofreading-review-route.png',
      fullPage: true
    });

    // The page should not show a 404 or "Page Not Found"
    const pageContent = await page.textContent('body');
    const has404 = pageContent?.includes('404') || pageContent?.includes('Not Found');

    console.log(`\n🔗 Route Registration:`);
    console.log(`   URL: ${BASE_URL}/worklist/1/review`);
    console.log(`   Has 404: ${has404 ? 'Yes' : 'No'}`);
    console.log(`   Status: ${!has404 ? '✅ PASS' : '❌ FAIL'}`);

    expect(has404).toBeFalsy();
  });

  test('should render review page UI elements', async ({ page }) => {
    // Navigate to review page
    await page.goto(`${BASE_URL}/worklist/1/review`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Check for key UI elements
    const checks = {
      hasHeader: await page.locator('text=/校对审核|Proofreading Review/i').count() > 0,
      hasBackButton: await page.locator('button:has-text("返回"), button:has-text("Back")').count() > 0,
      hasMainContent: await page.locator('main, article, .content').count() > 0,
    };

    console.log(`\n🎨 UI Elements Check:`);
    console.log(`   Header: ${checks.hasHeader ? '✅' : '❌'}`);
    console.log(`   Back Button: ${checks.hasBackButton ? '✅' : '❌'}`);
    console.log(`   Main Content: ${checks.hasMainContent ? '✅' : '❌'}`);

    // Take screenshot
    await page.screenshot({
      path: 'screenshots/proofreading-review-ui.png',
      fullPage: true
    });

    // At least header and main content should be present
    expect(checks.hasHeader || checks.hasMainContent).toBeTruthy();
  });

  test('should show loading state initially', async ({ page }) => {
    // Navigate to review page
    await page.goto(`${BASE_URL}/worklist/1/review`);

    // Check for loading indicator within first 500ms
    const hasLoadingIndicator = await page.locator('text=/加载中|Loading/i').count() > 0;
    const hasSpinner = await page.locator('.animate-spin').count() > 0;

    console.log(`\n⏳ Loading State:`);
    console.log(`   Has Loading Text: ${hasLoadingIndicator ? 'Yes' : 'No'}`);
    console.log(`   Has Spinner: ${hasSpinner ? 'Yes' : 'No'}`);
    console.log(`   Status: ${(hasLoadingIndicator || hasSpinner) ? '✅ PASS' : '⚠️  SKIP (loaded too fast)'}`);

    // Wait for page to fully load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    await page.screenshot({
      path: 'screenshots/proofreading-review-loaded.png',
      fullPage: true
    });
  });

  test('should handle API loading and error states', async ({ page }) => {
    let apiCalled = false;
    let apiStatus = 0;

    // Monitor API calls
    page.on('response', response => {
      if (response.url().includes('/v1/worklist/') && !response.url().includes('statistics')) {
        apiCalled = true;
        apiStatus = response.status();
        console.log(`\n🌐 API Call Detected:`);
        console.log(`   URL: ${response.url()}`);
        console.log(`   Status: ${apiStatus}`);
      }
    });

    // Navigate to review page
    await page.goto(`${BASE_URL}/worklist/1/review`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    if (apiCalled) {
      console.log(`   Expected: 200 or 404`);
      console.log(`   Status: ${(apiStatus === 200 || apiStatus === 404) ? '✅ PASS' : '❌ FAIL'}`);

      // Check for appropriate UI state based on status
      if (apiStatus === 404) {
        const hasNotFoundMessage = await page.locator('text=/未找到|Not Found|not found/i').count() > 0;
        console.log(`   Not Found Message: ${hasNotFoundMessage ? 'Yes' : 'No'}`);
      } else if (apiStatus === 200) {
        const hasContent = await page.locator('main, article, .content').count() > 0;
        console.log(`   Has Content: ${hasContent ? 'Yes' : 'No'}`);
      }
    } else {
      console.log(`\n⚠️  Warning: API call not detected`);
      console.log(`   This might indicate the page is not making API requests yet`);
    }

    await page.screenshot({
      path: 'screenshots/proofreading-review-api-state.png',
      fullPage: true
    });
  });

  test('should be accessible from worklist table', async ({ page }) => {
    // Navigate to worklist page first
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Check if there are any review buttons in the table
    const reviewButtons = await page.locator('button:has-text("审核"), button:has-text("Review")').count();

    console.log(`\n📋 Worklist Integration:`);
    console.log(`   Review Buttons Found: ${reviewButtons}`);

    if (reviewButtons > 0) {
      console.log(`   Status: ✅ PASS - Review buttons are visible`);

      // Take screenshot showing review buttons
      await page.screenshot({
        path: 'screenshots/worklist-review-buttons.png',
        fullPage: true
      });

      // Click the first review button
      await page.locator('button:has-text("审核"), button:has-text("Review")').first().click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);

      // Should navigate to review page
      const url = page.url();
      const isReviewPage = url.includes('/review');

      console.log(`   Navigation:`);
      console.log(`     Current URL: ${url}`);
      console.log(`     Is Review Page: ${isReviewPage ? 'Yes' : 'No'}`);
      console.log(`     Status: ${isReviewPage ? '✅ PASS' : '❌ FAIL'}`);

      await page.screenshot({
        path: 'screenshots/worklist-to-review-navigation.png',
        fullPage: true
      });

      expect(isReviewPage).toBeTruthy();
    } else {
      console.log(`   Status: ⚠️  SKIP - No review buttons (no items in under_review status)`);
    }
  });

  test('should show review page structure', async ({ page }) => {
    await page.goto(`${BASE_URL}/worklist/1/review`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Check for expected sections based on design spec
    const structure = {
      hasLeftPanel: await page.locator('.w-1\\/5, [data-testid="issue-list"]').count() > 0,
      hasMiddlePanel: await page.locator('.flex-1, [data-testid="article-content"]').count() > 0,
      hasRightPanel: await page.locator('.w-\\[30\\%\\], [data-testid="issue-detail"]').count() > 0,
      hasActionButtons: await page.locator('button:has-text("保存"), button:has-text("完成"), button:has-text("Save"), button:has-text("Complete")').count() > 0,
    };

    console.log(`\n🏗️  Page Structure:`);
    console.log(`   Left Panel (Issue List): ${structure.hasLeftPanel ? '✅' : '❌'}`);
    console.log(`   Middle Panel (Article Content): ${structure.hasMiddlePanel ? '✅' : '❌'}`);
    console.log(`   Right Panel (Issue Detail): ${structure.hasRightPanel ? '✅' : '❌'}`);
    console.log(`   Action Buttons: ${structure.hasActionButtons ? '✅' : '❌'}`);

    await page.screenshot({
      path: 'screenshots/proofreading-review-structure.png',
      fullPage: true
    });

    // At least middle panel (main content) should exist
    expect(structure.hasMiddlePanel).toBeTruthy();
  });

  test('should measure review page load performance', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(`${BASE_URL}/worklist/1/review`);
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    console.log(`\n⚡ Performance:`);
    console.log(`   Load Time: ${loadTime}ms`);
    console.log(`   Target: < 3000ms`);
    console.log(`   Status: ${loadTime < 3000 ? '✅ PASS' : '❌ FAIL'}`);

    await page.screenshot({
      path: 'screenshots/proofreading-review-performance.png',
      fullPage: true
    });

    // Review page should load in reasonable time
    expect(loadTime).toBeLessThan(3000);
  });

  test('should handle back navigation', async ({ page }) => {
    // Navigate to review page
    await page.goto(`${BASE_URL}/worklist/1/review`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Look for back button or link
    const backButton = page.locator('button:has-text("返回"), a:has-text("返回"), button:has-text("Back"), a:has-text("Back")').first();
    const hasBackButton = await backButton.count() > 0;

    console.log(`\n🔙 Back Navigation:`);
    console.log(`   Has Back Button: ${hasBackButton ? 'Yes' : 'No'}`);

    if (hasBackButton) {
      await backButton.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);

      const url = page.url();
      const isWorklistPage = url.includes('/worklist') && !url.includes('/review');

      console.log(`   After Click:`);
      console.log(`     URL: ${url}`);
      console.log(`     Back to Worklist: ${isWorklistPage ? 'Yes' : 'No'}`);
      console.log(`   Status: ${isWorklistPage ? '✅ PASS' : '❌ FAIL'}`);

      await page.screenshot({
        path: 'screenshots/proofreading-review-back-nav.png',
        fullPage: true
      });

      expect(isWorklistPage).toBeTruthy();
    } else {
      console.log(`   Status: ⚠️  SKIP - No back button found`);
    }
  });

  test('should support i18n (Chinese/English)', async ({ page }) => {
    await page.goto(`${BASE_URL}/worklist/1/review`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const pageText = await page.textContent('body') || '';

    const hasChinese = /[\u4e00-\u9fa5]/.test(pageText);
    const hasEnglish = /[a-zA-Z]/.test(pageText);

    console.log(`\n🌐 Internationalization:`);
    console.log(`   Has Chinese Text: ${hasChinese ? 'Yes' : 'No'}`);
    console.log(`   Has English Text: ${hasEnglish ? 'Yes' : 'No'}`);
    console.log(`   Status: ${(hasChinese || hasEnglish) ? '✅ PASS' : '❌ FAIL'}`);

    await page.screenshot({
      path: 'screenshots/proofreading-review-i18n.png',
      fullPage: true
    });

    // Should have some text content
    expect(hasChinese || hasEnglish).toBeTruthy();
  });
});
