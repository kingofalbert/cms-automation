/**
 * Publish Error Card component.
 * Displays error message after failed publishing.
 */

import { Card } from '@/components/ui';
import { PublishTask } from '@/types/publishing';

export interface PublishErrorCardProps {
  task: PublishTask;
  onRetry?: () => void;
  onContactSupport?: () => void;
  className?: string;
}

export const PublishErrorCard: React.FC<PublishErrorCardProps> = ({
  task,
  onRetry,
  onContactSupport,
  className,
}) => {
  const duration = task.duration
    ? `${Math.floor(task.duration / 60)}分${task.duration % 60}秒`
    : '未知';

  const getErrorType = (message?: string): string => {
    if (!message) return '未知错误';
    if (message.includes('login') || message.includes('登录')) return '登录失败';
    if (message.includes('network') || message.includes('网络')) return '网络错误';
    if (message.includes('timeout') || message.includes('超时')) return '操作超时';
    if (message.includes('permission') || message.includes('权限')) return '权限不足';
    return '发布失败';
  };

  const getSuggestions = (message?: string): string[] => {
    const suggestions: string[] = [];

    if (message?.includes('login') || message?.includes('登录')) {
      suggestions.push('检查 WordPress 登录凭证是否正确');
      suggestions.push('确认账号是否有发布文章的权限');
    } else if (message?.includes('network') || message?.includes('网络')) {
      suggestions.push('检查网络连接是否正常');
      suggestions.push('确认 WordPress 网站是否可访问');
    } else if (message?.includes('timeout') || message?.includes('超时')) {
      suggestions.push('网站响应较慢，建议重试');
      suggestions.push('考虑使用 Computer Use Provider（更高容错性）');
    } else {
      suggestions.push('检查文章内容和格式是否正确');
      suggestions.push('尝试切换到 Hybrid Provider 重试');
      suggestions.push('查看执行截图了解失败原因');
    }

    return suggestions;
  };

  const errorType = getErrorType(task.error_message);
  const suggestions = getSuggestions(task.error_message);

  return (
    <Card className={className}>
      <div className="space-y-4 p-6">
        {/* Error Icon */}
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
            <svg
              className="w-8 h-8 text-red-600"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        </div>

        {/* Title */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {errorType}
          </h2>
          <p className="text-gray-600">
            文章《{task.article_title}》发布失败
          </p>
        </div>

        {/* Error Message */}
        {task.error_message && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h4 className="font-semibold text-red-900 text-sm mb-2">
              错误详情
            </h4>
            <p className="text-sm text-red-700">{task.error_message}</p>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 py-4 border-y">
          <div className="text-center">
            <p className="text-xs text-gray-500 mb-1">Provider</p>
            <p className="text-sm font-semibold text-gray-900 capitalize">
              {task.provider}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500 mb-1">失败于</p>
            <p className="text-sm font-semibold text-gray-900">
              步骤 {task.completed_steps}/{task.total_steps}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500 mb-1">耗时</p>
            <p className="text-sm font-semibold text-gray-900">{duration}</p>
          </div>
        </div>

        {/* Suggestions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 text-sm mb-2">
            💡 解决建议
          </h4>
          <ul className="space-y-1 text-sm text-blue-800">
            {suggestions.map((suggestion, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">•</span>
                <span>{suggestion}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Actions */}
        <div className="flex gap-3 justify-center pt-2">
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              重试发布
            </button>
          )}
          {onContactSupport && (
            <button
              type="button"
              onClick={onContactSupport}
              className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
            >
              联系支持
            </button>
          )}
        </div>

        {/* Screenshots Hint */}
        {task.screenshots.length > 0 && (
          <p className="text-xs text-center text-gray-500">
            提示：查看执行截图可帮助诊断问题（共 {task.screenshots.length} 张）
          </p>
        )}
      </div>
    </Card>
  );
};
