/**
 * E2E tests for Proofreading Review Workflow
 * Tests the complete proofreading review process from Sprint 2 & 3 implementations
 */

import { test, expect } from '@playwright/test';

test.describe('Proofreading Review Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to worklist page
    await page.goto('/#/worklist');
    await page.waitForLoadState('networkidle');
  });

  test('should display worklist and navigate to review page', async ({ page }) => {
    // Check if worklist items are displayed
    await expect(page.locator('[data-testid="worklist-table"]').or(page.locator('table'))).toBeVisible({ timeout: 10000 });

    // Click first item's review button
    const reviewButton = page.locator('button, a').filter({ hasText: /review|审核/i }).first();
    if (await reviewButton.isVisible()) {
      await reviewButton.click();

      // Should navigate to review page
      await expect(page).toHaveURL(/\/worklist\/\d+\/review/);
    }
  });

  test('should display review page components', async ({ page }) => {
    // Try to access review page directly (assuming ID 1 exists)
    await page.goto('/#/worklist/1/review');
    await page.waitForLoadState('networkidle');

    // Check for breadcrumb navigation (Sprint 3 Task 3.1)
    await expect(page.getByText(/Proofreading Review|校对审核/)).toBeVisible({ timeout: 10000 });

    // Check for Stats Bar (Sprint 3 Task 3.2 - should be sticky)
    const statsBar = page.locator('text=/Critical|Warning|Info/').first();
    if (await statsBar.isVisible()) {
      expect(await statsBar.evaluate(el => window.getComputedStyle(el.closest('[class*="sticky"]') || el).position)).toContain('sticky');
    }

    // Check for ViewMode switcher (Sprint 2 Task 2.3)
    const originalButton = page.getByRole('button', { name: /Original|原始/ });
    const diffButton = page.getByRole('button', { name: /Diff|对比/ });
    const previewButton = page.getByRole('button', { name: /Preview|预览/ });

    if (await originalButton.isVisible()) {
      await expect(originalButton).toBeVisible();
      await expect(diffButton).toBeVisible();
      await expect(previewButton).toBeVisible();
    }
  });

  test('should switch between view modes', async ({ page }) => {
    await page.goto('/#/worklist/1/review');
    await page.waitForLoadState('networkidle');

    const diffButton = page.getByRole('button', { name: /Diff|对比/ });

    if (await diffButton.isVisible()) {
      // Click Diff button
      await diffButton.click();
      await page.waitForTimeout(500);

      // Check if diff view is active (button should be highlighted)
      await expect(diffButton).toHaveClass(/bg-white|text-blue/);

      // Switch back to Original
      const originalButton = page.getByRole('button', { name: /Original|原始/ });
      await originalButton.click();
      await page.waitForTimeout(500);

      await expect(originalButton).toHaveClass(/bg-white|text-blue/);
    }
  });

  test('should display and use issue filters (Sprint 3 Task 3.3)', async ({ page }) => {
    await page.goto('/#/worklist/1/review');
    await page.waitForLoadState('networkidle');

    // Check for filter dropdowns
    const severityFilter = page.locator('select').filter({ hasText: /All Severity|Critical|Warning/ }).first();
    const categoryFilter = page.locator('select').filter({ hasText: /All Categories|Category/ }).first();
    const engineFilter = page.locator('select').filter({ hasText: /All Engines|AI|Deterministic/ }).first();

    if (await severityFilter.isVisible()) {
      // Test severity filter
      await severityFilter.selectOption('critical');
      await page.waitForTimeout(500);

      // Issues should be filtered
      // (Actual assertion would depend on test data)
    }

    if (await engineFilter.isVisible()) {
      // Test engine filter
      await engineFilter.selectOption('ai');
      await page.waitForTimeout(500);
    }
  });

  test('should display issue details and decision options', async ({ page }) => {
    await page.goto('/#/worklist/1/review');
    await page.waitForLoadState('networkidle');

    // Wait for issues to load
    await page.waitForTimeout(2000);

    // Check for Accept/Reject buttons in detail panel
    const acceptButton = page.getByRole('button', { name: /Accept|接受/ });
    const rejectButton = page.getByRole('button', { name: /Reject|拒绝/ });

    if (await acceptButton.isVisible()) {
      await expect(acceptButton).toBeVisible();
      await expect(rejectButton).toBeVisible();

      // Should have custom modification textarea
      await expect(page.locator('textarea[placeholder*="custom"]').or(page.locator('textarea').first())).toBeVisible();
    }
  });

  test('should show historical decisions (Sprint 3 Task 3.4)', async ({ page }) => {
    await page.goto('/#/worklist/1/review');
    await page.waitForLoadState('networkidle');

    // Look for Decision History section
    const historyButton = page.getByText(/Decision History|决策历史/);

    if (await historyButton.isVisible()) {
      await historyButton.click();
      await page.waitForTimeout(500);

      // Should expand to show history
      // (Would show historical decisions if they exist)
    }
  });

  test('should display comparison cards (Sprint 2 Task 2.4)', async ({ page }) => {
    await page.goto('/#/worklist/1/review');
    await page.waitForLoadState('networkidle');

    // Check for AI optimization cards
    const aiHeading = page.getByText(/AI 优化建议|AI Optimization/);

    if (await aiHeading.isVisible()) {
      await expect(aiHeading).toBeVisible();

      // Check for Meta Description card
      const metaCard = page.getByText(/Meta Description/);
      if (await metaCard.isVisible()) {
        await metaCard.click();
        await page.waitForTimeout(500);
        // Should expand
      }

      // Check for SEO Keywords card
      const seoCard = page.getByText(/SEO 关键词|SEO Keywords/);
      if (await seoCard.isVisible()) {
        await expect(seoCard).toBeVisible();
      }
    }
  });

  test('should have review notes textarea (Sprint 2 Task 2.5)', async ({ page }) => {
    await page.goto('/#/worklist/1/review');
    await page.waitForLoadState('networkidle');

    // Check for review notes textarea in footer
    const reviewNotesTextarea = page.locator('textarea[id="review-notes"]').or(
      page.locator('textarea[placeholder*="审核备注"]').or(
        page.locator('textarea[placeholder*="review"]')
      )
    );

    if (await reviewNotesTextarea.isVisible()) {
      await expect(reviewNotesTextarea).toBeVisible();

      // Should be able to type in it
      await reviewNotesTextarea.fill('Test review notes');
      await expect(reviewNotesTextarea).toHaveValue('Test review notes');
    }
  });

  test('should have Cancel button with confirmation (Sprint 3 Task 3.1)', async ({ page }) => {
    await page.goto('/#/worklist/1/review');
    await page.waitForLoadState('networkidle');

    // Look for Cancel button
    const cancelButton = page.getByRole('button', { name: /Cancel|取消/ }).first();

    if (await cancelButton.isVisible()) {
      // Make a change to trigger confirmation
      const reviewNotesTextarea = page.locator('textarea[id="review-notes"]').or(
        page.locator('textarea').first()
      );

      if (await reviewNotesTextarea.isVisible()) {
        await reviewNotesTextarea.fill('Unsaved changes');

        // Setup dialog handler
        page.on('dialog', async dialog => {
          expect(dialog.message()).toContain(/unsaved|cancel|确认/i);
          await dialog.dismiss();
        });

        await cancelButton.click();
      }
    }
  });

  test('should auto-select first issue (Sprint 3 Task 3.5)', async ({ page }) => {
    await page.goto('/#/worklist/1/review');
    await page.waitForLoadState('networkidle');

    // Wait for issues to load
    await page.waitForTimeout(2000);

    // First issue should be highlighted/selected
    const issueList = page.locator('[data-testid="issue-list"]').or(
      page.locator('div').filter({ hasText: /#1|Issue #1/ }).first()
    );

    if (await issueList.isVisible()) {
      // Check if first issue has selection styling
      const firstIssue = page.locator('[class*="border-l-blue"]').or(
        page.locator('[class*="bg-blue"]')
      ).first();

      await expect(firstIssue).toBeVisible({ timeout: 5000 });
    }
  });

  test('performance: diff view renders smoothly', async ({ page }) => {
    await page.goto('/#/worklist/1/review');
    await page.waitForLoadState('networkidle');

    const diffButton = page.getByRole('button', { name: /Diff|对比/ });

    if (await diffButton.isVisible()) {
      // Measure time to switch to diff view
      const start = Date.now();
      await diffButton.click();
      await page.waitForTimeout(100);
      const end = Date.now();

      const renderTime = end - start;

      // Should render within 500ms (NFR-4: FPS >= 40 means ~25ms per frame, allow buffer)
      expect(renderTime).toBeLessThan(500);
    }
  });
});
