/**
 * Get error logs from localStorage after clicking Rendered view
 */

import { test } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const CACHE_BUST = Date.now();
const FRONTEND_URL = `https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html?v=${CACHE_BUST}`;

test.describe('Get localStorage Error Logs', () => {
  test('Extract error logs from localStorage', async ({ page }) => {
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

    // Click Rendered button to trigger error
    console.log('Clicking Rendered button...');
    const renderedButton = page.locator('button:has-text("Rendered")');
    await renderedButton.waitFor({ state: 'visible' });
    await renderedButton.click();

    // Wait for error to be logged
    await page.waitForTimeout(3000);

    // Extract error logs from localStorage
    const errorLogs = await page.evaluate(() => {
      const logs = localStorage.getItem('cms_automation_error_logs');
      return logs ? JSON.parse(logs) : [];
    });

    console.log('\n===== LOCALSTORAGE ERROR LOGS =====');
    console.log(JSON.stringify(errorLogs, null, 2));
    console.log('===================================\n');

    // Save to file
    const outputDir = path.join(process.cwd(), 'test-results');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(
      path.join(outputDir, 'localStorage-error-logs.json'),
      JSON.stringify(errorLogs, null, 2)
    );

    console.log(`✅ Error logs saved to test-results/localStorage-error-logs.json`);
    console.log(`   Found ${errorLogs.length} error(s)`);

    if (errorLogs.length > 0) {
      console.log('\n===== MOST RECENT ERROR =====');
      const latestError = errorLogs[0];
      console.log('Message:', latestError.message);
      console.log('Stack:', latestError.stack);
      console.log('Component Stack:', latestError.componentStack);
      console.log('Metadata:', latestError.metadata);
      console.log('============================\n');
    }

    await page.screenshot({ path: 'test-results/localStorage-error-state.png', fullPage: true });
  });
});
