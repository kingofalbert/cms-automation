import { test, expect } from '@playwright/test';

// Configuration
const FRONTEND_URL = process.env.TEST_LOCAL
  ? 'http://localhost:3000'
  : 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

const BACKEND_URL = 'https://cms-automation-backend-baau2zqeqq-ue.a.run.app';

test.describe('Comprehensive Visual and Functional Tests', () => {

  test.beforeEach(async ({ page }) => {
    // Collect console messages and errors
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      if (type === 'error' || type === 'warning') {
        console.log(`[Browser ${type.toUpperCase()}] ${text}`);
      }
    });

    // Collect network errors
    page.on('requestfailed', request => {
      console.log(`[Network Failed] ${request.method()} ${request.url()} - ${request.failure()?.errorText}`);
    });
  });

  test('Homepage - Worklist Display Test', async ({ page }) => {
    console.log('\n========================================');
    console.log('TEST 1: Homepage Worklist Display');
    console.log('========================================\n');

    // Step 1: Navigate to homepage
    console.log('Step 1: Navigating to homepage...');
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 30000 });

    // Take initial screenshot
    await page.screenshot({ path: 'test-results/01-homepage-initial.png', fullPage: true });
    console.log('✓ Screenshot saved: 01-homepage-initial.png');

    // Step 2: Check if page loaded
    const title = await page.title();
    console.log(`Page title: ${title}`);

    // Step 3: Check for worklist API call
    console.log('\nStep 2: Checking worklist API...');

    const worklistResponse = await page.waitForResponse(
      response => response.url().includes('/v1/worklist') && response.status() === 200,
      { timeout: 15000 }
    ).catch(() => null);

    if (worklistResponse) {
      const data = await worklistResponse.json();
      console.log(`✓ Worklist API response received`);
      console.log(`  Total items: ${data.total || 0}`);
      console.log(`  Items returned: ${data.items?.length || 0}`);

      if (data.items && data.items.length > 0) {
        console.log(`  First item: ID=${data.items[0].id}, Title="${data.items[0].title}"`);
      }
    } else {
      console.log('✗ Worklist API call not detected or failed');
    }

    // Step 4: Wait for worklist to render
    console.log('\nStep 3: Checking DOM elements...');

    // Check if worklist table/list exists
    await page.waitForTimeout(2000); // Give time for rendering

    const worklistContainer = page.locator('[data-testid="worklist-container"], .worklist, table, [role="table"]').first();
    const exists = await worklistContainer.count() > 0;

    console.log(`Worklist container exists: ${exists}`);

    if (exists) {
      const itemCount = await page.locator('tr[data-testid*="worklist"], [data-testid*="item"], .worklist-item').count();
      console.log(`Visible worklist items: ${itemCount}`);
    }

    // Step 5: Check for error messages
    const errorMessages = await page.locator('.error, [role="alert"], .alert-error').allTextContents();
    if (errorMessages.length > 0) {
      console.log('\n⚠️  Error messages found:');
      errorMessages.forEach(msg => console.log(`  - ${msg}`));
    }

    // Step 6: Take final screenshot
    await page.screenshot({ path: 'test-results/02-homepage-final.png', fullPage: true });
    console.log('\n✓ Screenshot saved: 02-homepage-final.png');

    // Assertions
    expect(worklistResponse).toBeTruthy();
  });

  test('Worklist Page - Full Functionality Test', async ({ page }) => {
    console.log('\n========================================');
    console.log('TEST 2: Worklist Page Functionality');
    console.log('========================================\n');

    // Navigate to worklist page directly
    await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle' });
    await page.screenshot({ path: 'test-results/03-worklist-page.png', fullPage: true });

    console.log('✓ Worklist page loaded');

    // Check for data
    await page.waitForTimeout(3000);
    const hasData = await page.locator('table tbody tr, .worklist-item').count() > 0;
    console.log(`Data visible: ${hasData}`);

    await page.screenshot({ path: 'test-results/04-worklist-data.png', fullPage: true });
  });

  test('Proofreading Review Page - Visual Test', async ({ page }) => {
    console.log('\n========================================');
    console.log('TEST 3: Proofreading Review Page');
    console.log('========================================\n');

    // First get a worklist item ID
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });

    const worklistResponse = await page.waitForResponse(
      response => response.url().includes('/v1/worklist'),
      { timeout: 10000 }
    ).catch(() => null);

    if (worklistResponse) {
      const data = await worklistResponse.json();
      if (data.items && data.items.length > 0) {
        const itemId = data.items[0].id;
        console.log(`Testing with worklist item ID: ${itemId}`);

        // Navigate to proofreading page
        await page.goto(`${FRONTEND_URL}#/proofreading/${itemId}`, { waitUntil: 'networkidle' });
        await page.waitForTimeout(3000);

        await page.screenshot({ path: 'test-results/05-proofreading-page.png', fullPage: true });
        console.log('✓ Proofreading page screenshot saved');

        // Check for view mode buttons
        const viewModeButtons = await page.locator('button:has-text("Original"), button:has-text("Rendered"), button:has-text("Preview")').count();
        console.log(`View mode buttons found: ${viewModeButtons}`);

        // Check for issues list
        const issuesList = await page.locator('[data-testid*="issue"], .issue-item, .proofreading-issue').count();
        console.log(`Issues found: ${issuesList}`);

        await page.screenshot({ path: 'test-results/06-proofreading-details.png', fullPage: true });
      }
    }
  });

  test('API Health Check', async ({ page }) => {
    console.log('\n========================================');
    console.log('TEST 4: Backend API Health');
    console.log('========================================\n');

    // Test backend health endpoint
    const response = await page.request.get(`${BACKEND_URL}/health`);
    console.log(`Health endpoint status: ${response.status()}`);

    const data = await response.json();
    console.log('Health data:', JSON.stringify(data, null, 2));

    expect(response.status()).toBe(200);
  });

  test('Network Waterfall Analysis', async ({ page }) => {
    console.log('\n========================================');
    console.log('TEST 5: Network Performance Analysis');
    console.log('========================================\n');

    const requests: any[] = [];

    page.on('request', request => {
      requests.push({
        url: request.url(),
        method: request.method(),
        resourceType: request.resourceType(),
      });
    });

    page.on('response', async response => {
      const timing = response.request().timing();
      console.log(`[${response.status()}] ${response.request().method()} ${response.url()} - ${timing?.responseEnd}ms`);
    });

    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(5000);

    console.log(`\nTotal requests made: ${requests.length}`);

    const apiRequests = requests.filter(r => r.url.includes('/v1/'));
    console.log(`API requests: ${apiRequests.length}`);
    apiRequests.forEach(r => {
      console.log(`  - ${r.method} ${r.url}`);
    });
  });

  test('Console Error Detection', async ({ page }) => {
    console.log('\n========================================');
    console.log('TEST 6: Console Error Detection');
    console.log('========================================\n');

    const errors: string[] = [];
    const warnings: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      } else if (msg.type() === 'warning') {
        warnings.push(msg.text());
      }
    });

    page.on('pageerror', error => {
      errors.push(`Page Error: ${error.message}`);
    });

    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(5000);

    console.log(`\nErrors found: ${errors.length}`);
    errors.forEach(err => console.log(`  ❌ ${err}`));

    console.log(`\nWarnings found: ${warnings.length}`);
    warnings.forEach(warn => console.log(`  ⚠️  ${warn}`));

    if (errors.length > 0) {
      console.log('\n⚠️  Errors detected - investigation needed');
    }
  });
});
