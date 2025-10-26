/**
 * Article preview component for displaying generated articles.
 */

import { Badge, Card, CardContent, CardHeader } from '../ui';

interface ArticlePreviewProps {
  article: {
    id: number;
    title: string;
    body: string;
    status: string;
    created_at: string;
    article_metadata?: {
      word_count?: number;
      cost_usd?: number;
      input_tokens?: number;
      output_tokens?: number;
    };
  };
  onView?: (articleId: number) => void;
}

export function ArticlePreview({ article, onView }: ArticlePreviewProps) {
  const statusColors = {
    draft: 'bg-gray-100 text-gray-800',
    'in-review': 'bg-yellow-100 text-yellow-800',
    scheduled: 'bg-blue-100 text-blue-800',
    published: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  const getExcerpt = (body: string, length: number = 200) => {
    if (body.length <= length) return body;
    return body.substring(0, length) + '...';
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader
        title={article.title}
        description={
          <div className="flex items-center gap-2 mt-1">
            <Badge
              className={statusColors[article.status as keyof typeof statusColors] || statusColors.draft}
            >
              {article.status}
            </Badge>
            <span className="text-sm text-gray-500">
              {new Date(article.created_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
              })}
            </span>
          </div>
        }
      />
      <CardContent>
        <p className="text-gray-700 mb-4 line-clamp-3">{getExcerpt(article.body)}</p>

        {article.article_metadata && (
          <div className="grid grid-cols-2 gap-2 text-sm text-gray-600 mb-4">
            {article.article_metadata.word_count && (
              <div>
                <span className="font-medium">Words:</span> {article.article_metadata.word_count.toLocaleString()}
              </div>
            )}
            {article.article_metadata.cost_usd && (
              <div>
                <span className="font-medium">Cost:</span> ${article.article_metadata.cost_usd.toFixed(4)}
              </div>
            )}
            {article.article_metadata.input_tokens && (
              <div>
                <span className="font-medium">Input tokens:</span>{' '}
                {article.article_metadata.input_tokens.toLocaleString()}
              </div>
            )}
            {article.article_metadata.output_tokens && (
              <div>
                <span className="font-medium">Output tokens:</span>{' '}
                {article.article_metadata.output_tokens.toLocaleString()}
              </div>
            )}
          </div>
        )}

        {onView && (
          <button
            onClick={() => onView(article.id)}
            className="text-primary-600 hover:text-primary-700 font-medium text-sm"
          >
            View full article →
          </button>
        )}
      </CardContent>
    </Card>
  );
}
