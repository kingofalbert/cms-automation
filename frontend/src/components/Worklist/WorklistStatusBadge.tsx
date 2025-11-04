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
      to_evaluate: {
        variant: 'secondary',
        label: '待评估',
        dot: true,
      },
      to_confirm: {
        variant: 'warning',
        label: '待确认',
        dot: true,
      },
      to_review: {
        variant: 'info',
        label: '待审稿',
        dot: true,
      },
      to_revise: {
        variant: 'error',
        label: '待修改',
        dot: true,
      },
      to_rereview: {
        variant: 'warning',
        label: '待复审',
        dot: true,
      },
      ready_to_publish: {
        variant: 'success',
        label: '待发布',
        dot: true,
      },
      published: {
        variant: 'default',
        label: '已发布',
        dot: false,
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
