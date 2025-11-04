/**
 * React Query hooks for article operations.
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

interface Article {
  id: number;
  title: string;
  body: string;
  status: string;
  author_id: number;
  cms_article_id?: string;
  published_at?: string;
  article_metadata: {
    word_count?: number;
    cost_usd?: number;
    input_tokens?: number;
    output_tokens?: number;
  };
  formatting: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

interface ArticleListItem {
  id: number;
  title: string;
  status: string;
  author_id: number;
  created_at: string;
  published_at?: string;
}

export function useArticles(skip = 0, limit = 20) {
  return useQuery({
    queryKey: ['articles', skip, limit],
    queryFn: async () => {
      const response = await api.get<ArticleListItem[]>('/v1/articles', {
        params: { skip, limit },
      });
      return response;
    },
  });
}

export function useArticle(articleId: number) {
  return useQuery({
    queryKey: ['article', articleId],
    queryFn: async () => {
      const response = await api.get<Article>(`/v1/articles/${articleId}`);
      return response;
    },
    enabled: !!articleId,
  });
}
