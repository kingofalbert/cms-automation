import { test } from '@playwright/test';

test('diagnose 404 resources on review page', async ({ page }) => {
  const failedRequests: Array<{ url: string; status: number; method: string }> = [];

  // Capture all failed requests
  page.on('response', (response) => {
    if (response.status() === 404) {
      failedRequests.push({
        url: response.url(),
        status: response.status(),
        method: response.request().method(),
      });
    }
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

  // Log all 404 requests
  console.log('\n=== 404 RESOURCES ===');
  if (failedRequests.length === 0) {
    console.log('No 404 errors found!');
  } else {
    failedRequests.forEach((req, index) => {
      console.log(`\n[${index + 1}] ${req.method} ${req.status}`);
      console.log(`URL: ${req.url}`);
    });
  }

  // Take screenshot
  await page.screenshot({ path: '/tmp/diagnose-404-resources.png', fullPage: true });
  console.log('\nScreenshot saved to /tmp/diagnose-404-resources.png');
});
