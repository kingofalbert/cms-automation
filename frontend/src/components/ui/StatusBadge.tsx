/**
 * StatusBadge component - Unified workflow status display
 *
 * Color system for 9-state workflow:
 * - pending: Gray (neutral, waiting)
 * - parsing: Blue (automated processing)
 * - parsing_review: Amber (needs human review)
 * - proofreading: Purple (AI processing)
 * - proofreading_review: Orange (needs human review)
 * - ready_to_publish: Cyan (ready state)
 * - publishing: Indigo (in progress)
 * - published: Green (success)
 * - failed: Red (error)
 */

import React from 'react';
import { cn } from '../../lib/cn';
import {
  Clock,
  FileSearch,
  FileEdit,
  Sparkles,
  ClipboardCheck,
  CheckCircle2,
  Upload,
  Check,
  AlertCircle,
  Loader2,
} from 'lucide-react';

export type WorkflowStatus =
  | 'pending'
  | 'parsing'
  | 'parsing_review'
  | 'proofreading'
  | 'proofreading_review'
  | 'ready_to_publish'
  | 'publishing'
  | 'published'
  | 'failed'
  // Legacy statuses
  | 'under_review';

export interface StatusBadgeProps {
  status: WorkflowStatus | string;
  /** Show icon alongside text */
  showIcon?: boolean;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Show as dot indicator only (no text) */
  dotOnly?: boolean;
  /** Custom label override */
  label?: string;
  /** Additional className */
  className?: string;
  /** Show loading animation for in-progress states */
  animated?: boolean;
}

interface StatusConfig {
  label: string;
  labelZh: string;
  bgColor: string;
  textColor: string;
  borderColor: string;
  dotColor: string;
  icon: React.ComponentType<{ className?: string }>;
  isAnimated?: boolean;
}

const statusConfig: Record<string, StatusConfig> = {
  pending: {
    label: 'Pending',
    labelZh: '待处理',
    bgColor: 'bg-gray-100',
    textColor: 'text-gray-700',
    borderColor: 'border-gray-200',
    dotColor: 'bg-gray-400',
    icon: Clock,
  },
  parsing: {
    label: 'Parsing',
    labelZh: '解析中',
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-700',
    borderColor: 'border-blue-200',
    dotColor: 'bg-blue-500',
    icon: FileSearch,
    isAnimated: true,
  },
  parsing_review: {
    label: 'Parsing Review',
    labelZh: '解析审核',
    bgColor: 'bg-amber-100',
    textColor: 'text-amber-700',
    borderColor: 'border-amber-200',
    dotColor: 'bg-amber-500',
    icon: FileEdit,
  },
  proofreading: {
    label: 'Proofreading',
    labelZh: '校对中',
    bgColor: 'bg-purple-100',
    textColor: 'text-purple-700',
    borderColor: 'border-purple-200',
    dotColor: 'bg-purple-500',
    icon: Sparkles,
    isAnimated: true,
  },
  proofreading_review: {
    label: 'Proofreading Review',
    labelZh: '校对审核',
    bgColor: 'bg-orange-100',
    textColor: 'text-orange-700',
    borderColor: 'border-orange-200',
    dotColor: 'bg-orange-500',
    icon: ClipboardCheck,
  },
  // Legacy status
  under_review: {
    label: 'Under Review',
    labelZh: '审核中',
    bgColor: 'bg-orange-100',
    textColor: 'text-orange-700',
    borderColor: 'border-orange-200',
    dotColor: 'bg-orange-500',
    icon: ClipboardCheck,
  },
  ready_to_publish: {
    label: 'Ready',
    labelZh: '待发布',
    bgColor: 'bg-cyan-100',
    textColor: 'text-cyan-700',
    borderColor: 'border-cyan-200',
    dotColor: 'bg-cyan-500',
    icon: CheckCircle2,
  },
  publishing: {
    label: 'Publishing',
    labelZh: '发布中',
    bgColor: 'bg-indigo-100',
    textColor: 'text-indigo-700',
    borderColor: 'border-indigo-200',
    dotColor: 'bg-indigo-500',
    icon: Upload,
    isAnimated: true,
  },
  published: {
    label: 'Published',
    labelZh: '已发布',
    bgColor: 'bg-green-100',
    textColor: 'text-green-700',
    borderColor: 'border-green-200',
    dotColor: 'bg-green-500',
    icon: Check,
  },
  failed: {
    label: 'Failed',
    labelZh: '失败',
    bgColor: 'bg-red-100',
    textColor: 'text-red-700',
    borderColor: 'border-red-200',
    dotColor: 'bg-red-500',
    icon: AlertCircle,
  },
};

const sizeClasses = {
  sm: {
    badge: 'px-2 py-0.5 text-xs',
    icon: 'h-3 w-3',
    dot: 'h-1.5 w-1.5',
  },
  md: {
    badge: 'px-2.5 py-1 text-xs',
    icon: 'h-3.5 w-3.5',
    dot: 'h-2 w-2',
  },
  lg: {
    badge: 'px-3 py-1.5 text-sm',
    icon: 'h-4 w-4',
    dot: 'h-2.5 w-2.5',
  },
};

export function StatusBadge({
  status,
  showIcon = true,
  size = 'md',
  dotOnly = false,
  label: customLabel,
  className,
  animated = true,
}: StatusBadgeProps) {
  // Normalize status (handle legacy statuses)
  const normalizedStatus = status.toLowerCase().replace(/-/g, '_');
  const config = statusConfig[normalizedStatus] || statusConfig.pending;
  const sizeClass = sizeClasses[size];

  const Icon = config.icon;
  const shouldAnimate = animated && config.isAnimated;

  // Dot only mode
  if (dotOnly) {
    return (
      <span
        className={cn(
          'inline-block rounded-full',
          sizeClass.dot,
          config.dotColor,
          shouldAnimate && 'animate-pulse',
          className
        )}
        title={customLabel || config.label}
      />
    );
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border font-medium',
        config.bgColor,
        config.textColor,
        config.borderColor,
        sizeClass.badge,
        className
      )}
    >
      {showIcon && (
        shouldAnimate ? (
          <Loader2 className={cn(sizeClass.icon, 'animate-spin')} />
        ) : (
          <Icon className={sizeClass.icon} />
        )
      )}
      <span>{customLabel || config.label}</span>
    </span>
  );
}

/**
 * Get status color for custom use
 */
export function getStatusColor(status: string): {
  bg: string;
  text: string;
  border: string;
  dot: string;
} {
  const normalizedStatus = status.toLowerCase().replace(/-/g, '_');
  const config = statusConfig[normalizedStatus] || statusConfig.pending;
  return {
    bg: config.bgColor,
    text: config.textColor,
    border: config.borderColor,
    dot: config.dotColor,
  };
}

/**
 * Get all available status configurations
 */
export function getStatusConfig() {
  return statusConfig;
}
