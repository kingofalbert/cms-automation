/**
 * Settings Page
 * Configure application settings including providers, CMS, costs, and screenshots.
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/services/api-client';
import { Button } from '@/components/ui';
import { ProviderConfigSection } from '@/components/Settings/ProviderConfigSection';
import { CMSConfigSection } from '@/components/Settings/CMSConfigSection';
import { CostLimitsSection } from '@/components/Settings/CostLimitsSection';
import { ScreenshotRetentionSection } from '@/components/Settings/ScreenshotRetentionSection';
import { AppSettings, SettingsUpdateRequest } from '@/types/settings';
import { Save, RotateCcw } from 'lucide-react';

export default function SettingsPage() {
  const [hasChanges, setHasChanges] = useState(false);
  const [localSettings, setLocalSettings] = useState<AppSettings | null>(null);

  // Fetch settings
  const { data: settings, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['app-settings'],
    queryFn: async () => {
      const response = await api.get<AppSettings>('v1/settings');

      // Check if response contains an error field (backend returns 200 with error message)
      if (response && 'error' in response) {
        throw new Error((response as any).message || 'Failed to load settings');
      }

      return response;
    },
    retry: 2,
    retryDelay: 1000,
  });

  // Update local settings when data changes
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
      alert('设置保存成功！');
      refetch();
      setHasChanges(false);
    },
    onError: (error: any) => {
      alert(`保存失败: ${error.response?.data?.message || error.message}`);
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

  // Fetch current cost usage - DISABLED due to API mismatch
  // Backend returns list[CostUsageEntry] but frontend expects {daily_spend, monthly_spend}
  const { data: costUsage } = useQuery({
    queryKey: ['cost-usage'],
    queryFn: async () => {
      const response = await api.get<{
        daily_spend: number;
        monthly_spend: number;
      }>('v1/analytics/cost-usage');
      return response;
    },
    enabled: false, // Disabled until backend provides aggregated endpoint
    refetchInterval: 60000, // Refresh every minute
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
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
        <div className="text-gray-600">加载中...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-md">
          <div className="text-red-600 mb-4">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">无法加载设置</h2>
          <p className="text-gray-600 mb-6">
            {error instanceof Error ? error.message : '连接到后端服务失败。请确保后端服务正在运行。'}
          </p>
          <Button onClick={() => refetch()} variant="primary">
            重试
          </Button>
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
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Page Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">系统设置</h1>
          <p className="mt-2 text-gray-600">
            配置发布 Provider、WordPress 连接、成本限额和截图策略
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={handleReset}
            disabled={!hasChanges || updateMutation.isPending}
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            重置
          </Button>
          <Button
            variant="primary"
            onClick={handleSave}
            disabled={!hasChanges || updateMutation.isPending}
          >
            <Save className="w-4 h-4 mr-2" />
            {updateMutation.isPending ? '保存中...' : '保存设置'}
          </Button>
        </div>
      </div>

      {/* Unsaved Changes Warning */}
      {hasChanges && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-700">
            您有未保存的更改。请点击"保存设置"按钮以保存更改。
          </p>
        </div>
      )}

      {/* Settings Sections */}
      <div className="space-y-6">
        {/* Provider Configuration */}
        <ProviderConfigSection
          config={localSettings.provider_config}
          onChange={(config) => {
            setLocalSettings({ ...localSettings, provider_config: config });
            setHasChanges(true);
          }}
        />

        {/* CMS Configuration */}
        <CMSConfigSection
          config={localSettings.cms_config}
          onChange={(config) => {
            setLocalSettings({ ...localSettings, cms_config: config });
            setHasChanges(true);
          }}
          onTestConnection={testConnection}
        />

        {/* Cost Limits */}
        <CostLimitsSection
          limits={localSettings.cost_limits}
          onChange={(limits) => {
            setLocalSettings({ ...localSettings, cost_limits: limits });
            setHasChanges(true);
          }}
          currentDailySpend={costUsage?.daily_spend}
          currentMonthlySpend={costUsage?.monthly_spend}
        />

        {/* Screenshot Retention */}
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
      </div>

      {/* Footer */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <p className="text-sm text-gray-500">
          最后更新: {new Date(localSettings.updated_at).toLocaleString('zh-CN')}
        </p>
      </div>
    </div>
  );
}
