/**
 * Article 9 Image Extraction Visual Test
 *
 * Tests: "10種「天然補血食物」" article image extraction and rendering
 */
import { test, expect } from '@playwright/test';

test.describe('Article 9 - 10種「天然補血食物」Image Test', () => {
  test('should display extracted images in UI', async ({ page }) => {
    const baseUrl = process.env.TEST_URL || 'http://localhost:5173';

    // Navigate to worklist
    await page.goto(`${baseUrl}/app.html`);
    await page.waitForLoadState('networkidle');

    // Wait for table to load (use tag selector since data-testid is missing)
    await page.waitForSelector('table', { timeout: 10000 });
    console.log('✅ Worklist table loaded');

    // Find the article row containing "10種「天然補血食物」" (shorter title)
    const articleRow = page.locator('tr:has-text("10種「天然補血食物」")').first();
    await expect(articleRow).toBeVisible({ timeout: 10000 });

    console.log('✅ Found article: 10種「天然補血食物」');

    // Scroll the row into view and click it (row is clickable)
    await articleRow.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    await articleRow.click();

    // Wait for modal to open
    await page.waitForSelector('[role="dialog"]', { timeout: 5000 });
    console.log('✅ Modal opened');

    // Check if "解析" tab exists and click it, otherwise we're already on parsing view
    const parsingTab = page.locator('button:has-text("解析")');
    const tabExists = await parsingTab.count() > 0;

    if (tabExists) {
      await parsingTab.click();
      await page.waitForTimeout(1000);
      console.log('✅ Clicked 解析 tab');
    } else {
      console.log('ℹ️  No 解析 tab found - already on parsing view');
    }

    // Wait for parsing panel to load
    await page.waitForSelector('[data-testid="parsing-review-grid"]', { timeout: 5000 });
    console.log('✅ Parsing review panel loaded');

    // Check for Image Review section
    const imageCard = page.locator('[data-testid="parsing-image-card"]');
    await expect(imageCard).toBeVisible({ timeout: 5000 });
    console.log('✅ Image review card visible');

    // Check for image elements
    const images = imageCard.locator('img');
    const imageCount = await images.count();

    console.log(`📊 Image count: ${imageCount}`);

    if (imageCount > 0) {
      // Verify first image
      const firstImage = images.first();
      const imageSrc = await firstImage.getAttribute('src');

      console.log(`✅ First image src: ${imageSrc}`);

      // Check if image is from Google user content
      expect(imageSrc).toContain('googleusercontent.com');

      // Wait for image to load
      await expect(firstImage).toBeVisible();

      // Check image dimensions (should be > 0)
      const box = await firstImage.boundingBox();
      expect(box).not.toBeNull();
      expect(box!.width).toBeGreaterThan(0);
      expect(box!.height).toBeGreaterThan(0);

      console.log(`✅ Image dimensions: ${box!.width}x${box!.height}px`);
      console.log('🎉 SUCCESS: Image extracted and rendered correctly!');
    } else {
      throw new Error('❌ NO IMAGES FOUND IN UI!');
    }
  });
});
