/**
 * Complete Visual Regression Test Suite
 * Tests all major features of the CMS Automation production environment
 */

const { chromium } = require('playwright');
const fs = require('fs');

const BASE_URL = 'https://storage.googleapis.com/cms-automation-frontend-2025/index.html';
const TEST_EMAIL = 'allen.chen@epochtimes.com';
const TEST_PASSWORD = 'Editor123$';
const SCREENSHOT_DIR = '/tmp/visual_regression';

// Ensure screenshot directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

const results = {
  passed: [],
  failed: [],
  warnings: []
};

function log(message, type = 'info') {
  const prefix = type === 'pass' ? '✅' : type === 'fail' ? '❌' : type === 'warn' ? '⚠️' : 'ℹ️';
  console.log(prefix + ' ' + message);
}

async function takeScreenshot(page, name) {
  const path = SCREENSHOT_DIR + '/' + name + '.png';
  await page.screenshot({ path, fullPage: true });
  return path;
}

async function runTests() {
  console.log('\n========================================');
  console.log('  Visual Regression Test Suite');
  console.log('  Target: ' + BASE_URL);
  console.log('========================================\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  // Collect console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  // Collect network errors
  const networkErrors = [];
  page.on('requestfailed', request => {
    networkErrors.push({
      url: request.url(),
      error: request.failure()?.errorText
    });
  });

  try {
    // ==========================================
    // TEST 1: Login Page Loads
    // ==========================================
    console.log('\n--- TEST 1: Login Page ---');
    await page.goto(BASE_URL + '?v=' + Date.now(), { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const loginUrl = page.url();
    if (loginUrl.includes('/login')) {
      log('Login page redirect works', 'pass');
      results.passed.push('Login page redirect');
    } else {
      log('Login page redirect failed. URL: ' + loginUrl, 'fail');
      results.failed.push('Login page redirect - URL: ' + loginUrl);
    }

    await takeScreenshot(page, '01_login_page');

    // Check login form elements
    const emailInput = await page.$('input[type="email"]');
    const passwordInput = await page.$('input[type="password"]');
    const submitBtn = await page.$('button[type="submit"]');

    if (emailInput && passwordInput && submitBtn) {
      log('Login form elements present', 'pass');
      results.passed.push('Login form elements');
    } else {
      log('Login form elements missing', 'fail');
      results.failed.push('Login form elements missing');
    }

    // ==========================================
    // TEST 2: Login Functionality
    // ==========================================
    console.log('\n--- TEST 2: Login Functionality ---');
    await emailInput.fill(TEST_EMAIL);
    await passwordInput.fill(TEST_PASSWORD);
    await takeScreenshot(page, '02_login_filled');

    await submitBtn.click();
    await page.waitForTimeout(5000);

    const afterLoginUrl = page.url();
    await takeScreenshot(page, '03_after_login');

    if (!afterLoginUrl.includes('/login')) {
      log('Login successful - redirected to: ' + afterLoginUrl, 'pass');
      results.passed.push('Login functionality');
    } else {
      // Check for error message
      const errorEl = await page.$('.text-red-700, .text-red-500');
      if (errorEl) {
        const errorText = await errorEl.textContent();
        log('Login failed with error: ' + errorText, 'fail');
        results.failed.push('Login failed: ' + errorText);
      } else {
        log('Login failed - still on login page', 'fail');
        results.failed.push('Login failed - no redirect');
      }
    }

    // ==========================================
    // TEST 3: Worklist Page
    // ==========================================
    console.log('\n--- TEST 3: Worklist Page ---');
    await page.waitForTimeout(3000);

    // Check if worklist loaded
    const worklistTitle = await page.$('text=Worklist');
    if (worklistTitle) {
      log('Worklist page title visible', 'pass');
      results.passed.push('Worklist page title');
    } else {
      log('Worklist page title not found', 'fail');
      results.failed.push('Worklist page title');
    }

    await takeScreenshot(page, '04_worklist_page');

    // Check for worklist items or empty state
    await page.waitForTimeout(3000);
    const worklistItems = await page.$$('[data-testid="worklist-item"], .worklist-item, tr[class*="worklist"]');
    const emptyState = await page.$('text=No worklist items');
    const loadingSpinner = await page.$('.animate-spin');

    if (worklistItems.length > 0) {
      log('Worklist has ' + worklistItems.length + ' items', 'pass');
      results.passed.push('Worklist data loaded: ' + worklistItems.length + ' items');
    } else if (emptyState) {
      log('Worklist shows empty state', 'warn');
      results.warnings.push('Worklist empty - may need Google Drive sync');
    } else if (loadingSpinner) {
      log('Worklist still loading', 'warn');
      results.warnings.push('Worklist loading - API may be slow');
    } else {
      // Try to find any table rows
      const tableRows = await page.$$('table tbody tr');
      if (tableRows.length > 0) {
        log('Found ' + tableRows.length + ' table rows', 'pass');
        results.passed.push('Worklist table has data');
      } else {
        log('No worklist items found', 'warn');
        results.warnings.push('No worklist items displayed');
      }
    }

    await takeScreenshot(page, '05_worklist_loaded');

    // ==========================================
    // TEST 4: Status Filter Tabs
    // ==========================================
    console.log('\n--- TEST 4: Status Filter Tabs ---');
    const filterTabs = await page.$$('button:has-text("All"), button:has-text("In Progress"), button:has-text("Completed")');
    if (filterTabs.length >= 3) {
      log('Status filter tabs present (' + filterTabs.length + ' tabs)', 'pass');
      results.passed.push('Status filter tabs');
    } else {
      log('Status filter tabs incomplete', 'warn');
      results.warnings.push('Status filter tabs: ' + filterTabs.length);
    }

    // ==========================================
    // TEST 5: Settings Page
    // ==========================================
    console.log('\n--- TEST 5: Settings Page ---');
    const settingsLink = await page.$('a[href*="settings"], button:has-text("Settings")');
    if (settingsLink) {
      await settingsLink.click();
      await page.waitForTimeout(2000);
      await takeScreenshot(page, '06_settings_page');

      const settingsTitle = await page.$('text=Settings');
      if (settingsTitle) {
        log('Settings page loaded', 'pass');
        results.passed.push('Settings page');
      } else {
        log('Settings page title not found', 'warn');
        results.warnings.push('Settings page title');
      }
    } else {
      log('Settings link not found', 'warn');
      results.warnings.push('Settings link not found');
    }

    // ==========================================
    // TEST 6: Navigation Back to Worklist
    // ==========================================
    console.log('\n--- TEST 6: Navigation ---');
    await page.goto(BASE_URL + '#/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    if (page.url().includes('#/') && !page.url().includes('settings')) {
      log('Navigation back to worklist works', 'pass');
      results.passed.push('Navigation');
    } else {
      log('Navigation issue', 'warn');
      results.warnings.push('Navigation back to worklist');
    }

    // ==========================================
    // TEST 7: Console Errors Check
    // ==========================================
    console.log('\n--- TEST 7: Console Errors ---');
    if (consoleErrors.length === 0) {
      log('No console errors', 'pass');
      results.passed.push('No console errors');
    } else {
      log('Console errors found: ' + consoleErrors.length, 'warn');
      results.warnings.push('Console errors: ' + consoleErrors.slice(0, 3).join('; '));
      consoleErrors.slice(0, 5).forEach(err => console.log('   - ' + err.substring(0, 100)));
    }

    // ==========================================
    // TEST 8: Network Errors Check
    // ==========================================
    console.log('\n--- TEST 8: Network Errors ---');
    const criticalNetworkErrors = networkErrors.filter(e =>
      !e.url.includes('favicon') && !e.url.includes('analytics')
    );
    if (criticalNetworkErrors.length === 0) {
      log('No critical network errors', 'pass');
      results.passed.push('No network errors');
    } else {
      log('Network errors found: ' + criticalNetworkErrors.length, 'fail');
      results.failed.push('Network errors');
      criticalNetworkErrors.slice(0, 5).forEach(err =>
        console.log('   - ' + err.url.substring(0, 80) + ' (' + err.error + ')')
      );
    }

  } catch (error) {
    log('Test execution error: ' + error.message, 'fail');
    results.failed.push('Execution error: ' + error.message);
    await takeScreenshot(page, '99_error');
  } finally {
    await browser.close();
  }

  // ==========================================
  // SUMMARY
  // ==========================================
  console.log('\n========================================');
  console.log('  TEST SUMMARY');
  console.log('========================================');
  console.log('✅ Passed:   ' + results.passed.length);
  console.log('❌ Failed:   ' + results.failed.length);
  console.log('⚠️  Warnings: ' + results.warnings.length);
  console.log('');

  if (results.failed.length > 0) {
    console.log('FAILURES:');
    results.failed.forEach(f => console.log('  - ' + f));
  }

  if (results.warnings.length > 0) {
    console.log('\nWARNINGS:');
    results.warnings.forEach(w => console.log('  - ' + w));
  }

  console.log('\nScreenshots saved to: ' + SCREENSHOT_DIR);
  console.log('========================================\n');

  return results;
}

runTests().then(results => {
  process.exit(results.failed.length > 0 ? 1 : 0);
});
