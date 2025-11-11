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

import { worklistAPI } from '@/services/worklist';

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
  const mockWorklistData = {
    id: 123,
    title: 'Test Article',
    content: 'Test content',
    status: 'parsing_review' as const,
    url: 'https://example.com/test',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    proofreading_issues: [],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch worklist item data successfully', async () => {
    vi.mocked(worklistAPI.get).mockResolvedValue(mockWorklistData);

    const { result } = renderHook(
      () => useArticleReviewData(mockWorklistItemId),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toBeDefined();
    expect(result.current.data?.id).toBe(mockWorklistItemId);
    expect(result.current.error).toBeNull();
  });

  it('should handle loading state', () => {
    vi.mocked(worklistAPI.get).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    const { result } = renderHook(
      () => useArticleReviewData(mockWorklistItemId),
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

    const { result } = renderHook(
      () => useArticleReviewData(mockWorklistItemId),
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
      () => useArticleReviewData(0),
      {
        wrapper: createWrapper(),
      }
    );

    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
    expect(worklistAPI.get).not.toHaveBeenCalled();
  });

  it('should refetch data when calling refetch', async () => {
    vi.mocked(worklistAPI.get).mockResolvedValue(mockWorklistData);

    const { result } = renderHook(
      () => useArticleReviewData(mockWorklistItemId),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(worklistAPI.get).toHaveBeenCalledTimes(1);

    // Refetch
    await result.current.refetch();

    await waitFor(() => {
      expect(worklistAPI.get).toHaveBeenCalledTimes(2);
    });
  });

  it('should compute hasParsingData correctly', async () => {
    vi.mocked(worklistAPI.get).mockResolvedValue(mockWorklistData);

    const { result } = renderHook(
      () => useArticleReviewData(mockWorklistItemId),
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
    vi.mocked(worklistAPI.get).mockResolvedValue(dataWithIssues);

    const { result } = renderHook(
      () => useArticleReviewData(mockWorklistItemId),
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
