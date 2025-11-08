/**
 * Task Status Badge component.
 * Displays the status of a publishing task with appropriate styling.
 */

import { Badge } from '@/components/ui';
import { PublishStatus } from '@/types/publishing';
import { useTranslation } from 'react-i18next';
import type { BadgeProps } from '@/components/ui';

export interface TaskStatusBadgeProps {
  status: PublishStatus;
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
}

type BadgeVariant = NonNullable<BadgeProps['variant']>;
const STATUS_VARIANT: Record<PublishStatus, BadgeVariant> = {
  idle: 'default',
  pending: 'secondary',
  initializing: 'info',
  logging_in: 'info',
  creating_post: 'info',
  uploading_images: 'info',
  configuring_seo: 'info',
  publishing: 'info',
  completed: 'success',
  failed: 'error',
};

export const TaskStatusBadge: React.FC<TaskStatusBadgeProps> = ({
  status,
  size = 'md',
  dot = true,
}) => {
  const { t } = useTranslation();

  return (
    <Badge variant={STATUS_VARIANT[status]} size={size} dot={dot}>
      {t(`publishTasks.statusLabels.${status}` as const)}
    </Badge>
  );
};
