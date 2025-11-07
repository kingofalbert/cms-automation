/**
 * Proofreading Article Content
 * Center panel displaying article with highlighted issues.
 */

import { useMemo } from 'react';
import { ProofreadingIssue, DecisionPayload } from '@/types/worklist';
import { cn } from '@/lib/cn';
import { DiffView } from './DiffView';

type ViewMode = 'original' | 'preview' | 'diff';

interface ProofreadingArticleContentProps {
  content: string;
  title: string;
  issues: ProofreadingIssue[];
  decisions: Record<string, DecisionPayload>;
  selectedIssue: ProofreadingIssue | null;
  viewMode: ViewMode;
  onIssueClick: (issue: ProofreadingIssue) => void;
  suggestedContent?: string | null;
}

export function ProofreadingArticleContent({
  content,
  title,
  issues,
  decisions,
  selectedIssue,
  viewMode,
  onIssueClick,
  suggestedContent,
}: ProofreadingArticleContentProps) {
  // If in diff mode and we have suggested content, show diff view
  if (viewMode === 'diff' && suggestedContent) {
    return <DiffView original={content} suggested={suggestedContent} title={title} />;
  }
  // Render content with issue highlights
  const renderedContent = useMemo(() => {
    if (!content || issues.length === 0) {
      return <p className="whitespace-pre-wrap text-gray-700">{content}</p>;
    }

    // Sort issues defensively to avoid undefined position errors
    const sortedIssues = [...issues].sort((a, b) => {
      const startA =
        typeof a?.position?.start === 'number' ? a.position.start : Number.MAX_SAFE_INTEGER;
      const startB =
        typeof b?.position?.start === 'number' ? b.position.start : Number.MAX_SAFE_INTEGER;
      return startA - startB;
    });

    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    sortedIssues.forEach((issue, idx) => {
      const rawStart = typeof issue.position?.start === 'number' ? issue.position.start : 0;
      const rawEnd =
        typeof issue.position?.end === 'number' && issue.position.end >= rawStart
          ? issue.position.end
          : rawStart;

      const start = Math.max(0, Math.min(content.length, rawStart));
      const end = Math.max(start, Math.min(content.length, rawEnd));

      const decision = decisions[issue.id];
      const decisionStatus = decision?.decision_type || issue.decision_status;

      if (start > lastIndex) {
        parts.push(
          <span key={`text-${idx}`} className="whitespace-pre-wrap">
            {content.slice(lastIndex, start)}
          </span>
        );
      }

      const issueText =
        end > start ? content.slice(start, end) : issue.original_text || issue.suggested_text || '';
      const isSelected = selectedIssue?.id === issue.id;

      parts.push(
        <span
          key={`issue-${issue.id}`}
          data-issue-id={issue.id}
          className={cn(
            'cursor-pointer rounded px-1 transition-all',
            isSelected && 'ring-2 ring-blue-500 ring-offset-2',
            issue.severity === 'critical' && 'bg-red-100 hover:bg-red-200',
            issue.severity === 'warning' && 'bg-yellow-100 hover:bg-yellow-200',
            issue.severity === 'info' && 'bg-blue-100 hover:bg-blue-200',
            decisionStatus === 'accepted' && 'bg-green-100',
            decisionStatus === 'rejected' && 'bg-gray-200 opacity-50 line-through',
            decisionStatus === 'modified' && 'bg-purple-100'
          )}
          onClick={() => onIssueClick(issue)}
          title={issue.explanation}
        >
          {viewMode === 'preview' && decisionStatus === 'accepted'
            ? issue.suggested_text || issueText
            : viewMode === 'preview' && decision?.modified_content
            ? decision.modified_content
            : issueText}
        </span>
      );

      lastIndex = end;
    });

    if (lastIndex < content.length) {
      parts.push(
        <span key="text-end" className="whitespace-pre-wrap">
          {content.slice(lastIndex)}
        </span>
      );
    }

    return <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">{parts}</div>;
  }, [content, issues, decisions, selectedIssue, viewMode, onIssueClick]);

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-8 text-3xl font-bold text-gray-900">{title}</h1>
      <div className="prose prose-lg max-w-none">{renderedContent}</div>
    </div>
  );
}
