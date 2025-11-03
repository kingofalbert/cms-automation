/**
 * Worklist API Service
 *
 * Provides type-safe methods for managing worklist items synced from Google Drive.
 */

import { api } from './api-client';
import type {
  WorklistItem,
  WorklistUpdateRequest,
  WorklistListParams,
  WorklistStatistics,
  PaginatedResponse,
  APIResponse,
} from '../types/api';

export const worklistAPI = {
  /**
   * Get paginated list of worklist items with optional filters.
   */
  list: (params?: WorklistListParams) =>
    api.get<APIResponse<PaginatedResponse<WorklistItem>>>('/api/v1/worklist', { params }),

  /**
   * Get a single worklist item by ID.
   */
  get: (id: number) =>
    api.get<APIResponse<WorklistItem>>(`/api/v1/worklist/${id}`),

  /**
   * Update a worklist item (status or add note).
   */
  update: (id: number, data: WorklistUpdateRequest) =>
    api.put<APIResponse<WorklistItem>>(`/api/v1/worklist/${id}`, data),

  /**
   * Delete a worklist item.
   */
  delete: (id: number) =>
    api.delete<APIResponse<void>>(`/api/v1/worklist/${id}`),

  /**
   * Sync worklist items from Google Drive.
   * Fetches latest documents from configured Google Drive folder.
   */
  sync: () =>
    api.post<
      APIResponse<{
        synced: number;
        updated: number;
        new: number;
        errors: string[];
      }>
    >('/api/v1/worklist/sync'),

  /**
   * Convert a worklist item to an article.
   * Moves the item from worklist to articles table.
   */
  convertToArticle: (id: number) =>
    api.post<
      APIResponse<{
        article_id: number;
        worklist_id: number;
      }>
    >(`/api/v1/worklist/${id}/convert`),

  /**
   * Get worklist statistics.
   */
  getStatistics: () =>
    api.get<APIResponse<WorklistStatistics>>('/api/v1/worklist/statistics'),

  /**
   * Bulk update status for multiple worklist items.
   */
  bulkUpdateStatus: (ids: number[], status: string) =>
    api.post<
      APIResponse<{
        updated: number;
        failed: number;
      }>
    >('/api/v1/worklist/bulk-update', {
      ids,
      status,
    }),

  /**
   * Get sync history.
   */
  getSyncHistory: (limit: number = 10) =>
    api.get<
      APIResponse<{
        history: Array<{
          timestamp: string;
          synced: number;
          updated: number;
          new: number;
          duration_seconds: number;
        }>;
      }>
    >('/api/v1/worklist/sync-history', {
      params: { limit },
    }),
};
