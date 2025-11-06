import { test } from '@playwright/test';

/**
 * Read error logs from localStorage
 */

const PROD_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323';

test('Read error logs from localStorage', async ({ page }) => {
  console.log('Navigating to Settings page...');
  await page.goto(`${PROD_URL}/index.html#/settings`, {
    waitUntil: 'networkidle',
  });

  await page.waitForTimeout(3000);

  // Read the error logs from localStorage
  const errorLogs = await page.evaluate(() => {
    try {
      const logs = localStorage.getItem('cms_automation_error_logs');
      const sessionId = localStorage.getItem('cms_automation_session_id');

      return {
        errorLogs: logs ? JSON.parse(logs) : null,
        sessionId,
        allKeys: Object.keys(localStorage),
      };
    } catch (e: any) {
      return {
        error: `Failed to parse: ${e.message}`,
        rawLogs: localStorage.getItem('cms_automation_error_logs'),
      };
    }
  });

  console.log('\n========================================');
  console.log('ERROR LOGS FROM LOCALSTORAGE');
  console.log('========================================\n');
  console.log(JSON.stringify(errorLogs, null, 2));
  console.log('\n========================================\n');
});
