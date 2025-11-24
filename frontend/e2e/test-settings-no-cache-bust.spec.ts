import { test, expect } from '@playwright/test';

test('Test Settings page without cache busting (simulating user access)', async ({ page, context }) => {
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

  console.log('\n=== Testing WITHOUT cache-busting parameters (simulating real user access) ===');

  // Clear all cache and cookies first
  await context.clearCookies();
  await context.clearPermissions();

  // Visit the production URL exactly as a user would (no timestamp parameter)
  await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html', {
    waitUntil: 'networkidle'
  });

  await page.waitForTimeout(3000);

  console.log('Home page loaded, navigating to Settings...');

  // Navigate to Settings
  const settingsLink = page.locator('a:has-text("設置")').first();
  await settingsLink.click();

  // Wait for loading to complete
  console.log('Waiting for Settings page to load...');
  try {
    await page.waitForFunction(
      () => {
        const loadingText = document.body.textContent?.includes('加载中');
        const errorText = document.body.textContent?.includes('應用程序出錯');
        const hasContent = document.querySelector('h2')?.textContent?.includes('Provider') ||
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

  console.log('\n=== Final Page Status ===');

  const isLoading = pageText?.includes('加载中');
  const hasError = pageText?.includes('應用程序出錯');
  const hasProviderConfig = pageText?.includes('Provider');
  const hasWordPressConfig = pageText?.includes('WordPress');
  const hasCostLimits = pageText?.includes('成本限额') || pageText?.includes('成本限');
  const hasScreenshot = pageText?.includes('截图保留策略') || pageText?.includes('截圖');

  console.log(`Still loading: ${isLoading}`);
  console.log(`❌ Has error page: ${hasError}`);
  console.log(`✅ Has Provider config: ${hasProviderConfig}`);
  console.log(`✅ Has WordPress config: ${hasWordPressConfig}`);
  console.log(`✅ Has Cost Limits: ${hasCostLimits}`);
  console.log(`✅ Has Screenshot section: ${hasScreenshot}`);

  if (hasError) {
    console.log('\n🚨 ERROR PAGE DETECTED! 🚨');
    const errorCount = await page.locator('text=個錯誤').textContent().catch(() => '');
    console.log(`Error count: ${errorCount}`);
  }

  // Print all errors
  console.log('\n=== JavaScript Errors ===');
  if (errors.length === 0) {
    console.log('✅ No page errors detected');
  } else {
    console.log(`❌ Found ${errors.length} errors:`);
    errors.forEach(err => console.log(err));
  }

  console.log('\n=== Console Errors ===');
  if (consoleLogs.length === 0) {
    console.log('✅ No console errors detected');
  } else {
    console.log(`⚠️ Found ${consoleLogs.length} console errors:`);
    consoleLogs.forEach(log => console.log(log));
  }

  await page.screenshot({
    path: 'test-results/settings-no-cache-bust.png',
    fullPage: true
  });

  console.log('\n📸 Screenshot saved to test-results/settings-no-cache-bust.png');

  // Test assertions
  if (hasError) {
    console.log('\n❌ TEST FAILED: Error page is displayed');
  } else if (isLoading) {
    console.log('\n❌ TEST FAILED: Page is still loading');
  } else {
    console.log('\n✅ TEST PASSED: Settings page loaded successfully');
  }

  expect(hasError).toBe(false);
  expect(isLoading).toBe(false);
  expect(hasProviderConfig || hasWordPressConfig).toBe(true);
});
