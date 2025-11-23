/**
 * Article Review Modal - Scroll Functionality Test
 *
 * Tests that the ParsingReviewPanel allows proper scrolling
 * after removing the overflow-auto conflict.
 */

import { test, expect } from '@playwright/test';
import {
  getTestConfig,
  navigateWithRetry,
  waitForPageReady,
} from './utils/test-helpers';

const config = getTestConfig();

test.describe('Article Review Modal - Scroll Test', () => {
  test('validates that modal content is scrollable', async ({ page }) => {
    // Navigate to worklist
    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    // Click first row to open modal
    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toBeVisible({ timeout: 20000 });
    await firstRow.click();

    // Wait for modal to appear
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 20000 });

    // Wait for loading to finish
    const loadingText = page.locator('text=/加载文章审核数据|Loading article review/i');
    if (await loadingText.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(loadingText).not.toBeVisible({ timeout: 20000 });
    }

    // Click parsing tab if exists
    const parsingTab = page.locator('button:has-text("解析审核"), button:has-text("Parsing Review")').first();
    if (await parsingTab.isVisible()) {
      await parsingTab.click();
      await page.waitForTimeout(500);
    }

    // Find the scrollable container
    // In ArticleReviewModal, the scrollable container is:
    // <div className="flex-1 overflow-y-auto overflow-x-hidden">
    const scrollContainer = modal.locator('.overflow-y-auto').first();
    await expect(scrollContainer).toBeVisible();

    // Get initial scroll position
    const initialScrollTop = await scrollContainer.evaluate((el) => el.scrollTop);
    console.log(`Initial scroll position: ${initialScrollTop}`);

    // Get scroll height and client height
    const scrollMetrics = await scrollContainer.evaluate((el) => ({
      scrollHeight: el.scrollHeight,
      clientHeight: el.clientHeight,
      scrollTop: el.scrollTop,
    }));

    console.log('Scroll metrics:', scrollMetrics);

    // Verify that content is taller than viewport (scrollable)
    expect(scrollMetrics.scrollHeight).toBeGreaterThan(scrollMetrics.clientHeight);

    // Try to scroll down by 500px
    await scrollContainer.evaluate((el) => {
      el.scrollTop = 500;
    });

    // Wait for scroll to settle
    await page.waitForTimeout(300);

    // Get new scroll position
    const newScrollTop = await scrollContainer.evaluate((el) => el.scrollTop);
    console.log(`After scroll: ${newScrollTop}`);

    // Verify that scroll actually happened
    expect(newScrollTop).toBeGreaterThan(initialScrollTop);
    expect(newScrollTop).toBeGreaterThanOrEqual(400); // Should be close to 500

    // Scroll to bottom
    await scrollContainer.evaluate((el) => {
      el.scrollTop = el.scrollHeight;
    });

    await page.waitForTimeout(300);

    const bottomScrollTop = await scrollContainer.evaluate((el) => el.scrollTop);
    console.log(`At bottom: ${bottomScrollTop}`);

    // Verify we can reach near the bottom
    const maxScroll = scrollMetrics.scrollHeight - scrollMetrics.clientHeight;
    expect(bottomScrollTop).toBeGreaterThanOrEqual(maxScroll * 0.9); // Within 10% of max

    // Scroll back to top
    await scrollContainer.evaluate((el) => {
      el.scrollTop = 0;
    });

    await page.waitForTimeout(300);

    const topScrollTop = await scrollContainer.evaluate((el) => el.scrollTop);
    console.log(`Back to top: ${topScrollTop}`);

    // Verify we're back at top
    expect(topScrollTop).toBeLessThan(10);

    console.log('✅ Scroll test passed: Modal content is properly scrollable');
  });

  test('validates that ParsingReviewPanel grid does not have overflow-auto', async ({ page }) => {
    // Navigate to worklist
    await navigateWithRetry(page, `${config.baseURL}#/worklist`);
    await waitForPageReady(page);

    // Click first row to open modal
    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toBeVisible({ timeout: 20000 });
    await firstRow.click();

    // Wait for modal
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 20000 });

    // Wait for loading to finish
    const loadingText = page.locator('text=/加载文章审核数据|Loading article review/i');
    if (await loadingText.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(loadingText).not.toBeVisible({ timeout: 20000 });
    }

    // Click parsing tab
    const parsingTab = page.locator('button:has-text("解析审核"), button:has-text("Parsing Review")').first();
    if (await parsingTab.isVisible()) {
      await parsingTab.click();
      await page.waitForTimeout(500);
    }

    // Find the parsing grid container
    const gridContainer = page.locator('[data-testid="parsing-review-grid"]');
    await expect(gridContainer).toBeVisible();

    // Check that grid does NOT have overflow-auto class
    const classes = await gridContainer.getAttribute('class');
    console.log('Grid classes:', classes);

    expect(classes).not.toContain('overflow-auto');
    expect(classes).not.toContain('overflow-y-auto');

    console.log('✅ Grid correctly does NOT have overflow-auto class');
  });
});
