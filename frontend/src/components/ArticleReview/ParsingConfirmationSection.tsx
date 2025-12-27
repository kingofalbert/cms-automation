/**
 * ParsingConfirmationSection - Displays parsed field confirmation details
 *
 * Phase 16: Enhanced Publish Preview
 * - Shows title breakdown: prefix | main title | suffix
 * - Shows SEO title with character count
 * - Shows author parsing details
 * - Shows parsing confirmation status
 *
 * Layout:
 * ┌─────────────────────────────────────────────────────────────┐
 * │ 📝 標題解析確認                                             │
 * ├─────────────────────────────────────────────────────────────┤
 * │ 前綴: [空]                                                  │
 * │ 主標題: 收藏10種「天然補血食物」                            │
 * │ 副標題: 附5道懶人食譜吃出紅潤好氣色                         │
 * │ SEO標題: 收藏10種天然補血食物｜氣血食療  [28/30字] ✅       │
 * ├─────────────────────────────────────────────────────────────┤
 * │ 👤 作者解析: 張淑智 (原文: "文/張淑智")                     │
 * │ 📅 解析確認: ✅ 已確認 (2025-12-24 16:20)                   │
 * └─────────────────────────────────────────────────────────────┘
 */

import React from 'react';
import { FileText, User, Check, AlertCircle, Clock } from 'lucide-react';

export interface ParsingConfirmationSectionProps {
  /** Main article title */
  title: string;
  /** Title prefix (e.g., category marker) */
  titlePrefix?: string | null;
  /** Title suffix (e.g., subtitle) */
  titleSuffix?: string | null;
  /** SEO title (30 chars optimized) */
  seoTitle?: string | null;
  /** Parsed author name */
  authorName?: string | null;
  /** Original author line text */
  authorLine?: string | null;
  /** Whether parsing has been confirmed */
  parsingConfirmed?: boolean;
  /** When parsing was confirmed (ISO date string) */
  parsingConfirmedAt?: string | null;
}

/**
 * ParsingConfirmationSection Component
 *
 * Displays the parsed field breakdown for verification.
 */
export const ParsingConfirmationSection: React.FC<ParsingConfirmationSectionProps> = ({
  title,
  titlePrefix,
  titleSuffix,
  seoTitle,
  authorName,
  authorLine,
  parsingConfirmed = false,
  parsingConfirmedAt,
}) => {
  // SEO title character count (optimal: 25-30 chars)
  const seoTitleLength = seoTitle?.length || 0;
  const isSeoTitleOptimal = seoTitleLength >= 25 && seoTitleLength <= 30;
  const isSeoTitleTooLong = seoTitleLength > 30;

  // Format confirmation date
  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return null;
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="p-4 bg-white border border-gray-200 rounded-lg">
      <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
        <FileText className="w-4 h-4 text-indigo-600" />
        解析欄位確認
      </h4>

      <div className="space-y-3">
        {/* Title Breakdown */}
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="text-xs text-gray-500 mb-2 font-medium">標題解析</div>
          <div className="space-y-2">
            {/* Prefix */}
            <div className="flex items-start gap-2 text-sm">
              <span className="text-gray-500 w-16 shrink-0">前綴:</span>
              {titlePrefix ? (
                <span className="text-gray-900 bg-purple-100 px-2 py-0.5 rounded">
                  {titlePrefix}
                </span>
              ) : (
                <span className="text-gray-400 italic">無</span>
              )}
            </div>

            {/* Main Title */}
            <div className="flex items-start gap-2 text-sm">
              <span className="text-gray-500 w-16 shrink-0">主標題:</span>
              <span className="text-gray-900 font-medium">{title || '(無標題)'}</span>
            </div>

            {/* Suffix */}
            <div className="flex items-start gap-2 text-sm">
              <span className="text-gray-500 w-16 shrink-0">副標題:</span>
              {titleSuffix ? (
                <span className="text-gray-900 bg-blue-100 px-2 py-0.5 rounded">
                  {titleSuffix}
                </span>
              ) : (
                <span className="text-gray-400 italic">無</span>
              )}
            </div>
          </div>
        </div>

        {/* SEO Title */}
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="text-xs text-gray-500 mb-2 font-medium">SEO 標題 (30字限制)</div>
          <div className="flex items-center gap-2">
            {seoTitle ? (
              <>
                <span className="text-sm text-gray-900">{seoTitle}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${
                  isSeoTitleOptimal
                    ? 'bg-green-100 text-green-700'
                    : isSeoTitleTooLong
                      ? 'bg-red-100 text-red-700'
                      : 'bg-amber-100 text-amber-700'
                }`}>
                  {seoTitleLength}/30
                  {isSeoTitleOptimal && <Check className="w-3 h-3 inline ml-1" />}
                  {isSeoTitleTooLong && <AlertCircle className="w-3 h-3 inline ml-1" />}
                </span>
              </>
            ) : (
              <span className="text-sm text-gray-400 italic">使用主標題</span>
            )}
          </div>
        </div>

        {/* Author Parsing */}
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="text-xs text-gray-500 mb-2 font-medium flex items-center gap-1">
            <User className="w-3 h-3" />
            作者解析
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-900 font-medium">
              {authorName || '(未識別)'}
            </span>
            {authorLine && authorLine !== authorName && (
              <span className="text-gray-500 text-xs">
                (原文: "{authorLine}")
              </span>
            )}
          </div>
        </div>

        {/* Parsing Confirmation Status */}
        <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
          {parsingConfirmed ? (
            <>
              <Check className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-700 font-medium">解析已確認</span>
              {parsingConfirmedAt && (
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatDate(parsingConfirmedAt)}
                </span>
              )}
            </>
          ) : (
            <>
              <AlertCircle className="w-4 h-4 text-amber-500" />
              <span className="text-sm text-amber-600">解析待確認</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

ParsingConfirmationSection.displayName = 'ParsingConfirmationSection';
