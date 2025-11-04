import { test } from '@playwright/test';

test('Debug Settings page errors', async ({ page }) => {
  const errors: string[] = [];
  const consoleLogs: string[] = [];

  // Capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleLogs.push(`CONSOLE ERROR: ${msg.text()}`);
    }
  });

  // Capture page errors
  page.on('pageerror', error => {
    errors.push(`PAGE ERROR: ${error.message}\n${error.stack}`);
  });

  // Add timestamp to bust cache
  const timestamp = Date.now();
  await page.goto(`https://storage.googleapis.com/cms-automation-frontend-2025/app.html?t=${timestamp}`, {
    waitUntil: 'networkidle'
  });

  await page.waitForTimeout(2000);

  // Click Settings link
  const link = page.locator('a:has-text("設置")').first();
  await link.click();

  await page.waitForTimeout(3000);

  // Print all errors
  console.log('\n=== JavaScript Errors ===');
  if (errors.length === 0) {
    console.log('No page errors detected');
  } else {
    errors.forEach(err => console.log(err));
  }

  console.log('\n=== Console Errors ===');
  if (consoleLogs.length === 0) {
    console.log('No console errors detected');
  } else {
    consoleLogs.forEach(log => console.log(log));
  }

  await page.screenshot({
    path: 'test-results/settings-debug.png',
    fullPage: true
  });

  console.log('\nScreenshot saved to test-results/settings-debug.png');
});
