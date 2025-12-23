/**
 * Article parsing service for Phase 7.
 *
 * Provides API calls for:
 * - Parsing articles (AI or heuristic)
 * - Retrieving parsing results
 * - Confirming parsed data
 * - Reviewing and managing images
 */

import { api } from './api-client';

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Parse article request parameters.
 */
export interface ParseArticleRequest {
  use_ai?: boolean;
  download_images?: boolean;
  fallback_to_heuristic?: boolean;
}

/**
 * Parse article response.
 */
export interface ParseArticleResponse {
  success: boolean;
  article_id: number;
  parsing_method?: 'ai' | 'heuristic';
  parsing_confidence?: number;
  images_processed: number;
  duration_ms: number;
  warnings: string[];
  errors: string[];
}

/**
 * Parsed article data.
 */
export interface ParsedArticleData {
  // Title components
  title_prefix?: string;
  title_main: string;
  title_suffix?: string;
  full_title: string;

  // Author info
  author_line?: string;
  author_name?: string;

  // Content
  body_html: string;
  meta_description?: string;
  seo_keywords: string[];

  // Parsing metadata
  parsing_method: string;
  parsing_confidence: number;
  parsing_confirmed: boolean;
  has_seo_data: boolean;

  // Images
  images: ArticleImage[];

  // Related articles for internal linking (Phase 12)
  related_articles: RelatedArticle[];

  // FAQ v2.2 Assessment Fields (Phase 13)
  faq_applicable?: boolean | null;
  faq_assessment?: {
    is_applicable: boolean;
    reason: string;
    target_pain_points?: string[];
  } | null;
  faq_html?: string | null;
  body_html_with_faq?: string | null;
}

/**
 * Article image data.
 */
export interface ArticleImage {
  id: number;
  position: number;
  source_url?: string;
  preview_path?: string;
  caption?: string;
  width?: number;
  height?: number;
  format?: string;
  file_size_bytes?: number;
}

/**
 * Related article for internal linking (Phase 12).
 */
export interface RelatedArticle {
  article_id: string;
  title: string;
  title_main?: string;
  url: string;
  excerpt?: string;
  similarity: number;
  match_type: 'semantic' | 'content' | 'keyword';
  ai_keywords: string[];
}

/**
 * Confirm parsing request.
 */
export interface ConfirmParsingRequest {
  confirmed_by: string;
  feedback?: string;
}

/**
 * Confirm parsing response.
 */
export interface ConfirmParsingResponse {
  success: boolean;
  article_id: number;
  confirmed_at: string;
  confirmed_by: string;
}

/**
 * Image review action types.
 */
export type ImageReviewAction =
  | 'keep'
  | 'remove'
  | 'replace_caption'
  | 'replace_source';

/**
 * Image review request.
 */
export interface ImageReviewRequest {
  action: ImageReviewAction;
  new_caption?: string;
  new_source_url?: string;
}

/**
 * Image review response.
 */
