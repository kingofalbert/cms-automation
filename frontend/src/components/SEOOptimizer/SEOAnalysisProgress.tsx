/**
 * SEO Analysis Progress component.
 * Shows analysis status with progress indicator.
 */

import { Spinner } from '@/components/ui';
import { clsx } from 'clsx';

export type AnalysisStatus = 'idle' | 'analyzing' | 'completed' | 'failed';

export interface SEOAnalysisProgressProps {
  status: AnalysisStatus;
  currentStep?: string;
  progress?: number; // 0-100
  error?: string;
  onRetry?: () => void;
  className?: string;
}

export const SEOAnalysisProgress: React.FC<SEOAnalysisProgressProps> = ({
  status,
  currentStep,
  progress = 0,
  error,
  onRetry,
  className,
}) => {
  if (status === 'idle') {
    return null;
  }

  return (
    <div className={clsx('border rounded-lg p-4', className)}>
      {status === 'analyzing' && (
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <Spinner size="md" variant="primary" />
            <div className="flex-1">
              <p className="font-medium text-gray-900">正在分析 SEO...</p>
              {currentStep && (
                <p className="text-sm text-gray-600 mt-1">{currentStep}</p>
              )}
            </div>
          </div>

          {progress > 0 && (
            <div className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">进度</span>
                <span className="text-gray-900 font-medium">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {status === 'completed' && (
        <div className="flex items-center gap-3 text-green-700">
          <svg className="w-6 h-6 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <p className="font-medium">SEO 分析完成</p>
            <p className="text-sm text-gray-600 mt-1">
              已生成优化建议和元数据
            </p>
          </div>
        </div>
      )}

      {status === 'failed' && (
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-red-700">
            <svg className="w-6 h-6 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div className="flex-1">
              <p className="font-medium">分析失败</p>
              {error && <p className="text-sm text-gray-600 mt-1">{error}</p>}
            </div>
          </div>

          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
            >
              重试
            </button>
          )}
        </div>
      )}
    </div>
  );
};
