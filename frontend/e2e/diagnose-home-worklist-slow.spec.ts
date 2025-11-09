import { test, expect } from '@playwright/test';

const FRONTEND_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323';
const BACKEND_URL = 'https://cms-automation-backend-baau2zqeqq-ue.a.run.app';

test.describe('Home and Worklist Loading Diagnostics', () => {
  test('diagnose home page loading performance', async ({ page }) => {
    const apiCalls: Array<{
      url: string;
      method: string;
      status: number;
      duration: number;
      responseSize: number;
    }> = [];

    // Monitor all network requests
    page.on('response', async (response) => {
      const request = response.request();
      const url = request.url();

      // Track API calls
      if (url.includes('/v1/') || url.includes('/api/v1/')) {
        const timing = response.timing();
        apiCalls.push({
          url,
          method: request.method(),
          status: response.status(),
          duration: timing.responseEnd,
          responseSize: parseInt(response.headers()['content-length'] || '0', 10),
        });
      }
    });

    console.log('\n=== 🏠 HOME PAGE LOADING DIAGNOSTICS ===\n');

    const startTime = Date.now();

    // Navigate to home page
    await page.goto(FRONTEND_URL, {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    const loadTime = Date.now() - startTime;

    console.log(`⏱️  Total load time: ${loadTime}ms\n`);

    // Wait a bit for any delayed requests
    await page.waitForTimeout(3000);

    // Analyze API calls
    console.log(`📊 Total API calls: ${apiCalls.length}\n`);

    if (apiCalls.length === 0) {
      console.log('⚠️  WARNING: No API calls detected!\n');
    } else {
      // Group by status code
      const byStatus = apiCalls.reduce((acc, call) => {
        const key = call.status.toString();
        if (!acc[key]) acc[key] = [];
        acc[key].push(call);
        return acc;
      }, {} as Record<string, typeof apiCalls>);

      console.log('📈 API Calls by Status:\n');
      Object.keys(byStatus).sort().forEach(status => {
        const calls = byStatus[status];
        const emoji = status.startsWith('2') ? '✅' : status.startsWith('4') ? '❌' : '⚠️';
        console.log(`${emoji} ${status}: ${calls.length} calls`);
        calls.forEach(call => {
          const path = call.url.replace(BACKEND_URL, '').replace(FRONTEND_URL, '');
          console.log(`   ${call.method} ${path} (${call.duration.toFixed(0)}ms)`);
        });
        console.log('');
      });

      // Show slow API calls (>2s)
      const slowCalls = apiCalls.filter(c => c.duration > 2000);
      if (slowCalls.length > 0) {
        console.log('🐌 Slow API calls (>2s):\n');
        slowCalls.forEach(call => {
          const path = call.url.replace(BACKEND_URL, '').replace(FRONTEND_URL, '');
          console.log(`   ${call.method} ${path} - ${call.duration.toFixed(0)}ms`);
        });
        console.log('');
      }

      // Show failed calls
      const failedCalls = apiCalls.filter(c => c.status >= 400);
      if (failedCalls.length > 0) {
        console.log('❌ Failed API calls:\n');
        failedCalls.forEach(call => {
          const path = call.url.replace(BACKEND_URL, '').replace(FRONTEND_URL, '');
          console.log(`   ${call.status} ${call.method} ${path}`);
        });
        console.log('');
      }
    }

    // Check if page loaded correctly
    const bodyText = await page.textContent('body');
    if (!bodyText || bodyText.length < 100) {
      console.log('⚠️  WARNING: Page body seems empty or very small!\n');
    }

    // Take screenshot
    await page.screenshot({ path: 'debug-home-full.png', fullPage: true });
    console.log('📸 Screenshot saved: debug-home-full.png\n');
  });

  test('diagnose worklist page loading', async ({ page }) => {
    const apiCalls: Array<{
      url: string;
      method: string;
      status: number;
      duration: number;
    }> = [];

    page.on('response', async (response) => {
      const request = response.request();
      const url = request.url();

      if (url.includes('/v1/') || url.includes('/api/v1/')) {
        const timing = response.timing();
        apiCalls.push({
          url,
          method: request.method(),
          status: response.status(),
          duration: timing.responseEnd,
        });
      }
    });

    console.log('\n=== 📋 WORKLIST PAGE LOADING DIAGNOSTICS ===\n');

    const startTime = Date.now();

    // Navigate to worklist
    await page.goto(`${FRONTEND_URL}/#/worklist`, {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    const loadTime = Date.now() - startTime;

    console.log(`⏱️  Total load time: ${loadTime}ms\n`);

    // Wait for potential delayed requests
    await page.waitForTimeout(5000);

    console.log(`📊 Total API calls: ${apiCalls.length}\n`);

    if (apiCalls.length === 0) {
      console.log('⚠️  WARNING: No API calls detected for worklist!\n');
    } else {
      // Analyze calls
      const byStatus = apiCalls.reduce((acc, call) => {
        const key = call.status.toString();
        if (!acc[key]) acc[key] = [];
        acc[key].push(call);
        return acc;
      }, {} as Record<string, typeof apiCalls>);

      console.log('📈 API Calls by Status:\n');
      Object.keys(byStatus).sort().forEach(status => {
        const calls = byStatus[status];
        const emoji = status.startsWith('2') ? '✅' : status.startsWith('4') ? '❌' : '⚠️';
        console.log(`${emoji} ${status}: ${calls.length} calls`);
        calls.forEach(call => {
          const path = call.url.replace(BACKEND_URL, '').replace(FRONTEND_URL, '');
          console.log(`   ${call.method} ${path} (${call.duration.toFixed(0)}ms)`);
        });
        console.log('');
      });

      // Check for worklist-specific calls
      const worklistCalls = apiCalls.filter(c => c.url.includes('/worklist'));
      console.log(`📋 Worklist-specific API calls: ${worklistCalls.length}\n`);

      if (worklistCalls.length === 0) {
        console.log('⚠️  WARNING: No /worklist API calls found!\n');
        console.log('All API calls made:');
        apiCalls.forEach(call => {
          console.log(`   ${call.method} ${call.url}`);
        });
        console.log('');
      }

      // Check for failed worklist calls
      const failedWorklistCalls = worklistCalls.filter(c => c.status >= 400);
      if (failedWorklistCalls.length > 0) {
        console.log('❌ Failed worklist API calls:\n');
        failedWorklistCalls.forEach(call => {
          console.log(`   ${call.status} ${call.method} ${call.url.replace(BACKEND_URL, '')}`);
        });
        console.log('');
      }
    }

    // Check page content
    const pageText = await page.textContent('body');
    console.log(`📝 Page text length: ${pageText?.length || 0} characters\n`);

    // Check for error messages
    const errorElements = await page.locator('text=/error|failed|not found/i').count();
    if (errorElements > 0) {
      console.log(`⚠️  Found ${errorElements} potential error messages on page\n`);
    }

    // Check for loading indicators
    const loadingElements = await page.locator('text=/loading|加载/i').count();
    console.log(`🔄 Loading indicators visible: ${loadingElements}\n`);

    // Take screenshots
    await page.screenshot({ path: 'debug-worklist-full.png', fullPage: true });
    console.log('📸 Screenshot saved: debug-worklist-full.png\n');
  });

  test('check all critical API endpoints', async ({ page }) => {
    console.log('\n=== 🔍 CHECKING CRITICAL API ENDPOINTS ===\n');

    const endpoints = [
      { path: '/v1/worklist', method: 'GET', critical: true },
      { path: '/v1/worklist/statistics', method: 'GET', critical: true },
      { path: '/v1/settings', method: 'GET', critical: true },
      { path: '/v1/analytics/storage-usage', method: 'GET', critical: false },
      { path: '/api/v1/proofreading/decisions/rules/published', method: 'GET', critical: false },
    ];

    for (const endpoint of endpoints) {
      try {
        const url = `${BACKEND_URL}${endpoint.path}`;
        console.log(`Testing ${endpoint.method} ${endpoint.path}...`);

        const response = await page.request.get(url, {
          timeout: 10000,
        });

        const emoji = response.status() === 200 ? '✅' :
                     response.status() === 401 ? '🔐' :
                     response.status() === 404 ? '❌' : '⚠️';

        console.log(`${emoji} Status: ${response.status()}`);

        if (response.status() !== 200 && endpoint.critical) {
          console.log(`⚠️  CRITICAL ENDPOINT FAILED!\n`);
        }
      } catch (error) {
        console.log(`❌ Request failed: ${error}\n`);
        if (endpoint.critical) {
          console.log(`🚨 CRITICAL ENDPOINT UNREACHABLE!\n`);
        }
      }
    }
  });
});
