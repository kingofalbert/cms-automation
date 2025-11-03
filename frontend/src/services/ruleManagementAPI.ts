/**
 * Proofreading Rule Management API Service
 *
 * Provides type-safe methods for managing proofreading rules, drafts, and rulesets.
 */

import { api, apiClient } from './api-client';
import type {
  DraftRule,
  RuleDraft,
  SaveDraftRequest,
  ReviewItem,
  BatchReviewRequest,
  PublishRulesRequest,
  PublishedRuleset,
  TestRulesRequest,
  TestResult,
  ProofreadingStats,
  APIResponse,
  PaginatedResponse,
} from '../types/api';

class RuleManagementAPI {
  private baseURL: string = '/api/v1/proofreading/decisions';

  constructor() {
    // No need for constructor body - baseURL is initialized above
  }

  /**
   * Get paginated list of rule drafts.
   */
  async fetchDrafts(status?: string, page: number = 1, limit: number = 20) {
    return api.get<APIResponse<PaginatedResponse<RuleDraft>>>(`${this.baseURL}/rules/drafts`, {
      params: { status, page, limit },
    });
  }

  /**
   * Get detailed information for a specific draft.
   */
  async getDraftDetail(draftId: string) {
    return api.get<APIResponse<RuleDraft>>(`${this.baseURL}/rules/drafts/${draftId}`);
  }

  /**
   * Save a new rule draft.
   */
  async saveDraft(data: SaveDraftRequest) {
    return api.post<APIResponse<RuleDraft>>(`${this.baseURL}/rules/draft`, data);
  }

  /**
   * Update a specific rule in a draft.
   */
  async updateRule(draftId: string, ruleId: string, data: Partial<DraftRule>) {
    return api.put<APIResponse<DraftRule>>(
      `${this.baseURL}/rules/drafts/${draftId}/rules/${ruleId}`,
      data
    );
  }

  /**
   * Batch review multiple rules in a draft.
   */
  async batchReview(draftId: string, reviews: ReviewItem[]) {
    return api.post<APIResponse<RuleDraft>>(
      `${this.baseURL}/rules/drafts/${draftId}/review`,
      { reviews }
    );
  }

  /**
   * Test rules against sample content.
   */
  async testRules(rules: DraftRule[], content: string) {
    return api.post<APIResponse<TestResult>>(`${this.baseURL}/rules/test`, {
      rules,
      test_content: content,
      options: {
        show_step_by_step: true,
        apply_conditions: true,
      },
    });
  }

  /**
   * Publish a draft as a ruleset.
   */
  async publishRules(draftId: string, config: PublishRulesRequest) {
    return api.post<APIResponse<PublishedRuleset>>(
      `${this.baseURL}/rules/drafts/${draftId}/publish`,
      config
    );
  }

  /**
   * Generate rules automatically based on patterns and preferences.
   */
  async generateRules(confidence_threshold: number = 0.8) {
    return api.post<APIResponse<RuleDraft>>(`${this.baseURL}/rules/generate`, {
      confidence_threshold,
      include_patterns: true,
      include_preferences: true,
    });
  }

  /**
   * Get list of published rulesets.
   */
  async getPublishedRulesets() {
    return api.get<
      APIResponse<{
        rulesets: PublishedRuleset[];
        total: number;
      }>
    >(`${this.baseURL}/rules/published`);
  }

  /**
   * Get detailed information for a published ruleset.
   */
  async getPublishedRulesetDetail(rulesetId: string) {
    return api.get<APIResponse<PublishedRuleset>>(`${this.baseURL}/rules/published/${rulesetId}`);
  }

  /**
   * Download rules in specified format (Python, TypeScript, or JSON).
   */
  async downloadRules(rulesetId: string, format: 'python' | 'typescript' | 'json') {
    const response = await apiClient.get(
      `${this.baseURL}/rules/download/${rulesetId}/${format}`,
      { responseType: 'blob' }
    );
    return response.data;
  }

  /**
   * Apply published rules to content.
   */
  async applyPublishedRules(rulesetId: string, content: string, context?: Record<string, unknown>) {
    return api.post<APIResponse<TestResult>>(`${this.baseURL}/rules/apply/${rulesetId}`, {
      content,
      context: context || {},
    });
  }

  /**
   * Get proofreading statistics.
   */
  async getStatistics() {
    return api.get<APIResponse<ProofreadingStats>>(`${this.baseURL}/rules/statistics`);
  }
}

export default new RuleManagementAPI();