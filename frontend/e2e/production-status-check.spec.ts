import { test, expect } from '@playwright/test';

// Test actual production URLs (no cache-busting)
const PRODUCTION_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

test.describe('Production Status Check', () => {

  test('Check homepage worklist loads correctly', async ({ page }) => {
    console.log('\n=== Testing Production Homepage ===\n');

    await page.goto(PRODUCTION_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(5000);

    // Take screenshot
    await page.screenshot({ path: 'test-results/prod-home.png', fullPage: true });

    // Check for worklist table
    const table = await page.locator('table').count();
    console.log(`Tables found: ${table}`);

    // Check for any items
    const rows = await page.locator('tr[role="row"]').count();
    console.log(`Table rows found: ${rows}`);

    // Get page text
    const bodyText = await page.locator('body').textContent();
    console.log(`\nPage has content: ${bodyText && bodyText.length > 100}`);
  });

  test('Check proofreading page for item 2', async ({ page }) => {
    console.log('\n=== Testing Production Proofreading Page ===\n');

    const proofreadingUrl = `${PRODUCTION_URL}#/proofreading/2`;
    await page.goto(proofreadingUrl, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(5000);

    // Take screenshot
    await page.screenshot({ path: 'test-results/prod-proofreading.png', fullPage: true });

    // Check for content
    const hasContent = await page.locator('article, main, [role="main"]').count();
    console.log(`Main content elements: ${hasContent}`);

    const bodyText = await page.locator('body').textContent();
    console.log(`Page text length: ${bodyText?.length || 0}`);
    console.log(`Has substantial content: ${bodyText && bodyText.length > 200}`);
  });
});
