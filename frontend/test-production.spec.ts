import { test, expect } from '@playwright/test';

test('production site loads correctly', async ({ page }) => {
  // Navigate with cache disabled
  await page.goto('https://storage.googleapis.com/cms-automation-frontend-2025/index.html', {
    waitUntil: 'networkidle',
  });
  
  // Wait a bit for any async loading
  await page.waitForTimeout(2000);
  
  // Take screenshot
  await page.screenshot({ path: 'production-test.png', fullPage: true });
  
  // Check if we can see the app
  const body = await page.textContent('body');
  console.log('Body text length:', body?.length);
  
  // Check console errors
  const errors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  
  await page.reload();
  await page.waitForTimeout(1000);
  
  console.log('Console errors:', errors);
});
