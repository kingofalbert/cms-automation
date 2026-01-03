/**
 * Proofreading Article Content
 * Center panel displaying article with highlighted issues.
 *
 * Spec 014: Uses plain_text_position for accurate issue highlighting.
 */

import { useMemo, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ProofreadingIssue, DecisionPayload } from '@/types/worklist';
import { cn } from '@/lib/cn';
import { sanitizeHtmlContent } from '@/lib/sanitizeHtml';
import { DiffView } from './DiffView';
import {
  stripHtmlTags,
  resolveAllIssuePositions,
  removeOverlappingRanges,
} from '@/utils/proofreadingPosition';

type ViewMode = 'original' | 'preview' | 'diff' | 'rendered';

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
  const containerRef = useRef<HTMLDivElement>(null);

  // Sanitize content to remove CSS pollution from Google Docs
  // Then strip HTML tags to prevent them from showing as raw text
  const cleanContent = useMemo(() => {
    const sanitized = sanitizeHtmlContent(content, {
      removeStyles: true,
      removeScripts: true,
      removeCssText: true,
      convertToText: false,
    });
    // Strip HTML tags to get plain text for display
    return stripHtmlTags(sanitized);
  }, [content]);

  // Also sanitize suggestedContent if provided
  const cleanSuggestedContent = useMemo(() => {
    if (!suggestedContent) return null;
    const sanitized = sanitizeHtmlContent(suggestedContent, {
      removeStyles: true,
      removeScripts: true,
      removeCssText: true,
      convertToText: false,
    });
    // Strip HTML tags to get plain text for display
    return stripHtmlTags(sanitized);
  }, [suggestedContent]);

  // Generate preview content based on user decisions (accepted/rejected/modified)
  // This applies only the changes the user has decided on, not all AI suggestions
  const userDecisionPreviewContent = useMemo(() => {
    if (!cleanContent || issues.length === 0) {
      return cleanContent;
    }

    // Resolve all issue positions
    const resolvedPositions = resolveAllIssuePositions(issues, cleanContent);
    const nonOverlappingRanges = removeOverlappingRanges(resolvedPositions);

    // Build the preview content by applying user decisions
    let result = '';
    let lastIndex = 0;

    nonOverlappingRanges.forEach(({ issue, position }) => {
      const { start, end } = position;
      const decision = decisions[issue.id];
      const decisionStatus = decision?.decision_type || issue.decision_status;

      // Add text before this issue
      if (start > lastIndex) {
        result += cleanContent.slice(lastIndex, start);
      }

      // Get the text to use based on decision status
      const issueText = cleanContent.slice(start, end);
      const strippedSuggested = issue.suggested_text_plain || stripHtmlTags(issue.suggested_text);

      if (decisionStatus === 'accepted') {
        // Use the suggested text for accepted changes
        result += strippedSuggested || issueText;
      } else if (decisionStatus === 'modified' && decision?.modified_content) {
        // Use the user's custom modification
        result += decision.modified_content;
      } else {
        // Keep original text for rejected or pending issues
        result += issueText;
      }

      lastIndex = end;
    });

    // Add remaining text after last issue
    if (lastIndex < cleanContent.length) {
      result += cleanContent.slice(lastIndex);
    }

    return result;
  }, [cleanContent, issues, decisions]);

  // Count how many decisions have been made (including those loaded from backend)
  const decisionCount = useMemo(() => {
    // Count local decisions made in this session
    const localDecisionCount = Object.values(decisions).filter(d => d.decision_type).length;

    // Also count decisions stored in issues from backend (that aren't in local state)
    const backendDecisionCount = issues.filter(issue =>
      issue.decision_status &&
      issue.decision_status !== 'pending' &&
      !decisions[issue.id]
    ).length;

    return localDecisionCount + backendDecisionCount;
  }, [decisions, issues]);

  // Auto-scroll to selected issue when it changes
  useEffect(() => {
    if (!selectedIssue) return;

    // Small delay to ensure DOM is updated
    const timer = setTimeout(() => {
      const element = document.querySelector(`[data-issue-id="${selectedIssue.id}"]`);
      if (element) {
        element.scrollIntoView({
          behavior: 'smooth',
          block: 'center', // Center the element in the viewport
          inline: 'nearest'
        });
      }
    }, 100);

    return () => clearTimeout(timer);
  }, [selectedIssue]);

  // IMPORTANT: Calculate renderedContent BEFORE early returns to maintain hook order
  // Spec 014: Use plain_text_position for accurate highlighting with text search fallback
  const renderedContent = useMemo(() => {
    if (!cleanContent || issues.length === 0) {
      return <p className="whitespace-pre-wrap text-gray-700">{cleanContent}</p>;
    }

    // Spec 014: Resolve all issue positions using the new utility functions
    // This first tries plain_text_position, then falls back to text search
    const resolvedPositions = resolveAllIssuePositions(issues, cleanContent);
    const nonOverlappingRanges = removeOverlappingRanges(resolvedPositions);

    // Build the rendered content with highlights
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    nonOverlappingRanges.forEach(({ issue, position }, idx) => {
      const { start, end } = position;
      const decision = decisions[issue.id];
      const decisionStatus = decision?.decision_type || issue.decision_status;

      // Add text before this issue
      if (start > lastIndex) {
        parts.push(
          <span key={`text-${idx}`} className="whitespace-pre-wrap">
            {cleanContent.slice(lastIndex, start)}
          </span>
        );
      }

      // Get display text based on decision status
      const issueText = cleanContent.slice(start, end);
      // Spec 014: Prefer pre-computed plain text from backend
      const strippedSuggested = issue.suggested_text_plain || stripHtmlTags(issue.suggested_text);
      const isSelected = selectedIssue?.id === issue.id;

      parts.push(
        <span
          key={`issue-${issue.id}`}
          data-issue-id={issue.id}
          data-position-source={position.source}
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
            ? strippedSuggested || issueText
            : viewMode === 'preview' && decision?.modified_content
            ? decision.modified_content
            : issueText}
        </span>
      );

      lastIndex = end;
    });

    // Add remaining text after last issue
    if (lastIndex < cleanContent.length) {
      parts.push(
        <span key="text-end" className="whitespace-pre-wrap">
          {cleanContent.slice(lastIndex)}
        </span>
      );
    }

    return <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">{parts}</div>;
  }, [cleanContent, issues, decisions, selectedIssue, viewMode, onIssueClick]);

  // NOW that all hooks are called, we can conditionally render based on viewMode

  // If in diff mode and we have suggested content, show diff view
  // Use cleanSuggestedContent to remove CSS garbage from Google Docs
  if (viewMode === 'diff' && cleanSuggestedContent) {
    return <DiffView original={cleanContent} suggested={cleanSuggestedContent} title={title} />;
  }

  // If in rendered mode, show Markdown-rendered content (original)
  if (viewMode === 'rendered') {
    return (
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-8 text-3xl font-bold text-gray-900">{title}</h1>
        <div className="prose prose-lg max-w-none prose-headings:text-gray-900 prose-h1:text-3xl prose-h2:text-2xl prose-h3:text-xl prose-p:text-gray-700 prose-a:text-blue-600 prose-strong:text-gray-900 prose-ul:list-disc prose-ol:list-decimal">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              // Custom link renderer to open links in new tab
              a: ({ node, ...props }) => (
                <a {...props} target="_blank" rel="noopener noreferrer" />
              ),
              // Custom heading renderers to ensure proper styling
              h1: ({ node, ...props }) => (
                <h1 className="text-3xl font-bold mt-8 mb-4 text-gray-900" {...props} />
              ),
              h2: ({ node, ...props }) => (
                <h2 className="text-2xl font-bold mt-6 mb-3 text-gray-900" {...props} />
              ),
              h3: ({ node, ...props }) => (
                <h3 className="text-xl font-bold mt-4 mb-2 text-gray-900" {...props} />
              ),
            }}
          >
            {cleanContent}
          </ReactMarkdown>
        </div>
      </div>
    );
  }

  // If in preview mode, show formatted preview based on user decisions
  // This shows the article with accepted changes applied, rejected changes kept as original
  if (viewMode === 'preview') {
    const hasDecisions = decisionCount > 0;

    return (
      <div className="mx-auto max-w-4xl">
        {/* Preview mode header */}
        <div className="mb-6 flex items-center gap-3 rounded-lg bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 p-4">
          <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-emerald-800">最終效果預覽</h3>
            <p className="text-xs text-emerald-600">
              {hasDecisions
                ? `顯示套用您的 ${decisionCount} 個決定後的文章效果`
                : '尚未做出任何決定，顯示原始文章'}
            </p>
          </div>
        </div>

        <h1 className="mb-8 text-3xl font-bold text-gray-900">{title}</h1>
        <div className="prose prose-lg max-w-none prose-headings:text-gray-900 prose-h1:text-3xl prose-h2:text-2xl prose-h3:text-xl prose-h4:text-lg prose-p:text-gray-700 prose-a:text-blue-600 prose-strong:text-gray-900 prose-ul:list-disc prose-ol:list-decimal">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ node, ...props }) => (
                <a {...props} target="_blank" rel="noopener noreferrer" />
              ),
              h1: ({ node, ...props }) => (
                <h1 className="text-3xl font-bold mt-8 mb-4 text-gray-900" {...props} />
              ),
              h2: ({ node, ...props }) => (
                <h2 className="text-2xl font-bold mt-6 mb-3 text-gray-900" {...props} />
              ),
              h3: ({ node, ...props }) => (
                <h3 className="text-xl font-bold mt-4 mb-2 text-gray-900" {...props} />
              ),
              h4: ({ node, ...props }) => (
                <h4 className="text-lg font-semibold mt-4 mb-2 text-gray-800" {...props} />
              ),
              p: ({ node, ...props }) => (
                <p className="text-gray-700 leading-relaxed mb-4" {...props} />
              ),
              li: ({ node, ...props }) => (
                <li className="text-gray-700 ml-4" {...props} />
              ),
            }}
          >
            {userDecisionPreviewContent}
          </ReactMarkdown>
        </div>
      </div>
    );
  }

  // For original mode (and preview mode without suggestedContent), show renderedContent with issue highlights
  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-8 text-3xl font-bold text-gray-900">{title}</h1>
      <div className="prose prose-lg max-w-none">{renderedContent}</div>
    </div>
  );
}
