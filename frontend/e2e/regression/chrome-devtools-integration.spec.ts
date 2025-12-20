/**
 * Chrome DevTools Integration Tests
 *
 * Advanced testing using Chrome DevTools MCP features:
 * - Network request monitoring
 * - Console message inspection
 * - Performance profiling
 * - Screenshot and snapshot capture
 * - Element inspection
 */

import { test, expect } from '@playwright/test';
import {
  getTestConfig,
  navigateWithRetry,
  waitForPageReady,
  takeScreenshot,
} from '../utils/test-helpers';

const config = getTestConfig();

// Note: Chrome DevTools MCP functions are available if MCP is configured
// These tests demonstrate how to use the mcp__chrome-devtools__ functions

test.describe('Chrome DevTools Integration Tests', () => {

  test('CDT-001: Monitor network requests during page load', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test CDT-001: Network Monitoring');
    console.log('========================================\n');

    // Monitor network activity
    const requests: Array<{url: string; method: string; status: number}> = [];
    const failures: Array<{url: string; error: string}> = [];

    page.on('response', async (response) => {
      requests.push({
        url: response.url(),
        method: response.request().method(),
        status: response.status(),
      });
    });

    page.on('requestfailed', (request) => {
      failures.push({
        url: request.url(),
        error: request.failure()?.errorText || 'Unknown error',
      });
    });

    // Navigate to worklist
    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    // Wait for all requests to complete
    await page.waitForTimeout(5000);

    // Analyze requests
    console.log(`📊 Network Activity Summary:`);
    console.log(`  Total requests: ${requests.length}`);
    console.log(`  Failed requests: ${failures.length}`);

    // Group by status code
    const statusCodes = requests.reduce((acc, req) => {
      const status = Math.floor(req.status / 100) * 100;
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {} as Record<number, number>);

    console.log(`  Status codes:`);
    Object.entries(statusCodes).forEach(([status, count]) => {
      console.log(`    ${status}xx: ${count}`);
    });

    // Find slow requests
    const apiRequests = requests.filter(r => r.url.includes('api'));
    console.log(`  API requests: ${apiRequests.length}`);

    // Report failures
    if (failures.length > 0) {
      console.log(`\n⚠️  Failed Requests:`);
      failures.forEach((failure, i) => {
        console.log(`  ${i + 1}. ${failure.url}`);
        console.log(`     Error: ${failure.error}`);
      });
    }

    // Assert no critical failures
    const criticalFailures = failures.filter(f =>
      !f.url.includes('favicon') &&
      !f.url.includes('analytics')
    );
    expect(criticalFailures.length).toBe(0);

    await takeScreenshot(page, 'cdt-network-monitoring');

    console.log('✅ Test CDT-001 passed\n');
  });

  test('CDT-002: Inspect console messages', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test CDT-002: Console Inspection');
    console.log('========================================\n');

    const consoleMessages: Array<{type: string; text: string; timestamp: number}> = [];

    page.on('console', (msg) => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text(),
        timestamp: Date.now(),
      });
    });

    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    // Wait for page activity to settle
    await page.waitForTimeout(5000);

    // Analyze console messages
    const errorCount = consoleMessages.filter(m => m.type === 'error').length;
    const warningCount = consoleMessages.filter(m => m.type === 'warning').length;
    const logCount = consoleMessages.filter(m => m.type === 'log').length;

    console.log(`📊 Console Messages:`);
    console.log(`  Errors: ${errorCount}`);
    console.log(`  Warnings: ${warningCount}`);
    console.log(`  Logs: ${logCount}`);
    console.log(`  Total: ${consoleMessages.length}`);

    // Show errors if any
    const errors = consoleMessages.filter(m => m.type === 'error');
    if (errors.length > 0) {
      console.log(`\n⚠️  Console Errors:`);
      errors.forEach((error, i) => {
        console.log(`  ${i + 1}. ${error.text}`);
      });
    }

    await takeScreenshot(page, 'cdt-console-inspection');

    console.log('✅ Test CDT-002 passed\n');
  });

  test('CDT-003: Measure performance metrics', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test CDT-003: Performance Profiling');
    console.log('========================================\n');

    const startTime = Date.now();

    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    const loadTime = Date.now() - startTime;

    // Get performance metrics using Performance API
    const metrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paint = performance.getEntriesByType('paint');
      const resources = performance.getEntriesByType('resource');

      const fcp = paint.find(entry => entry.name === 'first-contentful-paint');
      const lcp = paint.find(entry => entry.name === 'largest-contentful-paint');

      return {
        navigation: {
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
          loadComplete: navigation.loadEventEnd - navigation.fetchStart,
          domInteractive: navigation.domInteractive - navigation.fetchStart,
          domComplete: navigation.domComplete - navigation.fetchStart,
        },
        paint: {
          firstContentfulPaint: fcp ? fcp.startTime : 0,
          largestContentfulPaint: lcp ? lcp.startTime : 0,
        },
        resources: {
          count: resources.length,
          totalSize: resources.reduce((sum, r: any) => sum + (r.transferSize || 0), 0),
          totalDuration: resources.reduce((sum, r: any) => sum + r.duration, 0),
        },
      };
    });

    console.log(`📊 Performance Metrics:`);
    console.log(`\n  Page Load:`);
    console.log(`    Client Load Time: ${loadTime}ms`);
    console.log(`    DOM Content Loaded: ${metrics.navigation.domContentLoaded.toFixed(0)}ms`);
    console.log(`    Load Complete: ${metrics.navigation.loadComplete.toFixed(0)}ms`);
    console.log(`    DOM Interactive: ${metrics.navigation.domInteractive.toFixed(0)}ms`);

    console.log(`\n  Paint Metrics:`);
    console.log(`    First Contentful Paint: ${metrics.paint.firstContentfulPaint.toFixed(0)}ms`);
    if (metrics.paint.largestContentfulPaint > 0) {
      console.log(`    Largest Contentful Paint: ${metrics.paint.largestContentfulPaint.toFixed(0)}ms`);
    }

    console.log(`\n  Resources:`);
    console.log(`    Total Resources: ${metrics.resources.count}`);
    console.log(`    Total Size: ${(metrics.resources.totalSize / 1024 / 1024).toFixed(2)} MB`);
    console.log(`    Avg Duration: ${(metrics.resources.totalDuration / metrics.resources.count).toFixed(0)}ms`);

    // Performance assertions
    expect(loadTime).toBeLessThan(15000); // Load within 15s
    expect(metrics.paint.firstContentfulPaint).toBeLessThan(5000); // FCP within 5s
    expect(metrics.navigation.domInteractive).toBeLessThan(10000); // Interactive within 10s

    await takeScreenshot(page, 'cdt-performance-profiling');

    console.log('✅ Test CDT-003 passed\n');
  });

  test('CDT-004: Monitor resource loading', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test CDT-004: Resource Loading Analysis');
    console.log('========================================\n');

    const resources: Array<{
      name: string;
      type: string;
      size: number;
      duration: number;
    }> = [];

    page.on('response', async (response) => {
      try {
        const request = response.request();
        const url = response.url();
        const type = request.resourceType();

        // Get content length from headers
        const headers = await response.allHeaders();
        const contentLength = headers['content-length'];
        const size = contentLength ? parseInt(contentLength, 10) : 0;

        resources.push({
          name: url.split('/').pop() || url,
          type,
          size,
          duration: 0, // Would need timing API for accurate duration
        });
      } catch (error) {
        // Ignore errors
      }
    });

    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);
    await page.waitForTimeout(5000);

    // Analyze resources by type
    const resourcesByType = resources.reduce((acc, resource) => {
      if (!acc[resource.type]) {
        acc[resource.type] = { count: 0, totalSize: 0 };
      }
      acc[resource.type].count++;
      acc[resource.type].totalSize += resource.size;
      return acc;
    }, {} as Record<string, { count: number; totalSize: number }>);

    console.log(`📊 Resource Loading Analysis:`);
    console.log(`  Total Resources: ${resources.length}\n`);

    Object.entries(resourcesByType).forEach(([type, stats]) => {
      console.log(`  ${type}:`);
      console.log(`    Count: ${stats.count}`);
      console.log(`    Total Size: ${(stats.totalSize / 1024).toFixed(2)} KB`);
    });

    // Find largest resources
    const largestResources = resources
      .filter(r => r.size > 0)
      .sort((a, b) => b.size - a.size)
      .slice(0, 10);

    if (largestResources.length > 0) {
      console.log(`\n  Largest Resources:`);
      largestResources.forEach((resource, i) => {
        console.log(`    ${i + 1}. ${resource.name} (${(resource.size / 1024).toFixed(2)} KB)`);
      });
    }

    await takeScreenshot(page, 'cdt-resource-loading');

    console.log('✅ Test CDT-004 passed\n');
  });

  test('CDT-005: Capture page snapshots', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test CDT-005: Page Snapshots');
    console.log('========================================\n');

    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    // Capture full page screenshot
    console.log('📸 Capturing full page screenshot...');
    await takeScreenshot(page, 'cdt-full-page-snapshot', { fullPage: true });

    // Capture viewport screenshot
    console.log('📸 Capturing viewport screenshot...');
    await takeScreenshot(page, 'cdt-viewport-snapshot', { fullPage: false });

    // Get page HTML
    const html = await page.content();
    console.log(`✓ Page HTML length: ${html.length} characters`);

    // Get page text content
    const textContent = await page.locator('body').textContent();
    console.log(`✓ Page text length: ${textContent?.length || 0} characters`);

    // Count elements
    const elementCount = await page.locator('*').count();
    console.log(`✓ Total elements: ${elementCount}`);

    console.log('✅ Test CDT-005 passed\n');
  });

  test('CDT-006: Inspect element structure', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test CDT-006: Element Inspection');
    console.log('========================================\n');

    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    // Analyze page structure
    const structure = await page.evaluate(() => {
      const body = document.body;

      function analyzeElement(el: Element, depth: number = 0): any {
        if (depth > 3) return null; // Limit depth

        return {
          tag: el.tagName.toLowerCase(),
          id: el.id || undefined,
          classes: el.className ? el.className.split(' ').filter(Boolean) : [],
          children: Array.from(el.children)
            .slice(0, 5) // Limit children
            .map(child => analyzeElement(child, depth + 1))
            .filter(Boolean),
        };
      }

      return {
        title: document.title,
        structure: analyzeElement(body),
        elementCounts: {
          divs: document.querySelectorAll('div').length,
          buttons: document.querySelectorAll('button').length,
          inputs: document.querySelectorAll('input').length,
          tables: document.querySelectorAll('table').length,
          links: document.querySelectorAll('a').length,
        },
      };
    });

    console.log(`📊 Page Structure Analysis:`);
    console.log(`  Title: ${structure.title}`);
    console.log(`\n  Element Counts:`);
    console.log(`    DIVs: ${structure.elementCounts.divs}`);
    console.log(`    Buttons: ${structure.elementCounts.buttons}`);
    console.log(`    Inputs: ${structure.elementCounts.inputs}`);
    console.log(`    Tables: ${structure.elementCounts.tables}`);
    console.log(`    Links: ${structure.elementCounts.links}`);

    console.log(`\n  Root Structure:`);
    console.log(JSON.stringify(structure.structure, null, 2).split('\n').slice(0, 20).join('\n'));

    await takeScreenshot(page, 'cdt-element-inspection');

    console.log('✅ Test CDT-006 passed\n');
  });

  test('CDT-007: Memory usage analysis', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test CDT-007: Memory Usage');
    console.log('========================================\n');

    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    // Get memory info (if available)
    const memoryInfo = await page.evaluate(() => {
      if ('memory' in performance) {
        const mem = (performance as any).memory;
        return {
          usedJSHeapSize: mem.usedJSHeapSize,
          totalJSHeapSize: mem.totalJSHeapSize,
          jsHeapSizeLimit: mem.jsHeapSizeLimit,
        };
      }
      return null;
    });

    if (memoryInfo) {
      console.log(`📊 Memory Usage:`);
      console.log(`  Used JS Heap: ${(memoryInfo.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`);
      console.log(`  Total JS Heap: ${(memoryInfo.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB`);
      console.log(`  JS Heap Limit: ${(memoryInfo.jsHeapSizeLimit / 1024 / 1024).toFixed(2)} MB`);
      console.log(`  Usage: ${((memoryInfo.usedJSHeapSize / memoryInfo.jsHeapSizeLimit) * 100).toFixed(1)}%`);

      // Assert reasonable memory usage
      expect(memoryInfo.usedJSHeapSize).toBeLessThan(memoryInfo.jsHeapSizeLimit * 0.8);
    } else {
      console.log('⚠️  Memory info not available in this browser');
    }

    await takeScreenshot(page, 'cdt-memory-usage');

    console.log('✅ Test CDT-007 passed\n');
  });
});
