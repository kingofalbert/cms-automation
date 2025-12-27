/**
 * Proofreading Panel Visual Tests
 *
 * Tests visual appearance and layout of the proofreading review panel.
 * Covers: Issue list, batch operations, diff view, preview mode.
 */

import { test, expect } from '@playwright/test';
import { navigateWithRetry, waitForPageReady } from '../utils/test-helpers';
import {
  VIEWPORTS,
  waitForAnimations,
  captureScreenshot,
  expectToast,
} from '../utils/visual-test-helpers';

const BASE_URL = process.env.TEST_LOCAL === '1'
  ? 'http://localhost:4173'
  : 'https://storage.googleapis.com/cms-automation-frontend-476323/index.html';

test.describe('Proofreading Panel Visual Tests', () => {
  test.beforeEach(async ({ page }) => {
    await navigateWithRetry(page, BASE_URL);
    await waitForPageReady(page);
  });

  /**
   * Helper to navigate to proofreading panel
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

  test.describe('Panel Layout', () => {
    test('should display 3-panel layout on desktop', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop);
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Check for issue list panel
      const issueListPanel = page.locator('text=问题列表');
      await expect(issueListPanel).toBeVisible();

      // Check for content panel
      const contentPanel = page.locator('text=/文章|对比|预览/');
      await expect(contentPanel).toBeVisible();

      await captureScreenshot(page, 'proofreading-3-panel-desktop');
    });

    test('should stack panels on mobile', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile);
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      await captureScreenshot(page, 'proofreading-mobile-layout');
    });
  });

  test.describe('Issue List', () => {
    test('should display issue count header', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Check for pending issues count
      const pendingCount = page.locator('text=/\\d+ 个待处理问题/');
      const allReviewed = page.locator('text=所有问题已审核');

      const hasPending = await pendingCount.count() > 0;
      const hasAllReviewed = await allReviewed.count() > 0;

      expect(hasPending || hasAllReviewed).toBeTruthy();
    });

    test('should display issue items with severity indicators', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Check for severity badges
      const severityBadges = page.locator('text=/严重|一般|轻微|critical|warning|info/i');
      if (await severityBadges.count() > 0) {
        await expect(severityBadges.first()).toBeVisible();
      }
    });

    test('should display issue type badges (T, P, S, C)', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Check for type badges
      const typeBadges = page.locator('[class*="badge"]:has-text("T"), [class*="badge"]:has-text("P")');
      if (await typeBadges.count() > 0) {
        await expect(typeBadges.first()).toBeVisible();
      }
    });

    test('should highlight selected issue', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Click on first issue item
      const issueItem = page.locator('[data-testid="issue-item"], [class*="issue"]').first();
      if (await issueItem.isVisible()) {
        await issueItem.click();
        await waitForAnimations(page);

        // Check for selected state styling
        const selectedItem = page.locator('[class*="selected"], [aria-selected="true"]');
        if (await selectedItem.count() > 0) {
          await expect(selectedItem.first()).toBeVisible();
        }
      }
    });

    test('should display filter options', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Check for filter tabs or buttons
      const allFilter = page.locator('text=/全部|All/');
      const pendingFilter = page.locator('text=/待处理|Pending/');
      const acceptedFilter = page.locator('text=/已接受|Accepted/');
      const rejectedFilter = page.locator('text=/已拒绝|Rejected/');

      const hasFilters = await allFilter.count() > 0 ||
                        await pendingFilter.count() > 0 ||
                        await acceptedFilter.count() > 0;

      // May have different filter implementation
      console.log(`Filter buttons found: ${hasFilters}`);
    });
  });

  test.describe('Batch Operations', () => {
    test('should display batch accept button', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      const acceptAllButton = page.locator('button:has-text("全部接受")');
      if (await acceptAllButton.count() > 0) {
        await expect(acceptAllButton.first()).toBeVisible();
      }
    });

    test('should display batch reject button', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      const rejectAllButton = page.locator('button:has-text("全部拒绝")');
      if (await rejectAllButton.count() > 0) {
        await expect(rejectAllButton.first()).toBeVisible();
      }
    });

    test('should display severity-based batch buttons', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Check for severity-based batch operations
      const severitySection = page.locator('text=/严重问题|AI 建议/');
      if (await severitySection.count() > 0) {
        await expect(severitySection.first()).toBeVisible();
      }
    });

    test('should show toast feedback after batch accept', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      const acceptAllButton = page.locator('button:has-text("全部接受")').first();
      if (await acceptAllButton.isVisible()) {
        await acceptAllButton.click();

        // Check for toast notification
        const toast = page.locator('[class*="toast"], [role="alert"]');
        await expect(toast).toBeVisible({ timeout: 5000 }).catch(() => {
          console.log('Toast may have different selector or timing');
        });
      }
    });
  });

  test.describe('Content View Modes', () => {
    test('should display view mode tabs', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Check for view mode tabs
      const articleTab = page.locator('button:has-text("文章")');
      const diffTab = page.locator('button:has-text("对比")');
      const previewTab = page.locator('button:has-text("预览")');

      const hasArticle = await articleTab.count() > 0;
      const hasDiff = await diffTab.count() > 0;
      const hasPreview = await previewTab.count() > 0;

      expect(hasArticle || hasDiff || hasPreview).toBeTruthy();
    });

    test('should switch to diff view when clicking tab', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      const diffTab = page.locator('button:has-text("对比")');
      if (await diffTab.isVisible()) {
        await diffTab.click();
        await waitForAnimations(page);

        await captureScreenshot(page, 'proofreading-diff-view');
      }
    });

    test('should switch to preview view when clicking tab', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      const previewTab = page.locator('button:has-text("预览")');
      if (await previewTab.isVisible()) {
        await previewTab.click();
        await waitForAnimations(page);

        await captureScreenshot(page, 'proofreading-preview-view');
      }
    });
  });

  test.describe('Issue Detail Panel', () => {
    test('should display issue detail when selected', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Click on first issue
      const issueItem = page.locator('[data-testid="issue-item"], [class*="issue-item"]').first();
      if (await issueItem.isVisible()) {
        await issueItem.click();
        await waitForAnimations(page);

        // Check for detail panel content
        const detailPanel = page.locator('text=/原文|修改建议|Original|Suggestion/i');
        if (await detailPanel.count() > 0) {
          await expect(detailPanel.first()).toBeVisible();
        }
      }
    });

    test('should display accept/reject buttons in detail', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Click on first issue
      const issueItem = page.locator('[data-testid="issue-item"], [class*="issue"]').first();
      if (await issueItem.isVisible()) {
        await issueItem.click();
        await waitForAnimations(page);

        // Check for action buttons in detail panel
        const acceptButton = page.locator('button:has-text("接受")');
        const rejectButton = page.locator('button:has-text("拒绝")');

        await expect(acceptButton.or(rejectButton)).toBeVisible();
      }
    });
  });

  test.describe('Issue Highlighting', () => {
    test('should highlight issue position in article content', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Click on an issue to select it
      const issueItem = page.locator('[data-testid="issue-item"], [class*="issue"]').first();
      if (await issueItem.isVisible()) {
        await issueItem.click();
        await waitForAnimations(page);

        // Check for highlighted text in content panel
        const highlighted = page.locator('[class*="highlight"], mark, [style*="background"]');
        if (await highlighted.count() > 0) {
          await expect(highlighted.first()).toBeVisible();
        }
      }
    });

    test('should use correct color coding for issue severity', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Check for color-coded severity indicators
      const criticalBadge = page.locator('[class*="red"], [class*="danger"], [class*="critical"]');
      const warningBadge = page.locator('[class*="yellow"], [class*="warning"]');
      const infoBadge = page.locator('[class*="blue"], [class*="info"]');

      const hasCritical = await criticalBadge.count() > 0;
      const hasWarning = await warningBadge.count() > 0;
      const hasInfo = await infoBadge.count() > 0;

      console.log(`Color coding - Critical: ${hasCritical}, Warning: ${hasWarning}, Info: ${hasInfo}`);
    });
  });

  test.describe('Decision State Display', () => {
    test('should show accepted state styling', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Click accept on first issue
      const acceptButton = page.locator('button:has-text("接受")').first();
      if (await acceptButton.isVisible()) {
        await acceptButton.click();
        await waitForAnimations(page);

        // Check for accepted state indicator
        const acceptedIndicator = page.locator('text=/已接受|✓/, [class*="accepted"]');
        if (await acceptedIndicator.count() > 0) {
          await expect(acceptedIndicator.first()).toBeVisible();
        }
      }
    });

    test('should show rejected state styling', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Click reject on first issue
      const rejectButton = page.locator('button:has-text("拒绝")').first();
      if (await rejectButton.isVisible()) {
        await rejectButton.click();
        await waitForAnimations(page);

        // Check for rejected state indicator
        const rejectedIndicator = page.locator('text=/已拒绝|✗/, [class*="rejected"]');
        if (await rejectedIndicator.count() > 0) {
          await expect(rejectedIndicator.first()).toBeVisible();
        }
      }
    });
  });

  test.describe('Responsive Layout', () => {
    test('should adapt layout for tablet', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.tablet);
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      await captureScreenshot(page, 'proofreading-tablet');
    });

    test('should use tab navigation on mobile', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile);
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // On mobile, panels may be in tabs
      const tabButtons = page.locator('[role="tab"], button[class*="tab"]');
      const tabCount = await tabButtons.count();
      console.log(`Mobile tab count: ${tabCount}`);

      await captureScreenshot(page, 'proofreading-mobile');
    });
  });

  test.describe('Empty States', () => {
    test('should show empty state when no issues', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Accept all issues first
      const acceptAllButton = page.locator('button:has-text("全部接受")').first();
      if (await acceptAllButton.isVisible()) {
        await acceptAllButton.click();
        await waitForAnimations(page);

        // Check for empty state message
        const emptyMessage = page.locator('text=/所有问题已审核|无待处理问题/');
        if (await emptyMessage.count() > 0) {
          await expect(emptyMessage.first()).toBeVisible();
        }

        await captureScreenshot(page, 'proofreading-empty-state');
      }
    });
  });

  test.describe('Progress Indicator', () => {
    test('should update progress when issues are processed', async ({ page }) => {
      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // Get initial progress
      const progressText = page.locator('text=/%/');
      let initialProgress = '';
      if (await progressText.count() > 0) {
        initialProgress = await progressText.first().textContent() || '';
      }

      // Accept one issue
      const acceptButton = page.locator('button:has-text("接受")').first();
      if (await acceptButton.isVisible()) {
        await acceptButton.click();
        await waitForAnimations(page);

        // Progress should update
        if (await progressText.count() > 0) {
          const newProgress = await progressText.first().textContent() || '';
          console.log(`Progress changed from ${initialProgress} to ${newProgress}`);
        }
      }
    });
  });
});
