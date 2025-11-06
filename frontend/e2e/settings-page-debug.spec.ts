import { test, expect } from '@playwright/test';

const FRONTEND_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';
const BACKEND_URL = 'https://cms-automation-backend-297291472291.us-east1.run.app';

test.describe('Settings Page Debug', () => {
  test('should investigate Settings page error', async ({ page }) => {
    const consoleMessages: string[] = [];
    const errors: string[] = [];
    const networkRequests: Array<{ url: string; status: number; method: string }> = [];

    // Capture console messages
    page.on('console', (msg) => {
      const text = msg.text();
      consoleMessages.push(`[${msg.type()}] ${text}`);
      if (msg.type() === 'error') {
        errors.push(text);
      }
    });

    // Capture page errors
    page.on('pageerror', (error) => {
      errors.push(`Page Error: ${error.message}`);
    });

    // Capture network requests
    page.on('response', async (response) => {
      networkRequests.push({
        url: response.url(),
        status: response.status(),
        method: response.request().method(),
      });
    });

    console.log('Navigating to Settings page...');
    await page.goto(`${FRONTEND_URL}#/settings`, {
      waitUntil: 'networkidle',
      timeout: 30000,
    });

    // Wait a bit for any async operations
    await page.waitForTimeout(3000);

    // Take a screenshot
    await page.screenshot({
      path: 'test-results/settings-page-debug.png',
      fullPage: true,
    });

    // Log all findings
    console.log('\n=== Console Messages ===');
    consoleMessages.forEach((msg) => console.log(msg));

    console.log('\n=== Errors ===');
    if (errors.length > 0) {
      errors.forEach((err) => console.log(err));
    } else {
      console.log('No errors detected');
    }

    console.log('\n=== Failed Network Requests ===');
    const failedRequests = networkRequests.filter((req) => req.status >= 400);
    if (failedRequests.length > 0) {
      failedRequests.forEach((req) => {
        console.log(`${req.method} ${req.url} - Status: ${req.status}`);
      });
    } else {
      console.log('No failed requests');
    }

    console.log('\n=== API Requests to Backend ===');
    const apiRequests = networkRequests.filter((req) => req.url.includes(BACKEND_URL));
    apiRequests.forEach((req) => {
      console.log(`${req.method} ${req.url} - Status: ${req.status}`);
    });

    console.log('\n=== API Requests to Frontend Domain (WRONG!) ===');
    const wrongDomainRequests = networkRequests.filter((req) =>
      req.url.includes('storage.googleapis.com') &&
      (req.url.includes('/v1/') || req.url.includes('/api/'))
    );
    if (wrongDomainRequests.length > 0) {
      wrongDomainRequests.forEach((req) => {
        console.log(`${req.method} ${req.url} - Status: ${req.status}`);
      });
    } else {
      console.log('No wrong-domain API requests detected');
    }

    // Check if the page has any visible error messages
    const errorText = await page.locator('text=/error|failed|錯誤|失敗/i').all();
    if (errorText.length > 0) {
      console.log('\n=== Visible Error Messages on Page ===');
      for (const elem of errorText) {
        const text = await elem.textContent();
        console.log(text);
      }
    }

    // Get page content for analysis
    const pageContent = await page.content();
    console.log('\n=== Page Title ===');
    console.log(await page.title());

    // The test will fail if there are any errors, allowing us to see all the debug info
    expect(errors.length, `Found ${errors.length} errors on Settings page`).toBe(0);
  });

  test('should check Settings page via menu navigation', async ({ page }) => {
    const consoleMessages: string[] = [];
    const errors: string[] = [];

    // Capture console and page errors
    page.on('console', (msg) => {
      const text = msg.text();
      consoleMessages.push(`[${msg.type()}] ${text}`);
      if (msg.type() === 'error') {
        errors.push(text);
      }
    });

    page.on('pageerror', (error) => {
      errors.push(`Page Error: ${error.message}`);
    });

    console.log('Navigating to home page...');
    await page.goto(FRONTEND_URL, {
      waitUntil: 'networkidle',
      timeout: 30000,
    });

    // Wait for navigation to load
    await page.waitForTimeout(2000);

    // Find and click the Settings menu button
    console.log('Looking for Settings menu button...');
    const settingsLink = page.locator('a[href="#/settings"], button:has-text("設置"), a:has-text("設置")');

    await settingsLink.first().waitFor({ timeout: 10000 });

    console.log('Clicking Settings menu button...');
    await settingsLink.first().click();

    // Wait for navigation and any async operations
    await page.waitForTimeout(3000);

    // Take a screenshot
    await page.screenshot({
      path: 'test-results/settings-page-via-menu.png',
      fullPage: true,
    });

    // Log errors if any
    console.log('\n=== Errors After Menu Click ===');
    if (errors.length > 0) {
      errors.forEach((err) => console.log(err));
    } else {
      console.log('No errors detected');
    }

    expect(errors.length, `Found ${errors.length} errors when navigating via menu`).toBe(0);
  });
});
