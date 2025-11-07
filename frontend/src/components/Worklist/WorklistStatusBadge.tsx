/**
 * Worklist Status Badge component.
 * Displays status badge for worklist items with 7 states.
 */

import { WorklistStatus } from '@/types/worklist';
import { Badge } from '@/components/ui';
import type { BadgeProps } from '@/components/ui';

export interface WorklistStatusBadgeProps {
  status: WorklistStatus;
  size?: 'sm' | 'md' | 'lg';
}

export const WorklistStatusBadge: React.FC<WorklistStatusBadgeProps> = ({
  status,
  size = 'sm',
}) => {
  const getStatusConfig = (status: WorklistStatus) => {
    type BadgeVariant = NonNullable<BadgeProps['variant']>;
    const configs: Record<
      WorklistStatus,
      { variant: BadgeVariant; label: string; dot?: boolean }
    > = {
      pending: {
        variant: 'secondary',
        label: '待处理',
        dot: true,
      },
      proofreading: {
        variant: 'warning',
        label: '校对中',
        dot: true,
      },
      under_review: {
        variant: 'info',
        label: '审核中',
        dot: true,
      },
      ready_to_publish: {
        variant: 'success',
        label: '待发布',
        dot: true,
      },
      publishing: {
        variant: 'info',
        label: '发布中',
        dot: true,
      },
      published: {
        variant: 'default',
        label: '已发布',
        dot: false,
      },
      failed: {
        variant: 'error',
        label: '失败',
        dot: true,
      },
    };

    return configs[status];
  };

  const config = getStatusConfig(status);

  return (
    <Badge variant={config.variant} size={size} dot={config.dot}>
      {config.label}
    </Badge>
  );
};
