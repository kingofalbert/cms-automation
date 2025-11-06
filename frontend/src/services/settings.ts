/**
 * Settings API Service
 *
 * Provides type-safe methods for managing application settings and configurations.
 */

import { api } from './api-client';
import type {
  Settings,
  CMSConfig,
  ProviderConfig,
  CostLimits,
  ScreenshotRetention,
  APIResponse,
} from '../types/api';

export const settingsAPI = {
  /**
   * Get all application settings.
   */
  getAll: () => api.get<APIResponse<Settings>>('/v1/settings'),

  /**
   * Update all settings at once.
   */
  updateAll: (settings: Partial<Settings>) =>
    api.put<APIResponse<Settings>>('/v1/settings', settings),

  /**
   * Get CMS configuration.
   */
  getCMSConfig: () => api.get<APIResponse<CMSConfig>>('/v1/settings/cms'),

  /**
   * Update CMS configuration.
   */
  updateCMSConfig: (config: Partial<CMSConfig>) =>
    api.put<APIResponse<CMSConfig>>('/v1/settings/cms', config),

  /**
   * Test CMS connection with current settings.
   */
  testCMSConnection: () =>
    api.post<
      APIResponse<{
        success: boolean;
        message: string;
        cms_version?: string;
      }>
    >('/v1/settings/cms/test'),

  /**
   * Get provider configuration.
   */
  getProviderConfig: () =>
    api.get<APIResponse<ProviderConfig>>('/v1/settings/providers'),

  /**
   * Update provider configuration.
   */
  updateProviderConfig: (config: Partial<ProviderConfig>) =>
    api.put<APIResponse<ProviderConfig>>('/v1/settings/providers', config),

  /**
   * Test provider API keys.
   */
  testProviderKeys: (provider: string) =>
    api.post<
      APIResponse<{
        provider: string;
        valid: boolean;
        message: string;
      }>
    >(`/v1/settings/providers/${provider}/test`),

  /**
   * Get cost limits configuration.
   */
  getCostLimits: () => api.get<APIResponse<CostLimits>>('/v1/settings/cost-limits'),

  /**
   * Update cost limits configuration.
   */
  updateCostLimits: (limits: Partial<CostLimits>) =>
    api.put<APIResponse<CostLimits>>('/v1/settings/cost-limits', limits),

  /**
   * Get screenshot retention configuration.
   */
  getScreenshotRetention: () =>
    api.get<APIResponse<ScreenshotRetention>>('/v1/settings/screenshots'),

  /**
   * Update screenshot retention configuration.
   */
  updateScreenshotRetention: (config: Partial<ScreenshotRetention>) =>
    api.put<APIResponse<ScreenshotRetention>>('/v1/settings/screenshots', config),

  /**
   * Clean up old screenshots based on retention policy.
   */
  cleanupScreenshots: () =>
    api.post<
      APIResponse<{
        deleted: number;
        space_freed_mb: number;
      }>
    >('/v1/settings/screenshots/cleanup'),

  /**
   * Get current usage and cost statistics.
   */
  getUsageStats: (days: number = 30) =>
    api.get<
      APIResponse<{
        period_days: number;
        total_cost_usd: number;
        daily_average_usd: number;
        cost_by_provider: Record<string, number>;
        remaining_budget_usd?: number;
        budget_usage_percentage?: number;
      }>
    >('/v1/settings/usage-stats', {
      params: { days },
    }),

  /**
   * Reset settings to default values.
   */
  resetToDefaults: () => api.post<APIResponse<Settings>>('/v1/settings/reset'),

  /**
   * Export settings as JSON file.
   */
  exportSettings: async () => {
    const response = await api.get('/v1/settings/export', {
      responseType: 'blob',
    });
    return response;
  },

  /**
   * Import settings from JSON file.
   */
  importSettings: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    return api.post<APIResponse<Settings>>('/v1/settings/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};
