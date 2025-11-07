import { test, expect } from '@playwright/test';

const PROD_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323';

test.describe('Verify Performance Fix', () => {
  test('Settings page should load quickly without 404 errors', async ({ page }) => {
    const apiRequests: { url: string; status: number; duration: number }[] = [];
    const failedRequests: string[] = [];

    // Track API requests
    page.on('response', async (response) => {
      const url = response.url();
      const timing = response.timing();

      if (url.includes('/v1/')) {
        apiRequests.push({
          url,
          status: response.status(),
          duration: timing.responseEnd,
        });
      }
    });

    page.on('requestfailed', (request) => {
      failedRequests.push(request.url());
    });

    const startTime = Date.now();

    console.log('\\n🔍 Loading Settings page...');
    await page.goto(`${PROD_URL}/index.html#/settings`, {
      waitUntil: 'networkidle',
      timeout: 15000,
    });

    const loadTime = Date.now() - startTime;

    // Wait for rendering
    await page.waitForTimeout(2000);

    console.log(`\\n⏱️  Total load time: ${loadTime}ms`);

    // Log API requests
    console.log('\\n📡 API Requests:');
    apiRequests.forEach((req) => {
      const statusIcon = req.status >= 200 && req.status < 300 ? '✅' : '❌';
      console.log(`  ${statusIcon} ${req.status} - ${req.duration.toFixed(0)}ms - ${req.url}`);
    });

    // Check for 404 errors on proofreading endpoints
    const proofreading404s = apiRequests.filter(
      (r) => r.status === 404 && r.url.includes('/proofreading/')
    );

    if (proofreading404s.length > 0) {
      console.error('\\n❌ Still seeing proofreading 404 errors:');
      proofreading404s.forEach((r) => console.error(`  ${r.url}`));
    } else {
      console.log('\\n✅ No proofreading 404 errors detected');
    }

    // Check for failed requests
    if (failedRequests.length > 0) {
      console.log('\\n⚠️  Failed requests:');
      failedRequests.forEach((url) => console.log(`  - ${url}`));
    }

    // Performance assertions
    console.log('\\n📊 Performance Check:');
    console.log(`  Load time: ${loadTime}ms`);
    console.log(`  Target: <3000ms`);
    console.log(`  Status: ${loadTime < 3000 ? '✅ PASS' : '❌ FAIL'}`);

    // Assertions
    expect(proofreading404s.length).toBe(0);
    expect(loadTime).toBeLessThan(3000); // Should load within 3 seconds
  });

  test('Homepage should load quickly', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(`${PROD_URL}/index.html`, {
      waitUntil: 'networkidle',
      timeout: 10000,
    });

    const loadTime = Date.now() - startTime;

    console.log(`\\n⏱️  Homepage load time: ${loadTime}ms`);
    console.log(`  Target: <2000ms`);
    console.log(`  Status: ${loadTime < 2000 ? '✅ PASS' : '❌ FAIL'}`);

    expect(loadTime).toBeLessThan(2000);
  });

  test('Worklist page should load quickly', async ({ page }) => {
    const apiRequests: { url: string; status: number; duration: number }[] = [];

    page.on('response', async (response) => {
      const url = response.url();
      const timing = response.timing();

      if (url.includes('/v1/')) {
        apiRequests.push({
          url,
          status: response.status(),
          duration: timing.responseEnd,
        });
      }
    });

    const startTime = Date.now();

    await page.goto(`${PROD_URL}/index.html#/worklist`, {
      waitUntil: 'networkidle',
      timeout: 15000,
    });

    const loadTime = Date.now() - startTime;

    console.log(`\\n⏱️  Worklist load time: ${loadTime}ms`);
    console.log(`  Target: <3000ms`);
    console.log(`  Status: ${loadTime < 3000 ? '✅ PASS' : '❌ FAIL'}`);

    // Check API performance
    const slowAPIs = apiRequests.filter((r) => r.duration > 2000);
    if (slowAPIs.length > 0) {
      console.log('\\n⚠️  Slow API calls:');
      slowAPIs.forEach((r) => {
        console.log(`  ${r.duration.toFixed(0)}ms - ${r.url}`);
      });
    }

    expect(loadTime).toBeLessThan(3000);
  });
});
