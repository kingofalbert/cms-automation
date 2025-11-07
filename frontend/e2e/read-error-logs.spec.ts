import { test } from '@playwright/test';

test('read error logs from localStorage', async ({ page }) => {
  await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html#/worklist', {
    waitUntil: 'networkidle',
  });

  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.reload({ waitUntil: 'networkidle' });

  console.log('Navigating to worklist...');
  await page.waitForTimeout(2000);

  const reviewButton = page.getByRole('button', { name: /审核|review/i }).first();
  await reviewButton.click();

  console.log('Clicked review button, waiting for errors...');
  await page.waitForTimeout(5000);

  const errorLogs = await page.evaluate(() => {
    const stored = localStorage.getItem('cms_automation_error_logs');
    return stored ? JSON.parse(stored) : [];
  });

  console.log('\n=== ERROR LOGS ===');
  if (errorLogs.length === 0) {
    console.log('No error logs found');
  } else {
    console.log('Found ' + errorLogs.length + ' error logs\n');

    errorLogs.slice(0, 3).forEach((log: any, i: number) => {
      console.log('\n[LOG ' + (i + 1) + ']');
      console.log('Message: ' + log.message);
      if (log.stack) {
        console.log('\nStack:\n' + log.stack);
      }
      if (log.componentStack) {
        console.log('\nComponent Stack:\n' + log.componentStack);
      }
    });
  }
});
