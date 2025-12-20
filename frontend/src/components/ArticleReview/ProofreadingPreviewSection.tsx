/**
 * ProofreadingPreviewSection - Real-time preview of proofread content
 *
 * Phase 8.4: Real-time Preview Mode
 * - Shows the final content after applying AI proofreading suggestions
 * - Supports two view modes:
 *   1. Rendered HTML (default): Clean WYSIWYG preview for checking final layout
 *   2. Text with Highlights: Shows word-level changes with color coding
 *
 * Layout:
 * ┌─────────────────────────────────────────────┐
 * │ Preview Header (stats + view options)       │
 * ├─────────────────────────────────────────────┤
 * │ Content Preview                             │
 * │ • Rendered mode: Clean HTML preview         │
 * │ • Highlight mode: Word-level change marks   │
 * └─────────────────────────────────────────────┘
 */

import React, { useState, useMemo } from 'react';
import DOMPurify from 'dompurify';
import { Eye, Type, Highlighter, FileText, Check, X, Edit3, Code, Monitor } from 'lucide-react';
import type { DiffStats } from './DiffViewSection';

export interface ProofreadingPreviewSectionProps {
  /** Original content */
  originalContent: string;
  /** Proofread content */
  proofreadContent: string;
  /** Pre-calculated diff statistics from backend (optional) */
  diffStats?: DiffStats;
  /** Word-level changes from backend (optional) */
  wordChanges?: WordChange[];
}

export interface WordChange {
  type: 'replace' | 'delete' | 'insert';
  original?: string;
  suggested?: string;
  original_pos?: [number, number];
  suggested_pos?: [number, number];
}

/**
 * ProofreadingPreviewSection Component
 *
 * Provides a clean preview of the proofread content with optional change highlighting.
 */
