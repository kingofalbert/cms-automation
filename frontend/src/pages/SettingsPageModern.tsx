/**
 * Modern Settings Page - Completely redesigned with better UX
 * Features: Accordion layout, Toast notifications, improved visual hierarchy
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/services/api-client';
import { Accordion, AccordionItem, Button } from '@/components/ui';
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
  CheckCircle2,
  AlertCircle,
  Sparkles
} from 'lucide-react';

export default function SettingsPageModern() {
  const [hasChanges, setHasChanges] = useState(false);
  const [localSettings, setLocalSettings] = useState<AppSettings | null>(null);
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const [showErrorToast, setShowErrorToast] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Fetch settings
  const { data: settings, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['app-settings'],
    queryFn: async () => {
      const response = await api.get<AppSettings>('v1/settings');

      if (response && 'error' in response) {
        throw new Error((response as any).message || 'Failed to load settings');
      }

      return response;
    },
    retry: 2,
    retryDelay: 1000,
  });

  useEffect(() => {
    if (settings) {
      setLocalSettings(settings);
      setHasChanges(false);
    }
  }, [settings]);

  // Update settings mutation
  const updateMutation = useMutation({
    mutationFn: async (updates: SettingsUpdateRequest) => {
      const response = await api.put<AppSettings>('v1/settings', updates);
      return response;
    },
    onSuccess: () => {
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 3000);
      refetch();
      setHasChanges(false);
    },
    onError: (error: any) => {
      setErrorMessage(error.response?.data?.message || error.message || '保存失败');
      setShowErrorToast(true);
      setTimeout(() => setShowErrorToast(false), 5000);
    },
  });

  // Test WordPress connection
  const testConnection = async () => {
    if (!localSettings) return false;

    try {
      const response = await api.post<{ success: boolean }>('v1/settings/test-connection', {
        cms_config: localSettings.cms_config,
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

  const handleSave = () => {
    if (!localSettings) return;

    const updates: SettingsUpdateRequest = {
      provider_config: localSettings.provider_config,
      cms_config: localSettings.cms_config,
      cost_limits: localSettings.cost_limits,
      screenshot_retention: localSettings.screenshot_retention,
    };

    updateMutation.mutate(updates);
  };

  const handleReset = () => {
    if (settings) {
      setLocalSettings(settings);
      setHasChanges(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-6">
            <div className="absolute inset-0 rounded-full border-4 border-primary-200 animate-ping" />
            <div className="relative w-16 h-16 rounded-full border-4 border-primary-600 border-t-transparent animate-spin" />
          </div>
          <p className="text-lg font-medium text-gray-700 animate-pulse">加载设置中...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="max-w-md w-full mx-4">
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-error-100 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-error-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-3">无法加载设置</h2>
            <p className="text-gray-600 mb-8">
              {error instanceof Error ? error.message : '连接到后端服务失败。请确保后端服务正在运行。'}
            </p>
            <Button onClick={() => refetch()} variant="primary" size="lg" fullWidth>
              <RotateCcw className="w-5 h-5 mr-2" />
              重新加载
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!localSettings) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-50 to-primary-50/20">
      {/* Success Toast */}
      {showSuccessToast && (
        <div className="fixed top-6 right-6 z-50 animate-in slide-in-from-top-5 fade-in duration-300">
          <div className="bg-white rounded-xl shadow-2xl border border-success-200 p-5 max-w-sm">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-success-100 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6 text-success-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-success-900">保存成功！</p>
                <p className="text-sm text-success-700 mt-1">设置已更新</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Toast */}
      {showErrorToast && (
        <div className="fixed top-6 right-6 z-50 animate-in slide-in-from-top-5 fade-in duration-300">
          <div className="bg-white rounded-xl shadow-2xl border border-error-200 p-5 max-w-sm">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-error-100 flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-error-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-error-900">保存失败</p>
                <p className="text-sm text-error-700 mt-1">{errorMessage}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header Section */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-lg">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">系统设置</h1>
                <p className="text-sm text-gray-500 mt-1">
                  配置您的 CMS 自动化系统
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-3">
              {hasChanges && (
                <div className="px-4 py-2 rounded-lg bg-warning-50 border border-warning-200 text-warning-700 text-sm font-medium animate-in fade-in duration-200">
                  未保存的更改
                </div>
              )}
              <Button
                variant="outline"
                onClick={handleReset}
                disabled={!hasChanges || updateMutation.isPending}
                size="md"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                重置
              </Button>
              <Button
                variant="primary"
                onClick={handleSave}
                disabled={!hasChanges || updateMutation.isPending}
                isLoading={updateMutation.isPending}
                size="md"
              >
                <Save className="w-4 h-4 mr-2" />
                {updateMutation.isPending ? '保存中...' : '保存设置'}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <Accordion spacing="lg">
          {/* Provider Configuration */}
          <AccordionItem
            title="Provider 配置"
            subtitle="配置 Playwright、Computer Use 和 Hybrid 发布方式"
            icon={<Monitor className="w-5 h-5" />}
            defaultOpen={true}
          >
            <ProviderConfigSection
              config={localSettings.provider_config}
              onChange={(config) => {
                setLocalSettings({ ...localSettings, provider_config: config });
                setHasChanges(true);
              }}
            />
          </AccordionItem>

          {/* CMS Configuration */}
          <AccordionItem
            title="WordPress 配置"
            subtitle="配置 WordPress 站点连接信息"
            icon={<Globe className="w-5 h-5" />}
          >
            <CMSConfigSection
              config={localSettings.cms_config}
              onChange={(config) => {
                setLocalSettings({ ...localSettings, cms_config: config });
                setHasChanges(true);
              }}
              onTestConnection={testConnection}
            />
          </AccordionItem>

          {/* Cost Limits */}
          <AccordionItem
            title="成本限额"
            subtitle="设置每日和每月的支出限额"
            icon={<DollarSign className="w-5 h-5" />}
          >
            <CostLimitsSection
              limits={localSettings.cost_limits}
              onChange={(limits) => {
                setLocalSettings({ ...localSettings, cost_limits: limits });
                setHasChanges(true);
              }}
              currentDailySpend={costUsage?.daily_spend}
              currentMonthlySpend={costUsage?.monthly_spend}
            />
          </AccordionItem>

          {/* Screenshot Retention */}
          <AccordionItem
            title="截图保留策略"
            subtitle="配置截图自动清理规则"
            icon={<Camera className="w-5 h-5" />}
          >
            <ScreenshotRetentionSection
              retention={localSettings.screenshot_retention}
              onChange={(retention) => {
                setLocalSettings({
                  ...localSettings,
                  screenshot_retention: retention,
                });
                setHasChanges(true);
              }}
              estimatedStorageUsage={storageUsage?.total_mb}
            />
          </AccordionItem>
        </Accordion>

        {/* Footer Info */}
        <div className="mt-12 pt-8 border-t border-gray-200 text-center">
          <p className="text-sm text-gray-500">
            最后更新: {new Date(localSettings.updated_at).toLocaleString('zh-CN', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            })}
          </p>
        </div>
      </div>
    </div>
  );
}
