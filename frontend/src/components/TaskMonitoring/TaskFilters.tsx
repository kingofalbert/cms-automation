/**
 * Task Filters component.
 * Provides filtering options for task list.
 */

import { Select } from '@/components/ui';
import { PublishStatus, ProviderType } from '@/types/publishing';
import { useTranslation } from 'react-i18next';

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
  const { t } = useTranslation();
  const statusValues: Array<PublishStatus | 'all'> = [
    'all',
    'idle',
    'pending',
    'initializing',
    'logging_in',
    'creating_post',
    'uploading_images',
    'configuring_seo',
    'publishing',
    'completed',
    'failed',
  ];

  const statusOptions = statusValues.map((value) => ({
    value,
    label:
      value === 'all'
        ? t('publishTasks.filters.statusOptions.all')
        : t(`publishTasks.statusLabels.${value}` as const),
  }));

  const providerValues: Array<ProviderType | 'all'> = [
    'all',
    'playwright',
    'computer_use',
    'hybrid',
  ];

  const providerOptions = providerValues.map((value) => ({
    value,
    label:
      value === 'all'
        ? t('publishTasks.filters.providerOptions.all')
        : t(`publishTasks.filters.providerOptions.${value}` as const),
  }));

  return (
    <div className={className}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Select
          label={t('publishTasks.filters.statusLabel')}
          value={statusFilter}
          onChange={(e) =>
            onStatusFilterChange(e.target.value as PublishStatus | 'all')
          }
          options={statusOptions}
          fullWidth
        />
        <Select
          label={t('publishTasks.filters.providerLabel')}
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
