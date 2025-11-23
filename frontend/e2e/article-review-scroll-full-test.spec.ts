/**
 * Full E2E Test for Article Review Modal Scroll Functionality
 *
 * Uses API mocking to provide realistic test data without backend dependency
 */

import { test, expect } from '@playwright/test';

test.describe('Article Review Modal - Full Scroll Test with Mock Data', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses with realistic data

    // Mock worklist data
    await page.route('**/api/v1/worklist*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 1,
              article_id: 101,
              title: 'Test Article for Scroll Verification',
              status: 'parsing_review',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        }),
      });
    });

    // Mock article review data with lots of content to trigger scrolling
    await page.route('**/api/v1/article-review/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          article_id: 101,
          title: 'Long Article Title for Testing Scroll Behavior in Article Review Modal',
          author: 'Test Author',
          status: 'parsing_review',
          metadata: {
            featured_image_path: '/images/test.jpg',
            additional_images: ['/images/test1.jpg', '/images/test2.jpg'],
            faq_suggestions: Array(10).fill(null).map((_, i) => ({
              question: `FAQ Question ${i + 1} - This is a longer question to ensure we have enough content`,
              answer: `This is the answer to question ${i + 1}. It provides detailed information that helps test the scrolling behavior of the article review modal interface.`,
            })),
          },
          meta_description: 'This is a meta description for testing purposes. It should be between 150-160 characters long to meet SEO standards.',
          seo_keywords: ['test', 'scroll', 'article', 'review', 'modal', 'playwright', 'e2e', 'testing'],
          articleReview: {
            title: {
              original: 'Original Title',
              ai_suggested: 'AI Suggested Title',
            },
            meta: {
              original: 'Original meta description',
              ai_suggested: 'AI suggested meta description that is optimized for search engines',
            },
            seo: {
              original_keywords: ['original', 'keywords'],
              ai_keywords: ['ai', 'optimized', 'keywords'],
            },
            faq_proposals: Array(5).fill(null).map((_, i) => ({
              schema_type: 'FAQPage',
              score: 0.9,
              questions: [
                {
                  question: `Proposal ${i + 1} Question 1`,
                  answer: `Answer for proposal ${i + 1} question 1`,
                },
                {
                  question: `Proposal ${i + 1} Question 2`,
                  answer: `Answer for proposal ${i + 1} question 2`,
                },
              ],
            })),
          },
        }),
      });
    });

    // Navigate to production site
    await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html');
  });

  test('validates scroll functionality with real content', async ({ page }) => {
    console.log('✅ Page loaded with mocked API data');

    // Wait for worklist to load
    await page.waitForSelector('text=Test Article for Scroll Verification', { timeout: 10000 });

    // Click on the article to open review modal
    await page.click('text=Test Article for Scroll Verification');

    // Wait for modal to open
    await page.waitForSelector('[data-testid="parsing-review-grid"]', { timeout: 10000 });
    console.log('✅ Article Review Modal opened');

    // Get the scrollable container
    const scrollContainer = page.locator('.overflow-y-auto').first();

    // Verify container exists
    await expect(scrollContainer).toBeVisible();

    // Get scroll metrics
    const scrollMetrics = await scrollContainer.evaluate((el) => ({
      scrollHeight: el.scrollHeight,
      clientHeight: el.clientHeight,
      scrollTop: el.scrollTop,
    }));

    console.log('Scroll metrics:', scrollMetrics);

    // Verify content is taller than viewport (scrollable)
    expect(scrollMetrics.scrollHeight).toBeGreaterThan(scrollMetrics.clientHeight);
    console.log('✅ Content is scrollable');

    // Try to scroll down
    await scrollContainer.evaluate((el) => {
      el.scrollTop = 500;
    });

    // Wait a bit for scroll to complete
    await page.waitForTimeout(500);

    // Verify scroll position changed
    const newScrollTop = await scrollContainer.evaluate((el) => el.scrollTop);
    expect(newScrollTop).toBeGreaterThan(0);
    console.log(`✅ Scroll successful: ${newScrollTop}px`);

    // Verify grid does NOT have overflow-auto class
    const gridClasses = await page
      .locator('[data-testid="parsing-review-grid"]')
      .getAttribute('class');

    console.log('Grid classes:', gridClasses);

    expect(gridClasses).not.toContain('overflow-auto');
    expect(gridClasses).not.toContain('h-full');
    console.log('✅ Grid classes are correct (no overflow-auto, no h-full)');

    // Take screenshot
    await page.screenshot({
      path: 'test-results/article-review-scroll-full-test.png',
      fullPage: true,
    });

    console.log('✅ All scroll tests passed!');
  });
});
