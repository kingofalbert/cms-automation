/**
 * Comprehensive Visual Test for Modal Proofreading Review Panel
 * Tests the 3-column layout redesign in the modal dialog
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
  console.log('  Modal Proofreading Panel Visual Tests');
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
    await page.screenshot({ path: '/tmp/modal_1_logged_in.png' });
    testResults.screenshots.push('/tmp/modal_1_logged_in.png');

    // 2. Check worklist for proofreading items
    console.log('\n2. Worklist Phase');

    // Wait for worklist table
    await page.waitForSelector('table tbody tr', { timeout: 10000 }).catch(() => null);
    await page.waitForTimeout(1000);

    // Find worklist items
    const worklistItems = await page.evaluate(() => {
      const rows = document.querySelectorAll('table tbody tr');
      return Array.from(rows).slice(0, 10).map((row, index) => {
        const cells = row.querySelectorAll('td');
        const statusBadge = row.querySelector('[class*="badge"], [class*="Badge"]');
        return {
          index,
          title: cells[0]?.textContent?.trim()?.substring(0, 50),
          status: statusBadge?.textContent?.trim() || cells[1]?.textContent?.trim(),
        };
      });
    });

    console.log('   Found items:');
    worklistItems.forEach(item => {
      console.log(`   [${item.index}] ${item.title} - ${item.status}`);
    });

    // Find a proofreading_review item
    const proofreadingItem = worklistItems.find(i =>
      i.status?.toLowerCase().includes('proofreading') ||
      i.status?.includes('校对')
    );

    if (proofreadingItem) {
      console.log(`   Using item: ${proofreadingItem.title}`);
    }

    await page.screenshot({ path: '/tmp/modal_2_worklist.png' });
    testResults.screenshots.push('/tmp/modal_2_worklist.png');

    // 3. Click on first item to open modal
    console.log('\n3. Opening Article Modal');

    const firstRow = await page.$('table tbody tr:first-child');
    if (firstRow) {
      await firstRow.click();
      await page.waitForTimeout(3000);
    }

    // Check if modal opened
    let modalOpened = await page.evaluate(() => {
      return document.querySelector('[role="dialog"]') !== null ||
             document.body.innerText.includes('文章审核') ||
             document.body.innerText.includes('Article Review');
    });

    await page.screenshot({ path: '/tmp/modal_3_after_click.png' });
    testResults.screenshots.push('/tmp/modal_3_after_click.png');
    logTest('Article modal opened', modalOpened);

    // 4. Navigate to proofreading tab if needed
    console.log('\n4. Finding Proofreading Panel');

    // Look for proofreading/校对 tab
    const proofreadingTab = await page.$('button:has-text("校对"), button:has-text("Proofreading"), [role="tab"]:has-text("校对")');
    if (proofreadingTab) {
      await proofreadingTab.click();
      await page.waitForTimeout(2000);
      console.log('   Clicked proofreading tab');
    }

    await page.screenshot({ path: '/tmp/modal_4_proofreading_tab.png', fullPage: true });
    testResults.screenshots.push('/tmp/modal_4_proofreading_tab.png');

    // 5. Test the 3-column layout in modal
    console.log('\n5. Modal Layout Structure Tests');

    const layoutTests = await page.evaluate(() => {
      const results = {};
      const body = document.body.innerText;

      // Check for panel headers
      results.hasIssueList = body.includes('问题列表') || body.includes('Issue');
      results.hasStats = body.includes('待处理') || body.includes('已接受') || body.includes('已拒绝');

      // Check for view mode toggles
      results.hasDiffToggle = body.includes('对比') || body.includes('Diff');
      results.hasPreviewToggle = body.includes('预览') || body.includes('Preview');

      // Check for issue details
      results.hasDetailsPanel = body.includes('问题详情') || body.includes('Issue Details');

      // Check for original/suggested
      results.hasOriginal = body.includes('原文');
      results.hasSuggested = body.includes('建议');

      // Check for actions
      results.hasAccept = body.includes('接受') || body.includes('Accept');
      results.hasReject = body.includes('拒绝') || body.includes('Reject');

      // Check for submit
      results.hasSubmit = body.includes('提交审核') || body.includes('Submit');

      // Check for keyboard hint
      results.hasKeyboardHint = body.includes('快捷键') || body.includes('A 接受');

      return results;
    });

    logTest('Issue list visible', layoutTests.hasIssueList);
    logTest('Stats visible', layoutTests.hasStats);
    logTest('Diff toggle visible', layoutTests.hasDiffToggle);
    logTest('Preview toggle visible', layoutTests.hasPreviewToggle);
    logTest('Details panel visible', layoutTests.hasDetailsPanel);
    logTest('Original text label visible', layoutTests.hasOriginal);
    logTest('Suggested text label visible', layoutTests.hasSuggested);
    logTest('Accept button visible', layoutTests.hasAccept);
    logTest('Reject button visible', layoutTests.hasReject);
    logTest('Submit button visible', layoutTests.hasSubmit);
    logTest('Keyboard hint visible', layoutTests.hasKeyboardHint);

    // 6. Test Content in Original/Suggested Boxes
    console.log('\n6. Content Verification Tests');

    const contentTests = await page.evaluate(() => {
      const results = {};

      // Find elements with red/green background (original/suggested boxes)
      const allElements = document.querySelectorAll('*');
      let redBgContent = [];
      let greenBgContent = [];

      allElements.forEach(el => {
        const className = el.className || '';
        if (typeof className === 'string') {
          if (className.includes('bg-red') || className.includes('border-red')) {
            const text = el.textContent?.trim();
            if (text && text.length > 3 && text.length < 200) {
              redBgContent.push(text);
            }
          }
          if (className.includes('bg-green') || className.includes('border-green')) {
            const text = el.textContent?.trim();
            if (text && text.length > 3 && text.length < 200) {
              greenBgContent.push(text);
            }
          }
        }
      });

      results.originalContent = redBgContent.length > 0 ? redBgContent[0] : null;
      results.suggestedContent = greenBgContent.length > 0 ? greenBgContent[0] : null;
      results.hasOriginalContent = redBgContent.length > 0 && redBgContent[0].length > 0;
      results.hasSuggestedContent = greenBgContent.length > 0 && greenBgContent[0].length > 0;

      return results;
    });

    logTest('Original box has content', contentTests.hasOriginalContent,
            contentTests.originalContent?.substring(0, 30) || '(empty)');
    logTest('Suggested box has content', contentTests.hasSuggestedContent,
            contentTests.suggestedContent?.substring(0, 30) || '(empty)');

    // 7. Test Interactive Features
    console.log('\n7. Interactive Features Tests');

    // Try clicking on diff/preview toggle
    const diffBtn = await page.$('button:has-text("对比")');
    const previewBtn = await page.$('button:has-text("预览")');

    if (previewBtn) {
      await previewBtn.click();
      await page.waitForTimeout(500);
      logTest('Preview button clickable', true);

      if (diffBtn) {
        await diffBtn.click();
        await page.waitForTimeout(500);
      }
    } else {
      logTest('Preview button clickable', false, 'Button not found');
    }

    // Try clicking accept button
    const acceptBtn = await page.$('button:has-text("接受")');
    if (acceptBtn) {
      await acceptBtn.click();
      await page.waitForTimeout(500);

      const decisionRecorded = await page.evaluate(() => {
        return document.body.innerText.includes('已接受') ||
               document.body.innerText.includes('待提交') ||
               document.body.innerText.includes('撤销决定');
      });
      logTest('Accept decision works', decisionRecorded);

      await page.screenshot({ path: '/tmp/modal_5_after_accept.png' });
      testResults.screenshots.push('/tmp/modal_5_after_accept.png');
    } else {
      logTest('Accept decision works', false, 'Button not found');
    }

    // 8. Console Error Check
    console.log('\n8. Error Check');
    const hasNoErrors = consoleErrors.length === 0;
    logTest('No console errors', hasNoErrors, hasNoErrors ? '' : `${consoleErrors.length} errors`);
    if (!hasNoErrors) {
      consoleErrors.slice(0, 3).forEach(err => {
        console.log(`     - ${err.substring(0, 80)}`);
      });
    }

    // Final screenshot
    await page.screenshot({ path: '/tmp/modal_final.png', fullPage: true });
    testResults.screenshots.push('/tmp/modal_final.png');

  } catch (error) {
    console.log('\n[ERROR]', error.message);
    await page.screenshot({ path: '/tmp/modal_error.png' });
    testResults.screenshots.push('/tmp/modal_error.png');
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
