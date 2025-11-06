/**
 * Articles API Service
 *
 * Provides type-safe methods for article management operations.
 */

import { api } from './api-client';
import type {
  Article,
  ArticleCreateRequest,
  ArticleUpdateRequest,
  ArticleListParams,
  PaginatedResponse,
  APIResponse,
  ImportResult,
} from '../types/api';

export const articlesAPI = {
  /**
   * Get paginated list of articles with optional filters.
   */
  list: (params?: ArticleListParams) =>
    api.get<APIResponse<PaginatedResponse<Article>>>('/v1/articles', { params }),

  /**
   * Get a single article by ID.
   */
  get: (id: number) =>
    api.get<APIResponse<Article>>(`/v1/articles/${id}`),

  /**
   * Create a new article.
   */
  create: (data: ArticleCreateRequest) =>
    api.post<APIResponse<Article>>('/v1/articles', data),

  /**
   * Update an existing article.
   */
  update: (id: number, data: ArticleUpdateRequest) =>
    api.put<APIResponse<Article>>(`/v1/articles/${id}`, data),

  /**
   * Delete an article.
   */
  delete: (id: number) =>
    api.delete<APIResponse<void>>(`/v1/articles/${id}`),

  /**
   * Import articles from CSV file.
   */
  importCSV: (file: File, validateOnly: boolean = false) => {
    const formData = new FormData();
    formData.append('file', file);
    if (validateOnly) {
      formData.append('validate_only', 'true');
    }

    return api.post<APIResponse<ImportResult>>('/v1/articles/import/csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  /**
   * Import articles from JSON file.
   */
  importJSON: (file: File, validateOnly: boolean = false) => {
    const formData = new FormData();
    formData.append('file', file);
    if (validateOnly) {
      formData.append('validate_only', 'true');
    }

    return api.post<APIResponse<ImportResult>>('/v1/articles/import/json', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  /**
   * Upload featured image for an article.
   */
  uploadImage: (articleId: number, file: File, type: 'featured' | 'additional' = 'featured') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    return api.post<APIResponse<{ path: string }>>(
      `/v1/articles/${articleId}/images`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
  },

  /**
   * Delete an image from an article.
   */
  deleteImage: (articleId: number, imagePath: string) =>
    api.delete<APIResponse<void>>(`/v1/articles/${articleId}/images`, {
      data: { image_path: imagePath },
    }),
};
