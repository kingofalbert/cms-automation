/**
 * PublishPreviewPanel - Final preview before publishing
 *
 * Phase 11: Simplified Publish Preview
 * - Left: Final content preview (read-only summary)
 * - Right: Publish settings (actions only)
 *
 * Content-related settings (categories, tags, excerpt) are now in ParsingReviewPanel.
 * This panel focuses on:
 * - Final content preview
 * - Publish status/date
 * - Visibility settings
 * - Confirmation dialog
 *
 * Layout:
 * ┌───────────────────────┬──────────────────────────┐
 * │ Final Content Preview │ Publish Settings (60%)   │
 * │ (40%)                 │ • Status (publish/draft) │
 * │ • Title               │ • Scheduled time         │
 * │ • Content excerpt     │ • Visibility             │
 * │ • Categories (r/o)    │                          │
 * │ • Tags (r/o)          │ [Confirm Publish] btn    │
 * │ • SEO metadata        │                          │
 * └───────────────────────┴──────────────────────────┘
 */

import React, { useState, useMemo } from 'react';
import { Card } from '../ui';
import { Button } from '../ui';
import { FinalContentPreview } from './FinalContentPreview';
import { PublishSettingsSectionSimplified } from './PublishSettingsSectionSimplified';
import { PublishConfirmation } from './PublishConfirmation';
import type { ArticleReviewData } from '../../hooks/articleReview/useArticleReviewData';

