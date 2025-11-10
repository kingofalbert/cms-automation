/**
 * Worklist Status Badge component.
 * Displays status badge for worklist items with 9 states.
 */

import { WorklistStatus, LEGACY_STATUS_MAP } from '@/types/worklist';
import { Badge } from '@/components/ui';
import type { BadgeProps } from '@/components/ui';
import { useTranslation } from 'react-i18next';

export interface WorklistStatusBadgeProps {
  status: WorklistStatus | string;
  size?: 'sm' | 'md' | 'lg';
}

export const WorklistStatusBadge: React.FC<WorklistStatusBadgeProps> = ({
  status,
  size = 'sm',
}) => {
  const { t } = useTranslation();

  const getStatusConfig = (status: WorklistStatus | string) => {
    // Handle legacy status mapping
    const normalizedStatus = (LEGACY_STATUS_MAP[status] || status) as WorklistStatus;

    type BadgeVariant = NonNullable<BadgeProps['variant']>;
    const configs: Record<
      WorklistStatus,
      { variant: BadgeVariant; label: string; dot?: boolean }
    > = {
      pending: {
        variant: 'secondary',
        label: t('worklist.status.pending'),
        dot: true,
      },
      parsing: {
        variant: 'info',
        label: t('worklist.status.parsing'),
        dot: true,
      },
      parsing_review: {
        variant: 'info',
        label: t('worklist.status.parsing_review'),
        dot: true,
      },
      proofreading: {
        variant: 'warning',
        label: t('worklist.status.proofreading'),
        dot: true,
      },
      proofreading_review: {
        variant: 'info',
        label: t('worklist.status.proofreading_review'),
        dot: true,
      },
      ready_to_publish: {
        variant: 'success',
        label: t('worklist.status.ready_to_publish'),
        dot: true,
      },
      publishing: {
        variant: 'info',
        label: t('worklist.status.publishing'),
        dot: true,
      },
      published: {
        variant: 'default',
        label: t('worklist.status.published'),
        dot: false,
      },
      failed: {
        variant: 'error',
        label: t('worklist.status.failed'),
        dot: true,
      },
    };

    return configs[normalizedStatus] || configs.pending;
  };

  const config = getStatusConfig(status);

  return (
    <Badge variant={config.variant} size={size} dot={config.dot}>
      {config.label}
    </Badge>
  );
};
