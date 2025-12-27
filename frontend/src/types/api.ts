/**
 * API 類型定義
 *
 * 這個文件包含所有後端 API 的 TypeScript 類型定義，
 * 確保前端和後端之間的類型安全。
 */

import type { ProofreadingIssue } from './worklist';

// ============================================================================
// 通用類型
// ============================================================================

export interface APIResponse<T = unknown> {
  success: boolean;
  data: T;
  message?: string;
  request_id?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface APIError {
  error: string;
  message: string;
  details?: Record<string, string>;
  request_id?: string;
  status_code?: number;
}

// ============================================================================
// 文章相關類型
// ============================================================================

export type ArticleStatus =
  | 'imported'
  | 'in-review'
  | 'seo_optimized'
  | 'ready_to_publish'
  | 'publishing'
  | 'published'
  | 'failed';

export type ArticleSource = 'imported' | 'manual_entry' | 'google_drive';

export interface Article {
  id: number;
  title: string;
  content: string;
  excerpt?: string;
  category?: string;
  tags?: string[];
  status: ArticleStatus;
  source: ArticleSource;
  featured_image_path?: string;
  additional_images?: string[];
  published_url?: string;
  cms_article_id?: string;
  article_metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  published_at?: string;
  seo_metadata?: SEOMetadata;
}

export interface ArticleCreateRequest {
  title: string;
  content: string;
  excerpt?: string;
  category?: string;
  tags?: string[];
  source?: ArticleSource;
  featured_image?: File;
  additional_images?: File[];
  article_metadata?: Record<string, unknown>;
}

export interface ArticleUpdateRequest {
  title?: string;
  content?: string;
  excerpt?: string;
  category?: string;
  tags?: string[];
  status?: ArticleStatus;
  featured_image_path?: string;
  additional_images?: string[];
  article_metadata?: Record<string, unknown>;
}

export interface ArticleListParams {
  status?: ArticleStatus;
  source?: ArticleSource;
  search?: string;
  category?: string;
  page?: number;
  limit?: number;
  sort_by?: 'created_at' | 'updated_at' | 'title';
  sort_order?: 'asc' | 'desc';
}

// ============================================================================
// SEO 相關類型
// ============================================================================

export interface SEOMetadata {
  id: number;
  article_id: number;
  meta_title: string;
  meta_description: string;
  focus_keyword: string;
  primary_keywords: string[];
  secondary_keywords: string[];
  keyword_density: Record<string, number>;
  readability_score: number;
  optimization_recommendations: OptimizationRecommendation[];
  manual_overrides?: Record<string, unknown>;
  generated_by?: string;
  generation_cost?: number;
  generation_tokens?: number;
  created_at: string;
  updated_at: string;
}

export interface OptimizationRecommendation {
  type: 'title' | 'description' | 'keywords' | 'content' | 'readability';
  severity: 'info' | 'warning' | 'error';
  message: string;
  suggestion?: string;
}

export interface SEOAnalysisRequest {
  article_id: number;
  force_refresh?: boolean;
}

export interface SEOUpdateRequest {
  meta_title?: string;
  meta_description?: string;
  focus_keyword?: string;
  primary_keywords?: string[];
  secondary_keywords?: string[];
  manual_overrides?: Record<string, unknown>;
}

// ============================================================================
// SEO Title 相關類型 (Phase 9)
// ============================================================================

/**
 * SEO Title Variant - 單個 SEO Title 建議變體
 */
export interface SEOTitleVariant {
  /** Variant ID (e.g., "seo_variant_1") */
  id: string;
  /** SEO Title 內容 (~30 字) */
  seo_title: string;
  /** AI 生成原因說明 */
  reasoning: string;
  /** 此變體強調的關鍵詞 */
  keywords_focus: string[];
  /** 字符數 */
  character_count: number;
}

/**
 * SEO Title Suggestions Data - SEO Title 建議數據
 */
export interface SEOTitleSuggestionsData {
  /** 2-3 個 SEO Title 變體 */
  variants: SEOTitleVariant[];
  /** 原文提取的 SEO Title (如果有) */
  original_seo_title: string | null;
  /** 優化建議說明 */
  notes: string[];
}

/**
 * SEO Title 選擇請求
 */
export interface SelectSEOTitleRequest {
  /** 選擇的變體 ID (e.g., "seo_variant_1")，null 表示自定義 */
  variant_id?: string | null;
  /** 自定義 SEO Title (如果 variant_id 為 null) */
  custom_seo_title?: string | null;
}

/**
 * SEO Title 選擇回應
 */
export interface SelectSEOTitleResponse {
  /** 文章 ID */
  article_id: number;
  /** 應用的 SEO Title */
  seo_title: string;
  /** SEO Title 來源: extracted/ai_generated/user_input */
  seo_title_source: string;
  /** 之前的 SEO Title (如果有) */
  previous_seo_title: string | null;
  /** 更新時間 */
  updated_at: string;
}

// ============================================================================
// 發布任務相關類型
// ============================================================================

export type PublishProvider = 'anthropic' | 'gemini' | 'playwright';
export type PublishStatus = 'pending' | 'running' | 'completed' | 'failed';
export type CMSType = 'wordpress' | 'strapi' | 'ghost';

export interface PublishTask {
  id: number;
  article_id: number;
  task_id: string;
  provider: PublishProvider;
  cms_type: CMSType;
  cms_url: string;
  status: PublishStatus;
  retry_count: number;
  max_retries: number;
  error_message?: string;
  session_id?: string;
  screenshots: Screenshot[];
  cost_usd?: number;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  created_at: string;
  updated_at: string;
  current_step?: string;
  progress_percentage?: number;
}

export interface Screenshot {
  name: string;
  path: string;
  timestamp: string;
  description?: string;
}

export interface PublishTaskCreateRequest {
  article_id: number;
  provider: PublishProvider;
  cms_type?: CMSType;
  cms_url?: string;
  force_republish?: boolean;
}

export interface PublishTaskListParams {
  status?: PublishStatus;
  provider?: PublishProvider;
  article_id?: number;
  page?: number;
  limit?: number;
  sort_by?: 'created_at' | 'started_at' | 'completed_at';
  sort_order?: 'asc' | 'desc';
}

// ============================================================================
// 執行日誌相關類型
// ============================================================================

export type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
export type ActionType = 'navigate' | 'click' | 'type' | 'upload' | 'screenshot' | 'wait';
export type ActionResult = 'success' | 'failed' | 'timeout';

export interface ExecutionLog {
  id: number;
  task_id: number;
  log_level: LogLevel;
  step_name: string;
  message: string;
  details?: Record<string, unknown>;
  action_type?: ActionType;
  action_target?: string;
  action_result?: ActionResult;
  screenshot_path?: string;
  created_at: string;
}

// ============================================================================
// 文章導入相關類型
// ============================================================================

export interface CSVImportRequest {
  file: File;
  validate_only?: boolean;
}

export interface JSONImportRequest {
  file: File;
  validate_only?: boolean;
}

export interface ImportResult {
  success: boolean;
  total: number;
  imported: number;
  failed: number;
  skipped: number;
  errors: ImportError[];
  articles?: Article[];
}

export interface ImportError {
  row?: number;
  field?: string;
  message: string;
  value?: string;
}

// ============================================================================
// Worklist 相關類型
// ============================================================================

export type WorklistStatus =
  | 'pending'
  | 'proofreading'
  | 'under_review'
  | 'ready_to_publish'
  | 'publishing'
  | 'published'
  | 'failed';

export interface WorklistItem {
  id: number;
  drive_file_id?: string;
  title: string;
  content: string;
  status: WorklistStatus;
  metadata?: Record<string, unknown>;
  notes: WorklistNote[];
  synced_at?: string;
  created_at: string;
  updated_at: string;
}

export interface WorklistNote {
  author: string;
  content: string;
  created_at: string;
}

export interface WorklistUpdateRequest {
  status?: WorklistStatus;
  note?: {
    author: string;
    content: string;
  };
}

export interface WorklistListParams {
  status?: WorklistStatus;
  search?: string;
  page?: number;
  limit?: number;
}

export interface WorklistStatistics {
  total: number;
  breakdown: Record<WorklistStatus, number>;
}

// ============================================================================
// 設置相關類型
// ============================================================================

export interface Settings {
  cms_config: CMSConfig;
  provider_config: ProviderConfig;
  cost_limits: CostLimits;
  screenshot_retention: ScreenshotRetention;
}

export interface CMSConfig {
  cms_type: CMSType;
  base_url: string;
  username?: string;
  application_password?: string;
  api_token?: string;
}

export interface ProviderConfig {
  default_provider: PublishProvider;
  anthropic_api_key?: string;
  gemini_api_key?: string;
  enable_fallback: boolean;
  fallback_order: PublishProvider[];
}

export interface CostLimits {
  daily_budget_usd?: number;
  per_article_max_usd?: number;
  alert_threshold_percentage?: number;
}

export interface ScreenshotRetention {
  retention_days: number;
  compression_enabled: boolean;
  storage_type: 'local' | 's3' | 'gcs';
}

// ============================================================================
// Provider Comparison 相關類型
// ============================================================================

export interface ProviderMetrics {
  provider: PublishProvider;
  total_tasks: number;
  success_count: number;
  failed_count: number;
  success_rate: number;
  avg_duration_seconds: number;
  avg_cost_usd: number;
  total_cost_usd: number;
  last_30_days: TimeSeriesData[];
}

export interface TimeSeriesData {
  date: string;
  success_count: number;
  failed_count: number;
  avg_duration: number;
  avg_cost: number;
}

// ============================================================================
// 校對相關類型
// ============================================================================

export type RuleType = 'grammar' | 'style' | 'punctuation' | 'spelling' | 'consistency';
export type ReviewStatus = 'pending' | 'approved' | 'rejected' | 'modified';
export type ReviewAction = 'approve' | 'modify' | 'reject';
export type DraftStatus = 'draft' | 'pending_review' | 'in_review' | 'ready_to_publish' | 'published';

export interface DraftRule {
  rule_id: string;
  rule_type: RuleType;
  natural_language: string;
  pattern?: string;
  replacement?: string;
  confidence: number;
  examples: Example[];
  conditions?: Record<string, unknown>;
  review_status: ReviewStatus;
  review_comment?: string;
  user_feedback?: string;
  modified_at?: string;
  modified_by?: string;
  metadata?: Record<string, unknown>;
}

export interface Example {
  before: string;
  after: string;
  description?: string;
}

export interface ReviewProgress {
  total: number;
  reviewed: number;
  approved: number;
  modified: number;
  rejected: number;
}

export interface RuleDraft {
  draft_id: string;
  description?: string;
  status: DraftStatus;
  rules: DraftRule[];
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  created_by?: string;
  review_progress?: ReviewProgress;
  total_rules: number;
  approved_count: number;
  rejected_count: number;
  pending_count: number;
}

export interface SaveDraftRequest {
  rules: Array<{
    natural_language: string;
    examples: Example[];
    rule_type: RuleType;
    confidence?: number;
    conditions?: Record<string, unknown>;
  }>;
  description?: string;
  metadata?: Record<string, unknown>;
}

export interface ReviewItem {
  rule_id: string;
  action: ReviewAction;
  status?: ReviewStatus;
  comment?: string;
  natural_language?: string;
  modified_pattern?: string;
  modified_replacement?: string;
}

export interface BatchReviewRequest {
  reviews: ReviewItem[];
}

export interface PublishRulesRequest {
  name: string;
  description?: string;
  version?: string;
  module_name?: string;
  include_rejected?: boolean;
  test_mode?: boolean;
  activation_date?: string;
}

export interface PublishedRuleset {
  ruleset_id: string;
  name: string;
  total_rules: number;
  created_at: string;
  status: 'active' | 'test';
  download_urls: {
    python: string;
    typescript: string;
    json: string;
  };
}

export interface TestRulesRequest {
  ruleset_id?: string;
  rules?: DraftRule[];
  test_content: string;
  options?: Record<string, boolean>;
}

export interface TestResult {
  original: string;
  result: string;
  changes: Array<{
    rule_id: string;
    type: string;
    position: [number, number];
    original: string;
    replacement: string;
    confidence: number;
  }>;
  execution_time_ms: number;
}

export interface Suggestion {
  rule_id: string;
  rule_type: RuleType;
  original_text: string;
  suggested_text: string;
  confidence: number;
  applied: boolean;
  position?: {
    start: number;
    end: number;
  };
}

// ============================================================================
// 統計相關類型
// ============================================================================

export interface ProofreadingStats {
  total_rulesets: number;
  total_rules: number;
  active_rulesets: number;
  avg_rules_per_ruleset: number;
  recent_activity: RecentActivity[];
  ruleset_distribution: RulesetDistribution[];
  top_rulesets: PublishedRuleset[];
}

export interface RecentActivity {
  date: string;
  action: string;
  ruleset_id: string;
  rule_count: number;
}

export interface RulesetDistribution {
  rule_count: number;
  count: number;
}

// ============================================================================
// 認證相關類型
// ============================================================================

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  created_at: string;
}

