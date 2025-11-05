import { z } from 'zod';

const baseError = {
  required_error: '此字段为必填项',
  invalid_type_error: '输入的格式不正确',
};

export const playWrightConfigSchema = z.object({
  enabled: z.boolean(),
  headless: z.boolean(),
  screenshot_on_error: z.boolean(),
  browser: z.enum(['chromium', 'firefox', 'webkit'], {
    required_error: '请选择浏览器类型',
  }),
  timeout: z
    .number(baseError)
    .int('必须为整数')
    .min(1000, '超时时间不能低于 1000 毫秒')
    .max(120000, '超时时间不能超过 120000 毫秒'),
  retry_count: z
    .number(baseError)
    .int('必须为整数')
    .min(0, '重试次数不能小于 0')
    .max(5, '重试次数不能超过 5'),
});

export const computerUseConfigSchema = z.object({
  enabled: z.boolean(),
  model: z.string(baseError).min(1, '模型名称不能为空'),
  max_tokens: z
    .number(baseError)
    .int('必须为整数')
    .min(1024, '最大 Tokens 不能低于 1024')
    .max(32768, '最大 Tokens 不能超过 32768'),
  timeout: z
    .number(baseError)
    .int('必须为整数')
    .min(1000, '超时时间不能低于 1000 毫秒')
    .max(300000, '超时时间不能超过 300000 毫秒'),
  retry_count: z
    .number(baseError)
    .int('必须为整数')
    .min(0, '重试次数不能小于 0')
    .max(5, '重试次数不能超过 5'),
  screenshot_interval: z
    .number(baseError)
    .int('必须为整数')
    .min(1000, '截图间隔不能低于 1000 毫秒')
    .max(600000, '截图间隔不能超过 600000 毫秒'),
});

export const hybridConfigSchema = z.object({
  enabled: z.boolean(),
  primary_provider: z.enum(['playwright', 'computer_use'], {
    required_error: '请选择主 Provider',
    invalid_type_error: '请选择主 Provider',
  }),
  fallback_enabled: z.boolean(),
  fallback_on_error: z.boolean(),
  auto_switch_threshold: z
    .number(baseError)
    .int('必须为整数')
    .min(0, '阈值不能小于 0')
    .max(100, '阈值不能超过 100'),
});

export const providerConfigSchema = z.object({
  playwright: playWrightConfigSchema,
  computer_use: computerUseConfigSchema,
  hybrid: hybridConfigSchema,
});

export const cmsConfigSchema = z.object({
  wordpress_url: z
    .string(baseError)
    .min(1, 'WordPress URL 不能为空')
    .url('请输入合法的 URL'),
  username: z.string(baseError).min(1, '用户名不能为空'),
  password: z.string(baseError).min(1, '密码不能为空'),
  verify_ssl: z.boolean(),
  timeout: z
    .number(baseError)
    .int('必须为整数')
    .min(1000, '超时时间不能低于 1000 毫秒')
    .max(120000, '超时时间不能超过 120000 毫秒'),
  max_retries: z
    .number(baseError)
    .int('必须为整数')
    .min(0, '重试次数不能小于 0')
    .max(5, '重试次数不能超过 5'),
});

export const costLimitsSchema = z.object({
  daily_limit: z
    .number(baseError)
    .min(0, '每日限额不能小于 0')
    .max(100000, '每日限额过高'),
  monthly_limit: z
    .number(baseError)
    .min(0, '每月限额不能小于 0')
    .max(1000000, '每月限额过高'),
  per_task_limit: z
    .number(baseError)
    .min(0, '单任务限额不能小于 0')
    .max(50000, '单任务限额过高'),
  alert_threshold: z
    .number(baseError)
    .int('必须为整数')
    .min(0, '预警阈值不能小于 0')
    .max(100, '预警阈值不能超过 100'),
  auto_pause_on_limit: z.boolean(),
});

export const screenshotRetentionSchema = z.object({
  retention_days: z
    .number(baseError)
    .int('必须为整数')
    .min(1, '保留天数至少为 1 天')
    .max(365, '保留天数不能超过 365 天'),
  max_screenshots_per_task: z
    .number(baseError)
    .int('必须为整数')
    .min(1, '每任务截图数至少为 1')
    .max(100, '每任务截图数不能超过 100'),
  compress_screenshots: z.boolean(),
  compression_quality: z
    .number(baseError)
    .int('必须为整数')
    .min(10, '压缩质量不能低于 10')
    .max(100, '压缩质量不能超过 100'),
  delete_on_success: z.boolean(),
  delete_on_failure: z.boolean(),
});

export const settingsFormSchema = z.object({
  provider_config: providerConfigSchema,
  cms_config: cmsConfigSchema,
  cost_limits: costLimitsSchema,
  screenshot_retention: screenshotRetentionSchema,
  updated_at: z.string().optional(),
});

export type SettingsFormValues = z.infer<typeof settingsFormSchema>;
