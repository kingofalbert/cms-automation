/**
 * Real Scroll Test with Forced Overflow
 *
 * This test actually FORCES content to overflow and verifies scrolling works
 */

import { test, expect } from '@playwright/test';

const PROD_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

test.describe('Real Scroll Test with Overflow', () => {
  test('forces content overflow and verifies scrolling actually works', async ({ page }) => {
    console.log('🔍 Starting REAL scroll test with forced overflow...');

    // Navigate to production
    await page.goto(PROD_URL.replace('/index.html', '') + '#/worklist', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Open modal
    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toBeVisible({ timeout: 30000 });
    await firstRow.click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 20000 });

    // Wait for loading
    const loadingText = page.locator('text=/加载文章审核数据|Loading article review/i');
    if (await loadingText.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(loadingText).not.toBeVisible({ timeout: 30000 });
    }

    // Click parsing tab
    const parsingTab = page.locator('button:has-text("解析审核"), button:has-text("Parsing Review")').first();
    if (await parsingTab.isVisible()) {
      await parsingTab.click();
      await page.waitForTimeout(1000);
    }

    console.log('✅ Modal opened and parsing tab active');

    // Find scroll container
    const scrollContainer = modal.locator('.overflow-y-auto').first();
    await expect(scrollContainer).toBeVisible();

    // FORCE content to overflow by injecting tall content
    console.log('📝 Injecting tall content to force overflow...');

    await scrollContainer.evaluate((el) => {
      // Add a very tall div to force overflow
      const tallDiv = document.createElement('div');
      tallDiv.style.height = '3000px';
      tallDiv.style.background = 'linear-gradient(red, blue)';
      tallDiv.style.marginTop = '20px';
      tallDiv.setAttribute('data-test-overflow', 'true');
      tallDiv.innerHTML = '<h1 style="color: white; padding: 20px;">FORCED OVERFLOW TEST CONTENT</h1>';
      el.appendChild(tallDiv);
    });

    await page.waitForTimeout(500);

    // NOW test scrolling with actual overflow
    const metrics = await scrollContainer.evaluate((el) => ({
      scrollHeight: el.scrollHeight,
      clientHeight: el.clientHeight,
      scrollTop: el.scrollTop,
    }));

    console.log('Metrics after adding tall content:', metrics);
    console.log(`  - Content height: ${metrics.scrollHeight}px`);
    console.log(`  - Viewport height: ${metrics.clientHeight}px`);
    console.log(`  - Overflow: ${metrics.scrollHeight - metrics.clientHeight}px`);

    // Verify overflow exists
    expect(metrics.scrollHeight).toBeGreaterThan(metrics.clientHeight);
    console.log('✅ Content now overflows viewport');

    // Test 1: Scroll down by 500px
    console.log('\n🧪 Test 1: Scrolling down 500px...');
    await scrollContainer.evaluate((el) => {
      el.scrollTop = 500;
    });
    await page.waitForTimeout(300);

    const scrollTop1 = await scrollContainer.evaluate((el) => el.scrollTop);
    console.log(`  Scroll position: ${scrollTop1}px`);

    if (scrollTop1 < 400) {
      console.log('❌ FAILED: Could not scroll down! scrollTop =', scrollTop1);

      // Debug: Check computed styles
      const styles = await scrollContainer.evaluate((el) => {
        const computed = window.getComputedStyle(el);
        return {
          overflow: computed.overflow,
          overflowY: computed.overflowY,
          overflowX: computed.overflowX,
          height: computed.height,
          maxHeight: computed.maxHeight,
          display: computed.display,
          position: computed.position,
        };
      });
      console.log('Container computed styles:', styles);

      throw new Error(`Scrolling FAILED! Could only scroll to ${scrollTop1}px instead of 500px`);
    }

    expect(scrollTop1).toBeGreaterThanOrEqual(400);
    console.log('✅ Test 1 PASSED: Scroll down works');

    // Test 2: Scroll to bottom
    console.log('\n🧪 Test 2: Scrolling to bottom...');
    await scrollContainer.evaluate((el) => {
      el.scrollTop = el.scrollHeight;
    });
    await page.waitForTimeout(300);

    const scrollTop2 = await scrollContainer.evaluate((el) => el.scrollTop);
    const maxScroll = metrics.scrollHeight - metrics.clientHeight;
    console.log(`  Scroll position: ${scrollTop2}px (max: ${maxScroll}px)`);

    expect(scrollTop2).toBeGreaterThanOrEqual(maxScroll * 0.9);
    console.log('✅ Test 2 PASSED: Scroll to bottom works');

    // Test 3: Scroll back to top
    console.log('\n🧪 Test 3: Scrolling back to top...');
    await scrollContainer.evaluate((el) => {
      el.scrollTop = 0;
    });
    await page.waitForTimeout(300);

    const scrollTop3 = await scrollContainer.evaluate((el) => el.scrollTop);
    console.log(`  Scroll position: ${scrollTop3}px`);

    expect(scrollTop3).toBeLessThan(10);
    console.log('✅ Test 3 PASSED: Scroll to top works');

    console.log('\n🎉 ALL SCROLL TESTS PASSED!');
    console.log('═══════════════════════════════════════');
    console.log('Scrolling functionality is WORKING in production!');
    console.log('═══════════════════════════════════════');
  });
});
