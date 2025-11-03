/**
 * Publishing API Service
 *
 * Provides type-safe methods for managing publish tasks and monitoring publication progress.
 */

import { api } from './api-client';
import type {
  PublishTask,
  PublishTaskCreateRequest,
  PublishTaskListParams,
  ExecutionLog,
  PaginatedResponse,
  APIResponse,
  ProviderMetrics,
} from '../types/api';

export const publishingAPI = {
  /**
   * Get paginated list of publish tasks with optional filters.
   */
  list: (params?: PublishTaskListParams) =>
    api.get<APIResponse<PaginatedResponse<PublishTask>>>('/api/v1/publishing/tasks', {
      params,
    }),

  /**
   * Get a single publish task by ID.
   */
  get: (taskId: number) =>
    api.get<APIResponse<PublishTask>>(`/api/v1/publishing/tasks/${taskId}`),

  /**
   * Create a new publish task for an article.
   */
  create: (data: PublishTaskCreateRequest) =>
    api.post<APIResponse<PublishTask>>('/api/v1/publishing/tasks', data),

  /**
   * Retry a failed publish task.
   */
  retry: (taskId: number) =>
    api.post<APIResponse<PublishTask>>(`/api/v1/publishing/tasks/${taskId}/retry`),

  /**
   * Cancel a running publish task.
   */
  cancel: (taskId: number) =>
    api.post<APIResponse<PublishTask>>(`/api/v1/publishing/tasks/${taskId}/cancel`),

  /**
   * Delete a publish task and its associated data.
   */
  delete: (taskId: number) =>
    api.delete<APIResponse<void>>(`/api/v1/publishing/tasks/${taskId}`),

  /**
   * Get execution logs for a publish task.
   */
  getLogs: (taskId: number, level?: string) =>
    api.get<APIResponse<{ logs: ExecutionLog[]; total: number }>>(
      `/api/v1/publishing/tasks/${taskId}/logs`,
      {
        params: { level },
      }
    ),

  /**
   * Download screenshot from a publish task.
   */
  downloadScreenshot: async (taskId: number, screenshotName: string) => {
    const response = await api.get(
      `/api/v1/publishing/tasks/${taskId}/screenshots/${screenshotName}`,
      {
        responseType: 'blob',
      }
    );
    return response;
  },

  /**
   * Get provider comparison metrics.
   */
  getProviderMetrics: (days: number = 30) =>
    api.get<APIResponse<{ providers: ProviderMetrics[] }>>(
      '/api/v1/publishing/provider-metrics',
      {
        params: { days },
      }
    ),

  /**
   * Get publishing statistics.
   */
  getStatistics: () =>
    api.get<
      APIResponse<{
        total_tasks: number;
        success_rate: number;
        avg_duration_seconds: number;
        total_cost_usd: number;
        tasks_by_status: Record<string, number>;
        tasks_by_provider: Record<string, number>;
      }>
    >('/api/v1/publishing/statistics'),

  /**
   * Bulk publish multiple articles.
   */
  bulkPublish: (articleIds: number[], provider?: string, cmsType?: string) =>
    api.post<
      APIResponse<{
        total: number;
        successful: number;
        failed: number;
        tasks: PublishTask[];
      }>
    >('/api/v1/publishing/bulk-publish', {
      article_ids: articleIds,
      provider,
      cms_type: cmsType,
    }),
};
