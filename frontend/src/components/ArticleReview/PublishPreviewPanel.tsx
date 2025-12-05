/**
 * PublishPreviewPanel - Final preview before publishing
 *
 * Phase 8.4: Publish Preview Panel
 * - 40% + 60% layout
 * - Left: Final content preview
 * - Right: Publish settings + confirmation
 *
 * Layout:
 * ┌───────────────────────┬──────────────────────────┐
 * │ Final Content Preview │ Publish Settings (60%)   │
 * │ (40%)                 │ • Status/Visibility      │
 * │ • Title               │ • Publish date/time      │
 * │ • Content             │ • Categories/Tags        │
 * │ • Images              │ • Featured image         │
 * │ • SEO metadata        │ Confirmation             │
 * └───────────────────────┴──────────────────────────┘
 */

import React, { useState, useMemo } from 'react';
import { Card } from '../ui';
import { Button } from '../ui';
import { FinalContentPreview } from './FinalContentPreview';
import { PublishSettingsSection } from './PublishSettingsSection';
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
  // Local state for publish settings
  const [publishStatus, setPublishStatus] = useState<'draft' | 'publish' | 'schedule'>('publish');
  const [visibility, setVisibility] = useState<'public' | 'private' | 'password'>('public');
  const [password, setPassword] = useState('');
  const [publishDate, setPublishDate] = useState<string>(''); // Empty = immediate
  // Phase 11: Primary + Secondary category state
  const [primaryCategory, setPrimaryCategory] = useState<string | null>(
    data.primary_category || null
  );
  const [secondaryCategories, setSecondaryCategories] = useState<string[]>(
    data.secondary_categories || []
  );
  const [tags, setTags] = useState<string[]>(data.tags || []);
  const [featuredImage, setFeaturedImage] = useState<string>(
    (data.metadata?.featured_image_path as string) || ''
  );
  const [excerpt, setExcerpt] = useState<string>((data.metadata?.excerpt as string) || '');

  // Show confirmation dialog
  const [showConfirmation, setShowConfirmation] = useState(false);

  // Validation: Check if all required fields are present
  const isReadyToPublish = useMemo(() => {
    if (!data.title || !data.content) return false;
    if (publishStatus === 'schedule' && !publishDate) return false;
    if (visibility === 'password' && !password) return false;
    return true;
  }, [data.title, data.content, publishStatus, publishDate, visibility, password]);

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
      // Phase 11: Use primary + secondary categories
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

  // Content data for preview
  const contentData = {
    title: data.title || '',
    content: (data.metadata?.proofread_content as string) || data.content || '',
    author: data.author || '',
    featuredImage,
    seoMetadata: {
      metaDescription: data.meta_description || '',
      keywords: data.seo_keywords || [],
    },
    // Phase 11: Include both primary and secondary categories
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
          {/* Publish settings */}
          <Card className="p-6">
            <PublishSettingsSection
              publishStatus={publishStatus}
              visibility={visibility}
              password={password}
              publishDate={publishDate}
              primaryCategory={primaryCategory}
              secondaryCategories={secondaryCategories}
              tags={tags}
              featuredImage={featuredImage}
              excerpt={excerpt}
              onPublishStatusChange={setPublishStatus}
              onVisibilityChange={setVisibility}
              onPasswordChange={setPassword}
              onPublishDateChange={setPublishDate}
              onPrimaryCategoryChange={setPrimaryCategory}
              onSecondaryCategoriesChange={setSecondaryCategories}
              onTagsChange={setTags}
              onFeaturedImageChange={setFeaturedImage}
              onExcerptChange={setExcerpt}
            />
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
