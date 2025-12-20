/**
 * API Response Debug Test
 * Tests the review-decisions API call and shows detailed response
 */

const { chromium } = require('playwright');

const BASE_URL = 'https://storage.googleapis.com/cms-automation-frontend-2025/index.html';
const TEST_EMAIL = 'allen.chen@epochtimes.com';
const TEST_PASSWORD = 'Editor123$';

async function runTest() {
  console.log('\n========================================');
  console.log('  API Response Debug Test');
  console.log('========================================\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
  });
  const page = await context.newPage();

  // Track API responses in detail
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('review-decisions')) {
      console.log('\n=== API Response ===');
      console.log('URL:', url);
      console.log('Status:', response.status());
      try {
        const body = await response.json();
        console.log('Response Body:', JSON.stringify(body, null, 2));
      } catch (e) {
        const text = await response.text();
        console.log('Response Text:', text);
      }
      console.log('===================\n');
    }
  });

  // Track API requests
  page.on('request', request => {
    const url = request.url();
    if (url.includes('review-decisions')) {
      console.log('\n=== API Request ===');
      console.log('URL:', url);
      console.log('Method:', request.method());
      console.log('Request Body:', request.postData());
      console.log('===================\n');
    }
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
    console.log('   Logged in successfully');

    // 2. Find and click proofreading item
    console.log('\n2. Finding proofreading item...');
    await page.waitForSelector('table tbody tr', { timeout: 10000 });

    const rows = await page.$$('table tbody tr');
    for (let i = 0; i < rows.length; i++) {
      const text = await rows[i].textContent();
      if (text.includes('Proofreading')) {
        console.log(`   Found proofreading item at row ${i}`);
        await rows[i].click();
        await page.waitForTimeout(3000);
        break;
      }
    }

    // 3. Navigate to proofreading tab
    console.log('\n3. Navigating to proofreading tab...');
    const proofreadingTab = await page.$('button:has-text("校对"), button:has-text("Proofreading")');
    if (proofreadingTab) {
      await proofreadingTab.click();
      await page.waitForTimeout(2000);
      console.log('   Clicked proofreading tab');
    }

    // 4. Accept first issue
    console.log('\n4. Accepting first issue...');
    const acceptBtn = await page.$('button:has-text("接受")');
    if (acceptBtn) {
      await acceptBtn.click();
      await page.waitForTimeout(500);
      console.log('   Accepted first issue');
    }

    // 5. Click submit
    console.log('\n5. Submitting decisions...');
    const submitBtn = await page.$('button:has-text("提交审核")');
    if (submitBtn) {
      const isEnabled = await submitBtn.isEnabled();
      console.log(`   Submit button enabled: ${isEnabled}`);

      if (isEnabled) {
        await submitBtn.click();
        console.log('   Clicked submit button');

        // Wait for API response
        await page.waitForTimeout(5000);
      }
    }

    await page.screenshot({ path: '/tmp/api_debug_final.png' });
    console.log('\n   Screenshot saved to /tmp/api_debug_final.png');

  } catch (error) {
    console.log('\n[ERROR]', error.message);
    await page.screenshot({ path: '/tmp/api_debug_error.png' });
  } finally {
    await browser.close();
  }

  console.log('\n========================================\n');
}

runTest();
