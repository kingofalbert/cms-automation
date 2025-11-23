import { test, expect } from '@playwright/test';

const PROD_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

test('Production scrolling works after h-full fix', async ({ page }) => {
  console.log('🧪 Testing production scrolling...');
  
  await page.goto(PROD_URL, { waitUntil: 'networkidle', timeout: 30000 });
  console.log('✅ Loaded production');

  await page.waitForSelector('table tbody tr', { timeout: 10000 });
  console.log('✅ Worklist loaded');

  await page.locator('table tbody tr').first().click();
  console.log('✅ Clicked first article');

  await page.waitForSelector('[data-testid="parsing-review-grid"]', { timeout: 10000 });
  console.log('✅ Modal opened');

  const scrollContainer = page.locator('div.overflow-y-auto').filter({ 
    has: page.locator('[data-testid="parsing-review-grid"]') 
  });

  await expect(scrollContainer).toBeVisible();
  console.log('✅ Scroll container found');

  await scrollContainer.evaluate((el) => {
    const tallDiv = document.createElement('div');
    tallDiv.style.height = '5000px';
    tallDiv.style.background = 'linear-gradient(red, blue)';
    el.appendChild(tallDiv);
  });
  console.log('✅ Injected 5000px content');

  await page.waitForTimeout(500);

  const scrollHeight = await scrollContainer.evaluate(el => el.scrollHeight);
  const clientHeight = await scrollContainer.evaluate(el => el.clientHeight);
  console.log(`📊 scrollHeight: ${scrollHeight}, clientHeight: ${clientHeight}`);

  expect(scrollHeight).toBeGreaterThan(clientHeight);
  console.log('✅ Container IS scrollable');

  await scrollContainer.evaluate((el) => { el.scrollTop = 500; });
  await page.waitForTimeout(300);

  const scrolledTop = await scrollContainer.evaluate(el => el.scrollTop);
  console.log(`📊 scrollTop: ${scrolledTop}`);

  expect(scrolledTop).toBeGreaterThan(0);
  console.log('✅ SCROLLING WORKS!');
  console.log('✨ ALL TESTS PASSED!');
});