// ============================================================================
// WebSocket 相關類型
// ============================================================================

export interface WebSocketMessage {
  type: 'task_update' | 'worklist_update' | 'notification' | 'pong';
  data: unknown;
  timestamp: string;
}

export interface TaskUpdateMessage {
  task_id: string;
  status: PublishStatus;
  current_step?: string;
  progress_percentage?: number;
  error_message?: string;
}

export interface WorklistUpdateMessage {
  item_id: number;
  status: WorklistStatus;
  title: string;
}

// ============================================================================
// Phase 12: Related Articles for Internal Linking
// ============================================================================

/**
 * Related article recommendation for internal linking
 */
export interface RelatedArticle {
  /** Article ID (e.g., "n12345678") */
  article_id: string;
  /** Full article title */
  title: string;
  /** Main title component (optional) */
  title_main?: string;
  /** Original article URL */
  url: string;
  /** Article excerpt/summary */
  excerpt?: string;
  /** Similarity score (0-1) */
  similarity: number;
  /** Match type: semantic, content, or keyword */
  match_type: 'semantic' | 'content' | 'keyword';
  /** AI-extracted keywords */
  ai_keywords: string[];
}

// ============================================================================
// Article Review (Proofreading) 相關類型
// ============================================================================

export interface ContentComparison {
  original: string;
  suggested: string | null;
  changes: Record<string, unknown> | null;
}

