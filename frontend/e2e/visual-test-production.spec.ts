import { test, expect } from '@playwright/test';

test('Visual test: Check parsed fields display in production UI', async ({ page }) => {
  console.log('=== Starting Visual Test ===\n');

  // Navigate to production frontend
  await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html');

  // Wait for page to load
  await page.waitForLoadState('networkidle');
  console.log('✓ Page loaded\n');

  // Navigate to worklist
  await page.click('text=Worklist');
  await page.waitForTimeout(2000);
  console.log('✓ Navigated to Worklist\n');

  // Click on first article
  const firstArticle = page.locator('table tbody tr').first();
  const articleTitle = await firstArticle.locator('td').first().textContent();
  console.log(`Found article: ${articleTitle}\n`);

  await firstArticle.click();
  await page.waitForTimeout(3000);
  console.log('✓ Opened article detail\n');

  // Check for parsed fields in UI
  const fieldChecks = [
    { label: 'Title Prefix', selector: 'text=title_prefix' },
    { label: 'Title Main', selector: 'text=title_main' },
    { label: 'SEO Title', selector: 'text=seo_title' },
    { label: 'Author Name', selector: 'text=author_name' },
    { label: 'Meta Description', selector: 'text=meta_description' },
  ];

  console.log('Checking for parsed fields in UI:\n');
  for (const { label, selector } of fieldChecks) {
    const isVisible = await page.locator(selector).isVisible().catch(() => false);
    console.log(`  ${label}: ${isVisible ? '✅ VISIBLE' : '❌ NOT FOUND'}`);
  }

  // Take screenshot
  await page.screenshot({ path: '/tmp/worklist-visual-test.png', fullPage: true });
  console.log('\n✓ Screenshot saved to /tmp/worklist-visual-test.png');
});
