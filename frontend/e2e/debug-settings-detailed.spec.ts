import { test } from '@playwright/test';

/**
 * Detailed debugging test for Settings page
 * Captures ALL console messages and errors
 */

const PROD_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323';

test('Debug Settings page - Detailed inspection', async ({ page }) => {
  const allConsoleMessages: string[] = [];
  const allErrors: string[] = [];
  const allRequests: string[] = [];
  const failedRequests: string[] = [];

  // Capture ALL console messages (not just errors)
  page.on('console', msg => {
    const text = `[${msg.type().toUpperCase()}] ${msg.text()}`;
    allConsoleMessages.push(text);
    console.log(text);
  });

  // Capture page errors
  page.on('pageerror', error => {
    const errorText = `PAGE ERROR: ${error.message}\nStack: ${error.stack}`;
    allErrors.push(errorText);
    console.log('\n' + errorText + '\n');
  });

  // Capture failed requests
  page.on('requestfailed', request => {
    const failText = `FAILED: ${request.method()} ${request.url()}\nFailure: ${request.failure()?.errorText}`;
    failedRequests.push(failText);
    console.log('\n' + failText + '\n');
  });

  // Capture ALL requests
  page.on('request', request => {
    allRequests.push(`${request.method()} ${request.url()}`);
  });

  // Capture responses
  page.on('response', response => {
    const status = response.status();
    if (status >= 400) {
      console.log(`\n❌ ${status} ${response.url()}\n`);
    }
  });

  console.log('\n========================================');
  console.log('Starting Settings page navigation...');
  console.log('========================================\n');

  try {
    // Navigate to settings page
    await page.goto(`${PROD_URL}/index.html#/settings`, {
      waitUntil: 'networkidle',
      timeout: 30000,
    });

    console.log('\n✅ Navigation completed\n');

    // Wait a bit to let everything load
    await page.waitForTimeout(5000);

    // Check if error boundary is visible
    const errorBoundary = page.locator('text=應用程序出錯');
    const hasError = await errorBoundary.isVisible().catch(() => false);

    if (hasError) {
      console.log('\n❌ ERROR BOUNDARY IS VISIBLE!\n');

      // Take screenshot
      await page.screenshot({
        path: '/tmp/settings-error-debug.png',
        fullPage: true
      });

      // Get page content
      const pageContent = await page.content();
      console.log('\n=== PAGE HTML (first 500 chars) ===');
      console.log(pageContent.substring(0, 500));
      console.log('...\n');
    } else {
      console.log('\n✅ No error boundary visible\n');
    }

    // Print summary
    console.log('\n========================================');
    console.log('SUMMARY');
    console.log('========================================\n');

    console.log(`Console Messages: ${allConsoleMessages.length}`);
    if (allConsoleMessages.length > 0) {
      console.log('Last 10 console messages:');
      allConsoleMessages.slice(-10).forEach(msg => console.log(`  ${msg}`));
    }

    console.log(`\nPage Errors: ${allErrors.length}`);
    allErrors.forEach(err => console.log(err));

    console.log(`\nFailed Requests: ${failedRequests.length}`);
    failedRequests.forEach(req => console.log(req));

    console.log(`\nTotal Requests: ${allRequests.length}`);
    console.log('Last 10 requests:');
    allRequests.slice(-10).forEach(req => console.log(`  ${req}`));

  } catch (error) {
    console.log('\n❌ EXCEPTION CAUGHT:');
    console.log(error);
  }

  // Keep browser open for 5 seconds
  await page.waitForTimeout(5000);
});
