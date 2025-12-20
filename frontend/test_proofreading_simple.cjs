/**
 * Simple Proofreading Review Page Test
 */

const { chromium } = require('playwright');

const BASE_URL = 'https://storage.googleapis.com/cms-automation-frontend-2025/index.html';
const TEST_EMAIL = 'allen.chen@epochtimes.com';
const TEST_PASSWORD = 'Editor123$';

async function runTest() {
  console.log('\n========================================');
  console.log('  Proofreading Page Test');
  console.log('========================================\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  try {
    // 1. Login
    console.log('1. Logging in...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    await page.fill('input[type="email"]', TEST_EMAIL);
    await page.fill('input[type="password"]', TEST_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(5000);

    console.log('   Logged in, URL:', page.url());

    // 2. Navigate directly to proofreading review page for item 13
    const itemId = 13; // Known proofreading_review item
    const proofreadingUrl = `${BASE_URL}#/proofreading-review/${itemId}`;
    console.log('2. Navigating to proofreading review:', proofreadingUrl);

    await page.goto(proofreadingUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(5000);

    // Take screenshot
    await page.screenshot({ path: '/tmp/proofreading_page.png', fullPage: true });

    // 3. Check for issue content
    console.log('3. Checking for proofreading issues...');

    const pageContent = await page.evaluate(() => {
      const body = document.body.innerText;

      // Look for specific issue indicators
      const hasIssueList = document.querySelector('[class*="issue"]') !== null;
      const hasOriginalLabel = body.includes('Original') || body.includes('原文');
      const hasSuggestedLabel = body.includes('Suggested') || body.includes('建议');

      // Check red/green spans for actual content
      const redSpans = Array.from(document.querySelectorAll('.text-red-700, .text-red-900, [class*="text-red"]'));
      const greenSpans = Array.from(document.querySelectorAll('.text-green-700, .text-green-900, [class*="text-green"]'));

      // Get sample texts
      const redTexts = redSpans.map(s => s.textContent?.trim()).filter(t => t && t.length > 3).slice(0, 5);
      const greenTexts = greenSpans.map(s => s.textContent?.trim()).filter(t => t && t.length > 3).slice(0, 5);

      // Check for empty state
      const hasEmptyState = body.includes('Great job') || body.includes('no proofreading issues') || body.includes('暂无校对问题');

      // Check for loading state
      const isLoading = document.querySelector('.animate-spin') !== null;

      // Check for error state
      const hasError = body.includes('Unable to load') || body.includes('加载失败');

      return {
        hasIssueList,
        hasOriginalLabel,
        hasSuggestedLabel,
        redTexts,
        greenTexts,
        hasEmptyState,
        isLoading,
        hasError,
        bodyPreview: body.substring(0, 2000)
      };
    });

    console.log('   Has issue elements:', pageContent.hasIssueList);
    console.log('   Has Original label:', pageContent.hasOriginalLabel);
    console.log('   Has Suggested label:', pageContent.hasSuggestedLabel);
    console.log('   Is loading:', pageContent.isLoading);
    console.log('   Has error:', pageContent.hasError);
    console.log('   Has empty state:', pageContent.hasEmptyState);

    console.log('\n   Red text samples (original text):');
    pageContent.redTexts.forEach((text, i) => {
      console.log(`     [${i+1}] "${text.substring(0, 80)}"`);
    });

    console.log('\n   Green text samples (suggested text):');
    pageContent.greenTexts.forEach((text, i) => {
      console.log(`     [${i+1}] "${text.substring(0, 80)}"`);
    });

    // Determine success
    const hasContent = pageContent.redTexts.length > 0 || pageContent.greenTexts.length > 0;

    console.log('\n========================================');
    if (hasContent) {
      console.log('  SUCCESS: Issue texts are displayed correctly!');
    } else if (pageContent.isLoading) {
      console.log('  PENDING: Page still loading...');
    } else if (pageContent.hasError) {
      console.log('  FAILED: Error loading page');
    } else if (pageContent.hasEmptyState) {
      console.log('  INFO: No issues to display (empty state)');
    } else {
      console.log('  FAILED: Issue texts not found');
      console.log('\n  Body preview:');
      console.log(pageContent.bodyPreview.substring(0, 500));
    }
    console.log('========================================\n');

    console.log('Screenshot saved to /tmp/proofreading_page.png');

    return hasContent;

  } catch (error) {
    console.log('ERROR:', error.message);
    await page.screenshot({ path: '/tmp/proofreading_error.png' });
    return false;
  } finally {
    await browser.close();
  }
}

runTest().then(success => {
  process.exit(success ? 0 : 1);
});
