import { test } from '@playwright/test';

/**
 * Capture actual JavaScript errors from the page
 */

const PROD_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323';

test('Capture JavaScript error details', async ({ page }) => {
  const errors: any[] = [];

  // Capture ALL page errors with full details
  page.on('pageerror', (error) => {
    errors.push({
      message: error.message,
      name: error.name,
      stack: error.stack,
    });
    console.log('\n========== PAGE ERROR ==========');
    console.log('Name:', error.name);
    console.log('Message:', error.message);
    console.log('Stack:', error.stack);
    console.log('================================\n');
  });

  // Capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('\n[CONSOLE ERROR]', msg.text());
    }
  });

  // Capture unhandled promise rejections
  page.on('requestfailed', request => {
    console.log('\n[REQUEST FAILED]', request.url(), request.failure()?.errorText);
  });

  console.log('Navigating to Settings page...');
  await page.goto(`${PROD_URL}/index.html#/settings`, {
    waitUntil: 'networkidle',
    timeout: 30000,
  });

  // Wait for React to render
  await page.waitForTimeout(3000);

  console.log('\n========== SUMMARY ==========');
  console.log('Total errors captured:', errors.length);
  if (errors.length > 0) {
    console.log('\nErrors:');
    errors.forEach((err, index) => {
      console.log(`\n--- Error ${index + 1} ---`);
      console.log(JSON.stringify(err, null, 2));
    });
  } else {
    console.log('No page errors captured (errors are caught by React Error Boundary)');
  }
  console.log('============================\n');
});
