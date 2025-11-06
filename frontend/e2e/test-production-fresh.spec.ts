import { test, expect } from '@playwright/test';

const PROD_URL =
  'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323';

test('Test Settings page with fresh browser (no cache)', async ({ browser }) => {
  // Create a completely fresh browser context with no cache
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
  });

  // Clear all storage before starting
  await context.clearCookies();

  const page = await context.newPage();

  // Clear all caches
  await context.clearCookies();
  await page.goto(PROD_URL, { waitUntil: 'networkidle' });

  // Clear localStorage and sessionStorage
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  console.log('\n🧹 Cleared all caches and storage');

  // Add listeners to see what files are loaded
  const loadedFiles: string[] = [];
  page.on('response', response => {
    const url = response.url();
    if (url.includes('SettingsPageModern')) {
      loadedFiles.push(url);
      console.log(`📦 Loaded Settings file: ${url}`);
    }
  });

  // Navigate to Settings page
  console.log('\n🔄 Navigating to Settings page...');
  await page.goto(`${PROD_URL}/index.html#/settings`, {
    waitUntil: 'networkidle',
  });

  await page.waitForTimeout(3000);

  // Check if error boundary is visible
  const errorBoundary = page.locator('text=发生了一些错误');
  const hasError = await errorBoundary.isVisible().catch(() => false);

  console.log('\n========================================');
  console.log('FILES LOADED:');
  console.log('========================================');
  loadedFiles.forEach(file => console.log(file));
  console.log('========================================\n');

  if (hasError) {
    console.error('\n❌ Error boundary is STILL visible');

    // Read error logs
    const errorLogs = await page.evaluate(() => {
      const logs = localStorage.getItem('cms_automation_error_logs');
      return logs ? JSON.parse(logs) : null;
    });

    if (errorLogs && errorLogs.length > 0) {
      console.error('\nError details:');
      console.error(JSON.stringify(errorLogs[0], null, 2));
    }

    await page.screenshot({ path: '/tmp/settings-error-fresh.png' });
    throw new Error('Settings page STILL shows error with fresh browser!');
  }

  console.log('\n✅ SUCCESS: Settings page works with fresh browser!');

  await context.close();
});
