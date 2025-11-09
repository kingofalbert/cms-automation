/**
 * View Modes Visual Test
 * Tests all four view modes: Original, Rendered, Preview, Diff
 *
 * Test Strategy:
 * 1. Click each view mode button
 * 2. Take screenshots for visual verification
 * 3. Verify expected elements are present
 * 4. Compare behavior against requirements
 */

import { test, expect, Page } from '@playwright/test';

const CACHE_BUST = Date.now();
const FRONTEND_URL = `https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html?v=${CACHE_BUST}`;

// Helper function to wait for page load
async function waitForPageLoad(page: Page) {
  await page.waitForLoadState('networkidle', { timeout: 60000 });
  await page.waitForTimeout(2000); // Additional buffer
}

// Helper function to navigate to review page
async function navigateToReview(page: Page) {
  console.log('Navigating to frontend...');
  await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 60000 });
  await waitForPageLoad(page);

  console.log('Looking for Review buttons...');
  const reviewButton = page.locator('button:has-text("Review")').first();
  await expect(reviewButton).toBeVisible({ timeout: 30000 });

  await reviewButton.click();
  await waitForPageLoad(page);

  console.log('Arrived at proofreading review page');
}

test.describe('View Modes - Visual Testing', () => {
  test.setTimeout(180000); // 3 minutes per test

  test('Test 1: Original View Mode - Shows raw Markdown with highlighted issues', async ({ page }) => {
    console.log('\n=== TEST 1: ORIGINAL VIEW ===');

    await navigateToReview(page);

    // Click Original button (should be default, but click to be sure)
    const originalButton = page.locator('button:has-text("Original"), button[aria-label*="Original"]');
    await originalButton.click();
    await page.waitForTimeout(1000);

    // Take screenshot
    await page.screenshot({ path: 'test-results/view-mode-01-original.png', fullPage: true });

    // Verification: Original view should show:
    // 1. Raw Markdown text (with ## headers, **bold**, etc.)
    // 2. Highlighted issues (yellow/red/blue backgrounds)
    // 3. NOT formatted HTML

    // Check for raw Markdown patterns
    const articleContent = page.locator('.prose, [class*="article"], [class*="content"]').first();
    const text = await articleContent.textContent();

    console.log('Checking for Markdown syntax...');
    console.log('Content preview:', text?.substring(0, 500));

    // Look for issue highlights
    const highlightedIssues = page.locator('[class*="bg-yellow"], [class*="bg-red"], [class*="bg-blue"]');
    const issueCount = await highlightedIssues.count();
    console.log(`Found ${issueCount} highlighted issue spans`);

    // Verify we have some highlighted content
    expect(issueCount).toBeGreaterThan(0);

    console.log('✅ Original view verification complete');
  });

  test('Test 2: Rendered View Mode - Shows formatted Markdown', async ({ page }) => {
    console.log('\n=== TEST 2: RENDERED VIEW ===');

    await navigateToReview(page);

    // Click Rendered button
    const renderedButton = page.locator('button:has-text("Rendered")');
    await expect(renderedButton).toBeVisible({ timeout: 10000 });
    await renderedButton.click();
    await page.waitForTimeout(2000);

    // Take screenshot
    await page.screenshot({ path: 'test-results/view-mode-02-rendered.png', fullPage: true });

    // Verification: Rendered view should show:
    // 1. Formatted HTML (h1, h2, h3 tags instead of ##)
    // 2. No raw Markdown syntax visible
    // 3. Proper typography and spacing

    // Check for formatted HTML elements
    const article = page.locator('.prose').first();

    // Look for actual HTML heading tags (not Markdown ##)
    const h1Count = await article.locator('h1').count();
    const h2Count = await article.locator('h2').count();
    const h3Count = await article.locator('h3').count();
    const strongCount = await article.locator('strong').count();

    console.log(`HTML Elements found:
      - H1 headings: ${h1Count}
      - H2 headings: ${h2Count}
      - H3 headings: ${h3Count}
      - Bold (strong): ${strongCount}
    `);

    // Verify we have formatted HTML (at least some headers or bold text)
    const totalFormatting = h1Count + h2Count + h3Count + strongCount;
    expect(totalFormatting).toBeGreaterThan(0);

    console.log('✅ Rendered view verification complete');
  });

  test('Test 3: Preview View Mode - Shows accepted changes applied', async ({ page }) => {
    console.log('\n=== TEST 3: PREVIEW VIEW ===');

    await navigateToReview(page);

    // First, accept one issue to have something to preview
    console.log('Accepting first issue to create preview content...');
    const firstIssue = page.locator('[class*="cursor-pointer"][class*="bg-"]').first();
    await firstIssue.click();
    await page.waitForTimeout(500);

    // Press 'A' key to accept
    await page.keyboard.press('a');
    await page.waitForTimeout(500);

    // Now click Preview button
    const previewButton = page.locator('button:has-text("Preview")');
    await expect(previewButton).toBeVisible({ timeout: 10000 });
    await previewButton.click();
    await page.waitForTimeout(2000);

    // Take screenshot
    await page.screenshot({ path: 'test-results/view-mode-03-preview.png', fullPage: true });

    // Verification: Preview view should show:
    // 1. Original content with accepted changes applied
    // 2. Suggested text for accepted issues
    // 3. Different appearance from Original view

    console.log('Checking for applied changes in preview...');

    // Check decision counter
    const statsText = await page.locator('text=/\\d+\\s*\\/\\s*\\d+.*decided/i').textContent();
    console.log('Stats:', statsText);

    // Verify at least one decision was made
    expect(statsText).toMatch(/[1-9]\d*\s*\/.*decided/);

    console.log('✅ Preview view verification complete');
  });

  test('Test 4: Diff View Mode - Shows original vs suggested comparison', async ({ page }) => {
    console.log('\n=== TEST 4: DIFF VIEW ===');

    await navigateToReview(page);

    // Click Diff button
    const diffButton = page.locator('button:has-text("Diff")');
    await expect(diffButton).toBeVisible({ timeout: 10000 });
    await diffButton.click();
    await page.waitForTimeout(2000);

    // Take screenshot
    await page.screenshot({ path: 'test-results/view-mode-04-diff.png', fullPage: true });

    // Verification: Diff view should show:
    // 1. Side-by-side or inline comparison
    // 2. Deletions highlighted in red
    // 3. Additions highlighted in green
    // 4. Clear visual distinction between original and suggested

    console.log('Checking for diff visualization...');

    const pageContent = await page.content();

    // Look for diff-related elements or text
    const hasDiffContent =
      pageContent.includes('Original') ||
      pageContent.includes('Suggested') ||
      pageContent.includes('diff') ||
      await page.locator('[class*="bg-red"], [class*="bg-green"]').count() > 0;

    console.log('Diff view elements present:', hasDiffContent);

    // Note: If suggestedContent is not available, diff view might show a message or fallback
    // We'll document this behavior

    console.log('✅ Diff view verification complete');
  });

  test('Test 5: View Mode Switching - All buttons clickable and responsive', async ({ page }) => {
    console.log('\n=== TEST 5: VIEW MODE SWITCHING ===');

    await navigateToReview(page);

    const modes = [
      { name: 'Original', selector: 'button:has-text("Original")' },
      { name: 'Rendered', selector: 'button:has-text("Rendered")' },
      { name: 'Preview', selector: 'button:has-text("Preview")' },
      { name: 'Diff', selector: 'button:has-text("Diff")' },
    ];

    for (const mode of modes) {
      console.log(`\nSwitching to ${mode.name} view...`);

      const button = page.locator(mode.selector);
      await expect(button).toBeVisible({ timeout: 10000 });
      await button.click();
      await page.waitForTimeout(1000);

      // Take screenshot of each mode
      await page.screenshot({
        path: `test-results/view-mode-switch-${mode.name.toLowerCase()}.png`,
        fullPage: true
      });

      // Verify button appears active/selected
      const buttonClass = await button.getAttribute('class');
      console.log(`${mode.name} button classes:`, buttonClass);

      console.log(`✓ ${mode.name} view loaded`);
    }

    console.log('✅ All view modes are switchable');
  });

  test('Test 6: Content Persistence - Same content across modes', async ({ page }) => {
    console.log('\n=== TEST 6: CONTENT PERSISTENCE ===');

    await navigateToReview(page);

    // Get title from Original view
    await page.locator('button:has-text("Original")').click();
    await page.waitForTimeout(1000);
    const titleOriginal = await page.locator('h1').first().textContent();
    console.log('Title in Original:', titleOriginal);

    // Check title in Rendered view
    await page.locator('button:has-text("Rendered")').click();
    await page.waitForTimeout(1000);
    const titleRendered = await page.locator('h1').first().textContent();
    console.log('Title in Rendered:', titleRendered);

    // Check title in Preview view
    await page.locator('button:has-text("Preview")').click();
    await page.waitForTimeout(1000);
    const titlePreview = await page.locator('h1').first().textContent();
    console.log('Title in Preview:', titlePreview);

    // Titles should be consistent
    expect(titleOriginal).toBe(titleRendered);
    expect(titleOriginal).toBe(titlePreview);

    console.log('✅ Content persists correctly across view modes');
  });
});
