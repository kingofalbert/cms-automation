/**
 * Production Visual Test - Verify worklist loads articles
 */

import { test, expect } from '@playwright/test';

test('Production worklist visual verification', async ({ page }) => {
  const prodUrl = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

  console.log('📍 Opening production site...');
  await page.goto(prodUrl, { waitUntil: 'networkidle', timeout: 30000 });

  // Wait for React to mount
  await page.waitForSelector('#root', { timeout: 10000 });
  console.log('✅ Page loaded');

  // Wait for app to initialize
  await page.waitForTimeout(3000);

  // Take initial screenshot
  await page.screenshot({
    path: '/tmp/production-current-state.png',
    fullPage: true,
  });
  console.log('📸 Screenshot saved: /tmp/production-current-state.png');

  // Check page text
  const bodyText = await page.locator('body').innerText();
  console.log('\n=== Page Content ===');
  console.log(bodyText.substring(0, 500));

  // Check for loading state
  const hasLoading = bodyText.includes('Loading') || bodyText.includes('loading');
  console.log(`\n❓ Has "Loading" text: ${hasLoading}`);

  // Check for worklist
  const hasWorklist = bodyText.includes('Worklist') || bodyText.includes('工作列表');
  console.log(`❓ Has "Worklist" text: ${hasWorklist}`);

  // Count article items
  const articleCount = await page.locator('tbody tr, [role="row"]').count();
  console.log(`📊 Article rows found: ${articleCount}`);

  // Check for error messages
  const hasError = bodyText.toLowerCase().includes('error') || bodyText.toLowerCase().includes('错误');
  console.log(`❓ Has error message: ${hasError}`);

  // Check network requests
  const apiCalls: string[] = [];
  page.on('response', (response) => {
    if (response.url().includes('/v1/worklist')) {
      apiCalls.push(`${response.status()} - ${response.url()}`);
    }
  });

  // Refresh to see network calls
  await page.reload({ waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  console.log('\n=== API Calls ===');
  apiCalls.forEach(call => console.log(call));

  // Final screenshot
  await page.screenshot({
    path: '/tmp/production-after-reload.png',
    fullPage: true,
  });
  console.log('📸 After reload screenshot saved');

  // Output summary
  console.log('\n=== TEST SUMMARY ===');
  console.log(`✅ Page accessible: YES`);
  console.log(`📊 Articles visible: ${articleCount > 0 ? 'YES (' + articleCount + ')' : 'NO'}`);
  console.log(`⚠️  Still loading: ${hasLoading ? 'YES' : 'NO'}`);
  console.log(`❌ Has errors: ${hasError ? 'YES' : 'NO'}`);
});
