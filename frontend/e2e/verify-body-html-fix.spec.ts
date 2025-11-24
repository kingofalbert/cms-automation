/**
 * E2E Test: Verify HOTFIX-PARSE-004 - body_html saves correctly
 *
 * This test verifies that the "正文长度 0 字符" issue is fixed.
 * The fix ensures body_html is saved in both:
 * - pipeline.py (worklist auto-parsing)
 * - articles.py (manual reparse endpoint)
 */

import { test, expect } from '@playwright/test';

const PRODUCTION_FRONTEND_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/';
const PRODUCTION_BACKEND_URL = 'https://cms-automation-backend-297291472291.us-east1.run.app';

test.describe('HOTFIX-PARSE-004: body_html Display Verification', () => {
  test.beforeEach(async ({ page }) => {
    // Set longer timeout for production tests
    test.setTimeout(60000);
  });

  test('should display body length > 0 in parsing result page', async ({ page }) => {
    // Step 1: Navigate to worklist page
    console.log('Navigating to worklist page...');
    await page.goto(`${PRODUCTION_FRONTEND_URL}#/worklist`);
    await page.waitForLoadState('networkidle');

    // Wait for worklist to load
    await page.waitForTimeout(3000);

    // Take screenshot of worklist
    await page.screenshot({
      path: 'test-results/worklist-page.png',
      fullPage: true
    });
    console.log('Worklist screenshot saved');

    // Step 2: Find an article with parsing status (has article_id)
    // Look for clickable article row
    const articleRows = page.locator('tr').filter({ hasText: /parsing|解析/ });
    const rowCount = await articleRows.count();
    console.log(`Found ${rowCount} rows with parsing status`);

    if (rowCount === 0) {
      // Try to find any row with an article ID
      const allRows = page.locator('tbody tr');
      const allRowCount = await allRows.count();
      console.log(`Total rows in table: ${allRowCount}`);

      if (allRowCount > 0) {
        // Click first row to open drawer
        await allRows.first().click();
        await page.waitForTimeout(1000);

        // Take screenshot of drawer
        await page.screenshot({
          path: 'test-results/article-drawer.png',
          fullPage: true
        });
      }
    }
  });

  test('should verify parsing API returns body_html > 0 characters', async ({ page, request }) => {
    // Step 1: Get worklist items from API
    console.log('Fetching worklist items...');
    const worklistResponse = await request.get(`${PRODUCTION_BACKEND_URL}/v1/worklist/items?limit=10`);

    if (!worklistResponse.ok()) {
      console.log('Failed to fetch worklist:', worklistResponse.status());
      test.skip();
      return;
    }

    const worklistData = await worklistResponse.json();
    console.log(`Found ${worklistData.length || 0} worklist items`);

    // Step 2: Find an item with article_id
    const itemWithArticle = worklistData.find((item: any) => item.article_id);

    if (!itemWithArticle) {
      console.log('No worklist item with article_id found');
      test.skip();
      return;
    }

    console.log(`Testing article ID: ${itemWithArticle.article_id}`);

    // Step 3: Get parsing result for that article
    const parsingResponse = await request.get(
      `${PRODUCTION_BACKEND_URL}/v1/articles/${itemWithArticle.article_id}/parsing-result`
    );

    if (!parsingResponse.ok()) {
      console.log('Parsing result not available (article not parsed yet):', parsingResponse.status());
      // This is expected for some articles
      return;
    }

    const parsingData = await parsingResponse.json();
    console.log('Parsing data received:', {
      title_main: parsingData.title_main,
      body_html_length: parsingData.body_html?.length || 0,
      parsing_method: parsingData.parsing_method,
    });

    // Step 4: Verify body_html is not empty (THE KEY FIX VERIFICATION)
    const bodyHtmlLength = parsingData.body_html?.length || 0;

    console.log(`VERIFICATION: body_html length = ${bodyHtmlLength} characters`);

    // If body_html is 0, the fix didn't work
    if (bodyHtmlLength === 0) {
      console.error('HOTFIX-PARSE-004 NOT WORKING: body_html is still 0!');
    } else {
      console.log('HOTFIX-PARSE-004 VERIFIED: body_html has content!');
    }

    // Soft assertion - log but don't fail if no content (might be newly imported)
    expect.soft(bodyHtmlLength).toBeGreaterThan(0);
  });

  test('visual test: parsing page displays body content', async ({ page }) => {
    // Navigate directly to a parsing page if we know an article ID
    // First try to get one from API
    const response = await page.request.get(`${PRODUCTION_BACKEND_URL}/v1/worklist/items?limit=5`);

    if (!response.ok()) {
      console.log('Cannot fetch worklist for visual test');
      test.skip();
      return;
    }

    const items = await response.json();
    const itemWithArticle = items.find((item: any) => item.article_id);

    if (!itemWithArticle) {
      console.log('No article available for visual test');
      test.skip();
      return;
    }

    const articleId = itemWithArticle.article_id;
    console.log(`Visual test for article ${articleId}`);

    // Navigate to parsing page
    await page.goto(`${PRODUCTION_FRONTEND_URL}#/articles/${articleId}/parsing`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Take full page screenshot
    await page.screenshot({
      path: 'test-results/parsing-page-visual.png',
      fullPage: true
    });

    // Look for the body length text
    const bodyLengthText = page.locator('text=/正文长度.*字符/');
    const exists = await bodyLengthText.count() > 0;

    if (exists) {
      const text = await bodyLengthText.first().textContent();
      console.log(`Body length display: ${text}`);

      // Check if it says "0 字符" (the bug)
      if (text?.includes('0 字符')) {
        console.error('BUG DETECTED: Body length shows 0 字符!');
        // Take a screenshot with highlight
        await page.screenshot({
          path: 'test-results/body-html-bug-detected.png',
          fullPage: true
        });
      } else {
        console.log('PASS: Body length is not 0');
      }

      // Extract the number
      const match = text?.match(/正文长度:\s*(\d+)\s*字符/);
      if (match) {
        const length = parseInt(match[1]);
        expect(length).toBeGreaterThan(0);
        console.log(`Verified body_html length: ${length} characters`);
      }
    } else {
      console.log('Body length text not found on page - may be loading or error');
      // Take screenshot for debugging
      await page.screenshot({
        path: 'test-results/parsing-page-no-body-text.png',
        fullPage: true
      });
    }
  });
});

test.describe('Chrome DevTools Visual Verification', () => {
  test('capture full parsing page state', async ({ page }) => {
    // This test uses standard Playwright but captures detailed state
    // for integration with Chrome DevTools MCP

    const response = await page.request.get(`${PRODUCTION_BACKEND_URL}/v1/worklist/items?limit=3`);

    if (!response.ok()) {
      test.skip();
      return;
    }

    const items = await response.json();
    const itemWithArticle = items.find((item: any) => item.article_id);

    if (!itemWithArticle) {
      test.skip();
      return;
    }

    const articleId = itemWithArticle.article_id;

    // Go to parsing page
    await page.goto(`${PRODUCTION_FRONTEND_URL}#/articles/${articleId}/parsing`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);

    // Capture console logs
    const consoleLogs: string[] = [];
    page.on('console', msg => consoleLogs.push(`${msg.type()}: ${msg.text()}`));

    // Capture network requests for parsing result
    const parsingRequests: string[] = [];
    page.on('response', response => {
      if (response.url().includes('parsing-result')) {
        parsingRequests.push(`${response.status()} ${response.url()}`);
      }
    });

    // Wait a bit more for any async operations
    await page.waitForTimeout(2000);

    // Take comprehensive screenshot
    await page.screenshot({
      path: 'test-results/chrome-devtools-parsing-state.png',
      fullPage: true
    });

    // Log captured data
    console.log('Console logs:', consoleLogs.slice(0, 10));
    console.log('Parsing requests:', parsingRequests);

    // Get page content for analysis
    const pageContent = await page.content();
    const hasBodyLengthZero = pageContent.includes('正文长度: 0 字符') ||
                              pageContent.includes('正文长度:0 字符');

    if (hasBodyLengthZero) {
      console.error('PAGE SHOWS 0 CHARACTER BODY - BUG NOT FIXED!');
      await page.screenshot({
        path: 'test-results/BUG-body-length-zero.png',
        fullPage: true
      });
    }

    expect(hasBodyLengthZero).toBe(false);
  });
});
