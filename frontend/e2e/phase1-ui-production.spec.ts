/**
 * Phase 1 UI Production E2E Tests
 *
 * Tests the deployed Phase 1 UI in production environment:
 * - Production URL: https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html
 * - Internationalization (Chinese/English)
 * - Phase1Header navigation
 * - Route functionality
 * - Responsive design
 * - Accessibility
 */

import { test, expect } from '@playwright/test';

const PRODUCTION_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

test.describe('Phase 1 UI Production - Core Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage to start fresh
    await page.goto(PRODUCTION_URL);
    await page.evaluate(() => localStorage.clear());
  });

  test('should load production site and display Phase1Header', async ({ page }) => {
    await page.goto(PRODUCTION_URL);
    // Use domcontentloaded instead of networkidle to avoid API timeout issues
    await page.waitForLoadState('domcontentloaded');

    // Wait for the header to be visible
    await page.waitForSelector('header', { timeout: 10000 });

    // Check header is visible
    const header = page.locator('header');
    await expect(header).toBeVisible();

    // Check app name contains CMS (either Chinese or English)
    const appName = header.locator('h1');
    await expect(appName).toBeVisible();
    const appNameText = await appName.textContent();
    expect(appNameText).toMatch(/CMS/);

    // Check language switcher
    const languageSwitcher = header.locator('select').first();
    await expect(languageSwitcher).toBeVisible();

    console.log('✅ Production site loaded successfully with Phase1Header');
  });

  test('should navigate to settings page in production', async ({ page }) => {
    await page.goto(PRODUCTION_URL);
    await page.waitForLoadState('domcontentloaded');

    // Wait for header and settings button
    await page.waitForSelector('header', { timeout: 10000 });

    // Click settings button (looking for either Chinese or English text)
    const settingsButton = page.locator('button:has-text("設定"), button:has-text("Settings")').first();
    await expect(settingsButton).toBeVisible();
    await settingsButton.click();

    // Wait for URL change (hash routing)
    await page.waitForTimeout(1000);

    // Verify URL contains settings
    const url = page.url();
    expect(url).toContain('#/settings');

    // Verify settings page title is visible
    await page.waitForSelector('h1:has-text("系統設定"), h1:has-text("System Settings")', { timeout: 5000 });

    console.log('✅ Navigation to settings page works in production');
  });

  test('should navigate back to worklist from settings', async ({ page }) => {
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('domcontentloaded');

    // Wait for header
    await page.waitForSelector('header', { timeout: 10000 });

    // Click worklist button
    const worklistButton = page.locator('button:has-text("工作清單"), button:has-text("Worklist")').first();
    await expect(worklistButton).toBeVisible();
    await worklistButton.click();

    // Wait for navigation
    await page.waitForTimeout(1000);

    // Verify URL (should be root or /worklist)
    const url = page.url();
    expect(url).toMatch(/(#\/$|#\/worklist)/);

    console.log('✅ Navigation back to worklist works in production');
  });
});

test.describe('Phase 1 UI Production - Internationalization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(PRODUCTION_URL);
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForLoadState('domcontentloaded');
  });

  test('should default to Chinese language in production', async ({ page }) => {
    // Wait for page to load
    await page.waitForSelector('header', { timeout: 10000 });

    // Check that default language is Chinese
    const languageSwitcher = page.locator('select').first();
    await expect(languageSwitcher).toBeVisible();

    const selectedValue = await languageSwitcher.inputValue();
    expect(selectedValue).toBe('zh-TW');

    // Check Chinese text is displayed in app name
    const appName = page.locator('h1');
    const appNameText = await appName.textContent();
    expect(appNameText).toContain('CMS 自動化系統');

    console.log('✅ Production site defaults to Chinese');
  });

  test('should switch to English language in production', async ({ page }) => {
    // Wait for page to load
    await page.waitForSelector('header', { timeout: 10000 });

    // Switch to English
    const languageSwitcher = page.locator('select').first();
    await languageSwitcher.selectOption('en-US');

    // Wait for language change
    await page.waitForTimeout(1000);

    // Check English text is displayed
    const appName = page.locator('h1');
    const appNameText = await appName.textContent();
    expect(appNameText).toContain('CMS Automation System');

    // Check Settings button shows English text
    const settingsButton = page.locator('button:has-text("Settings")');
    await expect(settingsButton).toBeVisible();

    console.log('✅ Language switching to English works in production');
  });

  test('should persist language preference in production', async ({ page }) => {
    // Wait for page to load
    await page.waitForSelector('header', { timeout: 10000 });

    // Switch to English
    const languageSwitcher = page.locator('select').first();
    await languageSwitcher.selectOption('en-US');
    await page.waitForTimeout(500);

    // Reload page
    await page.reload();
    await page.waitForLoadState('domcontentloaded');
    await page.waitForSelector('header', { timeout: 10000 });

    // Check that English is still selected
    const selectedValue = await languageSwitcher.inputValue();
    expect(selectedValue).toBe('en-US');

    const appName = page.locator('h1');
    const appNameText = await appName.textContent();
    expect(appNameText).toContain('CMS Automation System');

    console.log('✅ Language preference persists after reload in production');
  });
});