export interface MetaComparison {
  original: string | null;
  suggested: string | null;
  reasoning: string | null;
  score: number | null;
  length_original: number;
  length_suggested: number;
}

export interface SEOComparison {
  original_keywords: string[];
  suggested_keywords: string[] | null;
  reasoning: string | null;
  score: number | null;
}

/**
 * Tags comparison for parsing review
 * Tags are WordPress internal navigation labels (different from SEO keywords)
 */
export interface TagsComparison {
  /** Tags extracted from original document */
  original_tags: string[];
  /** AI suggested tags with metadata */
  suggested_tags: SuggestedTag[] | null;
  /** AI strategy explanation for tag recommendations */
  tag_strategy: string | null;
}

export interface SuggestedTag {
  tag: string;
  relevance: number; // 0-1
  type: 'primary' | 'secondary' | 'trending';
  existing?: boolean; // Whether tag already exists in system
  article_count?: number; // Number of articles using this tag
}

export interface FAQQuestion {
  question: string;
  answer: string;
}

export interface FAQProposal {
  questions: FAQQuestion[];
  schema_type: string;
  score: number | null;
}

export interface ParagraphSuggestion {
  paragraph_index: number;
  original_text: string;
  suggested_text: string;
  reasoning: string;
  improvement_type: 'split' | 'merge' | 'rewrite' | 'reorder';
}

