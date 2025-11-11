/**
 * ProofreadingIssuesSection - List of proofreading issues
 *
 * Phase 8.3: Proofreading Review Panel
 * - Display issues grouped by severity
 * - Accept/Reject/Modify actions
 * - Filtering and sorting
 */

import React, { useState } from 'react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { AlertCircle, Info, AlertTriangle, Check, X } from 'lucide-react';
import type { ProofreadingIssue, DecisionPayload, IssueSeverity } from '../../types/worklist';

export interface ProofreadingIssuesSectionProps {
  /** List of issues */
  issues: ProofreadingIssue[];
  /** Current decisions map */
  decisions: Map<string, DecisionPayload>;
  /** Callback when decision is made */
  onDecision: (issueId: string, decision: DecisionPayload) => void;
}

/**
 * ProofreadingIssuesSection Component
 */
export const ProofreadingIssuesSection: React.FC<ProofreadingIssuesSectionProps> = ({
  issues,
  decisions,
  onDecision,
}) => {
  const [filterSeverity, setFilterSeverity] = useState<IssueSeverity | 'all'>('all');

  // Filter issues
  const filteredIssues = issues.filter((issue) => {
    if (filterSeverity !== 'all' && issue.severity !== filterSeverity) {
      return false;
    }
    return true;
  });

  // Group by severity
  const groupedIssues = {
    critical: filteredIssues.filter((i) => i.severity === 'critical'),
    warning: filteredIssues.filter((i) => i.severity === 'warning'),
    info: filteredIssues.filter((i) => i.severity === 'info'),
  };

  const getSeverityIcon = (severity: IssueSeverity) => {
    switch (severity) {
      case 'critical':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-600" />;
      case 'info':
        return <Info className="w-4 h-4 text-blue-600" />;
    }
  };

  const getSeverityColor = (severity: IssueSeverity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-amber-50 border-amber-200';
      case 'info':
        return 'bg-blue-50 border-blue-200';
    }
  };

  const renderIssue = (issue: ProofreadingIssue) => {
    const decision = decisions.get(issue.id);
    const currentStatus = decision?.decision_type || issue.decision_status;

    return (
      <div
        key={issue.id}
        className={`p-4 border rounded-lg ${getSeverityColor(issue.severity)}`}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            {/* Header */}
            <div className="flex items-center gap-2">
              {getSeverityIcon(issue.severity)}
              <Badge variant="secondary" className="text-xs">
                {issue.rule_category}
              </Badge>
              {issue.engine === 'ai' && (
                <Badge variant="secondary" className="text-xs bg-purple-100">
                  AI
                </Badge>
              )}
              {issue.confidence && (
                <span className="text-xs text-gray-500">
                  置信度: {Math.round(issue.confidence * 100)}%
                </span>
              )}
            </div>

            {/* Content */}
            <div className="space-y-1">
              <div className="text-sm">
                <span className="text-gray-600">原文: </span>
                <span className="font-mono bg-white px-1 py-0.5 rounded text-red-700">
                  {issue.original_text}
                </span>
              </div>
              <div className="text-sm">
                <span className="text-gray-600">建议: </span>
                <span className="font-mono bg-white px-1 py-0.5 rounded text-green-700">
                  {issue.suggested_text}
                </span>
              </div>
              <p className="text-xs text-gray-600 mt-1">{issue.explanation}</p>
            </div>

            {/* Current status */}
            {currentStatus !== 'pending' && (
              <div className="text-xs">
                <Badge
                  variant={
                    currentStatus === 'accepted'
                      ? 'success'
                      : currentStatus === 'rejected'
                      ? 'error'
                      : 'secondary'
                  }
                >
                  {currentStatus === 'accepted' && '✓ 已接受'}
                  {currentStatus === 'rejected' && '✗ 已拒绝'}
                  {currentStatus === 'modified' && '✎ 已修改'}
                </Badge>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-2">
            <Button
              size="sm"
              variant={currentStatus === 'accepted' ? 'primary' : 'outline'}
              onClick={() =>
                onDecision(issue.id, {
                  issue_id: issue.id,
                  decision_type: 'accepted',
                  feedback_provided: false,
                })
              }
              className="whitespace-nowrap"
            >
              <Check className="w-3 h-3 mr-1" />
              接受
            </Button>
            <Button
              size="sm"
              variant={currentStatus === 'rejected' ? 'danger' : 'outline'}
              onClick={() =>
                onDecision(issue.id, {
                  issue_id: issue.id,
                  decision_type: 'rejected',
                  feedback_provided: false,
                })
              }
              className="whitespace-nowrap"
            >
              <X className="w-3 h-3 mr-1" />
              拒绝
            </Button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          问题列表 ({filteredIssues.length})
        </h3>

        {/* Filter */}
        <div className="flex gap-2">
          {(['all', 'critical', 'warning', 'info'] as const).map((severity) => (
            <button
              key={severity}
              type="button"
              onClick={() => setFilterSeverity(severity)}
              className={`px-3 py-1 text-xs rounded ${
                filterSeverity === severity
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {severity === 'all' && '全部'}
              {severity === 'critical' && `严重 (${groupedIssues.critical.length})`}
              {severity === 'warning' && `警告 (${groupedIssues.warning.length})`}
              {severity === 'info' && `信息 (${groupedIssues.info.length})`}
            </button>
          ))}
        </div>
      </div>

      {/* Issues */}
      {filteredIssues.length > 0 ? (
        <div className="space-y-3 max-h-[600px] overflow-auto">
          {filteredIssues.map(renderIssue)}
        </div>
      ) : (
        <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-lg">
          <Info className="w-12 h-12 mx-auto text-gray-400 mb-2" />
          <p className="text-sm text-gray-500">
            {filterSeverity === 'all' ? '暂无校对问题' : '暂无该类型问题'}
          </p>
        </div>
      )}
    </div>
  );
};

ProofreadingIssuesSection.displayName = 'ProofreadingIssuesSection';
