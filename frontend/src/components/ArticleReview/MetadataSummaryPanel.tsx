/**
 * MetadataSummaryPanel - Comprehensive metadata overview for publish preview
 *
 * Phase 16: Enhanced Publish Preview
 * - Google search preview (NEW)
 * - Parsing confirmation details (NEW)
 * - Proofreading summary with proper stats (ENHANCED)
 * - SEO metadata (title, description, keywords)
 * - Categories (primary + secondary)
 * - Tags
 * - Article statistics (unified word/char count)
 * - Article images list (NEW)
 * - Featured image removed (shown in main preview only)
 */

import React from 'react';
import {
  Search,
  FolderTree,
  Tag,
  BarChart3,
  Clock,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { Badge } from '../ui';
// Phase 16: All components enabled
import { GoogleSearchPreview } from './GoogleSearchPreview';
import { ParsingConfirmationSection } from './ParsingConfirmationSection';
import { ProofreadingSummarySection } from './ProofreadingSummarySection';
import { ArticleImagesList } from './ArticleImagesList';

// Phase 16: Type definitions moved here temporarily for interface compatibility
export interface ProofreadingSummaryStats {
  totalIssues: number;
  acceptedCount: number;
  rejectedCount: number;
  modifiedCount: number;
  pendingCount: number;
  criticalCount?: number;
  warningCount?: number;
  infoCount?: number;
}

export interface ArticleImage {
  id?: number;
  image_url: string;
  alt_text?: string | null;
  ai_alt_text?: string | null;
  position?: number;
  filename?: string;
  source_url?: string;
}

export interface MetadataSummaryPanelProps {
  /** SEO data */
  seo: {
    title?: string;
    description?: string;
    keywords: string[];
    score?: number;
  };
  /** Category data */
  categories: {
    primary?: string | null;
    secondary: string[];
  };
  /** Tags */
  tags: string[];
  /** Article statistics */
  stats: {
    wordCount: number;
    charCount: number;
    readingTimeMinutes?: number;
    paragraphCount?: number;
  };
  /** Proofreading summary - ENHANCED */
  proofreading?: ProofreadingSummaryStats | null;
  /** Featured image URL - NO LONGER DISPLAYED HERE (shown in main preview) */
  featuredImage?: string;
  /** NEW: Parsing confirmation data */
  parsing?: {
    title: string;
    titlePrefix?: string | null;
    titleSuffix?: string | null;
    seoTitle?: string | null;
    authorName?: string | null;
    authorLine?: string | null;
    parsingConfirmed?: boolean;
    parsingConfirmedAt?: string | null;
  };
  /** NEW: Article images */
  articleImages?: ArticleImage[];
}

/**
 * MetadataSummaryPanel Component
 */
export const MetadataSummaryPanel: React.FC<MetadataSummaryPanelProps> = ({
  seo,
  categories,
  tags,
  stats,
  proofreading,
  featuredImage,
  parsing,
  articleImages,
}) => {
  // Calculate reading time if not provided
  const readingTime = stats.readingTimeMinutes ?? Math.ceil(stats.wordCount / 200);

  return (
    <div className="space-y-4">
      {/* 1. Google Search Preview (NEW) */}
      <GoogleSearchPreview
        seoTitle={seo.title}
        articleTitle={parsing?.title || seo.title || ''}
        metaDescription={seo.description}
        primaryCategory={categories.primary}
      />

      {/* 2. Parsing Confirmation Section (NEW) */}
      {parsing && (
        <ParsingConfirmationSection
          title={parsing.title}
          titlePrefix={parsing.titlePrefix}
          titleSuffix={parsing.titleSuffix}
          seoTitle={parsing.seoTitle}
          authorName={parsing.authorName}
          authorLine={parsing.authorLine}
          parsingConfirmed={parsing.parsingConfirmed}
          parsingConfirmedAt={parsing.parsingConfirmedAt}
        />
      )}

      {/* 3. Proofreading Summary (NEW component) */}
      <ProofreadingSummarySection stats={proofreading} />

      {/* 4. SEO Section */}
      <div className="p-4 bg-white border border-gray-200 rounded-lg">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
          <Search className="w-4 h-4 text-blue-600" />
          SEO 優化
          {seo.score != null && (
            <span
              className={`ml-auto text-xs px-2 py-0.5 rounded-full ${
                seo.score >= 0.7
                  ? 'bg-green-100 text-green-700'
                  : seo.score >= 0.5
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-red-100 text-red-700'
              }`}
            >
              {Math.round(seo.score * 100)}分
            </span>
          )}
        </h4>
        <div className="space-y-2.5">
          {/* Keywords */}
          <div>
            <div className="text-xs text-gray-500 mb-1">關鍵詞 ({seo.keywords.length})</div>
            {seo.keywords.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {seo.keywords.map((keyword, idx) => (
                  <Badge
                    key={idx}
                    variant="secondary"
                    className="text-xs bg-blue-50 text-blue-700 border-blue-200"
                  >
                    {keyword}
                  </Badge>
                ))}
              </div>
            ) : (
              <span className="text-sm text-gray-400 italic">未設置</span>
            )}
          </div>
        </div>
      </div>

      {/* 5. Categories & Tags Section */}
      <div className="p-4 bg-white border border-gray-200 rounded-lg">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
          <FolderTree className="w-4 h-4 text-purple-600" />
          分類與標籤
        </h4>
        <div className="space-y-2.5">
          {/* Primary Category */}
          <div>
            <div className="text-xs text-gray-500 mb-1">主分類</div>
            {categories.primary ? (
              <Badge className="bg-yellow-100 text-yellow-800 border-yellow-300">
                {categories.primary}
              </Badge>
            ) : (
              <span className="text-sm text-amber-600 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                未設置
              </span>
            )}
          </div>
          {/* Secondary Categories */}
          {categories.secondary.length > 0 && (
            <div>
              <div className="text-xs text-gray-500 mb-1">
                副分類 ({categories.secondary.length})
              </div>
              <div className="flex flex-wrap gap-1.5">
                {categories.secondary.map((cat, idx) => (
                  <Badge key={idx} variant="secondary" className="text-xs">
                    {cat}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {/* Tags */}
          <div>
            <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
              <Tag className="w-3 h-3" />
              標籤 ({tags.length})
            </div>
            {tags.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {tags.map((tag, idx) => (
                  <Badge
                    key={idx}
                    variant="info"
                    className="text-xs bg-cyan-50 text-cyan-700 border-cyan-200"
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            ) : (
              <span className="text-sm text-gray-400 italic">無標籤</span>
            )}
          </div>
        </div>
      </div>

      {/* 6. Statistics Section (Enhanced with word count) */}
      <div className="p-4 bg-white border border-gray-200 rounded-lg">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800 mb-3">
          <BarChart3 className="w-4 h-4 text-green-600" />
          文章統計
        </h4>
        <div className="grid grid-cols-3 gap-2">
          <div className="p-2 bg-gray-50 rounded text-center">
            <div className="text-lg font-semibold text-gray-900">
              {stats.wordCount.toLocaleString('zh-CN')}
            </div>
            <div className="text-xs text-gray-500">字數</div>
          </div>
          <div className="p-2 bg-gray-50 rounded text-center">
            <div className="text-lg font-semibold text-gray-900">
              {stats.charCount.toLocaleString('zh-CN')}
            </div>
            <div className="text-xs text-gray-500 flex items-center justify-center gap-1">
              <FileText className="w-3 h-3" />
              字符
            </div>
          </div>
          <div className="p-2 bg-gray-50 rounded text-center">
            <div className="text-lg font-semibold text-gray-900">~{readingTime}分</div>
            <div className="text-xs text-gray-500 flex items-center justify-center gap-1">
              <Clock className="w-3 h-3" />
              閱讀
            </div>
          </div>
        </div>
      </div>

      {/* 7. Article Images List (NEW) */}
      {articleImages && articleImages.length > 0 && (
        <ArticleImagesList images={articleImages} />
      )}
    </div>
  );
};

MetadataSummaryPanel.displayName = 'MetadataSummaryPanel';
