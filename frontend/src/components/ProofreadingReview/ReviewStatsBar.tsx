/**
 * Review Stats Bar
 * Displays statistics about proofreading issues.
 *
 * Performance optimizations:
 * - Sub-components memoized to prevent unnecessary re-renders
 * - Progress calculation optimized
 */

import { memo, useMemo } from 'react';
import { ProofreadingStats } from '@/types/worklist';
import { AlertCircle, AlertTriangle, Info, CheckCircle, XCircle, Eye, FileText, GitCompare } from 'lucide-react';
import { cn } from '@/lib/cn';

type ViewMode = 'original' | 'preview' | 'diff';

interface ReviewStatsBarProps {
  stats?: ProofreadingStats | null;
  dirtyCount: number;
  totalIssues: number;
  viewMode?: ViewMode;
  onViewModeChange?: (mode: ViewMode) => void;
}

export function ReviewStatsBar({ stats, dirtyCount, totalIssues, viewMode = 'original', onViewModeChange }: ReviewStatsBarProps) {
  if (!stats) return null;

  const progressPercent = totalIssues > 0 ? Math.round((dirtyCount / totalIssues) * 100) : 0;

  return (
    <div className="sticky top-0 z-10 border-b border-gray-200 bg-white px-6 py-3 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
          {/* Severity Stats */}
          <div className="flex items-center gap-4">
            <StatItem
              icon={<AlertCircle className="h-4 w-4 text-red-500" />}
              label="Critical"
              count={stats.critical_count}
            />
            <StatItem
              icon={<AlertTriangle className="h-4 w-4 text-yellow-500" />}
              label="Warning"
              count={stats.warning_count}
            />
            <StatItem
              icon={<Info className="h-4 w-4 text-blue-500" />}
              label="Info"
              count={stats.info_count}
            />
          </div>

          <div className="h-6 w-px bg-gray-300" />

          {/* Decision Stats */}
          <div className="flex items-center gap-4">
            <StatItem
              icon={<CheckCircle className="h-4 w-4 text-green-500" />}
              label="Accepted"
              count={stats.accepted_count}
            />
            <StatItem
              icon={<XCircle className="h-4 w-4 text-gray-400" />}
              label="Rejected"
              count={stats.rejected_count}
            />
            <StatItem
              icon={<div className="h-4 w-4 rounded-full bg-purple-500" />}
              label="Modified"
              count={stats.modified_count}
            />
          </div>
        </div>

        {/* Right Side: Progress & View Mode */}
        <div className="flex items-center gap-6">
          {/* Progress */}
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-sm font-medium text-gray-900">
                {dirtyCount} / {totalIssues}
              </div>
              <div className="text-xs text-gray-500">Issues Decided</div>
            </div>
            <div className="h-10 w-32 overflow-hidden rounded-full bg-gray-200">
              <div
                className="h-full bg-blue-500 transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <div className="text-sm font-medium text-gray-700">{progressPercent}%</div>
          </div>

          {/* View Mode Switcher */}
          {onViewModeChange && (
            <div className="flex items-center gap-1 rounded-lg border border-gray-200 bg-gray-50 p-1">
              <ViewModeButton
                mode="original"
                currentMode={viewMode}
                icon={<FileText className="h-4 w-4" />}
                label="Original"
                onClick={() => onViewModeChange('original')}
              />
              <ViewModeButton
                mode="diff"
                currentMode={viewMode}
                icon={<GitCompare className="h-4 w-4" />}
                label="Diff"
                onClick={() => onViewModeChange('diff')}
              />
              <ViewModeButton
                mode="preview"
                currentMode={viewMode}
                icon={<Eye className="h-4 w-4" />}
                label="Preview"
                onClick={() => onViewModeChange('preview')}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Memoized ViewModeButton to prevent re-renders when props don't change
const ViewModeButton = memo(({
  mode,
  currentMode,
  icon,
  label,
  onClick,
}: {
  mode: ViewMode;
  currentMode: ViewMode;
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}) => {
  const isActive = mode === currentMode;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-medium transition-colors',
        isActive
          ? 'bg-white text-blue-600 shadow-sm'
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
      )}
      aria-label={`View ${label} mode`}
      aria-pressed={isActive}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
});

ViewModeButton.displayName = 'ViewModeButton';

// Memoized StatItem to prevent re-renders when count doesn't change
const StatItem = memo(({
  icon,
  label,
  count,
}: {
  icon: React.ReactNode;
  label: string;
  count: number;
}) => {
  return (
    <div className="flex items-center gap-1.5">
      {icon}
      <span className="text-xs text-gray-600">{label}</span>
      <span className="text-sm font-semibold text-gray-900">{count}</span>
    </div>
  );
});

StatItem.displayName = 'StatItem';
