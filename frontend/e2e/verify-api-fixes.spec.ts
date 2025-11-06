import { test, expect } from '@playwright/test';

/**
 * Verification test for API path fixes
 * Tests that Settings and Worklist pages load correctly with fixed API paths
 */

test.describe('API Path Fixes Verification', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the production site
    await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html');

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
  });

  test('Settings page loads without errors', async ({ page }) => {
    const errors: string[] = [];

    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Click on Settings menu item
    const settingsLink = page.locator('a[href="/settings"]').first();
    await settingsLink.click();

    // Wait for navigation
    await page.waitForURL('**/settings');
    await page.waitForLoadState('networkidle');

    // Wait a moment for any API calls to complete
    await page.waitForTimeout(2000);

    // Check that error boundary is NOT displayed
    const errorBoundary = page.locator('text=應用程序出錯').or(page.locator('text=Something went wrong'));
    await expect(errorBoundary).not.toBeVisible();

    // Check that Settings content is visible
    const settingsTitle = page.locator('h1, h2, h3').filter({ hasText: /设置|設置|Settings/i });
    await expect(settingsTitle).toBeVisible();

    // Log any errors
    if (errors.length > 0) {
      console.log('Console errors found:', errors);
      expect(errors.filter(e => e.includes('API') || e.includes('404'))).toHaveLength(0);
    }
  });

  test('Worklist page loads without errors', async ({ page }) => {
    const errors: string[] = [];

    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Click on Worklist menu item
    const worklistLink = page.locator('a[href="/worklist"]').first();
    await worklistLink.click();

    // Wait for navigation
    await page.waitForURL('**/worklist');
    await page.waitForLoadState('networkidle');

    // Wait a moment for any API calls to complete
    await page.waitForTimeout(2000);

    // Check that error boundary is NOT displayed
    const errorBoundary = page.locator('text=應用程序出錯').or(page.locator('text=Something went wrong'));
    await expect(errorBoundary).not.toBeVisible();

    // Check that Worklist content is visible
    const worklistTitle = page.locator('h1, h2, h3').filter({ hasText: /worklist|工作列表|待处理/i });
    await expect(worklistTitle).toBeVisible();

    // Log any errors
    if (errors.length > 0) {
      console.log('Console errors found:', errors);
      expect(errors.filter(e => e.includes('API') || e.includes('404'))).toHaveLength(0);
    }
  });

  test('All service endpoints use correct paths', async ({ page }) => {
    const apiRequests: { url: string; method: string }[] = [];

    // Capture all API requests
    page.on('request', request => {
      const url = request.url();
      if (url.includes('/v1/') || url.includes('api/')) {
        apiRequests.push({
          url,
          method: request.method(),
        });
      }
    });

    // Visit both pages to trigger API calls
    await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html');
    await page.waitForLoadState('networkidle');

    const settingsLink = page.locator('a[href="/settings"]').first();
    await settingsLink.click();
    await page.waitForTimeout(2000);

    const worklistLink = page.locator('a[href="/worklist"]').first();
    await worklistLink.click();
    await page.waitForTimeout(2000);

    // Log captured API requests
    console.log('API Requests captured:', apiRequests.length);
    apiRequests.forEach(req => {
      console.log(`  ${req.method} ${req.url}`);
    });

    // Verify no requests have malformed paths (missing leading slash would cause issues)
    const malformedRequests = apiRequests.filter(req => {
      const url = new URL(req.url);
      // Check for paths that don't start with /v1/ or have duplicate /api/
      return url.pathname.includes('undefined') ||
             url.pathname.includes('//') ||
             url.pathname.includes('api/v1/');
    });

    expect(malformedRequests).toHaveLength(0);
  });
});
