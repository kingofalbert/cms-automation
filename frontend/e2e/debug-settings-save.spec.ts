/**
 * Debug test for Settings save button feedback issue
 *
 * User report: Clicking "立即儲存" (Save Now) button shows no visual feedback
 */

import { test, expect } from '@playwright/test';

const FRONTEND_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

test.describe('Settings Save Button Debug', () => {
  test('Verify Toast notification appears on save', async ({ page }) => {
    // Capture console logs and errors
    const consoleLogs: string[] = [];
    const consoleErrors: string[] = [];
    const networkRequests: { url: string; method: string; status: number | null }[] = [];

    page.on('console', (msg) => {
      const text = msg.text();
      consoleLogs.push(`[${msg.type()}] ${text}`);
      if (msg.type() === 'error') {
        consoleErrors.push(text);
      }
    });

    page.on('request', (request) => {
      if (request.url().includes('/v1/settings')) {
        networkRequests.push({
          url: request.url(),
          method: request.method(),
          status: null,
        });
      }
    });

    page.on('response', async (response) => {
      if (response.url().includes('/v1/settings')) {
        const request = networkRequests.find(
          (r) => r.url === response.url() && r.status === null
        );
        if (request) {
          request.status = response.status();
        }
        console.log(`API Response: ${response.url()} - Status: ${response.status()}`);
        try {
          const body = await response.json();
          console.log('Response body:', JSON.stringify(body, null, 2));
        } catch {
          console.log('Response is not JSON');
        }
      }
    });

    console.log('\n=== NAVIGATING TO SETTINGS PAGE ===\n');
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');

    // Navigate to Settings
    const settingsButton = page.locator('button:has-text("Settings"), a:has-text("Settings")').first();
    await expect(settingsButton).toBeVisible({ timeout: 10000 });
    await settingsButton.click();
    await page.waitForTimeout(2000);

    console.log('\n=== ON SETTINGS PAGE ===\n');

    // Wait for settings to load
    await page.waitForSelector('text=/Provider|WordPress|成本限額/i', { timeout: 10000 });

    // Make a small change - toggle Playwright enabled
    console.log('Looking for Provider Config accordion...');
    const providerAccordion = page.locator('button:has-text("Provider")').first();
    await expect(providerAccordion).toBeVisible({ timeout: 5000 });

    // Open Provider Config if not already open
    const isExpanded = await providerAccordion.getAttribute('aria-expanded');
    if (isExpanded !== 'true') {
      console.log('Opening Provider Config accordion...');
      await providerAccordion.click();
      await page.waitForTimeout(500);
    }

    // Find and toggle a checkbox
    console.log('Looking for a checkbox to toggle...');
    const playwrightCheckbox = page.locator('input[type="checkbox"]').first();
    await expect(playwrightCheckbox).toBeVisible({ timeout: 5000 });

    const wasChecked = await playwrightCheckbox.isChecked();
    console.log(`Checkbox current state: ${wasChecked ? 'checked' : 'unchecked'}`);

    await playwrightCheckbox.click();
    await page.waitForTimeout(500);

    const isNowChecked = await playwrightCheckbox.isChecked();
    console.log(`Checkbox new state: ${isNowChecked ? 'checked' : 'unchecked'}`);

    // Look for Save button
    console.log('\n=== LOOKING FOR SAVE BUTTON ===\n');
    const saveButton = page.locator('button:has-text("儲存設定"), button:has-text("Save Settings"), button:has-text("立即儲存"), button:has-text("Save now")');

    const saveButtonCount = await saveButton.count();
    console.log(`Found ${saveButtonCount} save button(s)`);

    if (saveButtonCount === 0) {
      console.log('❌ No save button found!');
      console.log('Available buttons:');
      const allButtons = await page.locator('button').allTextContents();
      console.log(allButtons);
    } else {
      await expect(saveButton.first()).toBeVisible();
      const buttonText = await saveButton.first().textContent();
      console.log(`Save button text: "${buttonText}"`);

      const isDisabled = await saveButton.first().isDisabled();
      console.log(`Save button disabled: ${isDisabled}`);

      if (!isDisabled) {
        // Look for toast container BEFORE clicking
        console.log('\n=== CLICKING SAVE BUTTON ===\n');

        // Take screenshot before save
        await page.screenshot({ path: '/home/kingofalbert/projects/CMS/frontend/test-results/settings-before-save.png', fullPage: true });

        await saveButton.first().click();
        console.log('Save button clicked!');

        // Wait for potential toast
        await page.waitForTimeout(1000);

        // Check for toast elements
        console.log('\n=== CHECKING FOR TOAST NOTIFICATION ===\n');

        const toastSelectors = [
          '[data-sonner-toast]',
          '[role="status"]',
          '[role="alert"]',
          '.sonner-toast',
          'text=/儲存成功|Saved successfully|正在儲存|Saving/i',
        ];

        for (const selector of toastSelectors) {
          const toastCount = await page.locator(selector).count();
          if (toastCount > 0) {
            console.log(`✅ Found ${toastCount} toast(s) with selector: ${selector}`);
            const toastText = await page.locator(selector).first().textContent();
            console.log(`Toast text: "${toastText}"`);
          } else {
            console.log(`❌ No toast found with selector: ${selector}`);
          }
        }

        // Wait a bit more for toast
        await page.waitForTimeout(3000);

        // Take screenshot after save
        await page.screenshot({ path: '/home/kingofalbert/projects/CMS/frontend/test-results/settings-after-save.png', fullPage: true });

        // Check network requests
        console.log('\n=== NETWORK REQUESTS ===\n');
        console.log('Settings API calls:', networkRequests);

        // Check console logs
        console.log('\n=== CONSOLE LOGS ===\n');
        console.log(consoleLogs.slice(-20).join('\n'));

        if (consoleErrors.length > 0) {
          console.log('\n=== CONSOLE ERRORS ===\n');
          console.log(consoleErrors.join('\n'));
        }

        // Final check for toast
        const finalToastCount = await page.locator('[data-sonner-toast]').count();
        console.log(`\n=== FINAL RESULT ===`);
        console.log(`Toast notifications visible: ${finalToastCount}`);

        if (finalToastCount === 0) {
          console.log('❌ NO TOAST NOTIFICATION APPEARED!');
        } else {
          console.log('✅ Toast notification appeared!');
        }
      } else {
        console.log('⚠️ Save button is disabled - no changes detected');
      }
    }
  });
});
