/**
 * GoogleSearchPreview - Simulates Google search result appearance
 *
 * Phase 16: Enhanced Publish Preview
 * - Shows how the article will appear in Google search results
 * - Displays SEO title with character count
 * - Shows URL structure based on primary category
 * - Displays meta description with character count
 *
 * Layout:
 * ┌─────────────────────────────────────────────────────────────┐
 * │ 🔍 Google 搜索預覽                                          │
 * ├─────────────────────────────────────────────────────────────┤
 * │ 收藏10種「天然補血食物」- 大紀元健康          [28/60 字符]   │
 * │ https://health.epochtimes.com/food/天然補血食物             │
 * │ 經常疲倦、頭暈、掉髮？可能是氣血不足的警訊！本文精選10種... │
 * │                                              [156/160 字符] │
 * └─────────────────────────────────────────────────────────────┘
 */

import React from 'react';
import { Search, AlertCircle, CheckCircle } from 'lucide-react';

export interface GoogleSearchPreviewProps {
  /** SEO Title (30-60 chars optimal) */
  seoTitle?: string;
  /** Fallback to article title if no SEO title */
  articleTitle: string;
  /** Meta description (120-160 chars optimal) */
  metaDescription?: string;
  /** Primary category for URL structure */
  primaryCategory?: string | null;
  /** Site name suffix */
  siteName?: string;
}

/**
 * GoogleSearchPreview Component
 *
 * Displays a preview of how the article will appear in Google search results.
 */
export const GoogleSearchPreview: React.FC<GoogleSearchPreviewProps> = ({
  seoTitle,
  articleTitle,
  metaDescription,
  primaryCategory,
  siteName = '大紀元健康',
}) => {
  // Use SEO title or fall back to article title
  const displayTitle = seoTitle || articleTitle;
  const fullTitle = `${displayTitle} - ${siteName}`;
  const titleLength = fullTitle.length;

  // Title validation (optimal: 30-60 chars)
  const isTitleOptimal = titleLength >= 30 && titleLength <= 60;
  const isTitleTooLong = titleLength > 60;
  const isTitleTooShort = titleLength < 30;

  // Description validation (optimal: 120-160 chars)
  const descLength = metaDescription?.length || 0;
  const isDescOptimal = descLength >= 120 && descLength <= 160;
  const isDescTooLong = descLength > 160;
  const isDescTooShort = descLength > 0 && descLength < 120;

  // Generate URL based on category
  const generateUrl = () => {
    const baseUrl = 'health.epochtimes.com';
    const categorySlug = primaryCategory
      ? primaryCategory.toLowerCase().replace(/\s+/g, '-')
      : 'article';
    const titleSlug = displayTitle
      .replace(/[「」『』【】《》〈〉]/g, '')
      .replace(/\s+/g, '-')
      .substring(0, 30);
    return `https://${baseUrl}/${categorySlug}/${titleSlug}`;
  };

  // Truncate description for display (Google truncates at ~160 chars)
  const truncatedDesc = metaDescription && metaDescription.length > 160
    ? metaDescription.substring(0, 157) + '...'
    : metaDescription;

  return (
    <div className="p-4 bg-white border border-gray-200 rounded-lg">
      <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
        <Search className="w-4 h-4 text-blue-600" />
        Google 搜索預覽
      </h4>

      {/* Google-style search result */}
      <div className="p-4 bg-white border border-gray-100 rounded-lg shadow-sm">
        {/* Title (Blue link) */}
        <div className="mb-1">
          <a
            href="#"
            className="text-xl text-[#1a0dab] hover:underline font-normal leading-tight cursor-pointer"
            onClick={(e) => e.preventDefault()}
          >
            {fullTitle.length > 60 ? fullTitle.substring(0, 57) + '...' : fullTitle}
          </a>
          <div className="flex items-center gap-2 mt-1">
            <span className={`text-xs px-1.5 py-0.5 rounded ${
              isTitleOptimal
                ? 'bg-green-100 text-green-700'
                : isTitleTooLong
                  ? 'bg-red-100 text-red-700'
                  : 'bg-amber-100 text-amber-700'
            }`}>
              {titleLength}/60 字符
              {isTitleOptimal && <CheckCircle className="w-3 h-3 inline ml-1" />}
              {(isTitleTooLong || isTitleTooShort) && <AlertCircle className="w-3 h-3 inline ml-1" />}
            </span>
            {isTitleTooLong && (
              <span className="text-xs text-red-600">標題過長，將被截斷</span>
            )}
            {isTitleTooShort && (
              <span className="text-xs text-amber-600">標題較短，可增加關鍵詞</span>
            )}
          </div>
        </div>

        {/* URL (Green) */}
        <div className="text-sm text-[#006621] mb-1 truncate">
          {generateUrl()}
        </div>

        {/* Description (Gray) */}
        <div className="text-sm text-[#545454] leading-relaxed">
          {truncatedDesc || (
            <span className="italic text-gray-400">未設置 Meta 描述</span>
          )}
        </div>
        {metaDescription && (
          <div className="flex items-center gap-2 mt-1">
            <span className={`text-xs px-1.5 py-0.5 rounded ${
              isDescOptimal
                ? 'bg-green-100 text-green-700'
                : isDescTooLong
                  ? 'bg-red-100 text-red-700'
                  : isDescTooShort
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-gray-100 text-gray-600'
            }`}>
              {descLength}/160 字符
              {isDescOptimal && <CheckCircle className="w-3 h-3 inline ml-1" />}
              {isDescTooLong && <AlertCircle className="w-3 h-3 inline ml-1" />}
            </span>
            {isDescTooLong && (
              <span className="text-xs text-red-600">描述過長，將被截斷</span>
            )}
            {isDescTooShort && (
              <span className="text-xs text-amber-600">描述較短，建議補充</span>
            )}
          </div>
        )}
      </div>

      {/* Tips */}
      <div className="mt-3 text-xs text-gray-500 space-y-1">
        <p>• 標題最佳長度: 30-60 字符 (含網站名稱)</p>
        <p>• 描述最佳長度: 120-160 字符</p>
      </div>
    </div>
  );
};

GoogleSearchPreview.displayName = 'GoogleSearchPreview';
