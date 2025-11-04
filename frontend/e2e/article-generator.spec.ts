import { test, expect } from '@playwright/test';

test.describe('Article Generator Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('index.html#/generate');
    await page.waitForLoadState('networkidle');
  });

  test('page loads with correct title and description', async ({ page }) => {
    // Check page heading
    await expect(page.locator('h1', { hasText: 'Article Generator' })).toBeVisible();

    // Check description
    await expect(page.locator('text=Generate AI-powered articles using Claude')).toBeVisible();
  });

  test('topic submission form displays all required fields', async ({ page }) => {
    // Check form heading
    await expect(page.locator('text=Generate New Article')).toBeVisible();

    // Check topic description field
    const topicField = page.locator('textarea[placeholder*="Describe the article topic"]');
    await expect(topicField).toBeVisible();

    // Check style/tone dropdown
    const styleSelect = page.locator('select').first();
    await expect(styleSelect).toBeVisible();
    await expect(styleSelect).toContainText('Professional');

    // Check word count field
    const wordCountField = page.locator('input[type="number"]').first();
    await expect(wordCountField).toBeVisible();

    // Check outline field
    const outlineField = page.locator('textarea[placeholder*="Optional: Provide a structured outline"]');
    await expect(outlineField).toBeVisible();

    // Check buttons
    await expect(page.locator('button', { hasText: 'Clear' })).toBeVisible();
    await expect(page.locator('button', { hasText: 'Generate Article' })).toBeVisible();
  });

  test('form validation works for topic description', async ({ page }) => {
    // Try to submit without filling required field
    const submitButton = page.locator('button', { hasText: 'Generate Article' });
    await submitButton.click();

    // Should show validation error
    await expect(page.locator('text=Topic description is required')).toBeVisible();
  });

  test('form validation works for word count limits', async ({ page }) => {
    const topicField = page.locator('textarea[placeholder*="Describe the article topic"]');
    const wordCountField = page.locator('input[type="number"]').first();

    // Fill topic
    await topicField.fill('Test article about AI technology');

    // Try too low word count
    await wordCountField.fill('50');
    await wordCountField.blur();

    // Submit to trigger validation
    await page.locator('button', { hasText: 'Generate Article' }).click();
    await expect(page.locator('text=Minimum 100 words')).toBeVisible({ timeout: 5000 });
  });

  test('style dropdown has all options', async ({ page }) => {
    const styleSelect = page.locator('select').first();

    // Get all options
    const options = await styleSelect.locator('option').allTextContents();

    expect(options).toContain('Professional');
    expect(options).toContain('Casual');
    expect(options).toContain('Technical');
    expect(options).toContain('Academic');
  });

  test('clear button resets form fields', async ({ page }) => {
    const topicField = page.locator('textarea[placeholder*="Describe the article topic"]');
    const wordCountField = page.locator('input[type="number"]').first();
    const outlineField = page.locator('textarea[placeholder*="Optional: Provide a structured outline"]');

    // Fill form
    await topicField.fill('Test article topic');
    await wordCountField.fill('2000');
    await outlineField.fill('Test outline');

    // Click clear
    await page.locator('button', { hasText: 'Clear' }).click();

    // Check fields are cleared
    await expect(topicField).toHaveValue('');
    await expect(outlineField).toHaveValue('');
    // Word count should reset to default (1000)
    await expect(wordCountField).toHaveValue('1000');
  });

  test('generated articles section is visible', async ({ page }) => {
    // Check section heading
    await expect(page.locator('h2', { hasText: 'Generated Articles' })).toBeVisible();

    // Check refresh button
    await expect(page.locator('button', { hasText: 'Refresh' })).toBeVisible();
  });

  test('no articles message displays when empty', async ({ page }) => {
    // Wait for articles to load
    await page.waitForTimeout(2000);

    // Should show empty state message
    const emptyMessage = page.locator('text=No articles yet');
    if (await emptyMessage.isVisible()) {
      await expect(page.locator('text=Get started by submitting a topic')).toBeVisible();
    }
  });

  test('refresh button is functional', async ({ page }) => {
    // Wait for initial loading to complete
    await page.waitForTimeout(3000);

    const refreshButton = page.locator('button', { hasText: 'Refresh' });
    await expect(refreshButton).toBeVisible();

    // Wait for button to be enabled (after loading)
    await expect(refreshButton).toBeEnabled({ timeout: 10000 });

    // Click refresh
    await refreshButton.click();

    // Should still be visible after click
    await expect(refreshButton).toBeVisible();
  });

  test('form layout is responsive', async ({ page }) => {
    // Test on desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator('textarea[placeholder*="Describe the article topic"]')).toBeVisible();

    // Test on tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('textarea[placeholder*="Describe the article topic"]')).toBeVisible();

    // Test on mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('textarea[placeholder*="Describe the article topic"]')).toBeVisible();
  });
});
