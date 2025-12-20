/**
 * Test Proofreading Review Page Fix
 * Verifies that original_text and suggested_text are displayed correctly
 */

const { chromium } = require('playwright');
const fs = require('fs');

const BASE_URL = 'https://storage.googleapis.com/cms-automation-frontend-2025/index.html';
const TEST_EMAIL = 'allen.chen@epochtimes.com';
const TEST_PASSWORD = 'Editor123$';

async function runTest() {
  console.log('\n========================================');
  console.log('  Proofreading Fix Verification Test');
  console.log('========================================\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  try {
    // 1. Login
    console.log('1. Navigating to production URL...');
    await page.goto(BASE_URL + '?v=' + Date.now(), { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    console.log('2. Logging in...');
    const emailInput = await page.$('input[type="email"]');
    const passwordInput = await page.$('input[type="password"]');
    const submitBtn = await page.$('button[type="submit"]');

    if (emailInput && passwordInput && submitBtn) {
      await emailInput.fill(TEST_EMAIL);
      await passwordInput.fill(TEST_PASSWORD);
      await submitBtn.click();
      await page.waitForTimeout(5000);
    } else {
      console.log('ERROR: Login form not found');
      await page.screenshot({ path: '/tmp/proofreading_test_error.png' });
      return false;
    }

    console.log('   Current URL:', page.url());

    // 2. Check worklist for proofreading_review items
    console.log('3. Looking for proofreading_review items in worklist...');
    await page.waitForTimeout(3000);

    // Find items with proofreading_review status
    const statusBadges = await page.$$('text=proofreading_review');
    console.log('   Found', statusBadges.length, 'items with proofreading_review status');

    if (statusBadges.length === 0) {
      console.log('   No proofreading_review items found. Looking for any clickable item...');
      await page.screenshot({ path: '/tmp/proofreading_test_worklist.png' });

      // Try to find first row that might be clickable
      const tableRows = await page.$$('table tbody tr');
      if (tableRows.length > 0) {
        console.log('   Found', tableRows.length, 'table rows');
        // Click on the first row
        await tableRows[0].click();
        await page.waitForTimeout(2000);
      }
    } else {
      // Click on the first proofreading_review item
      const firstItem = statusBadges[0];
      const parentRow = await firstItem.$('xpath=ancestor::tr');
      if (parentRow) {
        await parentRow.click();
        await page.waitForTimeout(2000);
      }
    }

    // 3. Navigate to proofreading review page
    // Look for a "Review" button or navigate directly
    console.log('4. Navigating to proofreading review...');

    // Check if we need to click a review button
    const reviewBtn = await page.$('text=Review, text=校对审核, button:has-text("Review")');
    if (reviewBtn) {
      await reviewBtn.click();
      await page.waitForTimeout(3000);
    }

    // Try direct navigation to a known proofreading review page
    // Find the first proofreading_review item ID from worklist
    const currentUrl = page.url();
    console.log('   Current URL after navigation:', currentUrl);

    await page.screenshot({ path: '/tmp/proofreading_test_current.png' });

    // Navigate directly to proofreading review page for item 1 (or find valid ID)
    console.log('5. Trying direct navigation to proofreading review page...');

    // Get a valid item ID from the worklist API
    const worklistResponse = await page.evaluate(async () => {
      try {
        const response = await fetch('https://cms-automation-backend-297291472291.us-east1.run.app/api/worklist?status=proofreading_review&limit=1');
        return await response.json();
      } catch (e) {
        return { error: e.message };
      }
    });

    console.log('   Worklist API response:', JSON.stringify(worklistResponse).substring(0, 200));

    let itemId = null;
    if (worklistResponse.items && worklistResponse.items.length > 0) {
      itemId = worklistResponse.items[0].id;
      console.log('   Found proofreading_review item ID:', itemId);
    } else {
      // Fallback: try to get any item with proofreading issues
      console.log('   No proofreading_review items, trying to get any item...');
      const anyItem = await page.evaluate(async () => {
        try {
          const response = await fetch('https://cms-automation-backend-297291472291.us-east1.run.app/api/worklist?limit=10');
          const data = await response.json();
          // Find first item with article_id
          for (const item of data.items || []) {
            if (item.article_id) {
              return item;
            }
          }
          return data.items?.[0];
        } catch (e) {
          return { error: e.message };
        }
      });

      if (anyItem && anyItem.id) {
        itemId = anyItem.id;
        console.log('   Using item ID:', itemId, 'status:', anyItem.status);
      }
    }

    if (!itemId) {
      console.log('ERROR: Could not find any valid worklist item');
      return false;
    }

    // Navigate to proofreading review page
    const proofreadingUrl = BASE_URL + '#/proofreading-review/' + itemId;
    console.log('6. Navigating to:', proofreadingUrl);
    await page.goto(proofreadingUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(5000);

    await page.screenshot({ path: '/tmp/proofreading_test_review_page.png', fullPage: true });

    // 4. Check for proofreading issues display
    console.log('7. Checking proofreading issues...');

    // Look for Original/Suggested text elements
    const originalTextEls = await page.$$('text=Original, text="原文"');
    const suggestedTextEls = await page.$$('text=Suggested, text="建议"');

    console.log('   Found "Original/原文" labels:', originalTextEls.length);
    console.log('   Found "Suggested/建议" labels:', suggestedTextEls.length);

    // Check if issue content is visible
    const issueContent = await page.evaluate(() => {
      // Find elements with issue details
      const containers = document.querySelectorAll('[class*="issue"], [class*="proofreading"]');
      const results = [];

      containers.forEach(container => {
        const text = container.textContent;
        if (text && text.length > 20) {
          results.push(text.substring(0, 200));
        }
      });

      // Also look for specific patterns
      const allText = document.body.innerText;
      const hasOriginal = allText.includes('Original') || allText.includes('原文');
      const hasSuggested = allText.includes('Suggested') || allText.includes('建议');
      const hasEmptyIssue = allText.includes('原文: ') && allText.match(/原文:\s*建议/);

      return {
        containerCount: containers.length,
        samples: results.slice(0, 3),
        hasOriginal,
        hasSuggested,
        hasEmptyIssue,
        bodyTextSample: allText.substring(0, 1000)
      };
    });

    console.log('   Issue containers found:', issueContent.containerCount);
    console.log('   Has Original label:', issueContent.hasOriginal);
    console.log('   Has Suggested label:', issueContent.hasSuggested);
    console.log('   Has empty issue pattern:', issueContent.hasEmptyIssue);

    if (issueContent.samples.length > 0) {
      console.log('\n   Sample issue content:');
      issueContent.samples.forEach((sample, i) => {
        console.log(`   [${i+1}] ${sample}`);
      });
    }

    // Check for the specific problem: empty original_text and suggested_text
    const emptyTextCheck = await page.evaluate(() => {
      // Find spans that should contain issue text
      const redSpans = document.querySelectorAll('.text-red-700, .text-red-900');
      const greenSpans = document.querySelectorAll('.text-green-700, .text-green-900');

      let emptyRed = 0;
      let nonEmptyRed = 0;
      let emptyGreen = 0;
      let nonEmptyGreen = 0;
      let redTexts = [];
      let greenTexts = [];

      redSpans.forEach(span => {
        const text = span.textContent?.trim() || '';
        if (text.length === 0 || text === '原文:' || text === 'Original:') {
          emptyRed++;
        } else {
          nonEmptyRed++;
          if (redTexts.length < 3) redTexts.push(text);
        }
      });

      greenSpans.forEach(span => {
        const text = span.textContent?.trim() || '';
        if (text.length === 0 || text === '建议:' || text === 'Suggested:') {
          emptyGreen++;
        } else {
          nonEmptyGreen++;
          if (greenTexts.length < 3) greenTexts.push(text);
        }
      });

      return {
        redSpans: redSpans.length,
        greenSpans: greenSpans.length,
        emptyRed,
        nonEmptyRed,
        emptyGreen,
        nonEmptyGreen,
        redTexts,
        greenTexts
      };
    });

    console.log('\n   === TEXT CONTENT CHECK ===');
    console.log('   Red spans (original text):', emptyTextCheck.redSpans);
    console.log('     - Empty:', emptyTextCheck.emptyRed);
    console.log('     - Non-empty:', emptyTextCheck.nonEmptyRed);
    console.log('   Green spans (suggested text):', emptyTextCheck.greenSpans);
    console.log('     - Empty:', emptyTextCheck.emptyGreen);
    console.log('     - Non-empty:', emptyTextCheck.nonEmptyGreen);

    if (emptyTextCheck.redTexts.length > 0) {
      console.log('\n   Sample original texts:');
      emptyTextCheck.redTexts.forEach((text, i) => {
        console.log(`     [${i+1}] "${text}"`);
      });
    }

    if (emptyTextCheck.greenTexts.length > 0) {
      console.log('   Sample suggested texts:');
      emptyTextCheck.greenTexts.forEach((text, i) => {
        console.log(`     [${i+1}] "${text}"`);
      });
    }

    // Determine test result
    const success = emptyTextCheck.nonEmptyRed > 0 || emptyTextCheck.nonEmptyGreen > 0;

    console.log('\n========================================');
    if (success) {
      console.log('  TEST PASSED: Issue texts are displayed!');
    } else if (emptyTextCheck.redSpans === 0 && emptyTextCheck.greenSpans === 0) {
      console.log('  TEST INCONCLUSIVE: No issue spans found');
      console.log('  (May need different item or issues not loaded)');
    } else {
      console.log('  TEST FAILED: Issue texts are empty!');
    }
    console.log('========================================\n');

    await page.screenshot({ path: '/tmp/proofreading_test_final.png', fullPage: true });
    console.log('Screenshots saved to /tmp/proofreading_test_*.png');

    return success;

  } catch (error) {
    console.log('ERROR:', error.message);
    await page.screenshot({ path: '/tmp/proofreading_test_error.png' });
    return false;
  } finally {
    await browser.close();
  }
}

runTest().then(success => {
  process.exit(success ? 0 : 1);
});
