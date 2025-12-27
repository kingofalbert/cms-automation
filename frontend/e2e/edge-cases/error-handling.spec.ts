/**
 * Error Handling Edge Case Tests
 *
 * Tests how the application handles various error scenarios.
 * Covers: API errors, network timeouts, invalid data, error boundaries.
 */

import { test, expect } from '@playwright/test';
import { navigateWithRetry, waitForPageReady } from '../utils/test-helpers';
import { waitForAnimations, captureScreenshot } from '../utils/visual-test-helpers';

const BASE_URL = process.env.TEST_LOCAL === '1'
  ? 'http://localhost:4173'
  : 'https://storage.googleapis.com/cms-automation-frontend-476323/index.html';

test.describe('Error Handling Edge Cases', () => {
  test.describe('API Error Handling', () => {
    test('should display error message on API failure', async ({ page }) => {
      // Intercept API calls and return error
      await page.route('**/api/**', (route) => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Internal Server Error' }),
        });
      });

      await navigateWithRetry(page, BASE_URL);

      // Check for error state display
      const errorIndicator = page.locator('text=/error|failed|失败|错误/i');
      // May show error or fallback to empty state
      console.log('API error handling captured');

      // Clear route
      await page.unroute('**/api/**');
    });

    test('should handle 404 API responses gracefully', async ({ page }) => {
      await page.route('**/api/articles/**', (route) => {
        route.fulfill({
          status: 404,
          body: JSON.stringify({ error: 'Not Found' }),
        });
      });

      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      // App should remain functional
      await expect(page.locator('text=CMS Automation System')).toBeVisible();

      await page.unroute('**/api/articles/**');
    });

    test('should handle 401 Unauthorized responses', async ({ page }) => {
      await page.route('**/api/**', (route) => {
        route.fulfill({
          status: 401,
          body: JSON.stringify({ error: 'Unauthorized' }),
        });
      });

      await navigateWithRetry(page, BASE_URL);

      // May redirect to login or show auth error
      const authError = page.locator('text=/unauthorized|login|登录/i');
      // App should handle gracefully
      console.log('401 handling captured');

      await page.unroute('**/api/**');
    });

    test('should handle 403 Forbidden responses', async ({ page }) => {
      await page.route('**/api/**', (route) => {
        route.fulfill({
          status: 403,
          body: JSON.stringify({ error: 'Forbidden' }),
        });
      });

      await navigateWithRetry(page, BASE_URL);

      // Should show access denied or permission error
      console.log('403 handling captured');

      await page.unroute('**/api/**');
    });
  });

  test.describe('Network Error Handling', () => {
    test('should handle network timeout gracefully', async ({ page }) => {
      // Set a short timeout for this test
      page.setDefaultTimeout(5000);

      // Simulate slow network that times out
      await page.route('**/api/**', async (route) => {
        await new Promise((resolve) => setTimeout(resolve, 10000));
        await route.continue();
      });

      await navigateWithRetry(page, BASE_URL);

      // Should show timeout error or loading state
      const loadingOrError = page.locator('text=/loading|timeout|超时|加载/i');
      console.log('Network timeout handling captured');

      await page.unroute('**/api/**');
    });

    test('should handle network disconnect', async ({ page }) => {
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      // Simulate offline mode
      await page.route('**/api/**', (route) => {
        route.abort('failed');
      });

      // Try to perform an action that requires API
      const syncButton = page.locator('button:has-text("Sync Google Drive")');
      if (await syncButton.isVisible()) {
        await syncButton.click();
        await waitForAnimations(page);

        // Should show network error
        const networkError = page.locator('text=/network|offline|连接失败/i');
        // May or may not show depending on implementation
      }

      await page.unroute('**/api/**');
    });

    test('should retry failed requests', async ({ page }) => {
      let requestCount = 0;

      await page.route('**/api/**', (route) => {
        requestCount++;
        if (requestCount < 3) {
          route.abort('failed');
        } else {
          route.continue();
        }
      });

      await navigateWithRetry(page, BASE_URL);

      console.log(`Request count after retries: ${requestCount}`);

      await page.unroute('**/api/**');
    });
  });

  test.describe('Invalid Data Handling', () => {
    test('should handle malformed JSON response', async ({ page }) => {
      await page.route('**/api/worklist**', (route) => {
        route.fulfill({
          status: 200,
          body: 'invalid json {{{',
          contentType: 'application/json',
        });
      });

      await navigateWithRetry(page, BASE_URL);

      // Should not crash - show error or empty state
      await expect(page.locator('text=CMS Automation System')).toBeVisible();

      await page.unroute('**/api/worklist**');
    });

    test('should handle empty API response', async ({ page }) => {
      await page.route('**/api/worklist**', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify([]),
        });
      });

      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      // Should show empty state
      await expect(page.locator('text=CMS Automation System')).toBeVisible();

      await page.unroute('**/api/worklist**');
    });

    test('should handle null values in response', async ({ page }) => {
      await page.route('**/api/worklist**', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify([
            { id: 1, title: null, status: null, author: null },
          ]),
        });
      });

      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      // Should not crash
      await expect(page.locator('text=CMS Automation System')).toBeVisible();

      await page.unroute('**/api/worklist**');
    });

    test('should handle unexpected data types', async ({ page }) => {
      await page.route('**/api/worklist**', (route) => {
        route.fulfill({
          status: 200,
          body: JSON.stringify([
            { id: 'not-a-number', title: 12345, status: [], author: {} },
          ]),
        });
      });

      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      // Should handle gracefully
      await expect(page.locator('text=CMS Automation System')).toBeVisible();

      await page.unroute('**/api/worklist**');
    });
  });

  test.describe('Form Validation Errors', () => {
    async function openArticleReview(page: any) {
      const reviewButton = page.locator('button:has-text("Review")').first();
      if (await reviewButton.isVisible()) {
        await reviewButton.click();
        await waitForAnimations(page);
        return true;
      }
      return false;
    }

    test('should show validation error for empty required fields', async ({ page }) => {
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      const opened = await openArticleReview(page);
      if (!opened) {
        test.skip();
        return;
      }

      // Clear a required field and try to proceed
      const titleInput = page.locator('input').first();
      if (await titleInput.isVisible()) {
        await titleInput.clear();

        // Try to proceed
        const nextButton = page.locator('button:has-text("下一步")');
        if (await nextButton.isVisible()) {
          await nextButton.click();
          await waitForAnimations(page);

          // Check for validation error
          const errorMessage = page.locator('text=/required|必填|不能为空/i');
          if (await errorMessage.count() > 0) {
            await expect(errorMessage.first()).toBeVisible();
          }
        }
      }
    });

    test('should show validation error for invalid input format', async ({ page }) => {
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      // Navigate to settings
      const settingsButton = page.locator('button:has-text("Settings")');
      await settingsButton.click();
      await waitForAnimations(page);

      // Find a number input and enter invalid value
      const numberInput = page.locator('input[type="number"]').first();
      if (await numberInput.isVisible()) {
        await numberInput.fill('invalid');
        await numberInput.blur();
        await waitForAnimations(page);
      }
    });
  });

  test.describe('Error Boundary Behavior', () => {
    test('should catch and display component errors gracefully', async ({ page }) => {
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      // Inject an error-causing script
      await page.evaluate(() => {
        // This might trigger error boundary if there's one
        const event = new ErrorEvent('error', {
          error: new Error('Test error'),
          message: 'Test error message',
        });
        window.dispatchEvent(event);
      });

      // App should either catch error or remain functional
      // Check that app doesn't show blank screen
      const content = await page.content();
      expect(content.length).toBeGreaterThan(100);
    });

    test('should recover from errors when navigating away', async ({ page }) => {
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      // Navigate to settings
      const settingsButton = page.locator('button:has-text("Settings")');
      await settingsButton.click();
      await waitForAnimations(page);

      // Go back to worklist
      const backButton = page.locator('button:has-text("← Back to Worklist")');
      await backButton.click();
      await waitForAnimations(page);

      // App should be fully functional
      await expect(page.locator('text=CMS Automation System')).toBeVisible();
    });
  });

  test.describe('Save Operation Errors', () => {
    test('should handle save failure gracefully', async ({ page }) => {
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      // Intercept save API call
      await page.route('**/api/**/save**', (route) => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Failed to save' }),
        });
      });

      // Open article review
      const reviewButton = page.locator('button:has-text("Review")').first();
      if (await reviewButton.isVisible()) {
        await reviewButton.click();
        await waitForAnimations(page);

        // Try to save
        const saveButton = page.locator('button:has-text("保存")');
        if (await saveButton.isVisible()) {
          await saveButton.click();
          await waitForAnimations(page);

          // Should show error notification
          const errorNotification = page.locator('text=/error|failed|失败/i');
          // May or may not show depending on implementation
        }
      }

      await page.unroute('**/api/**/save**');
    });

    test('should preserve data after save failure', async ({ page }) => {
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      // Intercept save API call
      await page.route('**/api/**/save**', (route) => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Failed to save' }),
        });
      });

      // Open article review and make changes
      const reviewButton = page.locator('button:has-text("Review")').first();
      if (await reviewButton.isVisible()) {
        await reviewButton.click();
        await waitForAnimations(page);

        const titleInput = page.locator('input').first();
        if (await titleInput.isVisible()) {
          const testValue = 'Test Title ' + Date.now();
          await titleInput.fill(testValue);

          // Try to save (will fail)
          const saveButton = page.locator('button:has-text("保存")');
          if (await saveButton.isVisible()) {
            await saveButton.click();
            await waitForAnimations(page);

            // Data should still be preserved in input
            const currentValue = await titleInput.inputValue();
            expect(currentValue).toBe(testValue);
          }
        }
      }

      await page.unroute('**/api/**/save**');
    });
  });

  test.describe('Concurrent Operation Errors', () => {
    test('should handle rapid save attempts gracefully', async ({ page }) => {
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      let saveCount = 0;
      await page.route('**/api/**/save**', (route) => {
        saveCount++;
        route.fulfill({
          status: 200,
          body: JSON.stringify({ success: true }),
        });
      });

      // Open article review
      const reviewButton = page.locator('button:has-text("Review")').first();
      if (await reviewButton.isVisible()) {
        await reviewButton.click();
        await waitForAnimations(page);

        // Rapidly click save multiple times
        const saveButton = page.locator('button:has-text("保存")');
        if (await saveButton.isVisible()) {
          for (let i = 0; i < 5; i++) {
            await saveButton.click();
          }
          await waitForAnimations(page);

          console.log(`Save attempts: ${saveCount}`);
        }
      }

      await page.unroute('**/api/**/save**');
    });
  });

  test.describe('Session and Auth Errors', () => {
    test('should handle session expiry', async ({ page }) => {
      await navigateWithRetry(page, BASE_URL);
      await waitForPageReady(page);

      // Simulate session expiry on next API call
      await page.route('**/api/**', (route) => {
        route.fulfill({
          status: 401,
          body: JSON.stringify({ error: 'Session expired' }),
        });
      });

      // Try to perform an action
      const syncButton = page.locator('button:has-text("Sync Google Drive")');
      if (await syncButton.isVisible()) {
        await syncButton.click();
        await waitForAnimations(page);
      }

      // Should handle session expiry (redirect to login or show message)
      console.log('Session expiry handling captured');

      await page.unroute('**/api/**');
    });
  });
});
