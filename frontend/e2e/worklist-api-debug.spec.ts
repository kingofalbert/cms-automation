/**
 * Debug test - Check what's happening with worklist API call
 */

import { test } from '@playwright/test';

test('Debug worklist API calls', async ({ page }) => {
  const prodUrl = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

  const apiCalls: Array<{ url: string; status: number; response: any }> = [];

  // Capture all API responses
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('/v1/')) {
      try {
        const text = await response.text();
        let json = null;
        try {
          json = JSON.parse(text);
        } catch {
          json = { _raw: text.substring(0, 200) };
        }
        apiCalls.push({
          url,
          status: response.status(),
          response: json,
        });
      } catch (e: any) {
        apiCalls.push({
          url,
          status: response.status(),
          response: { error: e.message },
        });
      }
    }
  });

  // Capture console errors
  const consoleErrors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  console.log('🔍 Opening production site...');
  await page.goto(prodUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });

  // Wait for React to mount
  await page.waitForSelector('#root', { timeout: 10000 });

  // Wait for network activity to settle (or timeout)
  await page.waitForTimeout(10000);

  // Print all API calls
  console.log('\n=== API Calls ===');
  for (const call of apiCalls) {
    console.log(`\n${call.status} - ${call.url}`);
    console.log('Response:', JSON.stringify(call.response, null, 2).substring(0, 500));
  }

  // Print console errors
  console.log('\n=== Console Errors ===');
  consoleErrors.forEach((err) => console.log(err));

  // Take screenshot
  await page.screenshot({ path: '/tmp/worklist-api-debug.png', fullPage: true });
  console.log('\n📸 Screenshot: /tmp/worklist-api-debug.png');
});
