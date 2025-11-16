/**
 * Publish Success Card component.
 * Displays success message after publishing.
 */

import { Card, CardContent } from '@/components/ui';
import { PublishTask } from '@/types/publishing';
import { format } from 'date-fns';

export interface PublishSuccessCardProps {
  task: PublishTask;
  publishedUrl?: string;
  onViewPost?: () => void;
  onPublishAnother?: () => void;
  className?: string;
}

export const PublishSuccessCard: React.FC<PublishSuccessCardProps> = ({
  task,
  publishedUrl,
  onViewPost,
  onPublishAnother,
  className,
}) => {
  const duration = task.duration
    ? `${Math.floor(task.duration / 60)}分${task.duration % 60}秒`
    : '未知';

  return (
    <Card className={className}>
      <CardContent padding="p-6">
        <div className="text-center space-y-4">
        {/* Success Icon */}
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
            <svg
              className="w-8 h-8 text-green-600"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        </div>

        {/* Title */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            发布成功！🎉
          </h2>
          <p className="text-gray-600">
            文章《{task.article_title}》已成功发布到 WordPress
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 py-4">
          <div className="text-center">
            <p className="text-xs text-gray-500 mb-1">Provider</p>
            <p className="text-sm font-semibold text-gray-900 capitalize">
              {task.provider}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500 mb-1">耗时</p>
            <p className="text-sm font-semibold text-gray-900">{duration}</p>
          </div>
          {task.cost !== undefined && (
            <div className="text-center">
              <p className="text-xs text-gray-500 mb-1">成本</p>
              <p className="text-sm font-semibold text-green-600">
                ${task.cost.toFixed(3)}
              </p>
            </div>
          )}
        </div>

        {/* Published URL */}
        {publishedUrl && (
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">发布地址</p>
            <a
              href={publishedUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary-600 hover:underline break-all"
            >
              {publishedUrl}
            </a>
          </div>
        )}

        {/* Completion Time */}
        {task.completed_at && (
          <p className="text-xs text-gray-500">
            完成时间: {format(new Date(task.completed_at), 'yyyy-MM-dd HH:mm:ss')}
          </p>
        )}

        {/* Actions */}
        <div className="flex gap-3 justify-center pt-4">
          {onViewPost && publishedUrl && (
            <a
              href={publishedUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              查看文章
            </a>
          )}
          {onPublishAnother && (
            <button
              type="button"
              onClick={onPublishAnother}
              className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
            >
              继续发布
            </button>
          )}
        </div>

        {/* Screenshots Count */}
        {task.screenshots.length > 0 && (
          <p className="text-xs text-gray-500">
            共生成 {task.screenshots.length} 张执行截图
          </p>
        )}
        </div>
      </CardContent>
    </Card>
  );
};
