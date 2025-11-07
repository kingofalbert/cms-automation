import { test } from '@playwright/test';

test('diagnose console errors on review page', async ({ page }) => {
  const consoleMessages: Array<{ type: string; text: string }> = [];
  const pageErrors: Error[] = [];

  // Capture all console messages
  page.on('console', (msg) => {
    consoleMessages.push({
      type: msg.type(),
      text: msg.text(),
    });
  });

  // Capture page errors
  page.on('pageerror', (error) => {
    pageErrors.push(error);
  });

  // Navigate to worklist
  await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html#/worklist', {
    waitUntil: 'networkidle',
  });

  // Clear storage and reload
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.reload({ waitUntil: 'networkidle' });

  console.log('Navigating to worklist...');
  await page.waitForTimeout(2000);

  // Click review button
  const reviewButton = page.getByRole('button', { name: /审核|review/i }).first();
  await reviewButton.click();

  console.log('Clicked review button, waiting for page to load...');
  await page.waitForTimeout(5000);

  // Log all console messages
  console.log('\n=== ALL CONSOLE MESSAGES ===');
  consoleMessages.forEach((msg, index) => {
    console.log(`[${index + 1}] ${msg.type.toUpperCase()}: ${msg.text}`);
  });

  // Log page errors
  console.log('\n=== PAGE ERRORS ===');
  pageErrors.forEach((error, index) => {
    console.log(`[${index + 1}] ${error.name}: ${error.message}`);
    console.log(`Stack: ${error.stack}`);
  });

  // Take screenshot
  await page.screenshot({ path: '/tmp/diagnose-console-errors.png', fullPage: true });
  console.log('\nScreenshot saved to /tmp/diagnose-console-errors.png');
});
