/**
 * RouteLoadingFallback Component
 *
 * Enhanced loading fallback for lazy-loaded routes
 * Provides skeleton screens and smooth loading experience
 */

import React from 'react';
import { clsx } from 'clsx';

export interface RouteLoadingFallbackProps {
  /** Loading text */
  text?: string;
  /** Show skeleton screen instead of spinner */
  skeleton?: boolean;
  /** Custom className */
  className?: string;
}

export const RouteLoadingFallback: React.FC<RouteLoadingFallbackProps> = ({
  text = '載入中...',
  skeleton = false,
  className,
}) => {
  if (skeleton) {
    return (
      <div className={clsx('animate-pulse p-6', className)}>
        {/* Header skeleton */}
        <div className="mb-6">
          <div className="h-8 w-64 rounded bg-gray-200" />
          <div className="mt-2 h-4 w-96 rounded bg-gray-200" />
        </div>

        {/* Content skeleton */}
        <div className="space-y-4">
          <div className="h-32 rounded-lg bg-gray-200" />
          <div className="h-32 rounded-lg bg-gray-200" />
          <div className="h-32 rounded-lg bg-gray-200" />
        </div>
      </div>
    );
  }

  return (
    <div
      className={clsx(
        'flex min-h-screen items-center justify-center',
        className
      )}
    >
      <div className="flex flex-col items-center gap-4">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
        <p className="text-sm text-gray-600">{text}</p>
      </div>
    </div>
  );
};

/**
 * Page skeleton for list views
 */
export const ListPageSkeleton: React.FC = () => {
  return (
    <div className="animate-pulse p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="h-8 w-48 rounded bg-gray-200" />
        <div className="h-10 w-32 rounded bg-gray-200" />
      </div>

      {/* Filters */}
      <div className="mb-6 flex gap-4">
        <div className="h-10 w-40 rounded bg-gray-200" />
        <div className="h-10 w-40 rounded bg-gray-200" />
        <div className="h-10 w-40 rounded bg-gray-200" />
      </div>

      {/* List items */}
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="rounded-lg border border-gray-200 p-4">
            <div className="mb-2 h-6 w-3/4 rounded bg-gray-200" />
            <div className="h-4 w-full rounded bg-gray-200" />
            <div className="mt-2 h-4 w-2/3 rounded bg-gray-200" />
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * Page skeleton for detail/form views
 */
export const DetailPageSkeleton: React.FC = () => {
  return (
    <div className="animate-pulse p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="h-8 w-64 rounded bg-gray-200" />
        <div className="mt-2 h-4 w-96 rounded bg-gray-200" />
      </div>

      {/* Form fields */}
      <div className="space-y-6">
        {[...Array(4)].map((_, i) => (
          <div key={i}>
            <div className="mb-2 h-4 w-24 rounded bg-gray-200" />
            <div className="h-10 w-full rounded bg-gray-200" />
          </div>
        ))}
      </div>

      {/* Action buttons */}
      <div className="mt-8 flex gap-4">
        <div className="h-10 w-32 rounded bg-gray-200" />
        <div className="h-10 w-32 rounded bg-gray-200" />
      </div>
    </div>
  );
};

/**
 * Page skeleton for dashboard views
 */
export const DashboardSkeleton: React.FC = () => {
  return (
    <div className="animate-pulse p-6">
      {/* Header */}
      <div className="mb-6 h-8 w-48 rounded bg-gray-200" />

      {/* Stats cards */}
      <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="rounded-lg border border-gray-200 p-4">
            <div className="mb-2 h-4 w-24 rounded bg-gray-200" />
            <div className="h-8 w-32 rounded bg-gray-200" />
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className="h-64 rounded-lg border border-gray-200 bg-gray-100" />
        <div className="h-64 rounded-lg border border-gray-200 bg-gray-100" />
      </div>
    </div>
  );
};

export default RouteLoadingFallback;