export interface PublishPreviewPanelProps {
  /** Article review data */
  data: ArticleReviewData;
  /** Callback when publish is triggered */
  onPublish: (settings: PublishSettings) => Promise<void>;
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
 */
export const PublishPreviewPanel: React.FC<PublishPreviewPanelProps> = ({
  data,
  onPublish,
  isPublishing = false,
}) => {
  // Local state for publish settings (simplified - actions only)
  const [publishStatus, setPublishStatus] = useState<'draft' | 'publish' | 'schedule'>('publish');
  const [visibility, setVisibility] = useState<'public' | 'private' | 'password'>('public');
  const [password, setPassword] = useState('');
  const [publishDate, setPublishDate] = useState<string>(''); // Empty = immediate

  // Show confirmation dialog
  const [showConfirmation, setShowConfirmation] = useState(false);

  // Read categories/tags from data (set in ParsingReviewPanel, read-only here)
  const primaryCategory = data.primary_category || null;
  const secondaryCategories = data.secondary_categories || [];
  const tags = data.tags || [];
  const featuredImage = (data.metadata?.featured_image_path as string) || '';
  const excerpt = (data.metadata?.excerpt as string) || '';

  // Validation: Check if all required fields are present
  const hasValidContent = Boolean(
    data.articleReview?.content?.original ||
    data.articleReview?.content?.suggested ||
    data.metadata?.proofread_content
  );
  const isReadyToPublish = useMemo(() => {
    if (!data.title || !hasValidContent) return false;
    if (publishStatus === 'schedule' && !publishDate) return false;
    if (visibility === 'password' && !password) return false;
    return true;
  }, [data.title, hasValidContent, publishStatus, publishDate, visibility, password]);

  const handlePublishClick = () => {
    if (!isReadyToPublish) {
      alert('请完成所有必填项');
      return;
    }
    setShowConfirmation(true);
  };

  const handleConfirmPublish = async () => {
    const settings: PublishSettings = {
      status: publishStatus,
      visibility,
      password: visibility === 'password' ? password : undefined,
      publish_date: publishStatus === 'schedule' ? publishDate : undefined,
      // Read from data (set in ParsingReviewPanel)
      primary_category: primaryCategory || undefined,
      secondary_categories: secondaryCategories.length > 0 ? secondaryCategories : undefined,
      tags,
      featured_image: featuredImage,
      excerpt,
    };

    await onPublish(settings);
    setShowConfirmation(false);
  };

  const handleCancelConfirmation = () => {
    setShowConfirmation(false);
  };

  // Content data for preview (read-only)
  const contentData = {
    title: data.title || '',
    content: (data.metadata?.proofread_content as string)
      || data.articleReview?.content?.suggested
      || data.articleReview?.content?.original
      || '',
    author: data.author || '',
    featuredImage,
    seoMetadata: {
      metaDescription: data.meta_description || '',
      keywords: data.seo_keywords || [],
    },
    primaryCategory,
    secondaryCategories,
    tags,
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">发布预览</h3>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-600">
              状态: <strong className="text-blue-600">{data.status}</strong>
            </span>
            {isReadyToPublish ? (
              <span className="text-green-600 font-medium">✓ 准备就绪</span>
            ) : (
              <span className="text-amber-600 font-medium">⚠️ 需要完善</span>
            )}
          </div>
        </div>
      </div>

      {/* Main content: 40% + 60% grid */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-5 gap-6 overflow-auto">
        {/* Left column: 40% (2 out of 5 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-6">
            <FinalContentPreview data={contentData} />
          </Card>
        </div>

        {/* Right column: 60% (3 out of 5 cols) */}
        <div className="lg:col-span-3 space-y-6">
          {/* Publish settings (simplified - actions only) */}
          <Card className="p-6">
            <PublishSettingsSectionSimplified
              publishStatus={publishStatus}
              visibility={visibility}
              password={password}
              publishDate={publishDate}
              onPublishStatusChange={setPublishStatus}
              onVisibilityChange={setVisibility}
              onPasswordChange={setPassword}
              onPublishDateChange={setPublishDate}
            />
          </Card>

          {/* Read-only summary of content settings (set in ParsingReviewPanel) */}
          <Card className="p-6 bg-slate-50">
            <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              内容设置摘要 (在解析审核中设置)
            </h4>
            <div className="space-y-2 text-sm">
              <div className="flex items-start gap-2">
                <span className="text-slate-500 w-20 shrink-0">主分类:</span>
                <span className="text-slate-900 font-medium">
                  {primaryCategory || <span className="text-amber-600">未设置</span>}
                </span>
              </div>
              {secondaryCategories.length > 0 && (
                <div className="flex items-start gap-2">
                  <span className="text-slate-500 w-20 shrink-0">副分类:</span>
                  <span className="text-slate-900">{secondaryCategories.join(', ')}</span>
                </div>
              )}
              <div className="flex items-start gap-2">
                <span className="text-slate-500 w-20 shrink-0">标签:</span>
                <span className="text-slate-900">
                  {tags.length > 0 ? tags.join(', ') : <span className="text-slate-400">无</span>}
                </span>
              </div>
              {excerpt && (
                <div className="flex items-start gap-2">
                  <span className="text-slate-500 w-20 shrink-0">摘要:</span>
                  <span className="text-slate-700 line-clamp-2">{excerpt}</span>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Action buttons */}
      <div className="mt-6 flex items-center justify-between pt-4 border-t">
        <div className="text-sm text-gray-600">
          {!isReadyToPublish && (
            <span className="text-amber-600">
              ⚠️ 请完成所有必填项才能发布
            </span>
          )}
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => {
              // Reset to defaults
              setPublishStatus('publish');
              setVisibility('public');
              setPassword('');
              setPublishDate('');
            }}
            disabled={isPublishing}
          >
            重置设置
          </Button>
          <Button
            onClick={handlePublishClick}
            disabled={!isReadyToPublish || isPublishing}
            className="min-w-32"
          >
            {isPublishing ? '发布中...' : publishStatus === 'schedule' ? '定时发布' : '立即发布'}
          </Button>
        </div>
      </div>

      {/* Confirmation dialog */}
      {showConfirmation && (
        <PublishConfirmation
          settings={{
            status: publishStatus,
            visibility,
            password: visibility === 'password' ? password : undefined,
            publish_date: publishStatus === 'schedule' ? publishDate : undefined,
            // Phase 11: Use primary + secondary categories
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
    </div>
  );
};

PublishPreviewPanel.displayName = 'PublishPreviewPanel';
