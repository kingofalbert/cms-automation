/**
 * Worklist Table component.
 * Displays worklist items in a sortable table with status filtering.
 */

import { useNavigate } from 'react-router-dom';
import { WorklistItem, WorklistStatus, LEGACY_STATUS_MAP } from '@/types/worklist';
import { WorklistStatusBadge } from './WorklistStatusBadge';
import { format } from 'date-fns';
import { FileText, User, Calendar, RefreshCw, ClipboardCheck } from 'lucide-react';
import { Button } from '@/components/ui';
import { useTranslation } from 'react-i18next';

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
  const { t } = useTranslation();

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
    // Handle legacy status mapping
    const mappedStatus = LEGACY_STATUS_MAP[status] || status;

    const statuses: WorklistStatus[] = [
      'pending',
      'parsing',
      'parsing_review',
      'proofreading',
      'proofreading_review',
      'ready_to_publish',
      'publishing',
      'published',
      'failed',
    ];
    return statuses.includes(mappedStatus as WorklistStatus)
      ? (mappedStatus as WorklistStatus)
      : 'pending';
  };

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-primary-600" />
        <p className="mt-2 text-gray-500">{t('common.loading')}</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-500">{t('worklist.table.emptyTitle')}</p>
        <p className="text-sm text-gray-500 mt-1">{t('worklist.table.emptyDescription')}</p>
        {onSync && (
          <button
            onClick={onSync}
            disabled={isSyncing}
            className="mt-4 inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${isSyncing ? 'animate-spin' : ''}`}
            />
            {isSyncing ? t('worklist.table.syncing') : t('worklist.table.syncNow')}
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
      parsing: 2,
      parsing_review: 3,
      proofreading: 4,
      proofreading_review: 5,
      ready_to_publish: 6,
      publishing: 7,
      published: 8,
      failed: 9,
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
            {isSyncing ? t('worklist.table.syncing') : t('worklist.table.syncNow')}
          </button>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('worklist.table.columns.title')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('worklist.table.columns.status')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('worklist.table.columns.author')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('worklist.table.columns.wordCount')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('worklist.table.columns.quality')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('worklist.table.columns.updatedAt')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('worklist.table.columns.actions')}
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
                      {item.author || t('worklist.table.columns.unknownAuthor')}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {wordCount !== null ? wordCount.toLocaleString() : '—'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {readingTime !== null
                        ? t('worklist.table.wordStats.readingTime', { minutes: readingTime })
                        : '—'}
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
                        <span className="text-xs text-gray-500 ml-1">
                          {t('worklist.table.quality.outOf', { score: 100 })}
                        </span>
                      </div>
                    ) : (
                      <span className="text-sm text-gray-400">
                        {t('worklist.table.quality.unrated')}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm text-gray-500">
                      <Calendar className="w-4 h-4 mr-2" />
                      {formatDate(item.updated_at)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {/* Parsing Review - Review article parsing results (title, author, SEO, images) */}
                    {resolveStatus(item.status) === 'parsing_review' && item.article_id && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/articles/${item.article_id}/parsing`);
                        }}
                      >
                        <ClipboardCheck className="mr-2 h-4 w-4" />
                        {t('worklist.table.actions.reviewParsing')}
                      </Button>
                    )}

                    {/* Proofreading Review - Review proofreading issues (includes backward compat for legacy 'under_review') */}
                    {(resolveStatus(item.status) === 'proofreading_review' ||
                      item.status === 'under_review') && item.article_id && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/worklist/${item.id}/review`);
                        }}
                      >
                        <ClipboardCheck className="mr-2 h-4 w-4" />
                        {t('worklist.table.actions.reviewProofreading')}
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
