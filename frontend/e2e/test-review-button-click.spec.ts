import { test, expect } from '@playwright/test';

test.describe('Review Button Click Test', () => {
  test('should click review button and check for errors', async ({ page }) => {
    // Collect console messages
    const consoleMessages: { type: string; text: string }[] = [];
    page.on('console', (msg) => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text(),
      });
    });

    // Collect page errors
    const pageErrors: Error[] = [];
    page.on('pageerror', (error) => {
      pageErrors.push(error);
      console.log(`❌ Page Error: ${error.message}`);
      console.log(`   Stack: ${error.stack}`);
    });

    // Collect failed requests
    const failedRequests: { url: string; error: string | null }[] = [];
    page.on('requestfailed', (request) => {
      failedRequests.push({
        url: request.url(),
        error: request.failure()?.errorText || null,
      });
      console.log(`❌ Failed Request: ${request.url()}`);
      console.log(`   Error: ${request.failure()?.errorText}`);
    });

    // Navigate to worklist page
    console.log('📍 Navigating to worklist page...');
    await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html#/worklist');

    // Wait for page to load
    await page.waitForTimeout(3000);

    // Take screenshot before click
    await page.screenshot({ path: '/tmp/before-review-click.png', fullPage: true });

    console.log('📍 Looking for review button...');

    // Find the first review button
    const reviewButton = page.getByRole('button', { name: /审核|review/i }).first();
    const buttonExists = await reviewButton.count();

    console.log(`✅ Found ${buttonExists} review button(s)`);

    if (buttonExists > 0) {
      console.log('🖱️ Clicking review button...');
      await reviewButton.click();

      // Wait for navigation or modal to appear
      await page.waitForTimeout(5000);

      // Take screenshot after click
      await page.screenshot({ path: '/tmp/after-review-click.png', fullPage: true });

      console.log('\n=== Console Messages After Click ===');
      const recentMessages = consoleMessages.slice(-20);
      recentMessages.forEach((msg, idx) => {
        console.log(`[${msg.type}] ${msg.text}`);
      });

      console.log('\n=== Page Errors ===');
      pageErrors.forEach((err, idx) => {
        console.log(`${idx + 1}. ${err.message}`);
      });

      console.log('\n=== Failed Requests ===');
      failedRequests.forEach((req) => {
        console.log(`URL: ${req.url}`);
        console.log(`Error: ${req.error}`);
      });

      // Check current URL
      const currentUrl = page.url();
      console.log(`\n📍 Current URL: ${currentUrl}`);

      // Check for error dialogs
      const errorDialog = await page.locator('[role="alert"], .error-message, .alert-error').count();
      console.log(`\n⚠️  Error Dialogs: ${errorDialog}`);

      if (errorDialog > 0) {
        const errorText = await page.locator('[role="alert"], .error-message, .alert-error').first().textContent();
        console.log(`Error Text: ${errorText}`);
      }

      // Check for error boundary
      const errorBoundary = await page.locator('text=/应用程序遇到|遇到了.*个错误|error/i').count();
      console.log(`\n🚨 Error Boundary Messages: ${errorBoundary}`);

      if (errorBoundary > 0) {
        const boundaryText = await page.locator('text=/应用程序遇到|遇到了.*个错误|error/i').first().textContent();
        console.log(`Error Boundary Text: ${boundaryText}`);
      }
    } else {
      console.log('❌ No review button found!');
    }

    // Final assertions
    console.log('\n=== Test Summary ===');
    console.log(`Total Console Messages: ${consoleMessages.length}`);
    console.log(`Total Page Errors: ${pageErrors.length}`);
    console.log(`Total Failed Requests: ${failedRequests.length}`);

    // Don't fail the test, just report
    // expect(pageErrors.length).toBe(0);
  });
});
