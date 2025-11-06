import { test } from '@playwright/test';

/**
 * Test Settings page in dev mode to see actual error messages
 */

test('Test Settings page in dev mode', async ({ page }) => {
  const errors: string[] = [];

  // Capture ALL errors
  page.on('pageerror', error => {
    const errorMsg = `
========== PAGE ERROR (DEV MODE) ==========
Name: ${error.name}
Message: ${error.message}
Stack:
${error.stack}
==========================================
`;
    errors.push(errorMsg);
    console.log(errorMsg);
  });

  page.on('console', msg => {
    const text = msg.text();
    if (msg.type() === 'error' || text.includes('Error') || text.includes('error')) {
      console.log(`[CONSOLE ${msg.type().toUpperCase()}] ${text}`);
    }
  });

  console.log('Navigating to Settings page in DEV MODE on localhost:3002...');
  await page.goto('http://localhost:3002/#/settings', {
    waitUntil: 'networkidle',
    timeout: 30000,
  });

  await page.waitForTimeout(3000);

  // Check if error boundary is visible
  const hasErrorBoundary = await page.locator('text=應用程序出錯').isVisible().catch(() => false);

  if (hasErrorBoundary) {
    console.log('\n❌ ERROR: Settings page shows error boundary in DEV MODE\n');
    console.log(`Total errors captured: ${errors.length}`);
  } else {
    console.log('\n✅ SUCCESS: Settings page loads correctly in DEV MODE\n');
  }
});
