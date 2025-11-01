/**
 * Publish Tasks Page
 * Displays and manages all publishing tasks.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Card } from '@/components/ui';
import { TaskListTable } from '@/components/TaskMonitoring/TaskListTable';
import { TaskFilters } from '@/components/TaskMonitoring/TaskFilters';
import { TaskDetailDrawer } from '@/components/TaskMonitoring/TaskDetailDrawer';
import { PublishTask, PublishStatus, ProviderType } from '@/types/publishing';

export default function PublishTasksPage() {
  const [statusFilter, setStatusFilter] = useState<PublishStatus | 'all'>('all');
  const [providerFilter, setProviderFilter] = useState<ProviderType | 'all'>('all');
  const [selectedTask, setSelectedTask] = useState<PublishTask | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Fetch tasks
  const { data: tasks = [], isLoading, refetch } = useQuery({
    queryKey: ['publish-tasks', statusFilter, providerFilter],
    queryFn: async () => {
      const params: any = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      if (providerFilter !== 'all') params.provider = providerFilter;

      const response = await axios.get<PublishTask[]>('/api/v1/publish/tasks', {
        params,
      });
      return response.data;
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const handleTaskClick = (task: PublishTask) => {
    setSelectedTask(task);
    setDrawerOpen(true);
  };

  const handleRetry = async (taskId: string) => {
    try {
      await axios.post(`/api/v1/publish/tasks/${taskId}/retry`);
      refetch();
      setDrawerOpen(false);
      alert('重试请求已提交');
    } catch (error: any) {
      alert(`重试失败: ${error.response?.data?.message || error.message}`);
    }
  };

  // Task statistics
  const stats = {
    total: tasks.length,
    completed: tasks.filter((t) => t.status === 'completed').length,
    failed: tasks.filter((t) => t.status === 'failed').length,
    inProgress: tasks.filter(
      (t) =>
        t.status !== 'completed' &&
        t.status !== 'failed' &&
        t.status !== 'idle'
    ).length,
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">发布任务监控</h1>
        <p className="mt-2 text-gray-600">
          实时查看所有文章发布任务的执行状态和详情
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">总任务数</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <svg
                className="w-6 h-6 text-blue-600"
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
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">已完成</p>
              <p className="text-2xl font-bold text-green-600">
                {stats.completed}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <svg
                className="w-6 h-6 text-green-600"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">进行中</p>
              <p className="text-2xl font-bold text-blue-600">
                {stats.inProgress}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <svg
                className="animate-spin w-6 h-6 text-blue-600"
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
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">失败</p>
              <p className="text-2xl font-bold text-red-600">{stats.failed}</p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              <svg
                className="w-6 h-6 text-red-600"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-6 p-6">
        <TaskFilters
          statusFilter={statusFilter}
          providerFilter={providerFilter}
          onStatusFilterChange={setStatusFilter}
          onProviderFilterChange={setProviderFilter}
        />
      </Card>

      {/* Task List */}
      <Card>
        <TaskListTable
          tasks={tasks}
          onTaskClick={handleTaskClick}
          isLoading={isLoading}
        />
      </Card>

      {/* Task Detail Drawer */}
      <TaskDetailDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        task={selectedTask}
        onRetry={handleRetry}
      />
    </div>
  );
}
