/**
 * Diagnose 404 Error in Production
 */

import { test } from '@playwright/test';

test('Find 404 resource', async ({ page }) => {
  const failedRequests: Array<{ url: string; status: number }> = [];

  // Capture all network requests
  page.on('response', (response) => {
    if (response.status() === 404) {
      failedRequests.push({
        url: response.url(),
        status: response.status(),
      });
    }
  });

  console.log('\n=== LOADING PRODUCTION PAGE ===\n');

  await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html', {
    waitUntil: 'networkidle',
    timeout: 30000,
  });

  console.log('=== 404 ERRORS ===\n');
  if (failedRequests.length > 0) {
    failedRequests.forEach((req) => {
      console.log(`❌ 404: ${req.url}`);
    });
  } else {
    console.log('✅ No 404 errors found');
  }

  // Wait a bit for any delayed requests
  await page.waitForTimeout(2000);

  console.log('\n=== TOTAL 404 ERRORS: ' + failedRequests.length + ' ===\n');
});
