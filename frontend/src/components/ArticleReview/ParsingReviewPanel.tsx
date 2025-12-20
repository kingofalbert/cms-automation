/**
 * ParsingReviewPanel - Parsing review interface for article metadata
 *
 * Phase 11: Three-column Layout Redesign (2025-12-06)
 * - Balanced 33% + 34% + 33% grid layout
 * - Left: Content basics (Title, SEO Title, Author)
 * - Center: SEO Optimization (Meta Description, Keywords, SEO Score)
 * - Right: Categories & Tags (Primary Category with AI, Secondary, Tags, Excerpt)
 * - Bottom: Image Review + FAQ (spans full width)
 *
 * Layout:
 * ┌─────────────────────┬─────────────────────┬─────────────────────┐
 * │    左栏 (33%)       │     中栏 (34%)      │    右栏 (33%)       │
 * ├─────────────────────┼─────────────────────┼─────────────────────┤
 * │ 1. 标题审核         │ 4. 元描述比较       │ 7. 主分类 (AI推荐)  │
 * │ 2. SEO Title 选择   │ 5. SEO 关键词       │ 8. 副分类选择       │
 * │ 3. 作者审核         │ 6. SEO 评分概览     │ 9. 内部标签 (Tags)  │
 * │                     │                     │ 10. 文章摘要        │
 * ├─────────────────────┼─────────────────────┴─────────────────────┤
 * │ 图片审核            │           FAQ 建议 (跨两栏)               │
 * └─────────────────────┴───────────────────────────────────────────┘
 */

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { Card } from '../ui';
import { Button } from '../ui';
import { TitleReviewSection } from './TitleReviewSection';
import { SEOTitleSelectionCard } from './SEOTitleSelectionCard';
import { AuthorReviewSection } from './AuthorReviewSection';
import { ImageReviewSection } from './ImageReviewSection';
import { ContentComparisonCard, ContentSource } from './ContentComparisonCard';
import { KeywordsComparisonCard, KeywordSource } from './KeywordsComparisonCard';
import { TagsComparisonCard, TagSource } from './TagsComparisonCard';
import { FAQReviewSection, type AIFAQSuggestion } from './FAQReviewSection';
import { CategorySelectionCard, type AICategoryRecommendation, type AISecondaryCategoryRecommendation } from './CategorySelectionCard';
import { ExcerptReviewSection } from './ExcerptReviewSection';
import type { SuggestedTag, RelatedArticle } from '../../types/api';
import type { ArticleReviewData } from '../../hooks/articleReview/useArticleReviewData';
import type { SEOTitleSuggestionsData, SelectSEOTitleResponse } from '../../types/api';
import { api } from '../../services/api-client';

/**
 * FAQ item structure
 */
export interface FAQItem {
  question: string;
  answer: string;
}

