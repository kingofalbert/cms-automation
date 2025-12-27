/**
 * Type definitions for worklist and Google Drive integration.
 */

/**
 * Worklist status - Extended 9-state workflow.
 *
 * Workflow: pending → parsing → parsing_review → proofreading → proofreading_review → ready_to_publish → publishing → published
 */
export type WorklistStatus =
  | 'pending' // 待处理
  | 'parsing' // 解析中 (Phase 7 - Article parsing in progress)
  | 'parsing_review' // 解析审核中 (Phase 7 - Review title/author/SEO/images)
  | 'proofreading' // 校对中 (AI proofreading in progress)
  | 'proofreading_review' // 校对审核中 (Review proofreading issues) - replaces 'under_review'
  | 'ready_to_publish' // 待发布
  | 'publishing' // 发布中
  | 'published' // 已发布
  | 'failed'; // 失败/需重试

/**
 * Legacy status mapping for backward compatibility
 */
export const LEGACY_STATUS_MAP: Record<string, WorklistStatus> = {
  'under_review': 'proofreading_review', // Map old status to new
};

/**
 * Worklist item from Google Drive.
 */
export interface WorklistMetadata extends Record<string, unknown> {
  word_count?: number;
  estimated_reading_time?: number;
  last_synced_at?: string;
  quality_score?: number;
  seo_score?: number;
}

export interface WorklistNote extends Record<string, unknown> {
  id?: string | number;
  author?: string | null;
  message?: string;
  content?: string;
  created_at?: string;
  resolved?: boolean;
}

/**
 * Article image information for Phase 16 enhanced preview.
 */
export interface ArticleImageInfo {
  id?: number;
  image_url: string;
  alt_text?: string | null;
  ai_alt_text?: string | null;
  position?: number;
  filename?: string;
  source_url?: string;
}

export interface WorklistItem {
  id: number;
  drive_file_id: string;
  title: string;
  status: WorklistStatus | string;
  author?: string | null;
  article_id?: number | null;
  metadata: WorklistMetadata;
  notes: WorklistNote[];
  synced_at: string;
  created_at: string;
  updated_at: string;
  tags?: string[];
  categories?: string[];
  article_status?: string | null;
  /** Google Drive metadata including webViewLink for opening original doc */
  drive_metadata?: Record<string, unknown>;
}

