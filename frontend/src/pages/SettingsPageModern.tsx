/**
 * Modern Settings Page - Completely redesigned with better UX
 * Features: Accordion layout, Toast notifications, improved visual hierarchy
 */

import { useEffect, useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { api } from '@/services/api-client';
import {
  Accordion,
  AccordionItem,
  Button,
  Skeleton,
  SkeletonSettingsSection,
} from '@/components/ui';
import { ProviderConfigSection } from '@/components/Settings/ProviderConfigSection';
import { CMSConfigSection } from '@/components/Settings/CMSConfigSection';
import { CostLimitsSection } from '@/components/Settings/CostLimitsSection';
import { ScreenshotRetentionSection } from '@/components/Settings/ScreenshotRetentionSection';
import { AppSettings, SettingsUpdateRequest } from '@/types/settings';
import {
  Save,
  RotateCcw,
  Monitor,
  Globe,
  DollarSign,
  Camera,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import { toast } from 'sonner';
import {
  settingsFormSchema,
  type SettingsFormValues,
} from '@/schemas/settings-schema';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';

const createDefaultSettings = (): SettingsFormValues => ({
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
      model: 'claude-3-5-sonnet-20241022',
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
    wordpress_url: '',
    username: '',
    password: '',
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
  updated_at: '',
});

const buildDefaultSettings = (settings?: AppSettings | null): SettingsFormValues => {
  const defaults = createDefaultSettings();

  if (!settings) {
    return defaults;
  }

  return {
    provider_config: {
      playwright: {
        enabled:
          settings.provider_config?.playwright?.enabled ??
          defaults.provider_config.playwright.enabled,
        headless:
          settings.provider_config?.playwright?.headless ??
          defaults.provider_config.playwright.headless,
        screenshot_on_error:
          settings.provider_config?.playwright?.screenshot_on_error ??
          defaults.provider_config.playwright.screenshot_on_error,
        browser:
          settings.provider_config?.playwright?.browser ??
          defaults.provider_config.playwright.browser,
        timeout:
          settings.provider_config?.playwright?.timeout ??
          defaults.provider_config.playwright.timeout,
        retry_count:
          settings.provider_config?.playwright?.retry_count ??
          defaults.provider_config.playwright.retry_count,
      },
      computer_use: {
        enabled:
          settings.provider_config?.computer_use?.enabled ??
          defaults.provider_config.computer_use.enabled,
        model:
          settings.provider_config?.computer_use?.model ??
          defaults.provider_config.computer_use.model,
        max_tokens:
          settings.provider_config?.computer_use?.max_tokens ??
          defaults.provider_config.computer_use.max_tokens,
        timeout:
          settings.provider_config?.computer_use?.timeout ??
          defaults.provider_config.computer_use.timeout,
        retry_count:
          settings.provider_config?.computer_use?.retry_count ??
          defaults.provider_config.computer_use.retry_count,
        screenshot_interval:
          settings.provider_config?.computer_use?.screenshot_interval ??
          defaults.provider_config.computer_use.screenshot_interval,
      },
      hybrid: {
        enabled:
          settings.provider_config?.hybrid?.enabled ??
          defaults.provider_config.hybrid.enabled,
        primary_provider:
          settings.provider_config?.hybrid?.primary_provider ??
          defaults.provider_config.hybrid.primary_provider,
        fallback_enabled:
          settings.provider_config?.hybrid?.fallback_enabled ??
          defaults.provider_config.hybrid.fallback_enabled,
        fallback_on_error:
          settings.provider_config?.hybrid?.fallback_on_error ??
          defaults.provider_config.hybrid.fallback_on_error,
        auto_switch_threshold:
          settings.provider_config?.hybrid?.auto_switch_threshold ??
          defaults.provider_config.hybrid.auto_switch_threshold,
      },
    },
    cms_config: {
      wordpress_url:
        settings.cms_config?.wordpress_url ?? defaults.cms_config.wordpress_url,
      username: settings.cms_config?.username ?? defaults.cms_config.username,
      password: settings.cms_config?.password ?? defaults.cms_config.password,
      verify_ssl: settings.cms_config?.verify_ssl ?? defaults.cms_config.verify_ssl,
      timeout: settings.cms_config?.timeout ?? defaults.cms_config.timeout,
      max_retries: settings.cms_config?.max_retries ?? defaults.cms_config.max_retries,
    },
    cost_limits: {
      daily_limit:
        settings.cost_limits?.daily_limit ?? defaults.cost_limits.daily_limit,
      monthly_limit:
        settings.cost_limits?.monthly_limit ?? defaults.cost_limits.monthly_limit,
      per_task_limit:
        settings.cost_limits?.per_task_limit ?? defaults.cost_limits.per_task_limit,
      alert_threshold:
        settings.cost_limits?.alert_threshold ?? defaults.cost_limits.alert_threshold,
      auto_pause_on_limit:
        settings.cost_limits?.auto_pause_on_limit ??
        defaults.cost_limits.auto_pause_on_limit,
    },
    screenshot_retention: {
      retention_days:
        settings.screenshot_retention?.retention_days ??
        defaults.screenshot_retention.retention_days,
      max_screenshots_per_task:
        settings.screenshot_retention?.max_screenshots_per_task ??
        defaults.screenshot_retention.max_screenshots_per_task,
      compress_screenshots:
        settings.screenshot_retention?.compress_screenshots ??
        defaults.screenshot_retention.compress_screenshots,
      compression_quality:
        settings.screenshot_retention?.compression_quality ??
        defaults.screenshot_retention.compression_quality,
      delete_on_success:
        settings.screenshot_retention?.delete_on_success ??
        defaults.screenshot_retention.delete_on_success,
      delete_on_failure:
        settings.screenshot_retention?.delete_on_failure ??
        defaults.screenshot_retention.delete_on_failure,
    },
    updated_at: settings.updated_at ?? defaults.updated_at,
  };
};

export default function SettingsPageModern() {
  const defaultValues = useMemo(() => buildDefaultSettings(null), []);
  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsFormSchema),
    mode: 'onBlur',
    reValidateMode: 'onBlur',
    defaultValues,
  });
  const {
    formState: { isDirty, isSubmitting },
    watch,
    reset,
  } = form;

  // Fetch settings
  const { data: settings, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['app-settings'],
    queryFn: async () => {
      const response = await api.get<AppSettings | { error: boolean; message?: string }>(
        'v1/settings'
      );

      if ('error' in response && response.error) {
        throw new Error(response.message || 'Failed to load settings');
      }

      return response as AppSettings;
    },
    retry: 2,
    retryDelay: 1000,
  });

  useEffect(() => {
    if (settings) {
      reset(buildDefaultSettings(settings), { keepDirty: false });
    }
  }, [settings, reset]);

  const updateMutation = useMutation({
    mutationFn: async (updates: SettingsUpdateRequest) => {
      const response = await api.put<AppSettings>('v1/settings', updates);
      return response;
    },
    onSuccess: (data) => {
      reset(buildDefaultSettings(data), { keepDirty: false });
      refetch();
    },
  });

  const testConnection = async (overrideConfig?: SettingsFormValues['cms_config']) => {
    const cmsConfig = overrideConfig ?? form.getValues('cms_config');

    try {
      const response = await api.post<{ success: boolean }>('v1/settings/test-connection', {
        cms_config: cmsConfig,
      });
      return response.success;
    } catch {
      return false;
    }
  };

  // Fetch cost usage
  const { data: costUsage } = useQuery({
    queryKey: ['cost-usage'],
    queryFn: async () => {
      const response = await api.get<{
        daily_spend: number;
        monthly_spend: number;
      }>('v1/analytics/cost-usage');
      return response;
    },
    enabled: false,
    refetchInterval: 60000,
  });

  // Fetch storage usage
  const { data: storageUsage } = useQuery({
    queryKey: ['storage-usage'],
    queryFn: async () => {
      const response = await api.get<{ total_mb: number }>(
        'v1/analytics/storage-usage'
      );
      return response;
    },
  });

  const resolveErrorMessage = (error: unknown) => {
    if (
      typeof error === 'object' &&
      error !== null &&
      'response' in error &&
      (error as { response?: { data?: { message?: string } } }).response
    ) {
      const response = (error as { response?: { data?: { message?: string } } }).response;
      const message = response?.data?.message;
      if (typeof message === 'string' && message.trim().length > 0) {
        return message;
      }
    }
    if (error instanceof Error) {
      return error.message;
    }
    return '保存失败，请稍后再试。';
  };

  const onSubmit = async (values: SettingsFormValues) => {
    const updates: SettingsUpdateRequest = {
      provider_config: values.provider_config,
      cms_config: values.cms_config,
      cost_limits: values.cost_limits,
      screenshot_retention: values.screenshot_retention,
    };

    const mutationPromise = updateMutation.mutateAsync(updates);

    toast.promise(mutationPromise, {
      loading: '保存设置中...',
      success: {
        message: '保存成功！',
        description: '设置已更新。',
      },
      error: (error) => ({
        message: '保存失败',
        description: resolveErrorMessage(error),
        action: {
          label: '重试',
          onClick: () => {
            void form.handleSubmit(onSubmit)();
          },
        },
      }),
    });

    try {
      await mutationPromise;
    } catch (error) {
      console.error('Failed to save settings:', error);
      throw error;
    }
  };

  const handleSave = form.handleSubmit(onSubmit);

  const handleReset = () => {
    if (settings) {
      reset(buildDefaultSettings(settings), { keepDirty: false });
    } else {
      reset(buildDefaultSettings(null), { keepDirty: false });
    }
  };

  const hasChanges = isDirty;
  const unsavedPromptMessage = '您有未保存的更改，确认要离开当前页面吗？';
  useUnsavedChanges({ when: hasChanges, message: unsavedPromptMessage });
  const isSaving = isSubmitting || updateMutation.isPending;
  const updatedAt = watch('updated_at');
  const formattedUpdatedAt =
    updatedAt && updatedAt.length > 0
      ? new Date(updatedAt).toLocaleString('zh-CN', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })
      : '暂无更新时间';

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-50 to-primary-50/20">
        <div className="sticky top-0 z-40 border-b border-gray-200 bg-white shadow-sm">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
            <div className="flex items-center gap-4">
              <Skeleton shape="circle" width={48} height={48} />
              <div className="space-y-2">
                <Skeleton width="200px" height={24} />
                <Skeleton shape="text" lines={1} lineWidths={['240px']} />
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Skeleton width={130} height={44} radius="lg" />
              <Skeleton width={160} height={44} radius="lg" />
            </div>
          </div>
        </div>

        <div className="mx-auto max-w-7xl space-y-6 px-6 py-8">
          <SkeletonSettingsSection
            fieldCount={6}
            hasTabs
            showIcon
            aria-label="Provider 配置加载中"
          />
          <SkeletonSettingsSection
            fieldCount={4}
            showIcon
            aria-label="WordPress 配置加载中"
          />
          <SkeletonSettingsSection
            fieldCount={4}
            showIcon
            aria-label="成本限额加载中"
          />
          <SkeletonSettingsSection
            fieldCount={5}
            showIcon
            aria-label="截图保留策略加载中"
          />
          <div className="mt-12 border-t border-gray-200 pt-8 text-center">
            <Skeleton
              shape="text"
              lines={1}
              lineWidths={['220px']}
              aria-label="最后更新时间加载中"
            />
          </div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="mx-4 w-full max-w-md">
          <div className="rounded-2xl bg-white p-8 text-center shadow-xl">
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-error-100">
              <AlertCircle className="h-8 w-8 text-error-600" />
            </div>
            <h2 className="mb-3 text-2xl font-bold text-gray-900">无法加载设置</h2>
            <p className="mb-8 text-gray-600">
              {error instanceof Error
                ? error.message
                : '连接到后端服务失败。请确保后端服务正在运行。'}
            </p>
            <Button onClick={() => refetch()} variant="primary" size="lg" fullWidth>
              <RotateCcw className="mr-2 h-5 w-5" />
              重新加载
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <FormProvider {...form}>
      <form
        onSubmit={handleSave}
        noValidate
        className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-50 to-primary-50/20"
      >
        <div className="sticky top-0 z-40 border-b border-gray-200 bg-white shadow-sm">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 shadow-lg">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">系统设置</h1>
                <p className="mt-1 text-sm text-gray-500">配置您的 CMS 自动化系统</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {hasChanges && (
                <div className="animate-in fade-in duration-200 rounded-lg border border-warning-200 bg-warning-50 px-4 py-2 text-sm font-medium text-warning-700">
                  未保存的更改
                </div>
              )}
              <Button
                variant="outline"
                type="button"
                onClick={handleReset}
                disabled={!hasChanges || isSaving}
                size="md"
              >
                <RotateCcw className="mr-2 h-4 w-4" />
                重置
              </Button>
              <Button
                variant="primary"
                type="submit"
                disabled={!hasChanges || isSaving}
                isLoading={isSaving}
                size="md"
              >
                <Save className="mr-2 h-4 w-4" />
                {isSaving ? '保存中...' : '保存设置'}
              </Button>
            </div>
          </div>
        </div>

        <div className="mx-auto max-w-7xl px-6 py-8">
          {hasChanges && (
            <div className="mb-8 flex flex-col gap-3 rounded-xl border border-warning-200 bg-warning-50 px-4 py-3 text-warning-800 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-start gap-3">
                <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-semibold">检测到未保存的更改</p>
                  <p className="text-sm text-warning-700/90">
                    请保存后再离开，避免丢失您的设置。
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Button
                  variant="ghost"
                  size="sm"
                  type="button"
                  onClick={handleReset}
                  disabled={isSaving}
                >
                  丢弃更改
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                  disabled={isSaving}
                  isLoading={isSaving}
                >
                  立即保存
                </Button>
              </div>
            </div>
          )}

          <Accordion spacing="lg">
            <AccordionItem
              title="Provider 配置"
              subtitle="配置 Playwright、Computer Use 和 Hybrid 发布方式"
              icon={<Monitor className="h-5 w-5" />}
              defaultOpen
            >
              <ProviderConfigSection />
            </AccordionItem>

            <AccordionItem
              title="WordPress 配置"
              subtitle="配置 WordPress 站点连接信息"
              icon={<Globe className="h-5 w-5" />}
            >
              <CMSConfigSection onTestConnection={testConnection} />
            </AccordionItem>

            <AccordionItem
              title="成本限额"
              subtitle="设置每日和每月的支出限额"
              icon={<DollarSign className="h-5 w-5" />}
            >
              <CostLimitsSection
                currentDailySpend={costUsage?.daily_spend ?? 0}
                currentMonthlySpend={costUsage?.monthly_spend ?? 0}
              />
            </AccordionItem>

            <AccordionItem
              title="截图保留策略"
              subtitle="配置截图自动清理规则"
              icon={<Camera className="h-5 w-5" />}
            >
              <ScreenshotRetentionSection
                estimatedStorageUsage={storageUsage?.total_mb ?? 0}
              />
            </AccordionItem>
          </Accordion>

          <div className="mt-12 border-t border-gray-200 pt-8 text-center">
            <p className="text-sm text-gray-500">最后更新: {formattedUpdatedAt}</p>
          </div>
        </div>
      </form>
    </FormProvider>
  );
}
