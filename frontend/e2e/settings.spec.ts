import { expect, test } from '@playwright/test';
import type { Page, Route } from '@playwright/test';

const SETTINGS_URL = '/app.html#/settings';

const baseSettingsResponse = {
  provider_config: {
    playwright: {
      enabled: true,
      headless: true,
      screenshot_on_error: true,
      browser: 'chromium',
      timeout: 30000,
      retry_count: 2,
    },
    computer_use: {
      enabled: false,
      model: 'claude-sonnet-4-5-20250929',
      max_tokens: 8192,
      timeout: 60000,
      retry_count: 2,
      screenshot_interval: 5000,
    },
    hybrid: {
      enabled: false,
      primary_provider: 'playwright',
      fallback_enabled: true,
      fallback_on_error: true,
      auto_switch_threshold: 70,
    },
  },
  cms_config: {
    wordpress_url: 'https://example.com',
    username: 'admin',
    password: 'password',
    verify_ssl: true,
    timeout: 30000,
    max_retries: 3,
  },
  cost_limits: {
    daily_limit: 100,
    monthly_limit: 3000,
    per_task_limit: 10,
    alert_threshold: 80,
    auto_pause_on_limit: true,
  },
  screenshot_retention: {
    retention_days: 30,
    max_screenshots_per_task: 10,
    compress_screenshots: true,
    compression_quality: 80,
    delete_on_success: false,
    delete_on_failure: false,
  },
  updated_at: '2025-01-10T10:00:00.000Z',
};

const costUsageResponse = {
  daily_spend: 12.5,
  monthly_spend: 320.75,
};

const storageUsageResponse = {
  total_mb: 512.34,
};

async function withSettingsRoutes(
  page: Page,
  options: {
    delayMs?: number;
    settingsOverride?: Partial<typeof baseSettingsResponse>;
    onPut?: (route: Route) => Promise<void>;
  } = {}
) {
  const { delayMs = 0, settingsOverride, onPut } = options;
  const settingsPayload = {
    ...baseSettingsResponse,
    ...settingsOverride,
  };

  const settingsHandler = async (route: Route) => {
    const request = route.request();
    if (request.method() === 'GET') {
      if (delayMs) {
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(settingsPayload),
      });
      return;
    }

    if (request.method() === 'PUT') {
      if (onPut) {
        await onPut(route);
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(settingsPayload),
      });
      return;
    }

    await route.continue();
  };

  const costHandler = async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(costUsageResponse),
    });
  };

  const storageHandler = async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(storageUsageResponse),
    });
  };

  const testConnectionHandler = async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true }),
    });
  };

  await page.route('**/v1/settings', settingsHandler);
  await page.route('**/v1/analytics/cost-usage', costHandler);
  await page.route('**/v1/analytics/storage-usage', storageHandler);
  await page.route('**/v1/settings/test-connection', testConnectionHandler);

  return async () => {
    await page.unroute('**/v1/settings', settingsHandler);
    await page.unroute('**/v1/analytics/cost-usage', costHandler);
    await page.unroute('**/v1/analytics/storage-usage', storageHandler);
    await page.unroute('**/v1/settings/test-connection', testConnectionHandler);
  };
}

test.describe('Modern Settings Page', () => {
  test('displays skeleton placeholders during loading', async ({ page }) => {
    const cleanup = await withSettingsRoutes(page, { delayMs: 1500 });

    try {
      await page.goto(SETTINGS_URL);

      await expect(page.getByLabel('Provider 配置加载中')).toBeVisible();
      await expect(page.getByLabel('WordPress 配置加载中')).toBeVisible();

      await expect(page.getByRole('heading', { name: '系统设置' })).toBeVisible();
      await expect(page.locator('[aria-label="Provider 配置加载中"]')).toHaveCount(0);
    } finally {
      await cleanup();
    }
  });

  test('shows validation errors and error styling on invalid input', async ({ page }) => {
    const cleanup = await withSettingsRoutes(page);

    try {
      await page.goto(SETTINGS_URL);
      const wordpressInput = page.getByLabel('WordPress URL');

      await wordpressInput.fill('invalid-url');
      await wordpressInput.blur();

      await expect(page.getByRole('alert', { name: '请输入合法的 URL' })).toBeVisible();
      const className = await wordpressInput.getAttribute('class');
      expect(className ?? '').toContain('border-error-500');
    } finally {
      await cleanup();
    }
  });

  test('shows success toast when settings save', async ({ page }) => {
    const cleanup = await withSettingsRoutes(page);

    try {
      await page.goto(SETTINGS_URL);

      await page.getByLabel('验证 SSL 证书').click();
      const saveButton = page.getByRole('button', { name: '保存设置' });
      await expect(saveButton).toBeEnabled();

      await saveButton.click();
      await expect(saveButton).toBeDisabled();
      await expect(page.getByText('保存成功！')).toBeVisible();
      await expect(page.getByText('设置已更新。')).toBeVisible();
    } finally {
      await cleanup();
    }
  });

  test('allows retry after failed save and shows error toast', async ({ page }) => {
    let putAttempt = 0;
    const cleanup = await withSettingsRoutes(page, {
      onPut: async route => {
        putAttempt += 1;
        if (putAttempt === 1) {
          await route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ message: 'Mock save failure' }),
          });
          return;
        }

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(baseSettingsResponse),
        });
      },
    });

    try {
      await page.goto(SETTINGS_URL);
      await page.getByLabel('验证 SSL 证书').click();

      await page.getByRole('button', { name: '保存设置' }).click();
      await expect(page.getByText('保存失败')).toBeVisible();

      const retryButton = page.getByRole('button', { name: '重试' });
      await expect(retryButton).toBeVisible();
      await retryButton.click();

      await expect(page.getByText('保存成功！')).toBeVisible();
      expect(putAttempt).toBeGreaterThanOrEqual(2);
    } finally {
      await cleanup();
    }
  });

  test('warns about unsaved changes when navigating away', async ({ page }) => {
    const cleanup = await withSettingsRoutes(page);

    try {
      await page.goto(SETTINGS_URL);

      const urlInput = page.getByLabel('WordPress URL');
      await urlInput.fill('https://new-domain.example');
      await urlInput.blur();

      await expect(page.getByText('未保存的更改')).toBeVisible();

      const navLink = page.locator('nav a:has-text("首頁")').first();
      await expect(navLink).toBeVisible();

      const dialogPromise = page.waitForEvent('dialog');
      await navLink.click();
      const dialog = await dialogPromise;
      expect(dialog.message()).toContain('未保存的更改');
      await dialog.dismiss();

      await expect(page).toHaveURL(/#\/settings$/);
      await expect(page.getByText('未保存的更改')).toBeVisible();
    } finally {
      await cleanup();
    }
  });
});
