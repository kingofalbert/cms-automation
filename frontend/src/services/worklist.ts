/**
 * Worklist API Service
 *
 * Provides type-safe methods for managing worklist items synced from Google Drive.
 */

import { api } from './api-client';
import type { APIResponse } from '../types/api';
import type {
  WorklistItemDetail,
  WorklistStatistics,
  WorklistFilters,
  DriveSyncStatus,
  WorklistListResponse,
  ReviewDecisionsRequest,
  ReviewDecisionsResponse,
  BatchDecisionsRequest,
  BatchDecisionsResponse,
} from '../types/worklist';

export const worklistAPI = {
  /**
   * Get paginated list of worklist items with optional filters.
   */
  list: (params?: Partial<WorklistFilters>) =>
    api.get<WorklistListResponse>('/v1/worklist', { params }),

  /**
   * Get a single worklist item by ID.
   */
  get: (id: number) =>
    api.get<WorklistItemDetail>(`/v1/worklist/${id}`),

  /**
   * Sync worklist items from Google Drive.
   * Fetches latest documents from configured Google Drive folder.
   */
  sync: () =>
    api.post('/v1/worklist/sync'),

  /**
   * Get worklist statistics.
   */
  getStatistics: () =>
    api.get<WorklistStatistics>('/v1/worklist/statistics'),

  /**
   * Get current sync status metadata.
   */
  getSyncStatus: () => api.get<DriveSyncStatus>('/v1/worklist/sync-status'),

  /**
   * Update status for a single worklist item.
   * BUGFIX: Added to support workflow step transitions
   */
  updateStatus: (itemId: number, status: string) =>
    api.post<WorklistItemDetail>(`/v1/worklist/${itemId}/status`, {
      status,
    }),

  /**
   * Bulk update status for multiple worklist items.
   */
  bulkUpdateStatus: (ids: number[], status: string) =>
    api.post<
      APIResponse<{
        updated: number;
        failed: number;
      }>
    >('/v1/worklist/bulk-update', {
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
    >('/v1/worklist/sync-history', {
      params: { limit },
    }),

  /**
   * Save proofreading review decisions.
   * Creates ProofreadingDecision records and optionally transitions status.
   */
  saveReviewDecisions: (itemId: number, request: ReviewDecisionsRequest) =>
    api.post<ReviewDecisionsResponse>(`/v1/worklist/${itemId}/review-decisions`, request),

  /**
   * Batch accept or reject multiple issues.
   */
  batchDecisions: (itemId: number, request: BatchDecisionsRequest) =>
    api.post<BatchDecisionsResponse>(`/v1/worklist/${itemId}/batch-decisions`, request),
};
