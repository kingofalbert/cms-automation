/**
 * Verification test for Rendered View fix
 * Tests that clicking Rendered button now works without error
 */

import { test, expect } from '@playwright/test';

const CACHE_BUST = Date.now();
const FRONTEND_URL = `https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html?v=${CACHE_BUST}`;

test.describe('Rendered View Fix Verification', () => {
  test('Rendered view should work without errors', async ({ page }) => {
    const errors: string[] = [];

    // Capture page errors
    page.on('pageerror', (error) => {
      errors.push(error.message);
      console.log('PAGE ERROR:', error.message);
    });

    console.log(`\nNavigating to: ${FRONTEND_URL}\n`);
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Find and click first Review button
    console.log('Looking for Review button...');
    const reviewButton = page.locator('button:has-text("Review")').first();
    await reviewButton.waitFor({ state: 'visible', timeout: 10000 });
    await reviewButton.click();

    // Wait for proofreading page
    await page.waitForTimeout(3000);
    console.log('On proofreading page\n');

    // Click Rendered button
    console.log('Clicking Rendered button...');
    const renderedButton = page.locator('button:has-text("Rendered")');
    await renderedButton.waitFor({ state: 'visible' });
    await renderedButton.click();

    // Wait for rendering
    await page.waitForTimeout(3000);

    // Check if error boundary is shown
    const errorTitle = await page.locator('text=應用程序出錯').count();

    console.log('\n=== VERIFICATION RESULTS ===');
    console.log(`Error boundary shown: ${errorTitle > 0 ? '❌ YES (FAILED)' : '✅ NO (SUCCESS)'}`);
    console.log(`Page errors: ${errors.length > 0 ? errors.join(', ') : 'None'}`);

    // Verify NO error boundary
    expect(errorTitle).toBe(0);
    expect(errors.length).toBe(0);

    // Verify Markdown was rendered
    const h1Count = await page.locator('h1').count();
    const h2Count = await page.locator('h2').count();
    const h3Count = await page.locator('h3').count();

    console.log('\n=== HTML ELEMENTS FOUND ===');
    console.log(`H1 headings: ${h1Count}`);
    console.log(`H2 headings: ${h2Count}`);
    console.log(`H3 headings: ${h3Count}`);
    console.log(`Total formatted elements: ${h1Count + h2Count + h3Count}`);

    // Should have at least some formatted content
    const totalFormatting = h1Count + h2Count + h3Count;
    expect(totalFormatting).toBeGreaterThan(0);

    // Take screenshot
    await page.screenshot({
      path: 'test-results/rendered-view-fixed.png',
      fullPage: true
    });

    console.log('\n✅ RENDERED VIEW FIX VERIFIED!\n');
    console.log('===========================\n');
  });
});
