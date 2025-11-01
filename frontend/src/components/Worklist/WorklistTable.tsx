/**
 * Worklist Table component.
 * Displays worklist items in a sortable table with status filtering.
 */

import { WorklistItem, WorklistStatus } from '@/types/worklist';
import { WorklistStatusBadge } from './WorklistStatusBadge';
import { format } from 'date-fns';
import { FileText, User, Calendar, RefreshCw } from 'lucide-react';

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
      to_evaluate: 1,
      to_confirm: 2,
      to_review: 3,
      to_revise: 4,
      to_rereview: 5,
      ready_to_publish: 6,
      published: 7,
    };
    return order[status];
  };

  // Sort items by status order and then by updated_at
  const sortedItems = [...items].sort((a, b) => {
    const statusDiff = getStatusOrder(a.status) - getStatusOrder(b.status);
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
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedItems.map((item) => (
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
                  <WorklistStatusBadge status={item.status} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm text-gray-900">
                    <User className="w-4 h-4 text-gray-400 mr-2" />
                    {item.author}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {item.metadata.word_count.toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-500">
                    {item.metadata.estimated_reading_time} 分钟
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {item.metadata.quality_score !== undefined ? (
                    <div className="flex items-center">
                      <span
                        className={`text-sm font-medium ${
                          item.metadata.quality_score >= 80
                            ? 'text-green-600'
                            : item.metadata.quality_score >= 60
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        }`}
                      >
                        {item.metadata.quality_score.toFixed(0)}
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
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
