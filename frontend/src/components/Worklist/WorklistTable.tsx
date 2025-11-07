/**
 * Worklist Table component.
 * Displays worklist items in a sortable table with status filtering.
 */

import { useNavigate } from 'react-router-dom';
import { WorklistItem, WorklistStatus } from '@/types/worklist';
import { WorklistStatusBadge } from './WorklistStatusBadge';
import { format } from 'date-fns';
import { FileText, User, Calendar, RefreshCw, ClipboardCheck } from 'lucide-react';
import { Button } from '@/components/ui';

export interface WorklistTableProps {
  items: WorklistItem[];
  onItemClick: (item: WorklistItem) => void;
  isLoading?: boolean;
  onSync?: () => void;
  isSyncing?: boolean;
}

export const WorklistTable: React.FC<WorklistTableProps> = ({
  items,
  onItemClick,
  isLoading,
  onSync,
  isSyncing,
}) => {
  const navigate = useNavigate();

  const safeNumber = (value: unknown): number | null => {
    if (typeof value === 'number' && !Number.isNaN(value)) {
      return value;
    }
    if (typeof value === 'string') {
      const parsed = Number(value);
      if (!Number.isNaN(parsed)) {
        return parsed;
      }
    }
    return null;
  };

  const resolveStatus = (status: WorklistStatus | string): WorklistStatus => {
    const statuses: WorklistStatus[] = [
      'pending',
      'proofreading',
      'under_review',
      'ready_to_publish',
      'publishing',
      'published',
      'failed',
    ];
    return statuses.includes(status as WorklistStatus)
      ? (status as WorklistStatus)
      : 'pending';
  };

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-primary-600" />
        <p className="mt-2 text-gray-500">加载中...</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-500">暂无工作清单项</p>
        {onSync && (
          <button
            onClick={onSync}
            disabled={isSyncing}
            className="mt-4 inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${isSyncing ? 'animate-spin' : ''}`}
            />
            {isSyncing ? '同步中...' : '从 Google Drive 同步'}
          </button>
        )}
      </div>
    );
  }

  const formatDate = (dateStr: string) => {
    try {
      return format(new Date(dateStr), 'yyyy-MM-dd HH:mm');
    } catch {
      return dateStr;
    }
  };

  const getStatusOrder = (status: WorklistStatus): number => {
    const order: Record<WorklistStatus, number> = {
      pending: 1,
      proofreading: 2,
      under_review: 3,
      ready_to_publish: 4,
      publishing: 5,
      published: 6,
      failed: 7,
    };
    return order[status];
  };

  // Sort items by status order and then by updated_at
  const sortedItems = [...items].sort((a, b) => {
    const statusDiff =
      getStatusOrder(resolveStatus(a.status)) -
      getStatusOrder(resolveStatus(b.status));
    if (statusDiff !== 0) return statusDiff;
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
  });

  return (
    <div>
      {/* Sync Button */}
      {onSync && (
        <div className="mb-4 flex justify-end">
          <button
            onClick={onSync}
            disabled={isSyncing}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${isSyncing ? 'animate-spin' : ''}`}
            />
            {isSyncing ? '同步中...' : '同步 Google Drive'}
          </button>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                标题
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                状态
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                作者
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                字数
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                质量分数
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                更新时间
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedItems.map((item) => {
              const wordCount = safeNumber(item.metadata?.word_count);
              const readingTime = safeNumber(item.metadata?.estimated_reading_time);
              const qualityScore = safeNumber(item.metadata?.quality_score);

              return (
                <tr
                  key={item.id}
                  onClick={() => onItemClick(item)}
                  className="hover:bg-gray-50 cursor-pointer"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <FileText className="w-5 h-5 text-gray-400 mr-2" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {item.title}
                        </div>
                        {item.tags && item.tags.length > 0 && (
                          <div className="text-xs text-gray-500 mt-1">
                            {item.tags.slice(0, 3).join(', ')}
                            {item.tags.length > 3 && ` +${item.tags.length - 3}`}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <WorklistStatusBadge status={resolveStatus(item.status)} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm text-gray-900">
                      <User className="w-4 h-4 text-gray-400 mr-2" />
                      {item.author || '未知作者'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {wordCount !== null ? wordCount.toLocaleString() : '—'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {readingTime !== null ? `${readingTime} 分钟` : '—'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {qualityScore !== null ? (
                      <div className="flex items-center">
                        <span
                          className={`text-sm font-medium ${
                            qualityScore >= 80
                              ? 'text-green-600'
                              : qualityScore >= 60
                              ? 'text-yellow-600'
                              : 'text-red-600'
                          }`}
                        >
                          {qualityScore.toFixed(0)}
                        </span>
                        <span className="text-xs text-gray-500 ml-1">/ 100</span>
                      </div>
                    ) : (
                      <span className="text-sm text-gray-400">未评分</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm text-gray-500">
                      <Calendar className="w-4 h-4 mr-2" />
                      {formatDate(item.updated_at)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {resolveStatus(item.status) === 'under_review' && item.article_id && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/worklist/${item.id}/review`);
                        }}
                      >
                        <ClipboardCheck className="mr-2 h-4 w-4" />
                        审核
                      </Button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
