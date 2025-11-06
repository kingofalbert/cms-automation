import { test, expect } from '@playwright/test';

/**
 * Production Environment Verification
 * Verifies Settings and Worklist pages load correctly after API path fixes
 */

const PROD_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323';

test.describe('Production Environment - API Fixes Verification', () => {
  test('Homepage loads successfully', async ({ page }) => {
    await page.goto(`${PROD_URL}/index.html`);
    await page.waitForLoadState('networkidle');

    // Should not show error boundary
    const errorBoundary = page.locator('text=應用程序出錯').or(page.locator('text=Something went wrong'));
    await expect(errorBoundary).not.toBeVisible();

    // Should show some content
    await expect(page.locator('body')).toBeVisible();

    console.log('✅ Homepage loaded successfully');
  });

  test('Settings page loads without API path errors', async ({ page }) => {
    const errors: string[] = [];
    const pageErrors: string[] = [];
    const apiRequests: { url: string; status: number }[] = [];
    const failedRequests: string[] = [];

    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Capture uncaught page errors
    page.on('pageerror', error => {
      pageErrors.push(`${error.name}: ${error.message}\n${error.stack}`);
    });

    // Capture failed requests
    page.on('requestfailed', request => {
      failedRequests.push(`${request.method()} ${request.url()} - ${request.failure()?.errorText}`);
    });

    // Capture API requests
    page.on('response', response => {
      const url = response.url();
      if (url.includes('/v1/')) {
        apiRequests.push({
          url,
          status: response.status(),
        });
      }
    });

    // Navigate directly to settings page
    await page.goto(`${PROD_URL}/index.html#/settings`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // Wait for any async operations

    // Take screenshot for verification
    await page.screenshot({ path: 'test-results/production-settings-page.png', fullPage: true });

    // Log API requests FIRST
    console.log('\n📡 API Requests made:');
    if (apiRequests.length === 0) {
      console.log('  (No API requests captured)');
    } else {
      apiRequests.forEach(req => {
        const status = req.status >= 200 && req.status < 300 ? '✅' : '❌';
        console.log(`  ${status} ${req.status} ${req.url}`);
      });
    }

    // Log page errors FIRST (uncaught exceptions)
    if (pageErrors.length > 0) {
      console.log('\n🔴 Page Errors (Uncaught Exceptions):');
      pageErrors.forEach(err => console.log(`  ${err}`));
    }

    // Log console errors
    if (errors.length > 0) {
      console.log('\n⚠️  Console Errors:');
      errors.forEach(err => console.log(`  - ${err}`));
    }

    // Log failed network requests
    if (failedRequests.length > 0) {
      console.log('\n❌ Failed Network Requests:');
      failedRequests.forEach(req => console.log(`  - ${req}`));
    }

    // Check that error boundary is NOT displayed
    const errorBoundary = page.locator('text=應用程序出錯').or(page.locator('text=Something went wrong'));
    const hasError = await errorBoundary.isVisible().catch(() => false);

    if (hasError) {
      console.error('\n❌ Error boundary is visible on Settings page');
      throw new Error('Settings page shows error boundary');
    }

    // Check for API path errors (404s on /v1/ endpoints)
    const failedApiRequests = apiRequests.filter(req => req.status >= 400);
    if (failedApiRequests.length > 0) {
      console.error('\n❌ Failed API requests:');
      failedApiRequests.forEach(req => {
        console.error(`  ${req.status} ${req.url}`);
      });
    }

    console.log('\n✅ Settings page verification complete');
    expect(failedApiRequests.length).toBe(0);
  });

  test('Worklist page loads without API path errors', async ({ page }) => {
    const errors: string[] = [];
    const apiRequests: { url: string; status: number }[] = [];

    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Capture API requests
    page.on('response', response => {
      const url = response.url();
      if (url.includes('/v1/')) {
        apiRequests.push({
          url,
          status: response.status(),
        });
      }
    });

    // Navigate directly to worklist page
    await page.goto(`${PROD_URL}/index.html#/worklist`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Take screenshot
    await page.screenshot({ path: 'test-results/production-worklist-page.png', fullPage: true });

    // Log API requests FIRST
    console.log('\n📡 API Requests made:');
    apiRequests.forEach(req => {
      const status = req.status >= 200 && req.status < 300 ? '✅' : '❌';
      console.log(`  ${status} ${req.status} ${req.url}`);
    });

    // Log errors BEFORE checking error boundary
    if (errors.length > 0) {
      console.log('\n⚠️  Console Errors:');
      errors.forEach(err => console.log(`  - ${err}`));
    }

    // Check that error boundary is NOT displayed
    const errorBoundary = page.locator('text=應用程序出錯').or(page.locator('text=Something went wrong'));
    const hasError = await errorBoundary.isVisible().catch(() => false);

    if (hasError) {
      console.error('❌ Error boundary is visible on Worklist page');
      throw new Error('Worklist page shows error boundary');
    }

    // Check for failed API requests
    const failedApiRequests = apiRequests.filter(req => req.status >= 400);
    if (failedApiRequests.length > 0) {
      console.error('\n❌ Failed API requests:');
      failedApiRequests.forEach(req => {
        console.error(`  ${req.status} ${req.url}`);
      });
    }

    console.log('\n✅ Worklist page verification complete');
    expect(failedApiRequests.length).toBe(0);
  });

  test('Verify no malformed API paths in network requests', async ({ page }) => {
    const malformedRequests: string[] = [];

    page.on('request', request => {
      const url = request.url();

      // Check for common malformed path patterns
      if (url.includes('storage.googleapis.com')) {
        // Bad pattern 1: v1/ without leading slash (would be relative)
        // This would appear as: .../some-path/v1/endpoint
        if (url.match(/[^/]v1\//)) {
          malformedRequests.push(`Missing leading slash: ${url}`);
        }

        // Bad pattern 2: api/v1/ prefix (should be just /v1/)
        if (url.includes('api/v1/')) {
          malformedRequests.push(`Extra api/ prefix: ${url}`);
        }
      }
    });

    // Visit both pages
    await page.goto(`${PROD_URL}/index.html#/settings`);
    await page.waitForTimeout(2000);

    await page.goto(`${PROD_URL}/index.html#/worklist`);
    await page.waitForTimeout(2000);

    if (malformedRequests.length > 0) {
      console.error('\n❌ Malformed API requests detected:');
      malformedRequests.forEach(req => console.error(`  - ${req}`));
    }

    expect(malformedRequests).toHaveLength(0);
  });
});
