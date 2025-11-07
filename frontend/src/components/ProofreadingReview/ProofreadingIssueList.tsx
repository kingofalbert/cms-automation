/**
 * Proofreading Issue List
 * Left sidebar showing all proofreading issues with filtering.
 */

import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ProofreadingIssue,
  DecisionPayload,
  IssueSeverity,
  DecisionStatus,
} from '@/types/worklist';
import { Button, Input } from '@/components/ui';
import {
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle,
  XCircle,
  Search,
} from 'lucide-react';
import { cn } from '@/lib/cn';

interface ProofreadingIssueListProps {
  issues: ProofreadingIssue[];
  decisions: Record<string, DecisionPayload>;
  selectedIssue: ProofreadingIssue | null;
  selectedIssueIds: Set<string>;
  onSelectIssue: (issue: ProofreadingIssue) => void;
  onToggleSelect: (issueId: string) => void;
  onBatchAccept: () => void;
  onBatchReject: () => void;
}

export function ProofreadingIssueList({
  issues,
  decisions,
  selectedIssue,
  selectedIssueIds,
  onSelectIssue,
  onToggleSelect,
  onBatchAccept,
  onBatchReject,
}: ProofreadingIssueListProps) {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<IssueSeverity | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<DecisionStatus | 'all'>('all');

  // Filter issues
  const filteredIssues = useMemo(() => {
    return issues.filter((issue) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        if (
          !issue.original_text.toLowerCase().includes(query) &&
          !issue.suggested_text.toLowerCase().includes(query) &&
          !issue.explanation.toLowerCase().includes(query)
        ) {
          return false;
        }
      }

      // Severity filter
      if (severityFilter !== 'all' && issue.severity !== severityFilter) {
        return false;
      }

      // Status filter
      const decisionStatus = decisions[issue.id]?.decision_type || issue.decision_status;
      if (statusFilter !== 'all' && decisionStatus !== statusFilter) {
        return false;
      }

      return true;
    });
  }, [issues, searchQuery, severityFilter, statusFilter, decisions]);

  return (
    <div className="flex h-full flex-col">
      {/* Search and Filters */}
      <div className="border-b border-gray-200 p-4">
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <Input
            type="text"
            placeholder={t('common.search')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        <div className="flex gap-2">
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value as any)}
            className="flex-1 rounded-md border border-gray-300 px-2 py-1 text-sm"
          >
            <option value="all">All Severity</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="flex-1 rounded-md border border-gray-300 px-2 py-1 text-sm"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="accepted">Accepted</option>
            <option value="rejected">Rejected</option>
            <option value="modified">Modified</option>
          </select>
        </div>
      </div>

      {/* Batch Actions */}
      {selectedIssueIds.size > 0 && (
        <div className="border-b border-gray-200 bg-blue-50 p-3">
          <div className="mb-2 text-xs font-medium text-gray-700">
            {selectedIssueIds.size} selected
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={onBatchAccept} className="flex-1">
              <CheckCircle className="mr-1 h-3 w-3" />
              Accept
            </Button>
            <Button size="sm" variant="outline" onClick={onBatchReject} className="flex-1">
              <XCircle className="mr-1 h-3 w-3" />
              Reject
            </Button>
          </div>
        </div>
      )}

      {/* Issue List */}
      <div className="flex-1 overflow-y-auto">
        {filteredIssues.length === 0 ? (
          <div className="p-4 text-center text-sm text-gray-500">
            {searchQuery || severityFilter !== 'all' || statusFilter !== 'all'
              ? t('common.noResults')
              : t('proofreading.messages.noIssuesFound')}
          </div>
        ) : (
          filteredIssues.map((issue, index) => (
            <IssueListItem
              key={issue.id}
              issue={issue}
              index={index + 1}
              isSelected={selectedIssue?.id === issue.id}
              isChecked={selectedIssueIds.has(issue.id)}
              decision={decisions[issue.id]}
              onClick={() => onSelectIssue(issue)}
              onCheckChange={() => onToggleSelect(issue.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}

interface IssueListItemProps {
  issue: ProofreadingIssue;
  index: number;
  isSelected: boolean;
  isChecked: boolean;
  decision?: DecisionPayload;
  onClick: () => void;
  onCheckChange: () => void;
}

function IssueListItem({
  issue,
  index,
  isSelected,
  isChecked,
  decision,
  onClick,
  onCheckChange,
}: IssueListItemProps) {
  const decisionStatus = decision?.decision_type || issue.decision_status;

  return (
    <div
      className={cn(
        'cursor-pointer border-b border-gray-100 p-4 transition-colors hover:bg-gray-50',
        isSelected && 'border-l-4 border-l-blue-500 bg-blue-50',
        decisionStatus === 'accepted' && 'bg-green-50',
        decisionStatus === 'rejected' && 'bg-gray-50 opacity-60'
      )}
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        {/* Checkbox */}
        <input
          type="checkbox"
          checked={isChecked}
          onChange={(e) => {
            e.stopPropagation();
            onCheckChange();
          }}
          className="mt-0.5"
        />

        {/* Severity Icon */}
        <div className="flex-shrink-0">
          {issue.severity === 'critical' && (
            <AlertCircle className="h-5 w-5 text-red-500" />
          )}
          {issue.severity === 'warning' && (
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
          )}
          {issue.severity === 'info' && <Info className="h-5 w-5 text-blue-500" />}
        </div>

        {/* Issue Content */}
        <div className="min-w-0 flex-1">
          <div className="mb-1 text-xs font-medium text-gray-500">
            #{index} · {issue.rule_category}
          </div>
          <p className="truncate text-sm font-medium text-gray-900">
            {issue.original_text}
          </p>
          <p className="truncate text-xs text-gray-600">
            → {issue.suggested_text}
          </p>

          {/* Decision Badge */}
          {decisionStatus !== 'pending' && (
            <div className="mt-2">
              <DecisionBadge status={decisionStatus} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DecisionBadge({ status }: { status: DecisionStatus }) {
  const config = {
    accepted: { label: '✓ Accepted', className: 'bg-green-100 text-green-700' },
    rejected: { label: '✗ Rejected', className: 'bg-gray-100 text-gray-700' },
    modified: { label: '✎ Modified', className: 'bg-purple-100 text-purple-700' },
    pending: { label: 'Pending', className: 'bg-gray-100 text-gray-500' },
  };

  const { label, className } = config[status];

  return (
    <span className={cn('inline-block rounded px-2 py-0.5 text-xs font-medium', className)}>
      {label}
    </span>
  );
}
