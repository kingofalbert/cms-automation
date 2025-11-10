/**
 * Phase 7 Complete Regression Test Suite
 *
 * Tests the entire multi-step workflow and UI consistency:
 * 1. Worklist page with pending items
 * 2. Article parsing flow (parsing → parsing_review)
 * 3. Article SEO confirmation page
 * 4. Proofreading flow (proofreading → proofreading_review)
 * 5. UI/UX consistency across all pages
 */

import { test, expect, Page } from '@playwright/test';

const PRODUCTION_URL = 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html';
const BACKEND_URL = 'https://cms-automation-backend-baau2zqeqq-ue.a.run.app';

// Test configuration
test.use({
  viewport: { width: 1920, height: 1080 },
  screenshot: 'only-on-failure',
  video: 'retain-on-failure',
});

test.describe('Phase 7 Complete Regression Test', () => {
  let page: Page;
  let issuesFound: Array<{category: string, page: string, issue: string, severity: 'critical' | 'major' | 'minor'}> = [];

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();

    // Capture console errors and warnings
    page.on('console', msg => {
      if (msg.type() === 'error') {
        issuesFound.push({
          category: 'JavaScript Error',
          page: page.url(),
          issue: `Console error: ${msg.text()}`,
          severity: 'major'
        });
      }
    });

    // Capture network failures
    page.on('requestfailed', request => {
      issuesFound.push({
        category: 'Network Failure',
        page: page.url(),
        issue: `Failed request: ${request.url()} - ${request.failure()?.errorText}`,
        severity: 'critical'
      });
    });
  });

  test.afterAll(async () => {
    // Generate issue report
    if (issuesFound.length > 0) {
      console.log('\n========== REGRESSION TEST ISSUES FOUND ==========\n');

      const criticalIssues = issuesFound.filter(i => i.severity === 'critical');
      const majorIssues = issuesFound.filter(i => i.severity === 'major');
      const minorIssues = issuesFound.filter(i => i.severity === 'minor');

      console.log(`Total Issues: ${issuesFound.length}`);
      console.log(`  Critical: ${criticalIssues.length}`);
      console.log(`  Major: ${majorIssues.length}`);
      console.log(`  Minor: ${minorIssues.length}\n`);

      // Group by category
      const byCategory = issuesFound.reduce((acc, issue) => {
        if (!acc[issue.category]) acc[issue.category] = [];
        acc[issue.category].push(issue);
        return acc;
      }, {} as Record<string, typeof issuesFound>);

      for (const [category, issues] of Object.entries(byCategory)) {
        console.log(`\n### ${category} (${issues.length} issues)`);
        issues.forEach((issue, idx) => {
          console.log(`${idx + 1}. [${issue.severity.toUpperCase()}] ${issue.page}`);
          console.log(`   ${issue.issue}\n`);
        });
      }

      console.log('\n==================================================\n');
    }

    await page.close();
  });

  test('1. Worklist Page - Initial Load and Display', async () => {
    console.log('\n🧪 Testing Worklist Page...');

    await page.goto(`${PRODUCTION_URL}?nocache=${Date.now()}`, { waitUntil: 'networkidle' });

    // Check page title
    await expect(page).toHaveTitle(/CMS Automation/);

    // Wait for worklist to load
    await page.waitForSelector('text=Worklist', { timeout: 10000 });

    // Verify worklist items are displayed
    const worklistItems = page.locator('[role="row"]').filter({ hasText: /pending|parsing|proofreading/ });
    const itemCount = await worklistItems.count();

    if (itemCount === 0) {
      issuesFound.push({
        category: 'Data Loading',
        page: 'Worklist',
        issue: 'No worklist items found. Expected at least 1 pending item.',
        severity: 'critical'
      });
    } else {
      console.log(`✓ Found ${itemCount} worklist items`);
    }

    // Check for status badges
    const statusBadges = page.locator('[class*="badge"], [class*="Badge"]').filter({ hasText: /pending|parsing|proofreading/i });
    const badgeCount = await statusBadges.count();

    if (badgeCount === 0) {
      issuesFound.push({
        category: 'UI Component',
        page: 'Worklist',
        issue: 'Status badges not displayed correctly',
        severity: 'major'
      });
    }

    // Verify filter controls exist
    const searchInput = page.locator('input[placeholder*="Search" i], input[placeholder*="搜索" i]');
    if (await searchInput.count() === 0) {
      issuesFound.push({
        category: 'UI Component',
        page: 'Worklist',
        issue: 'Search input not found',
        severity: 'minor'
      });
    }

    // Check for action buttons
    const actionButtons = page.locator('button').filter({ hasText: /Review|審核|Parse|解析/i });
    const buttonCount = await actionButtons.count();
    console.log(`✓ Found ${buttonCount} action buttons`);

    // Screenshot for manual review
    await page.screenshot({ path: 'e2e/screenshots/worklist-page.png', fullPage: true });
  });

  test('2. Worklist - Status-specific Action Buttons', async () => {
    console.log('\n🧪 Testing status-specific action buttons...');

    await page.goto(`${PRODUCTION_URL}?nocache=${Date.now()}`, { waitUntil: 'networkidle' });
    await page.waitForSelector('text=Worklist', { timeout: 10000 });

    // Test pending status - should have NO action button
    const pendingRows = page.locator('[role="row"]').filter({ has: page.locator('text=/pending/i') });
    const pendingCount = await pendingRows.count();

    if (pendingCount > 0) {
      const firstPendingRow = pendingRows.first();
      const actionButton = firstPendingRow.locator('button').filter({ hasText: /Review|審核/i });
      const hasButton = await actionButton.count() > 0;

      if (hasButton) {
        issuesFound.push({
          category: 'Business Logic',
          page: 'Worklist',
          issue: 'Pending items should NOT have action buttons (they are being processed automatically)',
          severity: 'major'
        });
      } else {
        console.log('✓ Pending items correctly have no action button');
      }
    }

    // Test parsing_review status - should have "Review Parsing" button
    const parsingReviewRows = page.locator('[role="row"]').filter({ has: page.locator('text=/parsing.*review/i') });
    const parsingReviewCount = await parsingReviewRows.count();

    if (parsingReviewCount > 0) {
      const firstParsingReviewRow = parsingReviewRows.first();
      const reviewButton = firstParsingReviewRow.locator('button').filter({ hasText: /Review.*Parsing|審核.*解析/i });

      if (await reviewButton.count() === 0) {
        issuesFound.push({
          category: 'Business Logic',
          page: 'Worklist',
          issue: 'parsing_review items should have "Review Parsing" button',
          severity: 'critical'
        });
      } else {
        console.log('✓ parsing_review items have correct action button');
      }
    }

    // Test proofreading_review status - should have "Review Proofreading" button
    const proofreadingReviewRows = page.locator('[role="row"]').filter({ has: page.locator('text=/proofreading.*review/i') });
    const proofreadingReviewCount = await proofreadingReviewRows.count();

    if (proofreadingReviewCount > 0) {
      const firstProofreadingReviewRow = proofreadingReviewRows.first();
      const reviewButton = firstProofreadingReviewRow.locator('button').filter({ hasText: /Review.*Proofreading|審核.*校對/i });

      if (await reviewButton.count() === 0) {
        issuesFound.push({
          category: 'Business Logic',
          page: 'Worklist',
          issue: 'proofreading_review items should have "Review Proofreading" button',
          severity: 'critical'
        });
      } else {
        console.log('✓ proofreading_review items have correct action button');
      }
    }
  });

  test('3. Article Parsing Page - Navigation and Content', async () => {
    console.log('\n🧪 Testing Article Parsing Page navigation...');

    // First check if we have any parsing_review items via API
    const response = await page.request.get(`${BACKEND_URL}/v1/worklist`);
    const data = await response.json();

    const parsingReviewItem = data.items.find((item: any) => item.status === 'parsing_review');

    if (!parsingReviewItem) {
      console.log('⚠ No parsing_review items found, skipping parsing page test');
      issuesFound.push({
        category: 'Test Limitation',
        page: 'Article Parsing',
        issue: 'Cannot test parsing page - no parsing_review items available',
        severity: 'minor'
      });
      return;
    }

    // Navigate to parsing page
    const parsingUrl = `${PRODUCTION_URL}#/articles/${parsingReviewItem.article_id}/parsing`;
    await page.goto(parsingUrl, { waitUntil: 'networkidle' });

    // Check for title optimization section
    const titleSection = page.locator('text=/Title.*Optimization|標題.*優化/i');
    if (await titleSection.count() === 0) {
      issuesFound.push({
        category: 'UI Component',
        page: 'Article Parsing',
        issue: 'Title optimization section not found',
        severity: 'critical'
      });
    } else {
      console.log('✓ Title optimization section found');
    }

    // Check for SEO section
    const seoSection = page.locator('text=/SEO.*Keywords|SEO.*關鍵字/i');
    if (await seoSection.count() === 0) {
      issuesFound.push({
        category: 'UI Component',
        page: 'Article Parsing',
        issue: 'SEO keywords section not found',
        severity: 'critical'
      });
    } else {
      console.log('✓ SEO section found');
    }

    // Check for image gallery section
    const imageSection = page.locator('text=/Image.*Gallery|圖片.*畫廊/i');
    if (await imageSection.count() === 0) {
      issuesFound.push({
        category: 'UI Component',
        page: 'Article Parsing',
        issue: 'Image gallery section not found',
        severity: 'major'
      });
    } else {
      console.log('✓ Image gallery section found');
    }

    // Check for action buttons
    const confirmButton = page.locator('button').filter({ hasText: /Confirm|確認|Next|下一步/i });
    if (await confirmButton.count() === 0) {
      issuesFound.push({
        category: 'UI Component',
        page: 'Article Parsing',
        issue: 'Confirm/Next button not found',
        severity: 'critical'
      });
    }

    await page.screenshot({ path: 'e2e/screenshots/article-parsing-page.png', fullPage: true });
  });

  test('4. Proofreading Review Page - Navigation and Content', async () => {
    console.log('\n🧪 Testing Proofreading Review Page...');

    // Get a proofreading_review item
    const response = await page.request.get(`${BACKEND_URL}/v1/worklist`);
    const data = await response.json();

    const proofreadingReviewItem = data.items.find((item: any) =>
      item.status === 'proofreading_review' || item.status === 'under_review'
    );

    if (!proofreadingReviewItem) {
      console.log('⚠ No proofreading_review items found, skipping proofreading page test');
      return;
    }

    // Navigate to proofreading review page
    const reviewUrl = `${PRODUCTION_URL}#/worklist/${proofreadingReviewItem.id}/review`;
    await page.goto(reviewUrl, { waitUntil: 'networkidle' });

    // Check for article title
    const articleTitle = page.locator('h1, h2').filter({ hasText: proofreadingReviewItem.title });
    if (await articleTitle.count() === 0) {
      issuesFound.push({
        category: 'UI Component',
        page: 'Proofreading Review',
        issue: 'Article title not displayed',
        severity: 'major'
      });
    } else {
      console.log('✓ Article title displayed');
    }

    // Check for issue counters
    const issueCounters = page.locator('text=/Critical|Warning|Info|致命|警告/i');
    if (await issueCounters.count() === 0) {
      issuesFound.push({
        category: 'UI Component',
        page: 'Proofreading Review',
        issue: 'Issue severity counters not found',
        severity: 'major'
      });
    } else {
      console.log('✓ Issue counters found');
    }

    // Check for action buttons (Accept/Reject/Modify)
    const actionButtons = page.locator('button').filter({ hasText: /Accept|Reject|Modify|接受|拒絕|修改/i });
    const buttonCount = await actionButtons.count();

    if (buttonCount < 2) {
      issuesFound.push({
        category: 'UI Component',
        page: 'Proofreading Review',
        issue: `Expected at least 2 action buttons (Accept/Reject), found ${buttonCount}`,
        severity: 'major'
      });
    } else {
      console.log(`✓ Found ${buttonCount} action buttons`);
    }

    await page.screenshot({ path: 'e2e/screenshots/proofreading-review-page.png', fullPage: true });
  });

  test('5. UI Consistency - Navigation and Layout', async () => {
    console.log('\n🧪 Testing UI consistency across pages...');

    await page.goto(`${PRODUCTION_URL}?nocache=${Date.now()}`, { waitUntil: 'networkidle' });

    // Check for consistent header/navigation
    const header = page.locator('header, nav, [role="navigation"]');
    if (await header.count() === 0) {
      issuesFound.push({
        category: 'UI Consistency',
        page: 'All Pages',
        issue: 'No header/navigation found',
        severity: 'major'
      });
    }

    // Check for consistent logo/branding
    const logo = page.locator('text=/CMS.*Automation|CMS.*系統/i').first();
    if (await logo.count() === 0) {
      issuesFound.push({
        category: 'UI Consistency',
        page: 'All Pages',
        issue: 'Logo/branding not found',
        severity: 'minor'
      });
    }

    // Check for consistent settings link
    const settingsLink = page.locator('a, button').filter({ hasText: /Settings|設置/i });
    if (await settingsLink.count() === 0) {
      issuesFound.push({
        category: 'UI Consistency',
        page: 'All Pages',
        issue: 'Settings link not found',
        severity: 'minor'
      });
    }

    // Check language selector
    const languageSelector = page.locator('select, button').filter({ hasText: /English|中文|Language/i });
    if (await languageSelector.count() === 0) {
      issuesFound.push({
        category: 'UI Consistency',
        page: 'All Pages',
        issue: 'Language selector not found',
        severity: 'minor'
      });
    } else {
      console.log('✓ Language selector found');
    }
  });

  test('6. Performance - Page Load Times', async () => {
    console.log('\n🧪 Testing page load performance...');

    const pages = [
      { name: 'Worklist', url: PRODUCTION_URL },
    ];

    for (const pageInfo of pages) {
      const startTime = Date.now();
      await page.goto(`${pageInfo.url}?nocache=${Date.now()}`, { waitUntil: 'networkidle' });
      const loadTime = Date.now() - startTime;

      console.log(`${pageInfo.name} load time: ${loadTime}ms`);

      if (loadTime > 5000) {
        issuesFound.push({
          category: 'Performance',
          page: pageInfo.name,
          issue: `Page load time ${loadTime}ms exceeds 5 second threshold`,
          severity: 'major'
        });
      }
    }
  });

  test('7. Accessibility - Basic Checks', async () => {
    console.log('\n🧪 Testing basic accessibility...');

    await page.goto(`${PRODUCTION_URL}?nocache=${Date.now()}`, { waitUntil: 'networkidle' });

    // Check for semantic HTML
    const mainElement = page.locator('main, [role="main"]');
    if (await mainElement.count() === 0) {
      issuesFound.push({
        category: 'Accessibility',
        page: 'Worklist',
        issue: 'No <main> or role="main" element found',
        severity: 'minor'
      });
    }

    // Check for button accessibility
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();

    for (let i = 0; i < Math.min(buttonCount, 10); i++) {
      const button = buttons.nth(i);
      const hasText = await button.textContent();
      const hasAriaLabel = await button.getAttribute('aria-label');

      if (!hasText?.trim() && !hasAriaLabel) {
        issuesFound.push({
          category: 'Accessibility',
          page: 'Worklist',
          issue: `Button ${i + 1} has no text or aria-label`,
          severity: 'minor'
        });
      }
    }

    // Check for image alt text
    const images = page.locator('img');
    const imageCount = await images.count();

    for (let i = 0; i < Math.min(imageCount, 5); i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute('alt');

      if (!alt) {
        issuesFound.push({
          category: 'Accessibility',
          page: 'Current Page',
          issue: `Image ${i + 1} missing alt text`,
          severity: 'minor'
        });
      }
    }
  });
});
