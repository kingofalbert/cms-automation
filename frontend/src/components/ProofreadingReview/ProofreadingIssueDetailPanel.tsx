/**
 * Proofreading Issue Detail Panel
 * Right sidebar showing issue details and decision actions.
 */

import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import DOMPurify from 'dompurify';
import { ProofreadingIssue, DecisionPayload, FeedbackCategory } from '@/types/worklist';
import { ProofreadingDecisionDetail } from '@/types/api';
import { Button, Input } from '@/components/ui';
import {
  CheckCircle,
  XCircle,
  Edit3,
  AlertCircle,
  AlertTriangle,
  Info,
  Sparkles,
  Code,
  History,
  Clock,
  Columns,
  GitCompareArrows,
  Eye,
} from 'lucide-react';
import { cn } from '@/lib/cn';

/**
 * Compute a simple word-level diff between two texts
 * Returns an array of diff segments with type: 'equal', 'delete', 'insert'
 */
function computeWordDiff(
  original: string,
  suggested: string
): Array<{ type: 'equal' | 'delete' | 'insert'; text: string }> {
  // Split into tokens (words and punctuation/spaces)
  const tokenize = (text: string): string[] => {
    const tokens: string[] = [];
    let current = '';
    for (const char of text) {
      if (/\s/.test(char) || /[，。、；：？！""''「」『』（）【】《》〈〉…—\.,;:?!\(\)\[\]\{\}]/.test(char)) {
        if (current) {
          tokens.push(current);
          current = '';
        }
        tokens.push(char);
      } else {
        current += char;
      }
    }
    if (current) tokens.push(current);
    return tokens;
  };

  const origTokens = tokenize(original);
  const suggTokens = tokenize(suggested);

  // Simple LCS-based diff
  const m = origTokens.length;
  const n = suggTokens.length;

  // Build LCS table
  const dp: number[][] = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (origTokens[i - 1] === suggTokens[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Backtrack to find diff
  const result: Array<{ type: 'equal' | 'delete' | 'insert'; text: string }> = [];
  let i = m, j = n;
  const temp: Array<{ type: 'equal' | 'delete' | 'insert'; text: string }> = [];

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && origTokens[i - 1] === suggTokens[j - 1]) {
      temp.unshift({ type: 'equal', text: origTokens[i - 1] });
      i--;
      j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      temp.unshift({ type: 'insert', text: suggTokens[j - 1] });
      j--;
    } else {
      temp.unshift({ type: 'delete', text: origTokens[i - 1] });
      i--;
    }
  }

  // Merge consecutive segments of the same type
  for (const seg of temp) {
    if (result.length > 0 && result[result.length - 1].type === seg.type) {
      result[result.length - 1].text += seg.text;
    } else {
      result.push({ ...seg });
    }
  }

  return result;
}

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

interface ProofreadingIssueDetailPanelProps {
  issue: ProofreadingIssue | null;
  decision?: DecisionPayload;
  onDecision: (issueId: string, decision: Partial<DecisionPayload>) => void;
  onClearDecision: (issueId: string) => void;
  existingDecisions?: ProofreadingDecisionDetail[];
  /** Current issue index (1-based) */
  issueIndex?: number;
  /** Total number of issues */
  totalIssues?: number;
}

