import axios from 'axios';
import {
  DraftListResponse,
  DraftDetailResponse,
  ModifyRuleRequest,
  BatchReviewRequest,
  PublishRulesRequest,
  TestRulesRequest,
  TestResult,
  ReviewItem,
  DraftRule
} from '../types/proofreading';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

class RuleManagementAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = `${API_BASE_URL}/api/v1/proofreading/decisions`;
  }

  // 獲取草稿列表
  async fetchDrafts(
    status?: string,
    page: number = 1,
    limit: number = 20
  ): Promise<DraftListResponse> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('page', page.toString());
    params.append('limit', limit.toString());

    const response = await axios.get(`${this.baseURL}/rules/drafts?${params}`);
    return response.data;
  }

  // 獲取草稿詳情
  async getDraftDetail(draftId: string): Promise<DraftDetailResponse> {
    const response = await axios.get(`${this.baseURL}/rules/drafts/${draftId}`);
    return response.data;
  }

  // 保存草稿
  async saveDraft(rules: any[], description?: string, metadata?: any) {
    const response = await axios.post(`${this.baseURL}/rules/draft`, {
      rules,
      description,
      metadata
    });
    return response.data;
  }

  // 修改規則
  async updateRule(
    draftId: string,
    ruleId: string,
    data: ModifyRuleRequest
  ) {
    const response = await axios.put(
      `${this.baseURL}/rules/drafts/${draftId}/rules/${ruleId}`,
      data
    );
    return response.data;
  }

  // 批量審查
  async batchReview(draftId: string, reviews: ReviewItem[]) {
    const response = await axios.post(
      `${this.baseURL}/rules/drafts/${draftId}/review`,
      { reviews }
    );
    return response.data;
  }

  // 測試規則
  async testRules(rules: DraftRule[], content: string): Promise<{
    success: boolean;
    data: TestResult;
  }> {
    const response = await axios.post(`${this.baseURL}/rules/test`, {
      rules,
      test_content: content,
      options: {
        show_step_by_step: true,
        apply_conditions: true
      }
    });
    return response.data;
  }

  // 發布規則
  async publishRules(draftId: string, config: PublishRulesRequest) {
    const response = await axios.post(
      `${this.baseURL}/rules/drafts/${draftId}/publish`,
      config
    );
    return response.data;
  }

  // 生成規則
  async generateRules(
    confidence_threshold: number = 0.8
  ) {
    const response = await axios.post(`${this.baseURL}/rules/generate`, {
      confidence_threshold,
      include_patterns: true,
      include_preferences: true
    });
    return response.data;
  }
}

export default new RuleManagementAPI();