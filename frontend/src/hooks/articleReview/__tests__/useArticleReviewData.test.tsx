/**
 * Tests for useArticleReviewData hook
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useArticleReviewData } from '../useArticleReviewData';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';

// Mock the worklist API
vi.mock('@/services/worklist', () => ({
  worklistAPI: {
    get: vi.fn(),
  },
}));

vi.mock('@/services/articles', () => ({
  articlesAPI: {
    getReviewData: vi.fn(),
  },
}));

import { worklistAPI } from '@/services/worklist';
import { articlesAPI } from '@/services/articles';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  const Wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  return Wrapper;
};

describe('useArticleReviewData', () => {
  const mockWorklistItemId = 123;
  const mockArticleId = 789;
  const mockWorklistData = {
    id: 123,
    drive_file_id: 'test-file-id',
    title: 'Test Article',
    content: 'Test content',
    status: 'parsing_review' as const,
    author: null,
    article_id: null,
    metadata: {},
    notes: [],
    synced_at: '2024-01-01T00:00:00Z',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    tags: [],
    categories: [],
    article_status: null,
    meta_description: null,
    seo_keywords: [],
    article_status_history: [],
    drive_metadata: {},
    proofreading_issues: [],
  };
  const mockArticleReviewData = {
    id: mockArticleId,
    title: 'Test Article',
    status: 'in-review' as const,
    content: {
      original: 'Original',
      suggested: 'Suggested',
      changes: null,
    },
    meta: {
      original: 'Meta',
      suggested: 'New Meta',
      reasoning: null,
      score: null,
      length_original: 4,
      length_suggested: 7,
    },
    seo: {
      original_keywords: [],
      suggested_keywords: null,
      reasoning: null,
      score: null,
    },
    faq_proposals: [],
    paragraph_suggestions: [],
    proofreading_issues: [],
    existing_decisions: [],
    ai_model_used: null,
    suggested_generated_at: null,
    generation_cost: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch worklist item data successfully', async () => {
    vi.mocked(worklistAPI.get).mockResolvedValue(mockWorklistData);
    vi.mocked(articlesAPI.getReviewData).mockResolvedValue(mockArticleReviewData);

    const { result } = renderHook(
      () => useArticleReviewData(mockWorklistItemId, mockArticleId),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toBeDefined();
    expect(result.current.data?.id).toBe(mockWorklistItemId);
    expect(result.current.data?.articleReview).toEqual(mockArticleReviewData);
    expect(result.current.error).toBeNull();
    expect(articlesAPI.getReviewData).toHaveBeenCalledTimes(1);
  });

  it('should handle loading state', () => {
    vi.mocked(worklistAPI.get).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );
    vi.mocked(articlesAPI.getReviewData).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    const { result } = renderHook(
      () => useArticleReviewData(mockWorklistItemId, mockArticleId),
      {
        wrapper: createWrapper(),
      }
    );

    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();
  });

  it('should handle error state', async () => {
    const error = new Error('Failed to fetch worklist item');
    vi.mocked(worklistAPI.get).mockRejectedValue(error);
    vi.mocked(articlesAPI.getReviewData).mockResolvedValue(mockArticleReviewData);

    const { result } = renderHook(
      () => useArticleReviewData(mockWorklistItemId, mockArticleId),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.error).toBeDefined();
    });

    expect(result.current.data).toBeUndefined();
  });

  it('should not fetch when worklistItemId is 0 or negative', () => {
    const { result } = renderHook(
      () => useArticleReviewData(0, mockArticleId),
      {
        wrapper: createWrapper(),
      }
    );

    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
    expect(worklistAPI.get).not.toHaveBeenCalled();
    expect(articlesAPI.getReviewData).not.toHaveBeenCalled();
  });

  it('should not fetch when articleId is missing', () => {
    const { result } = renderHook(
      () => useArticleReviewData(mockWorklistItemId, undefined),
      {
        wrapper: createWrapper(),
      }
    );

    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
    expect(worklistAPI.get).not.toHaveBeenCalled();
    expect(articlesAPI.getReviewData).not.toHaveBeenCalled();
  });

  it('should refetch data when calling refetch', async () => {
    vi.mocked(worklistAPI.get).mockResolvedValue(mockWorklistData);
    vi.mocked(articlesAPI.getReviewData).mockResolvedValue(mockArticleReviewData);

    const { result } = renderHook(
      () => useArticleReviewData(mockWorklistItemId, mockArticleId),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(worklistAPI.get).toHaveBeenCalledTimes(1);
    expect(articlesAPI.getReviewData).toHaveBeenCalledTimes(1);

    // Refetch
    await result.current.refetch();

    await waitFor(() => {
      expect(worklistAPI.get).toHaveBeenCalledTimes(2);
      expect(articlesAPI.getReviewData).toHaveBeenCalledTimes(2);
    });
  });

  it('should compute hasParsingData correctly', async () => {
    vi.mocked(worklistAPI.get).mockResolvedValue(mockWorklistData);
    vi.mocked(articlesAPI.getReviewData).mockResolvedValue(mockArticleReviewData);

    const { result } = renderHook(
      () => useArticleReviewData(mockWorklistItemId, mockArticleId),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data?.hasParsingData).toBe(true);
  });

  it('should compute hasProofreadingData correctly', async () => {
    const dataWithIssues = {
      ...mockWorklistData,
      proofreading_issues: [{ type: 'grammar', message: 'Test issue' }],
    };
    // @ts-expect-error - Test mock data doesn't need full ProofreadingIssue type
    vi.mocked(worklistAPI.get).mockResolvedValue(dataWithIssues);
    vi.mocked(articlesAPI.getReviewData).mockResolvedValue(mockArticleReviewData);

    const { result } = renderHook(
      () => useArticleReviewData(mockWorklistItemId, mockArticleId),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data?.hasProofreadingData).toBe(true);
  });
});
