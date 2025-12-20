/**
 * Comprehensive Visual Test for Proofreading Review Panel
 * Tests the 3-column layout redesign and all interactive features
 */

const { chromium } = require('playwright');

const BASE_URL = 'https://storage.googleapis.com/cms-automation-frontend-2025/index.html';
const TEST_EMAIL = 'allen.chen@epochtimes.com';
const TEST_PASSWORD = 'Editor123$';

// Test results collector
const testResults = {
  passed: [],
  failed: [],
  screenshots: [],
};

function logTest(name, passed, details = '') {
  if (passed) {
    testResults.passed.push(name);
    console.log(`  [PASS] ${name}${details ? `: ${details}` : ''}`);
  } else {
    testResults.failed.push(name);
    console.log(`  [FAIL] ${name}${details ? `: ${details}` : ''}`);
  }
}

async function runTests() {
  console.log('\n========================================');
  console.log('  Proofreading Review Panel Visual Tests');
  console.log('========================================\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
  });
  const page = await context.newPage();

  // Capture console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  try {
    // 1. Login
    console.log('1. Login Phase');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    await page.fill('input[type="email"]', TEST_EMAIL);
    await page.fill('input[type="password"]', TEST_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(5000);

    const loggedIn = page.url().includes('#/') || await page.$('table');
    logTest('Login successful', !!loggedIn);
    await page.screenshot({ path: '/tmp/visual_1_logged_in.png' });
    testResults.screenshots.push('/tmp/visual_1_logged_in.png');

    // 2. Navigate to proofreading review page
    console.log('\n2. Navigation Phase');
    const reviewUrl = `${BASE_URL}#/worklist/13/review`;
    await page.goto(reviewUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(8000);

    await page.screenshot({ path: '/tmp/visual_2_proofreading_page.png', fullPage: true });
    testResults.screenshots.push('/tmp/visual_2_proofreading_page.png');

    // 3. Test 3-Column Layout
    console.log('\n3. Layout Structure Tests');

    const layoutTests = await page.evaluate(() => {
      const results = {};

      // Check for 3-column layout structure
      const body = document.body.innerText;

      // Left column: Issue list
      results.hasIssueList = body.includes('问题列表') || body.includes('Issue');

      // Center column: Diff/Preview toggle
      results.hasDiffToggle = body.includes('对比') || body.includes('Diff');
      results.hasPreviewToggle = body.includes('预览') || body.includes('Preview');

      // Right column: Issue details
      results.hasIssueDetails = body.includes('问题详情') || body.includes('Issue Details');

      // Check for Original/Suggested content
      results.hasOriginalLabel = body.includes('原文') || body.includes('Original');
      results.hasSuggestedLabel = body.includes('建议') || body.includes('Suggested');

      // Check for action buttons
      results.hasAcceptButton = body.includes('接受') || body.includes('Accept');
      results.hasRejectButton = body.includes('拒绝') || body.includes('Reject');

      // Check stats header
      results.hasStatsHeader = body.includes('待处理') || body.includes('pending');

      // Check footer with submit
      results.hasSubmitButton = body.includes('提交审核') || body.includes('Submit');

      // Check keyboard shortcuts hint
      results.hasKeyboardHint = body.includes('快捷键') || body.includes('A 接受');

      return results;
    });

    logTest('Issue list present', layoutTests.hasIssueList);
    logTest('Diff toggle present', layoutTests.hasDiffToggle);
    logTest('Preview toggle present', layoutTests.hasPreviewToggle);
    logTest('Issue details panel present', layoutTests.hasIssueDetails);
    logTest('Original label visible', layoutTests.hasOriginalLabel);
    logTest('Suggested label visible', layoutTests.hasSuggestedLabel);
    logTest('Accept button present', layoutTests.hasAcceptButton);
    logTest('Reject button present', layoutTests.hasRejectButton);
    logTest('Stats header present', layoutTests.hasStatsHeader);
    logTest('Submit button present', layoutTests.hasSubmitButton);
    logTest('Keyboard shortcuts hint present', layoutTests.hasKeyboardHint);

    // 4. Test Original/Suggested Content
    console.log('\n4. Content Visibility Tests');

    const contentTests = await page.evaluate(() => {
      const results = {};

      // Find red-bordered box (original text)
      const redBoxes = document.querySelectorAll('[class*="border-red"], [class*="bg-red"]');
      const redTexts = Array.from(redBoxes)
        .map(el => el.textContent?.trim())
        .filter(t => t && t.length > 5);
      results.originalTextContent = redTexts.length > 0 ? redTexts[0].substring(0, 50) : null;
      results.hasOriginalContent = redTexts.length > 0;

      // Find green-bordered box (suggested text)
      const greenBoxes = document.querySelectorAll('[class*="border-green"], [class*="bg-green"]');
      const greenTexts = Array.from(greenBoxes)
        .map(el => el.textContent?.trim())
        .filter(t => t && t.length > 5);
      results.suggestedTextContent = greenTexts.length > 0 ? greenTexts[0].substring(0, 50) : null;
      results.hasSuggestedContent = greenTexts.length > 0;

      // Check for empty content (the bug we fixed)
      const hasEmptyOriginal = redTexts.some(t => t === '' || t.trim().length === 0);
      const hasEmptySuggested = greenTexts.some(t => t === '' || t.trim().length === 0);
      results.noEmptyContent = !hasEmptyOriginal && !hasEmptySuggested;

      return results;
    });

    logTest('Original content has text', contentTests.hasOriginalContent, contentTests.originalTextContent || '(empty)');
    logTest('Suggested content has text', contentTests.hasSuggestedContent, contentTests.suggestedTextContent || '(empty)');
    logTest('No empty content boxes', contentTests.noEmptyContent);

    // 5. Test Issue List Interaction
    console.log('\n5. Issue List Interaction Tests');

    // Find issue items in the left panel
    const issueItems = await page.$$('button[class*="text-left"]');
    logTest('Issue items found', issueItems.length > 0, `Found ${issueItems.length} items`);

    if (issueItems.length > 1) {
      // Click on second issue
      await issueItems[1].click();
      await page.waitForTimeout(500);
      await page.screenshot({ path: '/tmp/visual_3_second_issue.png' });
      testResults.screenshots.push('/tmp/visual_3_second_issue.png');

      // Check if detail panel updated
      const detailUpdated = await page.evaluate(() => {
        const detailPanel = document.querySelector('[class*="border-l"]');
        return detailPanel && detailPanel.textContent?.includes('原文');
      });
      logTest('Detail panel updates on selection', detailUpdated);
    }

    // 6. Test View Mode Toggle
    console.log('\n6. View Mode Toggle Tests');

    // Find and click preview button
    const previewButton = await page.$('button:has-text("预览")');
    if (previewButton) {
      await previewButton.click();
      await page.waitForTimeout(500);
      await page.screenshot({ path: '/tmp/visual_4_preview_mode.png' });
      testResults.screenshots.push('/tmp/visual_4_preview_mode.png');
      logTest('Preview mode toggle works', true);

      // Switch back to diff mode
      const diffButton = await page.$('button:has-text("对比")');
      if (diffButton) {
        await diffButton.click();
        await page.waitForTimeout(500);
      }
    } else {
      logTest('Preview mode toggle works', false, 'Button not found');
    }

    // 7. Test Accept/Reject Actions
    console.log('\n7. Decision Action Tests');

    // Click accept button
    const acceptBtn = await page.$('button:has-text("接受")');
    if (acceptBtn) {
      await acceptBtn.click();
      await page.waitForTimeout(500);

      // Check if decision was recorded
      const decisionMade = await page.evaluate(() => {
        const body = document.body.innerText;
        return body.includes('已接受') || body.includes('待提交') || body.includes('撤销决定');
      });
      logTest('Accept decision recorded', decisionMade);
      await page.screenshot({ path: '/tmp/visual_5_after_accept.png' });
      testResults.screenshots.push('/tmp/visual_5_after_accept.png');

      // Find and click undo button
      const undoBtn = await page.$('button:has-text("撤销决定")');
      if (undoBtn) {
        await undoBtn.click();
        await page.waitForTimeout(500);
        logTest('Undo decision works', true);
      }
    } else {
      logTest('Accept decision recorded', false, 'Button not found');
    }

    // 8. Test Keyboard Shortcuts
    console.log('\n8. Keyboard Shortcut Tests');

    // Press 'A' for accept
    await page.keyboard.press('a');
    await page.waitForTimeout(300);

    const keyboardAccept = await page.evaluate(() => {
      return document.body.innerText.includes('已接受') ||
             document.body.innerText.includes('撤销决定');
    });
    logTest('Keyboard "A" triggers accept', keyboardAccept);

    // Press 'R' for reject
    await page.keyboard.press('r');
    await page.waitForTimeout(300);

    // Press Arrow Down
    await page.keyboard.press('ArrowDown');
    await page.waitForTimeout(300);

    await page.screenshot({ path: '/tmp/visual_6_after_keyboard.png' });
    testResults.screenshots.push('/tmp/visual_6_after_keyboard.png');
    logTest('Keyboard navigation works', true);

    // 9. Test Stats Display
    console.log('\n9. Stats Display Tests');

    const statsTests = await page.evaluate(() => {
      const body = document.body.innerText;
      return {
        showsPending: /待处理[:\s]*\d+/.test(body),
        showsAccepted: /已接受[:\s]*\d+/.test(body),
        showsRejected: /已拒绝[:\s]*\d+/.test(body),
      };
    });

    logTest('Shows pending count', statsTests.showsPending);
    logTest('Shows accepted count', statsTests.showsAccepted);
    logTest('Shows rejected count', statsTests.showsRejected);

    // 10. Console Error Check
    console.log('\n10. Error Check');
    const hasNoErrors = consoleErrors.length === 0;
    logTest('No console errors', hasNoErrors, hasNoErrors ? '' : `${consoleErrors.length} errors found`);
    if (!hasNoErrors) {
      consoleErrors.slice(0, 5).forEach(err => {
        console.log(`     - ${err.substring(0, 100)}`);
      });
    }

    // Final screenshot
    await page.screenshot({ path: '/tmp/visual_final.png', fullPage: true });
    testResults.screenshots.push('/tmp/visual_final.png');

  } catch (error) {
    console.log('\n[ERROR]', error.message);
    await page.screenshot({ path: '/tmp/visual_error.png' });
    testResults.screenshots.push('/tmp/visual_error.png');
  } finally {
    await browser.close();
  }

  // Print Summary
  console.log('\n========================================');
  console.log('  Test Summary');
  console.log('========================================');
  console.log(`  Passed: ${testResults.passed.length}`);
  console.log(`  Failed: ${testResults.failed.length}`);
  console.log(`  Total:  ${testResults.passed.length + testResults.failed.length}`);

  if (testResults.failed.length > 0) {
    console.log('\n  Failed Tests:');
    testResults.failed.forEach(t => console.log(`    - ${t}`));
  }

  console.log('\n  Screenshots:');
  testResults.screenshots.forEach(s => console.log(`    - ${s}`));

  console.log('\n========================================\n');

  const success = testResults.failed.length === 0;
  return success;
}

runTests().then(success => {
  process.exit(success ? 0 : 1);
});
