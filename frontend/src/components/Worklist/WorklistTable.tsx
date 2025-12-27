/**
 * Worklist Table component.
 * Displays worklist items in a sortable table with status filtering.
 *
 * Feature: View Original Google Doc (2025-12-25)
 * - Added "View Original" button to open original Google Doc in new window
 * - Uses drive_metadata.webViewLink or constructs URL from drive_file_id
 */

import { useNavigate } from 'react-router-dom';
import { WorklistItem, WorklistStatus, LEGACY_STATUS_MAP } from '@/types/worklist';
import { WorklistStatusBadge } from './WorklistStatusBadge';
import { format } from 'date-fns';
import {
  FileText,
  User,
  Calendar,
  RefreshCw,
  ClipboardCheck,
  Eye,
  Check,
  X,
  Send,
  ExternalLink,
  RotateCcw
} from 'lucide-react';
import { Button } from '@/components/ui';
import { useTranslation } from 'react-i18next';

export interface WorklistTableProps {
  items: WorklistItem[];
  onItemClick: (item: WorklistItem) => void;
  isLoading?: boolean;
  onSync?: () => void;
  isSyncing?: boolean;
  onPublish?: (item: WorklistItem) => void;
  onRetry?: (item: WorklistItem) => void;
}

export const WorklistTable: React.FC<WorklistTableProps> = ({
  items,
  onItemClick,
  isLoading,
  onSync,
  isSyncing,
  onPublish,
  onRetry,
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
                    <div className="flex items-center gap-2">
                      {/* View button - always visible */}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          onItemClick(item);
                        }}
                        aria-label={t('worklist.table.actions.view')}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>

                      {/* View Original Google Doc button */}
                      {(item.drive_metadata?.webViewLink || item.drive_file_id) && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            const url = item.drive_metadata?.webViewLink as string
                              || `https://docs.google.com/document/d/${item.drive_file_id}/edit`;
                            window.open(url, '_blank', 'noopener,noreferrer');
                          }}
                          aria-label={t('worklist.table.actions.viewOriginal')}
                          title={t('worklist.table.actions.viewOriginal')}
                        >
                          <ExternalLink className="h-4 w-4 text-blue-500" />
                        </Button>
                      )}

                      {/* Parsing Review - Review button */}
                      {resolveStatus(item.status) === 'parsing_review' && item.article_id && (
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/articles/${item.article_id}/parsing`);
                          }}
                          aria-label={t('worklist.table.actions.review')}
                          title={t('worklist.table.actions.review')}
                        >
                          <Check className="h-4 w-4" />
                        </Button>
                      )}

                      {/* Proofreading Review - Review button */}
                      {(resolveStatus(item.status) === 'proofreading_review' ||
                        item.status === 'under_review') && item.article_id && (
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/worklist/${item.id}/review`);
                          }}
                          aria-label={t('worklist.table.actions.review')}
                          title={t('worklist.table.actions.review')}
                        >
                          <Check className="h-4 w-4" />
                        </Button>
                      )}

                      {/* Ready to Publish - Publish button */}
                      {resolveStatus(item.status) === 'ready_to_publish' && (
                        <Button
                          size="sm"
                          variant="primary"
                          className="bg-green-600 hover:bg-green-700 text-white"
                          onClick={(e) => {
                            e.stopPropagation();
                            onPublish?.(item);
                          }}
                          aria-label={t('worklist.table.actions.publish')}
                        >
                          <Send className="h-4 w-4" />
                        </Button>
                      )}

                      {/* Published - Open URL button */}
                      {resolveStatus(item.status) === 'published' &&
                       item.metadata &&
                       typeof item.metadata === 'object' &&
                       'published_url' in item.metadata &&
                       typeof item.metadata.published_url === 'string' && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            window.open(item.metadata.published_url as string, '_blank');
                          }}
                          aria-label={t('worklist.table.actions.openUrl')}
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      )}

                      {/* Failed - Retry button */}
                      {resolveStatus(item.status) === 'failed' && (
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={(e) => {
                            e.stopPropagation();
                            onRetry?.(item);
                          }}
                          aria-label={t('worklist.table.actions.retry')}
                        >
                          <RotateCcw className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
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