export interface WorklistStatusHistoryEntry {
  old_status: string | null;
  new_status: string;
  changed_by?: string | null;
  change_reason?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface WorklistItemDetail extends WorklistItem {
  content: string;
  meta_description?: string | null;
  seo_keywords: string[];

  // Phase 7: Parsing fields (HOTFIX-PARSE-005)
  title_main?: string | null;
  title_prefix?: string | null;
  title_suffix?: string | null;
  author_name?: string | null;
  author_line?: string | null;
  tags?: string[];
  parsing_confirmed?: boolean;
  parsing_confirmed_at?: string | null;

  // Phase 16: SEO Title for Google Preview
  seo_title?: string | null;

  // Phase 16: Article Images with Alt Text
  article_images?: ArticleImageInfo[];

  // Phase 11: WordPress Category Taxonomy
  /** Primary category (主分類) - determines URL structure */
  primary_category?: string | null;
  /** Secondary categories (副分類) - for cross-listing */
  secondary_categories?: string[];

  article_status_history: WorklistStatusHistoryEntry[];
  drive_metadata: Record<string, unknown>;
  proofreading_issues?: ProofreadingIssue[];
  proofreading_stats?: ProofreadingStats;

  /** Article metadata including FAQ suggestions for state persistence */
  article_metadata?: Record<string, unknown>;

  /** Phase 14: Extracted FAQs from original article HTML */
  extracted_faqs?: Array<{ question: string; answer: string }>;
  extracted_faqs_detection_method?: string | null;
}

/**
 * Worklist statistics.
 */
export interface WorklistStatistics {
  total: number;
  breakdown: Record<string, number>;
  total_word_count?: number;
  avg_quality_score?: number;
  avg_time_per_status?: Record<string, number>;
}

export interface WorklistListResponse {
  items: WorklistItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Worklist filter options.
 */
export interface WorklistFilters {
  status?: WorklistStatus | 'all';
  author?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  tags?: string[];
  categories?: string[];
}

/**
 * Status transition request.
 */
export interface StatusTransitionRequest {
  item_id: string;
  from_status: WorklistStatus;
  to_status: WorklistStatus;
  note?: string;
}

/**
 * Google Drive sync status.
 */
export interface DriveSyncStatus {
  last_synced_at: string | null;
  total_items: number;
  is_syncing?: boolean;
  synced_items?: number;
  failed_items?: number;
  errors?: string[];
}

/**
 * Worklist item update request.
 */
export interface WorklistItemUpdate {
  title?: string;
  content?: string;
  excerpt?: string;
  tags?: string[];
  categories?: string[];
  status?: WorklistStatus;
}

/**
 * Proofreading Review UI Types (Feature 003)
 */

export type IssueSeverity = 'critical' | 'warning' | 'info';
export type IssueEngine = 'ai' | 'deterministic';
export type DecisionStatus = 'pending' | 'accepted' | 'rejected' | 'modified';
export type DecisionType = 'accepted' | 'rejected' | 'modified';
export type FeedbackCategory =
  | 'suggestion_correct'
  | 'suggestion_partially_correct'
  | 'suggestion_incorrect'
  | 'rule_needs_adjustment';

export interface ProofreadingPosition {
  start: number;
  end: number;
  line?: number;
  column?: number;
  section?: string;
}

/**
 * Spec 014: Plain text position for accurate frontend highlighting.
 *
 * This position is calculated from the plain text content (HTML tags stripped),
 * solving the HTML/plain-text position mismatch problem.
 */
export interface PlainTextPosition {
  start: number;
  end: number;
}

/**
 * Warning labels for G-class contextual validation rules.
 * These flags indicate issues requiring manual verification.
 */
export type WarningLabel =
  | 'manual_verify' // 需手動驗證
  | 'ai_hallucination' // 可能為AI幻覺
  | 'geographic_anomaly' // 地理邏輯異常
  | 'symbol_format' // 符號格式異常
  | 'sentence_incomplete' // 語句不完整
  | 'structure_suggestion'; // 結構優化建議

export interface ProofreadingIssue {
  id: string;
  rule_id: string;
  rule_category: string;
  severity: IssueSeverity;
  engine: IssueEngine;
  position: ProofreadingPosition;
  original_text: string;
  suggested_text: string;
  explanation: string;
  explanation_detail?: string;
  confidence?: number; // AI only (0-1)
  decision_status: DecisionStatus;
  decision_id?: number;
  tags?: string[];
  /**
   * Warning label for G-class contextual validation issues
   * Indicates issues that need manual verification
   */
  warning_label?: WarningLabel;

  /**
   * Spec 014: Plain text position for accurate frontend highlighting.
   * This is calculated from the HTML content positions by the backend.
   */
  plain_text_position?: PlainTextPosition;

  /**
   * Spec 014: Plain text version of original_text (HTML tags stripped).
   * Used for display and text search fallback.
   */
  original_text_plain?: string;

  /**
   * Spec 014: Plain text version of suggested_text (HTML tags stripped).
   * Used for display in the UI.
   */
  suggested_text_plain?: string;
}

export interface ProofreadingStats {
  total_issues: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  pending_count: number;
  accepted_count: number;
  rejected_count: number;
  modified_count: number;
  ai_issues_count: number;
  deterministic_issues_count: number;
}

export interface DecisionPayload {
  issue_id: string;
  decision_type: DecisionType;
  decision_rationale?: string;
  modified_content?: string;
  feedback_provided: boolean;
  feedback_category?: FeedbackCategory;
  feedback_notes?: string;
}

export interface ReviewDecisionsRequest {
  decisions: DecisionPayload[];
  review_notes?: string;
  transition_to?: 'ready_to_publish' | 'proofreading' | 'failed';
}

export interface WorklistItemSummary {
  id: number;
  status: string;
  updated_at: string;
}

export interface ArticleSummary {
  id: number;
  status: string;
  updated_at: string;
}

export interface ReviewDecisionsResponse {
  success: boolean;
  saved_decisions_count: number;
  worklist_item: WorklistItemSummary;
  article: ArticleSummary;
  errors: string[];
}

export interface BatchDecisionsRequest {
  issue_ids: string[];
  decision_type: 'accepted' | 'rejected';
  rationale?: string;
}

export interface SavedDecisionSummary {
  issue_id: string;
  decision_id: number;
  decision_type: string;
}

export interface BatchDecisionsResponse {
  success: boolean;
  processed_count: number;
  failed: string[];
  saved_decisions: SavedDecisionSummary[];
}
