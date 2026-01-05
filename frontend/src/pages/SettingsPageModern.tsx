/**
 * Modern Settings Page - Completely redesigned with better UX
 * Features: Accordion layout, Toast notifications, improved visual hierarchy
 */

import { useEffect, useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useTranslation } from 'react-i18next';
import { api } from '@/services/api-client';
import {
  Accordion,
  AccordionItem,
  Button,
  Skeleton,
} from '@/components/ui';
import { ProviderConfigSection } from '@/components/Settings/ProviderConfigSection';
import { CostLimitsSection } from '@/components/Settings/CostLimitsSection';
import { ProofreadingRulesSection } from '@/components/Settings/ProofreadingRulesSection';
// Hidden in Phase 1:
// import { CMSConfigSection } from '@/components/Settings/CMSConfigSection';
// import { ScreenshotRetentionSection } from '@/components/Settings/ScreenshotRetentionSection';
// import { TagManagementSection } from '@/components/Settings/TagManagementSection';
import { AppSettings, SettingsUpdateRequest } from '@/types/settings';
import {
  Save,
  RotateCcw,
  Monitor,
  DollarSign,
  AlertCircle,
  Sparkles,
  CheckCircle,
  ChevronsUpDown,
  // Hidden in Phase 1: Globe, Camera, Tag
} from 'lucide-react';
import { toast } from 'sonner';
import {
  createSettingsFormSchema,
  type SettingsFormValues,
} from '@/schemas/settings-schema';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';
import { useAccordionState } from '@/hooks/useAccordionState';

