/**
 * Worklist Page
 * Manage articles from Google Drive with 7-state workflow.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { api, apiClient, EXTENDED_TIMEOUT } from '@/services/api-client';
import { Card, Select, Input, Button } from '@/components/ui';
import { WorklistTable } from '@/components/Worklist/WorklistTable';
import { WorklistDetailDrawer } from '@/components/Worklist/WorklistDetailDrawer';
import { WorklistStatistics } from '@/components/Worklist/WorklistStatistics';
import { QuickFilters, QuickFilterKey } from '@/components/Worklist/QuickFilters';
import { ArticleReviewModal } from '@/components/ArticleReview';
import {
  WorklistItem,
  WorklistStatistics as Stats,
  WorklistStatus,
  WorklistFilters,
  DriveSyncStatus,
  WorklistListResponse,
  WorklistItemDetail,
} from '@/types/worklist';
import { Search, Filter, RefreshCw, CheckSquare, X } from 'lucide-react';
import { SkeletonStatsCard } from '@/components/ui/skeleton';
import { formatDate, DATE_FORMATS } from '@/lib/utils';

export default function WorklistPage() {
  const { t } = useTranslation();
  const [filters, setFilters] = useState<WorklistFilters>({
    status: 'all',
    search: '',
  });
  const [quickFilter, setQuickFilter] = useState<QuickFilterKey>('all');
  const [selectedItem, setSelectedItem] = useState<WorklistItem | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Batch selection state
  const [showSelection, setShowSelection] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  // Phase 8: ArticleReviewModal state
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [reviewContext, setReviewContext] = useState<{ worklistId: number; articleId: number } | null>(null);

  // Feature flag for Phase 8 (can be env variable later)
  const ENABLE_ARTICLE_REVIEW_MODAL = true; // TODO: Move to env config

  const queryClient = useQueryClient();

  // Fetch worklist items
  const {
    data: worklistData,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['worklist', filters],
    queryFn: async () => {
      const params: Record<string, string> = {
        limit: '25',
      };
      if (filters.status && filters.status !== 'all') params.status = filters.status;
      if (filters.search) params.search = filters.search;
      if (filters.author) params.author = filters.author;

      return await api.get<WorklistListResponse>('/v1/worklist', {
        params,
      });
    },
    refetchInterval: 60000, // Refresh every 60 seconds (reduced from 30s to save resources)
  });

  // Fetch statistics
  const { data: statistics, isLoading: isStatisticsLoading } = useQuery({
    queryKey: ['worklist-statistics'],
    queryFn: async () => {
      return await api.get<Stats>('/v1/worklist/statistics');
    },
    refetchInterval: 60000, // Refresh every minute
  });

  // Fetch sync status
  const { data: syncStatus } = useQuery({
    queryKey: ['drive-sync-status'],
    queryFn: async () => {
      return await api.get<DriveSyncStatus>('/v1/worklist/sync-status');
    },
    refetchInterval: 60000, // Check every 60 seconds (reduced from 5s to save resources)
  });

  const selectedItemId = selectedItem?.id;

  const {
    data: selectedDetail,
    isFetching: isDetailLoading,
  } = useQuery<WorklistItemDetail>({
    queryKey: ['worklist-detail', selectedItemId],
    queryFn: async () => await api.get(`/v1/worklist/${selectedItemId}`),
    enabled: drawerOpen && Boolean(selectedItemId),
  });

  // Sync with Google Drive (uses extended timeout for long-running operation)
  const syncMutation = useMutation({
    mutationFn: async () => {
      // Use extended timeout (3 minutes) for Google Drive sync operation
      // The sync can take a long time if there are many files or API is slow
      return await apiClient.post('/v1/worklist/sync', {}, { timeout: EXTENDED_TIMEOUT }).then(res => res.data);
    },
    onSuccess: (data: any) => {
      const summary = data?.summary;
      if (summary) {
        const message = t('worklist.messages.syncCompleted', {
          created: summary.created || 0,
          updated: summary.updated || 0,
        });
        alert(message);
      } else {
        alert(t('worklist.messages.syncStarted'));
      }
      refetch();
    },
    onError: (error: any) => {
      alert(`${t('worklist.messages.syncFailed')}: ${error.response?.data?.message || error.message}`);
    },
  });

  // Change item status
  const statusChangeMutation = useMutation({
    mutationFn: async ({
      itemId,
      newStatus,
      note,
    }: {
      itemId: number;
      newStatus: WorklistStatus;
      note?: string;
    }) => {
      return await api.post(`/v1/worklist/${itemId}/status`, {
        status: newStatus,
        note: note ? { message: note } : undefined,
      });
    },
    onSuccess: (_, variables) => {
      alert(t('worklist.messages.statusChanged'));
      refetch();
      queryClient.invalidateQueries({ queryKey: ['worklist-detail', variables.itemId] });
      queryClient.invalidateQueries({ queryKey: ['worklist'] });
    },
    onError: (error: any) => {
      alert(`${t('worklist.messages.statusChangeFailed')}: ${error.response?.data?.message || error.message}`);
    },
  });

  // Publish to WordPress
  // Use extended timeout for publishing (Playwright automation takes ~60-90 seconds)
  const publishMutation = useMutation({
    mutationFn: async (itemId: number) => {
      return await api.post(`/v1/worklist/${itemId}/publish`, undefined, { timeout: EXTENDED_TIMEOUT });
    },
    onSuccess: (_, itemId) => {
      alert(t('worklist.messages.publishSubmitted'));
      refetch();
      queryClient.invalidateQueries({ queryKey: ['worklist-detail', itemId] });
      queryClient.invalidateQueries({ queryKey: ['worklist'] });
    },
    onError: (error: any) => {
      alert(`${t('worklist.messages.publishFailed')}: ${error.response?.data?.message || error.message}`);
    },
  });

  const items = worklistData?.items ?? [];
  const syncErrors = Array.isArray(syncStatus?.errors)
    ? (syncStatus?.errors as string[])
    : [];

  // Apply quick filter to items
  const filteredItems = (() => {
    if (quickFilter === 'all') return items;

    const filterMap: Record<QuickFilterKey, WorklistStatus[]> = {
      all: [],
      needsAttention: ['parsing_review', 'proofreading_review', 'ready_to_publish'],
      inProgress: ['parsing', 'proofreading', 'publishing'],
      completed: ['published'],
      failed: ['failed'],
    };

    const statuses = filterMap[quickFilter];
    return items.filter((item) => statuses.includes(item.status as WorklistStatus));
  })();

  const handleItemClick = (item: WorklistItem) => {
    if (ENABLE_ARTICLE_REVIEW_MODAL) {
      if (!item.article_id) {
        alert('该工作项尚未关联文章，无法打开审核。');
        return;
      }
      setReviewContext({ worklistId: item.id, articleId: item.article_id });
      setReviewModalOpen(true);
    } else {
      setSelectedItem(item);
      setDrawerOpen(true);
    }
  };

  const handleReviewModalClose = () => {
    setReviewModalOpen(false);
    setReviewContext(null);
    refetch();
  };

  const handleQuickFilterChange = (filter: QuickFilterKey) => {
    setQuickFilter(filter);
  };

  const handleStatusChange = (
    itemId: number,
    newStatus: WorklistStatus,
    note?: string
  ) => {
    statusChangeMutation.mutate({ itemId, newStatus, note });
  };

  const handlePublish = (itemId: number) => {
    publishMutation.mutate(itemId);
  };

  const handleSync = () => {
    syncMutation.mutate();
  };

  return (
    <main className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{t('worklist.title')}</h1>
            <p className="mt-2 text-gray-600">
              {t('worklist.subtitle')}
            </p>
          </div>

          {/* Sync Status */}
          {syncStatus && (
            <div className="text-sm text-gray-600">
              {syncStatus.is_syncing ? (
                <div className="flex items-center text-blue-600">
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  {t('worklist.syncing')}
                </div>
              ) : (
                <div>
                  {t('worklist.lastSync')}:{' '}
                  {syncStatus.last_synced_at
                    ? formatDate(syncStatus.last_synced_at, DATE_FORMATS.FULL)
                    : t('worklist.neverSynced')}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Statistics */}
      <div className="mb-8">
        {isStatisticsLoading ? (
          <>
            {/* Skeleton for first row - 4 cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <SkeletonStatsCard key={`row1-${i}`} />
              ))}
              {/* Last card spans 2 columns on md+ */}
              <div className="md:col-span-2">
                <SkeletonStatsCard />
              </div>
            </div>
            {/* Skeleton for second row - 3 cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <SkeletonStatsCard key={`row2-${i}`} />
              ))}
            </div>
          </>
        ) : statistics ? (
          <WorklistStatistics statistics={statistics} />
        ) : null}
      </div>

      {/* Quick Filters */}
      <QuickFilters
        items={items}
        activeFilter={quickFilter}
        onFilterChange={handleQuickFilterChange}
      />

      {/* Filters */}
      <Card className="mb-6 p-6">
        <div className="flex items-center mb-4">
          <Filter className="w-5 h-5 text-gray-500 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">{t('worklist.filters.title')}</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              type="text"
              placeholder={t('worklist.filters.search')}
              value={filters.search || ''}
              onChange={(e) =>
                setFilters({ ...filters, search: e.target.value })
              }
              className="pl-10"
            />
          </div>

          {/* Status Filter */}
          <Select
            value={filters.status || 'all'}
            onChange={(e) =>
              setFilters({
                ...filters,
                status: e.target.value as WorklistStatus | 'all',
              })
            }
            options={[
              { value: 'all', label: t('worklist.status.all') },
              { value: 'pending', label: t('worklist.status.pending') },
              { value: 'proofreading', label: t('worklist.status.proofreading') },
              { value: 'under_review', label: t('worklist.status.under_review') },
              { value: 'ready_to_publish', label: t('worklist.status.ready_to_publish') },
              { value: 'publishing', label: t('worklist.status.publishing') },
              { value: 'published', label: t('worklist.status.published') },
              { value: 'failed', label: t('worklist.status.failed') },
            ]}
          />

          {/* Author Filter */}
          <Input
            type="text"
            placeholder={t('worklist.filters.author')}
            value={filters.author || ''}
            onChange={(e) =>
              setFilters({ ...filters, author: e.target.value })
            }
          />
        </div>

        {/* Reset Filters */}
        {(filters.status !== 'all' || filters.search || filters.author) && (
          <div className="mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                setFilters({ status: 'all', search: '', author: '' })
              }
            >
              {t('worklist.filters.reset')}
            </Button>
          </div>
        )}
      </Card>

      {/* Batch Actions Toolbar */}
      {showSelection && selectedIds.size > 0 && (
        <Card className="mb-4 p-4 bg-primary-50 border-primary-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CheckSquare className="w-5 h-5 text-primary-600" />
              <span className="font-medium text-primary-700">
                {t('worklist.table.selectedCount', { count: selectedIds.size })}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Select
                value=""
                onChange={(e) => {
                  if (e.target.value) {
                    const newStatus = e.target.value as WorklistStatus;
                    const statusLabel = t(`worklist.status.${newStatus}`);
                    if (window.confirm(t('worklist.table.batchStatusChangeConfirm', { count: selectedIds.size, status: statusLabel }))) {
                      // TODO: Implement batch status change API
                      console.log('Batch status change:', Array.from(selectedIds), newStatus);
                      alert(t('worklist.table.batchStatusChangeSuccess', { count: selectedIds.size }));
                      setSelectedIds(new Set());
                      refetch();
                    }
                  }
                }}
                options={[
                  { value: '', label: t('worklist.table.batchStatusChange') },
                  { value: 'pending', label: t('worklist.status.pending') },
                  { value: 'ready_to_publish', label: t('worklist.status.ready_to_publish') },
                  { value: 'failed', label: t('worklist.status.failed') },
                ]}
                className="min-w-[180px]"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSelectedIds(new Set());
                  setShowSelection(false);
                }}
              >
                <X className="w-4 h-4 mr-1" />
                {t('worklist.table.clearSelection')}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Batch Selection Toggle */}
      {!showSelection && (
        <div className="mb-4 flex justify-end">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSelection(true)}
          >
            <CheckSquare className="w-4 h-4 mr-2" />
            {t('worklist.table.batchActions')}
          </Button>
        </div>
      )}

      {/* Worklist Table */}
      <Card>
        <WorklistTable
          items={filteredItems}
          onItemClick={handleItemClick}
          isLoading={isLoading}
          onSync={handleSync}
          isSyncing={syncStatus?.is_syncing || syncMutation.isPending}
          onPublish={(item) => handlePublish(item.id)}
          onRetry={(item) => {
            // TODO: Implement retry logic
            console.log('Retry:', item);
          }}
          hasFilters={filters.status !== 'all' || !!filters.search || !!filters.author || quickFilter !== 'all'}
          onClearFilters={() => {
            setFilters({ status: 'all', search: '', author: '' });
            setQuickFilter('all');
          }}
          showSelection={showSelection}
          selectedIds={selectedIds}
          onSelectionChange={setSelectedIds}
        />
      </Card>

      {/* Detail Drawer */}
      <WorklistDetailDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        item={selectedItem}
        detail={selectedDetail}
        isLoading={isDetailLoading && drawerOpen}
        onStatusChange={handleStatusChange}
        onPublish={handlePublish}
      />

      {/* Sync Errors */}
      {syncErrors.length > 0 && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="text-sm font-medium text-red-800 mb-2">{t('worklist.errors.title')}</h3>
          <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
            {syncErrors.slice(0, 5).map((error, index) => (
              <li key={index}>{error}</li>
            ))}
            {syncErrors.length > 5 && (
              <li>{t('worklist.errors.moreErrors', { count: syncErrors.length - 5 })}</li>
            )}
          </ul>
        </div>
      )}

      {/* Phase 8: ArticleReviewModal */}
      {ENABLE_ARTICLE_REVIEW_MODAL && reviewModalOpen && reviewContext && (
        <ArticleReviewModal
          isOpen={reviewModalOpen}
          onClose={handleReviewModalClose}
          worklistItemId={reviewContext.worklistId}
          articleId={reviewContext.articleId}
        />
      )}
    </main>
  );
}