export interface ProofreadingDecisionDetail {
  issue_id: string;
  decision_type: 'accepted' | 'rejected' | 'modified';
  rationale: string | null;
  modified_content: string | null;
  reviewer: string;
  decided_at: string;
}

/**
 * API Proofreading Issue - Actual structure returned by backend API
 * Different from frontend ProofreadingIssue which has transformed field names
 */
export interface APIProofreadingIssue {
  source: 'script' | 'ai';
  message: string;           // Maps to explanation
  rule_id: string;
  category: string;          // Maps to rule_category
  evidence: string;          // Maps to original_text
  location: {
    offset: number;
    line?: number;
    column?: number;
  };
  severity: 'critical' | 'warning' | 'info';
  confidence: number;        // 0-1 value
  suggestion: string;        // Maps to suggested_text
  subcategory?: string;
  can_auto_fix?: boolean;
  attributed_by?: string;
  blocks_publish?: boolean;
}

/**
 * Transform API proofreading issue to frontend format
 */
export const transformAPIProofreadingIssue = (
  apiIssue: APIProofreadingIssue,
  index: number
): ProofreadingIssue => ({
  id: `${apiIssue.rule_id}-${index}`,
  rule_id: apiIssue.rule_id,
  rule_category: apiIssue.category || apiIssue.subcategory || 'general',
  severity: apiIssue.severity,
  engine: apiIssue.source === 'ai' ? 'ai' : 'deterministic',
  position: {
    start: apiIssue.location.offset,
    end: apiIssue.location.offset + (apiIssue.evidence?.length || 0),
    line: apiIssue.location.line,
    column: apiIssue.location.column,
  },
  original_text: apiIssue.evidence || '',
  suggested_text: apiIssue.suggestion || '',
  explanation: apiIssue.message || '',
  confidence: apiIssue.confidence,
  decision_status: 'pending',
});

