/**
 * Current Step Display component.
 * Shows the current publishing step with visual indicator.
 */

import { PublishStatus } from '@/types/publishing';
import { clsx } from 'clsx';

export interface CurrentStepDisplayProps {
  status: PublishStatus;
  currentStep: string;
  completedSteps: number;
  totalSteps: number;
  className?: string;
}

const STEP_INFO: Record<PublishStatus, { icon: string; label: string; color: string }> = {
  idle: { icon: '⏸️', label: '待发布', color: 'text-gray-600' },
  pending: { icon: '⏳', label: '等待中', color: 'text-gray-600' },
  initializing: { icon: '🔧', label: '初始化', color: 'text-blue-600' },
  logging_in: { icon: '🔑', label: '登录中', color: 'text-blue-600' },
  creating_post: { icon: '✍️', label: '创建文章', color: 'text-blue-600' },
  uploading_images: { icon: '🖼️', label: '上传图片', color: 'text-blue-600' },
  configuring_seo: { icon: '🔍', label: '配置 SEO', color: 'text-blue-600' },
  publishing: { icon: '🚀', label: '发布中', color: 'text-blue-600' },
  completed: { icon: '✅', label: '完成', color: 'text-green-600' },
  failed: { icon: '❌', label: '失败', color: 'text-red-600' },
};

export const CurrentStepDisplay: React.FC<CurrentStepDisplayProps> = ({
  status,
  currentStep,
  completedSteps,
  totalSteps,
  className,
}) => {
  const stepInfo = STEP_INFO[status];
  const progressPercent = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

  return (
    <div className={clsx('space-y-3', className)}>
      {/* Current Step */}
      <div className="flex items-center gap-3">
        <span className="text-3xl">{stepInfo.icon}</span>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <h4 className={clsx('font-semibold text-lg', stepInfo.color)}>
              {stepInfo.label}
            </h4>
            <span className="text-sm text-gray-500">
              {completedSteps}/{totalSteps} 步骤
            </span>
          </div>
          <p className="text-sm text-gray-600">{currentStep}</p>
        </div>
      </div>

      {/* Progress Bar */}
      {status !== 'idle' && status !== 'pending' && (
        <div className="space-y-1">
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className={clsx(
                'h-2 rounded-full transition-all duration-300',
                status === 'completed'
                  ? 'bg-green-500'
                  : status === 'failed'
                  ? 'bg-red-500'
                  : 'bg-blue-500'
              )}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>进度</span>
            <span>{Math.round(progressPercent)}%</span>
          </div>
        </div>
      )}

      {/* Status Message */}
      {status === 'completed' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <div className="flex items-center gap-2 text-green-700">
            <svg
              className="w-5 h-5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <span className="text-sm font-medium">文章已成功发布！</span>
          </div>
        </div>
      )}

      {status === 'failed' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-center gap-2 text-red-700">
            <svg
              className="w-5 h-5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <span className="text-sm font-medium">发布失败，请重试</span>
          </div>
        </div>
      )}
    </div>
  );
};
