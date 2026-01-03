/**
 * Proofreading Review Page
 * Human review interface for AI-generated proofreading suggestions.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { stripHtmlTags, resolveAllIssuePositions, removeOverlappingRanges } from '@/utils/proofreadingPosition';
import { toast } from 'sonner';
import { worklistAPI } from '@/services/worklist';
import {
  ProofreadingIssue,
  DecisionPayload,
  DecisionType,
  WorklistItemDetail,
} from '@/types/worklist';
import { APIProofreadingIssue, transformAPIProofreadingIssues } from '@/types/api';
import { ProofreadingIssueList } from '@/components/ProofreadingReview/ProofreadingIssueList';
import { ProofreadingArticleContent } from '@/components/ProofreadingReview/ProofreadingArticleContent';
import { ProofreadingIssueDetailPanel } from '@/components/ProofreadingReview/ProofreadingIssueDetailPanel';
import { ReviewStatsBar } from '@/components/ProofreadingReview/ReviewStatsBar';
import { ProofreadingReviewHeader } from '@/components/ProofreadingReview/ProofreadingReviewHeader';
import { Button, SkeletonProofreadingPage, EmptyState, KeyboardShortcutsHint, PROOFREADING_SHORTCUTS_COMPACT } from '@/components/ui';
import { ArrowLeft, CheckCircle, AlertCircle, PanelLeftClose, PanelRightClose } from 'lucide-react';

type ViewMode = 'original' | 'preview' | 'diff' | 'rendered';

export default function ProofreadingReviewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  // Local state
  const [selectedIssue, setSelectedIssue] = useState<ProofreadingIssue | null>(null);
  const [decisions, setDecisions] = useState<Record<string, DecisionPayload>>({});
  const [reviewNotes, setReviewNotes] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('original');
  const [selectedIssueIds, setSelectedIssueIds] = useState<Set<string>>(new Set());

  // Responsive panel visibility (for mobile/tablet)
  const [showIssueList, setShowIssueList] = useState(true);
  const [showIssueDetail, setShowIssueDetail] = useState(true);

  // Fetch worklist item (contains all proofreading data)
  const {
    data: worklistItem,
    isLoading,
    error,
  } = useQuery<WorklistItemDetail>({
    queryKey: ['worklist-detail', id],
    queryFn: () => worklistAPI.get(Number(id)),
    enabled: Boolean(id),
  });

  // Save decisions mutation
  const saveDecisionsMutation = useMutation({
    mutationFn: async (transitionTo?: 'ready_to_publish' | 'proofreading' | 'failed') => {
      const decisionsArray = Object.values(decisions);
      if (decisionsArray.length === 0) {
        throw new Error('No decisions to save');
      }

      return worklistAPI.saveReviewDecisions(Number(id), {
        decisions: decisionsArray,
        review_notes: reviewNotes || undefined,
        transition_to: transitionTo,
      });
    },
    onSuccess: (_data, transitionTo) => {
      toast.success(
        transitionTo
          ? t('proofreading.messages.reviewCompletedAndTransitioned')
          : t('proofreading.messages.decisionsSaved')
      );
      queryClient.invalidateQueries({ queryKey: ['worklist-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['worklist'] });

      // Clear local decisions
      setDecisions({});
      setReviewNotes('');

      if (transitionTo === 'ready_to_publish') {
        navigate('/worklist');
      }
    },
    onError: (error: any) => {
      toast.error(
        `${t('proofreading.messages.saveFailed')}: ${
          error.response?.data?.message || error.message
        }`
      );
    },
  });

  // Get issues and stats from worklist item
  // Transform API format issues to frontend format if needed
  const rawIssues = worklistItem?.proofreading_issues || [];
  const issues: ProofreadingIssue[] = (() => {
    if (rawIssues.length === 0) return [];
    // Check if first issue is in API format (has 'evidence' or 'message' fields)
    // API format uses: evidence, suggestion, message, category
    // Frontend format uses: original_text, suggested_text, explanation, rule_category
    const firstIssue = rawIssues[0] as unknown as Record<string, unknown>;
    if ('evidence' in firstIssue || 'message' in firstIssue) {
      // Transform from API format to frontend format
      return transformAPIProofreadingIssues(rawIssues as unknown as APIProofreadingIssue[]);
    }
    // Already in frontend format
    return rawIssues as ProofreadingIssue[];
  })();
  const stats = worklistItem?.proofreading_stats;

  // Add decision
  const addDecision = (issueId: string, decision: Partial<DecisionPayload>) => {
    setDecisions((prev) => ({
      ...prev,
      [issueId]: {
        issue_id: issueId,
        decision_type: decision.decision_type || 'accepted',
        decision_rationale: decision.decision_rationale,
        modified_content: decision.modified_content,
        feedback_provided: decision.feedback_provided || false,
        feedback_category: decision.feedback_category,
        feedback_notes: decision.feedback_notes,
      },
    }));
  };

  // Batch decisions
  const batchDecision = (issueIds: string[], decisionType: DecisionType) => {
    const newDecisions = { ...decisions };
    issueIds.forEach((issueId) => {
      newDecisions[issueId] = {
        issue_id: issueId,
        decision_type: decisionType,
        decision_rationale: `Batch ${decisionType}`,
        feedback_provided: false,
      };
    });
    setDecisions(newDecisions);
    setSelectedIssueIds(new Set());
    toast.success(`${issueIds.length} issues ${decisionType}`);
  };

  // Clear decision
  const clearDecision = (issueId: string) => {
    setDecisions((prev) => {
      const next = { ...prev };
      delete next[issueId];
      return next;
    });
  };

  // Computed values
  const dirtyCount = Object.keys(decisions).length;
  const allIssuesDecided = issues.length > 0 && issues.length === dirtyCount;
  const hasUnsavedChanges = dirtyCount > 0 || reviewNotes.length > 0;

  // Generate suggested content by applying all issue suggestions to the original content
  // This is used for the Diff view mode
  const suggestedContent = useMemo(() => {
    if (!worklistItem?.content || issues.length === 0) {
      return null;
    }

    // Get plain text from original content
    const plainContent = stripHtmlTags(worklistItem.content);
    if (!plainContent) return null;

    // Resolve all issue positions
    const resolvedPositions = resolveAllIssuePositions(issues, plainContent);
    const nonOverlapping = removeOverlappingRanges(resolvedPositions);

    if (nonOverlapping.length === 0) {
      return plainContent; // No changes to apply
    }

    // Build suggested content by applying all suggestions
    let result = '';
    let lastIndex = 0;

    nonOverlapping.forEach(({ issue, position }) => {
      // Add text before this issue
      if (position.start > lastIndex) {
        result += plainContent.slice(lastIndex, position.start);
      }

      // Add the suggested text (or original if no suggestion)
      const suggestedText = issue.suggested_text_plain || stripHtmlTags(issue.suggested_text);
      result += suggestedText || plainContent.slice(position.start, position.end);

      lastIndex = position.end;
    });

    // Add remaining text after last issue
    if (lastIndex < plainContent.length) {
      result += plainContent.slice(lastIndex);
    }

    return result;
  }, [worklistItem?.content, issues]);

  // Handle cancel with confirmation if there are unsaved changes
  const handleCancel = useCallback(() => {
    if (hasUnsavedChanges) {
      const confirmed = window.confirm(
        t('proofreading.messages.cancelConfirm') ||
        'You have unsaved changes. Are you sure you want to cancel and return to the worklist?'
      );
      if (!confirmed) return;
    }
    navigate('/worklist');
  }, [hasUnsavedChanges, navigate, t]);

  // Handle keyboard shortcuts
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!selectedIssue) return;

    switch (e.key) {
      case 'a':
      case 'A':
        if (!e.ctrlKey && !e.metaKey) {
          addDecision(selectedIssue.id, { decision_type: 'accepted' });
        }
        break;
      case 'r':
      case 'R':
        if (!e.ctrlKey && !e.metaKey) {
          addDecision(selectedIssue.id, { decision_type: 'rejected' });
        }
        break;
      case ' ':
        // Toggle checkbox selection for current issue
        e.preventDefault();
        setSelectedIssueIds((prev) => {
          const next = new Set(prev);
          if (next.has(selectedIssue.id)) {
            next.delete(selectedIssue.id);
          } else {
            next.add(selectedIssue.id);
          }
          return next;
        });
        break;
      case 'ArrowDown':
      case 'ArrowUp':
        e.preventDefault();
        const currentIndex = issues.findIndex((i) => i.id === selectedIssue.id);
        if (e.key === 'ArrowDown' && currentIndex < issues.length - 1) {
          setSelectedIssue(issues[currentIndex + 1]);
        } else if (e.key === 'ArrowUp' && currentIndex > 0) {
          setSelectedIssue(issues[currentIndex - 1]);
        }
        break;
    }
  }, [selectedIssue, issues, addDecision, setSelectedIssueIds]);

  // Set up keyboard shortcuts
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown as any);
    return () => window.removeEventListener('keydown', handleKeyDown as any);
  }, [handleKeyDown]);

  // Auto-select first issue when issues are loaded
  useEffect(() => {
    if (issues.length > 0 && !selectedIssue) {
      setSelectedIssue(issues[0]);
    }
  }, [issues, selectedIssue]);

  if (isLoading) {
    return <SkeletonProofreadingPage />;
  }

  if (error || !worklistItem) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <EmptyState
          icon={<AlertCircle className="h-16 w-16 text-red-400" />}
          title={t('proofreading.messages.loadFailed')}
          description={t('proofreading.messages.loadFailedDesc') || 'Unable to load article data. Please try again.'}
          action={{
            label: t('common.backToList'),
            onClick: () => navigate('/worklist'),
          }}
          secondaryAction={{
            label: t('common.retry'),
            onClick: () => window.location.reload(),
          }}
          size="lg"
        />
      </div>
    );
  }

  // Check if worklist item has article_id
  if (!worklistItem.article_id) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <EmptyState
          icon="document"
          title={t('proofreading.messages.noArticleLinked')}
          description={t('proofreading.messages.noArticleLinkedDesc') || 'This worklist item is not linked to an article.'}
          action={{
            label: t('common.backToList'),
            onClick: () => navigate('/worklist'),
          }}
          size="lg"
        />
      </div>
    );
  }

  if (issues.length === 0) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <EmptyState
          icon={<CheckCircle className="h-20 w-20 text-green-500" />}
          title={t('proofreading.messages.noIssuesFound')}
          description={t('proofreading.messages.noIssuesFoundDesc') || 'Great job! This article has no proofreading issues.'}
          action={{
            label: t('common.backToList'),
            onClick: () => navigate('/worklist'),
          }}
          size="lg"
        />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      {/* Header with action buttons */}
      <ProofreadingReviewHeader
        worklistItem={worklistItem}
        onBack={() => navigate('/worklist')}
        onCancel={handleCancel}
        dirtyCount={dirtyCount}
        totalIssues={issues.length}
        allIssuesDecided={allIssuesDecided}
        isSaving={saveDecisionsMutation.isPending}
        onSaveDraft={() => saveDecisionsMutation.mutate(undefined)}
        onCompleteReview={() => saveDecisionsMutation.mutate('ready_to_publish')}
      />

      {/* Stats Bar */}
      <ReviewStatsBar
        stats={stats}
        dirtyCount={dirtyCount}
        totalIssues={issues.length}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      {/* Main Content - Responsive 3 Column Layout */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Mobile/Tablet Panel Toggle Buttons */}
        <div className="absolute top-2 left-2 z-20 flex gap-1 lg:hidden">
          <button
            onClick={() => setShowIssueList(!showIssueList)}
            className={`rounded-md p-2 shadow-md transition-colors ${
              showIssueList ? 'bg-blue-500 text-white' : 'bg-white text-gray-600 hover:bg-gray-100'
            }`}
            title={showIssueList ? 'Hide issue list' : 'Show issue list'}
          >
            <PanelLeftClose className="h-4 w-4" />
          </button>
        </div>
        <div className="absolute top-2 right-2 z-20 flex gap-1 lg:hidden">
          <button
            onClick={() => setShowIssueDetail(!showIssueDetail)}
            className={`rounded-md p-2 shadow-md transition-colors ${
              showIssueDetail ? 'bg-blue-500 text-white' : 'bg-white text-gray-600 hover:bg-gray-100'
            }`}
            title={showIssueDetail ? 'Hide detail panel' : 'Show detail panel'}
          >
            <PanelRightClose className="h-4 w-4" />
          </button>
        </div>

        {/* Left: Issue List - Responsive width */}
        <div
          className={`
            overflow-y-auto border-r border-gray-200 bg-white transition-all duration-300
            ${showIssueList ? 'w-full sm:w-1/3 lg:w-1/5' : 'w-0 overflow-hidden'}
            ${!showIssueList && 'border-r-0'}
            lg:w-1/5 lg:block
          `}
        >
          <ProofreadingIssueList
            issues={issues}
            decisions={decisions}
            selectedIssue={selectedIssue}
            selectedIssueIds={selectedIssueIds}
            onSelectIssue={(issue) => {
              setSelectedIssue(issue);
              // On mobile, auto-hide list and show detail when selecting
              if (window.innerWidth < 1024) {
                setShowIssueList(false);
                setShowIssueDetail(true);
              }
            }}
            onToggleSelect={(issueId) => {
              setSelectedIssueIds((prev) => {
                const next = new Set(prev);
                if (next.has(issueId)) {
                  next.delete(issueId);
                } else {
                  next.add(issueId);
                }
                return next;
              });
            }}
            onBatchAccept={() =>
              batchDecision(Array.from(selectedIssueIds), 'accepted')
            }
            onBatchReject={() =>
              batchDecision(Array.from(selectedIssueIds), 'rejected')
            }
          />
        </div>

        {/* Center: Article Content - Flexible width */}
        <div
          className={`
            flex-1 overflow-y-auto bg-white p-4 sm:p-6 lg:p-8 transition-all duration-300
            ${!showIssueList && !showIssueDetail ? 'flex-1' : ''}
          `}
        >
          <ProofreadingArticleContent
            content={worklistItem.content}
            title={worklistItem.title}
            issues={issues}
            decisions={decisions}
            selectedIssue={selectedIssue}
            viewMode={viewMode}
            onIssueClick={setSelectedIssue}
            suggestedContent={suggestedContent}
          />
        </div>

        {/* Right: Issue Detail Panel - Responsive width */}
        <div
          className={`
            overflow-y-auto border-l-2 border-blue-100 bg-white shadow-lg transition-all duration-300
            ${showIssueDetail ? 'w-full sm:w-1/2 lg:w-[30%]' : 'w-0 overflow-hidden'}
            ${!showIssueDetail && 'border-l-0'}
            lg:w-[30%] lg:block
            fixed lg:relative inset-y-0 right-0 z-10 lg:z-auto
            ${showIssueDetail ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
          `}
        >
          <ProofreadingIssueDetailPanel
            issue={selectedIssue}
            decision={selectedIssue ? decisions[selectedIssue.id] : undefined}
            onDecision={addDecision}
            onClearDecision={clearDecision}
            existingDecisions={[]}
            issueIndex={selectedIssue ? issues.findIndex(i => i.id === selectedIssue.id) + 1 : undefined}
            totalIssues={issues.length}
          />
        </div>

        {/* Mobile overlay when detail panel is open */}
        {showIssueDetail && (
          <div
            className="fixed inset-0 bg-black/20 z-[5] lg:hidden"
            onClick={() => setShowIssueDetail(false)}
          />
        )}
      </div>

      {/* Footer with Review Notes and Keyboard Shortcuts */}
      <div className="border-t border-gray-200 bg-white px-4 sm:px-6 py-3">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
          {/* Review Notes - responsive */}
          <div className="flex items-center gap-2 flex-1 w-full sm:w-auto">
            <label htmlFor="review-notes" className="text-xs font-medium text-gray-700 whitespace-nowrap hidden sm:inline">
              {t('proofreading.reviewNotes.label')}
            </label>
            <textarea
              id="review-notes"
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              className="flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              rows={1}
              placeholder={t('proofreading.reviewNotes.placeholder')}
            />
          </div>

          {/* Status and Shortcuts - responsive */}
          <div className="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-end">
            {/* Keyboard shortcuts - hidden on mobile */}
            <div className="hidden md:block">
              <KeyboardShortcutsHint
                shortcuts={PROOFREADING_SHORTCUTS_COMPACT}
                mode="inline"
              />
            </div>

            {/* Status display */}
            <span className="text-xs text-gray-500 whitespace-nowrap">
              {dirtyCount} / {issues.length} {t('proofreading.labels.issuesDecided')}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
