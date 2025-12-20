/**
 * Debug Proofreading Route
 */

const { chromium } = require('playwright');

const BASE_URL = 'https://storage.googleapis.com/cms-automation-frontend-2025/index.html';
const TEST_EMAIL = 'allen.chen@epochtimes.com';
const TEST_PASSWORD = 'Editor123$';

async function runTest() {
  console.log('\n========================================');
  console.log('  Debug Proofreading Route');
  console.log('========================================\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  // Capture console messages
  const consoleLogs = [];
  page.on('console', msg => {
    consoleLogs.push({ type: msg.type(), text: msg.text() });
  });

  // Capture errors
  page.on('pageerror', err => {
    consoleLogs.push({ type: 'pageerror', text: err.message });
  });

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
    await page.screenshot({ path: '/tmp/debug_1_logged_in.png' });

    // 2. Go to worklist first
    console.log('2. Checking worklist...');
    await page.goto(BASE_URL + '#/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/tmp/debug_2_worklist.png' });

    // Check what items are visible
    const worklistInfo = await page.evaluate(() => {
      const rows = document.querySelectorAll('table tbody tr');
      const items = [];
      rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length > 0) {
          items.push({
            id: cells[0]?.textContent?.trim(),
            title: cells[1]?.textContent?.trim()?.substring(0, 50),
            status: cells[2]?.textContent?.trim()
          });
        }
      });
      return items;
    });
    console.log('   Worklist items:', JSON.stringify(worklistInfo, null, 2));

    // 3. Try clicking on a proofreading_review item
    console.log('3. Looking for proofreading_review items...');
    const proofreadingItems = worklistInfo.filter(i => i.status === 'proofreading_review');
    console.log('   Found', proofreadingItems.length, 'proofreading_review items');

    if (proofreadingItems.length > 0) {
      const targetId = proofreadingItems[0].id;
      console.log('   Clicking on item:', targetId);

      // Click on the row
      const row = await page.$(`table tbody tr:has(td:first-child:text("${targetId}"))`);
      if (row) {
        await row.click();
        await page.waitForTimeout(3000);
        await page.screenshot({ path: '/tmp/debug_3_after_click.png' });
        console.log('   URL after click:', page.url());
      }
    }

    // 4. Direct navigation to proofreading review
    console.log('4. Direct navigation to proofreading-review/13...');
    await page.goto(BASE_URL + '#/proofreading-review/13', { waitUntil: 'networkidle' });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: '/tmp/debug_4_direct_nav.png' });
    console.log('   URL:', page.url());

    // 5. Check console errors
    console.log('\n5. Console messages:');
    const errors = consoleLogs.filter(l => l.type === 'error' || l.type === 'pageerror');
    const warnings = consoleLogs.filter(l => l.type === 'warning');

    console.log('   Errors:', errors.length);
    errors.slice(0, 10).forEach(e => console.log('     -', e.text.substring(0, 200)));

    console.log('   Warnings:', warnings.length);

    // 6. Check what React route rendered
    const pageState = await page.evaluate(() => {
      const hash = window.location.hash;
      const pathname = hash.replace('#', '');
      const bodyText = document.body.innerText;
      const mainContent = document.querySelector('main')?.innerHTML || 'No main element';

      return {
        hash,
        pathname,
        bodyTextLength: bodyText.length,
        mainContentPreview: mainContent.substring(0, 500),
        hasLoadingState: bodyText.includes('Loading'),
        hasErrorState: bodyText.includes('Error') || bodyText.includes('error'),
        hasSkeleton: document.querySelector('.animate-pulse') !== null
      };
    });

    console.log('\n6. Page state:');
    console.log('   Hash:', pageState.hash);
    console.log('   Body text length:', pageState.bodyTextLength);
    console.log('   Has loading:', pageState.hasLoadingState);
    console.log('   Has error:', pageState.hasErrorState);
    console.log('   Has skeleton:', pageState.hasSkeleton);
    console.log('   Main content:', pageState.mainContentPreview);

    // 7. Wait longer and try again
    console.log('\n7. Waiting 10 more seconds...');
    await page.waitForTimeout(10000);
    await page.screenshot({ path: '/tmp/debug_5_after_wait.png' });

    const finalState = await page.evaluate(() => {
      return {
        bodyText: document.body.innerText.substring(0, 2000),
        url: window.location.href
      };
    });
    console.log('   Final URL:', finalState.url);
    console.log('   Final body preview:', finalState.bodyText.substring(0, 500));

    console.log('\n========================================');
    console.log('Screenshots saved to /tmp/debug_*.png');
    console.log('========================================\n');

  } catch (error) {
    console.log('ERROR:', error.message);
    await page.screenshot({ path: '/tmp/debug_error.png' });
  } finally {
    await browser.close();
  }
}

runTest();
