import { test, expect } from '@playwright/test';

test('Settings page API calls', async ({ page }) => {
  const apiCalls: { url: string; status: number; method: string }[] = [];

  // Intercept all responses
  page.on('response', response => {
    const url = response.url();
    if (url.includes('/v1/') || url.includes('/api/v1/') || url.includes('cms-automation-backend')) {
      apiCalls.push({
        url: url,
        status: response.status(),
        method: response.request().method()
      });
      console.log(`← ${response.status()} ${url}`);
    }
  });

  console.log('\n=== Loading app.html ===');
  await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/app.html', {
    waitUntil: 'networkidle'
  });

  await page.waitForTimeout(2000);

  console.log('\n=== Looking for Settings link ===');

  // Try multiple selectors
  const selectors = [
    'a:has-text("設置")',
    'a:has-text("Settings")',
    'a[href*="settings"]',
    'nav a:has-text("設置")',
  ];

  let clicked = false;
  for (const selector of selectors) {
    try {
      const link = page.locator(selector).first();
      if (await link.count() > 0) {
        console.log(`Found link with selector: ${selector}`);
        await link.click();
        clicked = true;
        break;
      }
    } catch (e) {
      // Try next selector
    }
  }

  if (!clicked) {
    console.log('Trying direct navigation...');
    await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/app.html#/settings');
  }

  await page.waitForTimeout(5000);

  await page.screenshot({ path: 'test-results/settings-page-test.png', fullPage: true });

  console.log('\n=== API Calls Summary ===');
  console.log(`Total API calls: ${apiCalls.length}`);

  const v1Calls = apiCalls.filter(c => c.url.includes('/v1/') && !c.url.includes('/api/v1/'));
  const apiV1Calls = apiCalls.filter(c => c.url.includes('/api/v1/'));

  console.log(`Correct calls (/v1/): ${v1Calls.length}`);
  console.log(`Wrong calls (/api/v1/): ${apiV1Calls.length}`);

  if (v1Calls.length > 0) {
    console.log('\n✅ Correct API calls:');
    v1Calls.forEach(c => console.log(`  ${c.status} ${c.method} ${c.url}`));
  }

  if (apiV1Calls.length > 0) {
    console.log('\n❌ Wrong API calls:');
    apiV1Calls.forEach(c => console.log(`  ${c.status} ${c.method} ${c.url}`));
  }

  expect(apiV1Calls.length).toBe(0);

  if (v1Calls.length > 0) {
    const successCalls = v1Calls.filter(c => c.status === 200);
    console.log(`\n✅ Successful calls: ${successCalls.length}/${v1Calls.length}`);
  }
});
