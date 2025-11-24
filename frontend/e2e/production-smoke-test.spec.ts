/**
 * Production Environment Smoke Test
 * Tests the deployed application on GCS against the deployed backend
 */
import { test, expect } from '@playwright/test';
import type { Request, Response, ConsoleMessage, Page } from '@playwright/test';

type ProdWindow = typeof window & {
  VITE_API_URL?: string;
  __ENV__?: {
    VITE_API_URL?: string;
  };
};

const PRODUCTION_FRONTEND = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/app.html';
const PRODUCTION_BACKEND = 'https://cms-automation-backend-ufk65ob4ea-uc.a.run.app';

test.describe('Production Environment Smoke Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to production frontend
    await page.goto(PRODUCTION_FRONTEND);
  });

  test('should load the application with proper styling', async ({ page }) => {
    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Take a screenshot for visual verification
    await page.screenshot({ path: 'test-results/production-home.png', fullPage: true });

    // Check that CSS is loaded - look for styled elements
    const header = page.locator('header, [role="banner"], h1, .header').first();
    await expect(header).toBeVisible({ timeout: 10000 });

    // Verify the page has color (not just black and white)
    const body = page.locator('body');
    const bgColor = await body.evaluate((el) => window.getComputedStyle(el).backgroundColor);
    console.log('Body background color:', bgColor);

    // Check if any stylesheet is loaded
    const stylesheets = await page.evaluate(() => {
      return Array.from(document.styleSheets).map(sheet => ({
        href: sheet.href,
        rules: sheet.cssRules?.length || 0
      }));
    });
    console.log('Loaded stylesheets:', JSON.stringify(stylesheets, null, 2));
    expect(stylesheets.length).toBeGreaterThan(0);
  });

  test('should navigate to settings page', async ({ page }) => {
    // Find and click the settings link/button
    const settingsLink = page.locator('a[href*="settings"], button:has-text("設置"), a:has-text("設置"), [href="#/settings"]').first();

    // Wait for navigation element to be visible
    await page.waitForSelector('nav, header, [role="navigation"]', { timeout: 10000 });

    await settingsLink.click();
    await page.waitForLoadState('networkidle');

    // Take screenshot of settings page
    await page.screenshot({ path: 'test-results/production-settings.png', fullPage: true });

    // Check for error messages
    const errorText = await page.locator('body').textContent();
    console.log('Settings page content:', errorText);

    // Look for specific error indicators
    const has403Error = errorText?.includes('403') || errorText?.includes('Request failed');
    const hasErrorIcon = await page.locator('[class*="error"], [role="alert"]').count() > 0;

    if (has403Error || hasErrorIcon) {
      console.error('❌ Settings page shows error');

      // Check network requests
      page.on('request', (request: Request) => {
        if (request.url().includes('settings')) {
          console.log(`Settings request: ${request.method()} ${request.url()}`);
        }
      });
      page.on('response', async (response: Response) => {
        if (response.url().includes('settings')) {
          console.log(`Settings API: ${response.status()} ${response.url()}`);
          const headers = response.headers();
          console.log('Response headers:', JSON.stringify(headers, null, 2));
        }
      });
    }

    expect(has403Error).toBe(false);
  });

  test('should successfully call settings API', async ({ request }) => {
    // Test the API directly with correct origin
    const response = await request.get(`${PRODUCTION_BACKEND}/v1/settings`, {
      headers: {
        'Origin': 'https://storage.googleapis.com'
      }
    });

    console.log('Settings API status:', response.status());
    console.log('Settings API headers:', JSON.stringify(await response.headers(), null, 2));

    const body = await response.text();
    console.log('Settings API response:', body);

    expect(response.status()).toBe(200);
  });

  test('should check all navigation links', async ({ page }) => {
    await page.waitForSelector('nav, [role="navigation"]', { timeout: 10000 });

    // Get all navigation links
    const navLinks = await page.locator('nav a, [role="navigation"] a').all();
    console.log(`Found ${navLinks.length} navigation links`);

    for (const link of navLinks) {
      const href = await link.getAttribute('href');
      const text = await link.textContent();
      console.log(`Nav link: "${text}" -> ${href}`);
    }
  });

  test('should verify API connectivity', async ({ request }) => {
    // Test backend health endpoint
    const healthResponse = await request.get(`${PRODUCTION_BACKEND}/health`);
    expect(healthResponse.status()).toBe(200);

    const health = await healthResponse.json();
    console.log('Backend health:', health);
    expect(health.status).toBe('healthy');
  });

  test('should capture console errors', async ({ page }) => {
    const consoleMessages: string[] = [];
    const errors: string[] = [];

    page.on('console', (msg: ConsoleMessage) => {
      const text = msg.text();
      consoleMessages.push(`[${msg.type()}] ${text}`);
      if (msg.type() === 'error') {
        errors.push(text);
      }
    });

    page.on('pageerror', (error: Error) => {
      errors.push(`Page error: ${error.message}`);
    });

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Wait for any async operations

    console.log('Console messages:', consoleMessages.join('\n'));

    if (errors.length > 0) {
      console.error('❌ Errors found:', errors.join('\n'));
    }

    // Log but don't fail on console errors (for now, just for investigation)
    errors.forEach(error => console.error('Console error:', error));
  });

  test('should check frontend environment configuration', async ({ page }) => {
    // Check what API URL the frontend is configured to use
    const apiUrl = await page.evaluate<string>(() => {
      // Try to access environment variables or config
      const prodWindow = window as ProdWindow;
      return prodWindow.VITE_API_URL ?? prodWindow.__ENV__?.VITE_API_URL ?? 'not found';
    });

    console.log('Frontend API URL configuration:', apiUrl);
  });
});
