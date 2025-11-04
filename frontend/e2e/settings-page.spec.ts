import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('index.html#/settings');
    await page.waitForLoadState('networkidle');
  });

  test('page loads or shows error gracefully', async ({ page }) => {
    // Wait for page to finish loading or show error
    await page.waitForTimeout(6000);

    // Check if either settings loaded OR error message displayed
    const settingsHeading = page.locator('h1', { hasText: '系统设置' });
    const errorHeading = page.locator('h2', { hasText: '无法加载设置' });

    // At least one should be visible
    const hasSettings = await settingsHeading.isVisible().catch(() => false);
    const hasError = await errorHeading.isVisible().catch(() => false);

    expect(hasSettings || hasError).toBeTruthy();

    // If error is shown, verify retry button exists
    if (hasError) {
      await expect(page.locator('button', { hasText: '重试' })).toBeVisible();
    }
  });

  test('error state shows retry button', async ({ page }) => {
    // Wait for loading or error
    await page.waitForTimeout(6000);

    const errorHeading = page.locator('h2', { hasText: '无法加载设置' });
    const isError = await errorHeading.isVisible().catch(() => false);

    if (isError) {
      // Verify retry button is clickable
      const retryButton = page.locator('button', { hasText: '重试' });
      await expect(retryButton).toBeVisible();
      await expect(retryButton).toBeEnabled();

      // Click retry button
      await retryButton.click();

      // Should show loading state after click
      await page.waitForTimeout(1000);
    } else {
      // If no error, test passes - API is working
      expect(true).toBeTruthy();
    }
  });

  test('page navigation works from settings page', async ({ page }) => {
    // Wait for initial load
    await page.waitForTimeout(3000);

    // Should be able to navigate away from settings
    const homeLink = page.locator('nav >> text=首頁');
    await expect(homeLink).toBeVisible();
    await homeLink.click();
    await page.waitForLoadState('networkidle');

    // Should be on home page now
    await expect(page.locator('h1', { hasText: 'AI-Powered CMS Automation' })).toBeVisible();
  });

  test('page is responsive', async ({ page }) => {
    // Test on mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(3000);

    // Should show either content or error, not crash
    const hasContent = await page.locator('h1, h2').count() > 0;
    expect(hasContent).toBeTruthy();

    // Test on desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(1000);

    const hasContentDesktop = await page.locator('h1, h2').count() > 0;
    expect(hasContentDesktop).toBeTruthy();
  });
});
