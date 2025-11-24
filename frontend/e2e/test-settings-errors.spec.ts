import { test } from '@playwright/test';

test('Check Settings page console errors', async ({ page }) => {
  const errors: string[] = [];
  const consoleMessages: string[] = [];

  // Capture console messages
  page.on('console', msg => {
    const text = msg.text();
    consoleMessages.push(`[${msg.type()}] ${text}`);
    if (msg.type() === 'error') {
      errors.push(text);
    }
  });

  // Capture page errors
  page.on('pageerror', error => {
    errors.push(`Page error: ${error.message}`);
  });

  await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/app.html', {
    waitUntil: 'networkidle'
  });

  await page.waitForTimeout(2000);

  // Click Settings link
  const link = page.locator('a:has-text("設置")').first();
  await link.click();

  await page.waitForTimeout(5000);

  console.log('\n=== Console Messages ===');
  consoleMessages.forEach(msg => console.log(msg));

  console.log('\n=== Errors ===');
  errors.forEach(err => console.log(err));

  // Check page content
  const pageText = await page.locator('body').textContent();
  console.log('\n=== Page text (first 500 chars) ===');
  console.log(pageText?.substring(0, 500));

  // Try to click error details button if available
  const detailsButton = page.locator('button:has-text("顯示詳情")');
  if (await detailsButton.count() > 0) {
    console.log('\n=== Clicking error details button ===');
    await detailsButton.click();
    await page.waitForTimeout(1000);
    const errorDetailsText = await page.locator('#error-details').textContent();
    console.log('\n=== Error Details ===');
    console.log(errorDetailsText);
  } else {
    console.log('\n=== No error details button available (production mode) ===');
  }

  // Take screenshot
  await page.screenshot({ path: 'test-results/error-page.png', fullPage: true });
});
