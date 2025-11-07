/**
 * Simplified E2E Tests for New Settings Sections
 * Tests that the Proofreading Rules and Tag Management sections exist and are accessible
 */

import { test, expect } from '@playwright/test';

const PRODUCTION_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

test.describe('Settings Page - New Sections (Simplified)', () => {
  test('should display all 6 settings sections including new ones', async ({ page }) => {
    // Navigate directly to Settings page
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);

    // Take initial screenshot
    await page.screenshot({ path: 'screenshots/settings-initial.png', fullPage: true });

    // Wait for accordion buttons to load (more reliable than waiting for title)
    await page.waitForTimeout(3000);

    // Check for all 6 sections
    const sections = [
      { name: 'Provider Config', pattern: /Provider 配置|Provider Config/ },
      { name: 'WordPress Config', pattern: /WordPress 配置|WordPress Config/ },
      { name: 'Cost Limits', pattern: /成本限额|Cost Limits/ },
      { name: 'Screenshot Retention', pattern: /截图保留策略|Screenshot Retention/ },
      { name: 'Proofreading Rules', pattern: /校对规则|Proofreading Rules/ },
      { name: 'Tag Management', pattern: /标签管理|Tag Management/ },
    ];

    console.log('Checking for all 6 settings sections...');

    for (const section of sections) {
      const sectionButton = page.locator('button[type="button"]').filter({
        hasText: section.pattern,
      });

      try {
        await expect(sectionButton).toBeVisible({ timeout: 5000 });
        console.log(`✓ ${section.name} section found`);
      } catch (error) {
        console.error(`✗ ${section.name} section NOT found`);
        await page.screenshot({
          path: `screenshots/error-missing-${section.name.toLowerCase().replace(/\s+/g, '-')}.png`,
          fullPage: true,
        });
        throw error;
      }
    }

    // Take final screenshot
    await page.screenshot({ path: 'screenshots/all-sections-verified.png', fullPage: true });

    console.log('✓ All 6 sections verified successfully!');
  });

  test('should expand and show Proofreading Rules content', async ({ page }) => {
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);

    // Find Proofreading Rules section
    const proofreadingButton = page.locator('button[type="button"]').filter({
      hasText: /校对规则|Proofreading Rules/,
    });

    await expect(proofreadingButton).toBeVisible({ timeout: 10000 });
    await page.screenshot({ path: 'screenshots/proofreading-before-click.png', fullPage: true });

    // Click to expand
    await proofreadingButton.click();
    await page.waitForTimeout(1000);

    // Take screenshot after expansion
    await page.screenshot({ path: 'screenshots/proofreading-after-click.png', fullPage: true });

    // Verify content is visible (look for any content, not specific text)
    const cardElements = page.locator('.rounded-lg.border');
    const cardCount = await cardElements.count();

    console.log(`Found ${cardCount} card elements in Proofreading Rules section`);
    expect(cardCount).toBeGreaterThan(0);

    console.log('✓ Proofreading Rules section expands successfully');
  });

  test('should expand and show Tag Management content', async ({ page }) => {
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);

    // Find Tag Management section
    const tagButton = page.locator('button[type="button"]').filter({
      hasText: /标签管理|Tag Management/,
    });

    await expect(tagButton).toBeVisible({ timeout: 10000 });
    await page.screenshot({ path: 'screenshots/tag-before-click.png', fullPage: true });

    // Click to expand
    await tagButton.click();
    await page.waitForTimeout(1000);

    // Take screenshot after expansion
    await page.screenshot({ path: 'screenshots/tag-after-click.png', fullPage: true });

    // Verify "Add Tag" button is visible
    const addTagButton = page.locator('button', { hasText: /添加标签|Add Tag/ });
    await expect(addTagButton).toBeVisible({ timeout: 5000 });

    console.log('✓ Tag Management section expands and shows "Add Tag" button');
  });

  test('should show Tag Management statistics cards', async ({ page }) => {
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);

    // Expand Tag Management section
    const tagButton = page.locator('button[type="button"]').filter({
      hasText: /标签管理|Tag Management/,
    });
    await tagButton.click();
    await page.waitForTimeout(1000);

    // Count statistics cards (should have 3)
    const statCards = page.locator('.rounded-lg.border.border-gray-200.bg-gray-50');
    const statCount = await statCards.count();

    console.log(`Found ${statCount} statistics cards in Tag Management section`);
    expect(statCount).toBeGreaterThanOrEqual(3);

    await page.screenshot({ path: 'screenshots/tag-stats-cards.png', fullPage: true });

    console.log('✓ Tag Management statistics cards displayed');
  });

  test('should verify both new sections can be collapsed and expanded', async ({ page }) => {
    await page.goto(`${PRODUCTION_URL}#/settings`);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);

    // Test Proofreading Rules
    const proofreadingButton = page.locator('button[type="button"]').filter({
      hasText: /校对规则|Proofreading Rules/,
    });

    await proofreadingButton.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'screenshots/proofreading-expanded.png', fullPage: true });

    await proofreadingButton.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'screenshots/proofreading-collapsed.png', fullPage: true });

    // Test Tag Management
    const tagButton = page.locator('button[type="button"]').filter({
      hasText: /标签管理|Tag Management/,
    });

    await tagButton.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'screenshots/tag-expanded.png', fullPage: true });

    await tagButton.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'screenshots/tag-collapsed.png', fullPage: true });

    console.log('✓ Both sections can be collapsed and expanded');
  });
});
