/**
 * Import History Table component.
 * Displays recent import operations with status.
 */

import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Badge, Spinner } from '@/components/ui';
import type { BadgeProps } from '@/components/ui';
import { ImportHistoryItem } from '@/types/article';
import { clsx } from 'clsx';
import { format } from 'date-fns';

export const ImportHistoryTable: React.FC = () => {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['import-history'],
    queryFn: async () => {
      const response = await axios.get<ImportHistoryItem[]>(
        '/v1/articles/import/history',
        { params: { limit: 10 } }
      );
      return response.data;
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
        <span className="ml-3 text-gray-600">加载导入历史...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">加载失败: {(error as Error).message}</p>
        <button
          onClick={() => refetch()}
          className="mt-3 text-primary-600 hover:underline"
        >
          重试
        </button>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="w-12 h-12 mx-auto text-gray-400"
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
        <p className="mt-3 text-gray-600">暂无导入历史</p>
        <p className="text-sm text-gray-500 mt-1">
          导入文章后，历史记录将显示在这里
        </p>
      </div>
    );
  }

  const getStatusBadge = (status: ImportHistoryItem['status']) => {
    type BadgeConfig = {
      variant: NonNullable<BadgeProps['variant']>;
      label: string;
      dot?: boolean;
    };

    const variants: Record<ImportHistoryItem['status'], BadgeConfig> = {
      pending: { variant: 'secondary', label: '等待中' },
      processing: { variant: 'info', label: '处理中', dot: true },
      completed: { variant: 'success', label: '已完成' },
      failed: { variant: 'error', label: '失败' },
    };
    const config = variants[status];
    return (
      <Badge variant={config.variant} dot={config.dot}>
        {config.label}
      </Badge>
    );
  };

  const getImportTypeBadge = (type: ImportHistoryItem['import_type']) => {
    const labels = {
      csv: 'CSV',
      json: 'JSON',
      manual: '手动',
    };
    return <Badge variant="default">{labels[type]}</Badge>;
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th className="px-4 py-3 text-left font-semibold text-gray-700">
              文件名
            </th>
            <th className="px-4 py-3 text-left font-semibold text-gray-700">
              类型
            </th>
            <th className="px-4 py-3 text-center font-semibold text-gray-700">
              总数
            </th>
            <th className="px-4 py-3 text-center font-semibold text-gray-700">
              成功
            </th>
            <th className="px-4 py-3 text-center font-semibold text-gray-700">
              失败
            </th>
            <th className="px-4 py-3 text-left font-semibold text-gray-700">
              状态
            </th>
            <th className="px-4 py-3 text-left font-semibold text-gray-700">
              导入时间
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {data.map((item) => {
            const successRate =
              item.total_count > 0
                ? ((item.success_count / item.total_count) * 100).toFixed(0)
                : 0;

            return (
              <tr
                key={item.id}
                className={clsx(
                  'hover:bg-gray-50 transition-colors',
                  item.status === 'failed' && 'bg-red-50'
                )}
              >
                <td className="px-4 py-3">
                  <div className="flex flex-col">
                    <span className="font-medium text-gray-900">
                      {item.filename}
                    </span>
                    {item.error_message && (
                      <span className="text-xs text-red-600 mt-1">
                        {item.error_message}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3">
                  {getImportTypeBadge(item.import_type)}
                </td>
                <td className="px-4 py-3 text-center text-gray-900">
                  {item.total_count}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className="text-green-600 font-medium">
                    {item.success_count}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span
                    className={clsx(
                      'font-medium',
                      item.failed_count > 0 ? 'text-red-600' : 'text-gray-400'
                    )}
                  >
                    {item.failed_count}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {getStatusBadge(item.status)}
                    {item.status === 'completed' && (
                      <span className="text-xs text-gray-500">
                        ({successRate}%)
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {format(new Date(item.created_at), 'yyyy-MM-dd HH:mm:ss')}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