export function ProofreadingIssueDetailPanel({
  issue,
  decision,
  onDecision,
  onClearDecision,
  existingDecisions = [],
  issueIndex,
  totalIssues,
}: ProofreadingIssueDetailPanelProps) {
  const { t, i18n } = useTranslation();
  const [modifiedContent, setModifiedContent] = useState('');
  const [rationale, setRationale] = useState('');
  const [feedbackNotes, setFeedbackNotes] = useState('');
  const [feedbackCategory, setFeedbackCategory] = useState<FeedbackCategory | ''>('');
  const [showFeedback, setShowFeedback] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [comparisonMode, setComparisonMode] = useState<'split' | 'diff'>('split');
  // Content display mode: 'rendered' shows formatted HTML, 'source' shows raw HTML tags
  const [contentDisplayMode, setContentDisplayMode] = useState<'rendered' | 'source'>('rendered');

  // Compute diff when issue changes
  const diffSegments = useMemo(() => {
    if (!issue) return [];
    return computeWordDiff(issue.original_text, issue.suggested_text);
  }, [issue?.original_text, issue?.suggested_text]);

  // Filter existing decisions for the current issue
  const issueHistory = issue
    ? existingDecisions.filter((d) => d.issue_id === issue.id)
    : [];

  if (!issue) {
    return (
      <div className="flex h-full flex-col">
        {/* Empty state header */}
        <div className="sticky top-0 z-10 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4">
          <h3 className="text-sm font-semibold text-gray-600">
            {t('proofreading.issueDetail.title', 'Issue Details')}
          </h3>
        </div>
        <div className="flex flex-1 items-center justify-center p-8 text-center">
          <div className="rounded-lg border-2 border-dashed border-gray-200 bg-gray-50 p-8">
            <Info className="mx-auto h-12 w-12 text-gray-300" />
            <p className="mt-4 text-sm font-medium text-gray-500">
              {t('proofreading.messages.selectIssue')}
            </p>
            <p className="mt-2 text-xs text-gray-400">
              {t('proofreading.messages.selectIssueHint', 'Click an issue from the list to view details')}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const handleAccept = () => {
    onDecision(issue.id, {
      decision_type: 'accepted',
      decision_rationale: rationale || 'Suggestion accepted',
      feedback_provided: Boolean(feedbackCategory),
      feedback_category: feedbackCategory || undefined,
      feedback_notes: feedbackNotes || undefined,
    });
    resetForm();
  };

  const handleReject = () => {
    onDecision(issue.id, {
      decision_type: 'rejected',
      decision_rationale: rationale || 'Suggestion rejected',
      feedback_provided: Boolean(feedbackCategory),
      feedback_category: feedbackCategory || undefined,
      feedback_notes: feedbackNotes || undefined,
    });
    resetForm();
  };

  const handleModify = () => {
    if (!modifiedContent.trim()) {
      alert('Please provide modified content');
      return;
    }

    onDecision(issue.id, {
      decision_type: 'modified',
      modified_content: modifiedContent,
      decision_rationale: rationale || 'Custom modification applied',
      feedback_provided: Boolean(feedbackCategory),
      feedback_category: feedbackCategory || undefined,
      feedback_notes: feedbackNotes || undefined,
    });
    resetForm();
  };

  const resetForm = () => {
    setModifiedContent('');
    setRationale('');
    setFeedbackNotes('');
    setFeedbackCategory('');
    setShowFeedback(false);
  };

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      {/* Sticky Header with Issue Index */}
      <div className="sticky top-0 z-10 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-3 shadow-sm">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">
            {t('proofreading.issueDetail.title', 'Issue Details')}
          </h3>
          {issueIndex !== undefined && totalIssues !== undefined && (
            <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700">
              {issueIndex} / {totalIssues}
            </span>
          )}
        </div>
      </div>

      {/* Issue Category Header */}
      <div className="border-b border-gray-200 bg-white p-5">
        <div className="mb-3 flex items-center gap-2">
          {/* Severity Icon */}
          {issue.severity === 'critical' && (
            <AlertCircle className="h-5 w-5 text-red-500" />
          )}
          {issue.severity === 'warning' && (
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
          )}
          {issue.severity === 'info' && <Info className="h-5 w-5 text-blue-500" />}

          <span className="text-sm font-medium text-gray-700">
            {issue.rule_category
              ? `${getCategoryLabel(issue.rule_category, i18n.language)} (${issue.rule_category})`
              : t('proofreading.issueList.uncategorized')}
          </span>

          {/* Engine Badge */}
          <span
            className={cn(
              'ml-auto rounded px-2 py-0.5 text-xs font-medium',
              issue.engine === 'ai'
                ? 'bg-purple-100 text-purple-700'
                : 'bg-gray-100 text-gray-700'
            )}
          >
            {issue.engine === 'ai' ? (
              <span className="flex items-center gap-1">
                <Sparkles className="h-3 w-3" />
                AI
              </span>
            ) : (
              <span className="flex items-center gap-1">
                <Code className="h-3 w-3" />
                Rule
              </span>
            )}
          </span>
        </div>

        <div className="text-xs text-gray-500">
          Rule: {issue.rule_id}
          {issue.confidence && ` • Confidence: ${Math.round(issue.confidence * 100)}%`}
        </div>
      </div>

      {/* Original vs Suggested */}
      <div className="border-b border-gray-200 p-5">
        {/* View Mode Toggle */}
        <div className="mb-3 flex items-center justify-between gap-2">
          {/* Comparison mode toggle */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => setComparisonMode('split')}
              className={cn(
                'flex items-center gap-1 rounded-l-md border px-2 py-1 text-xs transition-colors',
                comparisonMode === 'split'
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-300 bg-white text-gray-600 hover:bg-gray-50'
              )}
              title={t('proofreading.issueDetail.splitView', 'Split View')}
            >
              <Columns className="h-3 w-3" />
              <span className="hidden sm:inline">{t('proofreading.issueDetail.splitView', 'Split')}</span>
            </button>
            <button
              onClick={() => setComparisonMode('diff')}
              className={cn(
                'flex items-center gap-1 rounded-r-md border-l-0 border px-2 py-1 text-xs transition-colors',
                comparisonMode === 'diff'
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-300 bg-white text-gray-600 hover:bg-gray-50'
              )}
              title={t('proofreading.issueDetail.diffView', 'Diff View')}
            >
              <GitCompareArrows className="h-3 w-3" />
              <span className="hidden sm:inline">{t('proofreading.issueDetail.diffView', 'Diff')}</span>
            </button>
          </div>

          {/* Content display mode toggle */}
          <button
            onClick={() => setContentDisplayMode(contentDisplayMode === 'rendered' ? 'source' : 'rendered')}
            className={cn(
              'flex items-center gap-1 rounded-md border px-2 py-1 text-xs transition-colors',
              contentDisplayMode === 'rendered'
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-purple-500 bg-purple-50 text-purple-700'
            )}
            title={contentDisplayMode === 'rendered'
              ? t('proofreading.issueDetail.showSource', '切換到源碼視圖（查看 HTML 標籤）')
              : t('proofreading.issueDetail.showRendered', '切換到渲染視圖（查看格式效果）')}
          >
            {contentDisplayMode === 'rendered' ? (
              <>
                <Eye className="h-3 w-3" />
                <span>渲染</span>
              </>
            ) : (
              <>
                <Code className="h-3 w-3" />
                <span>源碼</span>
              </>
            )}
          </button>
        </div>

        {comparisonMode === 'split' ? (
          /* Split View - Original and Suggested in separate boxes */
          <>
            <div className="mb-4">
              <div className="mb-1.5 flex items-center gap-2 text-xs font-medium text-red-600">
                <span className="inline-block h-2 w-2 rounded-full bg-red-400"></span>
                {t('proofreading.issueDetail.original', 'Original')}
              </div>
              <div className="rounded-md border border-red-100 bg-red-50 p-3 text-sm text-gray-900">
                {contentDisplayMode === 'rendered' ? (
                  <div
                    className="prose prose-sm max-w-none prose-strong:text-red-800 prose-strong:font-bold prose-em:italic"
                    dangerouslySetInnerHTML={{
                      __html: DOMPurify.sanitize(issue.original_text || '', {
                        ALLOWED_TAGS: ['strong', 'b', 'em', 'i', 'u', 'span', 'mark', 'del', 'ins', 'sub', 'sup', 'br'],
                        ALLOWED_ATTR: ['class', 'style'],
                      }),
                    }}
                  />
                ) : (
                  <code className="text-xs font-mono bg-red-100 text-red-800 px-1 py-0.5 rounded break-all whitespace-pre-wrap">
                    {issue.original_text}
                  </code>
                )}
              </div>
            </div>

            <div>
              <div className="mb-1.5 flex items-center gap-2 text-xs font-medium text-green-600">
                <span className="inline-block h-2 w-2 rounded-full bg-green-400"></span>
                {t('proofreading.issueDetail.suggested', 'Suggested')}
              </div>
              <div className="rounded-md border border-green-100 bg-green-50 p-3 text-sm text-gray-900">
                {contentDisplayMode === 'rendered' ? (
                  <div
                    className="prose prose-sm max-w-none prose-strong:text-green-800 prose-strong:font-bold prose-em:italic"
                    dangerouslySetInnerHTML={{
                      __html: DOMPurify.sanitize(issue.suggested_text || '', {
                        ALLOWED_TAGS: ['strong', 'b', 'em', 'i', 'u', 'span', 'mark', 'del', 'ins', 'sub', 'sup', 'br'],
                        ALLOWED_ATTR: ['class', 'style'],
                      }),
                    }}
                  />
                ) : (
                  <code className="text-xs font-mono bg-green-100 text-green-800 px-1 py-0.5 rounded break-all whitespace-pre-wrap">
                    {issue.suggested_text}
                  </code>
                )}
              </div>
            </div>

            {/* Helper hint for formatting differences */}
            {contentDisplayMode === 'rendered' && (
              <div className="mt-3 text-xs text-gray-400 text-center">
                💡 點擊「源碼」查看 HTML 標籤差異（如粗體、斜體等格式標記）
              </div>
            )}
          </>
        ) : (
          /* Diff View - Inline diff highlighting */
          <div>
            <div className="mb-2 flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5 text-red-600">
                <span className="inline-block h-2 w-2 rounded-full bg-red-400"></span>
                {t('proofreading.issueDetail.deleted', 'Deleted')}
              </span>
              <span className="flex items-center gap-1.5 text-green-600">
                <span className="inline-block h-2 w-2 rounded-full bg-green-400"></span>
                {t('proofreading.issueDetail.added', 'Added')}
              </span>
            </div>
            <div className="rounded-md border border-gray-200 bg-gray-50 p-3 text-sm leading-relaxed">
              {diffSegments.map((segment, idx) => {
                if (segment.type === 'equal') {
                  return <span key={idx}>{segment.text}</span>;
                } else if (segment.type === 'delete') {
                  return (
                    <span
                      key={idx}
                      className="rounded bg-red-200 text-red-900 line-through decoration-red-400"
                    >
                      {segment.text}
                    </span>
                  );
                } else {
                  return (
                    <span
                      key={idx}
                      className="rounded bg-green-200 text-green-900 font-medium"
                    >
                      {segment.text}
                    </span>
                  );
                }
              })}
            </div>
          </div>
        )}
      </div>

      {/* Explanation */}
      <div className="border-b border-gray-200 p-5">
        <div className="mb-1.5 text-xs font-medium text-gray-700">
          {t('proofreading.issueDetail.explanation', 'Explanation')}
        </div>
        <p className="text-sm text-gray-600">{issue.explanation}</p>
        {issue.explanation_detail && (
          <p className="mt-2 text-xs text-gray-500">{issue.explanation_detail}</p>
        )}
      </div>

      {/* Historical Decisions */}
      {issueHistory.length > 0 && (
        <div className="border-b border-gray-200 p-6">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="mb-3 flex w-full items-center justify-between text-left text-xs font-medium text-gray-700 hover:text-gray-900"
          >
            <div className="flex items-center gap-2">
              <History className="h-4 w-4" />
              <span>Decision History ({issueHistory.length})</span>
            </div>
            <span className="text-gray-400">{showHistory ? '−' : '+'}</span>
          </button>

          {showHistory && (
            <div className="space-y-3">
              {issueHistory.map((hist, idx) => (
                <div
                  key={idx}
                  className={cn(
                    'rounded-lg border p-3',
                    hist.decision_type === 'accepted'
                      ? 'border-green-200 bg-green-50'
                      : hist.decision_type === 'rejected'
                      ? 'border-gray-200 bg-gray-50'
                      : 'border-purple-200 bg-purple-50'
                  )}
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span
                      className={cn(
                        'text-xs font-medium',
                        hist.decision_type === 'accepted'
                          ? 'text-green-700'
                          : hist.decision_type === 'rejected'
                          ? 'text-gray-700'
                          : 'text-purple-700'
                      )}
                    >
                      {hist.decision_type.toUpperCase()}
                    </span>
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                      <Clock className="h-3 w-3" />
                      {new Date(hist.decided_at).toLocaleDateString()}
                    </div>
                  </div>

                  {hist.rationale && (
                    <p className="mb-2 text-xs text-gray-600">{hist.rationale}</p>
                  )}

                  {hist.modified_content && (
                    <div className="mb-2 rounded bg-white p-2 text-xs text-gray-800">
                      Modified: "{hist.modified_content}"
                    </div>
                  )}

                  <div className="text-xs text-gray-500">
                    Reviewer: {hist.reviewer}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Decision Actions */}
      <div className="flex-1 p-6">
        {decision ? (
          <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
            <div className="mb-2 text-sm font-medium text-gray-700">
              Decision: {decision.decision_type}
            </div>
            {decision.decision_rationale && (
              <p className="mb-3 text-sm text-gray-600">{decision.decision_rationale}</p>
            )}
            <Button size="sm" variant="outline" onClick={() => onClearDecision(issue.id)}>
              Clear Decision
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Quick Actions */}
            <div className="grid grid-cols-2 gap-2">
              <Button onClick={handleAccept} className="w-full">
                <CheckCircle className="mr-2 h-4 w-4" />
                Accept
              </Button>
              <Button variant="outline" onClick={handleReject} className="w-full">
                <XCircle className="mr-2 h-4 w-4" />
                Reject
              </Button>
            </div>

            {/* Custom Modification */}
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                Custom Modification
              </label>
              <textarea
                value={modifiedContent}
                onChange={(e) => setModifiedContent(e.target.value)}
                placeholder="Enter custom text..."
                className="w-full rounded-md border border-gray-300 p-2 text-sm"
                rows={3}
              />
              <Button
                size="sm"
                variant="outline"
                onClick={handleModify}
                disabled={!modifiedContent.trim()}
                className="mt-2 w-full"
              >
                <Edit3 className="mr-2 h-3 w-3" />
                Apply Modification
              </Button>
            </div>

            {/* Rationale */}
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                Decision Rationale (Optional)
              </label>
              <Input
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                placeholder="Why did you make this decision?"
              />
            </div>

            {/* Feedback Accordion */}
            <div className="rounded-md border border-gray-200">
              <button
                onClick={() => setShowFeedback(!showFeedback)}
                className="flex w-full items-center justify-between p-3 text-left text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                <span>Provide Feedback (Optional)</span>
                <span className="text-gray-400">{showFeedback ? '−' : '+'}</span>
              </button>

              {showFeedback && (
                <div className="space-y-3 border-t border-gray-200 p-3">
                  <div>
                    <label className="mb-1 block text-xs font-medium text-gray-700">
                      Feedback Category
                    </label>
                    <select
                      value={feedbackCategory}
                      onChange={(e) => setFeedbackCategory(e.target.value as any)}
                      className="w-full rounded-md border border-gray-300 p-2 text-sm"
                    >
                      <option value="">Select category...</option>
                      <option value="suggestion_correct">Suggestion Correct</option>
                      <option value="suggestion_partially_correct">
                        Partially Correct
                      </option>
                      <option value="suggestion_incorrect">Suggestion Incorrect</option>
                      <option value="rule_needs_adjustment">Rule Needs Adjustment</option>
                    </select>
                  </div>

                  <div>
                    <label className="mb-1 block text-xs font-medium text-gray-700">
                      Feedback Notes
                    </label>
                    <textarea
                      value={feedbackNotes}
                      onChange={(e) => setFeedbackNotes(e.target.value)}
                      placeholder="Additional comments for improving the rule..."
                      className="w-full rounded-md border border-gray-300 p-2 text-sm"
                      rows={3}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Keyboard Shortcuts Hint */}
      <div className="border-t border-gray-200 bg-gradient-to-r from-gray-50 to-gray-100 p-4">
        <div className="text-xs text-gray-500">
          <div className="font-medium text-gray-600">
            {t('proofreading.issueDetail.keyboardShortcuts', 'Keyboard Shortcuts')}:
          </div>
          <div className="mt-1.5 grid grid-cols-3 gap-2 text-center">
            <kbd className="rounded border border-gray-300 bg-white px-2 py-1 font-mono text-xs shadow-sm">
              A
            </kbd>
            <kbd className="rounded border border-gray-300 bg-white px-2 py-1 font-mono text-xs shadow-sm">
              R
            </kbd>
            <kbd className="rounded border border-gray-300 bg-white px-2 py-1 font-mono text-xs shadow-sm">
              ↑/↓
            </kbd>
          </div>
          <div className="mt-1 grid grid-cols-3 gap-2 text-center text-[10px]">
            <span>{t('proofreading.actions.accept', 'Accept')}</span>
            <span>{t('proofreading.actions.reject', 'Reject')}</span>
            <span>Navigate</span>
          </div>
        </div>
      </div>
    </div>
  );
}