export interface ParsingReviewPanelProps {
  /** Article review data */
  data: ArticleReviewData;
  /** Callback when parsing data is saved */
  onSave: (data: ParsingData) => Promise<void>;
  /** Whether save is in progress */
  isSaving?: boolean;
  /**
   * BUGFIX: Lifted FAQ state for persistence during backtracking
   * FAQs are managed by parent (ArticleReviewModal) to survive step navigation
   * See: docs/STATE_PERSISTENCE_FIX.md
   */
  faqs?: FAQItem[];
  /** Callback when FAQs change */
  onFaqsChange?: (faqs: FAQItem[]) => void;
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
  // BUGFIX: Lifted FAQ state for persistence during backtracking
  faqs: liftedFaqs,
  onFaqsChange: onLiftedFaqsChange,
}) => {
  // Local state for parsing data (editable)
  const initialParsingState = useMemo(() => {
    const metadata = data.metadata;

    // FIX: Read images from article_images array (database-backed images)
    const articleImages = (data as any).article_images || [];
    const imageUrls = articleImages
      .sort((a: any, b: any) => a.position - b.position)
      .map((img: any) => img.source_url);
    const featuredImageUrl = imageUrls.length > 0 ? imageUrls[0] : '';
    const additionalImageUrls = imageUrls.slice(1);

    return {
      // HOTFIX-PARSE-001: Use title_main from parsing, fallback to title
      title: (data as any).title_main || data.articleReview?.title?.trim() || data.title || '',
      // HOTFIX-PARSE-002: Use author_line to preserve original format (e.g., "文 / Author　編譯 / Translator")
      // Fallback chain: author_line -> author_name -> author
      author: (data as any).author_line || (data as any).author_name || data.author || '',
      // FIX: Use article_images from API response instead of metadata fields
      featuredImage: featuredImageUrl || (metadata?.featured_image_path as string) || '',
      additionalImages: additionalImageUrls.length > 0 ? additionalImageUrls : (metadata?.additional_images as string[]) || [],
      metaDescription:
        data.articleReview?.meta?.original?.trim() ||
        data.meta_description ||
        '',
      seoKeywords:
        (data.articleReview?.seo?.original_keywords &&
          data.articleReview.seo.original_keywords.length > 0
          ? data.articleReview.seo.original_keywords
          : data.seo_keywords) || [],
      // Tags: WordPress internal navigation labels
      tags:
        (data.articleReview?.tags?.original_tags &&
          data.articleReview.tags.original_tags.length > 0
          ? data.articleReview.tags.original_tags
          : (data as any).tags) || [],
      faqSuggestions:
        (metadata?.faq_suggestions as Array<{ question: string; answer: string }>) || [],
    };
  }, [data]);

  // BUGFIX: Use useRef to capture the FIRST NON-EMPTY extracted values
  // This prevents the "switch content corruption" bug
  // Key insight: We only lock in the values when meta_description has actual content
  const originalExtractedRef = useRef<{
    metaDescription: string;
    seoKeywords: string[];
    tags: string[];
    isLocked: boolean;
  }>({
    metaDescription: '',
    seoKeywords: [],
    tags: [],
    isLocked: false,
  });

  // Lock in values when we have real data (non-empty meta_description)
  // Once locked, these values NEVER change
  if (!originalExtractedRef.current.isLocked && data.meta_description) {
    originalExtractedRef.current = {
      metaDescription: data.meta_description,
      seoKeywords: data.seo_keywords || [],
      tags: (data as any).tags || [],
      isLocked: true, // Mark as locked - will never update again
    };
    console.log('[ParsingReviewPanel] LOCKED originalExtracted:', {
      metaDescription: data.meta_description.slice(0, 50),
      seoKeywordsCount: originalExtractedRef.current.seoKeywords.length,
      tagsCount: originalExtractedRef.current.tags.length,
    });
  }

  // Provide access to the locked values (or empty defaults if not yet locked)
  const originalExtracted = originalExtractedRef.current;

  const [title, setTitle] = useState(initialParsingState.title);
  const [author, setAuthor] = useState(initialParsingState.author);
  const [featuredImage, setFeaturedImage] = useState(initialParsingState.featuredImage);
  const [additionalImages, setAdditionalImages] = useState<string[]>(initialParsingState.additionalImages);
  const [metaDescription, setMetaDescription] = useState(initialParsingState.metaDescription);
  const [seoKeywords, setSeoKeywords] = useState<string[]>(initialParsingState.seoKeywords);
  const [tags, setTags] = useState<string[]>(initialParsingState.tags);

  // ============================================================
  // BUGFIX: FAQ State - Use lifted state if available (for backtrack persistence)
  // Fallback to local state for backwards compatibility
  // ============================================================
  const [localFaqSuggestions, setLocalFaqSuggestions] = useState<Array<{ question: string; answer: string }>>(
    initialParsingState.faqSuggestions
  );
  // Use lifted state if provided, otherwise fall back to local state
  const faqSuggestions = liftedFaqs ?? localFaqSuggestions;
  const setFaqSuggestions = useCallback((newFaqs: Array<{ question: string; answer: string }>) => {
    // Update both local and lifted state
    setLocalFaqSuggestions(newFaqs);
    if (onLiftedFaqsChange) {
      onLiftedFaqsChange(newFaqs);
    }
  }, [onLiftedFaqsChange]);

  // Phase 8.3: Content comparison source tracking
  const [metaDescriptionSource, setMetaDescriptionSource] = useState<ContentSource>('extracted');
  const [keywordsSource, setKeywordsSource] = useState<KeywordSource>('extracted');
  const [tagsSource, setTagsSource] = useState<TagSource>('extracted');

  // Phase 9: SEO Title state
  const [seoTitleSuggestions, setSeoTitleSuggestions] = useState<SEOTitleSuggestionsData | null>(null);
  const [currentSeoTitle, setCurrentSeoTitle] = useState<string | null>(null);
  const [seoTitleSource, setSeoTitleSource] = useState<string | null>(null);
  const [isLoadingSeoTitle, setIsLoadingSeoTitle] = useState(false);

  // Phase 9.2: AI FAQ state
  const [aiFaqSuggestions, setAiFaqSuggestions] = useState<AIFAQSuggestion[]>([]);
  const [isGeneratingFaqs, setIsGeneratingFaqs] = useState(false);
  const [faqError, setFaqError] = useState<string | null>(null);

  // Phase 11: Category state (moved from PublishPreviewPanel)
  const [primaryCategory, setPrimaryCategory] = useState<string | null>(
    (data as any).primary_category || null
  );
  const [secondaryCategories, setSecondaryCategories] = useState<string[]>(
    (data as any).secondary_categories || []
  );
  const [aiCategoryRecommendation, setAiCategoryRecommendation] = useState<AICategoryRecommendation | null>(null);
  const [aiSecondaryRecommendations, setAiSecondaryRecommendations] = useState<AISecondaryCategoryRecommendation[]>([]);
  const [isLoadingCategoryRecommendation, setIsLoadingCategoryRecommendation] = useState(false);

  // Phase 11: Excerpt state (moved from PublishPreviewPanel)
  const [excerpt, setExcerpt] = useState<string>(
    (data.metadata?.excerpt as string) || ''
  );

  // Phase 12: AI Tags and Excerpt suggestions
  const [aiSuggestedTags, setAiSuggestedTags] = useState<SuggestedTag[]>([]);
  const [aiTagStrategy, setAiTagStrategy] = useState<string | null>(null);
  const [aiSuggestedExcerpt, setAiSuggestedExcerpt] = useState<string | null>(null);
  const [isLoadingAiOptimizations, setIsLoadingAiOptimizations] = useState(false);

  // Track if data has been modified
  const [isDirty, setIsDirty] = useState(false);

  // Sync parsing data when source changes and form is pristine
  useEffect(() => {
    if (!isDirty) {
      setTitle(initialParsingState.title);
      setAuthor(initialParsingState.author);
      setFeaturedImage(initialParsingState.featuredImage);
      setAdditionalImages(initialParsingState.additionalImages);
      setMetaDescription(initialParsingState.metaDescription);
      setSeoKeywords(initialParsingState.seoKeywords);
      setTags(initialParsingState.tags);
      // BUGFIX: Only reset local FAQ state if lifted state is not provided
      // This prevents overwriting persisted lifted state during navigation
      if (!liftedFaqs) {
        setLocalFaqSuggestions(initialParsingState.faqSuggestions);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialParsingState, isDirty, liftedFaqs]);

  // Fetch SEO Title suggestions and AI FAQ suggestions when component mounts (if articleId exists)
  useEffect(() => {
    const fetchOptimizations = async () => {
      if (!data.article_id) {
        return;
      }

      setIsLoadingSeoTitle(true);
      try {
        // Fetch optimizations (which includes SEO Title suggestions, Tags, Excerpt, and FAQs)
        setIsLoadingAiOptimizations(true);
        try {
          const optimizationsData = await api.get<{
            title_suggestions?: { seo_title_suggestions?: SEOTitleSuggestionsData };
            seo_suggestions?: {
              tags?: {
                suggested_tags?: Array<{
                  tag: string;
                  relevance: number;
                  type: 'primary' | 'secondary' | 'trending';
                }>;
                tag_strategy?: string;
              };
              meta_description?: {
                suggested_meta_description?: string;
              };
            };
            faqs?: AIFAQSuggestion[];
          }>(`/v1/articles/${data.article_id}/optimizations`);

          // Extract SEO Title suggestions
          if (optimizationsData.title_suggestions?.seo_title_suggestions) {
            setSeoTitleSuggestions(optimizationsData.title_suggestions.seo_title_suggestions);
          }

          // Phase 12: Extract AI Tags suggestions
          if (optimizationsData.seo_suggestions?.tags?.suggested_tags) {
            const tags = optimizationsData.seo_suggestions.tags.suggested_tags.map(t => ({
              tag: t.tag,
              relevance: t.relevance,
              type: t.type,
            }));
            setAiSuggestedTags(tags);
            console.log('[ParsingReviewPanel] AI Tags loaded:', tags.length);
          }
          if (optimizationsData.seo_suggestions?.tags?.tag_strategy) {
            setAiTagStrategy(optimizationsData.seo_suggestions.tags.tag_strategy);
          }

          // Phase 12: Extract AI Excerpt suggestion (from meta_description optimization)
          if (optimizationsData.seo_suggestions?.meta_description?.suggested_meta_description) {
            // Meta description can be used as a base for excerpt
            // For now, we'll use it directly as AI suggested excerpt
            setAiSuggestedExcerpt(optimizationsData.seo_suggestions.meta_description.suggested_meta_description);
            console.log('[ParsingReviewPanel] AI Excerpt loaded');
          }

          // Extract AI FAQ suggestions (Phase 9.2)
          if (optimizationsData.faqs && Array.isArray(optimizationsData.faqs)) {
            setAiFaqSuggestions(optimizationsData.faqs);
          }
        } catch (err: unknown) {
          // 404 is expected if optimizations haven't been generated yet
          const axiosErr = err as { response?: { status?: number } };
          if (axiosErr.response?.status !== 404) {
            console.error('Failed to fetch optimizations:', err);
          }
        } finally {
          setIsLoadingAiOptimizations(false);
        }

        // Fetch current article data to get current SEO Title
        try {
          const articleData = await api.get<{
            seo_title?: string;
            seo_title_source?: string;
          }>(`/v1/articles/${data.article_id}`);
          setCurrentSeoTitle(articleData.seo_title ?? null);
          setSeoTitleSource(articleData.seo_title_source ?? null);
        } catch (err) {
          console.error('Error fetching article data:', err);
        }

        // Phase 11: Fetch AI category recommendation
        if (!primaryCategory) {
          setIsLoadingCategoryRecommendation(true);
          try {
            const categoryData = await api.post<{
              primary_category: string;
              confidence: number;
              reasoning: string;
              alternative_categories?: Array<{ category: string; confidence: number; reason: string }>;
              content_analysis?: string;
              cached?: boolean;
            }>(`/v1/articles/${data.article_id}/recommend-category`, {});

            setAiCategoryRecommendation({
              category: categoryData.primary_category,
              confidence: categoryData.confidence,
              reasoning: categoryData.reasoning,
            });

            // Set secondary category recommendations from alternative_categories
            if (categoryData.alternative_categories && categoryData.alternative_categories.length > 0) {
              const secondaryRecs = categoryData.alternative_categories.map((alt) => ({
                category: alt.category,
                confidence: alt.confidence,
                reasoning: alt.reason,
              }));
              setAiSecondaryRecommendations(secondaryRecs);
            }

            console.log('AI Category recommendation:', categoryData);
          } catch (err: unknown) {
            const axiosErr = err as { response?: { status?: number } };
            if (axiosErr.response?.status !== 404) {
              console.error('Error fetching category recommendation:', err);
            }
          } finally {
            setIsLoadingCategoryRecommendation(false);
          }
        }
      } catch (error) {
        console.error('Error fetching optimization data:', error);
      } finally {
        setIsLoadingSeoTitle(false);
      }
    };

    fetchOptimizations();
  }, [data.article_id, primaryCategory]);

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

  // Phase 9.2: Generate AI FAQs
  const handleGenerateFaqs = useCallback(async () => {
    if (!data.article_id) {
      setFaqError('無法生成 FAQ：缺少文章 ID');
      return;
    }

    setIsGeneratingFaqs(true);
    setFaqError(null);

    try {
      // Call the generate-all-optimizations endpoint using api client
      // Use longer timeout (2 min) for AI generation which can take a while
      const optimizationsData = await api.post<{
        faqs?: AIFAQSuggestion[];
      }>(
        `/v1/articles/${data.article_id}/generate-all-optimizations`,
        {
          regenerate: true,
          options: {
            include_title: false,
            include_seo: false,
            include_tags: false,
            include_faqs: true,
            faq_target_count: 8,
          },
        },
        { timeout: 120000 } // 2 minute timeout for AI generation
      );

      // Extract AI FAQ suggestions
      if (optimizationsData.faqs && Array.isArray(optimizationsData.faqs)) {
        setAiFaqSuggestions(optimizationsData.faqs);
      } else {
        setFaqError('未能獲取 FAQ 建議');
      }
    } catch (error: unknown) {
      console.error('Error generating FAQs:', error);
      const axiosErr = error as {
        response?: { data?: { detail?: string }; status?: number };
        code?: string;
        message?: string;
      };

      // Provide more helpful error messages
      let errorMessage: string;
      if (axiosErr.code === 'ECONNABORTED' || axiosErr.message?.includes('timeout')) {
        errorMessage = 'AI 生成超時，請稍後重試';
      } else if (axiosErr.response?.data?.detail) {
        errorMessage = axiosErr.response.data.detail;
      } else if (axiosErr.response?.status === 500) {
        errorMessage = '伺服器內部錯誤，請稍後重試或聯繫管理員';
      } else if (axiosErr.response?.status) {
        errorMessage = `生成失敗: ${axiosErr.response.status}`;
      } else {
        errorMessage = '生成 FAQ 時發生錯誤，請檢查網路連線';
      }
      setFaqError(errorMessage);
    } finally {
      setIsGeneratingFaqs(false);
    }
  }, [data.article_id]);

  // Handle SEO Title selection success
  const handleSeoTitleSelectionSuccess = (response: SelectSEOTitleResponse) => {
    setCurrentSeoTitle(response.seo_title);
    setSeoTitleSource(response.seo_title_source);
    // TODO: Show success toast notification
    console.log('SEO Title selected successfully:', response);
  };

  // Handle SEO Title selection error
  const handleSeoTitleSelectionError = (error: Error) => {
    // TODO: Show error toast notification
    console.error('Failed to select SEO Title:', error);
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

      {/* Main content: 3-column grid (33% + 34% + 33%) */}
      <div
        className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 overflow-auto"
        data-testid="parsing-review-grid"
      >
        {/* Left column: 33% (4 out of 12 cols) - Title, SEO Title, Author */}
        <div className="lg:col-span-4 space-y-4">
          {/* Title Review */}
          <Card className="p-4" data-testid="parsing-title-card">
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

          {/* Phase 9: SEO Title Selection */}
          {data.article_id && (
            <SEOTitleSelectionCard
              articleId={data.article_id}
              currentSeoTitle={currentSeoTitle}
              seoTitleSource={seoTitleSource}
              suggestions={seoTitleSuggestions}
              articleTitle={title}
              isLoading={isLoadingSeoTitle}
              onSelectionSuccess={handleSeoTitleSelectionSuccess}
              onError={handleSeoTitleSelectionError}
            />
          )}

          {/* Author Review */}
          <Card className="p-4" data-testid="parsing-author-card">
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
          <Card className="p-4" data-testid="parsing-image-card">
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

        {/* Center column: 34% (4 out of 12 cols) - SEO Optimization */}
        <div className="lg:col-span-4 space-y-4">
          {/* Meta Description Comparison */}
          <ContentComparisonCard
            title="元描述 (Meta Description)"
            extractedContent={originalExtracted.metaDescription}
            aiSuggestedContent={data.articleReview?.meta?.suggested || ''}
            selectedSource={metaDescriptionSource}
            customContent={metaDescriptionSource === 'custom' ? metaDescription : undefined}
            onSourceChange={(source, content) => {
              setMetaDescriptionSource(source);
              setMetaDescription(content);
              markDirty();
            }}
            onCustomContentChange={(content) => {
              setMetaDescription(content);
              markDirty();
            }}
            optimalLength={[120, 160]}
            aiReasoning={data.articleReview?.meta?.reasoning || undefined}
            testId="meta-description-comparison"
          />

          {/* Keywords Comparison */}
          <KeywordsComparisonCard
            extractedKeywords={originalExtracted.seoKeywords}
            aiSuggestedKeywords={data.articleReview?.seo?.suggested_keywords || undefined}
            selectedSource={keywordsSource}
            activeKeywords={seoKeywords}
            onKeywordsChange={(source, keywords) => {
              setKeywordsSource(source);
              setSeoKeywords(keywords);
              markDirty();
            }}
            optimalCount={[5, 10]}
            aiReasoning={data.articleReview?.seo?.reasoning || undefined}
            testId="keywords-comparison"
          />

          {/* SEO Score Summary */}
          <Card className="p-3 bg-gradient-to-br from-slate-50 to-blue-50 border-slate-200" data-testid="seo-score-summary">
            <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              SEO 评分概览
            </h4>
            <div className="grid grid-cols-4 gap-2">
              <div className="text-center p-1.5 bg-white rounded border">
                <div className={`text-base font-bold ${metaDescription.length >= 120 && metaDescription.length <= 160 ? 'text-green-600' : 'text-amber-600'}`}>
                  {metaDescription.length >= 120 && metaDescription.length <= 160 ? '✓' : '⚠'}
                </div>
                <div className="text-[10px] text-slate-600">元描述</div>
              </div>
              <div className="text-center p-1.5 bg-white rounded border">
                {/* Keywords score: Use AI quality score when AI keywords selected, otherwise use count-based */}
                {keywordsSource === 'ai' && data.articleReview?.seo?.score != null ? (
                  <>
                    <div className={`text-base font-bold ${data.articleReview.seo.score >= 0.7 ? 'text-green-600' : data.articleReview.seo.score >= 0.5 ? 'text-amber-600' : 'text-red-600'}`}>
                      {Math.round(data.articleReview.seo.score * 100)}
                    </div>
                    <div className="text-[10px] text-emerald-600">AI优化</div>
                  </>
                ) : (
                  <>
                    <div className={`text-base font-bold ${seoKeywords.length >= 5 && seoKeywords.length <= 10 ? 'text-green-600' : 'text-amber-600'}`}>
                      {seoKeywords.length >= 5 && seoKeywords.length <= 10 ? '✓' : '⚠'}
                    </div>
                    <div className="text-[10px] text-slate-600">关键词</div>
                  </>
                )}
              </div>
              <div className="text-center p-1.5 bg-white rounded border">
                <div className={`text-base font-bold ${tags.length >= 3 && tags.length <= 6 ? 'text-green-600' : 'text-amber-600'}`}>
                  {tags.length >= 3 && tags.length <= 6 ? '✓' : '⚠'}
                </div>
                <div className="text-[10px] text-slate-600">标签</div>
              </div>
              <div className="text-center p-1.5 bg-white rounded border">
                {/* Total score: Factor in AI quality when using AI keywords */}
                <div className="text-base font-bold text-blue-600">
                  {Math.round(
                    ((metaDescription.length >= 120 ? 33 : metaDescription.length / 3.6) +
                    (keywordsSource === 'ai' && data.articleReview?.seo?.score != null
                      ? data.articleReview.seo.score * 33  // Use AI quality score (0-1) * 33
                      : (seoKeywords.length >= 5 ? 33 : seoKeywords.length * 6.6)) +
                    (tags.length >= 3 ? 34 : tags.length * 11.3))
                  )}
                </div>
                <div className="text-[10px] text-slate-600">总分</div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right column: 33% (4 out of 12 cols) - Categories & Tags */}
        <div className="lg:col-span-4 space-y-4">
          {/* Category Selection with AI Recommendation */}
          <CategorySelectionCard
            aiRecommendation={aiCategoryRecommendation || undefined}
            aiSecondaryRecommendations={aiSecondaryRecommendations.length > 0 ? aiSecondaryRecommendations : undefined}
            primaryCategory={primaryCategory}
            secondaryCategories={secondaryCategories}
            onPrimaryCategoryChange={(cat) => {
              setPrimaryCategory(cat);
              markDirty();
            }}
            onSecondaryCategoriesChange={(cats) => {
              setSecondaryCategories(cats);
              markDirty();
            }}
            isLoading={isLoadingCategoryRecommendation}
            testId="category-selection"
          />

          {/* Tags Comparison - Phase 12: Priority: aiSuggestedTags from optimizations > articleReview.tags */}
          <TagsComparisonCard
            extractedTags={originalExtracted.tags}
            aiSuggestedTags={
              aiSuggestedTags.length > 0
                ? aiSuggestedTags
                : data.articleReview?.tags?.suggested_tags || undefined
            }
            selectedSource={tagsSource}
            activeTags={tags}
            onTagsChange={(source, newTags) => {
              setTagsSource(source);
              setTags(newTags);
              markDirty();
            }}
            optimalCount={[3, 6]}
            aiStrategy={aiTagStrategy || data.articleReview?.tags?.tag_strategy || undefined}
            testId="tags-comparison"
          />

          {/* Excerpt Review - Phase 12: Add AI suggested excerpt */}
          <ExcerptReviewSection
            excerpt={excerpt}
            articleBody={data.articleReview?.content?.original || ''}
            aiSuggestedExcerpt={aiSuggestedExcerpt || undefined}
            onExcerptChange={(newExcerpt) => {
              setExcerpt(newExcerpt);
              markDirty();
            }}
            optimalLength={[100, 200]}
            isGenerating={isLoadingAiOptimizations}
            testId="excerpt-review"
          />
        </div>

        {/* Bottom row: FAQ (full width) */}
        <div className="lg:col-span-12 space-y-4">
          {/* AI FAQ Proposals (if available from article review) */}
          {data.articleReview?.faq_proposals && data.articleReview.faq_proposals.length > 0 && (
            <Card className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
              <h4 className="text-sm font-semibold text-purple-900 mb-3 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                AI 建议：FAQ Schema ({data.articleReview.faq_proposals.length} 个提案)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {data.articleReview.faq_proposals.map((proposal, idx) => (
                  <div key={idx} className="p-3 bg-white rounded border border-purple-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-purple-700">
                        提案 #{idx + 1} - {proposal.schema_type}
                      </span>
                      {proposal.score !== null && proposal.score !== undefined && (
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                          评分: {Math.round(proposal.score * 100)}
                        </span>
                      )}
                    </div>
                    <div className="space-y-2">
                      {proposal.questions.map((q, qIdx) => (
                        <div key={qIdx} className="text-xs">
                          <p className="font-medium text-gray-900">Q{qIdx + 1}: {q.question}</p>
                          <p className="text-gray-600 ml-4 mt-1">A: {q.answer}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* FAQ Review - AI FAQs are auto-generated during parsing */}
          <Card className="p-4" data-testid="parsing-faq-card">
            <FAQReviewSection
              articleId={data.article_id}
              faqs={faqSuggestions}
              aiSuggestions={aiFaqSuggestions}
              isGenerating={isGeneratingFaqs}
              error={faqError}
              onFaqsChange={(faqs) => {
                setFaqSuggestions(faqs);
                markDirty();
              }}
            />
          </Card>

          {/* Phase 12: Related Articles for Internal Linking */}
          {data.articleReview?.related_articles && data.articleReview.related_articles.length > 0 && (
            <Card className="p-4 bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200" data-testid="related-articles-card">
              <h4 className="text-sm font-semibold text-emerald-900 mb-3 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                相關文章推薦 ({data.articleReview.related_articles.length} 篇)
                <span className="ml-auto text-xs text-emerald-600 font-normal">
                  用於內部鏈接優化 SEO
                </span>
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {data.articleReview.related_articles.map((article, idx) => (
                  <div key={article.article_id} className="p-3 bg-white rounded-lg border border-emerald-200 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className="text-xs font-mono text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">
                        #{idx + 1}
                      </span>
                      <div className="flex items-center gap-1">
                        <span className={`text-xs px-1.5 py-0.5 rounded ${
                          article.match_type === 'semantic'
                            ? 'bg-purple-100 text-purple-700'
                            : article.match_type === 'content'
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}>
                          {article.match_type === 'semantic' ? '語義匹配' : article.match_type === 'content' ? '內容匹配' : '關鍵詞匹配'}
                        </span>
                        <span className="text-xs font-semibold text-emerald-700">
                          {Math.round(article.similarity * 100)}%
                        </span>
                      </div>
                    </div>
                    <h5 className="text-sm font-medium text-gray-900 line-clamp-2 mb-2">
                      {article.title_main || article.title}
                    </h5>
                    {article.excerpt && (
                      <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                        {article.excerpt}
                      </p>
                    )}
                    {article.ai_keywords && article.ai_keywords.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        {article.ai_keywords.slice(0, 3).map((keyword, kIdx) => (
                          <span key={kIdx} className="text-[10px] px-1 py-0.5 bg-gray-100 text-gray-600 rounded">
                            {keyword}
                          </span>
                        ))}
                        {article.ai_keywords.length > 3 && (
                          <span className="text-[10px] text-gray-400">+{article.ai_keywords.length - 3}</span>
                        )}
                      </div>
                    )}
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-emerald-600 hover:text-emerald-800 hover:underline flex items-center gap-1"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      查看原文
                    </a>
                  </div>
                ))}
              </div>
            </Card>
          )}
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
