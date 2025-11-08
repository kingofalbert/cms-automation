/**
 * Proofreading Issue List
 * Left sidebar showing all proofreading issues with filtering.
 */

import { useState, useMemo, useEffect, useRef, forwardRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ProofreadingIssue,
  DecisionPayload,
  IssueSeverity,
  DecisionStatus,
  IssueEngine,
} from '@/types/worklist';
import { Button, Input } from '@/components/ui';
import {
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle,
  XCircle,
  Search,
  Sparkles,
  Code,
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
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [engineFilter, setEngineFilter] = useState<IssueEngine | 'all'>('all');

  // Refs to track issue elements for scrolling
  const issueRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  // Get unique categories from issues
  const categories = useMemo(() => {
    const uniqueCategories = new Set(
      issues
        .map((issue) => issue.rule_category)
        .filter((category): category is string => Boolean(category))
    );
    return Array.from(uniqueCategories).sort();
  }, [issues]);

  // Filter issues
  const filteredIssues = useMemo(() => {
    return issues.filter((issue) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const haystacks = [issue.original_text, issue.suggested_text, issue.explanation]
          .filter((value): value is string => Boolean(value))
          .map((value) => value.toLowerCase());
        if (!haystacks.some((text) => text.includes(query))) {
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

      // Category filter
      if (categoryFilter !== 'all') {
        const issueCategory = issue.rule_category || '';
        if (issueCategory !== categoryFilter) {
          return false;
        }
      }

      // Engine filter
      if (engineFilter !== 'all' && issue.engine !== engineFilter) {
        return false;
      }

      return true;
    });
  }, [issues, searchQuery, severityFilter, statusFilter, categoryFilter, engineFilter, decisions]);

  // Auto-scroll to selected issue in left sidebar when it changes (keyboard navigation)
  useEffect(() => {
    if (!selectedIssue) return;

    const element = issueRefs.current.get(selectedIssue.id);
    if (element) {
      // Small delay to ensure DOM is updated
      const timer = setTimeout(() => {
        element.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest', // Keep it in view without scrolling unnecessarily
          inline: 'nearest'
        });
      }, 50);

      return () => clearTimeout(timer);
    }
  }, [selectedIssue]);

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

        <div className="space-y-2">
          <div className="flex gap-2">
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value as any)}
              className="flex-1 rounded-md border border-gray-300 px-2 py-1 text-sm"
            >
              <option value="all">
                {t('proofreading.issueList.filters.severity.all')}
              </option>
              <option value="critical">
                {t('proofreading.issueList.filters.severity.critical')}
              </option>
              <option value="warning">
                {t('proofreading.issueList.filters.severity.warning')}
              </option>
              <option value="info">
                {t('proofreading.issueList.filters.severity.info')}
              </option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="flex-1 rounded-md border border-gray-300 px-2 py-1 text-sm"
            >
              <option value="all">
                {t('proofreading.issueList.filters.status.all')}
              </option>
              <option value="pending">
                {t('proofreading.issueList.filters.status.pending')}
              </option>
              <option value="accepted">
                {t('proofreading.issueList.filters.status.accepted')}
              </option>
              <option value="rejected">
                {t('proofreading.issueList.filters.status.rejected')}
              </option>
              <option value="modified">
                {t('proofreading.issueList.filters.status.modified')}
              </option>
            </select>
          </div>

          <div className="flex gap-2">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="flex-1 rounded-md border border-gray-300 px-2 py-1 text-sm"
            >
              <option value="all">
                {t('proofreading.issueList.filters.category.all')}
              </option>
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>

            <select
              value={engineFilter}
              onChange={(e) => setEngineFilter(e.target.value as any)}
              className="flex-1 rounded-md border border-gray-300 px-2 py-1 text-sm"
            >
              <option value="all">
                {t('proofreading.issueList.filters.engine.all')}
              </option>
              <option value="ai">
                {t('proofreading.issueList.filters.engine.ai')}
              </option>
              <option value="deterministic">
                {t('proofreading.issueList.filters.engine.deterministic')}
              </option>
            </select>
          </div>
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
              ref={(el) => {
                if (el) {
                  issueRefs.current.set(issue.id, el);
                } else {
                  issueRefs.current.delete(issue.id);
                }
              }}
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

const IssueListItem = forwardRef<HTMLDivElement, IssueListItemProps>(
  ({ issue, index, isSelected, isChecked, decision, onClick, onCheckChange }, ref) => {
    const { t } = useTranslation();
    const decisionStatus = decision?.decision_type || issue.decision_status;
    const categoryLabel =
      issue.rule_category || t('proofreading.issueList.uncategorized');
    const originalText =
      issue.original_text || t('proofreading.issueList.noOriginalText');
    const suggestedText = issue.suggested_text || originalText;

    return (
      <div
        ref={ref}
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
          <div className="mb-1 flex items-center gap-2 text-xs font-medium text-gray-500">
            <span>
              #{index} · {categoryLabel}
            </span>
            {/* Engine Badge */}
            {issue.engine === 'ai' ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-2 py-0.5 text-xs text-purple-700">
                <Sparkles className="h-3 w-3" />
                {t('proofreading.issueList.filters.engine.ai')}
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                <Code className="h-3 w-3" />
                {t('proofreading.issueList.filters.engine.deterministic')}
              </span>
            )}
            {/* Confidence Badge (AI only) */}
            {issue.engine === 'ai' && issue.confidence !== undefined && (
              <span className={cn(
                'rounded-full px-2 py-0.5 text-xs font-medium',
                issue.confidence >= 0.8 ? 'bg-green-100 text-green-700' :
                issue.confidence >= 0.6 ? 'bg-yellow-100 text-yellow-700' :
                'bg-red-100 text-red-700'
              )}>
                {Math.round(issue.confidence * 100)}%
              </span>
            )}
          </div>
          <p className="truncate text-sm font-medium text-gray-900">
            {originalText}
          </p>
          <p className="truncate text-xs text-gray-600">
            → {suggestedText}
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
);

IssueListItem.displayName = 'IssueListItem';

function DecisionBadge({ status }: { status: DecisionStatus }) {
  const { t } = useTranslation();
  const classNameMap: Record<DecisionStatus, string> = {
    accepted: 'bg-green-100 text-green-700',
    rejected: 'bg-gray-100 text-gray-700',
    modified: 'bg-purple-100 text-purple-700',
    pending: 'bg-gray-100 text-gray-500',
  };

  return (
    <span
      className={cn('inline-block rounded px-2 py-0.5 text-xs font-medium', classNameMap[status])}
    >
      {t(`proofreading.issueList.badges.${status}` as const)}
    </span>
  );
}
