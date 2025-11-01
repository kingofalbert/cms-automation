/**
 * Publish Progress Modal component.
 * Shows real-time progress of publishing process.
 */

import { useEffect } from 'react';
import { Modal } from '@/components/ui';
import { PublishTask } from '@/types/publishing';
import { CurrentStepDisplay } from './CurrentStepDisplay';
import { ScreenshotGallery } from './ScreenshotGallery';
import { clsx } from 'clsx';

export interface PublishProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: PublishTask | null;
  closeOnOverlayClick?: boolean;
}

export const PublishProgressModal: React.FC<PublishProgressModalProps> = ({
  isOpen,
  onClose,
  task,
  closeOnOverlayClick = false,
}) => {
  // Auto-scroll to bottom when new screenshots arrive
  useEffect(() => {
    if (task && task.screenshots.length > 0) {
      const galleryElement = document.getElementById('screenshot-gallery');
      if (galleryElement) {
        galleryElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }
    }
  }, [task?.screenshots.length]);

  if (!task) {
    return null;
  }

  const canClose = task.status === 'completed' || task.status === 'failed';
  const duration = task.duration
    ? `${Math.floor(task.duration / 60)}:${(task.duration % 60)
        .toString()
        .padStart(2, '0')}`
    : null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={canClose ? onClose : () => {}}
      title={`发布进度 - ${task.article_title}`}
      size="lg"
      closeOnOverlayClick={canClose && closeOnOverlayClick}
    >
      <div className="space-y-6">
        {/* Current Step */}
        <CurrentStepDisplay
          status={task.status}
          currentStep={task.current_step}
          completedSteps={task.completed_steps}
          totalSteps={task.total_steps}
        />

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-500 mb-1">进度</p>
            <p className="text-2xl font-bold text-primary-600">
              {task.progress}%
            </p>
          </div>
          {duration && (
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">耗时</p>
              <p className="text-2xl font-bold text-gray-900">{duration}</p>
            </div>
          )}
          {task.cost !== undefined && (
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">成本</p>
              <p className="text-2xl font-bold text-green-600">
                ${task.cost.toFixed(3)}
              </p>
            </div>
          )}
        </div>

        {/* Error Message */}
        {task.status === 'failed' && task.error_message && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h4 className="font-semibold text-red-900 mb-2">错误详情</h4>
            <p className="text-sm text-red-700">{task.error_message}</p>
          </div>
        )}

        {/* Screenshots */}
        {task.screenshots.length > 0 && (
          <div id="screenshot-gallery">
            <h4 className="font-semibold text-gray-900 mb-3">
              执行截图 ({task.screenshots.length})
            </h4>
            <ScreenshotGallery screenshots={task.screenshots} />
          </div>
        )}

        {/* Loading Indicator */}
        {task.status !== 'completed' && task.status !== 'failed' && (
          <div className="flex items-center justify-center py-4">
            <div className="flex items-center gap-2 text-gray-600">
              <svg
                className="animate-spin h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <span className="text-sm">
                正在执行中，请勿关闭此窗口...
              </span>
            </div>
          </div>
        )}

        {/* Actions */}
        {canClose && (
          <div className="flex justify-end pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className={clsx(
                'px-6 py-2 rounded-lg font-medium transition-colors',
                task.status === 'completed'
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-600 text-white hover:bg-gray-700'
              )}
            >
              {task.status === 'completed' ? '完成' : '关闭'}
            </button>
          </div>
        )}
      </div>
    </Modal>
  );
};
