/**
 * React Query client configuration for data fetching and caching.
 */

import { QueryClient } from '@tanstack/react-query';

/**
 * Create and configure React Query client.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Stale time: 5 minutes
      staleTime: 5 * 60 * 1000,
      // Cache time: 10 minutes
      gcTime: 10 * 60 * 1000,
      // Retry failed requests, but not for 4xx client errors
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors (client errors like 404, 400, etc.)
        if (error && typeof error === 'object' && 'response' in error) {
          const status = (error as { response?: { status?: number } }).response?.status;
          if (status && status >= 400 && status < 500) {
            return false;
          }
        }
        // Retry up to 3 times for other errors (network issues, 5xx, etc.)
        return failureCount < 3;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      // Refetch on window focus in production
      refetchOnWindowFocus: import.meta.env.PROD,
      // Don't refetch on mount if data is fresh
      refetchOnMount: false,
    },
    mutations: {
      // Retry mutations once
      retry: 1,
      retryDelay: 1000,
    },
  },
});

/**
 * Query keys for organizing cached data.
 */
export const queryKeys = {
  // Article generation
  topics: {
    all: ['topics'] as const,
    list: (params?: Record<string, unknown>) => ['topics', 'list', params] as const,
    detail: (id: string | number) => ['topics', 'detail', id] as const,
  },

  // Articles
  articles: {
    all: ['articles'] as const,
    list: (params?: Record<string, unknown>) => ['articles', 'list', params] as const,
    detail: (id: string | number) => ['articles', 'detail', id] as const,
    similarity: (id: string | number) => ['articles', 'similarity', id] as const,
  },

  // Tags
  tags: {
    all: ['tags'] as const,
    list: (params?: Record<string, unknown>) => ['tags', 'list', params] as const,
  },

  // Schedules
  schedules: {
    all: ['schedules'] as const,
    list: (params?: Record<string, unknown>) => ['schedules', 'list', params] as const,
    detail: (id: string | number) => ['schedules', 'detail', id] as const,
  },

  // Workflows
  workflows: {
    all: ['workflows'] as const,
    detail: (articleId: string | number) => ['workflows', 'detail', articleId] as const,
  },
};
