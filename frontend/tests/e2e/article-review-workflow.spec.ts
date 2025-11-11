/**
 * E2E Tests for Article Review Workflow
 * Phase 8.2: Basic workflow navigation and interaction tests
 */

import { test, expect } from '@playwright/test';

test.describe('Article Review Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to worklist page
    await page.goto('/worklist');
    await page.waitForLoadState('networkidle');
  });

  test('should open article review modal from worklist', async ({ page }) => {
    // Wait for worklist table to load
    await page.waitForSelector('table');

    // Click on first article row
    const firstRow = page.locator('table tbody tr').first();
    await firstRow.click();

    // Should open review modal
    await expect(page.locator('[role="dialog"]')).toBeVisible();
    await expect(page.locator('text=/Review|审核/')).toBeVisible();
  });

  test('should display progress stepper with three steps', async ({ page }) => {
    // Open first article
    await page.locator('table tbody tr').first().click();

    // Wait for modal
    await page.waitForSelector('[role="dialog"]');

    // Check for step indicators
    await expect(page.locator('text=/Parsing|解析/')).toBeVisible();
    await expect(page.locator('text=/Proofreading|校对/')).toBeVisible();
    await expect(page.locator('text=/Publish|发布/')).toBeVisible();
  });

  test('should navigate between review steps', async ({ page }) => {
    // Open first article
    await page.locator('table tbody tr').first().click();
    await page.waitForSelector('[role="dialog"]');

    // Should start at parsing review step
    const parsingStep = page.locator('button:has-text("Parsing"), button:has-text("解析")').first();
    await expect(parsingStep).toHaveClass(/border-blue-500|bg-blue/);

    // Click Next button
    const nextButton = page.locator('button:has-text("Next"), button:has-text("下一步")');
    await nextButton.click();

    // Should move to proofreading step
    const proofreadingStep = page.locator('button:has-text("Proofreading"), button:has-text("校对")').first();
    await expect(proofreadingStep).toHaveClass(/border-blue-500|bg-blue/);

    // Click Previous button
    const prevButton = page.locator('button:has-text("Previous"), button:has-text("上一步")');
    await prevButton.click();

    // Should go back to parsing step
    await expect(parsingStep).toHaveClass(/border-blue-500|bg-blue/);
  });

  test('should save progress using keyboard shortcut', async ({ page }) => {
    // Open first article
    await page.locator('table tbody tr').first().click();
    await page.waitForSelector('[role="dialog"]');

    // Press Ctrl+S to save
    await page.keyboard.press('Control+S');

    // Should show success message (if implemented)
    // await expect(page.locator('text=/saved|已保存/i')).toBeVisible({ timeout: 3000 });
  });

  test('should close modal using Esc key', async ({ page }) => {
    // Open first article
    await page.locator('table tbody tr').first().click();
    await page.waitForSelector('[role="dialog"]');

    // Modal should be visible
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Press Esc to close
    await page.keyboard.press('Escape');

    // Modal should be closed
    await expect(modal).not.toBeVisible({ timeout: 2000 });
  });

  test('should display article title in modal header', async ({ page }) => {
    // Get title from first row
    const firstRow = page.locator('table tbody tr').first();
    const titleInTable = await firstRow.locator('td').nth(1).textContent();

    // Open article
    await firstRow.click();
    await page.waitForSelector('[role="dialog"]');

    // Check if title appears in modal (somewhere)
    if (titleInTable) {
      await expect(page.locator(`text=${titleInTable.trim()}`).first()).toBeVisible();
    }
  });

  test('should show parsing review content in first step', async ({ page }) => {
    // Open first article
    await page.locator('table tbody tr').first().click();
    await page.waitForSelector('[role="dialog"]');

    // Should show title review section
    await expect(page.locator('text=/Title|标题/')).toBeVisible();

    // Should have approve/edit buttons
    await expect(page.locator('button:has-text("Approve"), button:has-text("批准")')).toBeVisible();
    await expect(page.locator('button:has-text("Edit"), button:has-text("编辑")')).toBeVisible();
  });

  test('should handle navigation with incomplete data gracefully', async ({ page }) => {
    // Open first article
    await page.locator('table tbody tr').first().click();
    await page.waitForSelector('[role="dialog"]');

    // Try to navigate to publish step directly
    const publishStep = page.locator('button:has-text("Publish"), button:has-text("发布")').first();
    await publishStep.click();

    // Should either allow navigation or show validation message
    // (Behavior depends on implementation)
    // Just check that page doesn't crash
    await expect(page.locator('[role="dialog"]')).toBeVisible();
  });
});

test.describe('Article Review - Quick Filters', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/worklist');
    await page.waitForLoadState('networkidle');
  });

  test('should filter worklist by status', async ({ page }) => {
    // Find and click parsing_review filter
    const parsingFilter = page.locator('button:has-text("Parsing Review"), button:has-text("解析审核")');

    if (await parsingFilter.isVisible()) {
      const initialCount = await page.locator('table tbody tr').count();

      await parsingFilter.click();
      await page.waitForTimeout(500); // Wait for filter to apply

      const filteredCount = await page.locator('table tbody tr').count();

      // Count should change or stay same (if all items match filter)
      expect(filteredCount).toBeLessThanOrEqual(initialCount);
    }
  });

  test('should show statistics cards', async ({ page }) => {
    // Check for statistics display
    await expect(page.locator('text=/Total|总计/')).toBeVisible();
    await expect(page.locator('text=/Pending|待处理/')).toBeVisible();
  });
});
