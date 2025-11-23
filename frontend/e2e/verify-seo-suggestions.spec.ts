import { test, expect } from '@playwright/test';

test.describe('SEO Suggestions Verification', () => {
  test('should show SEO suggestions for newly imported articles', async ({ page }) => {
    // 1. Open the frontend
    await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html');

    // Wait for page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    console.log('✅ Page loaded');

    // 2. Check if worklist is visible
    const worklistVisible = await page.locator('text=工作列表').isVisible().catch(() => false);
    console.log(`Worklist visible: ${worklistVisible}`);

    // 3. Take screenshot of the page
    await page.screenshot({ path: '/tmp/frontend-home.png', fullPage: true });
    console.log('📸 Screenshot saved: /tmp/frontend-home.png');

    // 4. Try to find worklist items
    await page.waitForTimeout(2000);
    const items = await page.locator('[data-testid="worklist-item"], .worklist-item, article, li').all();
    console.log(`Found ${items.length} potential worklist items`);

    // 5. Take another screenshot
    await page.screenshot({ path: '/tmp/frontend-worklist.png', fullPage: true });

    // 6. Try to click on the first item if exists
    if (items.length > 0) {
      console.log('Clicking on first item...');
      await items[0].click();
      await page.waitForTimeout(2000);

      // Take screenshot of detail view
      await page.screenshot({ path: '/tmp/frontend-detail.png', fullPage: true });
      console.log('📸 Detail screenshot saved');

      // Look for SEO suggestion fields
      const pageContent = await page.content();
      const hasSEOTitle = pageContent.includes('SEO') || pageContent.includes('标题建议') || pageContent.includes('suggested');
      console.log(`Has SEO content: ${hasSEOTitle}`);
    }

    // 7. Check API directly
    const response = await page.evaluate(async () => {
      try {
        const res = await fetch('https://cms-automation-backend-baau2zqeqq-ue.a.run.app/v1/worklist');
        const data = await res.json();
        return {
          success: true,
          total: data.items?.length || 0,
          items: data.items?.slice(0, 2).map((item: any) => ({
            id: item.id,
            status: item.status,
            title: item.title,
            article_id: item.article_id,
            created_at: item.created_at
          }))
        };
      } catch (error) {
        return { success: false, error: String(error) };
      }
    });

    console.log('\n📊 API Response:');
    console.log(JSON.stringify(response, null, 2));

    // 8. If we have items, check the newest one
    if (response.success && response.items && response.items.length > 0) {
      const newestItem = response.items[0];
      console.log(`\n🔍 Checking newest item ID ${newestItem.id}...`);

      const itemDetail = await page.evaluate(async (itemId) => {
        try {
          const res = await fetch(`https://cms-automation-backend-baau2zqeqq-ue.a.run.app/v1/worklist/${itemId}`);
          const data = await res.json();
          return {
            success: true,
            id: data.id,
            status: data.status,
            title: data.title,
            title_main: data.title_main,
            author_name: data.author_name,
            suggested_meta_description: data.suggested_meta_description,
            suggested_seo_keywords: data.suggested_seo_keywords,
            suggested_titles: data.suggested_titles
          };
        } catch (error) {
          return { success: false, error: String(error) };
        }
      }, newestItem.id);

      console.log('\n📋 Item Details:');
      console.log(JSON.stringify(itemDetail, null, 2));

      // Save result to file
      await page.evaluate((result) => {
        console.log('TEST RESULT:', JSON.stringify(result, null, 2));
      }, itemDetail);
    }
  });
});
