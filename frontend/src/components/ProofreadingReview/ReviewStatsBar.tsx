/**
 * Review Stats Bar
 * Displays statistics about proofreading issues.
 */

import { ProofreadingStats } from '@/types/worklist';
import { AlertCircle, AlertTriangle, Info, CheckCircle, XCircle } from 'lucide-react';

interface ReviewStatsBarProps {
  stats?: ProofreadingStats | null;
  dirtyCount: number;
  totalIssues: number;
}

export function ReviewStatsBar({ stats, dirtyCount, totalIssues }: ReviewStatsBarProps) {
  if (!stats) return null;

  const progressPercent = totalIssues > 0 ? Math.round((dirtyCount / totalIssues) * 100) : 0;

  return (
    <div className="border-b border-gray-200 bg-white px-6 py-3">
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
      </div>
    </div>
  );
}

function StatItem({
  icon,
  label,
  count,
}: {
  icon: React.ReactNode;
  label: string;
  count: number;
}) {
  return (
    <div className="flex items-center gap-1.5">
      {icon}
      <span className="text-xs text-gray-600">{label}</span>
      <span className="text-sm font-semibold text-gray-900">{count}</span>
    </div>
  );
}
