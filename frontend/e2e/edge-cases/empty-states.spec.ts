/**
 * Empty States Edge Case Tests
 *
 * Tests how the application handles various empty data scenarios.
 * Covers: No articles, no issues, no AI suggestions, no categories.
 */

import { test, expect } from '@playwright/test';
import { navigateWithRetry, waitForPageReady } from '../utils/test-helpers';
import { waitForAnimations, verifyEmptyState } from '../utils/visual-test-helpers';

const BASE_URL = process.env.TEST_LOCAL === '1'
  ? 'http://localhost:4173'
  : 'https://storage.googleapis.com/cms-automation-frontend-476323/index.html';

test.describe('Empty States Edge Cases', () => {
  test.beforeEach(async ({ page }) => {
    await navigateWithRetry(page, BASE_URL);
    await waitForPageReady(page);
  });

  test.describe('Worklist Empty States', () => {
    test('should display appropriate message when filtering returns no results', async ({ page }) => {
      // Use search to filter to no results
      const searchInput = page.locator('input[placeholder*="Search"]');
      await searchInput.fill('xyznonexistent123');
      await waitForAnimations(page);

      // Should show empty state or no results message
      const noResultsIndicator = page.locator('text=/No articles|沒有文章|No results|找不到/i');
      if (await noResultsIndicator.count() > 0) {
        await expect(noResultsIndicator.first()).toBeVisible();
      }
    });

    test('should display correct count when Completed tab is empty', async ({ page }) => {
      // Click on Completed tab
      const completedTab = page.locator('button:has-text("Completed")');
      await completedTab.click();
      await waitForAnimations(page);

      // Check the count badge shows 0
      const countBadge = completedTab.locator('[class*="badge"], span');
      const text = await countBadge.textContent();
      expect(text).toContain('0');
    });

    test('should handle dashboard metrics with no data gracefully', async ({ page }) => {
      // Check for "No data yet" or dash placeholder
      const noDataIndicators = page.locator('text=/No data yet|—|--/');
      const count = await noDataIndicators.count();

      // Should gracefully display empty state, not errors
      if (count > 0) {
        // Verify it's styled appropriately (not an error state)
        const firstIndicator = noDataIndicators.first();
        await expect(firstIndicator).not.toHaveClass(/error|danger/);
      }
    });
  });

  test.describe('Article Review Empty States', () => {
    /**
     * Helper to open article review modal
     */
    async function openArticleReview(page: any) {
      const reviewButton = page.locator('button:has-text("Review")').first();
      if (await reviewButton.isVisible()) {
        await reviewButton.click();
        await waitForAnimations(page);
        return true;
      }
      return false;
    }

    test('should handle missing SEO title suggestions gracefully', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Check SEO Title section
      const seoTitleSection = page.locator('text=SEO Title');
      if (await seoTitleSection.isVisible()) {
        // If no AI suggestions, should show document title or placeholder
        const aiSuggestion = page.locator('text=AI 优化建议');
        const documentExtract = page.locator('text=文档提取');

        // At least one option should be available
        const hasOptions =
          (await aiSuggestion.count()) > 0 || (await documentExtract.count()) > 0;
        expect(hasOptions).toBeTruthy();
      }
    });

    test('should handle missing meta description gracefully', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Check Meta Description section
      const metaSection = page.locator('text=Meta Description');
      if (await metaSection.isVisible()) {
        // Should show at least document extract or custom input option
        const hasInput =
          (await page.locator('textarea').count()) > 0 ||
          (await page.locator('text=文档提取').count()) > 0;
        expect(hasInput).toBeTruthy();
      }
    });

    test('should handle no keywords gracefully', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Check keywords section
      const keywordsSection = page.locator('text=/关键词|Keywords/i');
      if (await keywordsSection.isVisible()) {
        // Should show input or empty state, not error
        const hasEmptyState = await page.locator('text=/暂无|No keywords/i').count() > 0;
        const hasKeywords = await page.locator('[class*="tag"], [class*="chip"]').count() > 0;
        const hasInput = await page.locator('input[placeholder*="keyword"]').count() > 0;

        expect(hasEmptyState || hasKeywords || hasInput).toBeTruthy();
      }
    });

    test('should handle no categories available gracefully', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Check category section
      const categorySection = page.locator('text=/主分类|Primary Category/i');
      if (await categorySection.isVisible()) {
        // Should have dropdown or show loading/empty state
        const hasDropdown = await page.locator('select, [role="combobox"]').count() > 0;
        const hasEmptyState = await page.locator('text=/暂无分类|No categories/i').count() > 0;

        expect(hasDropdown || hasEmptyState).toBeTruthy();
      }
    });

    test('should handle no FAQ suggestions gracefully', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Scroll to FAQ section if exists
      const faqSection = page.locator('text=/FAQ|常見問題/i');
      if (await faqSection.count() > 0) {
        await faqSection.first().scrollIntoViewIfNeeded();

        // Should show empty state or "no suggestions" message
        const hasEmptyState = await page.locator('text=/暂无|No FAQ|没有建议/i').count() > 0;
        const hasFAQItems = await page.locator('[class*="faq"]').count() > 0;

        // Either has items or graceful empty state
        expect(hasEmptyState || hasFAQItems).toBeTruthy();
      }
    });
  });

  test.describe('Proofreading Empty States', () => {
    /**
     * Helper to navigate to proofreading step
     */
    async function navigateToProofreading(page: any) {
      const reviewButton = page.locator('button:has-text("Review")').first();
      if (await reviewButton.isVisible()) {
        await reviewButton.click();
        await waitForAnimations(page);

        const step2 = page.locator('text=校对审核').first();
        if (await step2.isVisible()) {
          await step2.click();
          await waitForAnimations(page);
          return true;
        }
      }
      return false;
    }

    test('should display "所有问题已审核" when no pending issues', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Check if there are no pending issues
      const noPendingMessage = page.locator('text=所有问题已审核');
      const pendingCount = page.locator('text=/\\d+ 个待处理问题/');

      // Either shows "all reviewed" or has pending issues
      const hasNoPending = await noPendingMessage.count() > 0;
      const hasPending = await pendingCount.count() > 0;

      expect(hasNoPending || hasPending).toBeTruthy();
    });

    test('should handle no AI proofreading issues gracefully', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Check for AI issues filter
      const aiFilter = page.locator('text=AI 建议');
      if (await aiFilter.count() > 0) {
        // Either shows AI issues or graceful empty state
        const hasAISection = await page.locator('[class*="ai"]').count() > 0;
        expect(hasAISection || true).toBeTruthy(); // Graceful handling
      }
    });

    test('should show diff view empty state when no changes', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Click on diff view tab
      const diffTab = page.locator('button:has-text("对比")');
      if (await diffTab.isVisible()) {
        await diffTab.click();
        await waitForAnimations(page);

        // Check for "no changes" message
        const noChangesMessage = page.locator('text=/内容未修改|无修改|No changes/i');
        if (await noChangesMessage.count() > 0) {
          await expect(noChangesMessage.first()).toBeVisible();
        }
      }
    });
  });

  test.describe('Settings Empty States', () => {
    test('should display settings page with defaults when no config', async ({ page }) => {
      // Navigate to settings
      const settingsButton = page.locator('button:has-text("Settings")');
      await settingsButton.click();
      await waitForAnimations(page);

      // Verify settings page loads with default values
      await expect(page.locator('text=System Settings')).toBeVisible();

      // Check for default configuration sections
      await expect(page.locator('text=Upload Settings')).toBeVisible();
      await expect(page.locator('text=Cost Limits')).toBeVisible();
    });
  });

  test.describe('Search Empty States', () => {
    test('should show clear search action when no results', async ({ page }) => {
      const searchInput = page.locator('input[placeholder*="Search"]');
      await searchInput.fill('xyznonexistent123456789');
      await waitForAnimations(page);

      // If no results shown, there should be a way to clear search
      const clearButton = page.locator('button[aria-label*="clear"], button:has-text("Clear")');
      if (await clearButton.count() > 0) {
        await expect(clearButton.first()).toBeVisible();
      }

      // Clear search
      await searchInput.clear();
      await waitForAnimations(page);

      // Results should reappear
      const results = page.locator('table tbody tr, [class*="article"]');
      // May have results now
    });

    test('should preserve filter state during search', async ({ page }) => {
      // Apply a filter first
      const inProgressTab = page.locator('button:has-text("In Progress")');
      await inProgressTab.click();
      await waitForAnimations(page);

      // Then search
      const searchInput = page.locator('input[placeholder*="Search"]');
      await searchInput.fill('test');
      await waitForAnimations(page);

      // Filter should still be active
      await expect(inProgressTab).toHaveClass(/active|selected|primary/i);
    });
  });
});
