import { test, expect } from '@playwright/test';

test('Test Settings page with full loading wait', async ({ page }) => {
  const errors: string[] = [];
  const consoleLogs: string[] = [];

  // Capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleLogs.push(`CONSOLE ERROR: ${msg.text()}`);
    }
  });

  // Capture page errors
  page.on('pageerror', error => {
    errors.push(`PAGE ERROR: ${error.message}\n${error.stack}`);
  });

  // Test with real production URL and cache-busting timestamp
  const timestamp = Date.now();
  console.log(`\nTesting with timestamp: ${timestamp}`);
  await page.goto(`https://storage.googleapis.com/cms-automation-frontend-2025/index.html?t=${timestamp}`, {
    waitUntil: 'networkidle'
  });

  await page.waitForTimeout(3000);

  // Navigate to Settings
  console.log('\nNavigating to Settings page...');
  const settingsLink = page.locator('a:has-text("設置")').first();
  await settingsLink.click();

  // Wait for loading spinner to disappear OR error page to appear
  console.log('Waiting for page to load...');
  try {
    await page.waitForFunction(
      () => {
        const loadingText = document.body.textContent?.includes('加载中');
        const errorText = document.body.textContent?.includes('應用程序出錯');
        const hasContent = document.querySelector('[class*="Provider"]') !== null ||
                          document.querySelector('[class*="WordPress"]') !== null ||
                          document.querySelector('h2')?.textContent?.includes('Provider') ||
                          document.querySelector('h2')?.textContent?.includes('WordPress');
        return !loadingText || errorText || hasContent;
      },
      { timeout: 30000 }
    );
  } catch (e) {
    console.log('Timeout waiting for page to load');
  }

  await page.waitForTimeout(5000);

  // Check page state
  const pageText = await page.textContent('body');
  console.log('\n=== Page Status ===');

  const isLoading = pageText?.includes('加载中');
  const hasError = pageText?.includes('應用程序出錯');
  const hasProviderConfig = pageText?.includes('Provider') || pageText?.includes('Playwright');
  const hasWordPressConfig = pageText?.includes('WordPress');
  const hasCostLimits = pageText?.includes('成本限额') || pageText?.includes('成本限');
  const hasScreenshot = pageText?.includes('截图保留策略') || pageText?.includes('截圖');

  console.log(`Still loading: ${isLoading}`);
  console.log(`Has error page: ${hasError}`);
  console.log(`Has Provider config: ${hasProviderConfig}`);
  console.log(`Has WordPress config: ${hasWordPressConfig}`);
  console.log(`Has Cost Limits: ${hasCostLimits}`);
  console.log(`Has Screenshot section: ${hasScreenshot}`);

  // Print all errors
  console.log('\n=== JavaScript Errors ===');
  if (errors.length === 0) {
    console.log('No page errors detected');
  } else {
    errors.forEach(err => console.log(err));
  }

  console.log('\n=== Console Errors ===');
  if (consoleLogs.length === 0) {
    console.log('No console errors detected');
  } else {
    consoleLogs.forEach(log => console.log(log));
  }

  await page.screenshot({
    path: 'test-results/settings-wait-loaded.png',
    fullPage: true
  });

  console.log('\nScreenshot saved to test-results/settings-wait-loaded.png');

  // Test should fail if error page is shown or still loading
  expect(hasError).toBe(false);
  expect(isLoading).toBe(false);
});
