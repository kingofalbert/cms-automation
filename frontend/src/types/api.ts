/**
 * API 類型定義
 *
 * 這個文件包含所有後端 API 的 TypeScript 類型定義，
 * 確保前端和後端之間的類型安全。
 */

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
  | 'to_evaluate'
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
