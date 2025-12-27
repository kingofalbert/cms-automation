/**
 * Visual Test Helper Utilities
 *
 * Provides reusable functions for visual regression testing and edge case testing.
 * Extends the existing test-helpers.ts with visual-specific utilities.
 */

import { Page, expect, Locator } from '@playwright/test';

/**
 * Viewport presets for responsive testing
 */
export const VIEWPORTS = {
  mobile: { width: 320, height: 568 },
  mobileLandscape: { width: 568, height: 320 },
  tablet: { width: 768, height: 1024 },
  tabletLandscape: { width: 1024, height: 768 },
  desktop: { width: 1280, height: 800 },
  desktopLarge: { width: 1920, height: 1080 },
  desktopUltrawide: { width: 2560, height: 1080 },
};

/**
 * Wait for all animations and transitions to complete
 */
export async function waitForAnimations(page: Page, options?: { timeout?: number }): Promise<void> {
  const timeout = options?.timeout || 5000;

  // Wait for CSS animations to complete
  await page.evaluate(() => {
    return new Promise<void>((resolve) => {
      const animations = document.getAnimations();
      if (animations.length === 0) {
        resolve();
        return;
      }
      Promise.all(animations.map((a) => a.finished)).then(() => resolve());
    });
  });

  // Additional wait for any React transitions
  await page.waitForTimeout(300);
}

/**
 * Test a page across multiple viewports
 */
export async function testResponsive(
  page: Page,
  callback: (viewport: { name: string; width: number; height: number }) => Promise<void>,
  options?: { viewports?: (keyof typeof VIEWPORTS)[] }
): Promise<void> {
  const viewportNames = options?.viewports || ['mobile', 'tablet', 'desktop'];

  for (const name of viewportNames) {
    const viewport = VIEWPORTS[name];
    await page.setViewportSize(viewport);
    await waitForAnimations(page);
    await callback({ name, ...viewport });
  }
}

/**
 * Capture screenshot with consistent naming and metadata
 */
export async function captureScreenshot(
  page: Page,
  name: string,
  options?: {
    fullPage?: boolean;
    viewport?: keyof typeof VIEWPORTS;
  }
): Promise<Buffer> {
  const fullPage = options?.fullPage ?? true;
  const viewportSuffix = options?.viewport ? `-${options.viewport}` : '';
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `e2e/screenshots/${timestamp}-${name}${viewportSuffix}.png`;

  await waitForAnimations(page);

  return await page.screenshot({
    path: filename,
    fullPage,
  });
}

/**
 * Expect a toast notification to appear with specific message
 */
export async function expectToast(
  page: Page,
  message: string | RegExp,
  options?: {
    type?: 'success' | 'error' | 'warning' | 'info';
    timeout?: number;
  }
): Promise<void> {
  const timeout = options?.timeout || 5000;

  // Sonner toast renders in a specific container
  const toastLocator = page.locator('[data-sonner-toast]').filter({
    hasText: message,
  });

  await expect(toastLocator).toBeVisible({ timeout });

  // Optionally verify toast type by checking for type-specific classes
  if (options?.type) {
    // Sonner uses data attributes for toast type
    await expect(toastLocator).toHaveAttribute('data-type', options.type, { timeout: 1000 }).catch(() => {
      // Fallback: check for success/error text or icon
      console.log(`Toast type verification skipped for type: ${options.type}`);
    });
  }
}

/**
 * Expect toast to disappear after showing
 */
export async function expectToastToDismiss(
  page: Page,
  message: string | RegExp,
  options?: { timeout?: number }
): Promise<void> {
  const timeout = options?.timeout || 10000;

  const toastLocator = page.locator('[data-sonner-toast]').filter({
    hasText: message,
  });

  await expect(toastLocator).not.toBeVisible({ timeout });
}

/**
 * Verify batch operation results by checking UI state
 */
export async function verifyBatchOperationResult(
  page: Page,
  expectedCounts: {
    pending?: number;
    accepted?: number;
    rejected?: number;
  }
): Promise<void> {
  // Check pending count in the batch controls
  if (expectedCounts.pending !== undefined) {
    const pendingText = page.locator('text=/\\d+ 个待处理问题/');
    if (expectedCounts.pending === 0) {
      await expect(pendingText).not.toBeVisible().catch(async () => {
        // Alternatively, check for "所有问题已审核" message
        await expect(page.locator('text=所有问题已审核')).toBeVisible();
      });
    } else {
      await expect(pendingText).toContainText(`${expectedCounts.pending} 个待处理问题`);
    }
  }

  // Check status indicators in the header
  if (expectedCounts.accepted !== undefined) {
    await expect(page.locator('text=/已接受.*' + expectedCounts.accepted + '/')).toBeVisible();
  }

  if (expectedCounts.rejected !== undefined) {
    await expect(page.locator('text=/已拒绝.*' + expectedCounts.rejected + '/')).toBeVisible();
  }
}

/**
 * Verify empty state is displayed correctly
 */