export interface ImageReviewResponse {
  success: boolean;
  image_id: number;
  action: string;
  review_id: number;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Parse an article to extract structured data.
 *
 * @param articleId - Article ID to parse
 * @param params - Parsing parameters
 * @returns Parse result with metadata
 *
 * @example
 * ```ts
 * const result = await parseArticle(123, {
 *   use_ai: true,
 *   download_images: true
 * });
 * console.log(`Parsed with ${result.parsing_method}`);
 * ```
 */
export async function parseArticle(
  articleId: number,
  params: ParseArticleRequest = {}
): Promise<ParseArticleResponse> {
  return api.post<ParseArticleResponse>(
    `/v1/articles/${articleId}/parse`,
    {
      use_ai: params.use_ai ?? true,
      download_images: params.download_images ?? true,
      fallback_to_heuristic: params.fallback_to_heuristic ?? true,
    }
  );
}

/**
 * Get parsing result for an article.
 *
 * @param articleId - Article ID
 * @returns Parsed article data
 *
 * @example
 * ```ts
 * const data = await getParsingResult(123);
 * console.log(data.full_title);
 * console.log(`Images: ${data.images.length}`);
 * ```
 */
export async function getParsingResult(
  articleId: number
): Promise<ParsedArticleData> {
  return api.get<ParsedArticleData>(
    `/v1/articles/${articleId}/parsing-result`
  );
}

/**
 * Confirm that parsed article data is correct.
 *
 * @param articleId - Article ID
 * @param params - Confirmation parameters
 * @returns Confirmation result
 *
 * @example
 * ```ts
 * await confirmParsing(123, {
 *   confirmed_by: 'john_doe',
 *   feedback: 'All data looks good'
 * });
 * ```
 */
export async function confirmParsing(
  articleId: number,
  params: ConfirmParsingRequest
): Promise<ConfirmParsingResponse> {
  return api.post<ConfirmParsingResponse>(
    `/v1/articles/${articleId}/confirm-parsing`,
    params
  );
}

/**
 * Get all images for an article.
 *
 * @param articleId - Article ID
 * @returns List of article images
 *
 * @example
 * ```ts
 * const images = await getArticleImages(123);
 * images.forEach(img => {
 *   console.log(`${img.position}: ${img.caption}`);
 * });
 * ```
 */
export async function getArticleImages(
  articleId: number
): Promise<ArticleImage[]> {
  return api.get<ArticleImage[]>(
    `/v1/articles/${articleId}/images`
  );
}

/**
 * Review and take action on an image.
 *
 * @param articleId - Article ID
 * @param imageId - Image ID
 * @param params - Review action parameters
 * @returns Review result
 *
 * @example
 * ```ts
 * // Replace caption
 * await reviewImage(123, 456, {
 *   action: 'replace_caption',
 *   new_caption: 'Updated caption'
 * });
 *
 * // Remove image
 * await reviewImage(123, 457, {
 *   action: 'remove'
 * });
 * ```
 */
export async function reviewImage(
  articleId: number,
  imageId: number,
  params: ImageReviewRequest
): Promise<ImageReviewResponse> {
  return api.post<ImageReviewResponse>(
    `/v1/articles/${articleId}/images/${imageId}/review`,
    params
  );
}

// ============================================================================
// React Query Hook Helpers
// ============================================================================

/**
 * Query key factory for parsing-related queries.
 */
export const parsingKeys = {
  all: ['parsing'] as const,
  article: (articleId: number) => ['parsing', 'article', articleId] as const,
  result: (articleId: number) => ['parsing', 'result', articleId] as const,
  images: (articleId: number) => ['parsing', 'images', articleId] as const,
  optimizations: (articleId: number) => ['parsing', 'optimizations', articleId] as const,
  optimizationStatus: (articleId: number) => ['parsing', 'optimization-status', articleId] as const,
};

/**
 * Default React Query options for parsing mutations.
 */
export const parsingMutationOptions = {
  retry: false, // Don't retry parsing automatically
  onError: (error: Error) => {
    console.error('Parsing error:', error);
  },
};

// ============================================================================
// Unified AI Optimization Types & Functions (Phase 7)
// ============================================================================

/**
 * Title optimization option.
 */
export interface TitleOption {
  id: string;
  title_prefix?: string | null;
  title_main: string;
  title_suffix?: string | null;
  full_title: string;
  score: number;
  strengths: string[];
  type: string;
  recommendation: string;
  character_count: {
    prefix: number;
    main: number;
    suffix: number;
    total: number;
  };
}

/**
 * FAQ data.
 */
export interface FAQData {
  question: string;
  answer: string;
  question_type?: string | null;
  search_intent?: string | null;
  keywords_covered: string[];
  confidence?: number | null;
}

/**
 * Tag suggestion.
 */
export interface TagSuggestion {
  tag: string;
  relevance: number;
  type: string;
}

/**
 * Unified optimizations response.
 */
export interface OptimizationsResponse {
  title_suggestions: {
    suggested_title_sets: TitleOption[];
    optimization_notes: string[];
  };
  seo_suggestions: {
    seo_keywords: {
      focus_keyword?: string | null;
      focus_keyword_rationale?: string | null;
      primary_keywords: string[];
      secondary_keywords: string[];
      keyword_difficulty?: any;
      search_volume_estimate?: any;
    };
    meta_description: {
      original_meta_description?: string | null;
      suggested_meta_description?: string | null;
      meta_description_improvements: string[];
      meta_description_score?: number | null;
    };
    tags: {
      suggested_tags: TagSuggestion[];
      recommended_tag_count?: string | null;
      tag_strategy?: string | null;
    };
  };
  faqs: FAQData[];
  generation_metadata: {
    total_cost_usd?: number | null;
    total_tokens?: number | null;
    input_tokens?: number | null;
    output_tokens?: number | null;
    duration_ms?: number | null;
    cached: boolean;
    message?: string | null;
  };
}

/**
 * Generate optimizations request.
 */
export interface GenerateOptimizationsRequest {
  regenerate?: boolean;
  options?: {
    include_title?: boolean;
    include_seo?: boolean;
    include_tags?: boolean;
    include_faqs?: boolean;
    faq_target_count?: number;
  };
}

/**
 * Optimization status response.
 */
export interface OptimizationStatusResponse {
  article_id: number;
  generated: boolean;
  generated_at?: string | null;
  cost_usd?: number | null;
  has_title_suggestions: boolean;
  has_seo_suggestions: boolean;
  has_faqs: boolean;
  faq_count: number;
}

/**
 * Generate all AI optimization suggestions for an article.
 * Single API call generates title + SEO + FAQ suggestions.
 *
 * @param articleId - Article ID
 * @param request - Generation options
 * @returns Complete optimization results
 *
 * @example
 * ```ts
 * const result = await generateAllOptimizations(123, {
 *   regenerate: false
 * });
 * console.log(`Cost: $${result.generation_metadata.total_cost_usd}`);
 * console.log(`${result.title_suggestions.suggested_title_sets.length} title options`);
 * console.log(`${result.faqs.length} FAQ questions`);
 * ```
 */
export async function generateAllOptimizations(
  articleId: number,
  request: GenerateOptimizationsRequest = {}
): Promise<OptimizationsResponse> {
  return api.post<OptimizationsResponse>(
    `/v1/articles/${articleId}/generate-all-optimizations`,
    request
  );
}

/**
 * Get cached optimization suggestions.
 * No AI API call - instant retrieval from database.
 *
 * @param articleId - Article ID
 * @returns Cached optimization results
 *
 * @example
 * ```ts
 * const optimizations = await getOptimizations(123);
 * // Display in Step 3: SEO & FAQ Confirmation UI
 * ```
 */
export async function getOptimizations(
  articleId: number
): Promise<OptimizationsResponse> {
  return api.get<OptimizationsResponse>(
    `/v1/articles/${articleId}/optimizations`
  );
}

/**
 * Check optimization generation status for an article.
 *
 * @param articleId - Article ID
 * @returns Optimization status metadata
 *
 * @example
 * ```ts
 * const status = await getOptimizationStatus(123);
 * if (status.generated) {
 *   console.log(`Generated at: ${status.generated_at}`);
 *   console.log(`Cost: $${status.cost_usd}`);
 *   console.log(`FAQs: ${status.faq_count}`);
 * }
 * ```
 */
export async function getOptimizationStatus(
  articleId: number
): Promise<OptimizationStatusResponse> {
  return api.get<OptimizationStatusResponse>(
    `/v1/articles/${articleId}/optimization-status`
  );
}

/**
 * Delete all cached optimization suggestions.
 * Use before regenerating with different parameters.
 *
 * @param articleId - Article ID
 *
 * @example
 * ```ts
 * await deleteOptimizations(123);
 * // Now regenerate with different options
 * await generateAllOptimizations(123, { regenerate: true });
 * ```
 */
export async function deleteOptimizations(articleId: number): Promise<void> {
  return api.delete(`/v1/articles/${articleId}/optimizations`);
}

/**
 * Refresh related articles for an article.
 * Calls the Supabase match-internal-links API to find related articles
 * based on title and SEO keywords.
 *
 * @param articleId - Article ID
 * @returns Updated article data with related_articles
 *
 * @example
 * ```ts
 * const article = await refreshRelatedArticles(123);
 * console.log(`Found ${article.related_articles.length} related articles`);
 * ```
 */
export async function refreshRelatedArticles(articleId: number): Promise<ParsedArticleData> {
  return api.post<ParsedArticleData>(`/v1/articles/${articleId}/refresh-related-articles`, {});
}
