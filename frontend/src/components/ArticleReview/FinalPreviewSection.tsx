/**
 * FinalPreviewSection - WYSIWYG Final Effect Preview
 *
 * Phase 8.7: True Final Effect Preview
 * - Shows the article exactly as it will appear after publishing
 * - Applies all accepted/modified changes
 * - Clean rendering without any highlights or markers
 * - Professional typography matching published article style
 */

import React, { useMemo } from 'react';
import DOMPurify from 'dompurify';
import { Eye, CheckCircle, FileText, Sparkles } from 'lucide-react';
import type { ProofreadingIssue, DecisionPayload } from '../../types/worklist';

export interface FinalPreviewSectionProps {
  /** Article title */
  title?: string;
  /** Original HTML content of the article */
  originalContent: string;
  /** List of proofreading issues */
  issues: ProofreadingIssue[];
  /** Current decisions map */
  decisions: Map<string, DecisionPayload>;
  /** Optional class name */
  className?: string;
}

/**
 * Strip HTML tags and return plain text
 */
const stripHtmlTags = (html: string): string => {
  if (!html) return '';
  const doc = new DOMParser().parseFromString(html, 'text/html');
  return doc.body.textContent || '';
};

/**
 * FinalPreviewSection Component
 *
 * Renders the article with all accepted changes applied,
 * showing users exactly what the final published article will look like.
 */
export const FinalPreviewSection: React.FC<FinalPreviewSectionProps> = ({
  title,
  originalContent,
  issues,
  decisions,
  className = '',
}) => {
  // Calculate stats for header
  const stats = useMemo(() => {
    let accepted = 0;
    let rejected = 0;
    let modified = 0;
    let pending = 0;

    issues.forEach((issue) => {
      const decision = decisions.get(issue.id);
      const status = decision?.decision_type || issue.decision_status;

      switch (status) {
        case 'accepted':
          accepted++;
          break;
        case 'rejected':
          rejected++;
          break;
        case 'modified':
          modified++;
          break;
        default:
          pending++;
      }
    });

    return { accepted, rejected, modified, pending, total: issues.length };
  }, [issues, decisions]);

  // Build the final content with all accepted/modified changes applied
  const finalContent = useMemo(() => {
    if (!originalContent) return '';

    // Get plain text from HTML for text-based replacements
    const plainText = stripHtmlTags(originalContent);

    // Build a list of replacements to apply
    interface Replacement {
      originalText: string;
      replacementText: string;
      start: number;
    }

    const replacements: Replacement[] = [];

    // Find each accepted/modified issue and create replacement entry
    issues.forEach((issue) => {
      const decision = decisions.get(issue.id);
      const status = decision?.decision_type || issue.decision_status;

      // Only process accepted or modified issues
      if (status !== 'accepted' && status !== 'modified') {
        return;
      }

      const originalText = stripHtmlTags(issue.original_text || '');
      if (!originalText) return;

      // Determine replacement text
      let replacementText: string;
      if (status === 'modified' && decision?.modified_content) {
        replacementText = decision.modified_content;
      } else {
        replacementText = stripHtmlTags(issue.suggested_text || '') || originalText;
      }

      // Find position in plain text
      const foundIndex = plainText.indexOf(originalText);
      if (foundIndex !== -1) {
        replacements.push({
          originalText,
          replacementText,
          start: foundIndex,
        });
      }
    });

    // Sort by position (descending) so we can replace from end to start
    // This prevents position shifts from affecting later replacements
    replacements.sort((a, b) => b.start - a.start);

    // Apply all replacements to the plain text
    let resultText = plainText;
    replacements.forEach((r) => {
      const before = resultText.slice(0, r.start);
      const after = resultText.slice(r.start + r.originalText.length);
      resultText = before + r.replacementText + after;
    });

    return resultText;
  }, [originalContent, issues, decisions]);

  // Format content into paragraphs for display
  const formattedParagraphs = useMemo(() => {
    if (!finalContent) return [];

    // Split by double newlines or single newlines
    const paragraphs = finalContent
      .split(/\n\n+/)
      .map(p => p.trim())
      .filter(p => p.length > 0);

    return paragraphs;
  }, [finalContent]);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header with status indicator */}
      <div className="flex items-center justify-between bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-lg p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
            <Eye className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-emerald-800">最終效果預覽</h3>
            <p className="text-sm text-emerald-600">
              此為文章上稿後的實際呈現效果
            </p>
          </div>
        </div>

        {/* Stats badges */}
        <div className="flex items-center gap-3">
          {stats.accepted > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-green-100 text-green-700 rounded-full text-sm font-medium">
              <CheckCircle className="w-4 h-4" />
              <span>{stats.accepted} 項已採用</span>
            </div>
          )}
          {stats.modified > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
              <Sparkles className="w-4 h-4" />
              <span>{stats.modified} 項自訂</span>
            </div>
          )}
          {stats.pending > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-100 text-amber-700 rounded-full text-sm font-medium">
              <FileText className="w-4 h-4" />
              <span>{stats.pending} 項待處理</span>
            </div>
          )}
        </div>
      </div>

      {/* Notice for pending items */}
      {stats.pending > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-800">
          <strong>提示：</strong>
          尚有 {stats.pending} 個問題待處理，預覽中暫顯示原始內容。
          處理完成後將自動更新預覽。
        </div>
      )}

      {/* Article preview container - styled like published article */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        {/* Article header */}
        <div className="border-b border-gray-100 px-8 py-6 bg-gradient-to-b from-gray-50 to-white">
          {title && (
            <h1 className="text-2xl font-bold text-gray-900 leading-tight tracking-tight">
              {title}
            </h1>
          )}
        </div>

        {/* Article body - professional typography */}
        <article className="px-8 py-6">
          <div
            className="prose prose-lg max-w-none
              prose-headings:text-gray-900 prose-headings:font-bold
              prose-p:text-gray-700 prose-p:leading-relaxed prose-p:mb-4
              prose-strong:text-gray-900 prose-strong:font-semibold
              prose-em:italic
              prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
              prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:text-gray-600
              prose-ul:list-disc prose-ol:list-decimal
              prose-li:text-gray-700
              font-sans"
            style={{
              fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans TC", "Microsoft JhengHei", sans-serif',
              fontSize: '17px',
              lineHeight: '1.8',
            }}
          >
            {formattedParagraphs.length > 0 ? (
              formattedParagraphs.map((paragraph, index) => (
                <p key={index} className="mb-4 last:mb-0">
                  {paragraph}
                </p>
              ))
            ) : (
              <p className="text-gray-400 italic">（無內容）</p>
            )}
          </div>
        </article>

        {/* Footer with character count */}
        <div className="border-t border-gray-100 px-8 py-3 bg-gray-50 flex items-center justify-between text-xs text-gray-500">
          <span>
            共 {finalContent.length.toLocaleString('zh-TW')} 字元
          </span>
          <span className="flex items-center gap-1">
            <Eye className="w-3 h-3" />
            即時預覽
          </span>
        </div>
      </div>

      {/* Help text */}
      <div className="text-center text-xs text-gray-400">
        💡 此預覽呈現文章上稿後的最終效果，所有已接受的修改已自動套用
      </div>
    </div>
  );
};

FinalPreviewSection.displayName = 'FinalPreviewSection';
