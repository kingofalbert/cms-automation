import { z } from 'zod';
import type { TFunction } from 'i18next';

type FieldKey =
  | 'browser'
  | 'timeout'
  | 'retryCount'
  | 'model'
  | 'maxTokens'
  | 'screenshotInterval'
  | 'primaryProvider'
  | 'autoSwitchThreshold'
  | 'wordpressUrl'
  | 'username'
  | 'password'
  | 'maxRetries'
  | 'dailyLimit'
  | 'monthlyLimit'
  | 'perTaskLimit'
  | 'alertThreshold'
  | 'retentionDays'
  | 'maxScreenshots'
  | 'compressionQuality';

type UnitKey = 'milliseconds' | 'tokens' | 'percent' | 'usd' | 'days';

const fieldLabel = (t: TFunction, field: FieldKey) => t(`settings.fields.${field}`);
const unitLabel = (t: TFunction, unit?: UnitKey) =>
  unit ? ` ${t(`settings.units.${unit}`)}` : '';

const baseError = (t: TFunction, field: FieldKey) => ({
  required_error: t('settings.validation.required', { field: fieldLabel(t, field) }),
  invalid_type_error: t('settings.validation.invalid'),
});

const integerMessage = (t: TFunction, field: FieldKey) =>
  t('settings.validation.integer', { field: fieldLabel(t, field) });

const minMessage = (t: TFunction, field: FieldKey, value: number, unit?: UnitKey) =>
  t('settings.validation.minValue', {
    field: fieldLabel(t, field),
    value,
    unit: unitLabel(t, unit),
  });

const maxMessage = (t: TFunction, field: FieldKey, value: number, unit?: UnitKey) =>
  t('settings.validation.maxValue', {
    field: fieldLabel(t, field),
    value,
    unit: unitLabel(t, unit),
  });

const requiredMessage = (t: TFunction, field: FieldKey) =>
  t('settings.validation.required', { field: fieldLabel(t, field) });

