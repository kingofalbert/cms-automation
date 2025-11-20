/**
 * Final Production Verification Test
 * Confirms worklist displays articles correctly
 */

import { test, expect } from '@playwright/test';

test('Production worklist displays articles', async ({ page }) => {
  const prodUrl = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

  console.log('📍 Opening production site...');
  await page.goto(prodUrl, { waitUntil: 'networkidle', timeout: 30000 });

  // Wait for React to mount
  await page.waitForSelector('#root', { timeout: 10000 });
  console.log('✅ React app mounted');

  // Wait for worklist page
  await page.waitForSelector('text=Worklist', { timeout: 10000 });
  console.log('✅ Worklist page loaded');

  // Wait for table to appear (not loading state)
  await page.waitForSelector('table tbody tr', { timeout: 15000 });
  console.log('✅ Article table rendered');

  // Count articles in table
  const articleCount = await page.locator('table tbody tr').count();
  console.log(`📊 Found ${articleCount} articles in table`);

  // Take screenshot
  await page.screenshot({
    path: '/tmp/production-final-verification.png',
    fullPage: true,
  });
  console.log('📸 Screenshot saved: /tmp/production-final-verification.png');

  // Verify we have articles
  expect(articleCount).toBeGreaterThan(0);

  // Check that we're not stuck in loading state
  const loadingText = await page.locator('text=Loading').count();
  expect(loadingText).toBe(0);

  console.log('\n=== ✅ SUCCESS ===');
  console.log(`Worklist is displaying ${articleCount} articles correctly!`);
});
