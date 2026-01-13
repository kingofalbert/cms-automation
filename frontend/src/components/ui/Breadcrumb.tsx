/**
 * Breadcrumb Navigation Component
 *
 * Features:
 * - Builds navigation path from route hierarchy
 * - Clickable items (except current page)
 * - Handles dynamic route parameters
 * - Responsive with truncation for long paths
 * - Accessible with proper ARIA labels
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useTranslation } from 'react-i18next';

export interface BreadcrumbItem {
  /** Display label */
  label: string;
  /** Navigation path */
  href?: string;
  /** Whether this is the current page */
  isCurrent?: boolean;
  /** Optional icon */
  icon?: React.ReactNode;
}

export interface BreadcrumbProps {
  /** Override automatic breadcrumb items */
  items?: BreadcrumbItem[];
  /** Show home icon at the start */
  showHomeIcon?: boolean;
  /** Home path (default: /worklist) */
  homePath?: string;
  /** Custom separator */
  separator?: React.ReactNode;
  /** Maximum items to show (middle items will be collapsed) */
  maxItems?: number;
  /** Additional className */
  className?: string;
}

/**
 * Map route paths to readable labels
 */
const getRouteLabel = (
  segment: string,
  t: (key: string, options?: { defaultValue?: string }) => string
): string => {
  // Handle special route segments
  const labelMap: Record<string, string> = {
    worklist: t('navigation.worklist', { defaultValue: '工作清單' }),
    settings: t('navigation.settings', { defaultValue: '設定' }),
    articles: t('breadcrumb.articles', { defaultValue: '文章' }),
    review: t('breadcrumb.review', { defaultValue: '審核' }),
    parsing: t('breadcrumb.parsing', { defaultValue: '解析' }),
    'seo-confirmation': t('breadcrumb.seoConfirmation', { defaultValue: 'SEO 確認' }),
    pipeline: t('breadcrumb.pipeline', { defaultValue: 'Pipeline 監控' }),
  };

  return labelMap[segment] || segment;
};

/**
 * Check if a segment looks like an ID (number or UUID pattern)
 */
const isIdSegment = (segment: string): boolean => {
  return /^\d+$/.test(segment) || /^[a-f0-9-]{36}$/i.test(segment);
};

/**
 * Build breadcrumb items from current route
 */
const buildBreadcrumbsFromPath = (
  pathname: string,
  t: (key: string, options?: { defaultValue?: string }) => string,
  homePath: string
): BreadcrumbItem[] => {
  const items: BreadcrumbItem[] = [];
  const segments = pathname.split('/').filter(Boolean);

  // Always start with home/worklist
  items.push({
    label: t('navigation.worklist', { defaultValue: '工作清單' }),
    href: homePath,
    icon: <Home className="w-4 h-4" />,
  });

  let currentPath = '';

  for (let i = 0; i < segments.length; i++) {
    const segment = segments[i];
    currentPath += `/${segment}`;

    // Skip home segment if it's the same as homePath
    if (currentPath === homePath && i === 0) {
      continue;
    }

    // Skip displaying ID segments as separate items, but include in the path
    if (isIdSegment(segment)) {
      // If the next segment exists, we'll show it with context
      // Otherwise, show as "Article #ID"
      if (i === segments.length - 1) {
        items.push({
          label: `#${segment}`,
          isCurrent: true,
        });
      }
      continue;
    }

    const isLast = i === segments.length - 1;
    items.push({
      label: getRouteLabel(segment, t),
      href: isLast ? undefined : currentPath,
      isCurrent: isLast,
    });
  }

  return items;
};

/**
 * Single Breadcrumb Item Component
 */
const BreadcrumbItemComponent: React.FC<{
  item: BreadcrumbItem;
  isFirst?: boolean;
}> = ({ item, isFirst }) => {
  const content = (
    <span className="flex items-center gap-1.5">
      {item.icon && !isFirst && item.icon}
      <span className="max-w-[200px] truncate" title={item.label}>
        {item.label}
      </span>
    </span>
  );

  if (item.href && !item.isCurrent) {
    return (
      <Link
        to={item.href}
        className={cn(
          'text-gray-500 hover:text-gray-700 transition-colors',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded',
          isFirst && 'flex items-center gap-1.5'
        )}
      >
        {isFirst && item.icon}
        {content}
      </Link>
    );
  }

  return (
    <span
      className={cn(
        'font-medium',
        item.isCurrent ? 'text-gray-900' : 'text-gray-500'
      )}
      aria-current={item.isCurrent ? 'page' : undefined}
    >
      {content}
    </span>
  );
};

/**
 * Collapsed Items Indicator
 */
const CollapsedIndicator: React.FC<{ count: number }> = ({ count }) => (
  <span className="text-gray-400 px-1" title={`${count} more items`}>
    ...
  </span>
);

/**
 * Breadcrumb Component
 */
export const Breadcrumb: React.FC<BreadcrumbProps> = ({
  items: customItems,
  showHomeIcon = true,
  homePath = '/worklist',
  separator,
  maxItems = 5,
  className,
}) => {
  const { t } = useTranslation();
  const location = useLocation();

  // Use custom items or build from current path
  const items = customItems || buildBreadcrumbsFromPath(location.pathname, t, homePath);

  // Handle item collapse for long paths
  let displayItems = items;
  let collapsedCount = 0;

  if (items.length > maxItems) {
    // Keep first item, last 2 items, and collapse the rest
    const firstItem = items[0];
    const lastItems = items.slice(-2);
    collapsedCount = items.length - 3;
    displayItems = [firstItem, ...lastItems];
  }

  // Default separator
  const separatorElement = separator || (
    <ChevronRight className="h-4 w-4 text-gray-400 flex-shrink-0" aria-hidden="true" />
  );

  return (
    <nav aria-label={t('breadcrumb.ariaLabel', { defaultValue: '麵包屑導航' })} className={cn('', className)}>
      <ol className="flex items-center gap-2 text-sm flex-wrap">
        {displayItems.map((item, index) => (
          <li key={index} className="flex items-center gap-2">
            {/* Show separator before all items except first */}
            {index > 0 && separatorElement}

            {/* Show collapsed indicator after first item if needed */}
            {index === 1 && collapsedCount > 0 && (
              <>
                <CollapsedIndicator count={collapsedCount} />
                {separatorElement}
              </>
            )}

            <BreadcrumbItemComponent
              item={item}
              isFirst={index === 0 && showHomeIcon}
            />
          </li>
        ))}
      </ol>
    </nav>
  );
};

/**
 * Simple Breadcrumb for use within page headers
 * Provides a more compact display
 */
export const PageBreadcrumb: React.FC<{
  items: BreadcrumbItem[];
  className?: string;
}> = ({ items, className }) => {
  const { t } = useTranslation();

  return (
    <nav
      aria-label={t('breadcrumb.ariaLabel', { defaultValue: '麵包屑導航' })}
      className={cn('flex items-center gap-2 text-sm text-gray-500', className)}
    >
      {items.map((item, index) => (
        <React.Fragment key={index}>
          {index > 0 && (
            <ChevronRight className="h-4 w-4 text-gray-400" aria-hidden="true" />
          )}
          {item.href && !item.isCurrent ? (
            <Link
              to={item.href}
              className="hover:text-gray-700 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded"
            >
              {item.label}
            </Link>
          ) : (
            <span
              className={item.isCurrent ? 'text-gray-900 font-medium' : ''}
              aria-current={item.isCurrent ? 'page' : undefined}
            >
              {item.label}
            </span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

Breadcrumb.displayName = 'Breadcrumb';
PageBreadcrumb.displayName = 'PageBreadcrumb';
