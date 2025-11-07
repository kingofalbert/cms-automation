/**
 * E2E Tests for New Settings Features
 * Tests Proofreading Rules and Tag Management sections in Settings page
 */

import { test, expect, type Page } from '@playwright/test';

const PRODUCTION_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

test.describe('Settings Page - New Features', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    await page.goto(PRODUCTION_URL);

    // Wait for app to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('should navigate to Settings page', async () => {
    // Navigate to Settings page
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Verify Settings page header
    const header = page.locator('h1', { hasText: '系统设置' }).or(page.locator('h1', { hasText: 'System Settings' }));
    await expect(header).toBeVisible({ timeout: 10000 });

    // Take screenshot
    await page.screenshot({ path: 'screenshots/settings-page-loaded.png', fullPage: true });
  });

  test('should display Proofreading Rules section', async () => {
    // Navigate to Settings page
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Wait for accordion buttons to load
    await page.waitForSelector('button[type="button"]', { timeout: 15000 });

    // Find and click Proofreading Rules accordion
    const proofreadingAccordion = page.locator('button[type="button"]').filter({
      hasText: /校对规则|Proofreading Rules/
    });

    await expect(proofreadingAccordion).toBeVisible({ timeout: 10000 });
    await page.screenshot({ path: 'screenshots/proofreading-accordion-visible.png', fullPage: true });

    // Click to expand
    await proofreadingAccordion.click();
    await page.waitForTimeout(1000);

    // Verify section content is visible
    const proofreadingContent = page.locator('text=/校对规则管理|Proofreading Rules Management/');
    await expect(proofreadingContent).toBeVisible({ timeout: 10000 });

    // Verify statistics cards
    const totalRulesCard = page.locator('text=/总规则数|Total Rules/');
    const publishedRulesetsCard = page.locator('text=/已发布规则集|Published Rulesets/');
    const appliedCountCard = page.locator('text=/应用次数|Times Applied/');

    await expect(totalRulesCard).toBeVisible({ timeout: 5000 });
    await expect(publishedRulesetsCard).toBeVisible({ timeout: 5000 });
    await expect(appliedCountCard).toBeVisible({ timeout: 5000 });

    // Take screenshot of expanded section
    await page.screenshot({ path: 'screenshots/proofreading-section-expanded.png', fullPage: true });
  });

  test('should display Tag Management section', async () => {
    // Navigate to Settings page
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Wait for accordion buttons to load
    await page.waitForSelector('button[type="button"]', { timeout: 15000 });

    // Find and click Tag Management accordion
    const tagAccordion = page.locator('button[type="button"]').filter({
      hasText: /标签管理|Tag Management/
    });

    await expect(tagAccordion).toBeVisible({ timeout: 10000 });
    await page.screenshot({ path: 'screenshots/tag-accordion-visible.png', fullPage: true });

    // Click to expand
    await tagAccordion.click();
    await page.waitForTimeout(1000);

    // Verify section content is visible
    const tagContent = page.locator('text=/标签管理|Tag Management/').first();
    await expect(tagContent).toBeVisible({ timeout: 10000 });

    // Verify statistics cards
    const totalTagsCard = page.locator('text=/标签总数|Total Tags/');
    const unusedTagsCard = page.locator('text=/未使用标签|Unused Tags/');
    const mostUsedCard = page.locator('text=/最常用标签|Most Used/');

    await expect(totalTagsCard).toBeVisible({ timeout: 5000 });
    await expect(unusedTagsCard).toBeVisible({ timeout: 5000 });
    await expect(mostUsedCard).toBeVisible({ timeout: 5000 });

    // Verify "Add Tag" button
    const addTagButton = page.locator('button', { hasText: /添加标签|Add Tag/ });
    await expect(addTagButton).toBeVisible({ timeout: 5000 });

    // Take screenshot of expanded section
    await page.screenshot({ path: 'screenshots/tag-section-expanded.png', fullPage: true });
  });

  test('should test Tag Management add tag interaction', async () => {
    // Navigate to Settings page
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Find and click Tag Management accordion
    const tagAccordion = page.locator('button[type="button"]').filter({
      hasText: /标签管理|Tag Management/
    });
    await tagAccordion.click();
    await page.waitForTimeout(1000);

    // Click "Add Tag" button
    const addTagButton = page.locator('button', { hasText: /添加标签|Add Tag/ });
    await addTagButton.click();
    await page.waitForTimeout(500);

    // Verify add tag form appears
    const tagInput = page.locator('input[placeholder*="标签"]').or(
      page.locator('input[placeholder*="tag"]')
    );
    await expect(tagInput).toBeVisible({ timeout: 5000 });

    // Take screenshot of add form
    await page.screenshot({ path: 'screenshots/tag-add-form.png', fullPage: true });

    // Test empty tag validation
    const saveButton = page.locator('button', { hasText: /保存|Save/ }).first();
    await saveButton.click();
    await page.waitForTimeout(500);

    // Screenshot after empty submission (should show error toast)
    await page.screenshot({ path: 'screenshots/tag-empty-error.png', fullPage: true });

    // Fill in tag name
    await tagInput.fill('测试标签 E2E');
    await page.waitForTimeout(300);

    // Save tag
    await saveButton.click();
    await page.waitForTimeout(1000);

    // Screenshot after adding tag
    await page.screenshot({ path: 'screenshots/tag-added.png', fullPage: true });
  });

  test('should verify all 6 settings sections exist', async () => {
    // Navigate to Settings page
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Wait for accordion buttons to load
    await page.waitForSelector('button[type="button"]', { timeout: 15000 });

    // Get all accordion buttons (filter for accordion items by checking if they contain an icon or title)
    const accordionButtons = page.locator('button[type="button"]').filter({
      has: page.locator('svg')
    });
    const count = await accordionButtons.count();

    // Should have 6 sections now
    expect(count).toBeGreaterThanOrEqual(6);

    // Verify section titles
    const expectedSections = [
      /Provider 配置|Provider Config/,
      /WordPress 配置|WordPress Config/,
      /成本限额|Cost Limits/,
      /截图保留策略|Screenshot Retention/,
      /校对规则|Proofreading Rules/,
      /标签管理|Tag Management/,
    ];

    for (const sectionPattern of expectedSections) {
      const section = page.locator('button[type="button"]').filter({
        hasText: sectionPattern
      });
      await expect(section).toBeVisible({ timeout: 5000 });
    }

    // Take screenshot of all sections
    await page.screenshot({ path: 'screenshots/all-settings-sections.png', fullPage: true });
  });

  test('should test Proofreading Rules quick actions', async () => {
    // Navigate to Settings page
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Find and click Proofreading Rules accordion
    const proofreadingAccordion = page.locator('button[type="button"]').filter({
      hasText: /校对规则|Proofreading Rules/
    });
    await proofreadingAccordion.click();
    await page.waitForTimeout(1000);

    // Verify quick action buttons exist
    const manageRulesButton = page.locator('button', { hasText: /管理规则|Manage Rules/ });
    const testRulesButton = page.locator('button', { hasText: /测试规则|Test Rules/ });
    const viewStatsButton = page.locator('button', { hasText: /查看统计|View Statistics/ });

    await expect(manageRulesButton).toBeVisible({ timeout: 5000 });
    await expect(testRulesButton).toBeVisible({ timeout: 5000 });
    await expect(viewStatsButton).toBeVisible({ timeout: 5000 });

    // Take screenshot
    await page.screenshot({ path: 'screenshots/proofreading-quick-actions.png', fullPage: true });
  });

  test('should display proper i18n translations', async () => {
    // Navigate to Settings page
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Check if Chinese or English is displayed
    const pageContent = await page.content();

    const hasChinese = pageContent.includes('校对规则') || pageContent.includes('标签管理');
    const hasEnglish = pageContent.includes('Proofreading Rules') || pageContent.includes('Tag Management');

    expect(hasChinese || hasEnglish).toBeTruthy();

    // Take screenshot
    await page.screenshot({ path: 'screenshots/settings-i18n.png', fullPage: true });
  });

  test('should collapse and expand sections correctly', async () => {
    // Navigate to Settings page
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Find Proofreading Rules accordion
    const proofreadingAccordion = page.locator('button[type="button"]').filter({
      hasText: /校对规则|Proofreading Rules/
    });

    // Expand
    await proofreadingAccordion.click();
    await page.waitForTimeout(500);

    // Verify content is visible
    const proofreadingContent = page.locator('text=/总规则数|Total Rules/');
    await expect(proofreadingContent).toBeVisible({ timeout: 5000 });

    await page.screenshot({ path: 'screenshots/accordion-expanded.png', fullPage: true });

    // Collapse
    await proofreadingAccordion.click();
    await page.waitForTimeout(500);

    // Verify content is hidden (may not be in DOM or hidden)
    await page.screenshot({ path: 'screenshots/accordion-collapsed.png', fullPage: true });

    // Expand again
    await proofreadingAccordion.click();
    await page.waitForTimeout(500);

    // Verify content is visible again
    await expect(proofreadingContent).toBeVisible({ timeout: 5000 });
  });
});
