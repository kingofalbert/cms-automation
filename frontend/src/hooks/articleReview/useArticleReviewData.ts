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
import { articlesAPI } from '../../services/articles';
import type { WorklistItemDetail, ProofreadingIssue } from '../../types/worklist';
import type { ArticleReviewResponse, ArticleReviewResponseTransformed, APIProofreadingIssue } from '../../types/api';
import { transformArticleReviewResponse, transformAPIProofreadingIssues } from '../../types/api';

export interface ArticleReviewData extends WorklistItemDetail {
  hasParsingData: boolean;
  hasProofreadingData: boolean;
  isReadyToPublish: boolean;
  articleReview: ArticleReviewResponseTransformed | null;
}

/**
 * Check if an issue needs transformation (has API format fields)
 */
const isAPIFormat = (issue: ProofreadingIssue | APIProofreadingIssue): issue is APIProofreadingIssue => {
  // API format has 'evidence' and 'message', frontend format has 'original_text' and 'explanation'
  return 'evidence' in issue || 'message' in issue;
};

/**
 * Transform worklist proofreading issues from API format to frontend format
 * Handles both API format (from worklist) and frontend format (already transformed)
 */
const transformWorklistIssues = (issues: (ProofreadingIssue | APIProofreadingIssue)[] | undefined): ProofreadingIssue[] => {
  if (!issues || issues.length === 0) return [];

  // Check if first issue is in API format (has 'evidence' or 'message' fields)
  const firstIssue = issues[0];
  if (isAPIFormat(firstIssue)) {
    // Transform from API format
    return transformAPIProofreadingIssues(issues as APIProofreadingIssue[]);
  }

  // Already in frontend format
  return issues as ProofreadingIssue[];
};

/**
 * Transform worklist item detail to review data
 */
const transformToReviewData = (
  item: WorklistItemDetail,
  review: ArticleReviewResponse | null
): ArticleReviewData => {
  // Transform API response including proofreading issues to frontend format
  const transformedReview = review ? transformArticleReviewResponse(review) : null;

  // Transform worklist issues if they're in API format
  const transformedWorklistIssues = transformWorklistIssues(item.proofreading_issues as (ProofreadingIssue | APIProofreadingIssue)[]);

  // Prefer articleReview issues (richer data), fall back to transformed worklist issues
  const transformedIssues = transformedReview?.proofreading_issues?.length
    ? transformedReview.proofreading_issues
    : transformedWorklistIssues;

  return {
    ...item,
    proofreading_issues: transformedIssues,
    hasParsingData: Boolean(item.title && item.content),
    hasProofreadingData: Boolean(transformedIssues && transformedIssues.length > 0),
    isReadyToPublish: item.status === 'ready_to_publish' || item.status === 'publishing',
    articleReview: transformedReview,
  };
};

/**
 * Hook: useArticleReviewData
 */
export const useArticleReviewData = (
  worklistItemId: number,
  articleId?: number,
  enabled = true,
) => {
  const queryClient = useQueryClient();
  const queryKey = ['articleReview', worklistItemId, articleId ?? null] as const;

  const query = useQuery({
    queryKey,
    queryFn: async (): Promise<ArticleReviewData> => {
      const [worklistData, articleReview] = await Promise.all([
        worklistAPI.get(worklistItemId),
        articleId ? articlesAPI.getReviewData(articleId) : Promise.resolve(null),
      ]);
      return transformToReviewData(worklistData, articleReview);
    },
    enabled: enabled && worklistItemId > 0 && Boolean(articleId),
    staleTime: 30 * 1000, // 30 seconds - data is fresh for 30s
    gcTime: 5 * 60 * 1000, // 5 minutes - cache for 5 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: true,
  });

  /**
   * Prefetch next/previous worklist items for smooth navigation
   */
  const prefetchAdjacentItems = (
    next?: { worklistId: number; articleId?: number },
    prev?: { worklistId: number; articleId?: number },
  ) => {
    if (next?.worklistId && next.articleId) {
      queryClient.prefetchQuery({
        queryKey: ['articleReview', next.worklistId, next.articleId],
        queryFn: async () => {
          const [worklistData, articleReview] = await Promise.all([
            worklistAPI.get(next.worklistId),
            articlesAPI.getReviewData(next.articleId!),
          ]);
          return transformToReviewData(worklistData, articleReview);
        },
        staleTime: 30 * 1000,
      });
    }

    if (prev?.worklistId && prev.articleId) {
      queryClient.prefetchQuery({
        queryKey: ['articleReview', prev.worklistId, prev.articleId],
        queryFn: async () => {
          const [worklistData, articleReview] = await Promise.all([
            worklistAPI.get(prev.worklistId),
            articlesAPI.getReviewData(prev.articleId!),
          ]);
          return transformToReviewData(worklistData, articleReview);
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
      queryKey,
    });
  };

  /**
   * Update cached data optimistically
   */
  const updateCachedData = (updater: (old: ArticleReviewData) => ArticleReviewData) => {
    queryClient.setQueryData<ArticleReviewData>(
      queryKey,
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