/**
 * Transform array of API proofreading issues
 */
export const transformAPIProofreadingIssues = (
  apiIssues: APIProofreadingIssue[]
): ProofreadingIssue[] => apiIssues.map(transformAPIProofreadingIssue);

export interface ArticleReviewResponse {
  // Basic info
  id: number;
  title: string;
  status: ArticleStatus;

  // Content comparison
  content: ContentComparison;

  // Meta comparison
  meta: MetaComparison;

  // SEO comparison
  seo: SEOComparison;

  // Tags comparison (WordPress internal navigation)
  tags?: TagsComparison;

  // FAQ proposals
  faq_proposals: FAQProposal[];

  // FAQ applicability (Phase 13 v2.2)
  faq_applicable?: boolean | null;

  // Paragraph suggestions
  paragraph_suggestions: ParagraphSuggestion[];

  // Proofreading issues (raw API format, needs transformation)
  proofreading_issues: APIProofreadingIssue[];

  // Existing decisions (hydrated from database)
  existing_decisions: ProofreadingDecisionDetail[];

  // Phase 12: Related Articles for Internal Linking
  related_articles?: RelatedArticle[];

  // AI metadata
  ai_model_used: string | null;
  suggested_generated_at: string | null;
  generation_cost: number | null;

  // Timestamps
  created_at: string;
  updated_at: string;
}

/**
 * Transformed ArticleReviewResponse with frontend-ready proofreading issues
 */
export interface ArticleReviewResponseTransformed extends Omit<ArticleReviewResponse, 'proofreading_issues'> {
  proofreading_issues: ProofreadingIssue[];
}

/**
 * Check if a proofreading issue is in API format (has evidence/message fields)
 * vs frontend format (has original_text/explanation fields)
 */
const isAPIFormatIssue = (issue: Record<string, unknown>): boolean => {
  return 'evidence' in issue || ('message' in issue && !('explanation' in issue));
};

/**
 * Smart transform for proofreading issues - handles both API and frontend formats
 * The backend may return issues in either format depending on the endpoint
 */
const smartTransformIssues = (issues: unknown[]): ProofreadingIssue[] => {
  if (!issues || issues.length === 0) return [];

  // Check the first issue to determine format
  const firstIssue = issues[0] as Record<string, unknown>;

  if (isAPIFormatIssue(firstIssue)) {
    // Old API format with evidence/suggestion/message - needs transformation
    return transformAPIProofreadingIssues(issues as APIProofreadingIssue[]);
  }

  // Already in frontend format with original_text/suggested_text/explanation
  // Just ensure the structure is correct
  return (issues as ProofreadingIssue[]).map((issue, index) => ({
    id: issue.id || `${issue.rule_id}-${index}`,
    rule_id: issue.rule_id,
    rule_category: issue.rule_category || 'general',
    severity: issue.severity || 'info',
    engine: issue.engine || 'deterministic',
    position: issue.position || { start: 0, end: 0 },
    original_text: issue.original_text || '',
    suggested_text: issue.suggested_text || '',
    explanation: issue.explanation || '',
    explanation_detail: issue.explanation_detail,
    confidence: issue.confidence,
    tags: issue.tags || [],
    decision_status: issue.decision_status || 'pending',
    decision_id: issue.decision_id,
  }));
};

/**
 * Transform ArticleReviewResponse to have frontend-ready proofreading issues
 */
export const transformArticleReviewResponse = (
  response: ArticleReviewResponse
): ArticleReviewResponseTransformed => ({
  ...response,
  proofreading_issues: smartTransformIssues(response.proofreading_issues || []),
});
