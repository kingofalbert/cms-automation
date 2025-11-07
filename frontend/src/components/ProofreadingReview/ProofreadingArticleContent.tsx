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

    // Sort issues by position
    const sortedIssues = [...issues].sort((a, b) => a.position.start - b.position.start);

    // Build highlighted content
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    sortedIssues.forEach((issue, idx) => {
      const { start, end } = issue.position;
      const decision = decisions[issue.id];
      const decisionStatus = decision?.decision_type || issue.decision_status;

      // Add text before issue
      if (start > lastIndex) {
        parts.push(
          <span key={`text-${idx}`} className="whitespace-pre-wrap">
            {content.slice(lastIndex, start)}
          </span>
        );
      }

      // Add highlighted issue
      const issueText = content.slice(start, end);
      const isSelected = selectedIssue?.id === issue.id;

      parts.push(
        <span
          key={`issue-${issue.id}`}
          data-issue-id={issue.id}
          className={cn(
            'cursor-pointer rounded px-1 transition-all',
            isSelected && 'ring-2 ring-blue-500 ring-offset-2',
            // Severity colors
            issue.severity === 'critical' && 'bg-red-100 hover:bg-red-200',
            issue.severity === 'warning' && 'bg-yellow-100 hover:bg-yellow-200',
            issue.severity === 'info' && 'bg-blue-100 hover:bg-blue-200',
            // Decision overlay
            decisionStatus === 'accepted' && 'bg-green-100',
            decisionStatus === 'rejected' && 'bg-gray-200 opacity-50 line-through',
            decisionStatus === 'modified' && 'bg-purple-100'
          )}
          onClick={() => onIssueClick(issue)}
          title={issue.explanation}
        >
          {viewMode === 'preview' && decisionStatus === 'accepted'
            ? issue.suggested_text
            : viewMode === 'preview' && decision?.modified_content
            ? decision.modified_content
            : issueText}
        </span>
      );

      lastIndex = end;
    });

    // Add remaining text
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
