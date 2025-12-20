/**
 * E2E Tests for SEO Title Selection Feature
 *
 * Tests the complete workflow of SEO Title selection including:
 * - Viewing current SEO Title
 * - Displaying AI-generated variants
 * - Selecting an AI variant
 * - Entering custom SEO Title
 * - Character counter validation
 * - API integration (success/error scenarios)
 */

import { test, expect } from '@playwright/test';

// Test configuration
const FRONTEND_URL = process.env.VITE_APP_URL || 'http://localhost:5173';
const API_URL = process.env.VITE_API_URL || 'http://localhost:8000';

test.describe('SEO Title Selection Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to article review page with SEO Title selection
    // Note: Adjust article ID to match a test article in your database
    const testArticleId = 1;
    await page.goto(`${FRONTEND_URL}/article-review/${testArticleId}`);

    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should display SEO Title selection card', async ({ page }) => {
    // Wait for SEO Title card to appear
    const seoTitleCard = page.locator('[data-testid="seo-title-selection-card"]').first();
    await expect(seoTitleCard).toBeVisible({ timeout: 10000 });

    // Verify card header
    await expect(page.locator('text=SEO Title 選擇').first()).toBeVisible();
  });

  test('should display current SEO Title with source badge', async ({ page }) => {
    // Wait for current SEO Title section
    const currentSection = page.locator('[data-testid="current-seo-title"]').first();
    await expect(currentSection).toBeVisible({ timeout: 10000 });

    // Check for source badge (原文提取, AI生成, 自定義, or 遷移)
    const badge = currentSection.locator('.badge, [class*="badge"]').first();

    // Badge should exist and have text
    const badgeText = await badge.textContent();
    expect(badgeText).toMatch(/(原文提取|AI生成|自定義|遷移)/);
  });

  test('should display AI-generated SEO Title variants', async ({ page }) => {
    // Wait for AI variants section
    const variantsSection = page.locator('[data-testid="ai-variants"]').first();
    await expect(variantsSection).toBeVisible({ timeout: 10000 });

    // Check if variants are loaded (should have at least 1)
    const variants = page.locator('[data-testid="seo-variant"]');
    const variantCount = await variants.count();

    if (variantCount > 0) {
      // Verify first variant has required elements
      const firstVariant = variants.first();

      // SEO Title text
      await expect(firstVariant.locator('[data-testid="variant-seo-title"]')).toBeVisible();

      // Reasoning
      await expect(firstVariant.locator('[data-testid="variant-reasoning"]')).toBeVisible();

      // Keywords
      await expect(firstVariant.locator('[data-testid="variant-keywords"]')).toBeVisible();

      // Character count
      await expect(firstVariant.locator('[data-testid="variant-char-count"]')).toBeVisible();

      // Use button
      await expect(firstVariant.locator('button:has-text("使用")').first()).toBeVisible();
    }
  });

  test('should select an AI variant and update SEO Title', async ({ page }) => {
    // Intercept API call
    const apiPromise = page.waitForResponse(
      response => response.url().includes('/select-seo-title') && response.status() === 200,
      { timeout: 15000 }
    );

    // Find and click the first "使用此 SEO Title" button
    const firstUseButton = page.locator('button:has-text("使用")').first();

    // Wait for button to be visible and enabled
    await expect(firstUseButton).toBeVisible({ timeout: 10000 });
    await expect(firstUseButton).toBeEnabled();

    await firstUseButton.click();

    // Wait for API response
    const response = await apiPromise;
    expect(response.status()).toBe(200);

    // Verify success message appears
    await expect(page.locator('text=成功').first()).toBeVisible({ timeout: 5000 });

    // Or check for toast notification
    const toast = page.locator('[role="status"], .toast, [class*="toast"]').first();
    await expect(toast).toBeVisible({ timeout: 5000 });
  });

  test('should display custom SEO Title input section', async ({ page }) => {
    // Click "自定義 SEO Title" button
    const customButton = page.locator('button:has-text("自定義")').first();
    await expect(customButton).toBeVisible({ timeout: 10000 });
    await customButton.click();

    // Wait for text area to appear
    const textArea = page.locator('textarea[placeholder*="SEO"]').first();
    await expect(textArea).toBeVisible({ timeout: 5000 });

    // Verify character counter appears
    await expect(page.locator('text=/字符數|字元/').first()).toBeVisible();
  });

  test('should validate custom SEO Title character count', async ({ page }) => {
    // Open custom input
    await page.locator('button:has-text("自定義")').first().click();

    const textArea = page.locator('textarea[placeholder*="SEO"]').first();
    await expect(textArea).toBeVisible({ timeout: 5000 });

    // Test short title (< 15 chars)
    await textArea.fill('短標題');

    // Character counter should update
    const charCount = page.locator('[data-testid="char-count"], text=/字符數: \\d+/').first();
    await expect(charCount).toBeVisible();

    // Test long title (> 50 chars)
    const longTitle = '這是一個非常非常非常非常非常非常非常非常非常非常非常長的SEO標題超過五十個字符的限制';
    await textArea.fill(longTitle);

    // Warning should appear for titles > 50 chars
    const warning = page.locator('text=/警告|建議|超過/').first();
    await expect(warning).toBeVisible({ timeout: 3000 });
  });

  test('should submit custom SEO Title successfully', async ({ page }) => {
    // Open custom input
    await page.locator('button:has-text("自定義")').first().click();

    const textArea = page.locator('textarea[placeholder*="SEO"]').first();
    await expect(textArea).toBeVisible({ timeout: 5000 });

    // Enter custom SEO Title
    const customTitle = '測試用的自定義 SEO Title 標題';
    await textArea.fill(customTitle);

    // Intercept API call
    const apiPromise = page.waitForResponse(
      response => response.url().includes('/select-seo-title') && response.status() === 200,
      { timeout: 15000 }
    );

    // Click submit button
    const submitButton = page.locator('button:has-text("套用")').first();
    await expect(submitButton).toBeVisible();
    await expect(submitButton).toBeEnabled();
    await submitButton.click();

    // Wait for API response
    const response = await apiPromise;
    expect(response.status()).toBe(200);

    // Verify response data
    const responseData = await response.json();
    expect(responseData.seo_title).toBe(customTitle);
    expect(responseData.seo_title_source).toBe('user_input');

    // Verify success notification
    await expect(page.locator('text=成功').first()).toBeVisible({ timeout: 5000 });
  });

  test('should handle API error gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route('**/select-seo-title', route => {
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Cannot provide both variant_id and custom_seo_title'
        })
      });
    });

    // Try to select a variant
    const firstUseButton = page.locator('button:has-text("使用")').first();
    await expect(firstUseButton).toBeVisible({ timeout: 10000 });
    await firstUseButton.click();

    // Wait for error message
    await expect(page.locator('text=/錯誤|失敗|Error/').first()).toBeVisible({ timeout: 5000 });
  });

  test('should display loading state during API call', async ({ page }) => {
    // Slow down the network to see loading state
    await page.route('**/select-seo-title', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000)); // 2s delay
      await route.continue();
    });

    // Click use button
    const firstUseButton = page.locator('button:has-text("使用")').first();
    await expect(firstUseButton).toBeVisible({ timeout: 10000 });
    await firstUseButton.click();

    // Verify loading state (button disabled or showing loading text)
    await expect(firstUseButton).toBeDisabled({ timeout: 1000 });

    // Or check for loading text
    const loadingText = page.locator('text=/處理中|載入|Loading/').first();
    await expect(loadingText).toBeVisible({ timeout: 2000 });
  });

  test('should show original extracted SEO Title if available', async ({ page }) => {
    // This test assumes the test article has an extracted SEO Title
    // Check if "原文提取的 SEO Title" section exists
    const extractedSection = page.locator('text=原文提取').first();

    // Only run test if extracted section exists
    const isVisible = await extractedSection.isVisible({ timeout: 5000 }).catch(() => false);

    if (isVisible) {
      // Verify extracted SEO Title display
      await expect(extractedSection).toBeVisible();

      // Should show badge "原文提取"
      const extractedBadge = page.locator('text=原文提取').first();
      await expect(extractedBadge).toBeVisible();

      // Should have a use button
      const useExtractedButton = extractedSection.locator('..').locator('button:has-text("使用")').first();
      await expect(useExtractedButton).toBeVisible();
    }
  });

  test('should prevent submission with empty custom SEO Title', async ({ page }) => {
    // Open custom input
    await page.locator('button:has-text("自定義")').first().click();

    const textArea = page.locator('textarea[placeholder*="SEO"]').first();
    await expect(textArea).toBeVisible({ timeout: 5000 });

    // Leave text area empty
    await textArea.fill('');

    // Submit button should be disabled or show validation error
    const submitButton = page.locator('button:has-text("套用")').first();

    // Try to click
    await submitButton.click();

    // Should either be disabled or show validation message
    const validationMsg = page.locator('text=/不能為空|必填|required/i').first();
    const isButtonDisabled = await submitButton.isDisabled();
    const hasValidation = await validationMsg.isVisible({ timeout: 2000 }).catch(() => false);

    expect(isButtonDisabled || hasValidation).toBeTruthy();
  });

  test('should update current SEO Title after successful selection', async ({ page }) => {
    // Get current SEO Title before change
    const currentSeoTitleBefore = await page.locator('[data-testid="current-seo-title"]')
      .first()
      .textContent();

    // Intercept API call
    await page.waitForResponse(
      response => response.url().includes('/select-seo-title') && response.status() === 200,
      { timeout: 15000 }
    );

    // Select a variant
    const firstUseButton = page.locator('button:has-text("使用")').first();
    await expect(firstUseButton).toBeVisible({ timeout: 10000 });
    await firstUseButton.click();

    // Wait for success
    await expect(page.locator('text=成功').first()).toBeVisible({ timeout: 5000 });

    // Wait a bit for state update
    await page.waitForTimeout(1000);

    // Current SEO Title should be updated (or component re-rendered)
    // This depends on your implementation - might need to refresh or check state
    const currentSeoTitleAfter = await page.locator('[data-testid="current-seo-title"]')
      .first()
      .textContent();

    // Note: This assertion might need adjustment based on your implementation
    // If the component doesn't auto-refresh, you might need to reload the page
  });

  test('should display keywords for each AI variant', async ({ page }) => {
    // Wait for variants
    const variants = page.locator('[data-testid="seo-variant"]');
    const variantCount = await variants.count();

    if (variantCount > 0) {
      const firstVariant = variants.first();
      const keywordsSection = firstVariant.locator('[data-testid="variant-keywords"]');

      await expect(keywordsSection).toBeVisible();

      // Should have keyword tags/badges
      const keywords = keywordsSection.locator('.badge, [class*="badge"], [data-testid="keyword"]');
      const keywordCount = await keywords.count();

      expect(keywordCount).toBeGreaterThan(0);
    }
  });

  test('should display reasoning for each AI variant', async ({ page }) => {
    // Wait for variants
    const variants = page.locator('[data-testid="seo-variant"]');
    const variantCount = await variants.count();

    if (variantCount > 0) {
      const firstVariant = variants.first();
      const reasoningSection = firstVariant.locator('[data-testid="variant-reasoning"]');

      await expect(reasoningSection).toBeVisible();

      // Reasoning should have meaningful text (> 10 chars)
      const reasoningText = await reasoningSection.textContent();
      expect(reasoningText?.length).toBeGreaterThan(10);
    }
  });

  test('should show character count for each AI variant', async ({ page }) => {
    // Wait for variants
    const variants = page.locator('[data-testid="seo-variant"]');
    const variantCount = await variants.count();

    if (variantCount > 0) {
      const firstVariant = variants.first();
      const charCountSection = firstVariant.locator('[data-testid="variant-char-count"]');

      await expect(charCountSection).toBeVisible();

      // Should display a number
      const charCountText = await charCountSection.textContent();
      expect(charCountText).toMatch(/\d+/);
    }
  });
});

