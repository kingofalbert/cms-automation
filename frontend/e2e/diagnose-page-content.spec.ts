import { test } from '@playwright/test';

test('diagnose page content after fix', async ({ page }) => {
  // Navigate to worklist
  await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html#/worklist', {
    waitUntil: 'networkidle',
  });

  // Clear storage and reload
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.reload({ waitUntil: 'networkidle' });

  console.log('📍 Navigating to worklist...');
  await page.waitForTimeout(2000);

  // Click review button
  const reviewButton = page.getByRole('button', { name: /审核|review/i }).first();
  await reviewButton.click();

  console.log('🖱️ Clicked review button, waiting for page to load...');
  await page.waitForTimeout(5000);

  // Get page HTML
  const bodyHTML = await page.locator('body').innerHTML();
  console.log('\n=== PAGE BODY HTML (first 1000 chars) ===');
  console.log(bodyHTML.substring(0, 1000));

  // Check for specific elements
  const hasErrorBoundary = await page.locator('text=/应用程序出错|error/i').count();
  const hasLoadingSpinner = await page.locator('[class*="loading"], [class*="spinner"]').count();
  const hasProofreadingContent = await page.locator('[class*="Proofreading"], [class*="proofreading"]').count();
  const hasIssueText = await page.getByText(/issue|问题/i).count();

  console.log('\n=== ELEMENT COUNTS ===');
  console.log(`Error boundaries: ${hasErrorBoundary}`);
  console.log(`Loading spinners: ${hasLoadingSpinner}`);
  console.log(`Proofreading elements: ${hasProofreadingContent}`);
  console.log(`Issue-related text: ${hasIssueText}`);

  // Get all visible text
  const pageText = await page.locator('body').innerText();
  console.log('\n=== VISIBLE TEXT (first 500 chars) ===');
  console.log(pageText.substring(0, 500));

  // Take screenshot
  await page.screenshot({ path: '/tmp/diagnose-page-content.png', fullPage: true });
  console.log('\nScreenshot saved to /tmp/diagnose-page-content.png');
});
