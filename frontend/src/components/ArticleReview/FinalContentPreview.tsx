/**
 * FinalContentPreview - Magazine-style article preview before publish
 *
 * Phase 11.5: Enhanced Publish Preview
 * - Full article preview with proper HTML rendering
 * - Title with prefix/suffix support
 * - Author information
 * - Complete content (not truncated)
 * - Clean, magazine-style layout
 *
 * Layout:
 * ┌─────────────────────────────────────────────┐
 * │ [前缀] 主标题 [后缀]                        │
 * │ 作者: xxx                                   │
 * │ ─────────────────────────────────────────── │
 * │                                             │
 * │ [完整正文内容，支持滚动]                    │
 * │                                             │
 * │                                             │
 * │                                             │
 * └─────────────────────────────────────────────┘
 */

import React, { useMemo } from 'react';
import DOMPurify from 'dompurify';
import { FileText, User, Newspaper, HelpCircle } from 'lucide-react';

export interface FAQItem {
  question: string;
  answer: string;
}

export interface FinalContentPreviewProps {
  /** Content data to preview */
  data: {
    title: string;
    titlePrefix?: string | null;
    titleSuffix?: string | null;
    content: string;
    author: string;
    featuredImage?: string;
    seoMetadata: {
      metaDescription: string;
      keywords: string[];
    };
    /** Primary category (主分類) - determines URL structure */
    primaryCategory?: string | null;
    /** Secondary categories (副分類) - for cross-listing */
    secondaryCategories?: string[];
    tags: string[];
  };
  /** FAQ items to display at the end of content */
  faqs?: FAQItem[];
  /**
   * Maximum height for content area
   * @deprecated Use flexHeight=true for responsive layouts
   * Default: 'none' (no max height, fills available space)
   */
  maxContentHeight?: string;
  /**
   * Enable flex-based height (fills parent container)
   * When true, component expands to fill available vertical space
   * Default: true
   */
  flexHeight?: boolean;
}

/**
 * FinalContentPreview Component
 *
 * Displays the final article in a clean, magazine-style layout.
 * Content is rendered with proper HTML formatting using DOMPurify for security.
 */
