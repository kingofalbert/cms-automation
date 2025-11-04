import { test, expect } from '@playwright/test';

test.describe('Production app.html test', () => {
  test('should load app.html and navigate to settings', async ({ page }) => {
    const errors: string[] = [];
    const networkRequests: { url: string; status: number }[] = [];
    
    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // Capture network requests
    page.on('response', response => {
      networkRequests.push({
        url: response.url(),
        status: response.status()
      });
    });
    
    console.log('Loading app.html...');
    await page.goto('https://storage.googleapis.com/cms-automation-frontend-2025/app.html', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    
    // Wait for React to render
    await page.waitForTimeout(2000);
    
    // Take screenshot
    await page.screenshot({ path: 'test-results/production-app-loaded.png', fullPage: true });
    
    // Check if root div has content
    const rootContent = await page.locator('#root').innerHTML();
    console.log('Root content length:', rootContent.length);
    expect(rootContent.length).toBeGreaterThan(100);
    
    // Try to find and click Settings link
    console.log('Looking for Settings link...');
    const settingsLink = page.locator('a[href*="settings"], nav >> text=/Settings|设置/i').first();
    
    if (await settingsLink.count() > 0) {
      console.log('Found Settings link, clicking...');
      await settingsLink.click();
      await page.waitForTimeout(3000);
      
      // Take screenshot of settings page
      await page.screenshot({ path: 'test-results/production-settings.png', fullPage: true });
      
      // Check for API calls
      const apiCalls = networkRequests.filter(r => 
        r.url.includes('cms-automation-backend') || 
        r.url.includes('/v1/') ||
        r.url.includes('/api/v1/')
      );
      
      console.log('\n=== API Calls ===');
      apiCalls.forEach(call => {
        console.log(`${call.status} ${call.url}`);
      });
      
      // Check if we got correct API calls (should be /v1/ not /api/v1/)
      const correctApiCalls = apiCalls.filter(c => c.url.includes('/v1/settings'));
      const wrongApiCalls = apiCalls.filter(c => c.url.includes('/api/v1/'));
      
      console.log('\nCorrect API calls (using /v1/):', correctApiCalls.length);
      console.log('Wrong API calls (using /api/v1/):', wrongApiCalls.length);
      
      expect(wrongApiCalls.length).toBe(0);
      expect(correctApiCalls.length).toBeGreaterThan(0);
    } else {
      console.log('Settings link not found, checking page content...');
      const bodyText = await page.textContent('body');
      console.log('Body text preview:', bodyText?.substring(0, 200));
    }
    
    // Report errors
    if (errors.length > 0) {
      console.log('\n=== Console Errors ===');
      errors.forEach(err => console.log(err));
    }
    
    console.log('\nTest completed');
  });
});
