/**
 * Proofreading Article Content
 * Center panel displaying article with highlighted issues.
 */

import { useMemo, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ProofreadingIssue, DecisionPayload } from '@/types/worklist';
import { cn } from '@/lib/cn';
import { sanitizeHtmlContent } from '@/lib/sanitizeHtml';
import { DiffView } from './DiffView';

type ViewMode = 'original' | 'preview' | 'diff' | 'rendered';

/**
 * Strip HTML tags from text for plain text display
 * This prevents HTML tags from showing as raw text in the article view
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
      convertToText: false,
    });
    // Strip HTML tags to get plain text for display
    return stripHtmlTags(sanitized);
  }, [content]);

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
  // Render content with issue highlights using text search (not position-based)
  // FIX: Use text search because positions are based on HTML content, not plain text
  const renderedContent = useMemo(() => {
    if (!cleanContent || issues.length === 0) {
      return <p className="whitespace-pre-wrap text-gray-700">{cleanContent}</p>;
    }

    // Build a list of text ranges to highlight
    // We'll find each issue's original_text within the plain text article content
    interface HighlightRange {
      start: number;
      end: number;
      issue: ProofreadingIssue;
    }

    const ranges: HighlightRange[] = [];
    let searchStartIndex = 0;

    // Find each issue's text within the article content
    issues.forEach((issue) => {
      const originalText = stripHtmlTags(issue.original_text);
      if (!originalText) return;

      // Search for the original text starting from the last found position
      let foundIndex = cleanContent.indexOf(originalText, searchStartIndex);

      // If not found from current position, try from beginning (for out-of-order issues)
      if (foundIndex === -1) {
        foundIndex = cleanContent.indexOf(originalText);
      }

      if (foundIndex !== -1) {
        ranges.push({
          start: foundIndex,
          end: foundIndex + originalText.length,
          issue,
        });
        searchStartIndex = foundIndex + originalText.length;
      }
    });

    // Sort ranges by start position
    ranges.sort((a, b) => a.start - b.start);

    // Remove overlapping ranges (keep the first one)
    const nonOverlappingRanges: HighlightRange[] = [];
    let lastEnd = 0;
    ranges.forEach((range) => {
      if (range.start >= lastEnd) {
        nonOverlappingRanges.push(range);
        lastEnd = range.end;
      }
    });

    // Build the rendered content with highlights
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    nonOverlappingRanges.forEach((range, idx) => {
      const { start, end, issue } = range;
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
      const strippedSuggested = stripHtmlTags(issue.suggested_text);
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
  if (viewMode === 'diff' && suggestedContent) {
    return <DiffView original={cleanContent} suggested={suggestedContent} title={title} />;
  }

  // If in rendered mode, show Markdown-rendered content
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

  // For original and preview modes, show renderedContent with issue highlights
  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-8 text-3xl font-bold text-gray-900">{title}</h1>
      <div className="prose prose-lg max-w-none">{renderedContent}</div>
    </div>
  );
}
