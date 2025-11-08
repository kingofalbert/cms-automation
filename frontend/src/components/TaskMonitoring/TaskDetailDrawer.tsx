/**
 * Task Detail Drawer component.
 * Shows detailed information about a publishing task.
 */

import { Drawer, DrawerFooter, Button } from '@/components/ui';
import { PublishTask } from '@/types/publishing';
import { CurrentStepDisplay } from '../Publishing/CurrentStepDisplay';
import { ScreenshotGallery } from '../Publishing/ScreenshotGallery';
import { format } from 'date-fns';
import { useTranslation } from 'react-i18next';

export interface TaskDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  task: PublishTask | null;
  onRetry?: (taskId: string) => void;
}

export const TaskDetailDrawer: React.FC<TaskDetailDrawerProps> = ({
  isOpen,
  onClose,
  task,
  onRetry,
}) => {
  const { t } = useTranslation();
  if (!task) {
    return null;
  }

  const duration = task.duration
    ? t('publishTasks.detail.durationValue', {
        minutes: Math.floor(task.duration / 60),
        seconds: (task.duration % 60).toString().padStart(2, '0'),
      })
    : t('publishTasks.detail.durationInProgress');

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={t('publishTasks.detail.drawerTitle')}
      size="lg"
      position="right"
    >
      <div className="space-y-6">
        {/* Article Info */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">
            {t('publishTasks.detail.articleInfo')}
          </h3>
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">
                {t('publishTasks.detail.articleTitle')}:
              </span>
              <span className="text-sm font-medium text-gray-900 max-w-xs truncate">
                {task.article_title}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">
                {t('publishTasks.detail.taskId')}:
              </span>
              <span className="text-sm text-gray-900 font-mono">
                {task.id.substring(0, 8)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">
                {t('publishTasks.detail.provider')}:
              </span>
              <span className="text-sm text-gray-900 capitalize">
                {t(`publishTasks.filters.providerOptions.${task.provider}` as const)}
              </span>
            </div>
          </div>
        </div>

        {/* Status */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">
            {t('publishTasks.detail.executionStatus')}
          </h3>
          <CurrentStepDisplay
            status={task.status}
            currentStep={task.current_step}
            completedSteps={task.completed_steps}
            totalSteps={task.total_steps}
          />
        </div>

        {/* Metrics */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">
            {t('publishTasks.detail.metrics')}
          </h3>
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 mb-1">
                {t('publishTasks.detail.progress')}
              </p>
              <p className="text-xl font-bold text-primary-600">
                {task.progress}%
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 mb-1">
                {t('publishTasks.detail.duration')}
              </p>
              <p className="text-xl font-bold text-gray-900">{duration}</p>
            </div>
            {task.cost !== undefined && (
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">
                  {t('publishTasks.detail.cost')}
                </p>
                <p className="text-xl font-bold text-green-600">
                  ${task.cost.toFixed(3)}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Timeline */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">
            {t('publishTasks.detail.timeline')}
          </h3>
          <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">
                {t('publishTasks.detail.startedAt')}:
              </span>
              <span className="text-gray-900">
                {format(new Date(task.started_at), 'yyyy-MM-dd HH:mm:ss')}
              </span>
            </div>
            {task.completed_at && (
              <div className="flex justify-between">
                <span className="text-gray-600">
                  {t('publishTasks.detail.completedAt')}:
                </span>
                <span className="text-gray-900">
                  {format(new Date(task.completed_at), 'yyyy-MM-dd HH:mm:ss')}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Error Message */}
        {task.status === 'failed' && task.error_message && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">
              {t('publishTasks.detail.error')}
            </h3>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-700">{task.error_message}</p>
            </div>
          </div>
        )}

        {/* Screenshots */}
        {task.screenshots.length > 0 && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">
              {t('publishTasks.detail.screenshots', { count: task.screenshots.length })}
            </h3>
            <ScreenshotGallery screenshots={task.screenshots} />
          </div>
        )}
      </div>

      {/* Footer */}
      <DrawerFooter>
        <Button variant="outline" onClick={onClose}>
          {t('publishTasks.detail.close')}
        </Button>
        {task.status === 'failed' && onRetry && (
          <Button variant="primary" onClick={() => onRetry(task.id)}>
            {t('publishTasks.detail.retry')}
          </Button>
        )}
      </DrawerFooter>
    </Drawer>
  );
};
