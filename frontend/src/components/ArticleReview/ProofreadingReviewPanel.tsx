/**
 * ProofreadingReviewPanel - Proofreading review interface
 *
 * Phase 8.3: Proofreading Review Panel
 * - 30% + 70% layout
 * - Left: Diff view (original vs proofread)
 * - Right: Issue list with accept/reject controls
 * - Batch approval operations
 *
 * Layout:
 * ┌──────────────┬────────────────────────────────────┐
 * │ Diff View    │ Issues List (70%)                  │
 * │ (30%)        │ • Critical issues                  │
 * │              │ • Warning issues                   │
 * │ Controls     │ • Info issues                      │
 * │              │ Batch controls                     │
 * └──────────────┴────────────────────────────────────┘
 */

import React, { useState, useMemo } from 'react';
import { Card } from '../ui';
import { Button } from '../ui';
import { DiffViewSection } from './DiffViewSection';
import { ProofreadingIssuesSection } from './ProofreadingIssuesSection';
import { BatchApprovalControls } from './BatchApprovalControls';
import type { ArticleReviewData } from '../../hooks/articleReview/useArticleReviewData';
import type { ProofreadingIssue, DecisionPayload } from '../../types/worklist';

export interface ProofreadingReviewPanelProps {
  /** Article review data */
  data: ArticleReviewData;
  /** Callback when decisions are submitted */
  onSubmitDecisions: (decisions: DecisionPayload[]) => Promise<void>;
  /** Whether submission is in progress */
  isSubmitting?: boolean;
}

/**
 * ProofreadingReviewPanel Component
 */
