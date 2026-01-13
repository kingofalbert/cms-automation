/**
 * PublishPreviewPanel - Upload preview with content-first layout
 *
 * Phase 12: Clarified "上稿" workflow
 * - Articles are ALWAYS uploaded as DRAFT to WordPress
 * - Final publishing is done by editors in WordPress admin
 * - "上稿" = Upload to WP as draft, NOT publish
 *
 * Layout:
 * ┌─────────────────────────────────────────────────────────────────────────────┐
 * │ 上稿預覽                                            [状态: ready_to_publish] │
 * ├─────────────────────────────────────────────────────────────────────────────┤
 * │ ✓ 标题  ✓ 正文  ✓ SEO  ✓ 分类  ○ 图片  │  4/5 完成   [准备就绪]            │
 * ├────────────────────────────────────────────┬────────────────────────────────┤
 * │ 📰 文章预览 (60%)                          │ 📊 元数据概览 (40%)             │
 * │ ────────────────────────────────────────   │ ──────────────────────────      │
 * │ [前缀] 主标题 [后缀]                       │ SEO 优化                        │
 * │ 作者: xxx | 2,345 字                       │ • 标题: xxx                     │
 * │ ────────────────────────────────────────   │ • 描述: xxx                     │
 * │                                            │ • 关键词: tag1, tag2            │
 * │ [完整正文内容，可滚动]                     │ ──────────────────────────      │
 * │                                            │ 分类与标签                      │
 * │                                            │ • 主分类: xxx                   │
 * │                                            │ • 副分类: xxx                   │
 * │                                            │ • 标签: xxx                     │
 * │                                            │ ──────────────────────────      │
 * │                                            │ 文章统计                        │
 * │                                            │ • 字数: 2,345                   │
 * │                                            │ ──────────────────────────      │
 * │                                            │ 校对摘要                        │
 * │                                            │ • 新增: 5 修改: 7 删除: 2       │
 * ├────────────────────────────────────────────┴────────────────────────────────┤
 * │ 上稿設置: [草稿模式]   可見性: [公開 ▼]                                     │
 * ├─────────────────────────────────────────────────────────────────────────────┤
 * │                                                    [重置设置]    [上稿 →]   │
 * └─────────────────────────────────────────────────────────────────────────────┘
 */

import React, { useState, useMemo } from 'react';
import { Button } from '../ui';
import { FinalContentPreview, type FAQItem } from './FinalContentPreview';
import { MetadataSummaryPanel } from './MetadataSummaryPanel';
import { PublishReadinessChecklist, createChecklistItems } from './PublishReadinessChecklist';
import { PublishConfirmation } from './PublishConfirmation';
import { PublishSuccessConfirmation } from './PublishSuccessConfirmation';
import type { ArticleReviewData } from '../../hooks/articleReview/useArticleReviewData';
import { Send, CheckCircle, ExternalLink } from 'lucide-react';

/**
 * Status labels mapping - English to Traditional Chinese
 */
const STATUS_LABELS: Record<string, string> = {
  imported: '已匯入',
  parsing: '解析中',
  parsing_review: '解析審核',
  proofreading: '校對中',
  proofreading_review: '校對審核',
  'in-review': '審核中',
  ready_to_publish: '準備上稿',
  publishing: '上稿中',
  published: '已發布',
  failed: '失敗',
};

/**
 * Get Chinese label for status
 */
const getStatusLabel = (status: string): string => {
  return STATUS_LABELS[status] || status;
};

/**
 * Result returned from onPublish callback
 */
export interface PublishResult {
  wordpress_draft_url: string;
  wordpress_draft_uploaded_at: string;
  wordpress_post_id: number;
  screenshots?: string[];
}

export interface PublishPreviewPanelProps {
  /** Article review data */
  data: ArticleReviewData;
  /** FAQs selected by user */
  faqs?: FAQItem[];
  /** Callback when publish is triggered. Returns publish result on success. */
  onPublish: (settings: PublishSettings) => Promise<PublishResult | void>;
  /** Whether publishing is in progress */
  isPublishing?: boolean;
}

