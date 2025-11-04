/**
 * Worklist Page
 * Manage articles from Google Drive with 7-state workflow.
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { Card, Select, Input, Button } from '@/components/ui';
import { WorklistTable } from '@/components/Worklist/WorklistTable';
import { WorklistDetailDrawer } from '@/components/Worklist/WorklistDetailDrawer';
import { WorklistStatistics } from '@/components/Worklist/WorklistStatistics';
import {
  WorklistItem,
  WorklistStatistics as Stats,
  WorklistStatus,
  WorklistFilters,
  DriveSyncStatus,
} from '@/types/worklist';
import { Search, Filter, RefreshCw } from 'lucide-react';

export default function WorklistPage() {
  const [filters, setFilters] = useState<WorklistFilters>({
    status: 'all',
    search: '',
  });
  const [selectedItem, setSelectedItem] = useState<WorklistItem | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Fetch worklist items
  const { data: items = [], isLoading, refetch } = useQuery({
    queryKey: ['worklist', filters],
    queryFn: async () => {
      const params: any = {};
      if (filters.status && filters.status !== 'all') params.status = filters.status;
      if (filters.search) params.search = filters.search;
      if (filters.author) params.author = filters.author;

      const response = await axios.get<WorklistItem[]>('v1/worklist', {
        params,
      });
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch statistics
  const { data: statistics } = useQuery({
    queryKey: ['worklist-statistics'],
    queryFn: async () => {
      const response = await axios.get<Stats>('v1/worklist/statistics');
      return response.data;
    },
    refetchInterval: 60000, // Refresh every minute
  });

  // Fetch sync status
  const { data: syncStatus } = useQuery({
    queryKey: ['drive-sync-status'],
    queryFn: async () => {
      const response = await axios.get<DriveSyncStatus>(
        'v1/worklist/sync-status'
      );
      return response.data;
    },
    refetchInterval: 5000, // Check every 5 seconds
  });

  // Sync with Google Drive
  const syncMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post('v1/worklist/sync');
      return response.data;
    },
    onSuccess: () => {
      alert('Google Drive 同步已开始');
      refetch();
    },
    onError: (error: any) => {
      alert(`同步失败: ${error.response?.data?.message || error.message}`);
    },
  });

  // Change item status
  const statusChangeMutation = useMutation({
    mutationFn: async ({
      itemId,
      newStatus,
      note,
    }: {
      itemId: string;
      newStatus: WorklistStatus;
      note?: string;
    }) => {
      const response = await axios.post(
        `/api/v1/worklist/${itemId}/status`,
        { status: newStatus, note }
      );
      return response.data;
    },
    onSuccess: () => {
      alert('状态变更成功');
      refetch();
      setDrawerOpen(false);
    },
    onError: (error: any) => {
      alert(`状态变更失败: ${error.response?.data?.message || error.message}`);
    },
  });

  // Publish to WordPress
  const publishMutation = useMutation({
    mutationFn: async (itemId: string) => {
      const response = await axios.post(`/api/v1/worklist/${itemId}/publish`);
      return response.data;
    },
    onSuccess: () => {
      alert('发布任务已提交');
      refetch();
      setDrawerOpen(false);
    },
    onError: (error: any) => {
      alert(`发布失败: ${error.response?.data?.message || error.message}`);
    },
  });

  const handleItemClick = (item: WorklistItem) => {
    setSelectedItem(item);
    setDrawerOpen(true);
  };

  const handleStatusChange = (
    itemId: string,
    newStatus: WorklistStatus,
    note?: string
  ) => {
    statusChangeMutation.mutate({ itemId, newStatus, note });
  };

  const handlePublish = (itemId: string) => {
    publishMutation.mutate(itemId);
  };

  const handleSync = () => {
    syncMutation.mutate();
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">工作清单</h1>
            <p className="mt-2 text-gray-600">
              管理来自 Google Drive 的文章，跟踪 7 阶段审稿流程
            </p>
          </div>

          {/* Sync Status */}
          {syncStatus && (
            <div className="text-sm text-gray-600">
              {syncStatus.is_syncing ? (
                <div className="flex items-center text-blue-600">
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  同步中... ({syncStatus.synced_files}/{syncStatus.total_files})
                </div>
              ) : (
                <div>
                  最后同步:{' '}
                  {new Date(syncStatus.last_sync_at).toLocaleString('zh-CN')}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="mb-8">
          <WorklistStatistics statistics={statistics} />
        </div>
      )}

      {/* Filters */}
      <Card className="mb-6 p-6">
        <div className="flex items-center mb-4">
          <Filter className="w-5 h-5 text-gray-500 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">筛选条件</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              type="text"
              placeholder="搜索标题或内容..."
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
              { value: 'all', label: '全部状态' },
              { value: 'to_evaluate', label: '待评估' },
              { value: 'to_confirm', label: '待确认' },
              { value: 'to_review', label: '待审稿' },
              { value: 'to_revise', label: '待修改' },
              { value: 'to_rereview', label: '待复审' },
              { value: 'ready_to_publish', label: '待发布' },
              { value: 'published', label: '已发布' },
            ]}
          />

          {/* Author Filter */}
          <Input
            type="text"
            placeholder="按作者筛选..."
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
              重置筛选
            </Button>
          </div>
        )}
      </Card>

      {/* Worklist Table */}
      <Card>
        <WorklistTable
          items={items}
          onItemClick={handleItemClick}
          isLoading={isLoading}
          onSync={handleSync}
          isSyncing={syncStatus?.is_syncing || syncMutation.isPending}
        />
      </Card>

      {/* Detail Drawer */}
      <WorklistDetailDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        item={selectedItem}
        onStatusChange={handleStatusChange}
        onPublish={handlePublish}
      />

      {/* Sync Errors */}
      {syncStatus && syncStatus.errors.length > 0 && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="text-sm font-medium text-red-800 mb-2">同步错误</h3>
          <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
            {syncStatus.errors.slice(0, 5).map((error, index) => (
              <li key={index}>{error}</li>
            ))}
            {syncStatus.errors.length > 5 && (
              <li>...还有 {syncStatus.errors.length - 5} 个错误</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
