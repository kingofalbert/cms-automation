import { test } from '@playwright/test';

/**
 * Test Settings page after clearing localStorage
 */

const PROD_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323';

test('Test Settings after clearing localStorage', async ({ page }) => {
  console.log('Navigating to homepage first...');
  await page.goto(`${PROD_URL}/index.html`, {
    waitUntil: 'networkidle',
  });

  await page.waitForTimeout(1000);

  // Clear localStorage
  console.log('Clearing localStorage...');
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  console.log('Navigating to Settings page...');
  await page.goto(`${PROD_URL}/index.html#/settings`, {
    waitUntil: 'networkidle',
  });

  await page.waitForTimeout(3000);

  // Check if error boundary is visible
  const hasErrorBoundary = await page.locator('text=應用程序出錯').isVisible().catch(() => false);

  if (hasErrorBoundary) {
    console.log('\n❌ Error boundary STILL visible after clearing storage\n');

    // Read new error logs
    const newErrors = await page.evaluate(() => {
      return localStorage.getItem('cms_automation_error_logs');
    });

    console.log('New error logs:');
    console.log(newErrors);
  } else {
    console.log('\n✅ No error boundary! Settings page loads successfully!\n');
  }

  await page.waitForTimeout(2000);
});
