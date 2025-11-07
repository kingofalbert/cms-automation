import { test, expect } from '@playwright/test';

test.describe('Worklist Page Error Diagnosis', () => {
  test('should load worklist page without errors', async ({ page }) => {
    // Collect console errors
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Collect page errors
    const pageErrors: Error[] = [];
    page.on('pageerror', (error) => {
      pageErrors.push(error);
    });

    // Navigate to worklist page
    await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html#/worklist');

    // Wait for page to load
    await page.waitForTimeout(5000);

    // Take screenshot
    await page.screenshot({ path: '/tmp/worklist-error-diagnosis.png', fullPage: true });

    // Check for error messages on page
    const errorText = await page.textContent('body').catch(() => '');

    console.log('=== Console Errors ===');
    consoleErrors.forEach((err, idx) => {
      console.log(`${idx + 1}. ${err}`);
    });

    console.log('\n=== Page Errors ===');
    pageErrors.forEach((err, idx) => {
      console.log(`${idx + 1}. ${err.message}`);
      console.log(`   Stack: ${err.stack}`);
    });

    console.log('\n=== Page Text Content ===');
    console.log(errorText.substring(0, 500));

    // Check if error dialog is present
    const errorDialog = await page.locator('[role="alert"], .error, .alert-error').count();
    console.log(`\n=== Error Dialogs Found: ${errorDialog} ===`);

    if (errorDialog > 0) {
      const errorMessage = await page.locator('[role="alert"], .error, .alert-error').first().textContent();
      console.log(`Error Message: ${errorMessage}`);
    }

    // Log network requests
    page.on('requestfailed', (request) => {
      console.log(`❌ Failed request: ${request.url()}`);
      console.log(`   Failure: ${request.failure()?.errorText}`);
    });

    // Expect no errors
    expect(consoleErrors.length).toBe(0);
    expect(pageErrors.length).toBe(0);
  });

  test('should check API connectivity', async ({ page }) => {
    const responses: { url: string; status: number; statusText: string }[] = [];

    page.on('response', (response) => {
      if (response.url().includes('cms-automation-backend')) {
        responses.push({
          url: response.url(),
          status: response.status(),
          statusText: response.statusText(),
        });
      }
    });

    await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html#/worklist');
    await page.waitForTimeout(5000);

    console.log('\n=== API Responses ===');
    responses.forEach((resp) => {
      console.log(`${resp.status} ${resp.statusText} - ${resp.url}`);
    });

    // Take screenshot
    await page.screenshot({ path: '/tmp/worklist-api-check.png', fullPage: true });
  });
});
