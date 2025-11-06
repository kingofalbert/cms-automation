import { test } from '@playwright/test';

/**
 * Test Settings page on local build (served from dist/)
 */

test('Test Settings page on local build', async ({ page }) => {
  // Capture errors
  page.on('pageerror', error => {
    console.log('\n[PAGE ERROR]', error.message);
    console.log('[STACK]', error.stack);
  });

  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`\n[CONSOLE ERROR] ${msg.text()}`);
    }
  });

  console.log('Navigating to Settings page on localhost:8080...');
  await page.goto('http://localhost:8080/index.html#/settings', {
    waitUntil: 'networkidle',
  });

  await page.waitForTimeout(3000);

  // Check if error boundary is visible
  const hasErrorBoundary = await page.locator('text=應用程序出錯').isVisible().catch(() => false);

  if (hasErrorBoundary) {
    console.log('\n❌ ERROR: Settings page shows error boundary on LOCAL BUILD\n');

    // Read error logs
    const errorLogs = await page.evaluate(() => {
      return localStorage.getItem('cms_automation_error_logs');
    });

    console.log('Error logs:', errorLogs);
  } else {
    console.log('\n✅ SUCCESS: Settings page loads correctly on LOCAL BUILD\n');
  }
});
