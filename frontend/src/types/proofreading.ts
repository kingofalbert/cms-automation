// 校對規則相關類型定義

export enum DraftStatus {
  PENDING_REVIEW = 'pending_review',
  IN_REVIEW = 'in_review',
  APPROVED = 'approved',
  REJECTED = 'rejected'
}

export enum ReviewStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  MODIFIED = 'modified',
  REJECTED = 'rejected'
}

export enum ReviewAction {
  APPROVE = 'approve',
  MODIFY = 'modify',
  REJECT = 'reject'
}

export interface Example {
  before: string;
  after: string;
}

export interface ReviewProgress {
  total: number;
  reviewed: number;
  approved: number;
  modified: number;
  rejected: number;
}

export interface DraftRule {
  rule_id: string;
  rule_type: string;
  natural_language: string;
  pattern?: string;
  replacement?: string;
  conditions?: Record<string, any>;
  confidence: number;
  examples: Example[];
  review_status: ReviewStatus;
  user_feedback?: string;
  modified_at?: string;
  modified_by?: string;
}

export interface RuleDraft {
  draft_id: string;
  rules: DraftRule[];
  status: DraftStatus;
  description?: string;
  metadata: Record<string, any>;
  created_at: string;
  created_by: string;
  review_progress: ReviewProgress;
}

export interface DraftListResponse {
  success: boolean;
  data: {
    drafts: Array<{
      draft_id: string;
      rule_count: number;
      status: string;
      description?: string;
      created_at: string;
      created_by: string;
      review_progress: ReviewProgress;
    }>;
    total: number;
    page: number;
    limit: number;
  };
}

export interface DraftDetailResponse {
  success: boolean;
  data: RuleDraft;
}

export interface ModifyRuleRequest {
  natural_language: string;
  examples?: Example[];
  conditions?: Record<string, any>;
}

export interface ReviewItem {
  rule_id: string;
  action: ReviewAction;
  comment?: string;
  natural_language?: string;
}

export interface BatchReviewRequest {
  reviews: ReviewItem[];
}

export interface PublishRulesRequest {
  name: string;
  description?: string;
  include_rejected: boolean;
  activation_date?: string;
  test_mode: boolean;
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