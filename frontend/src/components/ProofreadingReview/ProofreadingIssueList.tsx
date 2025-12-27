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
  Filter,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { cn } from '@/lib/cn';

/**
 * Human-readable category labels for proofreading issue categories
 */
const CATEGORY_LABELS: Record<string, { zh: string; en: string }> = {
  T: { zh: '錯字', en: 'Typo' },
  P: { zh: '標點', en: 'Punctuation' },
  S: { zh: '結構', en: 'Structure' },
  C: { zh: '一致性', en: 'Consistency' },
  G: { zh: '文法', en: 'Grammar' },
  W: { zh: '用詞', en: 'Word Choice' },
};

/**
 * Get human-readable label for a category code
 */
function getCategoryLabel(code: string, locale: string = 'zh'): string {
  const label = CATEGORY_LABELS[code];
  if (!label) return code;
  return locale.startsWith('en') ? label.en : label.zh;
}

/**
 * Strip HTML tags from text for plain text display
 * This prevents HTML tags from showing as raw text in the issue list
 */
function stripHtmlTags(html: string | undefined | null): string {
  if (!html) return '';
  // Step 1: Use DOMParser to strip actual HTML tags and decode entities
  const doc = new DOMParser().parseFromString(html, 'text/html');
  let text = doc.body.textContent || '';
  // Step 2: Remove any remaining HTML-like tags (encoded as entities)
  text = text.replace(/<[^>]*>/g, '');
  // Step 3: Clean up URLs that might leak through
  text = text.replace(/https?:\/\/[^\s<>]*/g, '');
  // Step 4: Normalize whitespace
  text = text.replace(/\s+/g, ' ').trim();
  return text;
}

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
  const { t, i18n } = useTranslation();
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<IssueSeverity | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<DecisionStatus | 'all'>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [engineFilter, setEngineFilter] = useState<IssueEngine | 'all'>('all');
  const [showFilters, setShowFilters] = useState(false);

  // Check if any filter is active
  const hasActiveFilters = severityFilter !== 'all' || statusFilter !== 'all' ||
    categoryFilter !== 'all' || engineFilter !== 'all';
  const activeFilterCount = [severityFilter !== 'all', statusFilter !== 'all',
    categoryFilter !== 'all', engineFilter !== 'all'].filter(Boolean).length;

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
      <div className="border-b border-gray-200 p-3">
        {/* Search Bar */}
        <div className="relative mb-2">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <Input
            type="text"
            placeholder={t('common.search')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 h-8 text-sm"
          />
        </div>

        {/* Collapsible Filter Toggle */}
        <button
          type="button"
          onClick={() => setShowFilters(!showFilters)}
          className={cn(
            'flex w-full items-center justify-between rounded px-2 py-1.5 text-xs font-medium transition-colors',
            hasActiveFilters
              ? 'bg-blue-50 text-blue-700 hover:bg-blue-100'
              : 'text-gray-600 hover:bg-gray-100'
          )}
        >
          <span className="flex items-center gap-1.5">
            <Filter className="h-3.5 w-3.5" />
            {t('proofreading.issueList.filters.title') || '篩選'}
            {activeFilterCount > 0 && (
              <span className="rounded-full bg-blue-600 px-1.5 py-0.5 text-[10px] font-bold text-white">
                {activeFilterCount}
              </span>
            )}
          </span>
          {showFilters ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
        </button>

        {/* Collapsible Filter Panel */}
        {showFilters && (
          <div className="mt-2 space-y-1.5 rounded-md bg-gray-50 p-2">
            {/* Row 1: Severity + Status */}
            <div className="flex gap-1.5">
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value as any)}
                className={cn(
                  'flex-1 rounded border px-1.5 py-1 text-xs',
                  severityFilter !== 'all'
                    ? 'border-blue-300 bg-blue-50 text-blue-700'
                    : 'border-gray-200 bg-white'
                )}
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
                className={cn(
                  'flex-1 rounded border px-1.5 py-1 text-xs',
                  statusFilter !== 'all'
                    ? 'border-blue-300 bg-blue-50 text-blue-700'
                    : 'border-gray-200 bg-white'
                )}
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

            {/* Row 2: Category + Engine */}
            <div className="flex gap-1.5">
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className={cn(
                  'flex-1 rounded border px-1.5 py-1 text-xs',
                  categoryFilter !== 'all'
                    ? 'border-blue-300 bg-blue-50 text-blue-700'
                    : 'border-gray-200 bg-white'
                )}
              >
                <option value="all">
                  {t('proofreading.issueList.filters.category.all')}
                </option>
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {getCategoryLabel(category, i18n.language)} ({category})
                  </option>
                ))}
              </select>

              <select
                value={engineFilter}
                onChange={(e) => setEngineFilter(e.target.value as any)}
                className={cn(
                  'flex-1 rounded border px-1.5 py-1 text-xs',
                  engineFilter !== 'all'
                    ? 'border-blue-300 bg-blue-50 text-blue-700'
                    : 'border-gray-200 bg-white'
                )}
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

            {/* Clear Filters Button */}
            {hasActiveFilters && (
              <button
                type="button"
                onClick={() => {
                  setSeverityFilter('all');
                  setStatusFilter('all');
                  setCategoryFilter('all');
                  setEngineFilter('all');
                }}
                className="w-full rounded bg-gray-200 px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-300"
              >
                {t('proofreading.issueList.filters.clear') || '清除篩選'}
              </button>
            )}
          </div>
        )}
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
    const { t, i18n } = useTranslation();
    const decisionStatus = decision?.decision_type || issue.decision_status;
    const categoryCode = issue.rule_category || '';
    const categoryLabel = categoryCode
      ? getCategoryLabel(categoryCode, i18n.language)
      : t('proofreading.issueList.uncategorized');
    const originalText =
      stripHtmlTags(issue.original_text) || t('proofreading.issueList.noOriginalText');
    const suggestedText = stripHtmlTags(issue.suggested_text) || originalText;

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
