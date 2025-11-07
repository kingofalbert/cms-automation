import { test, expect } from '@playwright/test';

const PROD_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323';

test.describe('Diagnose Slow Loading Issue', () => {
  test('Analyze homepage loading performance', async ({ page }) => {
    const metrics: {
      url: string;
      duration: number;
      status: number;
      size: number;
    }[] = [];

    const slowRequests: typeof metrics = [];
    const failedRequests: { url: string; error: string }[] = [];

    // Track all network requests
    page.on('response', async (response) => {
      const request = response.request();
      const timing = response.timing();
      const url = response.url();

      const metric = {
        url,
        duration: timing.responseEnd,
        status: response.status(),
        size: (await response.body().catch(() => Buffer.from(''))).length,
      };

      metrics.push(metric);

      // Track slow requests (> 1s)
      if (timing.responseEnd > 1000) {
        slowRequests.push(metric);
      }
    });

    page.on('requestfailed', (request) => {
      failedRequests.push({
        url: request.url(),
        error: request.failure()?.errorText || 'Unknown error',
      });
    });

    const startTime = Date.now();

    console.log('\\n🔍 Loading homepage...');
    await page.goto(`${PROD_URL}/index.html`, {
      waitUntil: 'networkidle',
      timeout: 60000,
    });

    const loadTime = Date.now() - startTime;
    console.log(`⏱️  Total load time: ${loadTime}ms`);

    // Wait a bit more for any async operations
    await page.waitForTimeout(2000);

    // Log statistics
    console.log('\\n📊 Network Statistics:');
    console.log(`  Total requests: ${metrics.length}`);
    console.log(`  Slow requests (>1s): ${slowRequests.length}`);
    console.log(`  Failed requests: ${failedRequests.length}`);

    // Show slowest requests
    if (slowRequests.length > 0) {
      console.log('\\n🐌 Slowest requests:');
      slowRequests
        .sort((a, b) => b.duration - a.duration)
        .slice(0, 10)
        .forEach((req) => {
          console.log(`  ${req.duration.toFixed(0)}ms - ${req.status} - ${(req.size / 1024).toFixed(1)}KB - ${req.url}`);
        });
    }

    // Show failed requests
    if (failedRequests.length > 0) {
      console.log('\\n❌ Failed requests:');
      failedRequests.forEach((req) => {
        console.log(`  ${req.error} - ${req.url}`);
      });
    }

    // Group by domain
    const byDomain = metrics.reduce((acc, m) => {
      try {
        const domain = new URL(m.url).hostname;
        if (!acc[domain]) {
          acc[domain] = { count: 0, totalTime: 0, totalSize: 0 };
        }
        acc[domain].count++;
        acc[domain].totalTime += m.duration;
        acc[domain].totalSize += m.size;
      } catch (e) {
        // Skip invalid URLs
      }
      return acc;
    }, {} as Record<string, { count: number; totalTime: number; totalSize: number }>);

    console.log('\\n🌐 By domain:');
    Object.entries(byDomain)
      .sort((a, b) => b[1].totalTime - a[1].totalTime)
      .forEach(([domain, stats]) => {
        console.log(`  ${domain}:`);
        console.log(`    Requests: ${stats.count}`);
        console.log(`    Total time: ${stats.totalTime.toFixed(0)}ms`);
        console.log(`    Total size: ${(stats.totalSize / 1024).toFixed(1)}KB`);
        console.log(`    Avg time: ${(stats.totalTime / stats.count).toFixed(0)}ms`);
      });
  });

  test('Analyze Settings page loading performance', async ({ page }) => {
    const metrics: {
      url: string;
      duration: number;
      status: number;
    }[] = [];

    const apiRequests: typeof metrics = [];

    page.on('response', async (response) => {
      const timing = response.timing();
      const url = response.url();

      const metric = {
        url,
        duration: timing.responseEnd,
        status: response.status(),
      };

      metrics.push(metric);

      // Track API requests
      if (url.includes('/v1/')) {
        apiRequests.push(metric);
      }
    });

    const startTime = Date.now();

    console.log('\\n🔍 Loading Settings page...');
    await page.goto(`${PROD_URL}/index.html#/settings`, {
      waitUntil: 'networkidle',
      timeout: 60000,
    });

    const loadTime = Date.now() - startTime;
    console.log(`⏱️  Total load time: ${loadTime}ms`);

    await page.waitForTimeout(3000);

    console.log('\\n📡 API Requests:');
    console.log(`  Total API requests: ${apiRequests.length}`);

    apiRequests
      .sort((a, b) => b.duration - a.duration)
      .forEach((req) => {
        const statusIcon = req.status >= 200 && req.status < 300 ? '✅' : '❌';
        console.log(`  ${statusIcon} ${req.status} - ${req.duration.toFixed(0)}ms - ${req.url}`);
      });

    // Check for blocking requests
    const blockingRequests = apiRequests.filter(r => r.duration > 2000);
    if (blockingRequests.length > 0) {
      console.log('\\n⚠️  Blocking API requests (>2s):');
      blockingRequests.forEach((req) => {
        console.log(`  ${req.duration.toFixed(0)}ms - ${req.url}`);
      });
    }
  });

  test('Analyze Worklist page loading performance', async ({ page }) => {
    const apiRequests: {
      url: string;
      duration: number;
      status: number;
    }[] = [];

    page.on('response', async (response) => {
      const timing = response.timing();
      const url = response.url();

      if (url.includes('/v1/')) {
        apiRequests.push({
          url,
          duration: timing.responseEnd,
          status: response.status(),
        });
      }
    });

    const startTime = Date.now();

    console.log('\\n🔍 Loading Worklist page...');
    await page.goto(`${PROD_URL}/index.html#/worklist`, {
      waitUntil: 'networkidle',
      timeout: 60000,
    });

    const loadTime = Date.now() - startTime;
    console.log(`⏱️  Total load time: ${loadTime}ms`);

    await page.waitForTimeout(3000);

    console.log('\\n📡 API Requests:');
    apiRequests.forEach((req) => {
      const statusIcon = req.status >= 200 && req.status < 300 ? '✅' : '❌';
      console.log(`  ${statusIcon} ${req.status} - ${req.duration.toFixed(0)}ms - ${req.url}`);
    });
  });
});
