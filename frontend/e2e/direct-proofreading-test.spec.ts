import { test, expect } from '@playwright/test';

// Add cache-busting timestamp to bypass CDN cache
const CACHE_BUST = Date.now();
const FRONTEND_URL = `https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html?v=${CACHE_BUST}`;

test.describe('Direct Proofreading Page Access Test (Cache-Busting URL)', () => {

  test.beforeEach(async ({ page }) => {
    // Collect all errors
    page.on('console', msg => {
      console.log(`[${msg.type().toUpperCase()}] ${msg.text()}`);
    });

    page.on('pageerror', error => {
      console.log(`[PAGE ERROR] ${error.message}`);
      console.log(error.stack);
    });

    page.on('requestfailed', request => {
      console.log(`[NETWORK FAILED] ${request.method()} ${request.url()}`);
    });
  });

  test('Access proofreading page directly with item ID 2', async ({ page }) => {
    console.log('\n========================================');
    console.log('TEST: Direct Proofreading Page Access');
    console.log('========================================\n');

    // Navigate directly to proofreading page for item ID 2
    const proofreadingUrl = `${FRONTEND_URL}#/proofreading/2`;
    console.log(`Navigating to: ${proofreadingUrl}`);

    await page.goto(proofreadingUrl, { waitUntil: 'networkidle', timeout: 30000 });

    // Wait for page to load
    await page.waitForTimeout(5000);

    console.log('\nStep 1: Page loaded, taking screenshot...');
    await page.screenshot({ path: 'test-results/direct-proof-01-initial.png', fullPage: true });

    // Check URL
    const currentUrl = page.url();
    console.log(`Current URL: ${currentUrl}`);

    // Check page title
    const title = await page.title();
    console.log(`Page title: ${title}`);

    // Check for error messages
    console.log('\nStep 2: Checking for error messages...');
    const errorSelectors = [
      '.error',
      '[role="alert"]',
      '.alert-error',
      '.text-red-500',
      '.text-red-600',
      '.text-red-700',
      'text:has-text("error")',
      'text:has-text("错误")',
      'text:has-text("失败")',
      'text:has-text("无法加载")',
      'text:has-text("出错")',
    ];

    for (const selector of errorSelectors) {
      const errors = await page.locator(selector).allTextContents();
      if (errors.length > 0) {
        console.log(`Found errors with selector "${selector}":`);
        errors.forEach(err => console.log(`  - ${err}`));
      }
    }

    // Check for specific proofreading components
    console.log('\nStep 3: Checking for proofreading components...');

    const hasArticleTitle = await page.locator('h1').count() > 0;
    console.log(`Has article title (h1): ${hasArticleTitle}`);
    if (hasArticleTitle) {
      const articleTitle = await page.locator('h1').first().textContent();
      console.log(`Article title: "${articleTitle}"`);
    }

    const hasViewModeButtons = await page.locator('button:has-text("Original"), button:has-text("Rendered"), button:has-text("Preview"), button:has-text("原始"), button:has-text("预览")').count();
    console.log(`View mode buttons found: ${hasViewModeButtons}`);

    const hasIssuesList = await page.locator('[data-testid*="issue"], .issue, .proofreading').count();
    console.log(`Issues/proofreading elements found: ${hasIssuesList}`);

    const hasMainContent = await page.locator('main, article, [role="main"]').count();
    console.log(`Main content elements: ${hasMainContent}`);

    // Check for loading states
    const hasLoadingSpinner = await page.locator('.loading, .spinner, [role="progressbar"]').count();
    console.log(`Loading indicators: ${hasLoadingSpinner}`);

    console.log('\nStep 4: Taking final screenshot...');
    await page.screenshot({ path: 'test-results/direct-proof-02-final.png', fullPage: true });

    // Get all text content to see what's actually displayed
    const bodyText = await page.locator('body').textContent();
    console.log('\nPage text content (first 500 chars):');
    console.log(bodyText?.substring(0, 500));

    // Check network requests
    console.log('\nStep 5: Summary...');
    console.log(`URL contains /proofreading/: ${currentUrl.includes('/proofreading/')}`);
    console.log(`Has article title: ${hasArticleTitle}`);
    console.log(`Has UI components: ${hasViewModeButtons > 0 || hasIssuesList > 0}`);
  });
});