export const createSettingsFormSchema = (t: TFunction) =>
  z.object({
    provider_config: z.object({
      playwright: z.object({
        enabled: z.boolean(),
        headless: z.boolean(),
        screenshot_on_error: z.boolean(),
        browser: z.enum(['chromium', 'firefox', 'webkit'], {
          required_error: requiredMessage(t, 'browser'),
        }),
        timeout: z
          .number(baseError(t, 'timeout'))
          .int(integerMessage(t, 'timeout'))
          .min(1000, minMessage(t, 'timeout', 1000, 'milliseconds'))
          .max(120000, maxMessage(t, 'timeout', 120000, 'milliseconds')),
        retry_count: z
          .number(baseError(t, 'retryCount'))
          .int(integerMessage(t, 'retryCount'))
          .min(0, minMessage(t, 'retryCount', 0))
          .max(5, maxMessage(t, 'retryCount', 5)),
      }),
      computer_use: z.object({
        enabled: z.boolean(),
        model: z
          .string(baseError(t, 'model'))
          .min(1, requiredMessage(t, 'model')),
        max_tokens: z
          .number(baseError(t, 'maxTokens'))
          .int(integerMessage(t, 'maxTokens'))
          .min(1024, minMessage(t, 'maxTokens', 1024, 'tokens'))
          .max(32768, maxMessage(t, 'maxTokens', 32768, 'tokens')),
        timeout: z
          .number(baseError(t, 'timeout'))
          .int(integerMessage(t, 'timeout'))
          .min(1000, minMessage(t, 'timeout', 1000, 'milliseconds'))
          .max(300000, maxMessage(t, 'timeout', 300000, 'milliseconds')),
        retry_count: z
          .number(baseError(t, 'retryCount'))
          .int(integerMessage(t, 'retryCount'))
          .min(0, minMessage(t, 'retryCount', 0))
          .max(5, maxMessage(t, 'retryCount', 5)),
        screenshot_interval: z
          .number(baseError(t, 'screenshotInterval'))
          .int(integerMessage(t, 'screenshotInterval'))
          .min(1000, minMessage(t, 'screenshotInterval', 1000, 'milliseconds'))
          .max(600000, maxMessage(t, 'screenshotInterval', 600000, 'milliseconds')),
      }),
      hybrid: z.object({
        enabled: z.boolean(),
        primary_provider: z.enum(['playwright', 'computer_use'], {
          required_error: requiredMessage(t, 'primaryProvider'),
        }),
        fallback_enabled: z.boolean(),
        fallback_on_error: z.boolean(),
        auto_switch_threshold: z
          .number(baseError(t, 'autoSwitchThreshold'))
          .int(integerMessage(t, 'autoSwitchThreshold'))
          .min(0, minMessage(t, 'autoSwitchThreshold', 0, 'percent'))
          .max(100, maxMessage(t, 'autoSwitchThreshold', 100, 'percent')),
      }),
    }),
    cms_config: z.object({
      wordpress_url: z
        .string(baseError(t, 'wordpressUrl'))
        .min(1, requiredMessage(t, 'wordpressUrl'))
        .url(t('settings.validation.invalidUrl')),
      username: z
        .string(baseError(t, 'username'))
        .min(1, requiredMessage(t, 'username')),
      password: z
        .string(baseError(t, 'password'))
        .min(1, requiredMessage(t, 'password')),
      verify_ssl: z.boolean(),
      timeout: z
        .number(baseError(t, 'timeout'))
        .int(integerMessage(t, 'timeout'))
        .min(1000, minMessage(t, 'timeout', 1000, 'milliseconds'))
        .max(120000, maxMessage(t, 'timeout', 120000, 'milliseconds')),
      max_retries: z
        .number(baseError(t, 'maxRetries'))
        .int(integerMessage(t, 'maxRetries'))
        .min(0, minMessage(t, 'maxRetries', 0))
        .max(5, maxMessage(t, 'maxRetries', 5)),
    }),
    cost_limits: z.object({
      daily_limit: z
        .number(baseError(t, 'dailyLimit'))
        .min(0, minMessage(t, 'dailyLimit', 0, 'usd'))
        .max(100000, maxMessage(t, 'dailyLimit', 100000, 'usd')),
      monthly_limit: z
        .number(baseError(t, 'monthlyLimit'))
        .min(0, minMessage(t, 'monthlyLimit', 0, 'usd'))
        .max(1000000, maxMessage(t, 'monthlyLimit', 1000000, 'usd')),
      per_task_limit: z
        .number(baseError(t, 'perTaskLimit'))
        .min(0, minMessage(t, 'perTaskLimit', 0, 'usd'))
        .max(50000, maxMessage(t, 'perTaskLimit', 50000, 'usd')),
      alert_threshold: z
        .number(baseError(t, 'alertThreshold'))
        .int(integerMessage(t, 'alertThreshold'))
        .min(0, minMessage(t, 'alertThreshold', 0, 'percent'))
        .max(100, maxMessage(t, 'alertThreshold', 100, 'percent')),
      auto_pause_on_limit: z.boolean(),
    }),
    screenshot_retention: z.object({
      retention_days: z
        .number(baseError(t, 'retentionDays'))
        .int(integerMessage(t, 'retentionDays'))
        .min(1, minMessage(t, 'retentionDays', 1, 'days'))
        .max(365, maxMessage(t, 'retentionDays', 365, 'days')),
      max_screenshots_per_task: z
        .number(baseError(t, 'maxScreenshots'))
        .int(integerMessage(t, 'maxScreenshots'))
        .min(1, minMessage(t, 'maxScreenshots', 1))
        .max(100, maxMessage(t, 'maxScreenshots', 100)),
      compress_screenshots: z.boolean(),
      compression_quality: z
        .number(baseError(t, 'compressionQuality'))
        .int(integerMessage(t, 'compressionQuality'))
        .min(10, minMessage(t, 'compressionQuality', 10, 'percent'))
        .max(100, maxMessage(t, 'compressionQuality', 100, 'percent')),
      delete_on_success: z.boolean(),
      delete_on_failure: z.boolean(),
    }),
    updated_at: z.string().optional(),
  });

export type SettingsFormSchema = ReturnType<typeof createSettingsFormSchema>;
export type SettingsFormValues = z.infer<SettingsFormSchema>;
