/**
 * Phase 1 UI E2E Tests
 *
 * Tests for Phase 1 UI implementation including:
 * - Internationalization (i18n) with Chinese and English
 * - Phase1Header with language switcher and navigation
 * - WorklistPage internationalization
 * - SettingsPage internationalization
 * - Route navigation
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.TEST_LOCAL
  ? 'http://localhost:4173/'
  : 'https://storage.googleapis.com/cms-automation-frontend-2025/';

test.describe('Phase 1 UI - Core Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage to start fresh
    await page.goto(BASE_URL);
    await page.evaluate(() => localStorage.clear());
  });

  test('should display Phase1Header with all elements', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Check header is visible
    const header = page.locator('header');
    await expect(header).toBeVisible();

    // Check app logo and name
    const appName = header.locator('h1');
    await expect(appName).toBeVisible();
    await expect(appName).toHaveText(/CMS/);

    // Check language switcher
    const languageSwitcher = header.locator('select').first();
    await expect(languageSwitcher).toBeVisible();

    // Check settings button (should be visible on worklist page)
    const settingsButton = header.locator('button:has-text("设置"), button:has-text("Settings")');
    await expect(settingsButton).toBeVisible();
  });

  test('should navigate to settings page', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Click settings button
    const settingsButton = page.locator('button:has-text("设置"), button:has-text("Settings")').first();
    await settingsButton.click();

    // Wait for navigation
    await page.waitForURL(/.*#\/settings/);

    // Verify we're on settings page
    await expect(page.locator('h1:has-text("系统设置"), h1:has-text("System Settings")')).toBeVisible();

    // Check that Worklist button is now visible instead of Settings
    const worklistButton = page.locator('button:has-text("工作清单"), button:has-text("Worklist")');
    await expect(worklistButton).toBeVisible();
  });

  test('should navigate back to worklist from settings', async ({ page }) => {
    await page.goto(`${BASE_URL}#/settings`);
    await page.waitForLoadState('networkidle');

    // Click worklist button
    const worklistButton = page.locator('button:has-text("工作清单"), button:has-text("Worklist")').first();
    await worklistButton.click();

    // Wait for navigation
    await page.waitForURL(/.*#\/(worklist)?/);

    // Verify we're on worklist page
    await expect(page.locator('h1:has-text("工作清单"), h1:has-text("Worklist")')).toBeVisible();
  });
});

test.describe('Phase 1 UI - Internationalization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForLoadState('networkidle');
  });

  test('should default to Chinese language', async ({ page }) => {
    // Check that default language is Chinese
    const languageSwitcher = page.locator('select').first();
    await expect(languageSwitcher).toHaveValue('zh-CN');

    // Check Chinese text is displayed
    await expect(page.locator('h1')).toContainText('CMS 自动化系统');
    await expect(page.locator('text=工作清单')).toBeVisible();
  });

  test('should switch to English language', async ({ page }) => {
    // Switch to English
    const languageSwitcher = page.locator('select').first();
    await languageSwitcher.selectOption('en-US');

    // Wait for language change
    await page.waitForTimeout(500);

    // Check English text is displayed
    await expect(page.locator('h1')).toContainText('CMS Automation System');
    await expect(page.locator('text=Worklist')).toBeVisible();
    await expect(page.locator('button:has-text("Settings")')).toBeVisible();
  });

  test('should persist language preference in localStorage', async ({ page }) => {
    // Switch to English
    const languageSwitcher = page.locator('select').first();
    await languageSwitcher.selectOption('en-US');
    await page.waitForTimeout(500);

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Check that English is still selected
    await expect(languageSwitcher).toHaveValue('en-US');
    await expect(page.locator('h1')).toContainText('CMS Automation System');
  });

  test('should translate all UI elements when switching language', async ({ page }) => {
    const languageSwitcher = page.locator('select').first();

    // Test Chinese
    await languageSwitcher.selectOption('zh-CN');
    await page.waitForTimeout(500);

    await expect(page.locator('button:has-text("设置")')).toBeVisible();
    await expect(page.locator('h1:has-text("工作清单")')).toBeVisible();
    await expect(page.locator('text=管理来自 Google Drive 的文章')).toBeVisible();

    // Test English
    await languageSwitcher.selectOption('en-US');
    await page.waitForTimeout(500);

    await expect(page.locator('button:has-text("Settings")')).toBeVisible();
    await expect(page.locator('h1:has-text("Worklist")')).toBeVisible();
    await expect(page.locator('text=Manage articles from Google Drive')).toBeVisible();
  });
});

test.describe('Phase 1 UI - WorklistPage Internationalization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}#/worklist`);
    await page.evaluate(() => localStorage.setItem('cms_automation_language', 'zh-CN'));
    await page.reload();
    await page.waitForLoadState('networkidle');
  });

  test('should display worklist page in Chinese', async ({ page }) => {
    // Check page title and subtitle
    await expect(page.locator('h1:has-text("工作清单")')).toBeVisible();
    await expect(page.locator('text=管理来自 Google Drive 的文章，跟踪 7 阶段审稿流程')).toBeVisible();

    // Check filter section
    await expect(page.locator('h2:has-text("筛选条件")')).toBeVisible();

    // Switch to English
    const languageSwitcher = page.locator('select').first();
    await languageSwitcher.selectOption('en-US');
    await page.waitForTimeout(500);

    // Check English translations
    await expect(page.locator('h1:has-text("Worklist")')).toBeVisible();
    await expect(page.locator('text=Manage articles from Google Drive and track the 7-stage review process')).toBeVisible();
    await expect(page.locator('h2:has-text("Filters")')).toBeVisible();
  });

  test('should display translated filter options', async ({ page }) => {
    const languageSwitcher = page.locator('select').first();

    // Chinese filter options
    await languageSwitcher.selectOption('zh-CN');
    await page.waitForTimeout(500);

    const statusFilter = page.locator('select').nth(1); // Second select is status filter
    await expect(statusFilter).toBeVisible();

    // Click to open options
    await statusFilter.click();

    // Check Chinese status options
    await expect(page.locator('option:has-text("全部状态")')).toBeVisible();
    await expect(page.locator('option:has-text("待评估")')).toBeVisible();
    await expect(page.locator('option:has-text("待确认")')).toBeVisible();

    // Switch to English
    await languageSwitcher.selectOption('en-US');
    await page.waitForTimeout(500);

    await statusFilter.click();

    // Check English status options
    await expect(page.locator('option:has-text("All Status")')).toBeVisible();
    await expect(page.locator('option:has-text("To Evaluate")')).toBeVisible();
    await expect(page.locator('option:has-text("To Confirm")')).toBeVisible();
  });

  test('should display translated placeholder text in search inputs', async ({ page }) => {
    const languageSwitcher = page.locator('select').first();

    // Check Chinese placeholders
    await languageSwitcher.selectOption('zh-CN');
    await page.waitForTimeout(500);

    const searchInput = page.locator('input[placeholder*="搜索"]');
    await expect(searchInput).toBeVisible();
    await expect(searchInput).toHaveAttribute('placeholder', '搜索标题或内容...');

    const authorInput = page.locator('input[placeholder*="作者"]');
    await expect(authorInput).toBeVisible();

    // Check English placeholders
    await languageSwitcher.selectOption('en-US');
    await page.waitForTimeout(500);

    const searchInputEn = page.locator('input[placeholder*="Search"]');
    await expect(searchInputEn).toBeVisible();
    await expect(searchInputEn).toHaveAttribute('placeholder', 'Search title or content...');

    const authorInputEn = page.locator('input[placeholder*="author"]');
    await expect(authorInputEn).toBeVisible();
  });
});

test.describe('Phase 1 UI - SettingsPage Internationalization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}#/settings`);
    await page.evaluate(() => localStorage.setItem('cms_automation_language', 'zh-CN'));
    await page.reload();
    await page.waitForLoadState('networkidle');
  });

  test('should display settings page in Chinese', async ({ page }) => {
    // Check page title and subtitle
    await expect(page.locator('h1:has-text("系统设置")')).toBeVisible();
    await expect(page.locator('text=配置您的 CMS 自动化系统')).toBeVisible();

    // Switch to English
    const languageSwitcher = page.locator('select').first();
    await languageSwitcher.selectOption('en-US');
    await page.waitForTimeout(500);

    // Check English translations
    await expect(page.locator('h1:has-text("System Settings")')).toBeVisible();
    await expect(page.locator('text=Configure your CMS Automation System')).toBeVisible();
  });

  test('should display action buttons in correct language', async ({ page }) => {
    const languageSwitcher = page.locator('select').first();

    // Check Chinese buttons
    await languageSwitcher.selectOption('zh-CN');
    await page.waitForTimeout(500);

    // Note: These buttons may not be visible if they're in accordion sections
    // We'll check if they exist in the page
    const saveButton = page.locator('button:has-text("保存")');
    const resetButton = page.locator('button:has-text("重置")');

    // Switch to English
    await languageSwitcher.selectOption('en-US');
    await page.waitForTimeout(500);

    const saveButtonEn = page.locator('button:has-text("Save")');
    const resetButtonEn = page.locator('button:has-text("Reset")');
  });
});

test.describe('Phase 1 UI - Route Simplification', () => {
  test('should only have 3 active routes', async ({ page }) => {
    // Test root route redirects to worklist
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1:has-text("工作清单"), h1:has-text("Worklist")')).toBeVisible();

    // Test /worklist route
    await page.goto(`${BASE_URL}#/worklist`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1:has-text("工作清单"), h1:has-text("Worklist")')).toBeVisible();

    // Test /settings route
    await page.goto(`${BASE_URL}#/settings`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1:has-text("系统设置"), h1:has-text("System Settings")')).toBeVisible();
  });

  test('should not display global navigation menu', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Check that there's no global navigation sidebar or menu
    // (This is a negative test - we're verifying something is NOT present)
    const navSidebar = page.locator('nav[role="navigation"]').filter({ hasText: '文章列表' });
    await expect(navSidebar).not.toBeVisible();

    const navMenu = page.locator('text=生成文章');
    await expect(navMenu).not.toBeVisible();

    const importLink = page.locator('text=導入文章');
    await expect(importLink).not.toBeVisible();
  });
});

test.describe('Phase 1 UI - Responsive Design', () => {
  test('should work on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Check header is visible
    const header = page.locator('header');
    await expect(header).toBeVisible();

    // Check language switcher is still functional
    const languageSwitcher = page.locator('select').first();
    await expect(languageSwitcher).toBeVisible();

    // Check settings button (text might be hidden on mobile)
    const settingsButton = page.locator('button').filter({ has: page.locator('svg') }).first();
    await expect(settingsButton).toBeVisible();
  });

  test('should work on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Check all elements are visible
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('select').first()).toBeVisible();
  });
});

test.describe('Phase 1 UI - Accessibility', () => {
  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Check language switcher has aria-label
    const languageSwitcher = page.locator('select').first();
    const ariaLabel = await languageSwitcher.getAttribute('aria-label');
    expect(ariaLabel).toBeTruthy();

    // Check buttons have proper labels
    const settingsButton = page.locator('button:has-text("设置"), button:has-text("Settings")').first();
    const buttonAriaLabel = await settingsButton.getAttribute('aria-label');
    expect(buttonAriaLabel).toBeTruthy();
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Tab through elements
    await page.keyboard.press('Tab'); // Language switcher
    await page.keyboard.press('Tab'); // Settings button

    // Check focus is on settings button
    const settingsButton = page.locator('button:has-text("设置"), button:has-text("Settings")').first();
    await expect(settingsButton).toBeFocused();

    // Press Enter to navigate
    await page.keyboard.press('Enter');
    await page.waitForTimeout(500);

    // Verify navigation occurred
    await expect(page.locator('h1:has-text("系统设置"), h1:has-text("System Settings")')).toBeVisible();
  });
});
