import { test, expect } from '@playwright/test';

// Configuration - Add cache-busting to bypass CDN cache
const CACHE_BUST = Date.now();
const FRONTEND_URL = process.env.TEST_LOCAL
  ? 'http://localhost:3000'
  : `https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html?v=${CACHE_BUST}`;

const BACKEND_URL = 'https://cms-automation-backend-baau2zqeqq-ue.a.run.app';

test.describe('Proofreading Page Click Test', () => {

  test.beforeEach(async ({ page }) => {
    // Collect console messages and errors
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      console.log(`[Browser ${type.toUpperCase()}] ${text}`);
    });

    // Collect network errors
    page.on('requestfailed', request => {
      console.log(`[Network Failed] ${request.method()} ${request.url()} - ${request.failure()?.errorText}`);
    });

    // Collect page errors
    page.on('pageerror', error => {
      console.log(`[Page Error] ${error.message}`);
      console.log(`[Stack] ${error.stack}`);
    });
  });

  test('Click worklist item and load proofreading page', async ({ page }) => {
    console.log('\n========================================');
    console.log('TEST: Click to Proofreading Page');
    console.log('========================================\n');

    // Step 1: Navigate to homepage
    console.log('Step 1: Navigating to homepage...');
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.screenshot({ path: 'test-results/click-01-homepage.png', fullPage: true });
    console.log('✓ Homepage loaded');

    // Step 2: Wait for worklist to load
    console.log('\nStep 2: Waiting for worklist data...');
    await page.waitForTimeout(3000);

    // Check if worklist items are visible
    const worklistItems = page.locator('tr[role="row"]').filter({ hasText: /被蜱蟲|902386|天然補血/ });
    const itemCount = await worklistItems.count();
    console.log(`Found ${itemCount} worklist items`);

    if (itemCount === 0) {
      console.log('❌ No worklist items found!');
      await page.screenshot({ path: 'test-results/click-02-no-items.png', fullPage: true });
      throw new Error('No worklist items to click');
    }

    // Step 3: Click the first item
    console.log('\nStep 3: Clicking first worklist item...');
    const firstItem = worklistItems.first();
    const itemTitle = await firstItem.locator('td').nth(1).textContent();
    console.log(`Clicking item: "${itemTitle}"`);

    await page.screenshot({ path: 'test-results/click-03-before-click.png', fullPage: true });

    // Click the item
    await firstItem.click();
    console.log('✓ Item clicked');

    // Step 4: Wait for navigation and page load
    console.log('\nStep 4: Waiting for proofreading page to load...');
    await page.waitForTimeout(3000);

    // Check URL
    const currentUrl = page.url();
    console.log(`Current URL: ${currentUrl}`);

    // Check if we're on the proofreading page
    const isProofreadingPage = currentUrl.includes('/proofreading/');
    console.log(`Is proofreading page: ${isProofreadingPage}`);

    await page.screenshot({ path: 'test-results/click-04-after-click.png', fullPage: true });

    // Step 5: Check for errors on the page
    console.log('\nStep 5: Checking for errors...');

    // Check for error messages
    const errorElements = await page.locator('.error, [role="alert"], .alert-error, .text-red-500, .text-red-600').allTextContents();
    if (errorElements.length > 0) {
      console.log('⚠️  Error messages found:');
      errorElements.forEach(msg => console.log(`  - ${msg}`));
    } else {
      console.log('✓ No error messages');
    }

    // Check if main content is visible
    const hasContent = await page.locator('article, main, [role="main"]').count() > 0;
    console.log(`Has main content: ${hasContent}`);

    // Check for proofreading-specific elements
    const hasViewModeButtons = await page.locator('button:has-text("Original"), button:has-text("Rendered"), button:has-text("Preview")').count() > 0;
    console.log(`Has view mode buttons: ${hasViewModeButtons}`);

    const hasIssuesList = await page.locator('[data-testid*="issue"], .issue-item, .proofreading-issue').count() > 0;
    console.log(`Has issues list: ${hasIssuesList}`);

    await page.screenshot({ path: 'test-results/click-05-final.png', fullPage: true });

    // Assertions
    expect(isProofreadingPage).toBeTruthy();
    expect(errorElements.length).toBe(0);
    expect(hasContent).toBeTruthy();
  });
});