export const FinalContentPreview: React.FC<FinalContentPreviewProps> = ({
  data,
  faqs = [],
  maxContentHeight,
  flexHeight = true,
}) => {
  // Sanitize HTML content for safe rendering
  const sanitizedContent = useMemo(() => {
    return DOMPurify.sanitize(data.content, {
      ALLOWED_TAGS: [
        'p',
        'br',
        'b',
        'strong',
        'i',
        'em',
        'u',
        'span',
        'div',
        'section',
        'h1',
        'h2',
        'h3',
        'h4',
        'h5',
        'h6',
        'ul',
        'ol',
        'li',
        'a',
        'blockquote',
        'pre',
        'code',
        'img',
        'figure',
        'figcaption',
        'table',
        'thead',
        'tbody',
        'tr',
        'th',
        'td',
        'hr',
        'sub',
        'sup',
        'mark',
        'small',
        'del',
        'ins',
      ],
      ALLOWED_ATTR: [
        'href',
        'src',
        'alt',
        'title',
        'class',
        'style',
        'target',
        'rel',
        'id',
        'width',
        'height',
      ],
    });
  }, [data.content]);

  // Build display title with prefix/suffix
  const displayTitle = useMemo(() => {
    const parts: string[] = [];
    if (data.titlePrefix) parts.push(data.titlePrefix);
    parts.push(data.title || '(无标题)');
    if (data.titleSuffix) parts.push(data.titleSuffix);
    return parts.join(' ');
  }, [data.title, data.titlePrefix, data.titleSuffix]);

  // Calculate word count
  const wordCount = useMemo(() => {
    const doc = new DOMParser().parseFromString(data.content, 'text/html');
    const text = doc.body.textContent || '';
    return text.length;
  }, [data.content]);

  return (
    <div className="h-full flex flex-col bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-white border-b border-gray-100">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <Newspaper className="w-4 h-4" />
          <span>文章预览</span>
        </div>
        {/* Title */}
        <h1 className="text-2xl font-bold text-gray-900 leading-tight mb-2">{displayTitle}</h1>
        {/* Author line */}
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span className="flex items-center gap-1.5">
            <User className="w-4 h-4" />
            {data.author || '(无作者)'}
          </span>
          <span className="text-gray-400">|</span>
          <span className="flex items-center gap-1.5">
            <FileText className="w-4 h-4" />
            {wordCount.toLocaleString('zh-CN')} 字
          </span>
        </div>
      </div>

      {/* Featured Image (if exists) */}
      {data.featuredImage && (
        <div className="px-6 py-4 border-b border-gray-100">
          <div className="relative aspect-[16/9] max-h-48 bg-gray-100 rounded-lg overflow-hidden">
            <img
              src={data.featuredImage}
              alt="特色图片"
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).parentElement!.style.display = 'none';
              }}
            />
          </div>
        </div>
      )}

      {/* Content Area - Full Article (flex-based height for responsive layouts) */}
      {/* FIXED: Changed min-h-0 to min-h-[200px] to prevent height collapse */}
      {/* The flex-1 allows expansion, min-h ensures minimum readable area */}
      <div
        className={`px-6 py-4 overflow-y-auto ${flexHeight ? 'flex-1 min-h-[200px]' : ''}`}
        style={!flexHeight && maxContentHeight ? { maxHeight: maxContentHeight } : undefined}
      >
        <article
          className="prose prose-sm md:prose-base max-w-none text-gray-800 leading-relaxed
            prose-headings:text-gray-900 prose-headings:font-semibold prose-headings:mt-6 prose-headings:mb-3
            prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg
            prose-p:my-3 prose-p:leading-relaxed prose-p:text-justify
            prose-ul:my-3 prose-ol:my-3
            prose-li:my-1
            prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
            prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:text-gray-700
            prose-img:rounded-lg prose-img:my-4 prose-img:mx-auto
            prose-figure:my-4 prose-figure:text-center
            prose-figcaption:text-sm prose-figcaption:text-gray-500
            prose-table:border-collapse prose-table:w-full
            prose-th:border prose-th:border-gray-300 prose-th:bg-gray-50 prose-th:p-2
            prose-td:border prose-td:border-gray-300 prose-td:p-2
            prose-hr:my-6 prose-hr:border-gray-200
            prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded
            prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-pre:p-4 prose-pre:rounded-lg"
          dangerouslySetInnerHTML={{ __html: sanitizedContent }}
        />

        {/* FAQ Section - Schema.org FAQPage format preview */}
        {faqs.length > 0 && (
          <section className="mt-8 pt-6 border-t border-gray-200">
            <div className="flex items-center gap-2 mb-4">
              <HelpCircle className="w-5 h-5 text-blue-600" />
              <h2 className="text-xl font-semibold text-gray-900">常見問題</h2>
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                {faqs.length} 個 FAQ
              </span>
            </div>
            <div className="space-y-4">
              {faqs.map((faq, index) => (
                <div
                  key={index}
                  className="bg-gray-50 rounded-lg p-4 border border-gray-100"
                >
                  <h3 className="font-medium text-gray-900 mb-2 flex items-start gap-2">
                    <span className="text-blue-600 font-bold">Q{index + 1}:</span>
                    <span>{faq.question}</span>
                  </h3>
                  <p className="text-gray-700 pl-7">{faq.answer}</p>
                </div>
              ))}
            </div>
            <p className="mt-4 text-xs text-gray-500 italic">
              * 此 FAQ 區塊將以 Schema.org FAQPage 格式發布，支持 Google 搜索富摘要
            </p>
          </section>
        )}
      </div>

      {/* Footer */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-100 text-xs text-gray-500 flex items-center justify-between">
        <span>预览模式 - 实际发布效果可能因 WordPress 主题而略有不同</span>
        <span>{data.content.length.toLocaleString('zh-CN')} 字符</span>
      </div>
    </div>
  );
};

FinalContentPreview.displayName = 'FinalContentPreview';
