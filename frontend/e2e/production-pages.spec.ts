import { test, expect, type Page } from '@playwright/test';

const PRODUCTION_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323';
const BACKEND_URL = 'https://cms-automation-backend-297291472291.us-east1.run.app';

// All pages in the application
const PAGES = [
  { path: '/index.html', name: 'Home Page', expectAuth: false },
  { path: '/index.html#/', name: 'Root Route', expectAuth: false },
  { path: '/index.html#/articles', name: 'Articles List', expectAuth: true },
  { path: '/index.html#/articles/generate', name: 'Article Generator', expectAuth: true },
  { path: '/index.html#/articles/import', name: 'Article Import', expectAuth: true },
  { path: '/index.html#/worklist', name: 'Worklist', expectAuth: true },
  { path: '/index.html#/publish-tasks', name: 'Publish Tasks', expectAuth: true },
  { path: '/index.html#/tags', name: 'Tags Management', expectAuth: true },
  { path: '/index.html#/rules/draft', name: 'Draft Rules', expectAuth: true },
  { path: '/index.html#/rules/published', name: 'Published Rules', expectAuth: true },
  { path: '/index.html#/rules/test', name: 'Rule Test', expectAuth: true },
  { path: '/index.html#/schedule', name: 'Schedule Manager', expectAuth: true },
  { path: '/index.html#/proofreading', name: 'Proofreading Stats', expectAuth: true },
  { path: '/index.html#/provider-comparison', name: 'Provider Comparison', expectAuth: true },
  { path: '/index.html#/settings', name: 'Settings', expectAuth: true },
];

