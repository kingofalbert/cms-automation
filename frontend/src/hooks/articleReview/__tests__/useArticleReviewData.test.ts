/**
 * Tests for useArticleReviewData hook
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useArticleReviewData } from '../useArticleReviewData';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

// Mock the articles service
vi.mock('@/services/articles', () => ({
  getArticleById: vi.fn(),
}));

import { getArticleById } from '@/services/articles';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useArticleReviewData', () => {
  const mockArticleId = '123';
  const mockArticleData = {
    id: '123',
    title: 'Test Article',
    content: 'Test content',
    status: 'parsing_review' as const,
    parsing_result: {
      title: { original: 'Test', suggested: 'Test Article' },
      author: { name: 'John Doe', bio: 'Author bio' },
      images: [],
      faqs: [],
      seo: { keywords: [], description: '', slug: 'test-article' },
    },
    proofreading_result: {
      content: 'Proofread content',
      issues: [],
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch article data successfully', async () => {
    vi.mocked(getArticleById).mockResolvedValue(mockArticleData);

    const { result } = renderHook(
      () => useArticleReviewData(mockArticleId),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.article).toEqual(mockArticleData);
    expect(result.current.isError).toBe(false);
  });

  it('should handle loading state', () => {
    vi.mocked(getArticleById).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    const { result } = renderHook(
      () => useArticleReviewData(mockArticleId),
      {
        wrapper: createWrapper(),
      }
    );

    expect(result.current.isLoading).toBe(true);
    expect(result.current.article).toBeUndefined();
  });

  it('should handle error state', async () => {
    const error = new Error('Failed to fetch article');
    vi.mocked(getArticleById).mockRejectedValue(error);

    const { result } = renderHook(
      () => useArticleReviewData(mockArticleId),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeDefined();
    expect(result.current.article).toBeUndefined();
  });

  it('should return null data when articleId is null', () => {
    const { result } = renderHook(
      () => useArticleReviewData(null),
      {
        wrapper: createWrapper(),
      }
    );

    expect(result.current.article).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
  });

  it('should refetch data when calling refetch', async () => {
    vi.mocked(getArticleById).mockResolvedValue(mockArticleData);

    const { result } = renderHook(
      () => useArticleReviewData(mockArticleId),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(getArticleById).toHaveBeenCalledTimes(1);

    // Refetch
    await result.current.refetch();

    expect(getArticleById).toHaveBeenCalledTimes(2);
  });

  it('should extract parsing data correctly', async () => {
    vi.mocked(getArticleById).mockResolvedValue(mockArticleData);

    const { result } = renderHook(
      () => useArticleReviewData(mockArticleId),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.parsingData).toEqual(mockArticleData.parsing_result);
  });

  it('should extract proofreading data correctly', async () => {
    vi.mocked(getArticleById).mockResolvedValue(mockArticleData);

    const { result } = renderHook(
      () => useArticleReviewData(mockArticleId),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.proofreadingData).toEqual(mockArticleData.proofreading_result);
  });
});
