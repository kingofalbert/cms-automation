/**
 * ArticleCard Component
 *
 * Optimized article card with lazy image loading and memoization
 * Used in virtual lists for efficient rendering
 */

import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { clsx } from 'clsx';
import { Calendar, Tag, FileText, ExternalLink } from 'lucide-react';
import type { Article } from '@/types/api';
import { LazyImage } from './LazyImage';

export interface ArticleCardProps {
  article: Article;
  /** Show full content or just excerpt */
  showExcerpt?: boolean;
  /** Custom onClick handler */
  onClick?: (article: Article) => void;
  /** Custom className */
  className?: string;
}

const STATUS_COLORS: Record<string, string> = {
  imported: 'bg-blue-100 text-blue-800',
  seo_optimized: 'bg-purple-100 text-purple-800',
  ready_to_publish: 'bg-green-100 text-green-800',
  publishing: 'bg-yellow-100 text-yellow-800',
  published: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

const STATUS_LABELS: Record<string, string> = {
  imported: '已導入',
  seo_optimized: 'SEO已優化',
  ready_to_publish: '準備發佈',
  publishing: '發佈中',
  published: '已發佈',
  failed: '失敗',
};

const ArticleCardComponent: React.FC<ArticleCardProps> = ({
  article,
  showExcerpt = true,
  onClick,
  className,
}) => {
  // Memoize formatted date
  const formattedDate = useMemo(() => {
    return format(new Date(article.created_at), 'yyyy-MM-dd HH:mm');
  }, [article.created_at]);

  // Memoize status label
  const statusLabel = useMemo(() => {
    return STATUS_LABELS[article.status] || article.status;
  }, [article.status]);

  // Memoize status color
  const statusColor = useMemo(() => {
    return STATUS_COLORS[article.status] || 'bg-gray-100 text-gray-800';
  }, [article.status]);

  // Truncate content for excerpt
  const excerpt = useMemo(() => {
    if (!showExcerpt) return null;
    if (article.excerpt) return article.excerpt;

    // Generate excerpt from content
    const plainText = article.content.replace(/<[^>]*>/g, '');
    return plainText.length > 150
      ? `${plainText.substring(0, 150)}...`
      : plainText;
  }, [article.excerpt, article.content, showExcerpt]);

  const handleClick = () => {
    onClick?.(article);
  };

  const cardContent = (
    <div
      className={clsx(
        'group relative overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition-all hover:shadow-md',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={handleClick}
    >
      {/* Featured Image */}
      {article.featured_image_path && (
        <div className="relative h-48 w-full overflow-hidden bg-gray-100">
          <LazyImage
            src={article.featured_image_path}
            alt={article.title}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
            placeholder="/images/placeholder.jpg"
          />
          {/* Status Badge on Image */}
          <div className="absolute top-2 right-2">
            <span
              className={clsx(
                'inline-flex items-center rounded-full px-3 py-1 text-xs font-medium',
                statusColor
              )}
            >
              {statusLabel}
            </span>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="p-4">
        {/* Status Badge (if no image) */}
        {!article.featured_image_path && (
          <div className="mb-2">
            <span
              className={clsx(
                'inline-flex items-center rounded-full px-3 py-1 text-xs font-medium',
                statusColor
              )}
            >
              {statusLabel}
            </span>
          </div>
        )}

        {/* Title */}
        <h3 className="mb-2 text-lg font-semibold text-gray-900 line-clamp-2 group-hover:text-blue-600">
          {article.title}
        </h3>

        {/* Excerpt */}
        {excerpt && (
          <p className="mb-3 text-sm text-gray-600 line-clamp-3">{excerpt}</p>
        )}

        {/* Metadata */}
        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
          {/* Date */}
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            <span>{formattedDate}</span>
          </div>

          {/* Category */}
          {article.category && (
            <div className="flex items-center gap-1">
              <FileText className="h-3 w-3" />
              <span>{article.category}</span>
            </div>
          )}

          {/* Tag Count */}
          {article.tags && article.tags.length > 0 && (
            <div className="flex items-center gap-1">
              <Tag className="h-3 w-3" />
              <span>{article.tags.length} 標籤</span>
            </div>
          )}

          {/* Published URL */}
          {article.published_url && (
            <a
              href={article.published_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-blue-600 hover:text-blue-700"
              onClick={(e) => e.stopPropagation()}
            >
              <ExternalLink className="h-3 w-3" />
              <span>查看</span>
            </a>
          )}
        </div>

        {/* Tags */}
        {article.tags && article.tags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {article.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
              >
                {tag}
              </span>
            ))}
            {article.tags.length > 3 && (
              <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                +{article.tags.length - 3}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );

  // Wrap in Link if not using custom onClick
  if (!onClick) {
    return (
      <Link to={`/articles/${article.id}`} className="block">
        {cardContent}
      </Link>
    );
  }

  return cardContent;
};

// Memoize the component to prevent unnecessary re-renders
// Only re-render if article changes
export const ArticleCard = React.memo(
  ArticleCardComponent,
  (prevProps, nextProps) => {
    return (
      prevProps.article.id === nextProps.article.id &&
      prevProps.article.updated_at === nextProps.article.updated_at &&
      prevProps.showExcerpt === nextProps.showExcerpt
    );
  }
);

export default ArticleCard;
