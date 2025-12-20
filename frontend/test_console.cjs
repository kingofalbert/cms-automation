const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  const consoleMessages = [];
  const networkErrors = [];

  // Capture console messages
  page.on('console', msg => {
    consoleMessages.push({ type: msg.type(), text: msg.text() });
  });

  // Capture network errors
  page.on('requestfailed', request => {
    networkErrors.push({
      url: request.url(),
      failure: request.failure()?.errorText
    });
  });

  try {
    console.log('1. Navigating to production URL...');
    await page.goto('https://storage.googleapis.com/cms-automation-frontend-2025/index.html', {
      waitUntil: 'domcontentloaded'
    });

    // Wait for a longer time to capture all errors
    console.log('2. Waiting 10 seconds for page to load...');
    await page.waitForTimeout(10000);

    console.log('\n=== CONSOLE MESSAGES ===');
    consoleMessages.forEach((msg, i) => {
      if (msg.type === 'error' || msg.type === 'warning') {
        console.log('[' + msg.type.toUpperCase() + '] ' + msg.text);
      }
    });

    console.log('\n=== NETWORK ERRORS ===');
    if (networkErrors.length === 0) {
      console.log('No network errors');
    } else {
      networkErrors.forEach(err => {
        console.log('Failed: ' + err.url + ' - ' + err.failure);
      });
    }

    // Check current state
    console.log('\n=== PAGE STATE ===');
    console.log('URL:', page.url());

    // Check if login form is visible
    const loginForm = await page.$('input[type="email"]');
    const loadingSpinner = await page.$('.animate-spin');

    console.log('Login form visible:', loginForm ? 'YES' : 'NO');
    console.log('Loading spinner visible:', loadingSpinner ? 'YES' : 'NO');

    // Take screenshot
    await page.screenshot({ path: '/tmp/debug_state.png' });

    // Check for specific errors
    console.log('\n=== SUPABASE/AUTH ERRORS ===');
    const supabaseErrors = consoleMessages.filter(m =>
      m.text.toLowerCase().includes('supabase') ||
      m.text.toLowerCase().includes('auth') ||
      m.text.toLowerCase().includes('error') ||
      m.text.toLowerCase().includes('failed')
    );
    supabaseErrors.forEach(err => {
      console.log('[' + err.type + '] ' + err.text);
    });

    // Print ALL console messages
    console.log('\n=== ALL CONSOLE MESSAGES ===');
    consoleMessages.forEach(msg => {
      console.log('[' + msg.type + '] ' + msg.text.substring(0, 200));
    });

  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await browser.close();
  }
})();
