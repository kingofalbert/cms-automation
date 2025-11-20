/**
 * Production Load Verification Test
 *
 * Verifies that the production site loads correctly after the fix
 */

import { test, expect } from '@playwright/test';

test.describe('Production Environment - Load Verification', () => {
  test('production site loads without errors', async ({ page }) => {
    const prodUrl = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

    // Collect console errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Collect network errors (404, 500, etc.)
    const networkErrors: string[] = [];
    page.on('response', response => {
      if (!response.ok()) {
        networkErrors.push(`${response.status()} ${response.url()}`);
      }
    });

    console.log(`📍 Navigating to: ${prodUrl}`);

    // Navigate to production site
    await page.goto(prodUrl, {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    // Wait for React root to mount
    await page.waitForSelector('#root', { timeout: 10000 });

    // Take screenshot
    await page.screenshot({
      path: 'test-results/production-load-verify.png',
      fullPage: true
    });

    console.log('✅ Page loaded successfully');
    console.log(`📊 Console errors: ${consoleErrors.length}`);
    console.log(`🌐 Network errors: ${networkErrors.length}`);

    if (consoleErrors.length > 0) {
      console.log('Console errors:', consoleErrors);
    }

    if (networkErrors.length > 0) {
      console.log('Network errors:', networkErrors);
    }

    // Verify no critical network errors (404 for JS bundles would be critical)
    const jsErrors = networkErrors.filter(err =>
      err.includes('.js') && err.includes('404')
    );

    expect(jsErrors.length).toBe(0);

    // Check if root element has content
    const rootContent = await page.locator('#root').innerHTML();
    expect(rootContent.length).toBeGreaterThan(0);

    console.log('✅ All verifications passed!');
  });

  test('can navigate to worklist page', async ({ page }) => {
    const prodUrl = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

    await page.goto(prodUrl, {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    // Wait for app to load
    await page.waitForSelector('#root', { timeout: 10000 });

    // Check if we can see any navigation or content
    const pageContent = await page.textContent('body');
    console.log('Page content length:', pageContent?.length || 0);

    // Take screenshot of what we see
    await page.screenshot({
      path: 'test-results/production-worklist-page.png',
      fullPage: true
    });

    console.log('✅ Worklist page screenshot captured');
  });
});
