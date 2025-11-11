/**
 * BatchApprovalControls - Batch operations for proofreading issues
 *
 * Phase 8.3: Proofreading Review Panel
 * - Select all by category/severity
 * - Batch accept/reject
 * - Quick filters
 */

import React, { useMemo } from 'react';
import { Button } from '../ui/Button';
import { CheckSquare, XSquare, Filter } from 'lucide-react';
import type { ProofreadingIssue, DecisionPayload } from '../../types/worklist';

export interface BatchApprovalControlsProps {
  /** List of all issues */
  issues: ProofreadingIssue[];
  /** Current decisions map */
  decisions: Map<string, DecisionPayload>;
  /** Callback for batch decision */
  onBatchDecision: (issueIds: string[], decisionType: 'accepted' | 'rejected') => void;
}

/**
 * BatchApprovalControls Component
 */
export const BatchApprovalControls: React.FC<BatchApprovalControlsProps> = ({
  issues,
  decisions,
  onBatchDecision,
}) => {
  // Calculate pending issues
  const pendingIssues = useMemo(() => {
    return issues.filter((issue) => {
      const decision = decisions.get(issue.id);
      return !decision && issue.decision_status === 'pending';
    });
  }, [issues, decisions]);

  // Group pending by severity
  const pendingBySeverity = useMemo(() => {
    return {
      critical: pendingIssues.filter((i) => i.severity === 'critical'),
      warning: pendingIssues.filter((i) => i.severity === 'warning'),
      info: pendingIssues.filter((i) => i.severity === 'info'),
    };
  }, [pendingIssues]);

  // Group pending by engine
  const pendingByEngine = useMemo(() => {
    return {
      ai: pendingIssues.filter((i) => i.engine === 'ai'),
      deterministic: pendingIssues.filter((i) => i.engine === 'deterministic'),
    };
  }, [pendingIssues]);

  const handleBatchAccept = (issueList: ProofreadingIssue[]) => {
    const ids = issueList.map((i) => i.id);
    onBatchDecision(ids, 'accepted');
  };

  const handleBatchReject = (issueList: ProofreadingIssue[]) => {
    const ids = issueList.map((i) => i.id);
    onBatchDecision(ids, 'rejected');
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Filter className="w-5 h-5 text-gray-600" />
        <h3 className="text-sm font-semibold text-gray-900">批量操作</h3>
        <span className="text-xs text-gray-500">
          ({pendingIssues.length} 个待处理问题)
        </span>
      </div>

      {pendingIssues.length === 0 && (
        <p className="text-sm text-gray-500">所有问题已审核</p>
      )}

      {pendingIssues.length > 0 && (
        <div className="space-y-3">
          {/* All pending */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-700 min-w-24">全部待处理:</span>
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleBatchAccept(pendingIssues)}
              className="text-xs"
            >
              <CheckSquare className="w-3 h-3 mr-1" />
              全部接受 ({pendingIssues.length})
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleBatchReject(pendingIssues)}
              className="text-xs"
            >
              <XSquare className="w-3 h-3 mr-1" />
              全部拒绝 ({pendingIssues.length})
            </Button>
          </div>

          {/* By severity */}
          {pendingBySeverity.critical.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700 min-w-24">严重问题:</span>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleBatchAccept(pendingBySeverity.critical)}
                className="text-xs"
              >
                接受 ({pendingBySeverity.critical.length})
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleBatchReject(pendingBySeverity.critical)}
                className="text-xs"
              >
                拒绝 ({pendingBySeverity.critical.length})
              </Button>
            </div>
          )}

          {pendingBySeverity.warning.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700 min-w-24">警告问题:</span>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleBatchAccept(pendingBySeverity.warning)}
                className="text-xs"
              >
                接受 ({pendingBySeverity.warning.length})
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleBatchReject(pendingBySeverity.warning)}
                className="text-xs"
              >
                拒绝 ({pendingBySeverity.warning.length})
              </Button>
            </div>
          )}

          {/* By engine */}
          {pendingByEngine.ai.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700 min-w-24">AI 建议:</span>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleBatchAccept(pendingByEngine.ai)}
                className="text-xs"
              >
                接受 ({pendingByEngine.ai.length})
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleBatchReject(pendingByEngine.ai)}
                className="text-xs"
              >
                拒绝 ({pendingByEngine.ai.length})
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Hint */}
      <div className="p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-800">
        <strong>提示：</strong>批量操作会覆盖之前的决定。请谨慎使用。
      </div>
    </div>
  );
};

BatchApprovalControls.displayName = 'BatchApprovalControls';