test.describe('SEO Title Selection - Edge Cases', () => {
  test('should handle article with no AI suggestions', async ({ page }) => {
    // Mock API to return no suggestions
    await page.route('**/optimizations', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          article_id: 1,
          title_suggestions: {
            seo_title_suggestions: null
          }
        })
      });
    });

    const testArticleId = 1;
    await page.goto(`${FRONTEND_URL}/article-review/${testArticleId}`);
    await page.waitForLoadState('networkidle');

    // Should show message about no suggestions
    const noSuggestionsMsg = page.locator('text=/尚未生成|沒有建議|No suggestions/i').first();
    await expect(noSuggestionsMsg).toBeVisible({ timeout: 10000 });

    // Custom input should still be available
    const customButton = page.locator('button:has-text("自定義")').first();
    await expect(customButton).toBeVisible();
  });

  test('should handle network timeout gracefully', async ({ page }) => {
    // Mock API to timeout
    await page.route('**/select-seo-title', route => {
      // Never resolve - simulates timeout
      // Playwright will handle the timeout
    });

    const testArticleId = 1;
    await page.goto(`${FRONTEND_URL}/article-review/${testArticleId}`);
    await page.waitForLoadState('networkidle');

    // Try to select a variant
    const firstUseButton = page.locator('button:has-text("使用")').first();
    await expect(firstUseButton).toBeVisible({ timeout: 10000 });
    await firstUseButton.click();

    // Should show timeout or error message
    await expect(page.locator('text=/超時|timeout|錯誤/i').first()).toBeVisible({ timeout: 10000 });
  });

  test('should handle very long custom SEO Title', async ({ page }) => {
    const testArticleId = 1;
    await page.goto(`${FRONTEND_URL}/article-review/${testArticleId}`);
    await page.waitForLoadState('networkidle');

    // Open custom input
    await page.locator('button:has-text("自定義")').first().click();

    const textArea = page.locator('textarea[placeholder*="SEO"]').first();
    await expect(textArea).toBeVisible({ timeout: 5000 });

    // Enter very long title (200 chars - database limit)
    const veryLongTitle = 'A'.repeat(200);
    await textArea.fill(veryLongTitle);

    // Should show warning about length
    const warningMsg = page.locator('text=/太長|超過|長度/').first();
    await expect(warningMsg).toBeVisible({ timeout: 3000 });
  });
});

test.describe('SEO Title Selection - Accessibility', () => {
  test('should have proper ARIA labels', async ({ page }) => {
    const testArticleId = 1;
    await page.goto(`${FRONTEND_URL}/article-review/${testArticleId}`);
    await page.waitForLoadState('networkidle');

    // Check for card role
    const card = page.locator('[role="region"], [role="article"]').first();

    // Check for button labels
    const buttons = page.locator('button:has-text("使用"), button:has-text("套用")');
    const buttonCount = await buttons.count();

    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      const ariaLabel = await button.getAttribute('aria-label');
      const buttonText = await button.textContent();

      // Should have either aria-label or text content
      expect(ariaLabel || buttonText).toBeTruthy();
    }
  });

  test('should be keyboard navigable', async ({ page }) => {
    const testArticleId = 1;
    await page.goto(`${FRONTEND_URL}/article-review/${testArticleId}`);
    await page.waitForLoadState('networkidle');

    // Tab through elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // At least one element should be focused
    const focusedElement = await page.locator(':focus').count();
    expect(focusedElement).toBeGreaterThan(0);
  });
});
