/**
 * Task List Table component.
 * Displays a list of publishing tasks with sorting and pagination.
 */

import { useState } from 'react';
import { PublishTask } from '@/types/publishing';
import { TaskStatusBadge } from './TaskStatusBadge';
import { clsx } from 'clsx';
import { formatDate, DATE_FORMATS } from '@/lib/utils';
import { useTranslation } from 'react-i18next';

export interface TaskListTableProps {
  tasks: PublishTask[];
  onTaskClick: (task: PublishTask) => void;
  isLoading?: boolean;
  className?: string;
}

export const TaskListTable: React.FC<TaskListTableProps> = ({
  tasks,
  onTaskClick,
  isLoading = false,
  className,
}) => {
  const [sortBy, setSortBy] = useState<keyof PublishTask>('started_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const { t } = useTranslation();

  const handleSort = (column: keyof PublishTask) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  const sortedTasks = [...tasks].sort((a, b) => {
    const aValue = a[sortBy];
    const bValue = b[sortBy];

    if (aValue === undefined || bValue === undefined) return 0;

    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex items-center gap-3">
          <svg
            className="animate-spin h-6 w-6 text-primary-600"
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
          <span className="text-gray-600">{t('publishTasks.table.loading')}</span>
        </div>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="w-16 h-16 mx-auto text-gray-400 mb-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p className="text-gray-600 text-lg mb-2">
          {t('publishTasks.table.emptyTitle')}
        </p>
        <p className="text-gray-500 text-sm">
          {t('publishTasks.table.emptyDescription')}
        </p>
      </div>
    );
  }

  return (
    <div className={clsx('overflow-x-auto', className)}>
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th
              className="px-4 py-3 text-left font-semibold text-gray-700 cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort('article_title')}
            >
              {t('publishTasks.table.columns.article')}
              {sortBy === 'article_title' && (
                <span className="ml-1">
                  {sortOrder === 'asc' ? '↑' : '↓'}
                </span>
              )}
            </th>
            <th
              className="px-4 py-3 text-left font-semibold text-gray-700 cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort('provider')}
            >
              {t('publishTasks.table.columns.provider')}
              {sortBy === 'provider' && (
                <span className="ml-1">
                  {sortOrder === 'asc' ? '↑' : '↓'}
                </span>
              )}
            </th>
            <th
              className="px-4 py-3 text-left font-semibold text-gray-700 cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort('status')}
            >
              {t('publishTasks.table.columns.status')}
              {sortBy === 'status' && (
                <span className="ml-1">
                  {sortOrder === 'asc' ? '↑' : '↓'}
                </span>
              )}
            </th>
            <th className="px-4 py-3 text-center font-semibold text-gray-700">
              {t('publishTasks.table.columns.progress')}
            </th>
            <th className="px-4 py-3 text-center font-semibold text-gray-700">
              {t('publishTasks.table.columns.duration')}
            </th>
            <th className="px-4 py-3 text-center font-semibold text-gray-700">
              {t('publishTasks.table.columns.cost')}
            </th>
            <th
              className="px-4 py-3 text-left font-semibold text-gray-700 cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort('started_at')}
            >
              {t('publishTasks.table.columns.startedAt')}
              {sortBy === 'started_at' && (
                <span className="ml-1">
                  {sortOrder === 'asc' ? '↑' : '↓'}
                </span>
              )}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {sortedTasks.map((task) => {
            const duration = task.duration
              ? `${Math.floor(task.duration / 60)}:${(task.duration % 60)
                  .toString()
                  .padStart(2, '0')}`
              : '-';

            return (
              <tr
                key={task.id}
                onClick={() => onTaskClick(task)}
                className="hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <td className="px-4 py-3">
                  <p className="font-medium text-gray-900 max-w-xs truncate">
                    {task.article_title}
                  </p>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded capitalize">
                    {t(`publishTasks.filters.providerOptions.${task.provider}` as const)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <TaskStatusBadge status={task.status} size="sm" />
                </td>
                <td className="px-4 py-3 text-center">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className={clsx(
                          'h-2 rounded-full transition-all',
                          task.status === 'completed'
                            ? 'bg-green-500'
                            : task.status === 'failed'
                            ? 'bg-red-500'
                            : 'bg-blue-500'
                        )}
                        style={{ width: `${task.progress}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-600 w-10">
                      {task.progress}%
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 text-center text-gray-600">
                  {duration}
                </td>
                <td className="px-4 py-3 text-center">
                  {task.cost !== undefined ? (
                    <span className="text-green-600 font-medium">
                      ${task.cost.toFixed(3)}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {formatDate(task.started_at, DATE_FORMATS.SHORT)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