// Accordion section IDs for state management
const SETTINGS_ACCORDION_SECTIONS = ['provider', 'cost', 'proofreading'] as const;

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
      // Map backend field names to frontend form field names
      wordpress_url:
        (settings.cms_config as any)?.base_url ?? defaults.cms_config.wordpress_url,
      username: settings.cms_config?.username ?? defaults.cms_config.username,
      password: (settings.cms_config as any)?.application_password ?? defaults.cms_config.password,
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
        // API returns 0-1 decimal, form uses 0-100 percentage
        settings.cost_limits?.alert_threshold !== undefined
          ? settings.cost_limits.alert_threshold <= 1
            ? Math.round(settings.cost_limits.alert_threshold * 100)
            : settings.cost_limits.alert_threshold
          : defaults.cost_limits.alert_threshold,
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
  const { t, i18n } = useTranslation();
  const defaultValues = useMemo(() => buildDefaultSettings(null), []);
  const validationSchema = useMemo(() => createSettingsFormSchema(t), [t]);
  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(validationSchema),
    mode: 'onBlur',
    reValidateMode: 'onBlur',
    defaultValues,
  });
  const {
    formState: { isDirty, isSubmitting },
    watch,
    reset,
  } = form;

  // Accordion state with localStorage persistence
  const accordionState = useAccordionState({
    storageKey: 'cms-settings-accordion-state',
    defaultOpenSections: ['provider'], // Provider section open by default
    sectionIds: [...SETTINGS_ACCORDION_SECTIONS],
  });

  // Fetch settings
  const { data: settings, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['app-settings'],
    queryFn: async () => {
      const response = await api.get<AppSettings | { error: boolean; message?: string }>(
        '/v1/settings'
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
      const response = await api.put<AppSettings>('/v1/settings', updates);
      return response;
    },
    onSuccess: (data) => {
      reset(buildDefaultSettings(data), { keepDirty: false });
      refetch();
    },
  });

  // Disabled in Phase 1 - CMS Config hidden
  // const testConnection = async (overrideConfig?: SettingsFormValues['cms_config']) => {
  //   const cmsConfig = overrideConfig ?? form.getValues('cms_config');
  //
  //   try {
  //     const response = await api.post<{ success: boolean }>(
  //       '/v1/settings/test-connection',
  //       {
  //         cms_type: 'wordpress',
  //         base_url: cmsConfig.wordpress_url,
  //         username: cmsConfig.username,
  //         application_password: cmsConfig.password,
  //       }
  //     );
  //     return response.success;
  //   } catch {
  //     return false;
  //   }
  // };

  // Fetch cost usage
  const { data: costUsage } = useQuery({
    queryKey: ['cost-usage'],
    queryFn: async () => {
      const response = await api.get<{
        daily_spend: number;
        monthly_spend: number;
      }>('/v1/analytics/cost-usage');
      return response;
    },
    enabled: false,
    refetchInterval: 60000,
  });

  // Disabled in Phase 1 - Screenshot Retention hidden
  // const { data: storageUsage } = useQuery({
  //   queryKey: ['storage-usage'],
  //   queryFn: async () => {
  //     const response = await api.get<{ total_mb: number }>(
  //       '/v1/analytics/storage-usage'
  //     );
  //     return response;
  //   },
  // });

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
    return t('settings.messages.genericError');
  };

  const onSubmit = async (values: SettingsFormValues) => {
    // Map frontend field names back to backend field names
    const updates: SettingsUpdateRequest = {
      provider_config: values.provider_config,
      cms_config: {
        ...(values.cms_config.wordpress_url && { base_url: values.cms_config.wordpress_url }),
        ...(values.cms_config.username && { username: values.cms_config.username }),
        ...(values.cms_config.password && { application_password: values.cms_config.password }),
        ...(values.cms_config.verify_ssl !== undefined && { verify_ssl: values.cms_config.verify_ssl }),
        ...(values.cms_config.timeout && { timeout: values.cms_config.timeout }),
        ...(values.cms_config.max_retries !== undefined && { max_retries: values.cms_config.max_retries }),
      } as any,
      cost_limits: {
        ...values.cost_limits,
        // Convert percentage (0-100) back to decimal (0-1) for API
        alert_threshold: values.cost_limits.alert_threshold / 100,
      },
      screenshot_retention: values.screenshot_retention,
    };

    const mutationPromise = updateMutation.mutateAsync(updates);

    toast.promise(mutationPromise, {
      loading: t('settings.messages.saveInProgress'),
      success: {
        message: t('settings.messages.saveSuccessTitle'),
        description: t('settings.messages.saveSuccessDescription'),
      },
      error: (error) => ({
        message: t('settings.messages.saveErrorTitle'),
        description: resolveErrorMessage(error),
        action: {
          label: t('settings.messages.retry'),
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
  const unsavedPromptMessage = t('settings.messages.unsavedPrompt');
  useUnsavedChanges({ when: hasChanges, message: unsavedPromptMessage });
  const isSaving = isSubmitting || updateMutation.isPending;
  const updatedAt = watch('updated_at');
  const locale = i18n.language === 'en-US' ? 'en-US' : 'zh-TW';
  const formattedUpdatedAt =
    updatedAt && updatedAt.length > 0
      ? new Date(updatedAt).toLocaleString(locale, {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })
      : t('settings.messages.noUpdateTime');

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-50 to-primary-50/20">
        <div className="sticky top-0 z-40 border-b border-gray-200 bg-white shadow-sm">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
            <div className="flex items-center gap-4">
              <Skeleton className="h-12 w-12 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-4 w-60" />
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Skeleton className="h-11 w-32" />
              <Skeleton className="h-11 w-40" />
            </div>
          </div>
        </div>

        <div className="mx-auto max-w-7xl space-y-6 px-6 py-8">
          <div className="space-y-4">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-64 w-full" />
          </div>
          <div className="space-y-4">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-48 w-full" />
          </div>
          <div className="space-y-4">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-48 w-full" />
          </div>
          <div className="space-y-4">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-56 w-full" />
          </div>
          <div className="mt-12 border-t border-gray-200 pt-8 text-center">
            <Skeleton className="h-4 w-56 mx-auto" />
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
            <h2 className="mb-3 text-2xl font-bold text-gray-900">
              {t('settings.errors.loadFailedTitle')}
            </h2>
            <p className="mb-8 text-gray-600">
              {error instanceof Error
                ? error.message
                : t('settings.errors.loadFailedDescription')}
            </p>
            <Button onClick={() => refetch()} variant="primary" size="lg" fullWidth>
              <RotateCcw className="mr-2 h-5 w-5" />
              {t('settings.errors.reload')}
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
                <h1 className="text-2xl font-bold text-gray-900">{t('settings.title')}</h1>
                <p className="mt-1 text-sm text-gray-500">{t('settings.subtitle')}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {hasChanges && (
                <div className="animate-in fade-in duration-200 rounded-lg border border-warning-200 bg-warning-50 px-4 py-2 text-sm font-medium text-warning-700">
                  {t('settings.messages.unsavedBadge')}
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
                {t('settings.actions.reset')}
              </Button>
              <Button
                variant="primary"
                type="submit"
                disabled={!hasChanges || isSaving}
                isLoading={isSaving}
                size="md"
              >
                <Save className="mr-2 h-4 w-4" />
                {isSaving ? t('settings.actions.saving') : t('settings.actions.saveSettings')}
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
                  <p className="text-sm font-semibold">
                    {t('settings.messages.unsavedDetected')}
                  </p>
                  <p className="text-sm text-warning-700/90">
                    {t('settings.messages.unsavedReminder')}
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
                  {t('settings.actions.discardChanges')}
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                  disabled={isSaving}
                  isLoading={isSaving}
                >
                  {t('settings.actions.saveNow')}
                </Button>
              </div>
            </div>
          )}

          {/* Expand/Collapse All Controls */}
          <div className="flex justify-end gap-2 mb-4">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={accordionState.expandAll}
              className="text-gray-600"
            >
              <ChevronsUpDown className="h-4 w-4 mr-1" />
              {t('settings.accordion.expandAll')}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={accordionState.collapseAll}
              className="text-gray-600"
            >
              <ChevronsUpDown className="h-4 w-4 mr-1 rotate-90" />
              {t('settings.accordion.collapseAll')}
            </Button>
          </div>

          <Accordion spacing="lg">
            <AccordionItem
              title={t('settings.accordion.provider.title')}
              subtitle={t('settings.accordion.provider.subtitle')}
              icon={<Monitor className="h-5 w-5" />}
              isOpen={accordionState.isOpen('provider')}
              onToggle={() => accordionState.toggle('provider')}
            >
              <ProviderConfigSection />
            </AccordionItem>

            {/* WordPress Configuration - Hidden in Phase 1 */}
            {/* <AccordionItem
              title={t('settings.accordion.cms.title')}
              subtitle={t('settings.accordion.cms.subtitle')}
              icon={<Globe className="h-5 w-5" />}
            >
              <CMSConfigSection onTestConnection={testConnection} />
            </AccordionItem> */}

            <AccordionItem
              title={t('settings.accordion.cost.title')}
              subtitle={t('settings.accordion.cost.subtitle')}
              icon={<DollarSign className="h-5 w-5" />}
              isOpen={accordionState.isOpen('cost')}
              onToggle={() => accordionState.toggle('cost')}
            >
              <CostLimitsSection
                currentDailySpend={costUsage?.daily_spend ?? 0}
                currentMonthlySpend={costUsage?.monthly_spend ?? 0}
              />
            </AccordionItem>

            {/* Screenshot Retention - Hidden in Phase 1 */}
            {/* <AccordionItem
              title={t('settings.accordion.screenshot.title')}
              subtitle={t('settings.accordion.screenshot.subtitle')}
              icon={<Camera className="h-5 w-5" />}
            >
              <ScreenshotRetentionSection
                estimatedStorageUsage={storageUsage?.total_mb ?? 0}
              />
            </AccordionItem> */}

            <AccordionItem
              title={t('settings.sections.proofreading')}
              subtitle={t('settings.proofreading.subtitle')}
              icon={<CheckCircle className="h-5 w-5" />}
              isOpen={accordionState.isOpen('proofreading')}
              onToggle={() => accordionState.toggle('proofreading')}
            >
              <ProofreadingRulesSection />
            </AccordionItem>

            {/* Tag Management - Hidden in Phase 1 */}
            {/* <AccordionItem
              title={t('settings.sections.tags')}
              subtitle={t('settings.tags.subtitle')}
              icon={<Tag className="h-5 w-5" />}
            >
              <TagManagementSection />
            </AccordionItem> */}
          </Accordion>

          <div className="mt-12 border-t border-gray-200 pt-8 text-center">
            <p className="text-sm text-gray-500">
              {t('settings.messages.lastUpdated', { timestamp: formattedUpdatedAt })}
            </p>
          </div>
        </div>
      </form>
    </FormProvider>
  );
}
