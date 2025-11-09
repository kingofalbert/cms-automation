/**
 * Verify Production Worklist Page Loads
 *
 * This test verifies that the production worklist page loads without errors
 */

import { test, expect } from '@playwright/test';

test.describe('Production Worklist Page', () => {
  test('should load worklist page without errors', async ({ page }) => {
    const errors: string[] = [];
    const consoleErrors: string[] = [];

    // Capture console errors
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Capture page errors
    page.on('pageerror', (error) => {
      errors.push(error.message);
    });

    console.log('\n=== LOADING PRODUCTION WORKLIST PAGE ===\n');

    // Load production page
    await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html', {
      waitUntil: 'networkidle',
      timeout: 30000,
    });

    console.log('Page loaded, waiting for content...\n');

    // Wait for React to mount
    await page.waitForSelector('#root', { timeout: 10000 });

    // Wait a bit for the app to initialize
    await page.waitForTimeout(3000);

    // Check for page errors
    console.log('=== PAGE ERRORS ===');
    if (errors.length > 0) {
      console.log('Errors found:');
      errors.forEach(err => console.log(`  - ${err}`));
    } else {
      console.log('✅ No page errors\n');
    }

    console.log('=== CONSOLE ERRORS ===');
    if (consoleErrors.length > 0) {
      console.log('Console errors found:');
      consoleErrors.forEach(err => console.log(`  - ${err}`));
    } else {
      console.log('✅ No console errors\n');
    }

    // Take screenshot
    await page.screenshot({ path: '/tmp/production-worklist-page.png', fullPage: true });
    console.log('Screenshot saved to /tmp/production-worklist-page.png\n');

    // Check if the app rendered
    const rootContent = await page.locator('#root').innerHTML();
    console.log(`Root element has content: ${rootContent.length > 100 ? '✅ YES' : '❌ NO'}`);

    // Look for navigation or worklist elements
    const hasNavigation = await page.locator('nav').count() > 0;
    console.log(`Has navigation: ${hasNavigation ? '✅ YES' : '❌ NO'}`);

    // Check for the app name in navigation
    const appName = await page.locator('nav a').first().textContent();
    console.log(`App name in nav: "${appName}"\n`);

    // Assertions
    expect(errors.length, `Expected no page errors, but found ${errors.length}`).toBe(0);
    expect(rootContent.length, 'Root element should have content').toBeGreaterThan(100);
    expect(hasNavigation, 'Should have navigation element').toBe(true);

    console.log('=== TEST PASSED ===\n');
  });
});
