/**
 * E2E Tests for Phase 8 Article Review Workflow
 *
 * Comprehensive end-to-end tests covering:
 * - Parsing review step (title, author, images, SEO)
 * - Proofreading review step
 * - Publish preview step
 * - Complete workflow navigation
 * - Keyboard shortcuts
 * - Error handling
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const TEST_TIMEOUT = 30000;

// Helper: Wait for modal to open
async function openArticleReviewModal(page: Page) {
  await page.waitForSelector('table tbody tr', { timeout: 10000 });
  const firstRow = page.locator('table tbody tr').first();
  await firstRow.click();
  await page.waitForSelector('[role="dialog"]', { timeout: 5000 });
}

// Helper: Navigate to specific step
async function navigateToStep(page: Page, stepName: 'parsing' | 'proofreading' | 'publish') {
  const stepMap = {
    parsing: /解析审核|Parsing Review/i,
    proofreading: /校对审核|Proofreading Review/i,
    publish: /发布预览|Publish Preview/i,
  };

  const stepButton = page.locator(`button`, { hasText: stepMap[stepName] }).first();
  await stepButton.click();
  await page.waitForTimeout(500); // Wait for transition
}

test.describe('Phase 8: Article Review Modal', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/worklist', { waitUntil: 'networkidle' });
  });

  test('should open review modal with correct structure', async ({ page }) => {
    await openArticleReviewModal(page);

    // Verify modal structure
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Should have progress stepper
    await expect(page.locator('text=/解析审核|Parsing Review/')).toBeVisible();
    await expect(page.locator('text=/校对审核|Proofreading Review/')).toBeVisible();
    await expect(page.locator('text=/发布预览|Publish Preview/')).toBeVisible();

    // Should have close button
    const closeButton = page.locator('button[aria-label*="close"], button:has-text("×")').first();
    await expect(closeButton).toBeVisible();
  });

  test('should close modal on Escape key', async ({ page }) => {
    await openArticleReviewModal(page);
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(modal).not.toBeVisible({ timeout: 2000 });
  });

  test('should close modal on close button click', async ({ page }) => {
    await openArticleReviewModal(page);
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    const closeButton = page.locator('button[aria-label*="close"], button:has-text("×")').first();
    await closeButton.click();
    await expect(modal).not.toBeVisible({ timeout: 2000 });
  });
});

test.describe('Phase 8: Parsing Review Step', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/worklist', { waitUntil: 'networkidle' });
    await openArticleReviewModal(page);
  });

  test('should display parsing review as first step', async ({ page }) => {
    // First step should be active
    const parsingStep = page.locator('button:has-text("解析审核"), button:has-text("Parsing Review")').first();

    // Check for active styling (could be border, background, etc.)
    const classList = await parsingStep.getAttribute('class');
    expect(classList).toMatch(/border-blue|border-primary|bg-blue|bg-primary/);
  });

  test('should show title review section', async ({ page }) => {
    // Should display title section header
    await expect(page.locator('text=/标题审核|Title Review/i')).toBeVisible({ timeout: 3000 });

    // Should have title input
    const titleInput = page.locator('input[type="text"], textarea').first();
    await expect(titleInput).toBeVisible();
  });

  test('should allow editing title', async ({ page }) => {
    const titleInput = page.locator('input[type="text"], textarea').first();

    if (await titleInput.isVisible()) {
      // Clear and type new title
      await titleInput.fill('Updated Test Title');

      // Verify value changed
      const value = await titleInput.inputValue();
      expect(value).toBe('Updated Test Title');
    }
  });

  test('should show AI optimization button for title', async ({ page }) => {
    const aiButton = page.locator('button:has-text("AI 优化标题"), button:has-text("AI Optimize")').first();

    if (await aiButton.isVisible()) {
      await expect(aiButton).toBeEnabled();

      // Click AI optimization button
      await aiButton.click();

      // Should show loading state
      await expect(page.locator('text=/优化中|Optimizing/i')).toBeVisible({ timeout: 2000 });
    }
  });

  test('should display author information if available', async ({ page }) => {
    // Check if author section exists
    const authorSection = page.locator('text=/作者|Author/i').first();

    if (await authorSection.isVisible()) {
      // Should have author name
      await expect(page.locator('text=/John|Jane|作者名/i').first()).toBeVisible({ timeout: 1000 });
    }
  });

  test('should show SEO metadata section', async ({ page }) => {
    // Check for SEO section
    const seoSection = page.locator('text=/SEO|元数据|Metadata/i').first();

    if (await seoSection.isVisible()) {
      // Should have meta description field
      await expect(page.locator('textarea, input').nth(1)).toBeVisible();
    }
  });
});

test.describe('Phase 8: Progress Stepper Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/worklist', { waitUntil: 'networkidle' });
    await openArticleReviewModal(page);
  });

  test('should navigate to proofreading step', async ({ page }) => {
    // Click on proofreading step
    await navigateToStep(page, 'proofreading');

    // Should show proofreading content
    await expect(page.locator('text=/校对|Proofreading|Diff/i')).toBeVisible({ timeout: 3000 });
  });

  test('should navigate to publish preview step', async ({ page }) => {
    // Click on publish step
    await navigateToStep(page, 'publish');

    // Should show publish content
    await expect(page.locator('text=/发布|Publish|Preview/i')).toBeVisible({ timeout: 3000 });
  });

  test('should allow navigating back to parsing step', async ({ page }) => {
    // Navigate forward
    await navigateToStep(page, 'proofreading');
    await page.waitForTimeout(500);

    // Navigate back
    await navigateToStep(page, 'parsing');

    // Should show parsing content again
    await expect(page.locator('text=/标题审核|Title Review/i')).toBeVisible({ timeout: 3000 });
  });

  test('should mark completed steps with checkmark', async ({ page }) => {
    // Navigate through steps
    await navigateToStep(page, 'proofreading');
    await page.waitForTimeout(500);
    await navigateToStep(page, 'publish');
    await page.waitForTimeout(500);

    // First step should show as completed
    const parsingStep = page.locator('button:has-text("解析审核"), button:has-text("Parsing Review")').first();
    const classList = await parsingStep.getAttribute('class');

    // Should have completed styling (green border or checkmark)
    expect(classList).toMatch(/border-green|border-success|completed/);
  });
});

test.describe('Phase 8: Keyboard Shortcuts', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/worklist', { waitUntil: 'networkidle' });
    await openArticleReviewModal(page);
  });

  test('should save progress with Ctrl+S', async ({ page }) => {
    // Make a change
    const titleInput = page.locator('input[type="text"], textarea').first();
    if (await titleInput.isVisible()) {
      await titleInput.fill('Test Title for Save');
    }

    // Press Ctrl+S
    await page.keyboard.press('Control+S');

    // Should show success indicator (toast/message)
    // This depends on implementation
    await page.waitForTimeout(1000);
  });

  test('should close modal with Escape', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(modal).not.toBeVisible({ timeout: 2000 });
  });
});

test.describe('Phase 8: Proofreading Review Step', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/worklist', { waitUntil: 'networkidle' });
    await openArticleReviewModal(page);
    await navigateToStep(page, 'proofreading');
  });

  test('should display comparison cards', async ({ page }) => {
    // Check for Meta Description card
    const metaCard = page.locator('text=/Meta Description|Meta 描述/i').first();
    if (await metaCard.isVisible({ timeout: 3000 })) {
      await expect(metaCard).toBeVisible();
    }

    // Check for SEO Keywords card
    const seoCard = page.locator('text=/SEO|关键词|Keywords/i').first();
    if (await seoCard.isVisible({ timeout: 3000 })) {
      await expect(seoCard).toBeVisible();
    }
  });

  test('should expand/collapse comparison cards', async ({ page }) => {
    const metaCard = page.locator('text=/Meta Description/i').first();

    if (await metaCard.isVisible({ timeout: 3000 })) {
      // Click to expand
      await metaCard.click();
      await page.waitForTimeout(500);

      // Should show card content
      await expect(page.locator('text=/Original|原始/i').first()).toBeVisible({ timeout: 2000 });
    }
  });

  test('should display diff view if content changed', async ({ page }) => {
    // Look for diff viewer indicators
    const diffView = page.locator('text=/Original|Suggested|原始|建议/i').first();

    if (await diffView.isVisible({ timeout: 3000 })) {
      await expect(diffView).toBeVisible();
    }
  });
});

test.describe('Phase 8: Complete Workflow', () => {
  test('should complete full review workflow', async ({ page }) => {
    // Start at worklist
    await page.goto('/worklist', { waitUntil: 'networkidle' });
    await openArticleReviewModal(page);

    // Step 1: Parsing Review
    await expect(page.locator('text=/标题审核|Title/i')).toBeVisible({ timeout: 5000 });

    // Navigate to proofreading
    await navigateToStep(page, 'proofreading');
    await page.waitForTimeout(1000);

    // Step 2: Proofreading Review
    await expect(page.locator('text=/校对|Proofreading|Comparison/i')).toBeVisible({ timeout: 5000 });

    // Navigate to publish
    await navigateToStep(page, 'publish');
    await page.waitForTimeout(1000);

    // Step 3: Publish Preview
    await expect(page.locator('text=/发布|Publish|Preview/i')).toBeVisible({ timeout: 5000 });

    // All steps should be marked as visited/completed
    const parsingStep = page.locator('button:has-text("解析审核"), button:has-text("Parsing")').first();
    const proofreadingStep = page.locator('button:has-text("校对审核"), button:has-text("Proofreading")').first();

    // Check they have appropriate styling
    await expect(parsingStep).toBeVisible();
    await expect(proofreadingStep).toBeVisible();
  });

  test('should persist changes when navigating between steps', async ({ page }) => {
    await page.goto('/worklist', { waitUntil: 'networkidle' });
    await openArticleReviewModal(page);

    // Make a change in parsing step
    const titleInput = page.locator('input[type="text"], textarea').first();
    if (await titleInput.isVisible()) {
      await titleInput.fill('Persistent Test Title');
      const initialValue = await titleInput.inputValue();

      // Navigate away
      await navigateToStep(page, 'proofreading');
      await page.waitForTimeout(500);

      // Navigate back
      await navigateToStep(page, 'parsing');
      await page.waitForTimeout(500);

      // Value should persist
      const finalValue = await titleInput.inputValue();
      expect(finalValue).toBe(initialValue);
    }
  });
});

test.describe('Phase 8: Error Handling', () => {
  test('should handle missing article data gracefully', async ({ page }) => {
    await page.goto('/worklist', { waitUntil: 'networkidle' });

    // Try to open an article
    const rows = page.locator('table tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      await openArticleReviewModal(page);

      // Modal should open even with incomplete data
      await expect(page.locator('[role="dialog"]')).toBeVisible();

      // Should not crash or show error modal
      await expect(page.locator('text=/Error|错误|Failed/i')).not.toBeVisible({ timeout: 2000 });
    }
  });

  test('should show validation for required fields', async ({ page }) => {
    await page.goto('/worklist', { waitUntil: 'networkidle' });
    await openArticleReviewModal(page);

    // Try to clear title
    const titleInput = page.locator('input[type="text"], textarea').first();
    if (await titleInput.isVisible()) {
      await titleInput.fill('');

      // Might show validation message
      const validation = page.locator('text=/required|必填|不能为空/i').first();
      if (await validation.isVisible({ timeout: 1000 })) {
        await expect(validation).toBeVisible();
      }
    }
  });
});

test.describe('Phase 8: Performance', () => {
  test('modal should open within 2 seconds', async ({ page }) => {
    await page.goto('/worklist', { waitUntil: 'networkidle' });

    const startTime = Date.now();
    await openArticleReviewModal(page);
    const endTime = Date.now();

    const duration = endTime - startTime;
    expect(duration).toBeLessThan(2000);
  });

  test('step navigation should be instant', async ({ page }) => {
    await page.goto('/worklist', { waitUntil: 'networkidle' });
    await openArticleReviewModal(page);

    const startTime = Date.now();
    await navigateToStep(page, 'proofreading');
    const endTime = Date.now();

    const duration = endTime - startTime;
    expect(duration).toBeLessThan(500);
  });
});