export const ProofreadingReviewPanel: React.FC<ProofreadingReviewPanelProps> = ({
  data,
  onSubmitDecisions,
  isSubmitting = false,
}) => {
  // Local state for decisions
  const [decisions, setDecisions] = useState<Map<string, DecisionPayload>>(new Map());

  // Use article review issues if available (richer data with historical context)
  // Falls back to worklist issues for backward compatibility
  const issues = useMemo(() => {
    if (data.articleReview?.proofreading_issues) {
      return data.articleReview.proofreading_issues;
    }
    return data.proofreading_issues || [];
  }, [data]);

  // Get existing decisions from article review (historical context)
  const existingDecisions = useMemo(() => {
    return data.articleReview?.existing_decisions || [];
  }, [data]);

  const stats = data.proofreading_stats || {
    total_issues: 0,
    critical_count: 0,
    warning_count: 0,
    info_count: 0,
    pending_count: 0,
    accepted_count: 0,
    rejected_count: 0,
    modified_count: 0,
    ai_issues_count: 0,
    deterministic_issues_count: 0,
  };

  // Calculate current stats based on local decisions
  const currentStats = useMemo(() => {
    let pending = 0;
    let accepted = 0;
    let rejected = 0;
    let modified = 0;

    issues.forEach((issue) => {
      const decision = decisions.get(issue.id);
      if (!decision) {
        if (issue.decision_status === 'pending') pending++;
        else if (issue.decision_status === 'accepted') accepted++;
        else if (issue.decision_status === 'rejected') rejected++;
        else if (issue.decision_status === 'modified') modified++;
      } else {
        if (decision.decision_type === 'accepted') accepted++;
        else if (decision.decision_type === 'rejected') rejected++;
        else if (decision.decision_type === 'modified') modified++;
      }
    });

    return {
      ...stats,
      pending_count: pending,
      accepted_count: accepted,
      rejected_count: rejected,
      modified_count: modified,
    };
  }, [decisions, issues, stats]);

  const handleDecision = (issueId: string, decision: DecisionPayload) => {
    const newDecisions = new Map(decisions);
    newDecisions.set(issueId, decision);
    setDecisions(newDecisions);
  };

  const handleBatchDecision = (issueIds: string[], decisionType: 'accepted' | 'rejected') => {
    const newDecisions = new Map(decisions);
    issueIds.forEach((issueId) => {
      newDecisions.set(issueId, {
        issue_id: issueId,
        decision_type: decisionType,
        feedback_provided: false,
      });
    });
    setDecisions(newDecisions);
  };

  const handleSubmit = async () => {
    const decisionList = Array.from(decisions.values());
    if (decisionList.length === 0) {
      alert('请至少做出一个审核决定');
      return;
    }

    await onSubmitDecisions(decisionList);
    setDecisions(new Map()); // Clear decisions after submit
  };

  const handleReset = () => {
    setDecisions(new Map());
  };

  // Check if there are any pending decisions
  const hasPendingDecisions = decisions.size > 0;

  return (
    <div className="h-full flex flex-col">
      {/* Header with stats */}
      <div className="mb-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">校对审核</h3>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-600">
              待处理: <strong className="text-amber-600">{currentStats.pending_count}</strong>
            </span>
            <span className="text-gray-600">
              已接受: <strong className="text-green-600">{currentStats.accepted_count}</strong>
            </span>
            <span className="text-gray-600">
              已拒绝: <strong className="text-red-600">{currentStats.rejected_count}</strong>
            </span>
          </div>
        </div>
      </div>

      {/* Pending decisions indicator */}
      {hasPendingDecisions && (
        <div className="mb-4 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            ⓘ 您有 <strong>{decisions.size}</strong> 个未提交的决定。记得点击"提交审核"保存。
          </p>
        </div>
      )}

      {/* Main content: 30% + 70% grid */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-10 gap-6 overflow-auto">
        {/* Left column: 30% (3 out of 10 cols) */}
        <div className="lg:col-span-3 space-y-6">
          <Card className="p-6">
            <DiffViewSection
              originalContent={data.articleReview?.content?.original || ''}
              proofreadContent={data.articleReview?.content?.suggested || (data.metadata?.proofread_content as string) || data.articleReview?.content?.original || ''}
            />
          </Card>
        </div>

        {/* Right column: 70% (7 out of 10 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Batch controls */}
          <Card className="p-4">
            <BatchApprovalControls
              issues={issues}
              decisions={decisions}
              onBatchDecision={handleBatchDecision}
            />
          </Card>

          {/* Historical decisions (if available from article review) */}
          {existingDecisions.length > 0 && (
            <Card className="p-6 bg-blue-50 border-blue-200">
              <h4 className="text-sm font-semibold text-blue-900 mb-3 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                历史审核决策 ({existingDecisions.length})
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {existingDecisions.slice(0, 5).map((decision, idx) => (
                  <div key={idx} className="p-3 bg-white rounded border border-blue-100">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-xs text-gray-600">问题 ID: {decision.issue_id}</p>
                        <p className="text-sm font-medium text-gray-900 mt-1">
                          决策: <span className={`${
                            decision.decision_type === 'accepted' ? 'text-green-600' :
                            decision.decision_type === 'rejected' ? 'text-red-600' :
                            'text-blue-600'
                          }`}>
                            {decision.decision_type === 'accepted' ? '已接受' :
                             decision.decision_type === 'rejected' ? '已拒绝' : '已修改'}
                          </span>
                        </p>
                        {decision.rationale && (
                          <p className="text-xs text-gray-600 mt-1">理由: {decision.rationale}</p>
                        )}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(decision.decided_at).toLocaleDateString('zh-CN')}
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      审核人: {decision.reviewer}
                    </p>
                  </div>
                ))}
                {existingDecisions.length > 5 && (
                  <p className="text-xs text-blue-600 text-center py-2">
                    还有 {existingDecisions.length - 5} 个历史决策...
                  </p>
                )}
              </div>
            </Card>
          )}

          {/* Issues list */}
          <Card className="p-6">
            <ProofreadingIssuesSection
              issues={issues}
              decisions={decisions}
              onDecision={handleDecision}
            />
          </Card>
        </div>
      </div>

      {/* Action buttons */}
      <div className="mt-6 flex items-center justify-between pt-4 border-t">
        <div className="text-sm text-gray-600">
          {hasPendingDecisions && (
            <span className="text-blue-600 font-medium">
              ● {decisions.size} 个待提交决定
            </span>
          )}
          {currentStats.pending_count > 0 && (
            <span className="ml-4 text-amber-600">
              ⚠️ 还有 {currentStats.pending_count} 个问题待审核
            </span>
          )}
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={handleReset}
            disabled={!hasPendingDecisions || isSubmitting}
          >
            重置决定
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!hasPendingDecisions || isSubmitting}
          >
            {isSubmitting ? '提交中...' : '提交审核'}
          </Button>
        </div>
      </div>
    </div>
  );
};

ProofreadingReviewPanel.displayName = 'ProofreadingReviewPanel';