export const ProofreadingPreviewSection: React.FC<ProofreadingPreviewSectionProps> = ({
  originalContent,
  proofreadContent,
  diffStats,
  wordChanges = [],
}) => {
  // View mode: 'rendered' for clean HTML preview, 'text' for highlighted text
  const [viewMode, setViewMode] = useState<'rendered' | 'text'>('rendered');
  const [showHighlights, setShowHighlights] = useState(true);
  const [showOriginalInline, setShowOriginalInline] = useState(false);

  // Sanitize HTML for safe rendering
  const sanitizedHtml = useMemo(() => {
    return DOMPurify.sanitize(proofreadContent, {
      ALLOWED_TAGS: ['p', 'br', 'b', 'strong', 'i', 'em', 'u', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'blockquote', 'pre', 'code', 'img', 'figure', 'figcaption', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'sub', 'sup', 'mark', 'small', 'del', 'ins'],
      ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'style', 'target', 'rel', 'id', 'width', 'height'],
    });
  }, [proofreadContent]);

  // Strip HTML tags to get plain text (for text view mode)
  const plainTextContent = useMemo(() => {
    const doc = new DOMParser().parseFromString(proofreadContent, 'text/html');
    return doc.body.textContent || '';
  }, [proofreadContent]);

  // Calculate whether there are changes
  const hasChanges = useMemo(() => {
    return originalContent !== proofreadContent;
  }, [originalContent, proofreadContent]);

  // Generate highlighted content with word-level changes
  const highlightedContent = useMemo(() => {
    if (!showHighlights || !hasChanges || wordChanges.length === 0) {
      return proofreadContent;
    }

    // Create a map of positions to highlight in the suggested content
    const highlights: Array<{
      start: number;
      end: number;
      type: 'insert' | 'replace';
      original?: string;
    }> = [];

    // Tokenize the suggested content the same way as backend
    const tokenize = (text: string): string[] => {
      return text.match(/[\u4e00-\u9fff]+|[a-zA-Z0-9]+|[^\s\w]|\s+/g) || [];
    };

    const suggestedTokens = tokenize(proofreadContent);

    // Calculate character positions from token positions
    let charPos = 0;
    const tokenStartPositions: number[] = [];
    suggestedTokens.forEach((token) => {
      tokenStartPositions.push(charPos);
      charPos += token.length;
    });
    tokenStartPositions.push(charPos); // End position

    // Map word changes to character positions
    wordChanges.forEach((change) => {
      if (change.type === 'insert' && change.suggested_pos) {
        const [start, end] = change.suggested_pos;
        if (start < tokenStartPositions.length && end <= tokenStartPositions.length) {
          highlights.push({
            start: tokenStartPositions[start],
            end: tokenStartPositions[end],
            type: 'insert',
          });
        }
      } else if (change.type === 'replace' && change.suggested_pos) {
        const [start, end] = change.suggested_pos;
        if (start < tokenStartPositions.length && end <= tokenStartPositions.length) {
          highlights.push({
            start: tokenStartPositions[start],
            end: tokenStartPositions[end],
            type: 'replace',
            original: change.original,
          });
        }
      }
    });

    return highlights;
  }, [showHighlights, hasChanges, wordChanges, proofreadContent]);

  // Render content with highlights (for text view mode)
  const renderHighlightedContent = () => {
    // Use plain text content for highlighting
    const textContent = plainTextContent;

    if (!showHighlights || !hasChanges || typeof highlightedContent === 'string') {
      // No highlights - just render the plain text content
      return (
        <div className="whitespace-pre-wrap break-words leading-relaxed text-gray-800">
          {textContent}
        </div>
      );
    }

    // Sort highlights by start position
    const sortedHighlights = [...highlightedContent].sort((a, b) => a.start - b.start);

    // Build highlighted content
    const elements: React.ReactNode[] = [];
    let lastEnd = 0;

    sortedHighlights.forEach((highlight, index) => {
      // Add text before this highlight
      if (highlight.start > lastEnd) {
        elements.push(
          <span key={`text-${index}`}>
            {textContent.slice(lastEnd, highlight.start)}
          </span>
        );
      }

      // Add highlighted text
      const highlightedText = textContent.slice(highlight.start, highlight.end);
      if (highlight.type === 'insert') {
        elements.push(
          <span
            key={`highlight-${index}`}
            className="bg-green-100 text-green-800 px-0.5 rounded border-b-2 border-green-400"
            title="新增内容"
          >
            {highlightedText}
          </span>
        );
      } else if (highlight.type === 'replace') {
        elements.push(
          <span key={`highlight-${index}`} className="relative group">
            {showOriginalInline && highlight.original && (
              <span className="bg-red-100 text-red-600 line-through px-0.5 mr-1 text-sm opacity-70">
                {highlight.original}
              </span>
            )}
            <span
              className="bg-amber-100 text-amber-800 px-0.5 rounded border-b-2 border-amber-400"
              title={highlight.original ? `原文: ${highlight.original}` : '修改内容'}
            >
              {highlightedText}
            </span>
          </span>
        );
      }

      lastEnd = highlight.end;
    });

    // Add remaining text
    if (lastEnd < textContent.length) {
      elements.push(
        <span key="text-final">{textContent.slice(lastEnd)}</span>
      );
    }

    return (
      <div className="whitespace-pre-wrap break-words leading-relaxed text-gray-800">
        {elements.length > 0 ? elements : textContent}
      </div>
    );
  };

  // Render HTML content (for rendered view mode)
  const renderHtmlContent = () => {
    return (
      <div
        className="prose prose-sm max-w-none text-gray-800 leading-relaxed
          prose-headings:text-gray-900 prose-headings:font-semibold
          prose-p:my-2 prose-p:leading-relaxed
          prose-ul:my-2 prose-ol:my-2
          prose-li:my-0.5
          prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
          prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:pl-4 prose-blockquote:italic
          prose-img:rounded-lg prose-img:my-4"
        dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
      />
    );
  };

  // Calculate change summary
  const changeSummary = useMemo(() => {
    if (!hasChanges) {
      return { inserts: 0, replaces: 0, deletes: 0 };
    }

    const inserts = wordChanges.filter((c) => c.type === 'insert').length;
    const replaces = wordChanges.filter((c) => c.type === 'replace').length;
    const deletes = wordChanges.filter((c) => c.type === 'delete').length;

    return { inserts, replaces, deletes };
  }, [hasChanges, wordChanges]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Eye className="w-5 h-5" />
          预览模式
        </h3>
        <div className="flex items-center gap-2">
          {/* View mode toggle: Rendered HTML vs Text with highlights */}
          <div className="flex items-center border border-gray-200 rounded-md overflow-hidden">
            <button
              type="button"
              onClick={() => setViewMode('rendered')}
              className={`px-3 py-1 text-xs flex items-center gap-1 transition-colors ${
                viewMode === 'rendered'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
              title="渲染模式：显示最终排版效果"
            >
              <Monitor className="w-3 h-3" />
              排版
            </button>
            <button
              type="button"
              onClick={() => setViewMode('text')}
              className={`px-3 py-1 text-xs flex items-center gap-1 transition-colors ${
                viewMode === 'text'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
              title="文本模式：显示修改高亮"
            >
              <Code className="w-3 h-3" />
              高亮
            </button>
          </div>
          {/* Highlight options (only in text mode) */}
          {viewMode === 'text' && (
            <>
              <button
                type="button"
                onClick={() => setShowHighlights(!showHighlights)}
                className={`px-3 py-1 text-xs rounded-md border flex items-center gap-1 transition-colors ${
                  showHighlights
                    ? 'bg-amber-50 border-amber-300 text-amber-700'
                    : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-50'
                }`}
                title={showHighlights ? '隐藏高亮' : '显示高亮'}
              >
                <Highlighter className="w-3 h-3" />
                高亮
              </button>
              {showHighlights && (
                <button
                  type="button"
                  onClick={() => setShowOriginalInline(!showOriginalInline)}
                  className={`px-3 py-1 text-xs rounded-md border flex items-center gap-1 transition-colors ${
                    showOriginalInline
                      ? 'bg-red-50 border-red-300 text-red-700'
                      : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-50'
                  }`}
                  title={showOriginalInline ? '隐藏原文' : '显示原文'}
                >
                  <Type className="w-3 h-3" />
                  原文
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* No changes message */}
      {!hasChanges && (
        <div className="p-6 bg-green-50 border border-green-200 rounded-lg text-center">
          <Check className="w-12 h-12 mx-auto text-green-600 mb-2" />
          <p className="text-sm font-medium text-green-800">内容无需修改</p>
          <p className="text-xs text-green-600 mt-1">AI 校对认为原文已经很好，无需调整</p>
        </div>
      )}

      {/* Preview content */}
      {hasChanges && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          {/* Mode indicator */}
          <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <span className="text-xs text-gray-500">
              {viewMode === 'rendered' ? (
                <>
                  <Monitor className="w-3 h-3 inline-block mr-1" />
                  排版预览 - 显示最终效果
                </>
              ) : (
                <>
                  <Code className="w-3 h-3 inline-block mr-1" />
                  文本预览 - 显示修改标记
                </>
              )}
            </span>
            <span className="text-xs text-gray-400">
              {proofreadContent.length.toLocaleString('zh-CN')} 字符
            </span>
          </div>
          {/* Content area */}
          <div className="p-6 bg-white min-h-[200px] max-h-[500px] overflow-y-auto">
            {viewMode === 'rendered' ? renderHtmlContent() : renderHighlightedContent()}
          </div>
        </div>
      )}

      {/* Legend and stats (only in text mode with highlights) */}
      {hasChanges && viewMode === 'text' && showHighlights && (
        <div className="flex flex-wrap items-center gap-4 text-xs text-gray-600">
          <span className="font-medium">图例:</span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-4 h-4 bg-green-100 border-b-2 border-green-400 rounded"></span>
            新增 ({changeSummary.inserts})
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-4 h-4 bg-amber-100 border-b-2 border-amber-400 rounded"></span>
            修改 ({changeSummary.replaces})
          </span>
          {changeSummary.deletes > 0 && (
            <span className="flex items-center gap-1">
              <span className="inline-block w-4 h-4 bg-red-100 border border-red-300 rounded line-through"></span>
              删除 ({changeSummary.deletes})
            </span>
          )}
        </div>
      )}

      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
        <div className="p-2 bg-gray-50 rounded-lg text-center">
          <div className="text-gray-500 mb-0.5 flex items-center justify-center gap-1">
            <FileText className="w-3 h-3" /> 字数
          </div>
          <div className="font-medium text-gray-900">
            {proofreadContent.length.toLocaleString('zh-CN')}
          </div>
          <div className="text-gray-400 text-[10px]">
            {proofreadContent.split('\n').length} 行
          </div>
        </div>
        <div className="p-2 bg-green-50 rounded-lg text-center">
          <div className="text-green-600 mb-0.5 flex items-center justify-center gap-1">
            <Check className="w-3 h-3" /> 新增
          </div>
          <div className="font-medium text-green-700">
            {diffStats?.additions ?? changeSummary.inserts}
          </div>
        </div>
        <div className="p-2 bg-amber-50 rounded-lg text-center">
          <div className="text-amber-600 mb-0.5 flex items-center justify-center gap-1">
            <Edit3 className="w-3 h-3" /> 修改
          </div>
          <div className="font-medium text-amber-700">
            {changeSummary.replaces}
          </div>
        </div>
        <div className="p-2 bg-red-50 rounded-lg text-center">
          <div className="text-red-600 mb-0.5 flex items-center justify-center gap-1">
            <X className="w-3 h-3" /> 删除
          </div>
          <div className="font-medium text-red-700">
            {diffStats?.deletions ?? changeSummary.deletes}
          </div>
        </div>
      </div>
    </div>
  );
};

ProofreadingPreviewSection.displayName = 'ProofreadingPreviewSection';
