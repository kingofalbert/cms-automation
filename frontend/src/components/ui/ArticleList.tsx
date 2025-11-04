/**
 * ArticleList Component
 *
 * High-performance article list with virtual scrolling
 * Efficiently renders large numbers of articles
 */

import React, { useCallback } from 'react';
import type { Article } from '@/types/api';
import { VirtualList } from './VirtualList';
import { ArticleCard } from './ArticleCard';
import { FileText } from 'lucide-react';

export interface ArticleListProps {
  /** Array of articles to display */
  articles: Article[];
  /** Loading state */
  isLoading?: boolean;
  /** Show excerpts on cards */
  showExcerpt?: boolean;
  /** Custom onClick handler for articles */
  onArticleClick?: (article: Article) => void;
  /** Height of the container */
  height?: string | number;
  /** Custom empty state message */
  emptyMessage?: string;
  /** Custom loading message */
  loadingMessage?: string;
}

export const ArticleList: React.FC<ArticleListProps> = ({
  articles,
  isLoading = false,
  showExcerpt = true,
  onArticleClick,
  height = '600px',
  emptyMessage = '暫無文章',
  loadingMessage = '載入文章中...',
}) => {
  // Memoize render function to prevent recreating on every render
  const renderArticle = useCallback(
    (article: Article) => {
      return (
        <div className="px-4" key={article.id}>
          <ArticleCard
            article={article}
            showExcerpt={showExcerpt}
            onClick={onArticleClick}
          />
        </div>
      );
    },
    [showExcerpt, onArticleClick]
  );

  // Memoize key extraction function
  const getItemKey = useCallback((article: Article) => article.id, []);

  // Custom loading component
  const loadingComponent = (
    <div className="flex items-center justify-center py-12">
      <div className="flex flex-col items-center gap-3">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
        <p className="text-sm text-gray-500">{loadingMessage}</p>
      </div>
    </div>
  );

  // Custom empty component
  const emptyComponent = (
    <div className="flex flex-col items-center justify-center py-12 text-gray-500">
      <FileText className="mb-4 h-16 w-16 text-gray-300" />
      <p className="text-lg font-medium">{emptyMessage}</p>
      <p className="mt-2 text-sm">嘗試調整篩選條件或導入新文章</p>
    </div>
  );

  return (
    <VirtualList
      items={articles}
      renderItem={renderArticle}
      estimateSize={280} // Estimated height of each article card
      gap={16} // Gap between cards
      height={height}
      overscan={3} // Render 3 extra items above/below viewport
      isLoading={isLoading}
      loadingComponent={loadingComponent}
      emptyComponent={emptyComponent}
      getItemKey={getItemKey}
      className="rounded-lg border border-gray-200 bg-gray-50"
      viewportClassName="bg-gray-50"
    />
  );
};

export default ArticleList;
