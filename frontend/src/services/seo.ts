/**
 * SEO API Service
 *
 * Provides type-safe methods for SEO optimization operations.
 */

import { api } from './api-client';
import type {
  SEOMetadata,
  SEOUpdateRequest,
  APIResponse,
} from '../types/api';

export const seoAPI = {
  /**
   * Analyze an article for SEO optimization.
   * Generates SEO metadata including keywords, meta title/description, and recommendations.
   */
  analyze: (articleId: number, forceRefresh: boolean = false) =>
    api.post<APIResponse<SEOMetadata>>('v1/seo/analyze', {
      article_id: articleId,
      force_refresh: forceRefresh,
    }),

  /**
   * Get SEO metadata for an article.
   */
  get: (articleId: number) =>
    api.get<APIResponse<SEOMetadata>>(`api/v1/seo/articles/${articleId}`),

  /**
   * Update SEO metadata for an article.
   * Allows manual overrides of AI-generated SEO data.
   */
  update: (articleId: number, data: SEOUpdateRequest) =>
    api.put<APIResponse<SEOMetadata>>(`api/v1/seo/articles/${articleId}`, data),

  /**
   * Delete SEO metadata for an article.
   */
  delete: (articleId: number) =>
    api.delete<APIResponse<void>>(`api/v1/seo/articles/${articleId}`),

  /**
   * Get SEO statistics for all articles.
   */
  getStatistics: () =>
    api.get<
      APIResponse<{
        total_analyzed: number;
        avg_readability_score: number;
        avg_keyword_density: number;
        total_optimization_cost: number;
      }>
    >('v1/seo/statistics'),

  /**
   * Bulk analyze multiple articles.
   */
  bulkAnalyze: (articleIds: number[]) =>
    api.post<
      APIResponse<{
        total: number;
        successful: number;
        failed: number;
        results: SEOMetadata[];
      }>
    >('v1/seo/bulk-analyze', { article_ids: articleIds }),
};
