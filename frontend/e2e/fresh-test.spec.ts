import { test, chromium } from '@playwright/test';

test('Fresh browser test - settings page', async () => {
  // Launch completely fresh browser with no cache
  const browser = await chromium.launch();
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  // Monitor network requests
  page.on('request', request => {
    if (request.url().includes('settings')) {
      console.log('📤 REQUEST:', request.method(), request.url());
    }
  });

  page.on('response', async response => {
    if (response.url().includes('settings')) {
      console.log('📥 RESPONSE:', response.status(), response.url());
    }
  });

  // Navigate to production site
  await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html', {
    waitUntil: 'networkidle',
  });

  console.log('✅ Page loaded');

  // Wait for React to render
  await page.waitForTimeout(2000);

  // Find and click settings link
  const settingsLink = page.locator('a[href*="settings"], a:has-text("設置")').first();
  await settingsLink.waitFor({ timeout: 10000 });
  await settingsLink.click();

  console.log('✅ Clicked settings link');

  // Wait for API call
  await page.waitForTimeout(3000);

  // Take screenshot
  await page.screenshot({ path: 'fresh-test-settings.png', fullPage: true });
  console.log('📸 Screenshot saved');

  // Check page content
  const content = await page.locator('body').textContent();
  console.log('📄 Page has 403?', content?.includes('403'));
  console.log('📄 Page has error?', content?.includes('Request failed'));

  await browser.close();
});
