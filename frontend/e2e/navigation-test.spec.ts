import { test, expect } from '@playwright/test';

test.describe('Navigation and Routes', () => {
  test('can access article generator page directly', async ({ page }) => {
    // Use hash routing
    await page.goto('index.html#/generate');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Check page title
    await expect(page).toHaveTitle(/生成文章/);

    // Take screenshot
    await page.screenshot({ path: 'test-results/generate-page.png' });
  });

  test('can access articles list page directly', async ({ page }) => {
    await page.goto('index.html#/articles');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Check page title
    await expect(page).toHaveTitle(/文章列表/);

    // Take screenshot
    await page.screenshot({ path: 'test-results/articles-page.png' });
  });

  test('can access settings page directly', async ({ page }) => {
    await page.goto('index.html#/settings');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Check page title
    await expect(page).toHaveTitle(/設置/);

    // Take screenshot
    await page.screenshot({ path: 'test-results/settings-page.png' });
  });
});
