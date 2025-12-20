/**
 * ProofreadingReviewPanel - Proofreading review interface
 *
 * Redesigned Phase 8.6: Three-panel layout with Article Content highlighting
 * - Left (20%): Compact issue list for quick navigation
 * - Center (50%): Article content with issues highlighted at positions
 * - Right (30%): Issue detail panel with full actions
 *
 * Layout:
 * ┌────────────┬──────────────────────┬─────────────────┐
 * │ Issue List │ Article Content      │ Issue Details   │
 * │ (20%)      │ (50%)                │ (30%)           │
 * │ • #1 Typo  │ Text with [issues]   │ Original/Suggest│
 * │ • #2 Punc  │ highlighted inline   │ Accept/Reject   │
 * │ • #3 ...   │ Click to select      │ Explanation     │
 * └────────────┴──────────────────────┴─────────────────┘
 */

import React, { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { FileText, Eye, AlertCircle, AlertTriangle, Info, Check, X, CheckCircle, XCircle, Sparkles, Code, GitCompare, Edit3, ShieldAlert, MapPin, Type, FileWarning, Lightbulb } from 'lucide-react';
import { Button, Badge } from '../ui';
import { DiffViewSection, type DiffStats } from './DiffViewSection';
import { ProofreadingPreviewSection, type WordChange } from './ProofreadingPreviewSection';
import { BatchApprovalControls } from './BatchApprovalControls';
import type { ArticleReviewData } from '../../hooks/articleReview/useArticleReviewData';
import type { ProofreadingIssue, DecisionPayload, IssueSeverity, WarningLabel } from '../../types/worklist';

export interface ProofreadingReviewPanelProps {
  /** Article review data */
  data: ArticleReviewData;
  /**
   * Lifted state: Decisions managed by parent component
   * This ensures decisions survive component unmount during step navigation
   * See: docs/STATE_PERSISTENCE_FIX.md
   */
  decisions: Map<string, DecisionPayload>;
  /** Callback to update decisions in parent */
  onDecisionsChange: (decisions: Map<string, DecisionPayload>) => void;
  /** Callback when decisions are submitted */
  onSubmitDecisions: (decisions: DecisionPayload[]) => Promise<void>;
  /** Whether submission is in progress */
  isSubmitting?: boolean;
  /**
   * Callback when all issues have been processed (accepted/rejected)
   * Triggers the workflow completion prompt to proceed to publish preview
   */
  onAllDecisionsComplete?: () => void;
}

// Helper function for severity icons
const getSeverityIcon = (severity: IssueSeverity) => {
  switch (severity) {
    case 'critical':
      return <AlertCircle className="w-3.5 h-3.5 text-red-600" />;
    case 'warning':
      return <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />;
    case 'info':
      return <Info className="w-3.5 h-3.5 text-blue-600" />;
  }
};

// Warning label configuration for G-class contextual validation
interface WarningLabelConfig {
  label: string;
  icon: React.ReactNode;
  bgColor: string;
  textColor: string;
  borderColor: string;
}

const getWarningLabelConfig = (warningLabel: WarningLabel): WarningLabelConfig => {
  switch (warningLabel) {
    case 'manual_verify':
      return {
        label: '需手動驗證',
        icon: <ShieldAlert className="w-3 h-3" />,
        bgColor: 'bg-yellow-50',
        textColor: 'text-yellow-800',
        borderColor: 'border-yellow-300',
      };
    case 'ai_hallucination':
      return {
        label: '可能為AI幻覺',
        icon: <Sparkles className="w-3 h-3" />,
        bgColor: 'bg-purple-50',
        textColor: 'text-purple-800',
        borderColor: 'border-purple-300',
      };
    case 'geographic_anomaly':
      return {
        label: '地理邏輯異常',
        icon: <MapPin className="w-3 h-3" />,
        bgColor: 'bg-orange-50',
        textColor: 'text-orange-800',
        borderColor: 'border-orange-300',
      };
    case 'symbol_format':
      return {
        label: '符號格式異常',
        icon: <Type className="w-3 h-3" />,
        bgColor: 'bg-blue-50',
        textColor: 'text-blue-800',
        borderColor: 'border-blue-300',
      };
    case 'sentence_incomplete':
      return {
        label: '語句不完整',
        icon: <FileWarning className="w-3 h-3" />,
        bgColor: 'bg-red-50',
        textColor: 'text-red-800',
        borderColor: 'border-red-300',
      };
    case 'structure_suggestion':
      return {
        label: '結構優化建議',
        icon: <Lightbulb className="w-3 h-3" />,
        bgColor: 'bg-green-50',
        textColor: 'text-green-800',
        borderColor: 'border-green-300',
      };
  }
};

// Warning label badge component
const WarningLabelBadge: React.FC<{ warningLabel: WarningLabel; compact?: boolean }> = ({
  warningLabel,
  compact = false
}) => {
  const config = getWarningLabelConfig(warningLabel);
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${config.bgColor} ${config.textColor} ${config.borderColor}`}
      title={config.label}
    >
      {config.icon}
      {!compact && <span>{config.label}</span>}
    </span>
  );
};

/**
 * ProofreadingReviewPanel Component - 3-Panel Layout
 */
export const ProofreadingReviewPanel: React.FC<ProofreadingReviewPanelProps> = ({
  data,
  decisions,
  onDecisionsChange,
  onSubmitDecisions,
  isSubmitting = false,
  onAllDecisionsComplete,
}) => {
  // Note: decisions state is now lifted to parent (ArticleReviewModal)
  // This ensures state survives step navigation. See: docs/STATE_PERSISTENCE_FIX.md
  // View mode: 'article' (with highlights), 'diff', or 'preview'
  const [contentViewMode, setContentViewMode] = useState<'article' | 'diff' | 'preview'>('article');
  // Selected issue for detail panel
  const [selectedIssue, setSelectedIssue] = useState<ProofreadingIssue | null>(null);
  // Ref for scrolling to issues
  const contentRef = useRef<HTMLDivElement>(null);
  // Show completion dialog when all issues are processed
  const [showCompletionDialog, setShowCompletionDialog] = useState(false);
  // Auto-navigation notification
  const [autoNavMessage, setAutoNavMessage] = useState<string | null>(null);
  // Custom edit mode states
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState('');

  // Use article review issues if available (richer data with historical context)
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

  // Auto-select first issue when issues are loaded
  useEffect(() => {
    if (issues.length > 0 && !selectedIssue) {
      setSelectedIssue(issues[0]);
    }
  }, [issues, selectedIssue]);

  // Scroll to selected issue in article view
  useEffect(() => {
    if (selectedIssue && contentViewMode === 'article') {
      const timer = setTimeout(() => {
        const element = document.querySelector(`[data-issue-id="${selectedIssue.id}"]`);
        if (element) {
          element.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'nearest'
          });
        }
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [selectedIssue, contentViewMode]);

  // Get article content
  const articleContent = useMemo(() => {
    return data.articleReview?.content?.original || data.metadata?.body_html as string || '';
  }, [data]);

  // Render article content with highlighted issues
  const renderArticleWithHighlights = useMemo(() => {
    if (!articleContent || issues.length === 0) {
      return <p className="whitespace-pre-wrap text-gray-700 leading-relaxed">{articleContent || '无内容'}</p>;
    }

    // Sort issues by position (descending) to insert highlights from end to start
    const sortedIssues = [...issues].sort((a, b) => {
      const startA = typeof a?.position?.start === 'number' ? a.position.start : Number.MAX_SAFE_INTEGER;
      const startB = typeof b?.position?.start === 'number' ? b.position.start : Number.MAX_SAFE_INTEGER;
      return startA - startB;
    });

    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    sortedIssues.forEach((issue, idx) => {
      const rawStart = typeof issue.position?.start === 'number' ? issue.position.start : 0;
      const rawEnd = typeof issue.position?.end === 'number' && issue.position.end >= rawStart
        ? issue.position.end : rawStart;

      const start = Math.max(0, Math.min(articleContent.length, rawStart));
      const end = Math.max(start, Math.min(articleContent.length, rawEnd));

      const decision = decisions.get(issue.id);
      const decisionStatus = decision?.decision_type || issue.decision_status;

      // Add text before this issue
      if (start > lastIndex) {
        parts.push(
          <span key={`text-${idx}`} className="whitespace-pre-wrap">
            {articleContent.slice(lastIndex, start)}
          </span>
        );
      }

      // Get the original issue text from article content
      const originalText = end > start
        ? articleContent.slice(start, end)
        : issue.original_text || '?';

      const isSelected = selectedIssue?.id === issue.id;

      // DISPLAY LOGIC: Show "Current State" not "Deletion Traces"
      // - Pending: Show original text with severity highlight (clickable to review)
      // - Accepted: Show SUGGESTED text (green) - this is the "current state" after accepting
      // - Modified: Show CUSTOM EDITED text (purple) - user's custom modification
      // - Rejected: Show original text (gray, dimmed) - keeping original means no change
      const currentDecision = decisions.get(issue.id);
      const displayText = decisionStatus === 'accepted'
        ? (issue.suggested_text || originalText)  // Show AI-suggested version
        : decisionStatus === 'modified'
          ? (currentDecision?.modified_content || issue.suggested_text || originalText)  // Show custom edit
          : originalText;  // Show original for pending/rejected

      // Get title based on decision status
      const getTitle = () => {
        if (decisionStatus === 'accepted') {
          return `已接受修改: "${issue.original_text}" → "${issue.suggested_text}"`;
        }
        if (decisionStatus === 'modified') {
          return `已自定義修改: "${issue.original_text}" → "${currentDecision?.modified_content}"`;
        }
        return issue.explanation;
      };

      // Add highlighted issue - showing CURRENT STATE, not deletion traces
      parts.push(
        <span
          key={`issue-${issue.id}`}
          data-issue-id={issue.id}
          className={`cursor-pointer rounded px-0.5 transition-all inline ${
            isSelected ? 'ring-2 ring-blue-500 ring-offset-1' : ''
          } ${
            decisionStatus === 'accepted'
              ? 'bg-green-100 hover:bg-green-200 text-green-800'  // Accepted: show green (current state)
              : decisionStatus === 'modified'
                ? 'bg-purple-100 hover:bg-purple-200 text-purple-800'  // Modified: show purple (custom edit)
                : decisionStatus === 'rejected'
                  ? 'bg-gray-100 text-gray-500'  // Rejected: dimmed original
                  : issue.severity === 'critical'
                    ? 'bg-red-100 hover:bg-red-200'
                    : issue.severity === 'warning'
                      ? 'bg-amber-100 hover:bg-amber-200'
                      : 'bg-blue-100 hover:bg-blue-200'
          }`}
          onClick={() => setSelectedIssue(issue)}
          title={getTitle()}
        >
          {displayText}
        </span>
      );

      lastIndex = end;
    });

    // Add remaining text after last issue
    if (lastIndex < articleContent.length) {
      parts.push(
        <span key="text-end" className="whitespace-pre-wrap">
          {articleContent.slice(lastIndex)}
        </span>
      );
    }

    return <div className="whitespace-pre-wrap text-gray-700 leading-relaxed text-sm">{parts}</div>;
  }, [articleContent, issues, decisions, selectedIssue]);

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

  /**
   * Find the next pending issue after current selection
   * Returns null if all issues have been processed
   */
  const findNextPendingIssue = useCallback((
    currentIssueId: string,
    updatedDecisions: Map<string, DecisionPayload>
  ): ProofreadingIssue | null => {
    const currentIndex = issues.findIndex(i => i.id === currentIssueId);

    // First, look forward from current position
    for (let i = currentIndex + 1; i < issues.length; i++) {
      const issue = issues[i];
      const decision = updatedDecisions.get(issue.id);
      if (!decision && issue.decision_status === 'pending') {
        return issue;
      }
    }

    // Then, wrap around and check from beginning
    for (let i = 0; i < currentIndex; i++) {
      const issue = issues[i];
      const decision = updatedDecisions.get(issue.id);
      if (!decision && issue.decision_status === 'pending') {
        return issue;
      }
    }

    return null;
  }, [issues]);

  /**
   * Check if all issues have been processed
   */
  const checkAllDecisionsComplete = useCallback((
    updatedDecisions: Map<string, DecisionPayload>
  ): boolean => {
    return issues.every(issue => {
      const decision = updatedDecisions.get(issue.id);
      return decision || issue.decision_status !== 'pending';
    });
  }, [issues]);

  const handleDecision = useCallback((issueId: string, decision: DecisionPayload) => {
    const newDecisions = new Map(decisions);
    newDecisions.set(issueId, decision);
    onDecisionsChange(newDecisions);

    // Auto-navigation: Find and select the next pending issue
    const nextPending = findNextPendingIssue(issueId, newDecisions);

    if (nextPending) {
      // Show navigation message
      const actionText = decision.decision_type === 'accepted'
        ? '已接受'
        : decision.decision_type === 'modified'
          ? '已修改'
          : '已拒绝';
      setAutoNavMessage(`${actionText}，跳转到下一个待处理问题`);

      // Auto-select next issue after a brief delay for visual feedback
      setTimeout(() => {
        setSelectedIssue(nextPending);
        setAutoNavMessage(null);
      }, 300);
    } else {
      // All issues processed - check for completion
      if (checkAllDecisionsComplete(newDecisions)) {
        setShowCompletionDialog(true);
      }
    }
  }, [decisions, onDecisionsChange, findNextPendingIssue, checkAllDecisionsComplete]);

  const handleBatchDecision = useCallback((issueIds: string[], decisionType: 'accepted' | 'rejected') => {
    const newDecisions = new Map(decisions);
    issueIds.forEach((issueId) => {
      newDecisions.set(issueId, {
        issue_id: issueId,
        decision_type: decisionType,
        feedback_provided: false,
      });
    });
    onDecisionsChange(newDecisions);

    // Check for completion after batch operation
    if (checkAllDecisionsComplete(newDecisions)) {
      setShowCompletionDialog(true);
    }
  }, [decisions, onDecisionsChange, checkAllDecisionsComplete]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!selectedIssue) return;
      // Don't trigger shortcuts when typing in inputs
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      switch (e.key.toLowerCase()) {
        case 'a':
          if (!e.ctrlKey && !e.metaKey) {
            handleDecision(selectedIssue.id, {
              issue_id: selectedIssue.id,
              decision_type: 'accepted',
              feedback_provided: false,
            });
          }
          break;
        case 'r':
          if (!e.ctrlKey && !e.metaKey) {
            handleDecision(selectedIssue.id, {
              issue_id: selectedIssue.id,
              decision_type: 'rejected',
              feedback_provided: false,
            });
          }
          break;
        case 'e':
          if (!e.ctrlKey && !e.metaKey && !isEditing) {
            // Enter custom edit mode with suggested text pre-filled
            setEditedText(selectedIssue.suggested_text || selectedIssue.original_text || '');
            setIsEditing(true);
          }
          break;
        case 'escape':
          if (isEditing) {
            setIsEditing(false);
            setEditedText('');
          }
          break;
        case 'arrowdown':
          e.preventDefault();
          const currentIndex = issues.findIndex(i => i.id === selectedIssue.id);
          if (currentIndex < issues.length - 1) {
            setSelectedIssue(issues[currentIndex + 1]);
          }
          break;
        case 'arrowup':
          e.preventDefault();
          const currIdx = issues.findIndex(i => i.id === selectedIssue.id);
          if (currIdx > 0) {
            setSelectedIssue(issues[currIdx - 1]);
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedIssue, issues, handleDecision, isEditing]);

  const handleSubmit = async () => {
    const decisionList = Array.from(decisions.values());
    if (decisionList.length === 0) {
      alert('请至少做出一个审核决定');
      return;
    }

    await onSubmitDecisions(decisionList);
    // Note: Don't clear decisions here - they're managed by parent and will be
    // synced with backend data after refetch
  };

  const handleReset = () => {
    onDecisionsChange(new Map());
  };

  const hasPendingDecisions = decisions.size > 0;

  // Get decision status for an issue
  const getIssueStatus = (issue: ProofreadingIssue) => {
    const decision = decisions.get(issue.id);
    if (decision) return decision.decision_type;
    return issue.decision_status;
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header with stats */}
      <div className="px-4 py-3 bg-white border-b border-gray-200 shadow-sm">
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
            {currentStats.modified_count > 0 && (
              <span className="text-gray-600">
                已修改: <strong className="text-purple-600">{currentStats.modified_count}</strong>
              </span>
            )}
            {hasPendingDecisions && (
              <span className="text-blue-600 font-medium">
                ● {decisions.size} 待提交
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Main content: 3-column layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Column: Issue List (20%) */}
        <div className="w-1/5 min-w-[200px] border-r border-gray-200 bg-white overflow-y-auto">
          <div className="p-3 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">问题列表</span>
              <span className="text-xs text-gray-500">{issues.length} 项</span>
            </div>
          </div>

          <div className="divide-y divide-gray-100">
            {issues.map((issue, index) => {
              const status = getIssueStatus(issue);
              const isSelected = selectedIssue?.id === issue.id;

              return (
                <button
                  key={issue.id}
                  onClick={() => setSelectedIssue(issue)}
                  className={`w-full text-left p-3 transition-colors hover:bg-gray-50 ${
                    isSelected ? 'bg-blue-50 border-l-2 border-blue-500' : ''
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-xs text-gray-400 font-mono mt-0.5">
                      #{index + 1}
                    </span>
                    {getSeverityIcon(issue.severity)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 mb-1 flex-wrap">
                        <span className="text-xs font-medium text-gray-700 truncate">
                          {issue.rule_category || '通用'}
                        </span>
                        {issue.engine === 'ai' && (
                          <Sparkles className="w-3 h-3 text-purple-500" />
                        )}
                        {issue.warning_label && (
                          <WarningLabelBadge warningLabel={issue.warning_label} compact />
                        )}
                      </div>
                      <div className="text-xs text-gray-600 line-clamp-2">
                        <span className="text-red-600">{issue.original_text?.substring(0, 20)}</span>
                        <span className="text-gray-400 mx-1">→</span>
                        <span className="text-green-600">{issue.suggested_text?.substring(0, 20)}</span>
                      </div>
                    </div>
                    {/* Status indicator */}
                    {status !== 'pending' && (
                      <span className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center ${
                        status === 'accepted' ? 'bg-green-100 text-green-600' :
                        status === 'rejected' ? 'bg-red-100 text-red-600' :
                        'bg-purple-100 text-purple-600'
                      }`}>
                        {status === 'accepted' && <Check className="w-3 h-3" />}
                        {status === 'rejected' && <X className="w-3 h-3" />}
                        {status === 'modified' && <Code className="w-3 h-3" />}
                      </span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Batch controls at bottom of list */}
          {issues.length > 0 && (
            <div className="p-3 border-t border-gray-200 bg-gray-50">
              <BatchApprovalControls
                issues={issues}
                decisions={decisions}
                onBatchDecision={handleBatchDecision}
              />
            </div>
          )}
        </div>

        {/* Center Column: Article Content with Issue Highlights (50%) */}
        <div className="flex-1 overflow-y-auto bg-white">
          {/* View mode toggle */}
          <div className="p-3 border-b border-gray-200 bg-gray-50 sticky top-0 z-10">
            <div className="flex items-center justify-between">
              <div className="flex rounded-lg overflow-hidden border border-gray-200 bg-white">
                <button
                  type="button"
                  onClick={() => setContentViewMode('article')}
                  className={`px-3 py-1.5 text-sm font-medium flex items-center justify-center gap-1.5 transition-colors ${
                    contentViewMode === 'article'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5" />
                  文章
                </button>
                <button
                  type="button"
                  onClick={() => setContentViewMode('diff')}
                  className={`px-3 py-1.5 text-sm font-medium flex items-center justify-center gap-1.5 border-l border-gray-200 transition-colors ${
                    contentViewMode === 'diff'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <GitCompare className="w-3.5 h-3.5" />
                  对比
                </button>
                <button
                  type="button"
                  onClick={() => setContentViewMode('preview')}
                  className={`px-3 py-1.5 text-sm font-medium flex items-center justify-center gap-1.5 border-l border-gray-200 transition-colors ${
                    contentViewMode === 'preview'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Eye className="w-3.5 h-3.5" />
                  预览
                </button>
              </div>
              {/* Legend for article view */}
              {contentViewMode === 'article' && (
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-red-100 border border-red-200"></span>
                    严重
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-amber-100 border border-amber-200"></span>
                    警告
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-blue-100 border border-blue-200"></span>
                    信息
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="p-4" ref={contentRef}>
            {contentViewMode === 'article' ? (
              <div className="max-w-3xl mx-auto">
                {/* Article title */}
                {data.title && (
                  <h2 className="text-xl font-bold text-gray-900 mb-4">{data.title}</h2>
                )}
                {/* Article content with issue highlights */}
                <div className="prose prose-sm max-w-none">
                  {renderArticleWithHighlights}
                </div>
                {/* Issue count indicator */}
                <div className="mt-6 pt-4 border-t border-gray-200 text-xs text-gray-500 text-center">
                  点击高亮文本查看问题详情 • 共 {issues.length} 个问题
                </div>
              </div>
            ) : contentViewMode === 'diff' ? (
              <DiffViewSection
                originalContent={data.articleReview?.content?.original || ''}
                proofreadContent={data.articleReview?.content?.suggested || (data.metadata?.proofread_content as string) || data.articleReview?.content?.original || ''}
                diffStats={data.articleReview?.content?.changes?.stats as DiffStats | undefined}
                hasDiffData={!!data.articleReview?.content?.changes}
              />
            ) : (
              <ProofreadingPreviewSection
                originalContent={data.articleReview?.content?.original || ''}
                proofreadContent={data.articleReview?.content?.suggested || (data.metadata?.proofread_content as string) || data.articleReview?.content?.original || ''}
                diffStats={data.articleReview?.content?.changes?.stats as DiffStats | undefined}
                wordChanges={data.articleReview?.content?.changes?.word_changes as WordChange[] | undefined}
              />
            )}
          </div>
        </div>

        {/* Right Column: Issue Detail Panel (30%) */}
        <div className="w-[30%] min-w-[300px] border-l border-gray-200 bg-white overflow-y-auto">
          {selectedIssue ? (
            <div className="flex flex-col h-full">
              {/* Detail Header */}
              <div className="px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-gray-700">问题详情</h4>
                  <span className="text-xs text-gray-500">
                    {issues.findIndex(i => i.id === selectedIssue.id) + 1} / {issues.length}
                  </span>
                </div>
              </div>

              {/* Issue Category & Severity */}
              <div className="px-4 py-3 border-b border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  {getSeverityIcon(selectedIssue.severity)}
                  <span className="text-sm font-medium text-gray-700">
                    {selectedIssue.rule_category || '通用'}
                  </span>
                  {selectedIssue.engine === 'ai' && (
                    <Badge variant="secondary" className="text-xs bg-purple-100 text-purple-700">
                      <Sparkles className="w-3 h-3 mr-1" />
                      AI
                    </Badge>
                  )}
                </div>
                <div className="text-xs text-gray-500">
                  规则: {selectedIssue.rule_id}
                  {selectedIssue.confidence && ` • 置信度: ${Math.round(selectedIssue.confidence * 100)}%`}
                </div>
                {/* Warning label for G-class contextual validation */}
                {selectedIssue.warning_label && (
                  <div className="mt-2">
                    <WarningLabelBadge warningLabel={selectedIssue.warning_label} />
                  </div>
                )}
              </div>

              {/* Comparison: Current State vs Original */}
              <div className="px-4 py-3 border-b border-gray-200">
                {/* Header with comparison label */}
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-gray-700">新舊對比</span>
                  <span className="text-xs text-gray-400">點擊查看差異</span>
                </div>

                {/* CURRENT STATE (修改後現狀) - Shown prominently first */}
                <div className="mb-3">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-green-700 mb-1.5">
                    <CheckCircle className="w-3.5 h-3.5" />
                    修改後（現狀）
                  </div>
                  <div className="rounded-md border-2 border-green-200 bg-green-50 p-3 text-sm text-gray-900 font-medium">
                    {selectedIssue.suggested_text}
                  </div>
                </div>

                {/* Divider with arrow */}
                <div className="flex items-center gap-2 my-2">
                  <div className="flex-1 border-t border-gray-200"></div>
                  <span className="text-xs text-gray-400 flex items-center gap-1">
                    <svg className="w-3 h-3 rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                    </svg>
                    修改自
                  </span>
                  <div className="flex-1 border-t border-gray-200"></div>
                </div>

                {/* ORIGINAL (原始版本) - Shown as reference */}
                <div>
                  <div className="flex items-center gap-1.5 text-xs font-medium text-gray-500 mb-1.5">
                    <span className="inline-block h-2 w-2 rounded-full bg-gray-400"></span>
                    原始版本
                  </div>
                  <div className="rounded-md border border-gray-200 bg-gray-50 p-2.5 text-sm text-gray-600">
                    {selectedIssue.original_text}
                  </div>
                </div>
              </div>

              {/* Explanation */}
              <div className="px-4 py-3 border-b border-gray-200">
                <div className="text-xs font-medium text-gray-700 mb-1.5">说明</div>
                <p className="text-sm text-gray-600">{selectedIssue.explanation}</p>
                {selectedIssue.explanation_detail && (
                  <p className="mt-1.5 text-xs text-gray-500">{selectedIssue.explanation_detail}</p>
                )}
              </div>

              {/* Decision Actions */}
              <div className="px-4 py-4 flex-1">
                {isEditing ? (
                  /* Custom Edit Mode */
                  <div className="space-y-3">
                    <div className="text-xs font-medium text-purple-700 mb-1">自定義修改</div>
                    <textarea
                      value={editedText}
                      onChange={(e) => setEditedText(e.target.value)}
                      className="w-full h-24 p-2 text-sm border border-purple-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none"
                      placeholder="輸入您的修改內容..."
                      autoFocus
                    />
                    <div className="flex gap-2">
                      <Button
                        onClick={() => {
                          if (editedText.trim()) {
                            handleDecision(selectedIssue.id, {
                              issue_id: selectedIssue.id,
                              decision_type: 'modified',
                              modified_content: editedText.trim(),
                              feedback_provided: false,
                            });
                            setIsEditing(false);
                            setEditedText('');
                          }
                        }}
                        disabled={!editedText.trim()}
                        className="flex-1 bg-purple-600 hover:bg-purple-700"
                      >
                        <Check className="w-4 h-4 mr-1" />
                        確認修改
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setIsEditing(false);
                          setEditedText('');
                        }}
                        className="flex-1"
                      >
                        <X className="w-4 h-4 mr-1" />
                        取消
                      </Button>
                    </div>
                  </div>
                ) : decisions.get(selectedIssue.id) ? (
                  /* Decision Made - Show Status */
                  <div className="rounded-md border border-gray-200 bg-gray-50 p-3">
                    <div className="flex items-center gap-2 mb-2">
                      {decisions.get(selectedIssue.id)?.decision_type === 'accepted' && (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      )}
                      {decisions.get(selectedIssue.id)?.decision_type === 'rejected' && (
                        <XCircle className="w-4 h-4 text-red-600" />
                      )}
                      {decisions.get(selectedIssue.id)?.decision_type === 'modified' && (
                        <Edit3 className="w-4 h-4 text-purple-600" />
                      )}
                      <span className="text-sm font-medium text-gray-700">
                        已{decisions.get(selectedIssue.id)?.decision_type === 'accepted'
                          ? '接受'
                          : decisions.get(selectedIssue.id)?.decision_type === 'modified'
                            ? '自定義修改'
                            : '拒绝'}
                      </span>
                    </div>
                    {/* Show modified content if custom edited */}
                    {decisions.get(selectedIssue.id)?.decision_type === 'modified' && (
                      <div className="mb-2 p-2 bg-purple-50 border border-purple-200 rounded text-sm text-purple-800">
                        {decisions.get(selectedIssue.id)?.modified_content}
                      </div>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        const newDecisions = new Map(decisions);
                        newDecisions.delete(selectedIssue.id);
                        onDecisionsChange(newDecisions);
                      }}
                    >
                      撤销决定
                    </Button>
                  </div>
                ) : (
                  /* No Decision Yet - Show Options */
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2">
                      <Button
                        onClick={() => handleDecision(selectedIssue.id, {
                          issue_id: selectedIssue.id,
                          decision_type: 'accepted',
                          feedback_provided: false,
                        })}
                        className="w-full"
                      >
                        <CheckCircle className="w-4 h-4 mr-1.5" />
                        接受
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => handleDecision(selectedIssue.id, {
                          issue_id: selectedIssue.id,
                          decision_type: 'rejected',
                          feedback_provided: false,
                        })}
                        className="w-full"
                      >
                        <XCircle className="w-4 h-4 mr-1.5" />
                        拒绝
                      </Button>
                    </div>
                    {/* Custom Edit Button */}
                    <Button
                      variant="outline"
                      onClick={() => {
                        // Pre-fill with suggested text for easier editing
                        setEditedText(selectedIssue.suggested_text || selectedIssue.original_text || '');
                        setIsEditing(true);
                      }}
                      className="w-full border-purple-300 text-purple-700 hover:bg-purple-50"
                    >
                      <Edit3 className="w-4 h-4 mr-1.5" />
                      自定義修改
                    </Button>
                    <p className="text-xs text-center text-gray-400">
                      快捷键: A 接受 | R 拒绝 | E 編輯 | ↑↓ 导航
                    </p>
                  </div>
                )}
              </div>

              {/* Historical decisions for this issue */}
              {existingDecisions.filter(d => d.issue_id === selectedIssue.id).length > 0 && (
                <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
                  <div className="text-xs font-medium text-gray-600 mb-2">历史决策</div>
                  <div className="space-y-1.5">
                    {existingDecisions
                      .filter(d => d.issue_id === selectedIssue.id)
                      .slice(0, 2)
                      .map((d, idx) => (
                        <div key={idx} className="text-xs p-2 bg-white rounded border border-gray-200">
                          <span className={`font-medium ${
                            d.decision_type === 'accepted'
                              ? 'text-green-600'
                              : d.decision_type === 'modified'
                                ? 'text-purple-600'
                                : 'text-red-600'
                          }`}>
                            {d.decision_type === 'accepted'
                              ? '已接受'
                              : d.decision_type === 'modified'
                                ? '已修改'
                                : '已拒绝'}
                          </span>
                          <span className="text-gray-400 ml-2">
                            {new Date(d.decided_at).toLocaleDateString('zh-CN')}
                          </span>
                          {d.decision_type === 'modified' && d.modified_content && (
                            <div className="mt-1 text-gray-600 italic">
                              "{d.modified_content}"
                            </div>
                          )}
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center p-8">
                <Info className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                <p className="text-sm text-gray-500">请从左侧列表选择一个问题</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer with action buttons */}
      <div className="px-4 py-3 bg-white border-t border-gray-200 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {currentStats.pending_count > 0 && (
              <span className="text-amber-600">
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
              {isSubmitting ? '提交中...' : `提交审核 (${decisions.size})`}
            </Button>
          </div>
        </div>
      </div>

      {/* Auto-navigation toast notification */}
      {autoNavMessage && (
        <div className="fixed bottom-24 left-1/2 transform -translate-x-1/2 z-50 animate-fade-in">
          <div className="bg-gray-900 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
            <Check className="w-4 h-4 text-green-400" />
            <span className="text-sm">{autoNavMessage}</span>
          </div>
        </div>
      )}

      {/* Completion dialog - all issues processed */}
      {showCompletionDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={() => setShowCompletionDialog(false)}
          />
          {/* Dialog */}
          <div className="relative bg-white rounded-xl shadow-2xl max-w-md w-full mx-4 overflow-hidden animate-scale-in">
            {/* Success header */}
            <div className="bg-gradient-to-r from-green-500 to-emerald-600 px-6 py-8 text-center">
              <div className="w-16 h-16 mx-auto bg-white rounded-full flex items-center justify-center mb-4">
                <CheckCircle className="w-10 h-10 text-green-500" />
              </div>
              <h3 className="text-xl font-bold text-white">
                校对审核完成！
              </h3>
              <p className="text-green-100 mt-2">
                所有 {issues.length} 个问题已处理完毕
              </p>
            </div>

            {/* Stats summary */}
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <div className="flex justify-center gap-8">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {currentStats.accepted_count}
                  </div>
                  <div className="text-xs text-gray-500">已接受</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {currentStats.rejected_count}
                  </div>
                  <div className="text-xs text-gray-500">已拒绝</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {currentStats.modified_count}
                  </div>
                  <div className="text-xs text-gray-500">已修改</div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="px-6 py-4 space-y-3">
              <Button
                className="w-full"
                onClick={() => {
                  setShowCompletionDialog(false);
                  onAllDecisionsComplete?.();
                }}
              >
                <Eye className="w-4 h-4 mr-2" />
                进入发布预览
              </Button>
              <Button
                variant="outline"
                className="w-full"
                onClick={() => setShowCompletionDialog(false)}
              >
                继续检查
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

ProofreadingReviewPanel.displayName = 'ProofreadingReviewPanel';
