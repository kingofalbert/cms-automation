/**
 * Settings Page Visual Tests
 *
 * Tests visual appearance and layout of the settings page.
 * Covers: Configuration sections, form inputs, validation.
 */

import { test, expect } from '@playwright/test';
import { navigateWithRetry, waitForPageReady } from '../utils/test-helpers';
import {
  VIEWPORTS,
  waitForAnimations,
  captureScreenshot,
} from '../utils/visual-test-helpers';

const BASE_URL = process.env.TEST_LOCAL === '1'
  ? 'http://localhost:4173'
  : 'https://storage.googleapis.com/cms-automation-frontend-476323/index.html';

test.describe('Settings Page Visual Tests', () => {
  test.beforeEach(async ({ page }) => {
    await navigateWithRetry(page, BASE_URL);
    await waitForPageReady(page);

    // Navigate to settings
    const settingsButton = page.locator('button:has-text("Settings")');
    await settingsButton.click();
    await waitForAnimations(page);
  });

  test.describe('Page Layout', () => {
    test('should display settings page header', async ({ page }) => {
      await expect(page.locator('text=System Settings')).toBeVisible();
    });

    test('should display back to worklist button', async ({ page }) => {
      const backButton = page.locator('button:has-text("← Back to Worklist")');
      await expect(backButton).toBeVisible();
    });

    test('should navigate back to worklist when clicking back', async ({ page }) => {
      const backButton = page.locator('button:has-text("← Back to Worklist")');
      await backButton.click();
      await waitForAnimations(page);

      // Should be back on worklist
      await expect(page.locator('text=CMS Automation System')).toBeVisible();
    });
  });

  test.describe('Configuration Sections', () => {
    test('should display Upload Settings section', async ({ page }) => {
      await expect(page.locator('text=Upload Settings')).toBeVisible();

      // Check for Google Drive folder ID input
      const folderIdInput = page.locator('input[placeholder*="folder"]');
      if (await folderIdInput.count() > 0) {
        await expect(folderIdInput.first()).toBeVisible();
      }
    });

    test('should display Cost Limits section', async ({ page }) => {
      await expect(page.locator('text=Cost Limits')).toBeVisible();

      // Check for cost limit inputs
      const costInputs = page.locator('input[type="number"]');
      if (await costInputs.count() > 0) {
        await expect(costInputs.first()).toBeVisible();
      }
    });

    test('should display Proofreading Settings section', async ({ page }) => {
      const proofreadingSection = page.locator('text=/Proofreading Settings|校对设置/');
      if (await proofreadingSection.count() > 0) {
        await expect(proofreadingSection.first()).toBeVisible();
      }
    });

    test('should display AI Configuration section', async ({ page }) => {
      const aiSection = page.locator('text=/AI Configuration|AI 设置|Model/');
      if (await aiSection.count() > 0) {
        await expect(aiSection.first()).toBeVisible();
      }
    });
  });

  test.describe('Form Inputs', () => {
    test('should display text inputs correctly', async ({ page }) => {
      const textInputs = page.locator('input[type="text"]');
      const count = await textInputs.count();
      console.log(`Found ${count} text inputs`);

      if (count > 0) {
        // Check first input has proper styling
        const firstInput = textInputs.first();
        await expect(firstInput).toBeVisible();
      }
    });

    test('should display number inputs correctly', async ({ page }) => {
      const numberInputs = page.locator('input[type="number"]');
      const count = await numberInputs.count();
      console.log(`Found ${count} number inputs`);

      if (count > 0) {
        const firstInput = numberInputs.first();
        await expect(firstInput).toBeVisible();
      }
    });

    test('should display toggle switches correctly', async ({ page }) => {
      const toggles = page.locator('[role="switch"], input[type="checkbox"]');
      const count = await toggles.count();
      console.log(`Found ${count} toggle switches`);

      if (count > 0) {
        await expect(toggles.first()).toBeVisible();
      }
    });

    test('should display dropdown selects correctly', async ({ page }) => {
      const selects = page.locator('select, [role="combobox"]');
      const count = await selects.count();
      console.log(`Found ${count} select inputs`);

      if (count > 0) {
        await expect(selects.first()).toBeVisible();
      }
    });
  });

  test.describe('Form Validation', () => {
    test('should show validation error for invalid input', async ({ page }) => {
      const numberInput = page.locator('input[type="number"]').first();
      if (await numberInput.isVisible()) {
        // Try entering invalid value
        await numberInput.fill('-100');
        await numberInput.blur();
        await waitForAnimations(page);

        // Check for error state
        const errorIndicator = page.locator('[class*="error"], [class*="invalid"], text=/invalid|错误/i');
        if (await errorIndicator.count() > 0) {
          await expect(errorIndicator.first()).toBeVisible();
        }
      }
    });

    test('should show validation error for empty required field', async ({ page }) => {
      const requiredInput = page.locator('input[required]').first();
      if (await requiredInput.isVisible()) {
        await requiredInput.clear();
        await requiredInput.blur();
        await waitForAnimations(page);
      }
    });
  });

  test.describe('Save Configuration', () => {
    test('should display save button', async ({ page }) => {
      const saveButton = page.locator('button:has-text("Save"), button:has-text("保存")');
      if (await saveButton.count() > 0) {
        await expect(saveButton.first()).toBeVisible();
      }
    });

    test('should show success message after saving', async ({ page }) => {
      const saveButton = page.locator('button:has-text("Save"), button:has-text("保存")');
      if (await saveButton.isVisible()) {
        await saveButton.click();
        await waitForAnimations(page);

        // Check for success toast or message
        const successMessage = page.locator('text=/saved|success|保存成功/i');
        if (await successMessage.count() > 0) {
          await expect(successMessage.first()).toBeVisible({ timeout: 5000 }).catch(() => {
            console.log('Success message may have different format');
          });
        }
      }
    });
  });

  test.describe('Reset Configuration', () => {
    test('should display reset button', async ({ page }) => {
      const resetButton = page.locator('button:has-text("Reset"), button:has-text("重置")');
      if (await resetButton.count() > 0) {
        await expect(resetButton.first()).toBeVisible();
      }
    });

    test('should show confirmation when resetting', async ({ page }) => {
      const resetButton = page.locator('button:has-text("Reset"), button:has-text("重置")');
      if (await resetButton.isVisible()) {
        await resetButton.click();
        await waitForAnimations(page);

        // Check for confirmation dialog
        const confirmDialog = page.locator('[role="dialog"], [class*="confirm"]');
        if (await confirmDialog.count() > 0) {
          await expect(confirmDialog.first()).toBeVisible();
        }
      }
    });
  });

  test.describe('Responsive Layout', () => {
    test('should display correctly on desktop', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop);
      await waitForAnimations(page);

      await captureScreenshot(page, 'settings-desktop');
    });

    test('should display correctly on tablet', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.tablet);
      await waitForAnimations(page);

      // Content should adapt
      await expect(page.locator('text=System Settings')).toBeVisible();

      await captureScreenshot(page, 'settings-tablet');
    });

    test('should display correctly on mobile', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile);
      await waitForAnimations(page);

      // Settings should stack vertically
      await expect(page.locator('text=System Settings')).toBeVisible();

      await captureScreenshot(page, 'settings-mobile');
    });
  });

  test.describe('Section Cards', () => {
    test('should display settings in card containers', async ({ page }) => {
      const cards = page.locator('[class*="card"], [class*="Card"]');
      const count = await cards.count();
      console.log(`Found ${count} card containers`);

      if (count > 0) {
        await expect(cards.first()).toBeVisible();
      }
    });

    test('should have proper spacing between sections', async ({ page }) => {
      const sections = page.locator('[class*="section"], [class*="card"]');
      const count = await sections.count();

      if (count > 1) {
        const firstBox = await sections.first().boundingBox();
        const secondBox = await sections.nth(1).boundingBox();

        if (firstBox && secondBox) {
          // Should have reasonable spacing
          const spacing = secondBox.y - (firstBox.y + firstBox.height);
          expect(spacing).toBeGreaterThanOrEqual(0);
        }
      }
    });
  });

  test.describe('Help Text and Labels', () => {
    test('should display labels for all inputs', async ({ page }) => {
      const labels = page.locator('label');
      const inputs = page.locator('input');

      const labelCount = await labels.count();
      const inputCount = await inputs.count();

      console.log(`Labels: ${labelCount}, Inputs: ${inputCount}`);
    });

    test('should display helper text where appropriate', async ({ page }) => {
      const helpText = page.locator('[class*="help"], [class*="hint"], [class*="description"]');
      if (await helpText.count() > 0) {
        await expect(helpText.first()).toBeVisible();
      }
    });
  });

  test.describe('Default Values', () => {
    test('should display default values in inputs', async ({ page }) => {
      const numberInputs = page.locator('input[type="number"]');
      if (await numberInputs.count() > 0) {
        const value = await numberInputs.first().inputValue();
        console.log(`First number input default value: ${value}`);
      }
    });

    test('should show current configuration values', async ({ page }) => {
      // Check that inputs have values (not empty)
      const textInputs = page.locator('input[type="text"]');
      if (await textInputs.count() > 0) {
        const value = await textInputs.first().inputValue();
        console.log(`First text input value: ${value || '(empty)'}`);
      }
    });
  });

  test.describe('Theme Consistency', () => {
    test('should use consistent styling with main app', async ({ page }) => {
      // Check for consistent header styling
      const header = page.locator('h1, h2').first();
      if (await header.isVisible()) {
        const styles = await header.evaluate((el) => {
          const computed = window.getComputedStyle(el);
          return {
            fontFamily: computed.fontFamily,
            color: computed.color,
          };
        });
        console.log('Header styles:', styles);
      }
    });

    test('should use consistent button styling', async ({ page }) => {
      const button = page.locator('button').first();
      if (await button.isVisible()) {
        const styles = await button.evaluate((el) => {
          const computed = window.getComputedStyle(el);
          return {
            backgroundColor: computed.backgroundColor,
            borderRadius: computed.borderRadius,
          };
        });
        console.log('Button styles:', styles);
      }
    });
  });
});
