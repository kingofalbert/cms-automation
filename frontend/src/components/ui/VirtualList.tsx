/**
 * VirtualList Component
 *
 * Efficient virtual scrolling for large lists using @tanstack/react-virtual
 * Only renders items currently in viewport, dramatically improving performance
 */

import React, { useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { clsx } from 'clsx';

export interface VirtualListProps<T> {
  /** Array of items to render */
  items: T[];
  /** Function to render each item */
  renderItem: (item: T, index: number) => React.ReactNode;
  /** Estimated size of each item in pixels */
  estimateSize: number;
  /** Gap between items in pixels */
  gap?: number;
  /** Custom class name for the container */
  className?: string;
  /** Custom class name for the viewport */
  viewportClassName?: string;
  /** Custom class name for each item wrapper */
  itemClassName?: string;
  /** Height of the scrollable container (defaults to 100%) */
  height?: string | number;
  /** Overscan count (number of items to render outside viewport) */
  overscan?: number;
  /** Loading state */
  isLoading?: boolean;
  /** Loading component */
  loadingComponent?: React.ReactNode;
  /** Empty state component */
  emptyComponent?: React.ReactNode;
  /** Function to extract unique key from item */
  getItemKey?: (item: T, index: number) => string | number;
}

export function VirtualList<T>({
  items,
  renderItem,
  estimateSize,
  gap = 8,
  className,
  viewportClassName,
  itemClassName,
  height = '100%',
  overscan = 5,
  isLoading = false,
  loadingComponent,
  emptyComponent,
  getItemKey,
}: VirtualListProps<T>) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimateSize,
    overscan,
    gap,
  });

  // Show loading state
  if (isLoading) {
    if (loadingComponent) {
      return <div className={clsx('w-full', className)}>{loadingComponent}</div>;
    }
    return (
      <div
        className={clsx(
          'flex items-center justify-center w-full',
          className
        )}
        style={{ height }}
      >
        <div className="flex flex-col items-center gap-3">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
          <p className="text-sm text-gray-500">載入中...</p>
        </div>
      </div>
    );
  }

  // Show empty state
  if (items.length === 0) {
    if (emptyComponent) {
      return <div className={clsx('w-full', className)}>{emptyComponent}</div>;
    }
    return (
      <div
        className={clsx(
          'flex items-center justify-center w-full text-gray-500',
          className
        )}
        style={{ height }}
      >
        <p>沒有數據</p>
      </div>
    );
  }

  const virtualItems = virtualizer.getVirtualItems();

  return (
    <div
      ref={parentRef}
      className={clsx('overflow-auto', viewportClassName)}
      style={{ height }}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualItems.map((virtualItem) => {
          const item = items[virtualItem.index];
          const key = getItemKey
            ? getItemKey(item, virtualItem.index)
            : virtualItem.index;

          return (
            <div
              key={key}
              data-index={virtualItem.index}
              ref={virtualizer.measureElement}
              className={itemClassName}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              {renderItem(item, virtualItem.index)}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default VirtualList;
