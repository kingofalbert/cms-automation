import { test, expect } from '@playwright/test';

test.describe('Check SEO Suggestions in Article Drawer', () => {
  test('should open article drawer and check SEO fields', async ({ page }) => {
    console.log('🚀 Opening frontend...');
    await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    console.log('✅ Page loaded');

    // Take initial screenshot
    await page.screenshot({ path: '/tmp/step1-worklist.png', fullPage: true });

    // Find the eye icon buttons (view buttons)
    const viewButtons = page.locator('button[aria-label*="View"], button:has-text("👁"), svg.lucide-eye').locator('..');
    const count = await viewButtons.count();
    console.log(`Found ${count} view buttons`);

    if (count === 0) {
      // Try alternative selector - rows with eye icon
      const rows = page.locator('tr');
      const rowCount = await rows.count();
      console.log(`Found ${rowCount} table rows`);

      if (rowCount > 1) {
        // Click on the first data row (skip header)
        console.log('Clicking on first row...');
        const firstRow = rows.nth(1);
        await firstRow.click();
        await page.waitForTimeout(2000);
      }
    } else {
      // Click the first view button
      console.log('Clicking first view button...');
      await viewButtons.first().click();
      await page.waitForTimeout(2000);
    }

    // Take screenshot after click
    await page.screenshot({ path: '/tmp/step2-drawer-opened.png', fullPage: true });

    // Wait for drawer to appear
    await page.waitForTimeout(2000);

    // Look for SEO-related text in the page
    const pageText = await page.textContent('body');
    const hasSEO = pageText?.includes('SEO') || pageText?.includes('建议') || pageText?.includes('suggested');
    console.log(`\n🔍 Page contains SEO-related text: ${hasSEO}`);

    // Try to find specific SEO fields
    const seoFieldsFound = {
      meta_description: await page.locator('text=meta_description, text=Meta Description, text=元描述').count() > 0,
      keywords: await page.locator('text=keywords, text=Keywords, text=关键词').count() > 0,
      titles: await page.locator('text=title, text=Title, text=标题').count() > 0,
    };

    console.log('\n📋 SEO Fields Found:');
    console.log(JSON.stringify(seoFieldsFound, null, 2));

    // Get all text content for analysis
    const allText = await page.evaluate(() => {
      const getText = (el: Element): string => {
        if (el.textContent) {
          const text = el.textContent.trim();
          if (text.length > 0 && text.length < 200) {
            return text;
          }
        }
        return '';
      };

      const labels = Array.from(document.querySelectorAll('label, .label, [class*="label"]'));
      const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
      const divs = Array.from(document.querySelectorAll('[class*="field"], [class*="Field"]'));

      return {
        labels: labels.map(getText).filter(t => t),
        headings: headings.map(getText).filter(t => t),
        fields: divs.map(getText).filter(t => t).slice(0, 20)
      };
    });

    console.log('\n📝 Page Content Analysis:');
    console.log('Labels found:', allText.labels.slice(0, 10));
    console.log('Headings found:', allText.headings.slice(0, 10));

    // Final screenshot
    await page.screenshot({ path: '/tmp/step3-final-state.png', fullPage: true });
    console.log('\n📸 All screenshots saved to /tmp/');
  });
});
