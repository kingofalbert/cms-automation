/**
 * Proofreading Review Page
 * Human review interface for AI-generated proofreading suggestions.
 */

import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { worklistAPI } from '@/services/worklist';
import {
  ProofreadingIssue,
  DecisionPayload,
  DecisionType,
  WorklistItemDetail,
} from '@/types/worklist';
import { ProofreadingIssueList } from '@/components/ProofreadingReview/ProofreadingIssueList';
import { ProofreadingArticleContent } from '@/components/ProofreadingReview/ProofreadingArticleContent';
import { ProofreadingIssueDetailPanel } from '@/components/ProofreadingReview/ProofreadingIssueDetailPanel';
import { ReviewStatsBar } from '@/components/ProofreadingReview/ReviewStatsBar';
import { ProofreadingReviewHeader } from '@/components/ProofreadingReview/ProofreadingReviewHeader';
import { Button } from '@/components/ui';
import { ArrowLeft, CheckCircle } from 'lucide-react';

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
  const issues = (worklistItem?.proofreading_issues || []) as unknown as ProofreadingIssue[];
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
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-lg text-gray-500">{t('common.loading')}</div>
      </div>
    );
  }

  if (error || !worklistItem) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-red-500">{t('proofreading.messages.loadFailed')}</p>
          <Button className="mt-4" onClick={() => navigate('/worklist')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            {t('common.backToList')}
          </Button>
        </div>
      </div>
    );
  }

  // Check if worklist item has article_id
  if (!worklistItem.article_id) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-red-500">
            {t('proofreading.messages.noArticleLinked')}
          </p>
          <Button className="mt-4" onClick={() => navigate('/worklist')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            {t('common.backToList')}
          </Button>
        </div>
      </div>
    );
  }

  if (issues.length === 0) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
          <p className="mt-4 text-lg text-gray-700">
            {t('proofreading.messages.noIssuesFound')}
          </p>
          <Button className="mt-4" onClick={() => navigate('/worklist')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            {t('common.backToList')}
          </Button>
        </div>
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

      {/* Main Content - 3 Column Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Issue List (20%) */}
        <div className="w-1/5 overflow-y-auto border-r border-gray-200 bg-white">
          <ProofreadingIssueList
            issues={issues}
            decisions={decisions}
            selectedIssue={selectedIssue}
            selectedIssueIds={selectedIssueIds}
            onSelectIssue={setSelectedIssue}
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

        {/* Center: Article Content (50%) */}
        <div className="flex-1 overflow-y-auto bg-white p-8">
          <ProofreadingArticleContent
            content={worklistItem.content}
            title={worklistItem.title}
            issues={issues}
            decisions={decisions}
            selectedIssue={selectedIssue}
            viewMode={viewMode}
            onIssueClick={setSelectedIssue}
            suggestedContent={undefined}
          />
        </div>

        {/* Right: Issue Detail Panel (30%) */}
        <div className="w-[30%] overflow-y-auto border-l-2 border-blue-100 bg-white shadow-lg">
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
      </div>

      {/* Simplified Footer - Review Notes only */}
      <div className="border-t border-gray-200 bg-white px-6 py-3">
        <div className="flex items-center gap-4">
          {/* Review Notes - compact inline */}
          <label htmlFor="review-notes" className="text-xs font-medium text-gray-700 whitespace-nowrap">
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

          {/* Status display */}
          <span className="text-xs text-gray-500 whitespace-nowrap">
            {dirtyCount} / {issues.length} {t('proofreading.labels.issuesDecided')}
          </span>
        </div>
      </div>
    </div>
  );
}
