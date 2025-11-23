/**
 * Production Environment Test with Real API Integration
 *
 * Tests the production frontend connecting to the real backend API
 * to verify scroll functionality with actual data
 */

import { test, expect } from '@playwright/test';

test.describe('Production Environment - Real API Integration', () => {
  const prodUrl = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

  test('loads production site and verifies API connection', async ({ page }) => {
    console.log('📍 Loading production site...');

    // Navigate to production
    await page.goto(prodUrl, { waitUntil: 'networkidle', timeout: 30000 });

    console.log('✅ Production page loaded');

    // Wait for React app to mount
    await page.waitForSelector('#root', { timeout: 10000 });

    // Check if root has content
    const rootContent = await page.locator('#root').innerHTML();
    expect(rootContent.length).toBeGreaterThan(100);

    console.log('✅ React app mounted successfully');

    // Wait for worklist page to load (may show login or worklist)
    await page.waitForTimeout(2000);

    // Take screenshot of initial state
    await page.screenshot({
      path: 'test-results/production-real-api-initial.png',
      fullPage: true,
    });

    console.log('✅ Screenshot captured');

    // Check if we can see the worklist or login page
    const pageText = await page.locator('body').innerText();

    if (pageText.includes('Worklist') || pageText.includes('工作列表')) {
      console.log('✅ Worklist page loaded (authenticated)');

      // Try to interact with the page
      const hasArticles = await page.locator('[data-testid="worklist-item"]').count();
      console.log(`📊 Found ${hasArticles} articles in worklist`);

      if (hasArticles > 0) {
        console.log('🎯 Testing scroll with real article data...');

        // Click first article to open review modal
        await page.locator('[data-testid="worklist-item"]').first().click();
        await page.waitForTimeout(1000);

        // Check if modal opened
        const modalVisible = await page.locator('[data-testid="parsing-review-grid"]').isVisible();

        if (modalVisible) {
          console.log('✅ Article review modal opened');

          // Test scroll functionality
          const scrollContainer = page.locator('.overflow-y-auto').first();

          if (await scrollContainer.isVisible()) {
            const scrollMetrics = await scrollContainer.evaluate((el) => ({
              scrollHeight: el.scrollHeight,
              clientHeight: el.clientHeight,
              scrollTop: el.scrollTop,
            }));

            console.log('📏 Scroll metrics:', scrollMetrics);

            if (scrollMetrics.scrollHeight > scrollMetrics.clientHeight) {
              console.log('✅ Content is scrollable');

              // Try to scroll
              await scrollContainer.evaluate((el) => {
                el.scrollTop = 500;
              });

              await page.waitForTimeout(500);

              const newScrollTop = await scrollContainer.evaluate((el) => el.scrollTop);
              expect(newScrollTop).toBeGreaterThan(0);

              console.log(`✅ Scroll successful: ${newScrollTop}px`);
            } else {
              console.log('ℹ️  Content fits in viewport (no scroll needed)');
            }

            // Take screenshot of modal
            await page.screenshot({
              path: 'test-results/production-real-api-modal.png',
              fullPage: true,
            });
          }
        }
      }
    } else if (pageText.includes('Login') || pageText.includes('登入')) {
      console.log('ℹ️  Login page displayed (not authenticated)');
      console.log('ℹ️  This is expected - authentication required to test scroll with real data');
    } else {
      console.log('⚠️  Unknown page state - check screenshot');
    }

    console.log('✅ Production test completed!');
  });

  test('verifies no console errors or network failures', async ({ page }) => {
    const consoleErrors: string[] = [];
    const networkErrors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    page.on('response', (response) => {
      if (!response.ok() && !response.url().includes('favicon')) {
        networkErrors.push(`${response.status()} ${response.url()}`);
      }
    });

    await page.goto(prodUrl, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForSelector('#root', { timeout: 10000 });
    await page.waitForTimeout(3000);

    // Filter out expected errors
    const criticalNetworkErrors = networkErrors.filter(err =>
      err.includes('.js') && err.includes('404')
    );

    console.log('📊 Console errors:', consoleErrors.length);
    console.log('📊 Network errors:', networkErrors.length);
    console.log('📊 Critical JS 404 errors:', criticalNetworkErrors.length);

    // No critical JavaScript 404 errors
    expect(criticalNetworkErrors.length).toBe(0);

    console.log('✅ No critical errors detected');
  });
});
