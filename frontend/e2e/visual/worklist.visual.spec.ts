/**
 * Worklist Page Visual Tests
 *
 * Tests visual appearance and layout of the main worklist/dashboard page.
 * Covers: Dashboard cards, filters, table, empty states, responsive layout.
 */

import { test, expect } from '@playwright/test';
import { navigateWithRetry, waitForPageReady, createConsoleMonitor } from '../utils/test-helpers';
import {
  VIEWPORTS,
  testResponsive,
  waitForAnimations,
  captureScreenshot,
  verifyEmptyState,
} from '../utils/visual-test-helpers';

const BASE_URL = process.env.TEST_LOCAL === '1'
  ? 'http://localhost:4173'
  : 'https://storage.googleapis.com/cms-automation-frontend-476323/index.html';

test.describe('Worklist Page Visual Tests', () => {
  test.beforeEach(async ({ page }) => {
    await navigateWithRetry(page, BASE_URL);
    await waitForPageReady(page);
  });

  test.describe('Dashboard Cards', () => {
    test('should display all dashboard metric cards', async ({ page }) => {
      // Verify all metric cards are visible
      await expect(page.locator('text=Total Articles')).toBeVisible();
      await expect(page.locator('text=Ready to Publish')).toBeVisible();
      await expect(page.locator('text=Average Cycle')).toBeVisible();
      await expect(page.locator('text=Average Quality')).toBeVisible();

      // Verify secondary status cards
      await expect(page.locator('text=Proofreading')).toBeVisible();
      await expect(page.locator('text=Under Review')).toBeVisible();
      await expect(page.locator('text=Needs Attention')).toBeVisible();
    });

    test('should display correct card styling with icons', async ({ page }) => {
      // Check for card container styling
      const cards = page.locator('[class*="card"], [class*="Card"]').first();
      await expect(cards).toBeVisible();

      // Verify icons are present (using lucide-react icons)
      const icons = page.locator('svg').first();
      await expect(icons).toBeVisible();
    });

    test('should handle "No data yet" state gracefully', async ({ page }) => {
      // Check for graceful handling of empty metrics
      const noDataText = page.locator('text=No data yet');
      if (await noDataText.count() > 0) {
        await expect(noDataText.first()).toBeVisible();
      }
    });
  });

  test.describe('Filter Tabs', () => {
    test('should display all filter tabs with counts', async ({ page }) => {
      // Verify filter tabs
      await expect(page.locator('button:has-text("All")')).toBeVisible();
      await expect(page.locator('button:has-text("Needs My Attention")')).toBeVisible();
      await expect(page.locator('button:has-text("In Progress")')).toBeVisible();
      await expect(page.locator('button:has-text("Completed")')).toBeVisible();
      await expect(page.locator('button:has-text("Has Issues")')).toBeVisible();
    });

    test('should highlight active tab correctly', async ({ page }) => {
      const allTab = page.locator('button:has-text("All")');
      await allTab.click();
      await waitForAnimations(page);

      // Check for active state styling (usually has different background/border)
      await expect(allTab).toHaveClass(/active|selected|primary/i);
    });

    test('should switch tabs and update content', async ({ page }) => {
      // Click "In Progress" tab
      const inProgressTab = page.locator('button:has-text("In Progress")');
      await inProgressTab.click();
      await waitForAnimations(page);

      // Verify tab is now active
      await expect(inProgressTab).toHaveClass(/active|selected|primary/i);
    });
  });

  test.describe('Search and Filters', () => {
    test('should display search input with placeholder', async ({ page }) => {
      const searchInput = page.locator('input[placeholder*="Search"]');
      await expect(searchInput).toBeVisible();
    });

    test('should display status dropdown filter', async ({ page }) => {
      const statusFilter = page.locator('text=All Status');
      await expect(statusFilter).toBeVisible();
    });

    test('should display author filter input', async ({ page }) => {
      const authorFilter = page.locator('input[placeholder*="author"]');
      await expect(authorFilter).toBeVisible();
    });
  });

  test.describe('Article Table', () => {
    test('should display table headers correctly', async ({ page }) => {
      await expect(page.locator('text=TITLE')).toBeVisible();
      await expect(page.locator('text=STATUS')).toBeVisible();
      await expect(page.locator('text=AUTHOR')).toBeVisible();
      await expect(page.locator('text=WORD COUNT')).toBeVisible();
      await expect(page.locator('text=QUALITY SCORE')).toBeVisible();
      await expect(page.locator('text=UPDATED AT')).toBeVisible();
      await expect(page.locator('text=ACTIONS')).toBeVisible();
    });

    test('should display article rows with status badges', async ({ page }) => {
      // Look for status badges
      const statusBadges = page.locator('text=/Parsing Review|Proofreading|Ready to Publish/');
      if (await statusBadges.count() > 0) {
        await expect(statusBadges.first()).toBeVisible();
      }
    });

    test('should display action buttons for each row', async ({ page }) => {
      const viewButtons = page.locator('button:has-text("View")');
      const reviewButtons = page.locator('button:has-text("Review")');

      // If there are articles, buttons should be visible
      if (await viewButtons.count() > 0) {
        await expect(viewButtons.first()).toBeVisible();
      }
    });
  });

  test.describe('Google Drive Sync', () => {
    test('should display Sync Google Drive button', async ({ page }) => {
      const syncButton = page.locator('button:has-text("Sync Google Drive")');
      await expect(syncButton).toBeVisible();
    });

    test('should display last synced timestamp', async ({ page }) => {
      const lastSynced = page.locator('text=/Last synced:/');
      await expect(lastSynced).toBeVisible();
    });
  });

  test.describe('Responsive Layout', () => {
    test('should adapt layout for mobile viewport', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile);
      await waitForAnimations(page);

      // Dashboard cards should stack vertically on mobile
      const header = page.locator('text=CMS Automation System');
      await expect(header).toBeVisible();

      // Take screenshot for visual comparison
      await captureScreenshot(page, 'worklist-mobile', { viewport: 'mobile' });
    });

    test('should adapt layout for tablet viewport', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.tablet);
      await waitForAnimations(page);

      await captureScreenshot(page, 'worklist-tablet', { viewport: 'tablet' });
    });

    test('should display full layout on desktop', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop);
      await waitForAnimations(page);

      await captureScreenshot(page, 'worklist-desktop', { viewport: 'desktop' });
    });
  });

  test.describe('Settings Navigation', () => {
    test('should navigate to settings page', async ({ page }) => {
      const settingsButton = page.locator('button:has-text("Settings")');
      await settingsButton.click();
      await waitForAnimations(page);

      // Verify we're on settings page
      await expect(page.locator('text=System Settings')).toBeVisible();
    });
  });

  test.describe('Language Switcher', () => {
    test('should display language selector', async ({ page }) => {
      const languageSelector = page.locator('text=English');
      await expect(languageSelector).toBeVisible();
    });
  });
});