export interface PublishSettings {
  status: 'draft' | 'publish' | 'schedule';
  visibility: 'public' | 'private' | 'password';
  password?: string;
  publish_date?: string; // ISO 8601 format
  /** @deprecated Use primary_category and secondary_categories instead */
  categories?: string[];
  /** Primary category (主分類) - determines URL structure */
  primary_category?: string;
  /** Secondary categories (副分類) - for cross-listing */
  secondary_categories?: string[];
  tags?: string[];
  featured_image?: string;
  excerpt?: string;
}

/**
 * PublishPreviewPanel Component
 *
 * Provides a unified, content-first layout for final publish preview.
 */
export const PublishPreviewPanel: React.FC<PublishPreviewPanelProps> = ({
  data,
  faqs = [],
  onPublish,
  isPublishing = false,
}) => {
  // Local state for publish settings
  // Default to 'draft' mode - articles are uploaded but NOT published
  // Final editors will review and publish in WordPress admin
  const [showConfirmation, setShowConfirmation] = useState(false);

  // Phase 17: State for success confirmation
  const [showSuccessConfirmation, setShowSuccessConfirmation] = useState(false);
  const [publishResult, setPublishResult] = useState<PublishResult | null>(null);

  // Read categories/tags from data (set in ParsingReviewPanel)
  const primaryCategory = data.primary_category || null;
  const secondaryCategories = data.secondary_categories || [];
  const tags = data.tags || [];
  const featuredImage = (data.metadata?.featured_image_path as string) || '';
  const excerpt = (data.metadata?.excerpt as string) || '';

  // Get content
  const content = useMemo(() => {
    return (
      (data.metadata?.proofread_content as string) ||
      data.articleReview?.content?.suggested ||
      data.articleReview?.content?.original ||
      ''
    );
  }, [data.metadata?.proofread_content, data.articleReview?.content]);

  // Validation
  const hasValidContent = Boolean(content);
  const hasSeoKeywords = (data.seo_keywords?.length ?? 0) > 0;
  const hasSeoDescription = Boolean(data.meta_description);

  const isReadyToPublish = useMemo(() => {
    // Simplified: only need title and content to be ready for draft upload
    if (!data.title || !hasValidContent) return false;
    return true;
  }, [data.title, hasValidContent]);

  // Check if article has FAQ applicable flag (defaults to true if not set)
  const faqApplicable = data.articleReview?.faq_applicable ?? true;

  // Check if article is already published (uploaded to WordPress)
  const isAlreadyPublished = data.status === 'published';

  // Extract WordPress draft info if available (from metadata or direct fields)
  const wordpressDraftUrl = (data.metadata?.wordpress_draft_url as string) ||
    ((data as unknown) as Record<string, unknown>).wordpress_draft_url as string | undefined;
  const wordpressPostId = (data.metadata?.wordpress_post_id as number) ||
    ((data as unknown) as Record<string, unknown>).wordpress_post_id as number | undefined;
  const wordpressDraftUploadedAt = (data.metadata?.wordpress_draft_uploaded_at as string) ||
    ((data as unknown) as Record<string, unknown>).wordpress_draft_uploaded_at as string | undefined;

  // Checklist items
  const checklistItems = useMemo(() => {
    return createChecklistItems({
      hasTitle: Boolean(data.title),
      hasContent: hasValidContent,
      hasSeoKeywords,
      hasSeoDescription,
      hasCategory: Boolean(primaryCategory),
      hasTags: tags.length > 0,
      hasFeaturedImage: Boolean(featuredImage),
      hasFaqs: faqs.length > 0,
      faqApplicable,
    });
  }, [data.title, hasValidContent, hasSeoKeywords, hasSeoDescription, primaryCategory, tags, featuredImage, faqs.length, faqApplicable]);

  // Calculate proofreading stats from worklist proofreading_stats (ENHANCED)
  const proofreadingStats = useMemo(() => {
    const stats = data.proofreading_stats;
    if (stats && stats.total_issues > 0) {
      return {
        totalIssues: stats.total_issues,
        acceptedCount: stats.accepted_count || 0,
        rejectedCount: stats.rejected_count || 0,
        modifiedCount: stats.modified_count || 0,
        pendingCount: stats.pending_count || 0,
        criticalCount: stats.critical_count,
        warningCount: stats.warning_count,
        infoCount: stats.info_count,
      };
    }
    return null;
  }, [data.proofreading_stats]);

  // Calculate character count
  const charCount = content.length;
  const wordCount = useMemo(() => {
    const doc = new DOMParser().parseFromString(content, 'text/html');
    return (doc.body.textContent || '').length;
  }, [content]);

  // Handlers
  const handlePublishClick = () => {
    if (!isReadyToPublish) {
      alert('請完成所有必填項');
      return;
    }
    setShowConfirmation(true);
  };

  const handleConfirmPublish = async () => {
    // Simplified settings - always upload as draft with public visibility
    const settings: PublishSettings = {
      status: 'draft',
      visibility: 'public',
      primary_category: primaryCategory || undefined,
      secondary_categories: secondaryCategories.length > 0 ? secondaryCategories : undefined,
      tags,
      featured_image: featuredImage,
      excerpt,
    };

    try {
      const result = await onPublish(settings);
      setShowConfirmation(false);

      // Phase 17: If onPublish returns a result with WordPress info, show success confirmation
      if (result && result.wordpress_draft_url && result.wordpress_post_id) {
        setPublishResult(result);
        setShowSuccessConfirmation(true);
      }
    } catch (error) {
      // Error handling is done by the parent component
      setShowConfirmation(false);
    }
  };

  const handleCancelConfirmation = () => {
    setShowConfirmation(false);
  };

  // Phase 17: Handler to close success confirmation
  const handleCloseSuccessConfirmation = () => {
    setShowSuccessConfirmation(false);
    setPublishResult(null);
  };

  // Content data for preview
  const contentData = {
    title: data.title || '',
    titlePrefix: data.title_prefix || null,
    titleSuffix: data.title_suffix || null,
    content,
    author: data.author || data.author_name || '',
    featuredImage,
    seoMetadata: {
      metaDescription: data.meta_description || '',
      keywords: data.seo_keywords || [],
    },
    primaryCategory,
    secondaryCategories,
    tags,
  };

  // Metadata for summary panel (ENHANCED with parsing and articleImages)
  const metadataData = {
    seo: {
      title: data.seo_title || data.title || undefined,
      description: data.meta_description || undefined,
      keywords: data.seo_keywords || [],
      score: data.articleReview?.seo?.score ?? undefined,
    },
    categories: {
      primary: primaryCategory,
      secondary: secondaryCategories,
    },
    tags,
    stats: {
      wordCount,
      charCount,
    },
    proofreading: proofreadingStats,
    featuredImage,
    // NEW: Parsing confirmation data
    parsing: {
      title: data.title || '',
      titlePrefix: data.title_prefix || null,
      titleSuffix: data.title_suffix || null,
      seoTitle: data.seo_title || null,
      authorName: data.author_name || data.author || null,
      authorLine: data.author_line || null,
      parsingConfirmed: data.parsing_confirmed || false,
      parsingConfirmedAt: data.parsing_confirmed_at || null,
    },
    // NEW: Article images
    articleImages: data.article_images || [],
  };

  return (
    <div className="h-full flex flex-col min-h-0 flex-1">
      {/* ===== SCROLLABLE PREVIEW CONTENT AREA ===== */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {/* Header */}
        <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">上稿預覽</h3>
            <div className="flex items-center gap-4 text-sm">
              <span className="text-gray-600">
                狀態: <strong className="text-blue-600">{getStatusLabel(data.status)}</strong>
              </span>
            </div>
          </div>
        </div>

        {/* Readiness Checklist */}
        <div className="mb-4">
          <PublishReadinessChecklist items={checklistItems} isReady={isReadyToPublish} />
        </div>

        {/* Main content: 60% + 40% grid */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 min-h-[400px]">
          {/* Left column: 60% (3 out of 5 cols) - Article Preview */}
          <div className="lg:col-span-3 flex flex-col h-full">
            <FinalContentPreview data={contentData} faqs={faqs} flexHeight={true} />
          </div>

          {/* Right column: 40% (2 out of 5 cols) - Metadata Summary (ENHANCED) */}
          <div className="lg:col-span-2 overflow-y-auto">
            <MetadataSummaryPanel
              seo={metadataData.seo}
              categories={metadataData.categories}
              tags={metadataData.tags}
              stats={metadataData.stats}
              proofreading={metadataData.proofreading}
              featuredImage={metadataData.featuredImage}
              parsing={metadataData.parsing}
              articleImages={metadataData.articleImages}
            />
          </div>
        </div>
      </div>

      {/* ===== BOTTOM SECTION: Action Button (always visible at bottom) ===== */}
      <div className="flex-shrink-0 border-t bg-white pt-4 mt-4">
        {/* Info banner - show different content based on published status */}
        {isAlreadyPublished && wordpressDraftUrl ? (
          /* Already published with WordPress URL - show success block */
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-full">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-green-900">已成功上稿至 WordPress</p>
                  <p className="text-sm text-green-700">
                    Post ID: #{wordpressPostId}
                    {wordpressDraftUploadedAt && ` | 上傳於: ${new Date(wordpressDraftUploadedAt).toLocaleString('zh-TW')}`}
                  </p>
                </div>
              </div>
              <a
                href={wordpressDraftUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                前往 WordPress 編輯
              </a>
            </div>
          </div>
        ) : (
          /* Not published yet - show draft mode info */
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-blue-800">
              <Send className="w-4 h-4 text-blue-600" />
              <span>
                <strong>上稿模式：</strong>文章將上傳到 WordPress 作為草稿，由最終審稿編輯在 WordPress 後台審核後再發布。
              </span>
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {isAlreadyPublished ? (
              <span className="text-green-600 flex items-center gap-1">
                <span>✅</span>
                此文章已上稿至 WordPress，無需重複提交
              </span>
            ) : !isReadyToPublish ? (
              <span className="text-amber-600 flex items-center gap-1">
                <span>⚠️</span>
                請完成所有必填項才能上稿
              </span>
            ) : (
              <span className="text-green-600 flex items-center gap-1">
                <span>✓</span>
                準備就緒，可以上稿
              </span>
            )}
          </div>
          <Button
            onClick={handlePublishClick}
            disabled={!isReadyToPublish || isPublishing || isAlreadyPublished}
            className="min-w-32 flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            {isPublishing ? '上稿中...' : isAlreadyPublished ? '已上稿' : '上稿'}
          </Button>
        </div>
      </div>

      {/* Confirmation dialog */}
      {showConfirmation && (
        <PublishConfirmation
          settings={{
            status: 'draft',
            visibility: 'public',
            primary_category: primaryCategory || undefined,
            secondary_categories: secondaryCategories.length > 0 ? secondaryCategories : undefined,
            tags,
            featured_image: featuredImage,
            excerpt,
          }}
          articleTitle={data.title || ''}
          onConfirm={handleConfirmPublish}
          onCancel={handleCancelConfirmation}
          isPublishing={isPublishing}
        />
      )}

      {/* Phase 17: Success confirmation with WordPress draft info */}
      {showSuccessConfirmation && publishResult && (
        <PublishSuccessConfirmation
          articleTitle={data.title || ''}
          wordpressDraftUrl={publishResult.wordpress_draft_url}
          uploadedAt={publishResult.wordpress_draft_uploaded_at}
          wordpressPostId={publishResult.wordpress_post_id}
          screenshots={publishResult.screenshots}
          onClose={handleCloseSuccessConfirmation}
        />
      )}
    </div>
  );
};

PublishPreviewPanel.displayName = 'PublishPreviewPanel';
