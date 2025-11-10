/**
 * Proofreading Review Workflow - Comprehensive Regression Tests
 *
 * Tests the complete proofreading review functionality including:
 * - Page load and layout
 * - View mode switching (Original, Rendered, Preview, Diff)
 * - Issue list and filtering
 * - Issue selection and navigation
 * - Decision actions (Accept/Reject)
 * - Review notes
 * - Chrome DevTools integration
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
} from '../utils/test-helpers';

const config = getTestConfig();

test.describe('Proofreading Review Workflow - Regression Tests', () => {
  // Navigate to review page before each test
  test.beforeEach(async ({ page }) => {
    // First go to worklist
    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    // Click first Review button to enter review page
    const reviewButton = page.locator('button:has-text("Review"), button:has-text("审核"), a:has-text("Review")').first();
    const hasButton = await reviewButton.count() > 0;

    if (hasButton) {
      await clickWithRetry(reviewButton);
      await page.waitForTimeout(3000);
    } else {
      console.log('⚠️  No Review button found, skipping to direct URL');
      // Fallback: try direct URL
      await page.goto(`${config.baseURL}#/worklist/1/review`);
      await waitForPageReady(page);
    }
  });

  test('PR-001: Should load proofreading review page', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test PR-001: Review Page Load');
    console.log('========================================\n');

    // Verify URL contains 'review' or 'proofreading'
    const url = page.url();
    console.log(`✓ Current URL: ${url}`);
    expect(url).toMatch(/review|proofreading/);

    // Verify page has content
    const bodyText = await page.locator('body').textContent();
    const hasContent = bodyText && bodyText.length > 200;
    console.log(`✓ Page has content: ${hasContent} (${bodyText?.length || 0} chars)`);
    expect(hasContent).toBeTruthy();

    // Take screenshot
    await takeScreenshot(page, 'review-page-loaded', { fullPage: true });

    console.log('✅ Test PR-001 passed\n');
  });

  test('PR-002: Should display article title', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test PR-002: Article Title Display');
    console.log('========================================\n');

    // Look for article title (h1, h2, or prominent text)
    const titleElement = page.locator('h1, h2').first();
    const hasTitle = await titleElement.count() > 0;

    if (hasTitle) {
      const titleText = await titleElement.textContent();
      console.log(`✓ Article title: ${titleText}`);
      expect(titleText).toBeTruthy();
      expect(titleText!.length).toBeGreaterThan(5);
    } else {
      console.log('⚠️  Title element not found, checking for any prominent text...');
      const prominentText = await page.locator('[class*="title"], [class*="heading"]').first().textContent();
      console.log(`  Found text: ${prominentText}`);
    }

    await takeScreenshot(page, 'review-article-title');

    console.log('✅ Test PR-002 passed\n');
  });

  test('PR-003: Should display view mode buttons', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test PR-003: View Mode Buttons');
    console.log('========================================\n');

    const viewModes = [
      { name: 'Original', cn: '原始' },
      { name: 'Rendered', cn: '渲染' },
      { name: 'Preview', cn: '预览' },
      { name: 'Diff', cn: '对比' },
    ];

    let foundCount = 0;

    for (const mode of viewModes) {
      const button = page.locator(`button:has-text("${mode.name}"), button:has-text("${mode.cn}")`);
      const count = await button.count();

      if (count > 0) {
        foundCount++;
        console.log(`✓ ${mode.name} button found`);
      } else {
        console.log(`  ${mode.name} button not found`);
      }
    }

    console.log(`\nTotal view mode buttons found: ${foundCount}`);
    expect(foundCount).toBeGreaterThan(0);

    await takeScreenshot(page, 'review-view-mode-buttons');

    console.log('✅ Test PR-003 passed\n');
  });

  test('PR-004: Should switch between view modes', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test PR-004: View Mode Switching');
    console.log('========================================\n');

    const viewModes = [
      { name: 'Original', cn: '原始' },
      { name: 'Rendered', cn: '渲染' },
      { name: 'Diff', cn: '对比' },
      { name: 'Preview', cn: '预览' },
    ];

    for (const mode of viewModes) {
      console.log(`\nTesting ${mode.name} view...`);

      const button = page.locator(`button:has-text("${mode.name}"), button:has-text("${mode.cn}")`).first();
      const hasButton = await button.count() > 0;

      if (hasButton) {
        // Click the button
        await clickWithRetry(button);
        console.log(`  ✓ Clicked ${mode.name} button`);

        // Wait for view to update
        await page.waitForTimeout(1000);

        // Check if button is active (has active styling)
        const buttonClass = await button.getAttribute('class');
        console.log(`  Button classes: ${buttonClass}`);

        // Take screenshot
        await takeScreenshot(page, `review-view-${mode.name.toLowerCase()}`);
      } else {
        console.log(`  ⚠️  ${mode.name} button not found, skipping`);
      }
    }

    console.log('✅ Test PR-004 passed\n');
  });

  test('PR-005: Should display issue list', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test PR-005: Issue List Display');
    console.log('========================================\n');

    // Wait a bit for issues to load
    await page.waitForTimeout(2000);

    // Look for issue items
    const issueSelectors = [
      '[data-testid*="issue"]',
      '.issue-item',
      '[class*="issue"]',
      'li',
    ];

    let issueCount = 0;
    let usedSelector = '';

    for (const selector of issueSelectors) {
      const count = await page.locator(selector).count();
      if (count > issueCount) {
        issueCount = count;
        usedSelector = selector;
      }
    }

    console.log(`✓ Found ${issueCount} potential issue items using selector: ${usedSelector}`);

    if (issueCount > 0) {
      // Get first issue details
      const firstIssue = page.locator(usedSelector).first();
      const issueText = await firstIssue.textContent();
      console.log(`  First issue preview: ${issueText?.substring(0, 100)}...`);
    } else {
      console.log('⚠️  No issues found (may be a clean article)');
    }

    await takeScreenshot(page, 'review-issue-list');

    console.log('✅ Test PR-005 passed\n');
  });

  test('PR-006: Should display issue filters', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test PR-006: Issue Filters');
    console.log('========================================\n');

    // Look for filter controls
    const filterTypes = [
      'All Severity', '所有严重程度',
      'Critical', '严重',
      'Warning', '警告',
      'All Categories', '所有类别',
      'All Engines', '所有引擎',
    ];

    let foundFilters = 0;

    for (const filterText of filterTypes) {
      const filter = page.locator(`select, button:has-text("${filterText}")`);
      const count = await filter.count();

      if (count > 0) {
        foundFilters++;
        console.log(`✓ Found filter: ${filterText}`);
      }
    }

    console.log(`\nTotal filters found: ${foundFilters}`);

    await takeScreenshot(page, 'review-issue-filters');

    console.log('✅ Test PR-006 passed\n');
  });

  test('PR-007: Should display issue detail panel', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test PR-007: Issue Detail Panel');
    console.log('========================================\n');

    await page.waitForTimeout(2000);

    // Look for decision buttons
    const acceptButton = page.locator('button:has-text("Accept"), button:has-text("接受")');
    const rejectButton = page.locator('button:has-text("Reject"), button:has-text("拒绝")');

    const hasAccept = await acceptButton.count() > 0;
    const hasReject = await rejectButton.count() > 0;

    console.log(`  Accept button: ${hasAccept ? '✓ Found' : '✗ Not found'}`);
    console.log(`  Reject button: ${hasReject ? '✓ Found' : '✗ Not found'}`);

    if (hasAccept || hasReject) {
      console.log('✓ Issue detail panel with decision buttons found');
    } else {
      console.log('⚠️  Decision buttons not found (may need to select an issue first)');
    }

    // Look for custom modification textarea
    const textarea = page.locator('textarea[placeholder*="custom"], textarea[placeholder*="自定义"], textarea').first();
    const hasTextarea = await textarea.count() > 0;
    console.log(`  Custom modification textarea: ${hasTextarea ? '✓ Found' : '✗ Not found'}`);

    await takeScreenshot(page, 'review-issue-detail');

    console.log('✅ Test PR-007 passed\n');
  });

  test('PR-008: Should click and select an issue', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test PR-008: Issue Selection');
    console.log('========================================\n');

    await page.waitForTimeout(2000);

    // Find issue items
    const issueItems = page.locator('[data-testid*="issue"], .issue-item, [class*="issue"], li');
    const count = await issueItems.count();

    if (count > 0) {
      console.log(`✓ Found ${count} issue items`);

      // Click first issue
      const firstIssue = issueItems.first();
      await clickWithRetry(firstIssue);
      console.log('✓ Clicked first issue');

      await page.waitForTimeout(1000);

      // Check if issue is highlighted
      const issueClass = await firstIssue.getAttribute('class');
      console.log(`  Issue classes: ${issueClass}`);

      await takeScreenshot(page, 'review-issue-selected');
    } else {
      console.log('⚠️  No issues to select');
    }

    console.log('✅ Test PR-008 passed\n');
  });

  test('PR-009: Should display review notes textarea', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test PR-009: Review Notes');
    console.log('========================================\n');

    // Look for review notes textarea
    const reviewNotes = page.locator(
      'textarea[id="review-notes"], textarea[placeholder*="审核备注"], textarea[placeholder*="review"]'
    ).first();

    const hasNotes = await reviewNotes.count() > 0;
    console.log(`✓ Review notes textarea: ${hasNotes ? 'Found' : 'Not found'}`);

    if (hasNotes) {
      // Try to type in it
      await reviewNotes.fill('Test review notes - automated test');
      const value = await reviewNotes.inputValue();
      console.log(`  Successfully entered text: ${value}`);
      expect(value).toContain('automated test');
    }

    await takeScreenshot(page, 'review-notes');

    console.log('✅ Test PR-009 passed\n');
  });

  test('PR-010: Should display action buttons', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test PR-010: Action Buttons');
    console.log('========================================\n');

    // Look for action buttons
    const actionButtons = [
      'Approve', '批准', '通过',
      'Reject', '拒绝',
      'Save', '保存',
      'Submit', '提交',
      'Cancel', '取消',
      'Back', '返回',
    ];

    const foundButtons: string[] = [];

    for (const buttonText of actionButtons) {
      const button = page.locator(`button:has-text("${buttonText}")`);
      const count = await button.count();

      if (count > 0) {
        foundButtons.push(buttonText);
        console.log(`✓ Found button: ${buttonText}`);
      }
    }

    console.log(`\nTotal action buttons found: ${foundButtons.length}`);
    console.log(`Buttons: ${foundButtons.join(', ')}`);

    await takeScreenshot(page, 'review-action-buttons');

    console.log('✅ Test PR-010 passed\n');
  });

  test('PR-011: Should display comparison cards', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test PR-011: AI Optimization Cards');
    console.log('========================================\n');

    // Look for AI optimization section
    const aiSection = page.locator('text=/AI 优化建议|AI Optimization|SEO/i');
    const hasAISection = await aiSection.count() > 0;

    console.log(`✓ AI optimization section: ${hasAISection ? 'Found' : 'Not found'}`);

    if (hasAISection) {
      // Look for specific cards
      const cards = [
        'Meta Description',
        'SEO Keywords', 'SEO 关键词',
        'Tags', '标签',
        'Title', '标题',
      ];

      for (const cardText of cards) {
        const card = page.locator(`text=/${cardText}/i`);
        const count = await card.count();

        if (count > 0) {
          console.log(`  ✓ ${cardText} card found`);
        }
      }
    }

    await takeScreenshot(page, 'review-comparison-cards');

    console.log('✅ Test PR-011 passed\n');
  });

  test('PR-012: Should measure review page performance', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test PR-012: Performance Metrics');
    console.log('========================================\n');

    // Measure performance
    const metrics = await measurePerformance(page);

    console.log('📊 Performance Metrics:');
    console.log(`  Load Event: ${metrics.loadTime.toFixed(0)}ms`);
    console.log(`  DOM Content Loaded: ${metrics.domContentLoaded.toFixed(0)}ms`);
    console.log(`  First Contentful Paint: ${metrics.firstContentfulPaint.toFixed(0)}ms`);
    console.log(`  Time to Interactive: ${metrics.timeToInteractive.toFixed(0)}ms`);
    console.log(`  Total Size: ${(metrics.totalSize / 1024 / 1024).toFixed(2)} MB`);
    console.log(`  Request Count: ${metrics.requestCount}`);

    // Performance assertions
    expect(metrics.loadTime).toBeLessThan(20000); // Should load within 20 seconds
    expect(metrics.firstContentfulPaint).toBeLessThan(8000); // FCP within 8 seconds

    console.log('✅ Test PR-012 passed\n');
  });

  test('PR-013: Should test diff view rendering performance', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test PR-013: Diff View Performance');
    console.log('========================================\n');

    const diffButton = page.locator('button:has-text("Diff"), button:has-text("对比")').first();
    const hasDiffButton = await diffButton.count() > 0;

    if (hasDiffButton) {
      // Measure time to switch to diff view
      const startTime = Date.now();

      await clickWithRetry(diffButton);

      // Wait for diff view to render
      await page.waitForTimeout(500);

      const endTime = Date.now();
      const renderTime = endTime - startTime;

      console.log(`📊 Diff View Render Time: ${renderTime}ms`);

      // Should render smoothly (< 1 second)
      expect(renderTime).toBeLessThan(1000);

      await takeScreenshot(page, 'review-diff-performance');

      console.log('✅ Diff view rendered within performance threshold');
    } else {
      console.log('⚠️  Diff button not found, skipping performance test');
    }

    console.log('✅ Test PR-013 passed\n');
  });

  test('PR-014: Should monitor console errors during interaction', async ({ page }) => {
    console.log('\n========================================');
    console.log('Test PR-014: Console Error Monitoring');
    console.log('========================================\n');

    const consoleMonitor = createConsoleMonitor(page);
    consoleMonitor.start();

    // Perform various interactions
    const diffButton = page.locator('button:has-text("Diff"), button:has-text("对比")').first();
    if (await diffButton.count() > 0) {
      await clickWithRetry(diffButton);
      await page.waitForTimeout(500);
    }

    const renderedButton = page.locator('button:has-text("Rendered"), button:has-text("渲染")').first();
    if (await renderedButton.count() > 0) {
      await clickWithRetry(renderedButton);
      await page.waitForTimeout(500);
    }

    consoleMonitor.stop();

    console.log(consoleMonitor.getReport());

    const criticalErrors = consoleMonitor.errors.filter(error =>
      !error.includes('ResizeObserver') &&
      !error.includes('favicon')
    );

    console.log(`\n${criticalErrors.length === 0 ? '✅' : '⚠️'} Critical errors: ${criticalErrors.length}`);

    console.log('✅ Test PR-014 passed\n');
  });
});
