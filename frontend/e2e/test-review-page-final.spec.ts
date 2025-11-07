import { test, expect } from '@playwright/test';

test.describe('Review Page Final Test', () => {
  test('should load review page without errors after fix', async ({ page }) => {
    const consoleErrors: string[] = [];
    const pageErrors: Error[] = [];
    
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    page.on('pageerror', (error) => {
      pageErrors.push(error);
    });

    // Navigate with no cache
    await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html#/worklist', {
      waitUntil: 'networkidle',
    });
    
    // Clear storage and reload
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    await page.reload({ waitUntil: 'networkidle' });
    
    console.log('📍 Navigating to worklist...');
    await page.waitForTimeout(2000);

    // Click review button
    const reviewButton = page.getByRole('button', { name: /审核|review/i }).first();
    await reviewButton.click();
    
    console.log('🖱️ Clicked review button, waiting for navigation...');
    await page.waitForTimeout(5000);

    // Take screenshot
    await page.screenshot({ path: '/tmp/review-page-final-test.png', fullPage: true });

    // Check URL
    const url = page.url();
    console.log(`📍 Current URL: ${url}`);
    expect(url).toContain('/worklist/');
    expect(url).toContain('/review');

    // Check for error boundary
    const errorBoundary = await page.locator('text=/应用程序遇到.*个错误|error boundary/i').count();
    console.log(`🚨 Error boundaries found: ${errorBoundary}`);
    
    // Check for the proofreading UI elements
    const issueList = await page.locator('[class*="ProofreadingIssueList"], [class*="issue-list"]').count();
    const articleContent = await page.locator('[class*="ProofreadingArticleContent"], [class*="article-content"]').count();
    
    console.log(`✅ Issue list found: ${issueList}`);
    console.log(`✅ Article content found: ${articleContent}`);
    console.log(`✅ Console errors: ${consoleErrors.length}`);
    console.log(`✅ Page errors: ${pageErrors.length}`);

    // Assertions
    expect(errorBoundary).toBe(0);
    expect(consoleErrors.length).toBe(0);
    expect(pageErrors.length).toBe(0);
  });
});
