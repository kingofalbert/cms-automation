import { test, expect } from '@playwright/test';

const FRONTEND_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';

test('Settings page - detailed network analysis', async ({ page }) => {
  const allRequests: Array<{ url: string; resourceType: string }> = [];

  // Capture all network requests
  page.on('request', (request) => {
    allRequests.push({
      url: request.url(),
      resourceType: request.resourceType(),
    });
  });

  console.log('Navigating to Settings page (bypassing cache)...');
  await page.goto(`${FRONTEND_URL}#/settings`, {
    waitUntil: 'networkidle',
    timeout: 30000,
  });

  // Wait for page to settle
  await page.waitForTimeout(3000);

  // Find which Settings JS file was loaded
  console.log('\n=== Settings Page JavaScript Files ===');
  const settingsFiles = allRequests.filter((req) =>
    req.url.includes('SettingsPageModern') || req.url.includes('SettingsPage')
  );
  settingsFiles.forEach((req) => {
    console.log(`${req.resourceType}: ${req.url}`);
  });

  // Check if the new file (CYOOXPnG) is loaded
  const newFileLoaded = settingsFiles.some((req) => req.url.includes('CYOOXPnG'));
  const oldFileLoaded = settingsFiles.some((req) =>
    req.url.includes('BCg74Amh') || req.url.includes('BD9W7Ztl')
  );

  console.log('\n=== File Version Check ===');
  console.log(`New file (CYOOXPnG) loaded: ${newFileLoaded}`);
  console.log(`Old file loaded: ${oldFileLoaded}`);

  // Check for error boundary
  const errorBoundary = await page.locator('text=/應用程序出錯|Application Error/i').count();
  console.log(`\nError boundary visible: ${errorBoundary > 0}`);

  // Check page content
  const hasSettingsContent = await page.locator('text=/系統設置|Provider 配置/i').count();
  console.log(`Settings content visible: ${hasSettingsContent > 0}`);

  // Take screenshot
  await page.screenshot({
    path: 'test-results/settings-detailed-test.png',
    fullPage: true,
  });
});
