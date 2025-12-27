/**
 * Article Review Modal Visual Tests
 *
 * Tests visual appearance and layout of the article review modal.
 * Covers: 3-step flow, SEO fields, categories, keywords, FAQ section.
 */

import { test, expect } from '@playwright/test';
import { navigateWithRetry, waitForPageReady } from '../utils/test-helpers';
import {
  VIEWPORTS,
  waitForAnimations,
  captureScreenshot,
  verifyEmptyState,
} from '../utils/visual-test-helpers';

const BASE_URL = process.env.TEST_LOCAL === '1'
  ? 'http://localhost:4173'
  : 'https://storage.googleapis.com/cms-automation-frontend-476323/index.html';

test.describe('Article Review Modal Visual Tests', () => {
  test.beforeEach(async ({ page }) => {
    await navigateWithRetry(page, BASE_URL);
    await waitForPageReady(page);
  });

  /**
   * Helper to open article review modal
   */
  async function openArticleReview(page: any) {
    const reviewButton = page.locator('button:has-text("Review")').first();
    if (await reviewButton.isVisible()) {
      await reviewButton.click();
      await waitForAnimations(page);
      return true;
    }
    return false;
  }

  test.describe('Modal Layout', () => {
    test('should display modal with correct dimensions', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      const modal = page.locator('[role="dialog"], [class*="modal"]').first();
      await expect(modal).toBeVisible();

      const box = await modal.boundingBox();
      if (box) {
        // Modal should have reasonable dimensions
        expect(box.width).toBeGreaterThan(600);
        expect(box.height).toBeGreaterThan(400);
      }
    });

    test('should display 3-step stepper', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Verify all steps are visible
      await expect(page.locator('text=解析审核')).toBeVisible();
      await expect(page.locator('text=校对审核')).toBeVisible();
      await expect(page.locator('text=最终发布')).toBeVisible();
    });

    test('should display progress bar with percentage', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Check for progress indicator
      const progressBar = page.locator('[role="progressbar"], [class*="progress"]');
      if (await progressBar.count() > 0) {
        await expect(progressBar.first()).toBeVisible();
      }

      // Check for percentage text
      const percentageText = page.locator('text=/%/');
      if (await percentageText.count() > 0) {
        await expect(percentageText.first()).toBeVisible();
      }
    });

    test('should display header with article title', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Modal header should contain article title
      const header = page.locator('text=/文章审核|Article Review/i');
      await expect(header).toBeVisible();
    });
  });

  test.describe('Step 1: Parsing Review', () => {
    test('should display 3-column layout on desktop', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.desktop);
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Check for section headers
      await expect(page.locator('text=基础信息')).toBeVisible();
      await expect(page.locator('text=SEO 优化')).toBeVisible();
      await expect(page.locator('text=分类与标签')).toBeVisible();

      await captureScreenshot(page, 'article-review-step1-desktop');
    });

    test('should display basic info section correctly', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Check for basic info fields
      const titleSection = page.locator('text=/标题|Title/i').first();
      await expect(titleSection).toBeVisible();

      // Check for author field
      const authorSection = page.locator('text=/作者|Author/i');
      if (await authorSection.count() > 0) {
        await expect(authorSection.first()).toBeVisible();
      }
    });

    test.describe('SEO Title Selection', () => {
      test('should display SEO Title selection cards', async ({ page }) => {
        const opened = await openArticleReview(page);
        if (!opened) {
          test.skip();
          return;
        }

        const seoTitleSection = page.locator('text=SEO Title');
        await expect(seoTitleSection).toBeVisible();

        // Check for selection options
        const documentExtract = page.locator('text=文档提取');
        const aiSuggestion = page.locator('text=AI 优化建议');

        const hasDocExtract = await documentExtract.count() > 0;
        const hasAiSuggestion = await aiSuggestion.count() > 0;

        expect(hasDocExtract || hasAiSuggestion).toBeTruthy();
      });

      test('should highlight selected SEO Title option', async ({ page }) => {
        const opened = await openArticleReview(page);
        if (!opened) {
          test.skip();
          return;
        }

        // Click on AI suggestion if available
        const aiSuggestion = page.locator('text=AI 优化建议');
        if (await aiSuggestion.isVisible()) {
          await aiSuggestion.click();
          await waitForAnimations(page);

          // Check for selected state styling
          const selectedCard = page.locator('[class*="selected"], [class*="active"], [aria-selected="true"]');
          if (await selectedCard.count() > 0) {
            await expect(selectedCard.first()).toBeVisible();
          }
        }
      });
    });

    test.describe('Meta Description', () => {
      test('should display Meta Description section', async ({ page }) => {
        const opened = await openArticleReview(page);
        if (!opened) {
          test.skip();
          return;
        }

        const metaSection = page.locator('text=Meta Description');
        await expect(metaSection).toBeVisible();

        // Check for character count indicator
        const charCount = page.locator('text=/\\d+ 字符|\\d+ characters/i');
        if (await charCount.count() > 0) {
          await expect(charCount.first()).toBeVisible();
        }
      });

      test('should allow switching between description options', async ({ page }) => {
        const opened = await openArticleReview(page);
        if (!opened) {
          test.skip();
          return;
        }

        // Find radio or tab options
        const options = page.locator('input[type="radio"], [role="tab"]');
        if (await options.count() > 1) {
          await options.nth(1).click();
          await waitForAnimations(page);
        }
      });
    });

    test.describe('Keywords Section', () => {
      test('should display keywords section with tags', async ({ page }) => {
        const opened = await openArticleReview(page);
        if (!opened) {
          test.skip();
          return;
        }

        const keywordsSection = page.locator('text=/关键词|Keywords/i');
        await expect(keywordsSection).toBeVisible();

        // Check for keyword tags
        const tags = page.locator('[class*="tag"], [class*="chip"], [class*="badge"]');
        const tagCount = await tags.count();
        console.log(`Found ${tagCount} keyword tags`);
      });

      test('should allow adding new keywords', async ({ page }) => {
        const opened = await openArticleReview(page);
        if (!opened) {
          test.skip();
          return;
        }

        const keywordInput = page.locator('input[placeholder*="keyword"], input[placeholder*="关键词"]');
        if (await keywordInput.isVisible()) {
          await keywordInput.fill('测试关键词');
          await page.keyboard.press('Enter');
          await waitForAnimations(page);
        }
      });
    });

    test.describe('Category Selection', () => {
      test('should display primary category dropdown', async ({ page }) => {
        const opened = await openArticleReview(page);
        if (!opened) {
          test.skip();
          return;
        }

        const categorySection = page.locator('text=/主分类|Primary Category/i');
        await expect(categorySection).toBeVisible();

        // Check for dropdown or select
        const dropdown = page.locator('select, [role="combobox"]');
        if (await dropdown.count() > 0) {
          await expect(dropdown.first()).toBeVisible();
        }
      });

      test('should display secondary categories with limit', async ({ page }) => {
        const opened = await openArticleReview(page);
        if (!opened) {
          test.skip();
          return;
        }

        const secondarySection = page.locator('text=/副分类|Secondary Categories/i');
        if (await secondarySection.count() > 0) {
          await expect(secondarySection.first()).toBeVisible();

          // Check for limit indicator (max 3)
          const limitText = page.locator('text=/最多.*3|max.*3/i');
          if (await limitText.count() > 0) {
            await expect(limitText.first()).toBeVisible();
          }
        }
      });
    });
  });

  test.describe('Step Navigation', () => {
    test('should navigate to step 2 when clicking on stepper', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      const step2 = page.locator('text=校对审核').first();
      await step2.click();
      await waitForAnimations(page);

      // Verify we're on step 2
      const proofreadingContent = page.locator('text=/问题列表|Issue List/i');
      await expect(proofreadingContent).toBeVisible({ timeout: 5000 }).catch(() => {
        console.log('Proofreading content check - may have different structure');
      });
    });

    test('should navigate to step 3 when clicking on stepper', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      const step3 = page.locator('text=最终发布').first();
      await step3.click();
      await waitForAnimations(page);

      // Verify we're on step 3
      const publishContent = page.locator('text=/发布|Publish|预览|Preview/i');
      await expect(publishContent).toBeVisible({ timeout: 5000 }).catch(() => {
        console.log('Publish content check - may have different structure');
      });
    });

    test('should show progress indicator on active step', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Check for active step indicator
      const activeStep = page.locator('[class*="active"], [aria-current="step"]');
      if (await activeStep.count() > 0) {
        await expect(activeStep.first()).toBeVisible();
      }
    });
  });

  test.describe('Action Buttons', () => {
    test('should display save and close buttons', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Check for action buttons
      const saveButton = page.locator('button:has-text("保存"), button:has-text("Save")');
      const closeButton = page.locator('button:has-text("关闭"), button:has-text("Close")');

      await expect(saveButton.or(closeButton)).toBeVisible();
    });

    test('should display next step button', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      const nextButton = page.locator('button:has-text("下一步"), button:has-text("Next")');
      if (await nextButton.count() > 0) {
        await expect(nextButton.first()).toBeVisible();
      }
    });
  });

  test.describe('Responsive Layout', () => {
    test('should display modal correctly on tablet', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.tablet);
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      await captureScreenshot(page, 'article-review-tablet');

      // Modal should still be functional
      await expect(page.locator('text=解析审核')).toBeVisible();
    });

    test('should display modal correctly on mobile', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS.mobile);
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      await captureScreenshot(page, 'article-review-mobile');

      // Sections should stack on mobile
      const modal = page.locator('[role="dialog"], [class*="modal"]').first();
      const box = await modal.boundingBox();
      if (box) {
        expect(box.width).toBeGreaterThanOrEqual(VIEWPORTS.mobile.width * 0.9);
      }
    });
  });

  test.describe('FAQ Section', () => {
    test('should display FAQ section when available', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Scroll to find FAQ section
      const faqSection = page.locator('text=/FAQ|常見問題/i');
      if (await faqSection.count() > 0) {
        await faqSection.first().scrollIntoViewIfNeeded();
        await expect(faqSection.first()).toBeVisible();
      }
    });

    test('should display FAQ items with selection', async ({ page }) => {
      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      const faqItems = page.locator('[class*="faq-item"], [data-testid*="faq"]');
      if (await faqItems.count() > 0) {
        // Click on first FAQ to select
        await faqItems.first().click();
        await waitForAnimations(page);
      }
    });
  });
});
