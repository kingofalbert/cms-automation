/**
 * Test with correct proofreading route
 */

const { chromium } = require('playwright');

const BASE_URL = 'https://storage.googleapis.com/cms-automation-frontend-2025/index.html';
const TEST_EMAIL = 'allen.chen@epochtimes.com';
const TEST_PASSWORD = 'Editor123$';

async function runTest() {
  console.log('\n========================================');
  console.log('  Proofreading Review Test (Correct Route)');
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

    // 2. Navigate to correct proofreading review URL: /worklist/:id/review
    const itemId = 13; // Known proofreading_review item
    const correctUrl = `${BASE_URL}#/worklist/${itemId}/review`;
    console.log('2. Navigating to:', correctUrl);

    await page.goto(correctUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(8000); // Wait longer for data to load

    await page.screenshot({ path: '/tmp/proofreading_correct_route.png', fullPage: true });
    console.log('   URL:', page.url());

    // 3. Check for proofreading issues
    console.log('3. Checking for proofreading issues...');

    const pageState = await page.evaluate(() => {
      const body = document.body.innerText;

      // Look for issue-related text
      const hasOriginal = body.includes('Original') || body.includes('原文');
      const hasSuggested = body.includes('Suggested') || body.includes('建议');
      const hasIssueList = body.includes('Issue') || body.includes('问题');
      const hasAcceptReject = body.includes('Accept') || body.includes('Reject') || body.includes('接受') || body.includes('拒绝');

      // Check for actual content in red/green spans
      const redSpans = Array.from(document.querySelectorAll('[class*="text-red"]'));
      const greenSpans = Array.from(document.querySelectorAll('[class*="text-green"]'));

      const redTexts = redSpans
        .map(s => s.textContent?.trim())
        .filter(t => t && t.length > 5 && !t.includes('Original') && !t.includes('原文'))
        .slice(0, 5);

      const greenTexts = greenSpans
        .map(s => s.textContent?.trim())
        .filter(t => t && t.length > 5 && !t.includes('Suggested') && !t.includes('建议'))
        .slice(0, 5);

      return {
        bodyLength: body.length,
        hasOriginal,
        hasSuggested,
        hasIssueList,
        hasAcceptReject,
        redTexts,
        greenTexts,
        bodyPreview: body.substring(0, 1500)
      };
    });

    console.log('   Body length:', pageState.bodyLength);
    console.log('   Has Original label:', pageState.hasOriginal);
    console.log('   Has Suggested label:', pageState.hasSuggested);
    console.log('   Has Issue list:', pageState.hasIssueList);
    console.log('   Has Accept/Reject:', pageState.hasAcceptReject);

    console.log('\n   Red text samples (original text):');
    if (pageState.redTexts.length > 0) {
      pageState.redTexts.forEach((text, i) => {
        console.log(`     [${i+1}] "${text.substring(0, 80)}"`);
      });
    } else {
      console.log('     (none found)');
    }

    console.log('\n   Green text samples (suggested text):');
    if (pageState.greenTexts.length > 0) {
      pageState.greenTexts.forEach((text, i) => {
        console.log(`     [${i+1}] "${text.substring(0, 80)}"`);
      });
    } else {
      console.log('     (none found)');
    }

    // Determine success
    const hasContent = pageState.redTexts.length > 0 || pageState.greenTexts.length > 0;
    const hasUI = pageState.hasOriginal && pageState.hasSuggested;

    console.log('\n========================================');
    if (hasContent) {
      console.log('  SUCCESS: Issue texts are displayed correctly!');
    } else if (hasUI) {
      console.log('  PARTIAL: UI elements present but no issue texts');
      console.log('\n  Body preview:');
      console.log(pageState.bodyPreview.substring(0, 800));
    } else if (pageState.bodyLength < 100) {
      console.log('  FAILED: Page appears empty');
    } else {
      console.log('  FAILED: Could not verify issue display');
      console.log('\n  Body preview:');
      console.log(pageState.bodyPreview.substring(0, 800));
    }
    console.log('========================================\n');

    console.log('Screenshot saved to /tmp/proofreading_correct_route.png');

    return hasContent || hasUI;

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
