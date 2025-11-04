import { test } from '@playwright/test';
import type { Request, Response, ConsoleMessage } from '@playwright/test';

type DebugWindow = typeof window & {
  __API_URL__?: string;
  VITE_API_URL?: string;
};

test('Debug settings page with screenshots', async ({ page, context }) => {
  // Clear all cookies, cache, and storage first
  await context.clearCookies();

  // Navigate to the app with hard reload
  await page.goto('https://storage.googleapis.com/cms-automation-frontend-2025/index.html', {
    waitUntil: 'networkidle',
  });

  // Force hard refresh to bypass all caching
  await page.reload({ waitUntil: 'networkidle' });

  // Wait for page to load
  await page.waitForLoadState('networkidle');

  // Take screenshot of home page
  await page.screenshot({ path: 'debug-home.png', fullPage: true });
  console.log('📸 Home page screenshot saved');

  // Listen to network requests
  page.on('request', (request: Request) => {
    if (request.url().includes('settings')) {
      console.log('📤 REQUEST:', request.method(), request.url());
      console.log('   Headers:', JSON.stringify(request.headers(), null, 2));
    }
  });

  page.on('response', async (response: Response) => {
    if (response.url().includes('settings')) {
      console.log('📥 RESPONSE:', response.status(), response.url());
      console.log('   Headers:', JSON.stringify(response.headers(), null, 2));
      try {
        const body = await response.text();
        console.log('   Body:', body);
      } catch (e) {
        console.log('   Body: (could not read)');
      }
    }
  });

  // Capture console logs
  page.on('console', (msg: ConsoleMessage) => {
    console.log(`🖥️  CONSOLE [${msg.type()}]:`, msg.text());
  });

  // Click settings link
  console.log('🔍 Looking for settings link...');
  const settingsLink = page.locator('a[href*="settings"], a:has-text("設置")').first();
  await settingsLink.waitFor({ timeout: 10000 });
  console.log('✅ Found settings link');

  await settingsLink.click();
  console.log('👆 Clicked settings link');

  // Wait a bit for the page to load
  await page.waitForTimeout(3000);

  // Take screenshot of settings page
  await page.screenshot({ path: 'debug-settings.png', fullPage: true });
  console.log('📸 Settings page screenshot saved');

  // Check what's on the page
  const pageText = await page.locator('body').textContent();
  console.log('📄 Page content:', pageText);

  // Check for error
  const has403 = pageText?.includes('403');
  const hasError = pageText?.includes('Request failed');

  console.log('❌ Has 403?', has403);
  console.log('❌ Has Error?', hasError);

  // Get the API URL from window
  const apiUrl = await page.evaluate<string>(() => {
    const debugWindow = window as DebugWindow;
    return debugWindow.__API_URL__ ?? debugWindow.VITE_API_URL ?? 'NOT FOUND';
  });
  console.log('🔗 Frontend API URL:', apiUrl);
});
