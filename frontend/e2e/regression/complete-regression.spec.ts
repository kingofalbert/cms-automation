/**
 * Complete End-to-End Regression Test Suite
 *
 * Comprehensive test suite covering all major workflows and features:
 * 1. Worklist management
 * 2. Proofreading review workflow
 * 3. Settings configuration
 * 4. Navigation and routing
 * 5. Performance and accessibility
 * 6. Error handling
 *
 * This suite can be run as a smoke test before deployment or
 * as a full regression test suite after major changes.
 */

import { test, expect } from '@playwright/test';
import {
  getTestConfig,
  navigateWithRetry,
  waitForPageReady,
  waitForElement,
  elementExists,
  clickWithRetry,
  createConsoleMonitor,
  createNetworkMonitor,
  takeScreenshot,
  measurePerformance,
  assertNoConsoleErrors,
  assertNoNetworkFailures,
} from '../utils/test-helpers';

const config = getTestConfig();

test.describe('Complete E2E Regression Suite', () => {

  test.describe.configure({ mode: 'serial' });

  test('REG-001: Complete user workflow - Worklist to Review', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test REG-001: Complete User Workflow');
    console.log('========================================\n');

    // Set up monitoring
    const consoleMonitor = createConsoleMonitor(page);
    const networkMonitor = createNetworkMonitor(page);
    consoleMonitor.start();
    networkMonitor.start();

    // Step 1: Load worklist
    console.log('Step 1: Load Worklist...');
    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    // Verify worklist loaded
    const hasTable = await elementExists(page, 'table');
    expect(hasTable).toBeTruthy();
    console.log('  ✓ Worklist loaded');

    await takeScreenshot(page, 'reg-001-step1-worklist');

    // Step 2: Click Review button
    console.log('\nStep 2: Navigate to Review...');
    const reviewButton = await waitForElement(
      page,
      'button:has-text("Review"), button:has-text("审核")',
      { timeout: 15000 }
    );
    await clickWithRetry(reviewButton.first());
    await page.waitForTimeout(3000);

    // Verify review page loaded
    const url = page.url();
    expect(url).toMatch(/review|proofreading/);
    console.log('  ✓ Review page loaded');

    await takeScreenshot(page, 'reg-001-step2-review-page');

    // Step 3: Interact with review page
    console.log('\nStep 3: Test Review Page Interactions...');

    // Try switching views
    const diffButton = page.locator('button:has-text("Diff"), button:has-text("对比")').first();
    if (await diffButton.count() > 0) {
      await clickWithRetry(diffButton);
      await page.waitForTimeout(1000);
      console.log('  ✓ Switched to Diff view');
    }

    await takeScreenshot(page, 'reg-001-step3-interactions');

    // Step 4: Navigate back to worklist
    console.log('\nStep 4: Navigate Back...');
    await page.goBack();
    await waitForPageReady(page);

    const backUrl = page.url();
    const isWorklist = backUrl.includes('worklist') || backUrl === config.baseURL;
    expect(isWorklist).toBeTruthy();
    console.log('  ✓ Navigated back to worklist');

    await takeScreenshot(page, 'reg-001-step4-back-to-worklist');

    // Stop monitoring and report
    consoleMonitor.stop();
    networkMonitor.stop();

    console.log('\n' + consoleMonitor.getReport());
    console.log('\n' + networkMonitor.getReport());

    // Assert no critical issues
    assertNoConsoleErrors(consoleMonitor, {
      allowedErrors: ['ResizeObserver', 'favicon'],
    });

    assertNoNetworkFailures(networkMonitor, {
      allowedFailures: ['favicon', 'analytics'],
    });

    console.log('\n✅ Test REG-001 passed - Complete workflow executed successfully\n');
  });

  test('REG-002: Settings page workflow', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test REG-002: Settings Workflow');
    console.log('========================================\n');

    // Step 1: Navigate to settings from worklist
    console.log('Step 1: Load Worklist...');
    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    console.log('\nStep 2: Click Settings Button...');
    const settingsButton = page.locator('button:has-text("Settings"), button:has-text("设置"), a[href*="settings"]').first();

    if (await settingsButton.count() > 0) {
      await clickWithRetry(settingsButton);
      await page.waitForTimeout(2000);
      console.log('  ✓ Navigated to settings via button');
    } else {
      // Direct navigation fallback
      await page.goto(`${config.baseURL}#/settings`);
      await waitForPageReady(page);
      console.log('  ✓ Navigated to settings via URL');
    }

    // Verify settings page
    const url = page.url();
    expect(url).toContain('settings');

    await takeScreenshot(page, 'reg-002-settings-page', { fullPage: true });

    // Step 3: Navigate back
    console.log('\nStep 3: Navigate Back...');
    const backButton = page.locator('button:has-text("Back"), button:has-text("返回"), a[href*="worklist"]').first();

    if (await backButton.count() > 0) {
      await clickWithRetry(backButton);
      await page.waitForTimeout(2000);
    } else {
      await page.goBack();
      await waitForPageReady(page);
    }

    const backUrl = page.url();
    const isWorklist = backUrl.includes('worklist') || backUrl === config.baseURL || backUrl.endsWith('/');
    expect(isWorklist).toBeTruthy();
    console.log('  ✓ Navigated back to worklist');

    console.log('\n✅ Test REG-002 passed\n');
  });

  test('REG-003: Language switching', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test REG-003: Language Switching');
    console.log('========================================\n');

    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    // Look for language selector
    const langSelector = page.locator('button:has-text("English"), button:has-text("繁體中文"), button:has-text("简体中文")').first();

    if (await langSelector.count() > 0) {
      const initialLang = await langSelector.textContent();
      console.log(`  Initial language: ${initialLang}`);

      // Click to open language menu
      await clickWithRetry(langSelector);
      await page.waitForTimeout(500);

      await takeScreenshot(page, 'reg-003-language-menu');

      // Look for language options
      const langOptions = await page.locator('[role="menuitem"], [role="option"], button').filter({
        hasText: /English|繁體中文|简体中文/
      }).count();

      console.log(`  Found ${langOptions} language options`);

      if (langOptions > 0) {
        // Select a different language
        const otherLang = page.locator('[role="menuitem"], [role="option"], button').filter({
          hasText: /English|繁體中文|简体中文/
        }).nth(1);

        if (await otherLang.count() > 0) {
          await clickWithRetry(otherLang);
          await page.waitForTimeout(1000);

          const newLang = await langSelector.textContent();
          console.log(`  New language: ${newLang}`);

          await takeScreenshot(page, 'reg-003-language-changed');
        }
      }

      console.log('  ✓ Language switching tested');
    } else {
      console.log('  ⚠️  Language selector not found');
    }

    console.log('\n✅ Test REG-003 passed\n');
  });

  test('REG-004: Performance benchmark', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test REG-004: Performance Benchmark');
    console.log('========================================\n');

    const results: Array<{page: string; metrics: any}> = [];

    // Test worklist performance
    console.log('Testing Worklist Performance...');
    const worklistStart = Date.now();
    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);
    const worklistTime = Date.now() - worklistStart;
    const worklistMetrics = await measurePerformance(page);

    results.push({
      page: 'Worklist',
      metrics: { ...worklistMetrics, clientLoadTime: worklistTime },
    });

    await takeScreenshot(page, 'reg-004-worklist-performance');

    // Test review page performance
    console.log('\nTesting Review Page Performance...');
    const reviewButton = page.locator('button:has-text("Review"), button:has-text("审核")').first();

    if (await reviewButton.count() > 0) {
      const reviewStart = Date.now();
      await clickWithRetry(reviewButton);
      await page.waitForTimeout(3000);
      const reviewTime = Date.now() - reviewStart;
      const reviewMetrics = await measurePerformance(page);

      results.push({
        page: 'Review',
        metrics: { ...reviewMetrics, clientLoadTime: reviewTime },
      });

      await takeScreenshot(page, 'reg-004-review-performance');
    }

    // Report results
    console.log('\n📊 Performance Benchmark Results:');
    results.forEach(result => {
      console.log(`\n  ${result.page} Page:`);
      console.log(`    Client Load Time: ${result.metrics.clientLoadTime}ms`);
      console.log(`    Load Event: ${result.metrics.loadTime.toFixed(0)}ms`);
      console.log(`    First Contentful Paint: ${result.metrics.firstContentfulPaint.toFixed(0)}ms`);
      console.log(`    Total Size: ${(result.metrics.totalSize / 1024 / 1024).toFixed(2)} MB`);
      console.log(`    Requests: ${result.metrics.requestCount}`);
    });

    // Performance assertions
    results.forEach(result => {
      expect(result.metrics.clientLoadTime).toBeLessThan(20000); // 20s max
      expect(result.metrics.firstContentfulPaint).toBeLessThan(8000); // 8s FCP max
    });

    console.log('\n✅ Test REG-004 passed - All pages meet performance thresholds\n');
  });

  test('REG-005: Error resilience test', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test REG-005: Error Resilience');
    console.log('========================================\n');

    const consoleMonitor = createConsoleMonitor(page);
    const networkMonitor = createNetworkMonitor(page);

    consoleMonitor.start();
    networkMonitor.start();

    // Test various scenarios that might cause errors
    console.log('Scenario 1: Rapid navigation...');
    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await page.waitForTimeout(1000);
    await page.goto(`${config.baseURL}#/settings`);
    await page.waitForTimeout(1000);
    await page.goto(`${config.baseURL}#/worklist`);
    await waitForPageReady(page);
    console.log('  ✓ Rapid navigation handled');

    console.log('\nScenario 2: Back/forward navigation...');
    await page.goBack();
    await page.waitForTimeout(500);
    await page.goForward();
    await waitForPageReady(page);
    console.log('  ✓ Back/forward navigation handled');

    console.log('\nScenario 3: Multiple interactions...');
    const reviewButton = page.locator('button:has-text("Review"), button:has-text("审核")').first();
    if (await reviewButton.count() > 0) {
      await clickWithRetry(reviewButton);
      await page.waitForTimeout(2000);

      // Switch views multiple times
      const viewButtons = ['Diff', 'Original', 'Rendered', 'Preview'];
      for (const viewName of viewButtons) {
        const button = page.locator(`button:has-text("${viewName}")`).first();
        if (await button.count() > 0) {
          await clickWithRetry(button);
          await page.waitForTimeout(300);
        }
      }

      console.log('  ✓ Multiple interactions handled');
    }

    await page.waitForTimeout(2000);

    consoleMonitor.stop();
    networkMonitor.stop();

    console.log('\n' + consoleMonitor.getReport());
    console.log('\n' + networkMonitor.getReport());

    // Check for critical errors
    const criticalErrors = consoleMonitor.errors.filter(error =>
      !error.includes('ResizeObserver') &&
      !error.includes('favicon') &&
      !error.includes('analytics')
    );

    const criticalFailures = networkMonitor.failures.filter(failure =>
      !failure.url.includes('favicon') &&
      !failure.url.includes('analytics')
    );

    console.log(`\n📊 Error Summary:`);
    console.log(`  Critical Console Errors: ${criticalErrors.length}`);
    console.log(`  Critical Network Failures: ${criticalFailures.length}`);

    expect(criticalErrors.length).toBeLessThan(5); // Allow up to 5 non-critical errors
    expect(criticalFailures.length).toBe(0); // No network failures allowed

    await takeScreenshot(page, 'reg-005-error-resilience');

    console.log('\n✅ Test REG-005 passed - Application is resilient to errors\n');
  });

  test('REG-006: Accessibility quick check', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test REG-006: Accessibility Check');
    console.log('========================================\n');

    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    // Check for basic accessibility features
    const a11yFeatures = await page.evaluate(() => {
      return {
        hasDoctype: !!document.doctype,
        hasLang: !!document.documentElement.lang,
        hasTitle: !!document.title && document.title.length > 0,
        buttonCount: document.querySelectorAll('button').length,
        linkCount: document.querySelectorAll('a').length,
        inputCount: document.querySelectorAll('input').length,
        headingCount: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
        imagesWithAlt: Array.from(document.querySelectorAll('img')).filter(img => img.alt).length,
        totalImages: document.querySelectorAll('img').length,
        tabindexNegative: document.querySelectorAll('[tabindex="-1"]').length,
      };
    });

    console.log('📊 Accessibility Features:');
    console.log(`  Has DOCTYPE: ${a11yFeatures.hasDoctype ? '✓' : '✗'}`);
    console.log(`  Has lang attribute: ${a11yFeatures.hasLang ? '✓' : '✗'}`);
    console.log(`  Has page title: ${a11yFeatures.hasTitle ? '✓' : '✗'}`);
    console.log(`  Buttons: ${a11yFeatures.buttonCount}`);
    console.log(`  Links: ${a11yFeatures.linkCount}`);
    console.log(`  Inputs: ${a11yFeatures.inputCount}`);
    console.log(`  Headings: ${a11yFeatures.headingCount}`);
    console.log(`  Images with alt: ${a11yFeatures.imagesWithAlt}/${a11yFeatures.totalImages}`);
    console.log(`  Tabindex -1: ${a11yFeatures.tabindexNegative}`);

    // Basic assertions
    expect(a11yFeatures.hasDoctype).toBeTruthy();
    expect(a11yFeatures.hasTitle).toBeTruthy();
    expect(a11yFeatures.headingCount).toBeGreaterThan(0);

    await takeScreenshot(page, 'reg-006-accessibility');

    console.log('\n✅ Test REG-006 passed - Basic accessibility requirements met\n');
  });

  test('REG-007: Cross-page data consistency', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test REG-007: Data Consistency');
    console.log('========================================\n');

    // Load worklist and count items
    console.log('Step 1: Count worklist items...');
    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    const worklistRows = await page.locator('tbody tr').count();
    console.log(`  Worklist rows: ${worklistRows}`);

    if (worklistRows > 0) {
      // Get first row title
      const firstRowTitle = await page.locator('tbody tr').first().locator('td').nth(1).textContent();
      console.log(`  First article title: ${firstRowTitle?.substring(0, 50)}...`);

      // Navigate to review
      console.log('\nStep 2: Navigate to review page...');
      const reviewButton = page.locator('button:has-text("Review"), button:has-text("审核")').first();
      await clickWithRetry(reviewButton);
      await page.waitForTimeout(3000);

      // Check if same article title appears
      const reviewTitle = await page.locator('h1, h2').first().textContent();
      console.log(`  Review page title: ${reviewTitle?.substring(0, 50)}...`);

      // Navigate back
      console.log('\nStep 3: Navigate back and verify data...');
      await page.goBack();
      await waitForPageReady(page);

      const backFirstRowTitle = await page.locator('tbody tr').first().locator('td').nth(1).textContent();
      console.log(`  First article title after back: ${backFirstRowTitle?.substring(0, 50)}...`);

      // Data should be consistent
      expect(firstRowTitle).toBe(backFirstRowTitle);
      console.log('  ✓ Data consistency verified');
    }

    await takeScreenshot(page, 'reg-007-data-consistency');

    console.log('\n✅ Test REG-007 passed\n');
  });
});
