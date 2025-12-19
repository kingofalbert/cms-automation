/**
 * EmptyState component - Display when no data is available
 */

import React from 'react';
import { cn } from '../../lib/cn';
import {
  FileText,
  Search,
  AlertCircle,
  CheckCircle,
  Inbox,
  BarChart3,
  Settings,
  FileQuestion
} from 'lucide-react';
import { Button } from './button';

export interface EmptyStateProps {
  /** Icon to display - can be a Lucide icon name or custom React node */
  icon?: 'document' | 'search' | 'error' | 'success' | 'inbox' | 'chart' | 'settings' | 'question' | React.ReactNode;
  /** Main title text */
  title: string;
  /** Description text */
  description?: string;
  /** Primary action button */
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'default' | 'outline' | 'secondary';
  };
  /** Secondary action button */
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Additional className */
  className?: string;
}

type IconName = 'document' | 'search' | 'error' | 'success' | 'inbox' | 'chart' | 'settings' | 'question';

const iconMap: Record<IconName, React.ComponentType<{ className?: string }>> = {
  document: FileText,
  search: Search,
  error: AlertCircle,
  success: CheckCircle,
  inbox: Inbox,
  chart: BarChart3,
  settings: Settings,
  question: FileQuestion,
};

const sizeConfig = {
  sm: {
    iconSize: 'h-10 w-10',
    titleSize: 'text-base',
    descSize: 'text-sm',
    padding: 'p-6',
    gap: 'gap-2',
  },
  md: {
    iconSize: 'h-14 w-14',
    titleSize: 'text-lg',
    descSize: 'text-sm',
    padding: 'p-8',
    gap: 'gap-3',
  },
  lg: {
    iconSize: 'h-20 w-20',
    titleSize: 'text-xl',
    descSize: 'text-base',
    padding: 'p-12',
    gap: 'gap-4',
  },
};

export function EmptyState({
  icon = 'inbox',
  title,
  description,
  action,
  secondaryAction,
  size = 'md',
  className,
}: EmptyStateProps) {
  const config = sizeConfig[size];

  // Render icon
  const renderIcon = () => {
    if (React.isValidElement(icon)) {
      return icon;
    }

    if (typeof icon === 'string' && icon in iconMap) {
      const IconComponent = iconMap[icon as IconName];
      return <IconComponent className={cn(config.iconSize, 'text-gray-300')} />;
    }

    return <Inbox className={cn(config.iconSize, 'text-gray-300')} />;
  };

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center',
        config.padding,
        className
      )}
    >
      {/* Icon container with subtle background */}
      <div className="mb-4 rounded-full bg-gray-50 p-4">
        {renderIcon()}
      </div>

      {/* Title */}
      <h3 className={cn('font-semibold text-gray-900', config.titleSize, config.gap)}>
        {title}
      </h3>

      {/* Description */}
      {description && (
        <p className={cn('mt-2 max-w-sm text-gray-500', config.descSize)}>
          {description}
        </p>
      )}

      {/* Actions */}
      {(action || secondaryAction) && (
        <div className={cn('mt-6 flex items-center', config.gap)}>
          {action && (
            <Button
              onClick={action.onClick}
              variant={action.variant || 'default'}
            >
              {action.label}
            </Button>
          )}
          {secondaryAction && (
            <Button
              onClick={secondaryAction.onClick}
              variant="outline"
            >
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Pre-configured empty states for common scenarios
 */

export function EmptyStateNoIssues({ onBack }: { onBack?: () => void }) {
  return (
    <EmptyState
      icon="success"
      title="No Issues Found"
      description="Great job! This article has no proofreading issues."
      action={onBack ? { label: 'Back to Worklist', onClick: onBack } : undefined}
      size="lg"
    />
  );
}

export function EmptyStateNoData({ onRefresh }: { onRefresh?: () => void }) {
  return (
    <EmptyState
      icon="chart"
      title="No Data Available"
      description="Complete some proofreading reviews to see statistics here."
      action={onRefresh ? { label: 'Refresh', onClick: onRefresh, variant: 'outline' } : undefined}
    />
  );
}

export function EmptyStateSearchNoResults({
  query,
  onClear
}: {
  query?: string;
  onClear?: () => void
}) {
  return (
    <EmptyState
      icon="search"
      title="No Results Found"
      description={query ? `No items match "${query}". Try adjusting your search or filters.` : 'No items match your search criteria.'}
      action={onClear ? { label: 'Clear Search', onClick: onClear, variant: 'outline' } : undefined}
      size="sm"
    />
  );
}

export function EmptyStateError({
  message,
  onRetry
}: {
  message?: string;
  onRetry?: () => void
}) {
  return (
    <EmptyState
      icon="error"
      title="Something Went Wrong"
      description={message || 'An error occurred while loading data. Please try again.'}
      action={onRetry ? { label: 'Try Again', onClick: onRetry } : undefined}
    />
  );
}

export function EmptyStateNoArticle({ onBack }: { onBack?: () => void }) {
  return (
    <EmptyState
      icon="document"
      title="Article Not Found"
      description="The requested article could not be found or may have been deleted."
      action={onBack ? { label: 'Back to Worklist', onClick: onBack } : undefined}
    />
  );
}