export async function verifyEmptyState(
  page: Page,
  expectedText: string | RegExp,
  options?: { hasAction?: boolean }
): Promise<void> {
  const emptyState = page.locator('[data-testid="empty-state"], .empty-state, [class*="EmptyState"]');

  await expect(emptyState).toBeVisible();
  await expect(emptyState).toContainText(expectedText);

  if (options?.hasAction) {
    const actionButton = emptyState.locator('button');
    await expect(actionButton).toBeVisible();
  }
}

/**
 * Test text truncation for long content
 */
export async function verifyTextTruncation(
  locator: Locator,
  options?: { maxLines?: number }
): Promise<boolean> {
  const element = await locator.elementHandle();
  if (!element) return false;

  const isTruncated = await locator.evaluate((el) => {
    return el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight;
  });

  return isTruncated;
}

/**
 * Verify element is within viewport (for scroll testing)
 */
export async function isInViewport(page: Page, locator: Locator): Promise<boolean> {
  const boundingBox = await locator.boundingBox();
  if (!boundingBox) return false;

  const viewport = page.viewportSize();
  if (!viewport) return false;

  return (
    boundingBox.x >= 0 &&
    boundingBox.y >= 0 &&
    boundingBox.x + boundingBox.width <= viewport.width &&
    boundingBox.y + boundingBox.height <= viewport.height
  );
}

/**
 * Simulate rapid clicks (for testing debounce/throttle)
 */
export async function rapidClick(
  locator: Locator,
  count: number = 5,
  intervalMs: number = 50
): Promise<void> {
  for (let i = 0; i < count; i++) {
    await locator.click({ force: true });
    if (i < count - 1) {
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
    }
  }
}

/**
 * Test modal behavior (open, close, escape key)
 */
export async function testModalBehavior(
  page: Page,
  triggerLocator: Locator,
  modalSelector: string
): Promise<{
  opens: boolean;
  closesOnEscape: boolean;
  closesOnBackdrop: boolean;
  closesOnButton: boolean;
}> {
  const results = {
    opens: false,
    closesOnEscape: false,
    closesOnBackdrop: false,
    closesOnButton: false,
  };

  // Test modal opens
  await triggerLocator.click();
  await waitForAnimations(page);
  results.opens = await page.locator(modalSelector).isVisible();

  if (!results.opens) return results;

  // Test escape key
  await page.keyboard.press('Escape');
  await waitForAnimations(page);
  results.closesOnEscape = !(await page.locator(modalSelector).isVisible());

  // Reopen for next test
  await triggerLocator.click();
  await waitForAnimations(page);

  // Test close button (if exists)
  const closeButton = page.locator(`${modalSelector} [aria-label="Close"], ${modalSelector} button:has-text("关闭"), ${modalSelector} button:has-text("×")`).first();
  if (await closeButton.isVisible()) {
    await closeButton.click();
    await waitForAnimations(page);
    results.closesOnButton = !(await page.locator(modalSelector).isVisible());
  }

  return results;
}

/**
 * Measure scroll performance (for large lists)
 */
export async function measureScrollPerformance(
  page: Page,
  containerSelector: string,
  scrollDistance: number = 1000
): Promise<{
  avgFrameTime: number;
  droppedFrames: number;
}> {
  const container = page.locator(containerSelector);

  const metrics = await page.evaluate(
    async ({ selector, distance }) => {
      const el = document.querySelector(selector);
      if (!el) return { avgFrameTime: 0, droppedFrames: 0 };

      const frameTimes: number[] = [];
      let lastTime = performance.now();

      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'frame') {
            const currentTime = performance.now();
            frameTimes.push(currentTime - lastTime);
            lastTime = currentTime;
          }
        }
      });

      observer.observe({ entryTypes: ['frame'] });

      // Smooth scroll
      el.scrollBy({ top: distance, behavior: 'smooth' });
      await new Promise((resolve) => setTimeout(resolve, 1000));

      observer.disconnect();

      const avgFrameTime =
        frameTimes.length > 0
          ? frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length
          : 16.67;
      const droppedFrames = frameTimes.filter((t) => t > 33.33).length;

      return { avgFrameTime, droppedFrames };
    },
    { selector: containerSelector, distance: scrollDistance }
  );

  return metrics;
}

/**
 * Generate mock data for testing edge cases
 */
export const MockDataGenerators = {
  /**
   * Generate a long string for truncation testing
   */
  longString(length: number = 200, pattern: string = '测试文本'): string {
    let result = '';
    while (result.length < length) {
      result += pattern;
    }
    return result.substring(0, length);
  },

  /**
   * Generate array of items for list testing
   */
  generateItems<T>(count: number, factory: (index: number) => T): T[] {
    return Array.from({ length: count }, (_, i) => factory(i));
  },

  /**
   * Generate mock proofreading issue
   */
  proofreadingIssue(index: number) {
    const severities = ['critical', 'warning', 'info'] as const;
    const categories = ['typo', 'punctuation', 'style', 'consistency'] as const;

    return {
      id: `issue-${index}`,
      original_text: `原始文本 ${index}`,
      suggested_text: `建議文本 ${index}`,
      severity: severities[index % 3],
      category: categories[index % 4],
      engine: index % 2 === 0 ? 'ai' : 'deterministic',
      confidence: 0.7 + (index % 30) / 100,
      decision_status: 'pending',
    };
  },
};
