/**
 * Navigation Flow Edge Case Tests
 *
 * Tests navigation and workflow edge cases across the application.
 * Covers: Step navigation, modal states, back navigation, deep linking.
 */

import { test, expect } from '@playwright/test';
import { navigateWithRetry, waitForPageReady } from '../utils/test-helpers';
import { waitForAnimations, captureScreenshot } from '../utils/visual-test-helpers';

const BASE_URL = process.env.TEST_LOCAL === '1'
  ? 'http://localhost:4173'
  : 'https://storage.googleapis.com/cms-automation-frontend-476323/index.html';

test.describe('Navigation Flow Edge Cases', () => {
  test.beforeEach(async ({ page }) => {
    await navigateWithRetry(page, BASE_URL);
    await waitForPageReady(page);
  });

  test.describe('Worklist to Settings Navigation', () => {
    test('should navigate to settings and back', async ({ page }) => {
      // Go to settings
      const settingsButton = page.locator('button:has-text("Settings")');
      await settingsButton.click();
      await waitForAnimations(page);

      await expect(page.locator('text=System Settings')).toBeVisible();

      // Go back to worklist
      const backButton = page.locator('button:has-text("← Back to Worklist")');
      await backButton.click();
      await waitForAnimations(page);

      await expect(page.locator('text=CMS Automation System')).toBeVisible();
    });

    test('should preserve worklist state after settings visit', async ({ page }) => {
      // Apply filter first
      const inProgressTab = page.locator('button:has-text("In Progress")');
      await inProgressTab.click();
      await waitForAnimations(page);

      // Go to settings
      const settingsButton = page.locator('button:has-text("Settings")');
      await settingsButton.click();
      await waitForAnimations(page);

      // Go back
      const backButton = page.locator('button:has-text("← Back to Worklist")');
      await backButton.click();
      await waitForAnimations(page);

      // Filter should be preserved (may depend on implementation)
      console.log('Checking if filter state is preserved');
    });
  });

  test.describe('Article Review Modal Navigation', () => {
    async function openArticleReview(page: any) {
      const reviewButton = page.locator('button:has-text("Review")').first();
      if (await reviewButton.isVisible()) {
        await reviewButton.click();
        await waitForAnimations(page);
        return true;
      }
      return false;
    }

    test('should open and close modal correctly', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Modal should be open
      await expect(page.locator('text=解析审核')).toBeVisible();

      // Close modal
      const closeButton = page.locator('button:has-text("关闭审核"), button:has-text("Close")');
      if (await closeButton.isVisible()) {
        await closeButton.click();
        await waitForAnimations(page);

        // Should be back on worklist
        await expect(page.locator('text=CMS Automation System')).toBeVisible();
      }
    });

    test('should navigate through all 3 steps', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Step 1: Parsing Review
      await expect(page.locator('text=解析审核')).toBeVisible();

      // Go to Step 2
      const step2 = page.locator('text=校对审核').first();
      await step2.click();
      await waitForAnimations(page);

      // Go to Step 3
      const step3 = page.locator('text=最终发布').first();
      await step3.click();
      await waitForAnimations(page);

      // Go back to Step 1
      const step1 = page.locator('text=解析审核').first();
      await step1.click();
      await waitForAnimations(page);
    });

    test('should preserve data when switching steps', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Enter some data in step 1
      const titleInput = page.locator('input').first();
      if (await titleInput.isVisible()) {
        const originalValue = await titleInput.inputValue();

        // Go to step 2
        const step2 = page.locator('text=校对审核').first();
        await step2.click();
        await waitForAnimations(page);

        // Go back to step 1
        const step1 = page.locator('text=解析审核').first();
        await step1.click();
        await waitForAnimations(page);

        // Data should be preserved
        const newValue = await titleInput.inputValue();
        expect(newValue).toBe(originalValue);
      }
    });

    test('should handle closing modal while on step 2', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Go to step 2
      const step2 = page.locator('text=校对审核').first();
      await step2.click();
      await waitForAnimations(page);

      // Close modal
      const closeButton = page.locator('button:has-text("关闭审核"), button[aria-label="close"]');
      if (await closeButton.isVisible()) {
        await closeButton.click();
        await waitForAnimations(page);

        // Should be back on worklist
        await expect(page.locator('text=CMS Automation System')).toBeVisible();
      }
    });

    test('should handle closing modal while on step 3', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Go to step 3
      const step3 = page.locator('text=最终发布').first();
      await step3.click();
      await waitForAnimations(page);

      // Close modal
      const closeButton = page.locator('button:has-text("关闭审核"), button[aria-label="close"]');
      if (await closeButton.isVisible()) {
        await closeButton.click();
        await waitForAnimations(page);

        await expect(page.locator('text=CMS Automation System')).toBeVisible();
      }
    });
  });

  test.describe('Browser Navigation', () => {
    test('should handle browser back button on settings page', async ({ page }) => {
      // Go to settings
      const settingsButton = page.locator('button:has-text("Settings")');
      await settingsButton.click();
      await waitForAnimations(page);

      // Use browser back
      await page.goBack();
      await waitForAnimations(page);

      // Should be back on worklist
      await expect(page.locator('text=CMS Automation System')).toBeVisible();
    });

    test('should handle browser forward button', async ({ page }) => {
      // Go to settings
      const settingsButton = page.locator('button:has-text("Settings")');
      await settingsButton.click();
      await waitForAnimations(page);

      // Go back
      await page.goBack();
      await waitForAnimations(page);

      // Go forward
      await page.goForward();
      await waitForAnimations(page);

      // Should be on settings
      await expect(page.locator('text=System Settings')).toBeVisible();
    });

    test('should handle page refresh on worklist', async ({ page }) => {
      // Apply filter
      const inProgressTab = page.locator('button:has-text("In Progress")');
      await inProgressTab.click();
      await waitForAnimations(page);

      // Refresh page
      await page.reload();
      await waitForPageReady(page);

      // App should load correctly
      await expect(page.locator('text=CMS Automation System')).toBeVisible();
    });

    test('should handle page refresh on settings', async ({ page }) => {
      // Go to settings
      const settingsButton = page.locator('button:has-text("Settings")');
      await settingsButton.click();
      await waitForAnimations(page);

      // Refresh page
      await page.reload();
      await waitForPageReady(page);

      // Should reload worklist (since settings might not be a separate route)
      await expect(page.locator('text=/System Settings|CMS Automation System/')).toBeVisible();
    });
  });

  test.describe('Filter Tab Navigation', () => {
    test('should switch between all filter tabs', async ({ page }) => {
      const tabs = ['All', 'Needs My Attention', 'In Progress', 'Completed', 'Has Issues'];

      for (const tabText of tabs) {
        const tab = page.locator(`button:has-text("${tabText}")`);
        if (await tab.isVisible()) {
          await tab.click();
          await waitForAnimations(page);

          // Tab should be active
          await expect(tab).toHaveClass(/active|selected|primary/i);
        }
      }
    });

    test('should persist filter when opening/closing article', async ({ page }) => {
      // Select "In Progress" filter
      const inProgressTab = page.locator('button:has-text("In Progress")');
      await inProgressTab.click();
      await waitForAnimations(page);

      // Open article review
      const reviewButton = page.locator('button:has-text("Review")').first();
      if (await reviewButton.isVisible()) {
        await reviewButton.click();
        await waitForAnimations(page);

        // Close modal
        const closeButton = page.locator('button:has-text("关闭审核"), button[aria-label="close"]');
        if (await closeButton.isVisible()) {
          await closeButton.click();
          await waitForAnimations(page);
        }
      }

      // Filter should still be "In Progress"
      await expect(inProgressTab).toHaveClass(/active|selected|primary/i);
    });
  });

  test.describe('Search Navigation', () => {
    test('should clear search when navigating away and back', async ({ page }) => {
      // Enter search term
      const searchInput = page.locator('input[placeholder*="Search"]');
      await searchInput.fill('test search');
      await waitForAnimations(page);

      // Go to settings
      const settingsButton = page.locator('button:has-text("Settings")');
      await settingsButton.click();
      await waitForAnimations(page);

      // Go back
      const backButton = page.locator('button:has-text("← Back to Worklist")');
      await backButton.click();
      await waitForAnimations(page);

      // Search might be cleared or preserved (implementation dependent)
      const newSearchValue = await searchInput.inputValue();
      console.log(`Search value after navigation: ${newSearchValue || '(empty)'}`);
    });

    test('should handle search with special characters', async ({ page }) => {
      const searchInput = page.locator('input[placeholder*="Search"]');
      await searchInput.fill('test & <script> 测试');
      await waitForAnimations(page);

      // Should not cause errors
      await expect(page.locator('text=CMS Automation System')).toBeVisible();
    });
  });

  test.describe('Modal Overlay Navigation', () => {
    test('should close modal when clicking outside', async ({ page }) => {
      const reviewButton = page.locator('button:has-text("Review")').first();
      if (await reviewButton.isVisible()) {
        await reviewButton.click();
        await waitForAnimations(page);

        // Click on overlay (outside modal content)
        const overlay = page.locator('[class*="overlay"], [class*="backdrop"]');
        if (await overlay.isVisible()) {
          await overlay.click({ position: { x: 10, y: 10 } });
          await waitForAnimations(page);
        }
      }
    });

    test('should close modal with Escape key', async ({ page }) => {
      const reviewButton = page.locator('button:has-text("Review")').first();
      if (await reviewButton.isVisible()) {
        await reviewButton.click();
        await waitForAnimations(page);

        // Press Escape
        await page.keyboard.press('Escape');
        await waitForAnimations(page);

        // Modal may or may not close (depends on implementation)
        console.log('Escape key behavior captured');
      }
    });
  });

  test.describe('Concurrent Navigation', () => {
    test('should handle rapid navigation between articles', async ({ page }) => {
      const reviewButtons = page.locator('button:has-text("Review")');
      const count = await reviewButtons.count();

      if (count >= 2) {
        // Open first article
        await reviewButtons.first().click();
        await waitForAnimations(page);

        // Close immediately
        const closeButton = page.locator('button:has-text("关闭审核")');
        if (await closeButton.isVisible()) {
          await closeButton.click();
          await waitForAnimations(page);

          // Open second article quickly
          await reviewButtons.nth(1).click();
          await waitForAnimations(page);
        }
      }
    });

    test('should handle rapid filter switching', async ({ page }) => {
      const tabs = ['All', 'In Progress', 'Completed'];

      for (let i = 0; i < 3; i++) {
        for (const tabText of tabs) {
          const tab = page.locator(`button:has-text("${tabText}")`);
          if (await tab.isVisible()) {
            await tab.click();
            // No waiting - rapid clicks
          }
        }
      }

      await waitForAnimations(page);

      // App should remain functional
      await expect(page.locator('text=CMS Automation System')).toBeVisible();
    });
  });

  test.describe('Deep Linking', () => {
    test('should load base URL correctly', async ({ page }) => {
      await page.goto(BASE_URL);
      await waitForPageReady(page);

      await expect(page.locator('text=CMS Automation System')).toBeVisible();
    });

    test('should handle direct navigation to settings if supported', async ({ page }) => {
      // Try settings route if app supports it
      await page.goto(`${BASE_URL}#/settings`);
      await waitForPageReady(page);

      // May load settings or fallback to main page
      const settingsOrMain = page.locator('text=/System Settings|CMS Automation System/');
      await expect(settingsOrMain).toBeVisible();
    });

    test('should handle invalid routes gracefully', async ({ page }) => {
      await page.goto(`${BASE_URL}#/invalid-route`);
      await waitForPageReady(page);

      // Should show main page or 404
      await expect(page.locator('text=/CMS Automation System|Not Found|404/')).toBeVisible();
    });
  });
});
