/**
 * Proofreading Issue Detail Panel
 * Right sidebar showing issue details and decision actions.
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ProofreadingIssue, DecisionPayload, FeedbackCategory } from '@/types/worklist';
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
} from 'lucide-react';
import { cn } from '@/lib/cn';

interface ProofreadingIssueDetailPanelProps {
  issue: ProofreadingIssue | null;
  decision?: DecisionPayload;
  onDecision: (issueId: string, decision: Partial<DecisionPayload>) => void;
  onClearDecision: (issueId: string) => void;
}

export function ProofreadingIssueDetailPanel({
  issue,
  decision,
  onDecision,
  onClearDecision,
}: ProofreadingIssueDetailPanelProps) {
  const { t } = useTranslation();
  const [modifiedContent, setModifiedContent] = useState('');
  const [rationale, setRationale] = useState('');
  const [feedbackNotes, setFeedbackNotes] = useState('');
  const [feedbackCategory, setFeedbackCategory] = useState<FeedbackCategory | ''>('');
  const [showFeedback, setShowFeedback] = useState(false);

  if (!issue) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center">
        <div>
          <Info className="mx-auto h-12 w-12 text-gray-300" />
          <p className="mt-4 text-sm text-gray-500">
            {t('proofreading.messages.selectIssue')}
          </p>
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
      {/* Issue Header */}
      <div className="border-b border-gray-200 p-6">
        <div className="mb-3 flex items-center gap-2">
          {/* Severity Icon */}
          {issue.severity === 'critical' && (
            <AlertCircle className="h-5 w-5 text-red-500" />
          )}
          {issue.severity === 'warning' && (
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
          )}
          {issue.severity === 'info' && <Info className="h-5 w-5 text-blue-500" />}

          <span className="text-sm font-medium text-gray-700">{issue.rule_category}</span>

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
      <div className="border-b border-gray-200 p-6">
        <div className="mb-4">
          <div className="mb-1 text-xs font-medium text-gray-500">Original</div>
          <div className="rounded-md bg-red-50 p-3 text-sm text-gray-900">
            {issue.original_text}
          </div>
        </div>

        <div>
          <div className="mb-1 text-xs font-medium text-gray-500">Suggested</div>
          <div className="rounded-md bg-green-50 p-3 text-sm text-gray-900">
            {issue.suggested_text}
          </div>
        </div>
      </div>

      {/* Explanation */}
      <div className="border-b border-gray-200 p-6">
        <div className="mb-1 text-xs font-medium text-gray-700">Explanation</div>
        <p className="text-sm text-gray-600">{issue.explanation}</p>
        {issue.explanation_detail && (
          <p className="mt-2 text-xs text-gray-500">{issue.explanation_detail}</p>
        )}
      </div>

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
      <div className="border-t border-gray-200 bg-gray-50 p-4">
        <div className="text-xs text-gray-500">
          <div className="font-medium">Keyboard Shortcuts:</div>
          <div className="mt-1 space-y-0.5">
            <div>A - Accept</div>
            <div>R - Reject</div>
            <div>↑/↓ - Navigate</div>
          </div>
        </div>
      </div>
    </div>
  );
}
