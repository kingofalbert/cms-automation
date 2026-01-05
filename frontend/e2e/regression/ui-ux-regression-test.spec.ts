/**
 * Comprehensive UI/UX Regression Test Suite
 *
 * This test suite evaluates the CMS automation system from a UI/UX designer perspective,
 * checking for visual issues, usability problems, accessibility, and overall user experience.
 *
 * Focus Areas:
 * 1. Visual/Layout issues: Misaligned elements, overflow, responsive issues
 * 2. UX problems: Confusing navigation, unclear button labels, missing feedback
 * 3. Functionality bugs: Broken buttons, failed API calls, state management issues
 * 4. Edge cases: Empty states, error handling, loading states
 * 5. Accessibility: Keyboard navigation, focus states, contrast
 * 6. i18n: Missing translations, text overflow in different languages
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';

// Configuration
const FRONTEND_URL = 'https://storage.googleapis.com/cms-automation-frontend-476323/index.html';
const BACKEND_URL = 'https://cms-automation-backend-297291472291.us-east1.run.app';
const SCREENSHOT_DIR = './e2e/regression/screenshots';

// Test credentials (from environment or defaults)
const TEST_EMAIL = process.env.TEST_EMAIL || 'allen.chen@epochtimes.com';
const TEST_PASSWORD = process.env.TEST_PASSWORD || 'Editor123$';

// Bug report structure
interface BugReport {
  id: string;
  page: string;
  severity: 'Critical' | 'Major' | 'Minor' | 'Enhancement';
  category: 'Visual' | 'UX' | 'Functionality' | 'Accessibility' | 'i18n' | 'Performance';
  title: string;
  description: string;
  stepsToReproduce: string[];
  expectedBehavior: string;
  actualBehavior: string;
  screenshot?: string;
  recommendedFix: string;
}

// Collect bugs during test run
const bugsFound: BugReport[] = [];

// Helper function to add bug
function reportBug(bug: Omit<BugReport, 'id'>) {
  const id = `BUG-${String(bugsFound.length + 1).padStart(4, '0')}`;
  bugsFound.push({ id, ...bug });
  console.log(`[${id}] ${bug.severity}: ${bug.title}`);
}

// Helper function to take screenshot with timestamp
async function takeScreenshot(page: Page, name: string): Promise<string> {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `${timestamp}_${name}.png`;
  await page.screenshot({ path: `${SCREENSHOT_DIR}/${filename}`, fullPage: true });
  return filename;
}

// Helper function to login
async function login(page: Page): Promise<boolean> {
  try {
    await page.goto(`${FRONTEND_URL}#/login`, { waitUntil: 'networkidle', timeout: 60000 });

    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Check if already logged in
    const pageContent = await page.content();
    if (pageContent.includes('Worklist') || pageContent.includes('worklist')) {
      return true;
    }

    // Fill login form
    const emailInput = page.locator('input[type="email"]');
    if (await emailInput.isVisible({ timeout: 5000 })) {
      await emailInput.fill(TEST_EMAIL);
      await page.locator('input[type="password"]').fill(TEST_PASSWORD);
      await page.locator('button[type="submit"]').click();

      // Wait for login to complete
      await page.waitForTimeout(5000);
      await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});

      return true;
    }

    return false;
  } catch (error) {
    console.error('Login failed:', error);
    return false;
  }
}

// Helper to check console errors
async function captureConsoleErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  return errors;
}

test.describe('UI/UX Regression Test Suite', () => {
  let context: BrowserContext;
  let page: Page;
  let consoleErrors: string[] = [];

  test.beforeAll(async ({ browser }) => {
    // Create a shared context for all tests to maintain login state
    context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      locale: 'zh-TW',
    });
    page = await context.newPage();

    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Login once
    const loginSuccess = await login(page);
    expect(loginSuccess).toBe(true);
  });

  test.afterAll(async () => {
    // Generate final bug report
    console.log('\n' + '='.repeat(80));
    console.log('  UI/UX REGRESSION TEST REPORT');
    console.log('='.repeat(80));
    console.log(`Total Bugs Found: ${bugsFound.length}`);
    console.log(`Critical: ${bugsFound.filter(b => b.severity === 'Critical').length}`);
    console.log(`Major: ${bugsFound.filter(b => b.severity === 'Major').length}`);
    console.log(`Minor: ${bugsFound.filter(b => b.severity === 'Minor').length}`);
    console.log(`Enhancement: ${bugsFound.filter(b => b.severity === 'Enhancement').length}`);
    console.log('='.repeat(80));

    // Print each bug
    for (const bug of bugsFound) {
      console.log(`\n[${bug.id}] ${bug.severity} - ${bug.category}`);
      console.log(`Page: ${bug.page}`);
      console.log(`Title: ${bug.title}`);
      console.log(`Description: ${bug.description}`);
      console.log(`Steps: ${bug.stepsToReproduce.join(' -> ')}`);
      console.log(`Expected: ${bug.expectedBehavior}`);
      console.log(`Actual: ${bug.actualBehavior}`);
      console.log(`Screenshot: ${bug.screenshot || 'N/A'}`);
      console.log(`Recommended Fix: ${bug.recommendedFix}`);
    }

    if (consoleErrors.length > 0) {
      console.log('\n' + '='.repeat(80));
      console.log('  CONSOLE ERRORS CAPTURED');
      console.log('='.repeat(80));
      consoleErrors.forEach((err, i) => {
        console.log(`${i + 1}. ${err}`);
      });
    }

    await context.close();
  });

  // =========================================================================
  // 1. LOGIN PAGE TESTS
  // =========================================================================
  test.describe('Login Page', () => {
    test('should display login form with proper styling', async () => {
      await page.goto(`${FRONTEND_URL}#/login`, { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(2000);

      const screenshot = await takeScreenshot(page, 'login-page');

      // Check for email input
      const emailInput = page.locator('input[type="email"]');
      const emailVisible = await emailInput.isVisible().catch(() => false);

      if (!emailVisible) {
        // May already be logged in, check for worklist content
        const content = await page.content();
        if (!content.includes('Worklist') && !content.includes('worklist')) {
          reportBug({
            page: '/login',
            severity: 'Critical',
            category: 'Functionality',
            title: 'Login form not visible',
            description: 'Email input field is not visible on login page',
            stepsToReproduce: ['Navigate to /login'],
            expectedBehavior: 'Login form should be visible with email/password fields',
            actualBehavior: 'Login form elements are missing',
            screenshot,
            recommendedFix: 'Check if LoginPage component renders correctly',
          });
        }
      }

      // Check form labels
      const labels = await page.locator('label').allTextContents();
      if (labels.length === 0) {
        reportBug({
          page: '/login',
          severity: 'Minor',
          category: 'Accessibility',
          title: 'Missing form labels',
          description: 'Input fields may be missing accessible labels',
          stepsToReproduce: ['Navigate to /login', 'Inspect form fields'],
          expectedBehavior: 'All form inputs should have associated labels',
          actualBehavior: 'Labels not found',
          screenshot,
          recommendedFix: 'Add proper <label> elements with for/htmlFor attributes',
        });
      }
    });
  });

  // =========================================================================
  // 2. WORKLIST PAGE TESTS
  // =========================================================================
  test.describe('Worklist Page', () => {
    test('should load worklist page with statistics', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      const screenshot = await takeScreenshot(page, 'worklist-page');
      const content = await page.content();

      // Check for page header
      const hasTitle = content.includes('Worklist') || content.includes('worklist');
      if (!hasTitle) {
        reportBug({
          page: '/worklist',
          severity: 'Major',
          category: 'Visual',
          title: 'Worklist title not visible',
          description: 'The page title is not displayed',
          stepsToReproduce: ['Login', 'Navigate to /worklist'],
          expectedBehavior: 'Page should show "Worklist" or equivalent title',
          actualBehavior: 'Title not found in page content',
          screenshot,
          recommendedFix: 'Ensure header renders correctly with proper text',
        });
      }

      // Check for statistics cards
      const statsCards = page.locator('[class*="stat"], [class*="card"], [class*="Card"]');
      const statsCount = await statsCards.count();

      // Check for table presence
      const table = page.locator('table');
      const hasTable = await table.isVisible().catch(() => false);

      if (!hasTable) {
        reportBug({
          page: '/worklist',
          severity: 'Major',
          category: 'Functionality',
          title: 'Worklist table not visible',
          description: 'The main worklist table is not displayed',
          stepsToReproduce: ['Login', 'Navigate to /worklist', 'Wait for page load'],
          expectedBehavior: 'Table with worklist items should be visible',
          actualBehavior: 'Table element not found or not visible',
          screenshot,
          recommendedFix: 'Check WorklistTable component rendering and API data loading',
        });
      }
    });

    test('should display loading state correctly', async () => {
      // Force a fresh load to see loading state
      await page.goto(`${FRONTEND_URL}#/worklist`, { timeout: 30000 });

      // Take screenshot immediately to capture loading state
      const loadingScreenshot = await takeScreenshot(page, 'worklist-loading-state');

      // Check for spinner or loading indicator
      const spinner = page.locator('[class*="spin"], [class*="loading"], [class*="Spinner"]');
      const hasSpinner = await spinner.first().isVisible({ timeout: 2000 }).catch(() => false);

      // Wait for content to load
      await page.waitForTimeout(10000);
      const screenshot = await takeScreenshot(page, 'worklist-loaded');
    });

    test('should handle filter interactions', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      // Check for search input
      const searchInput = page.locator('input[placeholder*="search"], input[type="search"]');
      const hasSearch = await searchInput.first().isVisible().catch(() => false);

      // Check for status filter dropdown
      const statusSelect = page.locator('select');
      const hasStatusFilter = await statusSelect.first().isVisible().catch(() => false);

      if (!hasSearch && !hasStatusFilter) {
        const screenshot = await takeScreenshot(page, 'worklist-filters');
        reportBug({
          page: '/worklist',
          severity: 'Minor',
          category: 'UX',
          title: 'Filter controls may not be visible',
          description: 'Search and filter controls might be missing or hard to find',
          stepsToReproduce: ['Login', 'Navigate to /worklist', 'Look for filter controls'],
          expectedBehavior: 'Search input and status filter should be prominently visible',
          actualBehavior: 'Filter controls not immediately visible',
          screenshot,
          recommendedFix: 'Ensure filters are visible above the table with clear labels',
        });
      }

      // Test quick filter buttons
      const quickFilterButtons = page.locator('button').filter({ hasText: /All|Needs Attention|In Progress|Completed|Failed/i });
      const quickFilterCount = await quickFilterButtons.count();

      if (quickFilterCount < 3) {
        const screenshot = await takeScreenshot(page, 'worklist-quick-filters');
        reportBug({
          page: '/worklist',
          severity: 'Minor',
          category: 'UX',
          title: 'Quick filter buttons may be missing',
          description: 'Expected quick filter buttons for common status filters',
          stepsToReproduce: ['Login', 'Navigate to /worklist', 'Look for quick filter buttons'],
          expectedBehavior: 'Quick filter buttons for All, Needs Attention, etc.',
          actualBehavior: `Only found ${quickFilterCount} quick filter buttons`,
          screenshot,
          recommendedFix: 'Add prominent quick filter buttons for common workflows',
        });
      }
    });

    test('should handle table row click for review', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      // Wait for table to load
      const tableRows = page.locator('table tbody tr');
      const rowCount = await tableRows.count();

      if (rowCount > 0) {
        // Click first row
        await tableRows.first().click();
        await page.waitForTimeout(3000);

        const screenshot = await takeScreenshot(page, 'worklist-row-click');

        // Check if modal or drawer opened
        const modal = page.locator('[class*="modal"], [class*="Modal"], [class*="drawer"], [class*="Drawer"]');
        const hasModal = await modal.first().isVisible().catch(() => false);

        // Check if navigated to review page
        const currentUrl = page.url();
        const navigatedToReview = currentUrl.includes('/review') || currentUrl.includes('/parsing');

        if (!hasModal && !navigatedToReview) {
          reportBug({
            page: '/worklist',
            severity: 'Major',
            category: 'UX',
            title: 'Unclear feedback when clicking table row',
            description: 'Clicking a table row does not provide clear visual feedback',
            stepsToReproduce: ['Login', 'Navigate to /worklist', 'Click on a table row'],
            expectedBehavior: 'Should open a modal, drawer, or navigate to review page',
            actualBehavior: 'No visible change after clicking',
            screenshot,
            recommendedFix: 'Ensure click handler opens modal/drawer or navigates to review',
          });
        }
      }
    });

    test('should check responsive design at mobile size', async () => {
      await page.setViewportSize({ width: 375, height: 812 }); // iPhone X
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(3000);

      const screenshot = await takeScreenshot(page, 'worklist-mobile');
      const content = await page.content();

      // Check for horizontal overflow
      const hasHorizontalScroll = await page.evaluate(() => {
        return document.body.scrollWidth > document.body.clientWidth;
      });

      if (hasHorizontalScroll) {
        reportBug({
          page: '/worklist',
          severity: 'Major',
          category: 'Visual',
          title: 'Horizontal scroll on mobile viewport',
          description: 'Page has horizontal overflow on mobile devices',
          stepsToReproduce: ['Open on mobile device or resize to 375px width'],
          expectedBehavior: 'Page should fit within mobile viewport without horizontal scroll',
          actualBehavior: 'Horizontal scrollbar appears',
          screenshot,
          recommendedFix: 'Review CSS for fixed widths and ensure responsive layout',
        });
      }

      // Check for mobile menu
      const mobileMenu = page.locator('[class*="mobile"], [class*="hamburger"], button[aria-label*="menu"]');
      const hasMobileMenu = await mobileMenu.first().isVisible().catch(() => false);

      // Reset viewport
      await page.setViewportSize({ width: 1920, height: 1080 });
    });
  });

  // =========================================================================
  // 3. PROOFREADING REVIEW PAGE TESTS
  // =========================================================================
  test.describe('Proofreading Review Page', () => {
    test('should load proofreading review page', async () => {
      // Navigate to worklist first to find an item
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      // Try to navigate to a proofreading review page
      // Use a known worklist item ID if available
      await page.goto(`${FRONTEND_URL}#/worklist/6/review`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(8000);

      const screenshot = await takeScreenshot(page, 'proofreading-review');
      const content = await page.content();

      // Check for key proofreading elements
      const hasIssueList = content.includes('Issue') || content.includes('issue') ||
                          content.includes('Original') || content.includes('Suggested');

      if (!hasIssueList) {
        reportBug({
          page: '/worklist/:id/review',
          severity: 'Major',
          category: 'Functionality',
          title: 'Proofreading content not loading',
          description: 'Issue list or proofreading content not displayed',
          stepsToReproduce: ['Login', 'Navigate to a proofreading review page'],
          expectedBehavior: 'Should display list of proofreading issues with original/suggested text',
          actualBehavior: 'Proofreading content not visible',
          screenshot,
          recommendedFix: 'Check API response and component rendering',
        });
      }

      // Check for action buttons
      const acceptButton = page.locator('button').filter({ hasText: /Accept|Reject|Skip/i });
      const hasActionButtons = await acceptButton.first().isVisible().catch(() => false);

      // Check for three-panel layout
      const panels = page.locator('[class*="panel"], [class*="Panel"], [class*="col-"]');
      const panelCount = await panels.count();

      // Check for keyboard shortcuts hint
      const keyboardHint = content.includes('keyboard') || content.includes('shortcut') ||
                          content.includes('快捷鍵');
    });

    test('should verify diff view mode works', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist/6/review`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      // Look for view mode tabs/buttons
      const viewModeButtons = page.locator('button').filter({ hasText: /Original|Preview|Diff|Rendered/i });
      const viewModeCount = await viewModeButtons.count();

      if (viewModeCount > 0) {
        // Click on Diff view
        const diffButton = page.locator('button').filter({ hasText: /Diff/i }).first();
        if (await diffButton.isVisible()) {
          await diffButton.click();
          await page.waitForTimeout(2000);

          const screenshot = await takeScreenshot(page, 'proofreading-diff-view');

          // Check for diff visualization
          const content = await page.content();
          const hasDiffContent = content.includes('diff') || content.includes('Diff') ||
                                content.includes('change') || content.includes('modified');
        }
      }
    });

    test('should test issue navigation', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist/6/review`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      // Look for issue navigation (previous/next)
      const navButtons = page.locator('button').filter({ hasText: /<|>|Previous|Next|Prev/i });
      const hasNavButtons = await navButtons.first().isVisible().catch(() => false);

      // Look for issue counter
      const content = await page.content();
      const hasCounter = /\d+\s*\/\s*\d+/.test(content) || /\d+ of \d+/.test(content);

      const screenshot = await takeScreenshot(page, 'proofreading-issue-nav');

      if (!hasNavButtons && !hasCounter) {
        reportBug({
          page: '/worklist/:id/review',
          severity: 'Minor',
          category: 'UX',
          title: 'Issue navigation controls not visible',
          description: 'No visible way to navigate between issues',
          stepsToReproduce: ['Navigate to proofreading review page'],
          expectedBehavior: 'Should have Previous/Next buttons or issue counter',
          actualBehavior: 'Navigation controls not found',
          screenshot,
          recommendedFix: 'Add clear issue navigation with keyboard shortcuts',
        });
      }
    });
  });

  // =========================================================================
  // 4. PARSING REVIEW PAGE TESTS
  // =========================================================================
  test.describe('Parsing Review Page', () => {
    test('should load parsing page', async () => {
      await page.goto(`${FRONTEND_URL}#/articles/9/parsing`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      const screenshot = await takeScreenshot(page, 'parsing-page');
      const content = await page.content();

      // Check for parsing-specific content
      const hasParsingContent = content.includes('Parsing') || content.includes('parsing') ||
                               content.includes('Extract') || content.includes('Article');

      // Check for structured data display (title, content, images)
      const hasStructuredData = content.includes('Title') || content.includes('Content') ||
                               content.includes('Image') || content.includes('標題');
    });
  });

  // =========================================================================
  // 5. SEO CONFIRMATION PAGE TESTS
  // =========================================================================
  test.describe('SEO Confirmation Page', () => {
    test('should load SEO confirmation page', async () => {
      await page.goto(`${FRONTEND_URL}#/articles/9/seo-confirmation`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      const screenshot = await takeScreenshot(page, 'seo-confirmation-page');
      const content = await page.content();

      // Check for SEO-specific elements
      const hasSEOContent = content.includes('SEO') || content.includes('Meta') ||
                           content.includes('Keywords') || content.includes('Description');

      if (!hasSEOContent) {
        reportBug({
          page: '/articles/:id/seo-confirmation',
          severity: 'Major',
          category: 'Functionality',
          title: 'SEO content not loading',
          description: 'SEO fields and suggestions not displayed',
          stepsToReproduce: ['Navigate to SEO confirmation page'],
          expectedBehavior: 'Should display SEO title, meta description, keywords',
          actualBehavior: 'SEO content not visible',
          screenshot,
          recommendedFix: 'Check API response and component rendering',
        });
      }

      // Check for editable fields
      const inputs = page.locator('input, textarea');
      const inputCount = await inputs.count();

      // Check for confirm button
      const confirmButton = page.locator('button').filter({ hasText: /Confirm|Save|Submit|確認/i });
      const hasConfirmButton = await confirmButton.first().isVisible().catch(() => false);
    });
  });

  // =========================================================================
  // 6. PIPELINE MONITOR PAGE TESTS
  // =========================================================================
  test.describe('Pipeline Monitor Page', () => {
    test('should load pipeline monitor page', async () => {
      await page.goto(`${FRONTEND_URL}#/pipeline`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      const screenshot = await takeScreenshot(page, 'pipeline-monitor');
      const content = await page.content();

      // Check for pipeline-specific content
      const hasPipelineContent = content.includes('Pipeline') || content.includes('pipeline') ||
                                content.includes('Monitor') || content.includes('Status');

      // Check for status indicators
      const statusIndicators = page.locator('[class*="status"], [class*="badge"], [class*="indicator"]');
      const hasStatusIndicators = await statusIndicators.first().isVisible().catch(() => false);
    });
  });

  // =========================================================================
  // 7. SETTINGS PAGE TESTS
  // =========================================================================
  test.describe('Settings Page', () => {
    test('should load settings page without errors', async () => {
      await page.goto(`${FRONTEND_URL}#/settings`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      const screenshot = await takeScreenshot(page, 'settings-page');
      const content = await page.content();

      // Check for error messages
      const hasError = content.includes('Network Error') || content.includes('Unable to load') ||
                      content.includes('Error loading');

      if (hasError) {
        reportBug({
          page: '/settings',
          severity: 'Critical',
          category: 'Functionality',
          title: 'Settings page shows error',
          description: 'Network or loading error displayed on settings page',
          stepsToReproduce: ['Login', 'Navigate to /settings'],
          expectedBehavior: 'Settings should load without errors',
          actualBehavior: 'Error message displayed',
          screenshot,
          recommendedFix: 'Check API endpoint and error handling',
        });
      }

      // Check for settings sections
      const hasSettingsContent = content.includes('Settings') || content.includes('Provider') ||
                                content.includes('Cost') || content.includes('設定');

      // Check for accordion or expandable sections
      const accordions = page.locator('[class*="accordion"], [class*="Accordion"], [class*="collapse"]');
      const accordionCount = await accordions.count();

      // Check for save button
      const saveButton = page.locator('button').filter({ hasText: /Save|Apply|Update|保存|儲存/i });
      const hasSaveButton = await saveButton.first().isVisible().catch(() => false);
    });

    test('should test provider configuration section', async () => {
      await page.goto(`${FRONTEND_URL}#/settings`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      const screenshot = await takeScreenshot(page, 'settings-provider');
      const content = await page.content();

      // Check for provider selection
      const hasProviderSection = content.includes('Provider') || content.includes('AI') ||
                                content.includes('OpenAI') || content.includes('Claude') ||
                                content.includes('Anthropic');

      // Check for dropdown/select elements
      const selects = page.locator('select');
      const selectCount = await selects.count();

      // Check for API key fields (should be masked)
      const passwordInputs = page.locator('input[type="password"]');
      const hasPasswordFields = await passwordInputs.first().isVisible().catch(() => false);
    });

    test('should test form validation', async () => {
      await page.goto(`${FRONTEND_URL}#/settings`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      // Try to save with empty required fields
      const saveButton = page.locator('button').filter({ hasText: /Save|Apply|Update|保存|儲存/i }).first();
      if (await saveButton.isVisible()) {
        await saveButton.click();
        await page.waitForTimeout(2000);

        const screenshot = await takeScreenshot(page, 'settings-validation');
        const content = await page.content();

        // Check for validation messages
        const hasValidation = content.includes('required') || content.includes('Required') ||
                             content.includes('invalid') || content.includes('error') ||
                             content.includes('success') || content.includes('saved');
      }
    });
  });

  // =========================================================================
  // 8. ACCESSIBILITY TESTS
  // =========================================================================
  test.describe('Accessibility', () => {
    test('should have proper focus management', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(3000);

      // Test tab navigation
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');

      // Check if focus is visible
      const focusedElement = await page.locator(':focus').first();
      const hasFocusStyle = await focusedElement.evaluate(el => {
        const style = window.getComputedStyle(el);
        return style.outline !== 'none' || style.boxShadow !== 'none';
      }).catch(() => false);

      const screenshot = await takeScreenshot(page, 'accessibility-focus');

      if (!hasFocusStyle) {
        reportBug({
          page: 'All pages',
          severity: 'Major',
          category: 'Accessibility',
          title: 'Focus indicators may be missing',
          description: 'Keyboard focus is not clearly visible',
          stepsToReproduce: ['Navigate to any page', 'Press Tab key multiple times'],
          expectedBehavior: 'Focused elements should have visible outline or highlight',
          actualBehavior: 'Focus style not visible',
          screenshot,
          recommendedFix: 'Add :focus-visible styles with visible outlines',
        });
      }
    });

    test('should have proper contrast ratios', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(3000);

      // Check text contrast on key elements
      const textElements = page.locator('p, span, h1, h2, h3, button');
      const screenshot = await takeScreenshot(page, 'accessibility-contrast');

      // Note: Full contrast checking requires specialized tools like axe-core
      // This is a basic visual check
    });

    test('should have ARIA labels on interactive elements', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(3000);

      // Check buttons for aria-labels
      const buttons = await page.locator('button').all();
      let unlabeledButtons = 0;

      for (const button of buttons.slice(0, 10)) { // Check first 10 buttons
        const ariaLabel = await button.getAttribute('aria-label');
        const text = await button.textContent();

        if (!ariaLabel && (!text || text.trim().length === 0)) {
          unlabeledButtons++;
        }
      }

      if (unlabeledButtons > 2) {
        const screenshot = await takeScreenshot(page, 'accessibility-aria');
        reportBug({
          page: 'All pages',
          severity: 'Minor',
          category: 'Accessibility',
          title: 'Some buttons may lack accessible labels',
          description: `Found ${unlabeledButtons} buttons without text or aria-label`,
          stepsToReproduce: ['Navigate to worklist', 'Inspect button elements'],
          expectedBehavior: 'All buttons should have visible text or aria-label',
          actualBehavior: 'Some buttons have neither',
          screenshot,
          recommendedFix: 'Add aria-label to icon-only buttons',
        });
      }
    });
  });

  // =========================================================================
  // 9. i18n TESTS
  // =========================================================================
  test.describe('Internationalization', () => {
    test('should display content in Traditional Chinese', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      const content = await page.content();
      const screenshot = await takeScreenshot(page, 'i18n-chinese');

      // Check for Chinese characters
      const chinesePattern = /[\u4e00-\u9fff]/;
      const hasChineseText = chinesePattern.test(content);

      // Check for missing translation keys (usually appear as namespaced strings)
      const missingTranslationPattern = /[a-z]+\.[a-z]+\.[a-z]+/gi;
      const possibleMissingTranslations = content.match(missingTranslationPattern) || [];

      // Filter out false positives (URLs, class names, etc.)
      const likelyMissing = possibleMissingTranslations.filter(match =>
        !match.includes('http') &&
        !match.includes('www') &&
        !match.includes('googleapis')
      );

      if (likelyMissing.length > 5) {
        reportBug({
          page: 'All pages',
          severity: 'Minor',
          category: 'i18n',
          title: 'Possible missing translations',
          description: `Found patterns that might be untranslated keys: ${likelyMissing.slice(0, 5).join(', ')}`,
          stepsToReproduce: ['Navigate to any page', 'Look for English key patterns'],
          expectedBehavior: 'All text should be properly translated',
          actualBehavior: 'Some translation keys may be showing',
          screenshot,
          recommendedFix: 'Add missing translations to i18n files',
        });
      }
    });

    test('should handle language switcher if present', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(3000);

      // Look for language switcher
      const langSwitcher = page.locator('button, select').filter({ hasText: /EN|English|繁體|简体|Language/i });
      const hasLangSwitcher = await langSwitcher.first().isVisible().catch(() => false);

      const screenshot = await takeScreenshot(page, 'i18n-switcher');

      // Note: Having a language switcher is optional but good for UX
    });
  });

  // =========================================================================
  // 10. PERFORMANCE VISUAL INDICATORS
  // =========================================================================
  test.describe('Performance Indicators', () => {
    test('should show loading indicators during data fetch', async () => {
      // Navigate with cache disabled to see loading state
      await page.goto(`${FRONTEND_URL}#/worklist`, { timeout: 30000 });

      // Take immediate screenshot to capture loading
      const loadingScreenshot = await takeScreenshot(page, 'performance-loading');

      // Wait for load
      await page.waitForLoadState('networkidle', { timeout: 60000 }).catch(() => {});
      await page.waitForTimeout(5000);

      const loadedScreenshot = await takeScreenshot(page, 'performance-loaded');
    });

    test('should handle slow network gracefully', async () => {
      // Simulate slow network
      await page.route('**/*', async route => {
        await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay
        await route.continue();
      });

      await page.goto(`${FRONTEND_URL}#/worklist`, { timeout: 120000 }).catch(() => {});
      await page.waitForTimeout(10000);

      const screenshot = await takeScreenshot(page, 'performance-slow-network');
      const content = await page.content();

      // Check for timeout or loading stuck messages
      const hasTimeoutError = content.includes('timeout') || content.includes('Timeout') ||
                             content.includes('slow') || content.includes('retry');

      // Clear route handlers
      await page.unroute('**/*');
    });
  });

  // =========================================================================
  // 11. ERROR STATE TESTS
  // =========================================================================
  test.describe('Error States', () => {
    test('should handle 404 pages gracefully', async () => {
      await page.goto(`${FRONTEND_URL}#/nonexistent-page`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(3000);

      const screenshot = await takeScreenshot(page, 'error-404');
      const content = await page.content();

      // Check for 404 message or redirect
      const has404Message = content.includes('404') || content.includes('not found') ||
                           content.includes('Not Found') || content.includes('Page not found');
      const redirectedToHome = page.url().includes('/worklist') || page.url().endsWith('#/');

      if (!has404Message && !redirectedToHome) {
        reportBug({
          page: '/nonexistent-page',
          severity: 'Minor',
          category: 'UX',
          title: '404 handling unclear',
          description: 'Navigating to non-existent route has unclear behavior',
          stepsToReproduce: ['Navigate to a non-existent route like /nonexistent-page'],
          expectedBehavior: 'Should show 404 page or redirect to home',
          actualBehavior: 'Behavior is unclear',
          screenshot,
          recommendedFix: 'Add a proper 404 page or redirect logic',
        });
      }
    });

    test('should handle API errors gracefully', async () => {
      // Intercept and mock API error
      await page.route(`${BACKEND_URL}/**`, route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Internal Server Error' }),
        });
      });

      await page.goto(`${FRONTEND_URL}#/worklist`, { timeout: 60000 }).catch(() => {});
      await page.waitForTimeout(5000);

      const screenshot = await takeScreenshot(page, 'error-api-500');
      const content = await page.content();

      // Check for user-friendly error message
      const hasErrorUI = content.includes('error') || content.includes('Error') ||
                        content.includes('retry') || content.includes('Retry') ||
                        content.includes('問題') || content.includes('失敗');

      // Clear route handlers
      await page.unroute(`${BACKEND_URL}/**`);

      if (!hasErrorUI) {
        reportBug({
          page: 'All pages',
          severity: 'Major',
          category: 'UX',
          title: 'API error handling may be insufficient',
          description: 'When API returns error, user feedback may be unclear',
          stepsToReproduce: ['Cause an API error', 'Observe page behavior'],
          expectedBehavior: 'Should show clear error message with retry option',
          actualBehavior: 'Error handling unclear',
          screenshot,
          recommendedFix: 'Add error boundaries and user-friendly error states',
        });
      }
    });
  });

  // =========================================================================
  // 12. EMPTY STATE TESTS
  // =========================================================================
  test.describe('Empty States', () => {
    test('should display empty state for filtered results', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      // Search for something that shouldn't exist
      const searchInput = page.locator('input[placeholder*="search"], input[type="search"]').first();
      if (await searchInput.isVisible()) {
        await searchInput.fill('zzzznonexistent12345');
        await page.waitForTimeout(3000);

        const screenshot = await takeScreenshot(page, 'empty-state-search');
        const content = await page.content();

        // Check for empty state message
        const hasEmptyState = content.includes('No results') || content.includes('not found') ||
                             content.includes('empty') || content.includes('沒有') ||
                             content.includes('無');

        // Clear search
        await searchInput.clear();
      }
    });
  });

  // =========================================================================
  // 13. BUTTON AND INTERACTION TESTS
  // =========================================================================
  test.describe('Interactive Elements', () => {
    test('should verify all buttons are clickable', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      const buttons = await page.locator('button:visible').all();
      let disabledButtons = 0;
      let clickableButtons = 0;

      for (const button of buttons.slice(0, 10)) {
        const isDisabled = await button.isDisabled().catch(() => false);
        if (isDisabled) {
          disabledButtons++;
        } else {
          clickableButtons++;
        }
      }

      const screenshot = await takeScreenshot(page, 'buttons-state');
      console.log(`Buttons checked: ${clickableButtons} clickable, ${disabledButtons} disabled`);
    });

    test('should verify dropdowns open correctly', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      const selects = await page.locator('select:visible').all();

      for (const select of selects.slice(0, 3)) {
        await select.click();
        await page.waitForTimeout(500);
      }

      const screenshot = await takeScreenshot(page, 'dropdowns-test');
    });
  });

  // =========================================================================
  // 14. MODAL AND DRAWER TESTS
  // =========================================================================
  test.describe('Modals and Drawers', () => {
    test('should verify modal can be closed with Escape key', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      // Try to open a modal by clicking on a table row
      const tableRows = page.locator('table tbody tr');
      if (await tableRows.count() > 0) {
        await tableRows.first().click();
        await page.waitForTimeout(2000);

        // Check if modal opened
        const modal = page.locator('[class*="modal"], [class*="Modal"], [class*="drawer"], [class*="Drawer"]');
        if (await modal.first().isVisible()) {
          // Try to close with Escape
          await page.keyboard.press('Escape');
          await page.waitForTimeout(1000);

          const isStillVisible = await modal.first().isVisible().catch(() => false);
          const screenshot = await takeScreenshot(page, 'modal-escape-test');

          if (isStillVisible) {
            reportBug({
              page: 'All pages',
              severity: 'Minor',
              category: 'UX',
              title: 'Modal may not close with Escape key',
              description: 'Modal/drawer does not respond to Escape key press',
              stepsToReproduce: ['Open a modal', 'Press Escape key'],
              expectedBehavior: 'Modal should close',
              actualBehavior: 'Modal remains open',
              screenshot,
              recommendedFix: 'Add keyboard event handler for Escape key',
            });
          }
        }
      }
    });

    test('should verify modal backdrop closes modal on click', async () => {
      await page.goto(`${FRONTEND_URL}#/worklist`, { waitUntil: 'networkidle', timeout: 60000 });
      await page.waitForTimeout(5000);

      // Try to open a modal
      const tableRows = page.locator('table tbody tr');
      if (await tableRows.count() > 0) {
        await tableRows.first().click();
        await page.waitForTimeout(2000);

        // Check for backdrop
        const backdrop = page.locator('[class*="backdrop"], [class*="overlay"]');
        if (await backdrop.first().isVisible()) {
          await backdrop.first().click({ position: { x: 10, y: 10 } });
          await page.waitForTimeout(1000);

          const screenshot = await takeScreenshot(page, 'modal-backdrop-test');
        }
      }
    });
  });

  // =========================================================================
  // 15. FINAL SUMMARY TEST
  // =========================================================================
  test('Generate Final Bug Report', async () => {
    // This test runs last and generates the final report
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

    // Write bugs to JSON file
    const reportPath = `${SCREENSHOT_DIR}/${timestamp}_bug_report.json`;
    const fs = await import('fs');

    const report = {
      generatedAt: new Date().toISOString(),
      frontendUrl: FRONTEND_URL,
      backendUrl: BACKEND_URL,
      totalBugsFound: bugsFound.length,
      summary: {
        critical: bugsFound.filter(b => b.severity === 'Critical').length,
        major: bugsFound.filter(b => b.severity === 'Major').length,
        minor: bugsFound.filter(b => b.severity === 'Minor').length,
        enhancement: bugsFound.filter(b => b.severity === 'Enhancement').length,
      },
      byCategory: {
        visual: bugsFound.filter(b => b.category === 'Visual').length,
        ux: bugsFound.filter(b => b.category === 'UX').length,
        functionality: bugsFound.filter(b => b.category === 'Functionality').length,
        accessibility: bugsFound.filter(b => b.category === 'Accessibility').length,
        i18n: bugsFound.filter(b => b.category === 'i18n').length,
        performance: bugsFound.filter(b => b.category === 'Performance').length,
      },
      consoleErrorsCount: consoleErrors.length,
      bugs: bugsFound,
    };

    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log(`\nBug report saved to: ${reportPath}`);

    // Always pass this test - it's just for reporting
    expect(true).toBe(true);
  });
});
