import { test } from '@playwright/test';

/**
 * Advanced debugging - Evaluate JavaScript in the page context
 */

const PROD_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323';

test('Debug Settings - JavaScript evaluation', async ({ page }) => {
  // Enable console message capture
  page.on('console', msg => {
    console.log(`[${msg.type().toUpperCase()}] ${msg.text()}`);
  });

  // Capture unhandled exceptions
  page.on('pageerror', error => {
    console.log(`\n🔴 PAGE ERROR: ${error.message}`);
    console.log(`Stack: ${error.stack}\n`);
  });

  console.log('Navigating to Settings page...');
  await page.goto(`${PROD_URL}/index.html#/settings`, {
    waitUntil: 'networkidle',
  });

  // Wait for everything to settle
  await page.waitForTimeout(3000);

  // Check if error boundary is visible
  const hasErrorBoundary = await page.locator('text=應用程序出錯').isVisible().catch(() => false);

  if (hasErrorBoundary) {
    console.log('\n❌ Error boundary detected\n');

    // Try to find React's error info in the DOM
    const reactErrorInfo = await page.evaluate(() => {
      // Check if there's any error info in window
      const win: any = window;

      // Try to find React DevTools error info
      const errors: string[] = [];

      // Check for any global error state
      if (win.__REACT_ERROR__) {
        errors.push(`React Error: ${JSON.stringify(win.__REACT_ERROR__)}`);
      }

      // Check console for errors
      if (win.console && win.console.error) {
        errors.push('Console error method exists');
      }

      // Check if React Query has errors
      if (win.__REACT_QUERY_STATE__) {
        errors.push(`React Query State: ${JSON.stringify(win.__REACT_QUERY_STATE__)}`);
      }

      // Try to get error from error boundary component
      const errorTexts: string[] = [];
      document.querySelectorAll('*').forEach(el => {
        const text = el.textContent || '';
        if (text.includes('Error') || text.includes('error') || text.includes('錯')) {
          if (text.length < 200) {
            errorTexts.push(text.trim());
          }
        }
      });

      return {
        globalErrors: errors,
        errorTexts: [...new Set(errorTexts)], // deduplicate
        pathname: win.location.pathname,
        hash: win.location.hash,
        href: win.location.href,
      };
    });

    console.log('\n=== React Error Info ===');
    console.log(JSON.stringify(reactErrorInfo, null, 2));

    // Try to access localStorage/sessionStorage
    const storageInfo = await page.evaluate(() => {
      try {
        return {
          localStorage: localStorage.length > 0 ? 'Has data' : 'Empty',
          localStorageKeys: Object.keys(localStorage),
          sessionStorage: sessionStorage.length > 0 ? 'Has data' : 'Empty',
        };
      } catch (e: any) {
        return { error: e.message };
      }
    });

    console.log('\n=== Storage Info ===');
    console.log(JSON.stringify(storageInfo, null, 2));

    // Check network state
    const networkState = await page.evaluate(() => {
      return {
        online: navigator.onLine,
        userAgent: navigator.userAgent,
      };
    });

    console.log('\n=== Network State ===');
    console.log(JSON.stringify(networkState, null, 2));
  } else {
    console.log('\n✅ No error boundary visible\n');
  }

  // Keep open for inspection
  await page.waitForTimeout(2000);
});
