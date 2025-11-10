/**
 * E2E Test Helper Utilities
 *
 * Provides reusable functions for Playwright and Chrome DevTools tests
 */

import { Page, expect, Locator } from '@playwright/test';
import type { APIRequestContext } from '@playwright/test';

export interface TestConfig {
  baseURL: string;
  apiBaseURL: string;
  timeout: {
    default: number;
    network: number;
    navigation: number;
  };
}

/**
 * Get test configuration based on environment
 */
export function getTestConfig(): TestConfig {
  const isLocal = process.env.TEST_LOCAL === '1';

  return {
    baseURL: isLocal
      ? 'http://localhost:4173/'
      : 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html',
    apiBaseURL: isLocal
      ? 'http://localhost:8000'
      : 'https://cms-automation-backend-baau2zqeqq-ue.a.run.app',
    timeout: {
      default: 30000,
      network: 60000,
      navigation: 45000,
    },
  };
}

/**
 * Wait for page to be fully loaded and hydrated
 */
export async function waitForPageReady(page: Page, options?: { timeout?: number }): Promise<void> {
  const timeout = options?.timeout || 10000;

  // Wait for network to be idle
  await page.waitForLoadState('networkidle', { timeout });

  // Wait for React to hydrate
  await page.waitForFunction(() => {
    return (window as any).__REACT_HYDRATED__ !== false;
  }, { timeout }).catch(() => {
    // If __REACT_HYDRATED__ doesn't exist, just continue
    console.log('React hydration flag not found, continuing...');
  });

  // Additional wait for any pending renders
  await page.waitForTimeout(1000);
}

/**
 * Enhanced page navigation with retry logic
 */
export async function navigateWithRetry(
  page: Page,
  url: string,
  options?: {
    maxRetries?: number;
    waitForNetworkIdle?: boolean;
  }
): Promise<void> {
  const maxRetries = options?.maxRetries || 3;
  const waitForNetworkIdle = options?.waitForNetworkIdle !== false;

  let lastError: Error | null = null;

  for (let i = 0; i < maxRetries; i++) {
    try {
      await page.goto(url, {
        waitUntil: waitForNetworkIdle ? 'networkidle' : 'load',
        timeout: 30000
      });

      await waitForPageReady(page);
      return;
    } catch (error) {
      lastError = error as Error;
      console.log(`Navigation attempt ${i + 1} failed: ${error}`);

      if (i < maxRetries - 1) {
        await page.waitForTimeout(2000 * (i + 1)); // Exponential backoff
      }
    }
  }

  throw new Error(`Failed to navigate to ${url} after ${maxRetries} attempts: ${lastError?.message}`);
}

/**
 * Wait for element with enhanced error reporting
 */
export async function waitForElement(
  page: Page,
  selector: string,
  options?: {
    timeout?: number;
    state?: 'attached' | 'detached' | 'visible' | 'hidden';
  }
): Promise<Locator> {
  const timeout = options?.timeout || 10000;
  const state = options?.state || 'visible';

  try {
    const element = page.locator(selector);
    await element.waitFor({ state, timeout });
    return element;
  } catch (error) {
    // Enhanced error reporting
    const pageContent = await page.content();
    const allElements = await page.locator('*').evaluateAll(els =>
      els.map(el => ({
        tag: el.tagName,
        id: el.id,
        class: el.className,
        text: el.textContent?.substring(0, 50)
      })).slice(0, 20)
    );

    console.error('Failed to find element:', selector);
    console.error('Page elements:', JSON.stringify(allElements, null, 2));
    throw error;
  }
}

/**
 * Check if element exists without throwing
 */
export async function elementExists(page: Page, selector: string): Promise<boolean> {
  try {
    const count = await page.locator(selector).count();
    return count > 0;
  } catch {
    return false;
  }
}

/**
 * Get element text with fallback
 */
export async function getTextContent(locator: Locator, defaultValue: string = ''): Promise<string> {
  try {
    const text = await locator.textContent();
    return text || defaultValue;
  } catch {
    return defaultValue;
  }
}

/**
 * Click element with retry logic
 */
