/**
 * Worklist Page Performance Tests
 * Tests loading time and performance metrics after Codex CLI optimizations
 */

import { test, expect } from '@playwright/test';

const PRODUCTION_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

test.describe('Worklist Performance Tests', () => {
  test('should load worklist page within reasonable time', async ({ page }) => {
    // Start timer
    const startTime = Date.now();

    // Navigate to worklist (homepage)
    await page.goto(PRODUCTION_URL);

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');

    // Wait for worklist table or empty state to be visible
    const worklistVisible = page.locator('[data-testid="worklist-table"], .empty-state, table').first();
    await worklistVisible.waitFor({ state: 'visible', timeout: 10000 });

    // Calculate load time
    const loadTime = Date.now() - startTime;

    console.log(`\n📊 Performance Metrics:`);
    console.log(`   Total Page Load Time: ${loadTime}ms`);
    console.log(`   Target: < 3000ms`);
    console.log(`   Status: ${loadTime < 3000 ? '✅ PASS' : '❌ FAIL'}`);

    // Take screenshot
    await page.screenshot({
      path: 'screenshots/worklist-performance-loaded.png',
      fullPage: true
    });

    // Assert load time is reasonable (< 3 seconds)
    expect(loadTime).toBeLessThan(3000);
  });

  test('should measure API response time for worklist endpoint', async ({ page }) => {
    // Listen for API responses
    let apiResponseTime = 0;
    let apiFound = false;

    page.on('response', response => {
      if (response.url().includes('/v1/worklist') && !response.url().includes('statistics') && !response.url().includes('sync')) {
        apiFound = true;
        const timing = response.timing();
        apiResponseTime = timing.responseEnd;
        console.log(`\n🌐 API Response Details:`);
        console.log(`   URL: ${response.url()}`);
        console.log(`   Status: ${response.status()}`);
        console.log(`   Response Time: ${apiResponseTime}ms`);
      }
    });

    // Navigate to worklist
    await page.goto(PRODUCTION_URL);
    await page.waitForLoadState('networkidle');

    // Wait a bit for API call to complete
    await page.waitForTimeout(2000);

    if (apiFound) {
      console.log(`   Target: < 1000ms`);
      console.log(`   Status: ${apiResponseTime < 1000 ? '✅ PASS' : '❌ FAIL'}`);

      // Assert API response time is reasonable (< 1 second)
      expect(apiResponseTime).toBeLessThan(1000);
    } else {
      console.log(`\n⚠️  Warning: Worklist API call not detected`);
      console.log(`   This might indicate the page loaded from cache or no data exists`);
    }
  });

  test('should verify worklist loads with limit=25', async ({ page }) => {
    let requestUrl = '';
    let limitParam = '';

    // Intercept API requests
    page.on('request', request => {
      if (request.url().includes('/v1/worklist') && !request.url().includes('statistics') && !request.url().includes('sync')) {
        requestUrl = request.url();
        const url = new URL(requestUrl);
        limitParam = url.searchParams.get('limit') || 'not set';

        console.log(`\n📋 Worklist API Request:`);
        console.log(`   URL: ${requestUrl}`);
        console.log(`   Limit Parameter: ${limitParam}`);
      }
    });

    // Navigate to worklist
    await page.goto(PRODUCTION_URL);
    await page.waitForLoadState('networkidle');

    // Wait for API call
    await page.waitForTimeout(2000);

    if (requestUrl) {
      console.log(`   Expected: 25`);
      console.log(`   Status: ${limitParam === '25' ? '✅ PASS' : '❌ FAIL'}`);

      // Assert limit parameter is 25
      expect(limitParam).toBe('25');
    } else {
      console.log(`\n⚠️  Warning: Worklist API request not intercepted`);
    }
  });

  test('should measure Time to Interactive (TTI)', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(PRODUCTION_URL);

    // Wait for the page to be fully interactive
    await page.waitForLoadState('networkidle');

    // Wait for key interactive elements
    await page.waitForSelector('button', { timeout: 10000 });

    const tti = Date.now() - startTime;

    console.log(`\n⚡ Time to Interactive (TTI):`);
    console.log(`   TTI: ${tti}ms`);
    console.log(`   Target: < 4000ms`);
    console.log(`   Status: ${tti < 4000 ? '✅ PASS' : '❌ FAIL'}`);

    await page.screenshot({
      path: 'screenshots/worklist-tti.png',
      fullPage: true
    });

    expect(tti).toBeLessThan(4000);
  });

  test('should check worklist table renders correctly', async ({ page }) => {
    await page.goto(PRODUCTION_URL);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Take screenshot
    await page.screenshot({
      path: 'screenshots/worklist-table.png',
      fullPage: true
    });

    // Check if table or empty state is visible
    const hasTable = await page.locator('table').count() > 0;
    const hasEmptyState = await page.locator('text=/暂无文章|No Articles/i').count() > 0;

    console.log(`\n📊 Worklist Content:`);
    console.log(`   Has Table: ${hasTable ? 'Yes' : 'No'}`);
    console.log(`   Has Empty State: ${hasEmptyState ? 'Yes' : 'No'}`);
    console.log(`   Status: ${(hasTable || hasEmptyState) ? '✅ PASS' : '❌ FAIL'}`);

    // Either table or empty state should be visible
    expect(hasTable || hasEmptyState).toBeTruthy();
  });

  test('should benchmark page load performance', async ({ page }) => {
    const metrics: Record<string, number> = {};
    const startTime = Date.now();

    // Navigate to page
    await page.goto(PRODUCTION_URL);

    metrics['navigation'] = Date.now() - startTime;

    // Wait for DOM content loaded
    await page.waitForLoadState('domcontentloaded');
    metrics['domContentLoaded'] = Date.now() - startTime;

    // Wait for network idle
    await page.waitForLoadState('networkidle');
    metrics['networkIdle'] = Date.now() - startTime;

    // Get performance metrics from browser
    const performanceMetrics = await page.evaluate(() => {
      const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoadedTime: perfData.domContentLoadedEventEnd - perfData.fetchStart,
        loadTime: perfData.loadEventEnd - perfData.fetchStart,
        responseTime: perfData.responseEnd - perfData.requestStart,
      };
    });

    console.log(`\n📈 Performance Benchmark:`);
    console.log(`\n   Navigation Timing:`);
    console.log(`   - Navigation Start: ${metrics['navigation']}ms`);
    console.log(`   - DOM Content Loaded: ${metrics['domContentLoaded']}ms`);
    console.log(`   - Network Idle: ${metrics['networkIdle']}ms`);
    console.log(`\n   Browser Metrics:`);
    console.log(`   - DOM Load Time: ${performanceMetrics.domContentLoadedTime.toFixed(2)}ms`);
    console.log(`   - Total Load Time: ${performanceMetrics.loadTime.toFixed(2)}ms`);
    console.log(`   - Server Response Time: ${performanceMetrics.responseTime.toFixed(2)}ms`);

    // Take final screenshot
    await page.screenshot({
      path: 'screenshots/worklist-benchmark.png',
      fullPage: true
    });

    // Assert total load time is reasonable
    expect(performanceMetrics.loadTime).toBeLessThan(5000);
  });
});
