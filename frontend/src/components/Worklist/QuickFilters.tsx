/**
 * Quick Filters component for Worklist.
 * Provides 4 quick filter buttons for common worklist views.
 */

import { Bell, Loader, Check, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { WorklistStatus, WorklistItem } from '@/types/worklist';
import { cn } from '@/lib/utils';

export type QuickFilterKey = 'all' | 'needsAttention' | 'inProgress' | 'completed' | 'failed';

interface QuickFilter {
  key: QuickFilterKey;
  icon: React.ComponentType<{ className?: string }>;
  statuses: WorklistStatus[];
  color: 'orange' | 'blue' | 'green' | 'red' | 'gray';
}

const QUICK_FILTERS: QuickFilter[] = [
  {
    key: 'needsAttention',
    icon: Bell,
    statuses: ['parsing_review', 'proofreading_review', 'ready_to_publish'],
    color: 'orange',
  },
  {
    key: 'inProgress',
    icon: Loader,
    statuses: ['parsing', 'proofreading', 'publishing'],
    color: 'blue',
  },
  {
    key: 'completed',
    icon: Check,
    statuses: ['published'],
    color: 'green',
  },
  {
    key: 'failed',
    icon: AlertTriangle,
    statuses: ['failed'],
    color: 'red',
  },
];

interface QuickFiltersProps {
  items: WorklistItem[];
  activeFilter: QuickFilterKey;
  onFilterChange: (filter: QuickFilterKey) => void;
}

export const QuickFilters: React.FC<QuickFiltersProps> = ({
  items,
  activeFilter,
  onFilterChange,
}) => {
  const { t } = useTranslation();

  const getCount = (statuses: WorklistStatus[]): number => {
    return items.filter((item) => statuses.includes(item.status as WorklistStatus)).length;
  };

  const getColorClasses = (
    color: QuickFilter['color'],
    isActive: boolean
  ): { bg: string; text: string; border: string; badge: string } => {
    if (isActive) {
      return {
        bg: 'bg-primary-100',
        text: 'text-primary-700 font-semibold',
        border: 'border-primary-500 ring-2 ring-primary-200',
        badge: 'bg-primary-600',
      };
    }

    const colorMap = {
      orange: { badge: 'bg-orange-500' },
      blue: { badge: 'bg-blue-500' },
      green: { badge: 'bg-green-500' },
      red: { badge: 'bg-red-500' },
      gray: { badge: 'bg-gray-500' },
    };

    return {
      bg: 'bg-gray-100',
      text: 'text-gray-700',
      border: 'border-gray-200',
      badge: colorMap[color].badge,
    };
  };

  return (
    <div className="mb-6 overflow-x-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent pb-2 -mx-4 px-4 sm:mx-0 sm:px-0">
      <div className="flex gap-2 sm:gap-3 min-w-max">
        {/* All filter */}
        <button
          onClick={() => onFilterChange('all')}
          className={cn(
            'flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full transition-all',
            'border text-xs sm:text-sm font-medium whitespace-nowrap',
            activeFilter === 'all'
              ? 'bg-primary-100 text-primary-700 font-semibold border-primary-500 ring-2 ring-primary-200'
              : 'bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-200'
          )}
          aria-label={t('worklist.quickFilters.all')}
          aria-pressed={activeFilter === 'all'}
        >
          {t('worklist.quickFilters.all')}
          <span className={cn(
            'px-2 py-0.5 rounded-full text-xs font-semibold text-white',
            activeFilter === 'all' ? 'bg-primary-600' : 'bg-gray-500'
          )}>
            {items.length}
          </span>
        </button>

        {/* Quick filters */}
        {QUICK_FILTERS.map((filter) => {
          const Icon = filter.icon;
          const count = getCount(filter.statuses);
          const isActive = activeFilter === filter.key;
          const colors = getColorClasses(filter.color, isActive);

          return (
            <button
              key={filter.key}
              onClick={() => onFilterChange(filter.key)}
              className={cn(
                'flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full transition-all',
                'border text-xs sm:text-sm font-medium whitespace-nowrap',
                colors.bg,
                colors.text,
                colors.border,
                !isActive && 'hover:bg-gray-200'
              )}
              aria-label={t(`worklist.quickFilters.${filter.key}`)}
              aria-pressed={isActive}
            >
              <Icon className="w-4 h-4 sm:w-5 sm:h-5" aria-hidden="true" />
              {t(`worklist.quickFilters.${filter.key}`)}
              <span className={cn(
                'px-2 py-0.5 rounded-full text-xs font-semibold text-white',
                colors.badge
              )}>
                {count}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
