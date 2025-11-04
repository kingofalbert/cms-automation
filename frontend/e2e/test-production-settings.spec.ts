import { test, expect } from '@playwright/test';

test('Test production Settings page', async ({ page }) => {
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

  // Test with real production URL and cache-busting timestamp
  const timestamp = Date.now();
  console.log(`\nTesting with timestamp: ${timestamp}`);
  await page.goto(`https://storage.googleapis.com/cms-automation-frontend-2025/index.html?t=${timestamp}`, {
    waitUntil: 'networkidle'
  });

  await page.waitForTimeout(3000);

  // Check for error page
  const errorPageVisible = await page.locator('text=應用程序出錯').isVisible().catch(() => false);
  if (errorPageVisible) {
    console.log('\n❌ ERROR PAGE DETECTED on home page!');
    await page.screenshot({
      path: 'test-results/production-error-home.png',
      fullPage: true
    });
  } else {
    console.log('\n✅ Home page loaded successfully');
  }

  // Click Settings link
  console.log('\nNavigating to Settings page...');
  const settingsLink = page.locator('a:has-text("設置")').first();
  await settingsLink.click();

  await page.waitForTimeout(5000);

  // Check for error page on Settings
  const settingsErrorVisible = await page.locator('text=應用程序出錯').isVisible().catch(() => false);

  console.log('\n=== Test Results ===');
  if (settingsErrorVisible) {
    console.log('❌ ERROR PAGE DETECTED on Settings page!');

    // Try to get error count
    const errorCountText = await page.locator('text=個錯誤').textContent().catch(() => '');
    console.log(`Error message: ${errorCountText}`);
  } else {
    console.log('✅ Settings page loaded successfully');
  }

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
    path: 'test-results/production-settings-final.png',
    fullPage: true
  });

  console.log('\nScreenshot saved to test-results/production-settings-final.png');

  // Fail test if error page is visible
  expect(settingsErrorVisible).toBe(false);
});
