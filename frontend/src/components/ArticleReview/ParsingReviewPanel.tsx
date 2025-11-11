/**
 * ParsingReviewPanel - Parsing review interface for article metadata
 *
 * Phase 8.2: Parsing Review Panel
 * - 60% + 40% grid layout
 * - Left: Title, Author, Images
 * - Right: SEO, FAQ
 * - All parsing data in one view (no page jumps)
 *
 * Layout:
 * ┌────────────────────────────────┬──────────────────┐
 * │ Title Review (60%)             │ SEO Review (40%) │
 * │ Author Review                  │ FAQ Review       │
 * │ Image Review                   │                  │
 * └────────────────────────────────┴──────────────────┘
 */

import React, { useState } from 'react';
import { Card } from '../ui';
import { Button } from '../ui';
import { TitleReviewSection } from './TitleReviewSection';
import { AuthorReviewSection } from './AuthorReviewSection';
import { ImageReviewSection } from './ImageReviewSection';
import { SEOReviewSection } from './SEOReviewSection';
import { FAQReviewSection } from './FAQReviewSection';
import type { ArticleReviewData } from '../../hooks/articleReview/useArticleReviewData';

export interface ParsingReviewPanelProps {
  /** Article review data */
  data: ArticleReviewData;
  /** Callback when parsing data is saved */
  onSave: (data: ParsingData) => Promise<void>;
  /** Whether save is in progress */
  isSaving?: boolean;
}

/**
 * Parsing data structure for saving
 */
export interface ParsingData {
  title?: string;
  author?: string;
  featured_image_path?: string;
  additional_images?: string[];
  seo_metadata?: {
    meta_description?: string;
    keywords?: string[];
  };
  faq_suggestions?: Array<{
    question: string;
    answer: string;
  }>;
}

/**
 * ParsingReviewPanel Component
 */
export const ParsingReviewPanel: React.FC<ParsingReviewPanelProps> = ({
  data,
  onSave,
  isSaving = false,
}) => {
  // Local state for parsing data (editable)
  const [title, setTitle] = useState(data.title || '');
  const [author, setAuthor] = useState(data.author || '');
  const [featuredImage, setFeaturedImage] = useState((data.metadata?.featured_image_path as string) || '');
  const [additionalImages, setAdditionalImages] = useState<string[]>(
    (data.metadata?.additional_images as string[]) || []
  );
  const [metaDescription, setMetaDescription] = useState(
    data.meta_description || ''
  );
  const [seoKeywords, setSeoKeywords] = useState<string[]>(data.seo_keywords || []);
  const [faqSuggestions, setFaqSuggestions] = useState<Array<{ question: string; answer: string }>>(
    (data.metadata?.faq_suggestions as Array<{ question: string; answer: string }>) || []
  );

  // Track if data has been modified
  const [isDirty, setIsDirty] = useState(false);

  const handleSave = async () => {
    const parsingData: ParsingData = {
      title,
      author,
      featured_image_path: featuredImage,
      additional_images: additionalImages,
      seo_metadata: {
        meta_description: metaDescription,
        keywords: seoKeywords,
      },
      faq_suggestions: faqSuggestions,
    };

    await onSave(parsingData);
    setIsDirty(false);
  };

  const markDirty = () => {
    if (!isDirty) {
      setIsDirty(true);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Dirty indicator */}
      {isDirty && (
        <div className="mb-4 px-4 py-2 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-sm text-amber-800">
            ⚠️ 您有未保存的更改。请记得保存或按 Ctrl+S。
          </p>
        </div>
      )}

      {/* Main content: 60% + 40% grid */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-5 gap-6 overflow-auto">
        {/* Left column: 60% (3 out of 5 cols) */}
        <div className="lg:col-span-3 space-y-6">
          {/* Title Review */}
          <Card className="p-6">
            <TitleReviewSection
              title={title}
              originalTitle={data.title || ''}
              worklistItemId={data.id}
              onTitleChange={(newTitle) => {
                setTitle(newTitle);
                markDirty();
              }}
            />
          </Card>

          {/* Author Review */}
          <Card className="p-6">
            <AuthorReviewSection
              author={author}
              originalAuthor={data.author || ''}
              onAuthorChange={(newAuthor) => {
                setAuthor(newAuthor);
                markDirty();
              }}
            />
          </Card>

          {/* Image Review */}
          <Card className="p-6">
            <ImageReviewSection
              featuredImage={featuredImage}
              additionalImages={additionalImages}
              worklistItemId={data.id}
              onFeaturedImageChange={(url) => {
                setFeaturedImage(url);
                markDirty();
              }}
              onAdditionalImagesChange={(urls) => {
                setAdditionalImages(urls);
                markDirty();
              }}
            />
          </Card>
        </div>

        {/* Right column: 40% (2 out of 5 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* SEO Review */}
          <Card className="p-6">
            <SEOReviewSection
              metaDescription={metaDescription}
              keywords={seoKeywords}
              onMetaDescriptionChange={(desc) => {
                setMetaDescription(desc);
                markDirty();
              }}
              onKeywordsChange={(kw) => {
                setSeoKeywords(kw);
                markDirty();
              }}
            />
          </Card>

          {/* FAQ Review */}
          <Card className="p-6">
            <FAQReviewSection
              faqs={faqSuggestions}
              onFaqsChange={(faqs) => {
                setFaqSuggestions(faqs);
                markDirty();
              }}
            />
          </Card>
        </div>
      </div>

      {/* Action buttons */}
      <div className="mt-6 flex items-center justify-between pt-4 border-t">
        <div className="text-sm text-gray-600">
          {isDirty && (
            <span className="text-amber-600 font-medium">● 未保存的更改</span>
          )}
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => {
              // Reset to original data
              setTitle(data.title || '');
              setAuthor(data.author || '');
              setFeaturedImage((data.metadata?.featured_image_path as string) || '');
              setAdditionalImages((data.metadata?.additional_images as string[]) || []);
              setMetaDescription(data.meta_description || '');
              setSeoKeywords(data.seo_keywords || []);
              setFaqSuggestions((data.metadata?.faq_suggestions as Array<{ question: string; answer: string }>) || []);
              setIsDirty(false);
            }}
            disabled={!isDirty || isSaving}
          >
            重置
          </Button>
          <Button
            onClick={handleSave}
            disabled={!isDirty || isSaving}
          >
            {isSaving ? '保存中...' : '保存解析数据'}
          </Button>
        </div>
      </div>
    </div>
  );
};

ParsingReviewPanel.displayName = 'ParsingReviewPanel';