test.describe('Production Website - All Pages Test', () => {
  let consoleErrors: string[] = [];
  let networkErrors: string[] = [];
  let jsErrors: string[] = [];

  test.beforeEach(async ({ page }) => {
    // Reset error collectors
    consoleErrors = [];
    networkErrors = [];
    jsErrors = [];

    // Listen for console errors
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(`Console Error: ${msg.text()}`);
      }
    });

    // Listen for page errors (JavaScript errors)
    page.on('pageerror', (error) => {
      jsErrors.push(`JS Error: ${error.message}`);
    });

    // Listen for network errors
    page.on('response', (response) => {
      if (!response.ok() && response.status() !== 304) {
        networkErrors.push(
          `Network Error: ${response.status()} ${response.statusText()} - ${response.url()}`
        );
      }
    });

    // Listen for failed requests
    page.on('requestfailed', (request) => {
      networkErrors.push(`Request Failed: ${request.url()} - ${request.failure()?.errorText}`);
    });
  });

  test.afterEach(async ({ page }, testInfo) => {
    // Log errors if test failed
    if (testInfo.status !== 'passed') {
      console.log('\n=== Test Failed: ' + testInfo.title + ' ===');

      if (consoleErrors.length > 0) {
        console.log('\n--- Console Errors ---');
        consoleErrors.forEach((err) => console.log(err));
      }

      if (jsErrors.length > 0) {
        console.log('\n--- JavaScript Errors ---');
        jsErrors.forEach((err) => console.log(err));
      }

      if (networkErrors.length > 0) {
        console.log('\n--- Network Errors ---');
        networkErrors.forEach((err) => console.log(err));
      }

      // Take screenshot on failure
      await page.screenshot({
        path: `test-results/failure-${testInfo.title.replace(/\s+/g, '-')}.png`,
        fullPage: true
      });
    }
  });

  // Test backend health first
  test('Backend Health Check', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/health`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toBe('healthy');
    expect(data.service).toBe('cms-automation');
  });

  // Test each page
  for (const pageInfo of PAGES) {
    test(`Load ${pageInfo.name} (${pageInfo.path})`, async ({ page }) => {
      const url = `${PRODUCTION_URL}${pageInfo.path}`;

      console.log(`\nTesting: ${pageInfo.name}`);
      console.log(`URL: ${url}`);

      // Navigate to the page
      const response = await page.goto(url, {
        waitUntil: 'networkidle',
        timeout: 30000,
      });

      // Check that page loaded successfully
      expect(response?.status()).toBe(200);

      // Wait for React to render
      await page.waitForTimeout(2000);

      // Check if there's a root element
      const root = await page.locator('#root');
      await expect(root).toBeVisible({ timeout: 10000 });

      // Check if content is rendered (not just a blank page)
      const rootContent = await root.innerHTML();
      expect(rootContent.length).toBeGreaterThan(100);

      // Take a screenshot for visual inspection
      await page.screenshot({
        path: `test-results/page-${pageInfo.name.replace(/\s+/g, '-')}.png`,
        fullPage: true
      });

      // Report errors found during page load
      if (consoleErrors.length > 0) {
        console.log(`\n⚠️  Console Errors on ${pageInfo.name}:`, consoleErrors.length);
      }

      if (jsErrors.length > 0) {
        console.log(`\n❌ JavaScript Errors on ${pageInfo.name}:`, jsErrors.length);
        jsErrors.forEach((err) => console.log(`  - ${err}`));
      }

      if (networkErrors.length > 0) {
        console.log(`\n⚠️  Network Errors on ${pageInfo.name}:`, networkErrors.length);
        // Filter out expected 401/403 for auth-required pages
        const unexpectedErrors = networkErrors.filter(
          (err) => !err.includes('401') && !err.includes('403')
        );
        if (unexpectedErrors.length > 0) {
          unexpectedErrors.forEach((err) => console.log(`  - ${err}`));
        }
      }

      // No critical JavaScript errors should occur
      expect(jsErrors.length).toBe(0);
    });
  }

  // Test CORS configuration
  test('Backend CORS Configuration', async ({ page }) => {
    // Navigate to the app first
    await page.goto(`${PRODUCTION_URL}/index.html`, { waitUntil: 'networkidle' });

    // Try to make a request to the backend
    const response = await page.evaluate(async (backendUrl) => {
      try {
        const res = await fetch(`${backendUrl}/health`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        return {
          ok: res.ok,
          status: res.status,
          data: await res.json(),
        };
      } catch (error) {
        return {
          ok: false,
          error: error instanceof Error ? error.message : String(error),
        };
      }
    }, BACKEND_URL);

    console.log('CORS Test Response:', response);
    expect(response.ok).toBeTruthy();
  });

  // Test static assets loading
  test('Static Assets Load Correctly', async ({ page }) => {
    await page.goto(`${PRODUCTION_URL}/index.html`, { waitUntil: 'networkidle' });

    // Check CSS is loaded
    const cssLinks = await page.locator('link[rel="stylesheet"]').count();
    expect(cssLinks).toBeGreaterThan(0);
    console.log(`✅ Found ${cssLinks} CSS files`);

    // Check JS is loaded
    const jsScripts = await page.locator('script[src]').count();
    expect(jsScripts).toBeGreaterThan(0);
    console.log(`✅ Found ${jsScripts} JS files`);

    // Verify cache headers
    const response = await page.goto(`${PRODUCTION_URL}/index.html`);
    const headers = response?.headers();

    console.log('\n--- HTML Cache Headers ---');
    console.log('cache-control:', headers?.['cache-control']);
    expect(headers?.['cache-control']).toContain('no-cache');
  });

  // Test navigation between pages
  test('Navigation Between Pages Works', async ({ page }) => {
    await page.goto(`${PRODUCTION_URL}/index.html`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Try to find and click navigation links
    const navLinks = await page.locator('nav a, [role="navigation"] a, .ant-menu-item').count();
    console.log(`\n✅ Found ${navLinks} navigation links`);

    if (navLinks > 0) {
      // Click first navigation link
      const firstLink = page.locator('nav a, [role="navigation"] a, .ant-menu-item').first();
      const linkText = await firstLink.textContent();
      console.log(`Clicking navigation: ${linkText}`);

      await firstLink.click();
      await page.waitForTimeout(1000);

      // Verify navigation occurred
      const url = page.url();
      console.log(`New URL: ${url}`);
      expect(url).toContain('#/');
    }
  });

  // Summary test - report all findings
  test('Test Summary and Report', async () => {
    console.log('\n=== Production Website Test Summary ===');
    console.log(`Total Pages Tested: ${PAGES.length}`);
    console.log(`Backend URL: ${BACKEND_URL}`);
    console.log(`Frontend URL: ${PRODUCTION_URL}`);
    console.log('=====================================\n');
  });
});
