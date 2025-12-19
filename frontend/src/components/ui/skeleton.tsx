/**
 * Skeleton component - Loading placeholder with variants
 */

import React from 'react';
import { cn } from '../../lib/cn';

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Visual variant of the skeleton */
  variant?: 'default' | 'circular' | 'text' | 'rectangular';
  /** Animation type */
  animation?: 'pulse' | 'wave' | 'none';
  /** Width - can be number (px) or string (e.g., '100%') */
  width?: number | string;
  /** Height - can be number (px) or string */
  height?: number | string;
}

function Skeleton({
  className,
  variant = 'default',
  animation = 'pulse',
  width,
  height,
  style,
  ...props
}: SkeletonProps) {
  const variantClasses = {
    default: 'rounded-md',
    circular: 'rounded-full',
    text: 'rounded h-4 w-full',
    rectangular: 'rounded-none',
  };

  const animationClasses = {
    pulse: 'animate-pulse',
    wave: 'animate-shimmer bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 bg-[length:200%_100%]',
    none: '',
  };

  return (
    <div
      className={cn(
        'bg-gray-200',
        variantClasses[variant],
        animationClasses[animation],
        className
      )}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
        ...style,
      }}
      {...props}
    />
  );
}

/**
 * Skeleton for card layouts
 */
function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn('rounded-lg border border-gray-200 p-4 space-y-3', className)}>
      <Skeleton height={20} width="60%" />
      <Skeleton height={16} width="100%" />
      <Skeleton height={16} width="80%" />
      <div className="flex gap-2 pt-2">
        <Skeleton height={32} width={80} />
        <Skeleton height={32} width={80} />
      </div>
    </div>
  );
}

/**
 * Skeleton for table rows
 */
function SkeletonTableRow({ columns = 6 }: { columns?: number }) {
  return (
    <tr className="border-b border-gray-100">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton height={16} width={i === 0 ? '80%' : '60%'} />
        </td>
      ))}
    </tr>
  );
}

/**
 * Skeleton for stats cards (dashboard)
 */
function SkeletonStatsCard() {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-2">
      <Skeleton height={14} width={100} />
      <Skeleton height={32} width={60} />
      <Skeleton height={12} width="80%" />
    </div>
  );
}

/**
 * Skeleton for proofreading issue list
 */
function SkeletonIssueList({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="border-b border-gray-100 p-4 space-y-2">
          <div className="flex items-center gap-2">
            <Skeleton variant="circular" width={20} height={20} />
            <Skeleton height={14} width={80} />
            <Skeleton height={20} width={40} className="rounded-full" />
          </div>
          <Skeleton height={16} width="90%" />
          <Skeleton height={14} width="70%" />
        </div>
      ))}
    </div>
  );
}

/**
 * Skeleton for article content
 */
function SkeletonArticleContent() {
  return (
    <div className="space-y-4 max-w-4xl mx-auto">
      {/* Title */}
      <Skeleton height={36} width="70%" className="mb-8" />
      {/* Paragraphs */}
      <div className="space-y-2">
        <Skeleton height={16} width="100%" />
        <Skeleton height={16} width="95%" />
        <Skeleton height={16} width="88%" />
      </div>
      <div className="space-y-2 pt-4">
        <Skeleton height={16} width="100%" />
        <Skeleton height={16} width="92%" />
        <Skeleton height={16} width="85%" />
        <Skeleton height={16} width="78%" />
      </div>
      <div className="space-y-2 pt-4">
        <Skeleton height={16} width="100%" />
        <Skeleton height={16} width="90%" />
      </div>
    </div>
  );
}

/**
 * Skeleton for issue detail panel
 */
function SkeletonIssueDetail() {
  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Skeleton height={20} width={120} />
        <Skeleton height={24} width={60} className="rounded-full" />
      </div>
      {/* Category */}
      <div className="flex items-center gap-2">
        <Skeleton variant="circular" width={20} height={20} />
        <Skeleton height={16} width={100} />
        <Skeleton height={20} width={40} className="rounded-full ml-auto" />
      </div>
      {/* Original/Suggested boxes */}
      <div className="space-y-4">
        <div>
          <Skeleton height={12} width={60} className="mb-2" />
          <Skeleton height={60} width="100%" className="rounded-lg" />
        </div>
        <div>
          <Skeleton height={12} width={70} className="mb-2" />
          <Skeleton height={60} width="100%" className="rounded-lg" />
        </div>
      </div>
      {/* Explanation */}
      <div>
        <Skeleton height={12} width={80} className="mb-2" />
        <Skeleton height={40} width="100%" />
      </div>
      {/* Action buttons */}
      <div className="grid grid-cols-2 gap-2 pt-4">
        <Skeleton height={40} width="100%" />
        <Skeleton height={40} width="100%" />
      </div>
    </div>
  );
}

/**
 * Full page loading skeleton for proofreading review
 */
function SkeletonProofreadingPage() {
  return (
    <div className="flex h-screen flex-col bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Skeleton height={32} width={32} variant="circular" />
            <Skeleton height={24} width={200} />
          </div>
          <div className="flex gap-2">
            <Skeleton height={36} width={100} />
            <Skeleton height={36} width={120} />
          </div>
        </div>
      </div>
      {/* Stats bar */}
      <div className="border-b border-gray-200 bg-white px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="flex items-center gap-2">
                <Skeleton variant="circular" width={16} height={16} />
                <Skeleton height={14} width={50} />
                <Skeleton height={18} width={24} />
              </div>
            ))}
          </div>
          <div className="flex items-center gap-4">
            <Skeleton height={40} width={150} />
            <Skeleton height={36} width={200} />
          </div>
        </div>
      </div>
      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel */}
        <div className="w-1/5 border-r border-gray-200 bg-white p-3">
          <Skeleton height={32} width="100%" className="mb-3" />
          <SkeletonIssueList count={6} />
        </div>
        {/* Center panel */}
        <div className="flex-1 bg-white p-8">
          <SkeletonArticleContent />
        </div>
        {/* Right panel */}
        <div className="w-[30%] border-l border-gray-200 bg-white">
          <SkeletonIssueDetail />
        </div>
      </div>
    </div>
  );
}

export {
  Skeleton,
  SkeletonCard,
  SkeletonTableRow,
  SkeletonStatsCard,
  SkeletonIssueList,
  SkeletonArticleContent,
  SkeletonIssueDetail,
  SkeletonProofreadingPage,
};
export type { SkeletonProps };
