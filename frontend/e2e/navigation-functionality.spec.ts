import { test, expect } from '@playwright/test';

test.describe('Navigation Functionality', () => {
  test('navigation bar is visible on homepage', async ({ page }) => {
    await page.goto('index.html');
    await page.waitForLoadState('networkidle');

    // Check for navigation element
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();

    // Check for brand/logo
    await expect(page.locator('text=CMS Automation').first()).toBeVisible();
  });

  test('navigation bar contains expected links', async ({ page }) => {
    await page.goto('index.html');
    await page.waitForLoadState('networkidle');

    // Check for key navigation links
    const navLinks = [
      '首頁',
      '生成文章',
      '導入文章',
      '文章列表',
      '發佈任務',
      '設置',
    ];

    for (const linkText of navLinks) {
      const link = page.locator(`nav >> text=${linkText}`);
      await expect(link).toBeVisible({ timeout: 5000 });
    }
  });

  test('can navigate from homepage to article generator', async ({ page }) => {
    await page.goto('index.html');
    await page.waitForLoadState('networkidle');

    // Click on "生成文章" link
    await page.locator('nav >> text=生成文章').click();
    await page.waitForLoadState('networkidle');

    // Verify we're on the article generator page
    await expect(page).toHaveTitle(/生成文章/);
    await expect(page.locator('h1', { hasText: 'Article Generator' })).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'test-results/nav-to-generator.png' });
  });

  test('can navigate from homepage to articles list', async ({ page }) => {
    await page.goto('index.html');
    await page.waitForLoadState('networkidle');

    // Click on "文章列表" link
    await page.locator('nav >> text=文章列表').click();
    await page.waitForLoadState('networkidle');

    // Verify we're on the articles list page
    await expect(page).toHaveTitle(/文章列表/);

    // Take screenshot
    await page.screenshot({ path: 'test-results/nav-to-articles.png' });
  });

  test('can navigate from homepage to settings', async ({ page }) => {
    await page.goto('index.html');
    await page.waitForLoadState('networkidle');

    // Click on "設置" link
    await page.locator('nav >> text=設置').click();
    await page.waitForLoadState('networkidle');

    // Verify we're on the settings page
    await expect(page).toHaveTitle(/設置/);

    // Take screenshot
    await page.screenshot({ path: 'test-results/nav-to-settings.png' });
  });

  test('active navigation link is highlighted', async ({ page }) => {
    await page.goto('index.html#/generate');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // The "生成文章" link should be highlighted
    const activeLink = page.locator('nav >> text=生成文章');
    await expect(activeLink).toHaveClass(/bg-blue-100/);
  });

  test('navigation is persistent across pages', async ({ page }) => {
    await page.goto('index.html');
    await page.waitForLoadState('networkidle');

    // Navigate to different pages and verify nav is always visible
    const pages = ['/generate', '/articles', '/settings'];

    for (const pagePath of pages) {
      await page.goto(`index.html#${pagePath}`);
      await page.waitForLoadState('networkidle');

      // Verify navigation is still visible
      const nav = page.locator('nav');
      await expect(nav).toBeVisible();
    }
  });
});
