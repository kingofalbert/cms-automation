/**
 * Task Detail Drawer component.
 * Shows detailed information about a publishing task.
 */

import { Drawer, DrawerFooter, Button } from '@/components/ui';
import { PublishTask } from '@/types/publishing';
import { CurrentStepDisplay } from '../Publishing/CurrentStepDisplay';
import { ScreenshotGallery } from '../Publishing/ScreenshotGallery';
import { format } from 'date-fns';

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
  if (!task) {
    return null;
  }

  const duration = task.duration
    ? `${Math.floor(task.duration / 60)}分${task.duration % 60}秒`
    : '进行中';

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title="任务详情"
      size="lg"
      position="right"
    >
      <div className="space-y-6">
        {/* Article Info */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">文章信息</h3>
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">标题:</span>
              <span className="text-sm font-medium text-gray-900 max-w-xs truncate">
                {task.article_title}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">任务 ID:</span>
              <span className="text-sm text-gray-900 font-mono">
                {task.id.substring(0, 8)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Provider:</span>
              <span className="text-sm text-gray-900 capitalize">
                {task.provider}
              </span>
            </div>
          </div>
        </div>

        {/* Status */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">执行状态</h3>
          <CurrentStepDisplay
            status={task.status}
            currentStep={task.current_step}
            completedSteps={task.completed_steps}
            totalSteps={task.total_steps}
          />
        </div>

        {/* Metrics */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">执行指标</h3>
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 mb-1">进度</p>
              <p className="text-xl font-bold text-primary-600">
                {task.progress}%
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 mb-1">耗时</p>
              <p className="text-xl font-bold text-gray-900">{duration}</p>
            </div>
            {task.cost !== undefined && (
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">成本</p>
                <p className="text-xl font-bold text-green-600">
                  ${task.cost.toFixed(3)}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Timeline */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">时间线</h3>
          <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">开始时间:</span>
              <span className="text-gray-900">
                {format(new Date(task.started_at), 'yyyy-MM-dd HH:mm:ss')}
              </span>
            </div>
            {task.completed_at && (
              <div className="flex justify-between">
                <span className="text-gray-600">完成时间:</span>
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
            <h3 className="font-semibold text-gray-900 mb-2">错误信息</h3>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-700">{task.error_message}</p>
            </div>
          </div>
        )}

        {/* Screenshots */}
        {task.screenshots.length > 0 && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">
              执行截图 ({task.screenshots.length})
            </h3>
            <ScreenshotGallery screenshots={task.screenshots} />
          </div>
        )}
      </div>

      {/* Footer */}
      <DrawerFooter>
        <Button variant="outline" onClick={onClose}>
          关闭
        </Button>
        {task.status === 'failed' && onRetry && (
          <Button variant="primary" onClick={() => onRetry(task.id)}>
            重试
          </Button>
        )}
      </DrawerFooter>
    </Drawer>
  );
};