test.describe('Phase 1 UI Production - Responsive Design', () => {
  test('should work on mobile viewport in production', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(PRODUCTION_URL);
    await page.waitForLoadState('domcontentloaded');

    // Wait for header
    await page.waitForSelector('header', { timeout: 10000 });

    // Check header is visible
    const header = page.locator('header');
    await expect(header).toBeVisible();

    // Check language switcher is still functional
    const languageSwitcher = page.locator('select').first();
    await expect(languageSwitcher).toBeVisible();

    // Check settings button (icon should be visible even if text is hidden)
    const settingsButton = page.locator('button').filter({ has: page.locator('svg') }).first();
    await expect(settingsButton).toBeVisible();

    console.log('✅ Production site works on mobile viewport');
  });

  test('should work on tablet viewport in production', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(PRODUCTION_URL);
    await page.waitForLoadState('domcontentloaded');

    // Wait for header
    await page.waitForSelector('header', { timeout: 10000 });

    // Check all elements are visible
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('select').first()).toBeVisible();

    console.log('✅ Production site works on tablet viewport');
  });
});

test.describe('Phase 1 UI Production - Accessibility', () => {
  test('should have proper ARIA labels in production', async ({ page }) => {
    await page.goto(PRODUCTION_URL);
    await page.waitForLoadState('domcontentloaded');

    // Wait for header
    await page.waitForSelector('header', { timeout: 10000 });

    // Check language switcher has aria-label
    const languageSwitcher = page.locator('select').first();
    const ariaLabel = await languageSwitcher.getAttribute('aria-label');
    expect(ariaLabel).toBeTruthy();

    // Check buttons have proper labels
    const settingsButton = page.locator('button:has-text("設定"), button:has-text("Settings")').first();
    const buttonAriaLabel = await settingsButton.getAttribute('aria-label');
    expect(buttonAriaLabel).toBeTruthy();

    console.log('✅ Production site has proper ARIA labels');
  });

  test('should be keyboard navigable in production', async ({ page }) => {
    await page.goto(PRODUCTION_URL);
    await page.waitForLoadState('domcontentloaded');

    // Wait for header
    await page.waitForSelector('header', { timeout: 10000 });

    // Tab through elements
    await page.keyboard.press('Tab'); // Language switcher
    await page.keyboard.press('Tab'); // Settings button

    // Check focus is on settings button
    const settingsButton = page.locator('button:has-text("設定"), button:has-text("Settings")').first();
    await expect(settingsButton).toBeFocused();

    // Press Enter to navigate
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1000);

    // Verify navigation occurred
    const url = page.url();
    expect(url).toContain('#/settings');

    console.log('✅ Production site is keyboard navigable');
  });
});

test.describe('Phase 1 UI Production - Visual Verification', () => {
  test('should render all UI elements correctly', async ({ page }) => {
    await page.goto(PRODUCTION_URL);
    await page.waitForLoadState('domcontentloaded');

    // Wait for header
    await page.waitForSelector('header', { timeout: 10000 });

    // Take screenshot for visual verification
    await page.screenshot({ path: 'test-results/phase1-production-homepage.png', fullPage: true });

    // Verify key elements are present
    const header = page.locator('header');
    await expect(header).toBeVisible();

    const logo = header.locator('svg, img').first();
    await expect(logo).toBeVisible();

    const h1 = header.locator('h1');
    await expect(h1).toBeVisible();

    const languageSelector = header.locator('select').first();
    await expect(languageSelector).toBeVisible();

    const settingsButton = header.locator('button').last();
    await expect(settingsButton).toBeVisible();

    console.log('✅ All UI elements rendered correctly in production');
  });

  test('should render settings page correctly', async ({ page }) => {
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('domcontentloaded');

    // Wait for settings page
    await page.waitForSelector('h1:has-text("系統設定"), h1:has-text("System Settings")', { timeout: 10000 });

    // Take screenshot
    await page.screenshot({ path: 'test-results/phase1-production-settings.png', fullPage: true });

    // Verify worklist button is visible on settings page
    const worklistButton = page.locator('button:has-text("工作清單"), button:has-text("Worklist")');
    await expect(worklistButton).toBeVisible();

    console.log('✅ Settings page rendered correctly in production');
  });
});

test.describe('Phase 1 UI Production - Performance', () => {
  test('should load within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(PRODUCTION_URL);
    await page.waitForLoadState('domcontentloaded');

    // Wait for critical UI elements
    await page.waitForSelector('header', { timeout: 10000 });

    const loadTime = Date.now() - startTime;

    // Should load within 10 seconds (generous for production)
    expect(loadTime).toBeLessThan(10000);

    console.log(`✅ Production site loaded in ${loadTime}ms`);
  });

  test('should have no console errors on load', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto(PRODUCTION_URL);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForSelector('header', { timeout: 10000 });

    // Allow for minor errors but log them
    if (errors.length > 0) {
      console.log('⚠️  Console errors detected:', errors);
    }

    // Critical errors should not exist (you can adjust this based on your criteria)
    const criticalErrors = errors.filter(err =>
      !err.includes('favicon') && // Ignore favicon errors
      !err.includes('404') // Ignore 404s from API calls during load
    );

    expect(criticalErrors.length).toBe(0);

    console.log('✅ No critical console errors in production');
  });
});