export async function clickWithRetry(
  locator: Locator,
  options?: {
    maxRetries?: number;
    waitAfter?: number;
  }
): Promise<void> {
  const maxRetries = options?.maxRetries || 3;
  const waitAfter = options?.waitAfter || 500;

  let lastError: Error | null = null;

  for (let i = 0; i < maxRetries; i++) {
    try {
      await locator.click({ timeout: 5000 });
      await new Promise(resolve => setTimeout(resolve, waitAfter));
      return;
    } catch (error) {
      lastError = error as Error;
      console.log(`Click attempt ${i + 1} failed: ${error}`);

      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  }

  throw new Error(`Failed to click element after ${maxRetries} attempts: ${lastError?.message}`);
}

/**
 * Fill input with validation
 */
export async function fillInput(
  locator: Locator,
  value: string,
  options?: {
    clear?: boolean;
    validate?: boolean;
  }
): Promise<void> {
  const clear = options?.clear !== false;
  const validate = options?.validate !== false;

  if (clear) {
    await locator.clear();
  }

  await locator.fill(value);

  if (validate) {
    const actualValue = await locator.inputValue();
    expect(actualValue).toBe(value);
  }
}

/**
 * Monitor console errors and warnings
 */
export interface ConsoleMonitor {
  errors: string[];
  warnings: string[];
  logs: string[];
  start: () => void;
  stop: () => void;
  getReport: () => string;
}

export function createConsoleMonitor(page: Page): ConsoleMonitor {
  const errors: string[] = [];
  const warnings: string[] = [];
  const logs: string[] = [];
  let isMonitoring = false;

  const errorHandler = (msg: any) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    } else if (msg.type() === 'warning') {
      warnings.push(msg.text());
    } else {
      logs.push(`[${msg.type()}] ${msg.text()}`);
    }
  };

  const pageErrorHandler = (error: Error) => {
    errors.push(`[PAGE ERROR] ${error.message}`);
  };

  return {
    errors,
    warnings,
    logs,

    start() {
      if (!isMonitoring) {
        page.on('console', errorHandler);
        page.on('pageerror', pageErrorHandler);
        isMonitoring = true;
      }
    },

    stop() {
      if (isMonitoring) {
        page.off('console', errorHandler);
        page.off('pageerror', pageErrorHandler);
        isMonitoring = false;
      }
    },

    getReport() {
      return `
Console Errors: ${errors.length}
${errors.map((e, i) => `  ${i + 1}. ${e}`).join('\n')}

Console Warnings: ${warnings.length}
${warnings.map((w, i) => `  ${i + 1}. ${w}`).join('\n')}

Console Logs: ${logs.length}
${logs.slice(0, 10).map((l, i) => `  ${i + 1}. ${l}`).join('\n')}
${logs.length > 10 ? `  ... and ${logs.length - 10} more` : ''}
      `.trim();
    },
  };
}

/**
 * Monitor network requests
 */
export interface NetworkMonitor {
  requests: Array<{ method: string; url: string; status?: number }>;
  failures: Array<{ method: string; url: string; error: string }>;
  start: () => void;
  stop: () => void;
  getReport: () => string;
}

export function createNetworkMonitor(page: Page, options?: {
  urlFilter?: RegExp;
}): NetworkMonitor {
  const requests: Array<{ method: string; url: string; status?: number }> = [];
  const failures: Array<{ method: string; url: string; error: string }> = [];
  const urlFilter = options?.urlFilter;
  let isMonitoring = false;

  const responseHandler = async (response: any) => {
    const url = response.url();
    if (urlFilter && !urlFilter.test(url)) return;

    requests.push({
      method: response.request().method(),
      url,
      status: response.status(),
    });
  };

  const requestFailedHandler = (request: any) => {
    const url = request.url();
    if (urlFilter && !urlFilter.test(url)) return;

    failures.push({
      method: request.method(),
      url,
      error: request.failure()?.errorText || 'Unknown error',
    });
  };

  return {
    requests,
    failures,

    start() {
      if (!isMonitoring) {
        page.on('response', responseHandler);
        page.on('requestfailed', requestFailedHandler);
        isMonitoring = true;
      }
    },

    stop() {
      if (isMonitoring) {
        page.off('response', responseHandler);
        page.off('requestfailed', requestFailedHandler);
        isMonitoring = false;
      }
    },

    getReport() {
      const successCount = requests.filter(r => r.status && r.status < 400).length;
      const errorCount = requests.filter(r => r.status && r.status >= 400).length;

      return `
Network Requests: ${requests.length}
  Success: ${successCount}
  Errors: ${errorCount}
  Failures: ${failures.length}

Failed Requests:
${failures.map((f, i) => `  ${i + 1}. ${f.method} ${f.url} - ${f.error}`).join('\n')}

Error Responses:
${requests.filter(r => r.status && r.status >= 400).map((r, i) =>
  `  ${i + 1}. ${r.method} ${r.url} - ${r.status}`
).join('\n')}
      `.trim();
    },
  };
}

