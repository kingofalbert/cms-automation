/**
 * Debug test to capture the actual error when clicking Rendered view
 */

import { test, expect } from '@playwright/test';

const CACHE_BUST = Date.now();
const FRONTEND_URL = `https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html?v=${CACHE_BUST}`;

test.describe('Debug Rendered View Error', () => {
  test('Capture console errors and stack trace', async ({ page }) => {
    const consoleMessages: string[] = [];
    const errors: string[] = [];

    // Capture all console messages
    page.on('console', (msg) => {
      const text = `[${msg.type()}] ${msg.text()}`;
      consoleMessages.push(text);
      console.log(text);
    });

    // Capture page errors
    page.on('pageerror', (error) => {
      const errorText = `PAGE ERROR: ${error.message}\n${error.stack}`;
      errors.push(errorText);
      console.log(errorText);
    });

    console.log('Navigating to frontend...');
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Find and click first Review button
    console.log('Looking for Review button...');
    const reviewButton = page.locator('button:has-text("Review")').first();
    await reviewButton.waitFor({ state: 'visible', timeout: 10000 });
    await reviewButton.click();

    // Wait for proofreading page
    await page.waitForTimeout(3000);
    console.log('On proofreading page');

    // Click Rendered button
    console.log('Clicking Rendered button...');
    const renderedButton = page.locator('button:has-text("Rendered")');
    await renderedButton.waitFor({ state: 'visible' });

    // Wait a bit more to ensure errors are captured
    await page.waitForTimeout(1000);

    await renderedButton.click();

    // Wait for error to appear
    await page.waitForTimeout(3000);

    // Check if error boundary is shown
    const errorTitle = await page.locator('text=應用程序出錯').count();
    console.log(`Error boundary shown: ${errorTitle > 0}`);

    // Try to click "Show Details" button if in dev mode
    const showDetailsButton = page.locator('button:has-text("顯示詳情")');
    if ((await showDetailsButton.count()) > 0) {
      console.log('Clicking Show Details button...');
      await showDetailsButton.click();
      await page.waitForTimeout(1000);

      // Capture error details
      const errorDetails = await page.locator('#error-details').textContent();
      console.log('===== ERROR DETAILS =====');
      console.log(errorDetails);
      console.log('========================');
    }

    // Take screenshot
    await page.screenshot({ path: 'test-results/debug-rendered-error.png', fullPage: true });

    console.log('\n===== ALL CONSOLE MESSAGES =====');
    consoleMessages.forEach((msg) => console.log(msg));

    console.log('\n===== ALL PAGE ERRORS =====');
    errors.forEach((err) => console.log(err));

    // Save to file
    const fs = require('fs');
    fs.writeFileSync(
      'test-results/rendered-view-error-log.txt',
      `Console Messages:\n${consoleMessages.join('\n')}\n\nPage Errors:\n${errors.join('\n')}`
    );
  });
});
