/**
 * useArticleReviewData - Data fetching and caching for article review
 *
 * Phase 8.1: Modal Framework
 * - Fetches worklist item detail with all review data
 * - Uses React Query for caching and prefetching
 * - Provides loading, error states
 * - Auto-refetch on status changes
 *
 * Returns:
 * - Worklist item data (title, content, status)
 * - Article data (if linked)
 * - Parsing data (title, author, images, SEO, FAQ)
 * - Proofreading issues
 * - Publish preview data
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { worklistAPI } from '../../services/worklist';
import type { WorklistItemDetail } from '../../types/worklist';

export interface ArticleReviewData extends WorklistItemDetail {
  // Extended with computed properties for UI
  hasParsingData: boolean;
  hasProofreadingData: boolean;
  isReadyToPublish: boolean;
}

/**
 * Transform worklist item detail to review data
 */
const transformToReviewData = (item: WorklistItemDetail): ArticleReviewData => {
  return {
    ...item,
    hasParsingData: Boolean(item.title && item.content),
    hasProofreadingData: Boolean(item.proofreading_issues && item.proofreading_issues.length > 0),
    isReadyToPublish: item.status === 'ready_to_publish' || item.status === 'publishing',
  };
};

/**
 * Hook: useArticleReviewData
 */
export const useArticleReviewData = (worklistItemId: number, enabled = true) => {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['articleReview', worklistItemId],
    queryFn: async (): Promise<ArticleReviewData> => {
      const data = await worklistAPI.get(worklistItemId);
      return transformToReviewData(data);
    },
    enabled: enabled && worklistItemId > 0,
    staleTime: 30 * 1000, // 30 seconds - data is fresh for 30s
    gcTime: 5 * 60 * 1000, // 5 minutes - cache for 5 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: true,
  });

  /**
   * Prefetch next/previous worklist items for smooth navigation
   */
  const prefetchAdjacentItems = (nextId?: number, prevId?: number) => {
    if (nextId) {
      queryClient.prefetchQuery({
        queryKey: ['articleReview', nextId],
        queryFn: async () => {
          const data = await worklistAPI.get(nextId);
          return transformToReviewData(data);
        },
        staleTime: 30 * 1000,
      });
    }

    if (prevId) {
      queryClient.prefetchQuery({
        queryKey: ['articleReview', prevId],
        queryFn: async () => {
          const data = await worklistAPI.get(prevId);
          return transformToReviewData(data);
        },
        staleTime: 30 * 1000,
      });
    }
  };

  /**
   * Invalidate and refetch current item data
   */
  const invalidate = () => {
    queryClient.invalidateQueries({
      queryKey: ['articleReview', worklistItemId],
    });
  };

  /**
   * Update cached data optimistically
   */
  const updateCachedData = (updater: (old: ArticleReviewData) => ArticleReviewData) => {
    queryClient.setQueryData<ArticleReviewData>(
      ['articleReview', worklistItemId],
      (old) => (old ? updater(old) : old)
    );
  };

  return {
    data: query.data,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    error: query.error,
    refetch: query.refetch,
    prefetchAdjacentItems,
    invalidate,
    updateCachedData,
  };
};

/**
 * Hook: useArticleReviewMutation
 * For updating article review data
 */
export const useArticleReviewMutation = () => {
  const queryClient = useQueryClient();

  // TODO: Implement mutation hooks in Phase 8.2-8.4
  // - updateParsingData
  // - submitProofreadingDecisions
  // - publishArticle

  return {
    // Placeholder for future mutations
    invalidateAll: () => {
      queryClient.invalidateQueries({
        queryKey: ['articleReview'],
      });
    },
  };
};