/**
 * Take screenshot with metadata
 */
export async function takeScreenshot(
  page: Page,
  name: string,
  options?: {
    fullPage?: boolean;
    path?: string;
  }
): Promise<Buffer> {
  const fullPage = options?.fullPage !== false;
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = options?.path || `test-results/screenshots/${timestamp}-${name}.png`;

  const screenshot = await page.screenshot({
    path: filename,
    fullPage,
  });

  console.log(`📸 Screenshot saved: ${filename}`);
  return screenshot;
}

/**
 * Wait for API response
 */
export async function waitForAPIResponse(
  page: Page,
  urlPattern: string | RegExp,
  options?: {
    timeout?: number;
    status?: number;
  }
): Promise<any> {
  const timeout = options?.timeout || 30000;
  const expectedStatus = options?.status || 200;

  const response = await page.waitForResponse(
    response => {
      const matchesURL = typeof urlPattern === 'string'
        ? response.url().includes(urlPattern)
        : urlPattern.test(response.url());

      const matchesStatus = !expectedStatus || response.status() === expectedStatus;

      return matchesURL && matchesStatus;
    },
    { timeout }
  );

  return await response.json();
}

/**
 * Measure page performance
 */
export interface PerformanceMetrics {
  loadTime: number;
  domContentLoaded: number;
  firstContentfulPaint: number;
  timeToInteractive: number;
  totalSize: number;
  requestCount: number;
}

export async function measurePerformance(page: Page): Promise<PerformanceMetrics> {
  const performanceData = await page.evaluate(() => {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    const paint = performance.getEntriesByType('paint');
    const fcp = paint.find(entry => entry.name === 'first-contentful-paint');

    return {
      loadTime: navigation.loadEventEnd - navigation.fetchStart,
      domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
      firstContentfulPaint: fcp ? fcp.startTime : 0,
      timeToInteractive: navigation.domInteractive - navigation.fetchStart,
    };
  });

  // Get resource metrics
  const resources = await page.evaluate(() => {
    const resources = performance.getEntriesByType('resource');
    return {
      totalSize: resources.reduce((sum, r: any) => sum + (r.transferSize || 0), 0),
      requestCount: resources.length,
    };
  });

  return {
    ...performanceData,
    ...resources,
  };
}

/**
 * Assert no console errors
 */
export function assertNoConsoleErrors(monitor: ConsoleMonitor, options?: {
  allowedErrors?: string[];
}) {
  const allowedErrors = options?.allowedErrors || [];
  const unexpectedErrors = monitor.errors.filter(error =>
    !allowedErrors.some(allowed => error.includes(allowed))
  );

  if (unexpectedErrors.length > 0) {
    throw new Error(
      `Found ${unexpectedErrors.length} console errors:\n${unexpectedErrors.join('\n')}`
    );
  }
}

/**
 * Assert no network failures
 */
export function assertNoNetworkFailures(monitor: NetworkMonitor, options?: {
  allowedFailures?: string[];
}) {
  const allowedFailures = options?.allowedFailures || [];
  const unexpectedFailures = monitor.failures.filter(failure =>
    !allowedFailures.some(allowed => failure.url.includes(allowed))
  );

  if (unexpectedFailures.length > 0) {
    throw new Error(
      `Found ${unexpectedFailures.length} network failures:\n` +
      unexpectedFailures.map(f => `${f.method} ${f.url} - ${f.error}`).join('\n')
    );
  }
}
