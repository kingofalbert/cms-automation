/**
 * Worklist Status Badge component.
 * Displays status badge for worklist items with 9 states, icons, and animations.
 */

import { Clock, Loader, ClipboardCheck, Check, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { WorklistStatus, LEGACY_STATUS_MAP } from '@/types/worklist';
import { cn } from '@/lib/utils';

export interface WorklistStatusBadgeProps {
  status: WorklistStatus | string;
  showText?: boolean; // For mobile: icon only when false
}

interface StatusConfig {
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
  label: string;
  pulse: boolean;
}

const STATUS_CONFIG: Record<WorklistStatus, StatusConfig> = {
  pending: {
    icon: Clock,
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
    label: 'worklist.status.pending',
    pulse: false,
  },
  parsing: {
    icon: Loader,
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    label: 'worklist.status.parsing',
    pulse: true,
  },
  parsing_review: {
    icon: ClipboardCheck,
    color: 'text-orange-700',
    bgColor: 'bg-orange-100',
    label: 'worklist.status.parsing_review',
    pulse: false,
  },
  proofreading: {
    icon: Loader,
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    label: 'worklist.status.proofreading',
    pulse: true,
  },
  proofreading_review: {
    icon: ClipboardCheck,
    color: 'text-orange-700',
    bgColor: 'bg-orange-100',
    label: 'worklist.status.proofreading_review',
    pulse: false,
  },
  ready_to_publish: {
    icon: ClipboardCheck,
    color: 'text-orange-700',
    bgColor: 'bg-orange-100',
    label: 'worklist.status.ready_to_publish',
    pulse: false,
  },
  publishing: {
    icon: Loader,
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    label: 'worklist.status.publishing',
    pulse: true,
  },
  published: {
    icon: Check,
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    label: 'worklist.status.published',
    pulse: false,
  },
  failed: {
    icon: X,
    color: 'text-red-700',
    bgColor: 'bg-red-100',
    label: 'worklist.status.failed',
    pulse: false,
  },
};

export const WorklistStatusBadge: React.FC<WorklistStatusBadgeProps> = ({
  status,
  showText = true,
}) => {
  const { t } = useTranslation();

  // Handle legacy status mapping
  const normalizedStatus = (LEGACY_STATUS_MAP[status] || status) as WorklistStatus;
  const config = STATUS_CONFIG[normalizedStatus] || STATUS_CONFIG.pending;
  const Icon = config.icon;

  const statusDescription = t(`worklist.statusDescriptions.${normalizedStatus}`, {
    defaultValue: t(config.label),
  });

  return (
    <span
      className={cn(
        'inline-flex items-center gap-2 px-3 py-1 rounded-full',
        'text-sm font-medium transition-all',
        config.bgColor,
        config.color,
        config.pulse && 'animate-pulse'
      )}
      title={statusDescription}
      aria-label={statusDescription}
    >
      <Icon
        className={cn(
          'w-4 h-4',
          config.pulse && 'animate-spin'
        )}
        aria-hidden="true"
      />
      {showText && (
        <span className="hidden md:inline">{t(config.label)}</span>
      )}
    </span>
  );
};
