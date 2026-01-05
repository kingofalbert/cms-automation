/**
 * ProofreadingSummarySection - Displays proofreading review summary
 *
 * Phase 16: Enhanced Publish Preview
 * - Shows total proofreading issues count
 * - Shows breakdown: accepted, rejected, pending
 * - Warning if pending issues remain
 *
 * Layout:
 * ┌─────────────────────────────────────────────────────────────┐
 * │ ✏️ 校對審核摘要                                             │
 * ├─────────────────────────────────────────────────────────────┤
 * │ 總問題數: 145                                               │
 * │ ├─ ✅ 已接受: 12                                           │
 * │ ├─ ❌ 已拒絕: 3                                            │
 * │ └─ ⏳ 待處理: 130                                          │
 * │                                                             │
 * │ ⚠️ 警告: 仍有 130 個問題待處理                              │
 * └─────────────────────────────────────────────────────────────┘
 */

import React from 'react';
import { Edit3, Check, X, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';

export interface ProofreadingSummaryStats {
  /** Total number of proofreading issues */
  totalIssues: number;
  /** Number of accepted suggestions */
  acceptedCount: number;
  /** Number of rejected suggestions */
  rejectedCount: number;
  /** Number of modified suggestions */
  modifiedCount: number;
  /** Number of pending (unreviewed) issues */
  pendingCount: number;
  /** Critical issues count */
  criticalCount?: number;
  /** Warning issues count */
  warningCount?: number;
  /** Info issues count */
  infoCount?: number;
}

export interface ProofreadingSummarySectionProps {
  /** Proofreading statistics */
  stats?: ProofreadingSummaryStats | null;
  /** Whether to show warning for pending issues */
  showPendingWarning?: boolean;
}

/**
 * ProofreadingSummarySection Component
 *
 * Displays a comprehensive summary of proofreading review status.
 */
export const ProofreadingSummarySection: React.FC<ProofreadingSummarySectionProps> = ({
  stats,
  showPendingWarning = true,
}) => {
  // If no stats, show placeholder
  if (!stats || stats.totalIssues === 0) {
    return (
      <div className="p-4 bg-white border border-gray-200 rounded-lg">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
          <Edit3 className="w-4 h-4 text-amber-600" />
          校對審核摘要
        </h4>
        <div className="text-sm text-gray-500 italic flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-green-500" />
          無校對問題
        </div>
      </div>
    );
  }

  // Calculate reviewed percentage
  const reviewedCount = stats.acceptedCount + stats.rejectedCount + stats.modifiedCount;
  const reviewedPercent = Math.round((reviewedCount / stats.totalIssues) * 100);
  const isFullyReviewed = stats.pendingCount === 0;

  return (
    <div className="p-4 bg-white border border-gray-200 rounded-lg">
      <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
        <Edit3 className="w-4 h-4 text-amber-600" />
        校對審核摘要
        {isFullyReviewed && (
          <span className="ml-auto text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" />
            審核完成
          </span>
        )}
      </h4>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
          <span>審核進度</span>
          <span>{reviewedCount}/{stats.totalIssues} ({reviewedPercent}%)</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-500 to-green-400 transition-all duration-300"
            style={{ width: `${reviewedPercent}%` }}
          />
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-4 gap-2 text-center">
        {/* Total */}
        <div className="p-2 bg-gray-50 rounded">
          <div className="text-lg font-semibold text-gray-800">{stats.totalIssues}</div>
          <div className="text-xs text-gray-500">總問題</div>
        </div>

        {/* Accepted */}
        <div className="p-2 bg-green-50 rounded">
          <div className="text-lg font-semibold text-green-700">{stats.acceptedCount}</div>
          <div className="text-xs text-green-600 flex items-center justify-center gap-0.5">
            <Check className="w-3 h-3" />
            已接受
          </div>
        </div>

        {/* Rejected */}
        <div className="p-2 bg-red-50 rounded">
          <div className="text-lg font-semibold text-red-700">{stats.rejectedCount}</div>
          <div className="text-xs text-red-600 flex items-center justify-center gap-0.5">
            <X className="w-3 h-3" />
            已拒絕
          </div>
        </div>

        {/* Pending */}
        <div className={`p-2 rounded ${
          stats.pendingCount > 0 ? 'bg-amber-50' : 'bg-gray-50'
        }`}>
          <div className={`text-lg font-semibold ${
            stats.pendingCount > 0 ? 'text-amber-700' : 'text-gray-600'
          }`}>
            {stats.pendingCount}
          </div>
          <div className={`text-xs flex items-center justify-center gap-0.5 ${
            stats.pendingCount > 0 ? 'text-amber-600' : 'text-gray-500'
          }`}>
            <Clock className="w-3 h-3" />
            待處理
          </div>
        </div>
      </div>

      {/* Modified count if any */}
      {stats.modifiedCount > 0 && (
        <div className="mt-2 text-center text-xs text-gray-500">
          已修改: {stats.modifiedCount} 處
        </div>
      )}

      {/* Severity breakdown if available */}
      {(stats.criticalCount !== undefined || stats.warningCount !== undefined) && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="text-xs text-gray-500 mb-2">問題嚴重程度</div>
          <div className="flex gap-3 text-xs">
            {stats.criticalCount !== undefined && stats.criticalCount > 0 && (
              <span className="text-red-600">
                🔴 嚴重: {stats.criticalCount}
              </span>
            )}
            {stats.warningCount !== undefined && stats.warningCount > 0 && (
              <span className="text-amber-600">
                🟡 警告: {stats.warningCount}
              </span>
            )}
            {stats.infoCount !== undefined && stats.infoCount > 0 && (
              <span className="text-blue-600">
                🔵 提示: {stats.infoCount}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Warning for pending issues */}
      {showPendingWarning && stats.pendingCount > 0 && (
        <div className="mt-3 p-2 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-700">
            <strong>注意:</strong> 仍有 {stats.pendingCount} 個問題待處理。
            建議在上稿前完成所有校對審核。
          </div>
        </div>
      )}
    </div>
  );
};

ProofreadingSummarySection.displayName = 'ProofreadingSummarySection';
