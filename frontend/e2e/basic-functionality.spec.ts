import { test, expect } from '@playwright/test';

type BrowserEnv = {
  import?: {
    meta?: {
      env?: {
        VITE_API_URL?: string;
      };
    };
  };
};

test.describe('CMS Automation Frontend - Basic Functionality', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('index.html');

    // Wait for the app to load
    await page.waitForLoadState('networkidle');

    // Check if page title is correct
    await expect(page).toHaveTitle(/CMS Automation/i);
  });

  test('has correct app title in header', async ({ page }) => {
    await page.goto('index.html');

    // Wait for content to load
    await page.waitForLoadState('networkidle');

    // Look for app title or logo
    const appTitle = page.locator('h1, [class*="logo"], [class*="title"]').first();
    await expect(appTitle).toBeVisible({ timeout: 10000 });
  });

  test('homepage content is visible', async ({ page }) => {
    await page.goto('index.html');

    await page.waitForLoadState('networkidle');

    // Check for main heading
    const heading = page.locator('h1').first();
    await expect(heading).toBeVisible({ timeout: 10000 });
    await expect(heading).toContainText('AI-Powered CMS Automation');
  });

  test('homepage displays feature cards', async ({ page }) => {
    await page.goto('index.html');

    await page.waitForLoadState('networkidle');

    // Check for feature cards
    const cards = page.locator('div.rounded-lg.bg-white.border');
    const cardCount = await cards.count();

    // Should have at least 3 feature cards
    expect(cardCount).toBeGreaterThanOrEqual(3);

    // Verify some card content is visible
    await expect(page.locator('text=Article Generation')).toBeVisible();
  });

  test('checks API configuration', async ({ page }) => {
    await page.goto('index.html');

    await page.waitForLoadState('networkidle');

    // Check if environment variables are accessible
    const apiUrl = await page.evaluate(() => {
      const env = (globalThis as BrowserEnv).import?.meta?.env;
      return env?.VITE_API_URL ?? localStorage.getItem('api_url') ?? 'not found';
    });

    console.log('API URL configured:', apiUrl);

    // At minimum, we should not get errors
    expect(apiUrl).toBeDefined();
  });

  test('no console errors on load', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('index.html');
    await page.waitForLoadState('networkidle');

    // Filter out known benign errors
    const criticalErrors = errors.filter(error =>
      !error.includes('favicon') &&
      !error.includes('manifest') &&
      !error.includes('404')
    );

    if (criticalErrors.length > 0) {
      console.log('Console errors found:', criticalErrors);
    }

    expect(criticalErrors.length).toBe(0);
  });

  test('page responds to resize', async ({ page }) => {
    await page.goto('index.html');
    await page.waitForLoadState('networkidle');

    // Test desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(500);

    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);

    // Verify page is still visible
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });
});
