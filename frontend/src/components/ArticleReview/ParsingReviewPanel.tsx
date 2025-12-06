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

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Card } from '../ui';
import { Button } from '../ui';
import { TitleReviewSection } from './TitleReviewSection';
import { SEOTitleSelectionCard } from './SEOTitleSelectionCard';
import { AuthorReviewSection } from './AuthorReviewSection';
import { ImageReviewSection } from './ImageReviewSection';
import { ContentComparisonCard, ContentSource } from './ContentComparisonCard';
import { KeywordsComparisonCard, KeywordSource } from './KeywordsComparisonCard';
import { FAQReviewSection, type AIFAQSuggestion } from './FAQReviewSection';
import type { ArticleReviewData } from '../../hooks/articleReview/useArticleReviewData';
import type { SEOTitleSuggestionsData, SelectSEOTitleResponse } from '../../types/api';
import { api } from '../../services/api-client';

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
      // HOTFIX-PARSE-001: Use author_name from parsing, fallback to author
      author: (data as any).author_name || data.author || '',
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
      faqSuggestions:
        (metadata?.faq_suggestions as Array<{ question: string; answer: string }>) || [],
    };
  }, [data]);

  const [title, setTitle] = useState(initialParsingState.title);
  const [author, setAuthor] = useState(initialParsingState.author);
  const [featuredImage, setFeaturedImage] = useState(initialParsingState.featuredImage);
  const [additionalImages, setAdditionalImages] = useState<string[]>(initialParsingState.additionalImages);
  const [metaDescription, setMetaDescription] = useState(initialParsingState.metaDescription);
  const [seoKeywords, setSeoKeywords] = useState<string[]>(initialParsingState.seoKeywords);
  const [faqSuggestions, setFaqSuggestions] = useState<Array<{ question: string; answer: string }>>(
    initialParsingState.faqSuggestions
  );

  // Phase 8.3: Content comparison source tracking
  const [metaDescriptionSource, setMetaDescriptionSource] = useState<ContentSource>('extracted');
  const [keywordsSource, setKeywordsSource] = useState<KeywordSource>('extracted');

  // Phase 9: SEO Title state
  const [seoTitleSuggestions, setSeoTitleSuggestions] = useState<SEOTitleSuggestionsData | null>(null);
  const [currentSeoTitle, setCurrentSeoTitle] = useState<string | null>(null);
  const [seoTitleSource, setSeoTitleSource] = useState<string | null>(null);
  const [isLoadingSeoTitle, setIsLoadingSeoTitle] = useState(false);

  // Phase 9.2: AI FAQ state
  const [aiFaqSuggestions, setAiFaqSuggestions] = useState<AIFAQSuggestion[]>([]);
  const [isGeneratingFaqs, setIsGeneratingFaqs] = useState(false);
  const [faqError, setFaqError] = useState<string | null>(null);

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
      setFaqSuggestions(initialParsingState.faqSuggestions);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialParsingState, isDirty]);

  // Fetch SEO Title suggestions and AI FAQ suggestions when component mounts (if articleId exists)
  useEffect(() => {
    const fetchOptimizations = async () => {
      if (!data.article_id) {
        return;
      }

      setIsLoadingSeoTitle(true);
      try {
        // Fetch optimizations (which includes SEO Title suggestions and FAQs)
        try {
          const optimizationsData = await api.get<{
            title_suggestions?: { seo_title_suggestions?: SEOTitleSuggestionsData };
            faqs?: AIFAQSuggestion[];
          }>(`/v1/articles/${data.article_id}/optimizations`);

          // Extract SEO Title suggestions
          if (optimizationsData.title_suggestions?.seo_title_suggestions) {
            setSeoTitleSuggestions(optimizationsData.title_suggestions.seo_title_suggestions);
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
      } catch (error) {
        console.error('Error fetching optimization data:', error);
      } finally {
        setIsLoadingSeoTitle(false);
      }
    };

    fetchOptimizations();
  }, [data.article_id]);

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

      {/* Main content: 60% + 40% grid */}
      <div
        className="flex-1 grid grid-cols-1 lg:grid-cols-5 gap-6 overflow-auto"
        data-testid="parsing-review-grid"
      >
        {/* Left column: 60% (3 out of 5 cols) */}
        <div className="lg:col-span-3 space-y-6">
          {/* Title Review */}
          <Card className="p-6" data-testid="parsing-title-card">
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

          {/* Phase 9: SEO Title Selection - Side-by-side comparison layout */}
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
          <Card className="p-6" data-testid="parsing-author-card">
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
          <Card className="p-6" data-testid="parsing-image-card">
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
          {/* Phase 8.3: Meta Description Comparison Card */}
          <ContentComparisonCard
            title="元描述 (Meta Description)"
            extractedContent={metaDescription}
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

          {/* Phase 8.3: Keywords Comparison Card */}
          <KeywordsComparisonCard
            extractedKeywords={seoKeywords}
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

          {/* SEO Score Summary - Simplified */}
          <Card className="p-4 bg-gradient-to-br from-slate-50 to-blue-50 border-slate-200" data-testid="seo-score-summary">
            <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              SEO 评分概览
            </h4>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-2 bg-white rounded border">
                <div className={`text-lg font-bold ${metaDescription.length >= 120 && metaDescription.length <= 160 ? 'text-green-600' : 'text-amber-600'}`}>
                  {metaDescription.length >= 120 && metaDescription.length <= 160 ? '✓' : '⚠'}
                </div>
                <div className="text-xs text-slate-600">元描述</div>
                <div className="text-xs text-slate-400">{metaDescription.length}/120-160</div>
              </div>
              <div className="text-center p-2 bg-white rounded border">
                <div className={`text-lg font-bold ${seoKeywords.length >= 5 && seoKeywords.length <= 10 ? 'text-green-600' : 'text-amber-600'}`}>
                  {seoKeywords.length >= 5 && seoKeywords.length <= 10 ? '✓' : '⚠'}
                </div>
                <div className="text-xs text-slate-600">关键词</div>
                <div className="text-xs text-slate-400">{seoKeywords.length}/5-10个</div>
              </div>
              <div className="text-center p-2 bg-white rounded border">
                <div className="text-lg font-bold text-blue-600">
                  {Math.round(((metaDescription.length >= 120 ? 50 : metaDescription.length / 2.4) + (seoKeywords.length >= 5 ? 50 : seoKeywords.length * 10)))}
                </div>
                <div className="text-xs text-slate-600">总分</div>
                <div className="text-xs text-slate-400">/100</div>
              </div>
            </div>
          </Card>

          {/* AI FAQ Proposals (if available from article review) */}
          {data.articleReview?.faq_proposals && data.articleReview.faq_proposals.length > 0 && (
            <Card className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
              <h4 className="text-sm font-semibold text-purple-900 mb-3 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                AI 建议：FAQ Schema ({data.articleReview.faq_proposals.length} 个提案)
              </h4>
              <div className="space-y-3">
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

          {/* FAQ Review - Phase 9.2: AI-powered FAQ generation */}
          <Card className="p-6" data-testid="parsing-faq-card">
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
              onGenerateFaqs={handleGenerateFaqs}
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
