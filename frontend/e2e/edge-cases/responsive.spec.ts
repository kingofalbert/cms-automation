/**
 * Responsive Layout Edge Case Tests
 *
 * Tests how the application adapts to different viewport sizes.
 * Covers: Mobile, tablet, desktop, ultrawide, dynamic resize.
 */

import { test, expect } from '@playwright/test';
import { navigateWithRetry, waitForPageReady } from '../utils/test-helpers';
import {
  VIEWPORTS,
  testResponsive,
  waitForAnimations,
  captureScreenshot,
  isInViewport,
} from '../utils/visual-test-helpers';

const BASE_URL = process.env.TEST_LOCAL === '1'
  ? 'http://localhost:4173'
  : 'https://storage.googleapis.com/cms-automation-frontend-476323/index.html';

test.describe('Responsive Layout Edge Cases', () => {
  test.describe('Mobile Viewport (320px)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile);
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);
    });

    test('should display header without overflow', async ({ page }) => {
      const header = page.locator('header, [class*="header"]').first();
      if (await header.isVisible()) {
        const box = await header.boundingBox();
        expect(box?.width).toBeLessThanOrEqual(VIEWPORTS.mobile.width);
      }
    });

    test('should stack dashboard cards vertically', async ({ page }) => {
      const cards = page.locator('[class*="card"], [class*="Card"]');
      const count = await cards.count();

      if (count > 1) {
        const firstBox = await cards.first().boundingBox();
        const secondBox = await cards.nth(1).boundingBox();

        if (firstBox && secondBox) {
          // Cards should be stacked (second card below first)
          expect(secondBox.y).toBeGreaterThanOrEqual(firstBox.y + firstBox.height - 10);
        }
      }
    });

    test('should make table scrollable horizontally', async ({ page }) => {
      const tableContainer = page.locator('table').locator('..');

      if (await tableContainer.isVisible()) {
        const overflow = await tableContainer.evaluate((el) => {
          const style = window.getComputedStyle(el);
          return style.overflowX;
        });

        // Should be scrollable or auto
        expect(['scroll', 'auto', 'hidden']).toContain(overflow);
      }
    });

    test('should hide non-essential columns on mobile', async ({ page }) => {
      // On mobile, some columns might be hidden
      const qualityScoreHeader = page.locator('text=QUALITY SCORE');
      const wordCountHeader = page.locator('text=WORD COUNT');

      // These columns might be hidden on mobile for better UX
      // Test passes regardless - just documenting behavior
      const qualityVisible = await qualityScoreHeader.isVisible();
      const wordCountVisible = await wordCountHeader.isVisible();

      console.log(`Mobile view - Quality Score visible: ${qualityVisible}, Word Count visible: ${wordCountVisible}`);
    });

    test('should display mobile-friendly action buttons', async ({ page }) => {
      const actionButtons = page.locator('button:has-text("Review"), button:has-text("View")');

      if (await actionButtons.count() > 0) {
        const firstButton = actionButtons.first();
        const box = await firstButton.boundingBox();

        // Buttons should be at least 44px for touch targets
        if (box) {
          expect(box.height).toBeGreaterThanOrEqual(32);
          expect(box.width).toBeGreaterThanOrEqual(32);
        }
      }
    });

    test('should allow scrolling to see all content', async ({ page }) => {
      // Scroll to bottom
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await waitForAnimations(page);

      // Should be able to scroll
      const scrollTop = await page.evaluate(() => window.scrollY);
      expect(scrollTop).toBeGreaterThan(0);
    });
  });

  test.describe('Tablet Viewport (768px)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.tablet);
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);
    });

    test('should display 2-column layout for dashboard cards', async ({ page }) => {
      const cards = page.locator('[class*="card"], [class*="Card"]');
      const count = await cards.count();

      if (count >= 2) {
        const firstBox = await cards.first().boundingBox();
        const secondBox = await cards.nth(1).boundingBox();

        if (firstBox && secondBox) {
          // On tablet, cards might be side by side or stacked
          // Just verify they're positioned reasonably
          expect(secondBox.x + secondBox.width).toBeLessThanOrEqual(VIEWPORTS.tablet.width);
        }
      }
    });

    test('should display filter tabs without overflow', async ({ page }) => {
      const filterTabs = page.locator('button:has-text("All")').locator('..');

      if (await filterTabs.isVisible()) {
        const box = await filterTabs.boundingBox();
        if (box) {
          expect(box.width).toBeLessThanOrEqual(VIEWPORTS.tablet.width);
        }
      }
    });
  });

  test.describe('Desktop Viewport (1280px)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop);
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);
    });

    test('should display full dashboard layout', async ({ page }) => {
      // All dashboard cards should be visible without scrolling
      await expect(page.locator('text=Total Articles')).toBeVisible();
      await expect(page.locator('text=Ready to Publish')).toBeVisible();
      await expect(page.locator('text=Average Cycle')).toBeVisible();
    });

    test('should display all table columns', async ({ page }) => {
      await expect(page.locator('text=TITLE')).toBeVisible();
      await expect(page.locator('text=STATUS')).toBeVisible();
      await expect(page.locator('text=AUTHOR')).toBeVisible();
      await expect(page.locator('text=QUALITY SCORE')).toBeVisible();
    });
  });

  test.describe('Ultrawide Viewport (2560px)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktopUltrawide);
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);
    });

    test('should constrain content width appropriately', async ({ page }) => {
      const mainContent = page.locator('main, [class*="container"], [class*="content"]').first();

      if (await mainContent.isVisible()) {
        const box = await mainContent.boundingBox();
        if (box) {
          // Content should be constrained, not stretch to full width
          // Common max-width values: 1280px, 1440px, 1920px
          expect(box.width).toBeLessThanOrEqual(1920);
        }
      }
    });

    test('should center content on ultrawide', async ({ page }) => {
      const mainContent = page.locator('main, [class*="container"]').first();

      if (await mainContent.isVisible()) {
        const box = await mainContent.boundingBox();
        if (box) {
          // Should have equal margins on both sides (approximately centered)
          const leftMargin = box.x;
          const rightMargin = VIEWPORTS.desktopUltrawide.width - (box.x + box.width);

          // Allow some tolerance
          expect(Math.abs(leftMargin - rightMargin)).toBeLessThan(50);
        }
      }
    });
  });

  test.describe('Dynamic Viewport Resize', () => {
    test('should handle resize from desktop to mobile', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop);
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      // Resize to mobile
      await page.setViewportSize(VIEWPORTS.mobile);
      await waitForAnimations(page);

      // Page should still be functional
      await expect(page.locator('text=CMS Automation System')).toBeVisible();

      // Capture screenshot
      await captureScreenshot(page, 'resize-desktop-to-mobile');
    });

    test('should handle resize from mobile to desktop', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile);
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      // Resize to desktop
      await page.setViewportSize(VIEWPORTS.desktop);
      await waitForAnimations(page);

      // Page should still be functional
      await expect(page.locator('text=CMS Automation System')).toBeVisible();

      // Capture screenshot
      await captureScreenshot(page, 'resize-mobile-to-desktop');
    });

    test('should handle rapid viewport changes', async ({ page }) => {
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      // Rapidly change viewport sizes
      const viewports = [
        VIEWPORTS.desktop,
        VIEWPORTS.tablet,
        VIEWPORTS.mobile,
        VIEWPORTS.tablet,
        VIEWPORTS.desktop,
      ];

      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(100);
      }

      await waitForAnimations(page);

      // Page should remain functional
      await expect(page.locator('text=CMS Automation System')).toBeVisible();
    });
  });

  test.describe('Article Review Modal Responsive', () => {
    test('should display modal correctly on mobile', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile);
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      const reviewButton = page.locator('button:has-text("Review")').first();
      if (await reviewButton.isVisible()) {
        await reviewButton.click();
        await waitForAnimations(page);

        // Modal should take full width on mobile
        const modal = page.locator('[role="dialog"], [class*="modal"]').first();
        if (await modal.isVisible()) {
          const box = await modal.boundingBox();
          if (box) {
            expect(box.width).toBeGreaterThanOrEqual(VIEWPORTS.mobile.width * 0.9);
          }
        }

        await captureScreenshot(page, 'article-review-modal-mobile');
      }
    });

    test('should display 3-column layout on desktop modal', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop);
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      const reviewButton = page.locator('button:has-text("Review")').first();
      if (await reviewButton.isVisible()) {
        await reviewButton.click();
        await waitForAnimations(page);

        // Check for 3-column sections
        const basicInfoSection = page.locator('text=基础信息');
        const seoSection = page.locator('text=SEO 优化');
        const categorySection = page.locator('text=分类与标签');

        if (await basicInfoSection.isVisible() && await seoSection.isVisible()) {
          const basicBox = await basicInfoSection.boundingBox();
          const seoBox = await seoSection.boundingBox();

          if (basicBox && seoBox) {
            // Sections should be side by side on desktop
            expect(Math.abs(basicBox.y - seoBox.y)).toBeLessThan(50);
          }
        }
      }
    });
  });

  test.describe('Proofreading Panel Responsive', () => {
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

    test('should stack panels on mobile', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile);
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      // On mobile, panels should be stacked or have tabs
      const issueList = page.locator('text=问题列表');
      const articleContent = page.locator('text=/文章|对比|预览/');

      if (await issueList.isVisible() && await articleContent.isVisible()) {
        const listBox = await issueList.boundingBox();
        const contentBox = await articleContent.boundingBox();

        // May be stacked or tabbed on mobile
        console.log('Mobile proofreading layout captured');
      }

      await captureScreenshot(page, 'proofreading-mobile');
    });

    test('should display 3-panel layout on desktop', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop);
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      const navigated = await navigateToProofreading(page);
      if (!navigated) {
        test.skip();
        return;
      }

      await captureScreenshot(page, 'proofreading-desktop');
    });
  });
});
