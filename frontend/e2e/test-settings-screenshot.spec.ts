import { test } from '@playwright/test';

test('Take Settings page screenshot', async ({ page }) => {
  await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/app.html', {
    waitUntil: 'networkidle'
  });

  await page.waitForTimeout(2000);

  // Click Settings link
  const link = page.locator('a:has-text("設置")').first();
  await link.click();

  await page.waitForTimeout(3000);

  await page.screenshot({ 
    path: 'test-results/settings-page-fixed.png', 
    fullPage: true 
  });
  
  console.log('Screenshot saved to test-results/settings-page-fixed.png');
});
