/**
 * Task Filters component.
 * Provides filtering options for task list.
 */

import { Select } from '@/components/ui';
import { PublishStatus, ProviderType } from '@/types/publishing';

export interface TaskFiltersProps {
  statusFilter: PublishStatus | 'all';
  providerFilter: ProviderType | 'all';
  onStatusFilterChange: (status: PublishStatus | 'all') => void;
  onProviderFilterChange: (provider: ProviderType | 'all') => void;
  className?: string;
}

export const TaskFilters: React.FC<TaskFiltersProps> = ({
  statusFilter,
  providerFilter,
  onStatusFilterChange,
  onProviderFilterChange,
  className,
}) => {
  const statusOptions = [
    { value: 'all', label: '全部状态' },
    { value: 'pending', label: '等待中' },
    { value: 'initializing', label: '初始化' },
    { value: 'logging_in', label: '登录中' },
    { value: 'creating_post', label: '创建文章' },
    { value: 'uploading_images', label: '上传图片' },
    { value: 'configuring_seo', label: '配置 SEO' },
    { value: 'publishing', label: '发布中' },
    { value: 'completed', label: '已完成' },
    { value: 'failed', label: '失败' },
  ];

  const providerOptions = [
    { value: 'all', label: '全部 Provider' },
    { value: 'playwright', label: '🎭 Playwright' },
    { value: 'computer_use', label: '🤖 Computer Use' },
    { value: 'hybrid', label: '⚡ Hybrid' },
  ];

  return (
    <div className={className}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Select
          label="状态筛选"
          value={statusFilter}
          onChange={(e) =>
            onStatusFilterChange(e.target.value as PublishStatus | 'all')
          }
          options={statusOptions}
          fullWidth
        />
        <Select
          label="Provider 筛选"
          value={providerFilter}
          onChange={(e) =>
            onProviderFilterChange(e.target.value as ProviderType | 'all')
          }
          options={providerOptions}
          fullWidth
        />
      </div>
    </div>
  );
};
