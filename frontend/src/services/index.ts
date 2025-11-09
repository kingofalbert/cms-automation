/**
 * Services Index
 *
 * Central export point for all API services.
 */

export { api, apiClient, setAuthToken, clearAuthToken, getAuthToken, isAuthenticated } from './api-client';
export { queryClient } from './query-client';
export { articlesAPI } from './articles';
export { seoAPI } from './seo';
export { publishingAPI } from './publishing';
export { worklistAPI } from './worklist';
export { settingsAPI } from './settings';
export { authAPI } from './auth';
export { default as ruleManagementAPI } from './ruleManagementAPI';

// Phase 7: Article parsing service
export * as parsingAPI from './parsing';
export type {
  ParseArticleRequest,
  ParseArticleResponse,
  ParsedArticleData,
  ArticleImage,
  ConfirmParsingRequest,
  ImageReviewRequest,
  ImageReviewAction,
} from './parsing';

// Re-export all types from api.ts for convenience
export type * from '../types/api';
