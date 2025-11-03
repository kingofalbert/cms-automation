"""校對決策 API 的 Pydantic 模型

定義請求和響應的數據模型，用於 API 數據驗證和序列化。
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


# ============================================================================
# 枚舉類型
# ============================================================================

class DecisionTypeEnum(str, Enum):
    """決策類型枚舉"""
    ACCEPT = "accept"
    REJECT = "reject"
    MODIFY = "modify"


class SuggestionTypeEnum(str, Enum):
    """建議類型枚舉"""
    SPELLING = "spelling"
    GRAMMAR = "grammar"
    PUNCTUATION = "punctuation"
    STYLE = "style"
    VOCABULARY = "vocabulary"
    FORMATTING = "formatting"
    OTHER = "other"


class AggregationPeriod(str, Enum):
    """聚合週期枚舉"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class TrendType(str, Enum):
    """趨勢類型枚舉"""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    INCREASING = "increasing"
    DECREASING = "decreasing"


class PriorityLevel(str, Enum):
    """優先級枚舉"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# 基礎模型
# ============================================================================

class BaseResponse(BaseModel):
    """基礎響應模型"""
    success: bool = Field(default=True, description="操作是否成功")
    message: Optional[str] = Field(default=None, description="響應消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="響應時間戳")


class PaginationParams(BaseModel):
    """分頁參數"""
    page: int = Field(default=1, ge=1, description="頁碼")
    limit: int = Field(default=20, ge=1, le=100, description="每頁數量")


class DateRangeParams(BaseModel):
    """日期範圍參數"""
    start_date: Optional[datetime] = Field(default=None, description="開始日期")
    end_date: Optional[datetime] = Field(default=None, description="結束日期")

    @validator("end_date")
    def validate_date_range(cls, v, values):
        if v and "start_date" in values and values["start_date"]:
            if v < values["start_date"]:
                raise ValueError("結束日期必須晚於開始日期")
        return v


# ============================================================================
# 決策相關請求模型
# ============================================================================

class DecisionRequest(BaseModel):
    """決策記錄請求"""
    article_id: int = Field(..., gt=0, description="文章ID")
    proofreading_history_id: int = Field(..., gt=0, description="校對歷史ID")
    suggestion_id: str = Field(..., min_length=1, description="建議ID")
    decision: DecisionTypeEnum = Field(..., description="決策類型")
    custom_correction: Optional[str] = Field(default=None, description="自定義修正")
    decision_reason: Optional[str] = Field(default=None, description="決策原因")
    tags: Optional[List[str]] = Field(default=None, description="標籤列表")

    class Config:
        schema_extra = {
            "example": {
                "article_id": 123,
                "proofreading_history_id": 456,
                "suggestion_id": "sug_001",
                "decision": "accept",
                "decision_reason": "拼寫錯誤需要修正",
                "tags": ["spelling", "important"]
            }
        }


class BatchDecisionItem(BaseModel):
    """批量決策項"""
    suggestion_id: str = Field(..., min_length=1, description="建議ID")
    decision: DecisionTypeEnum = Field(..., description="決策類型")
    custom_correction: Optional[str] = Field(default=None, description="自定義修正")
    reason: Optional[str] = Field(default=None, description="決策原因")
    tags: Optional[List[str]] = Field(default=None, description="標籤")


class BatchDecisionRequest(BaseModel):
    """批量決策請求"""
    article_id: int = Field(..., gt=0, description="文章ID")
    proofreading_history_id: int = Field(..., gt=0, description="校對歷史ID")
    decisions: List[BatchDecisionItem] = Field(..., min_items=1, description="決策列表")

    class Config:
        schema_extra = {
            "example": {
                "article_id": 123,
                "proofreading_history_id": 456,
                "decisions": [
                    {
                        "suggestion_id": "sug_001",
                        "decision": "accept",
                        "reason": "拼寫正確"
                    },
                    {
                        "suggestion_id": "sug_002",
                        "decision": "reject",
                        "reason": "保持原樣"
                    }
                ]
            }
        }


class DecisionUpdateRequest(BaseModel):
    """決策更新請求"""
    decision: Optional[DecisionTypeEnum] = Field(default=None, description="新的決策類型")
    custom_correction: Optional[str] = Field(default=None, description="新的自定義修正")
    decision_reason: Optional[str] = Field(default=None, description="新的決策原因")
    tags: Optional[List[str]] = Field(default=None, description="新的標籤")


# ============================================================================
# 決策相關響應模型
# ============================================================================

class DecisionResponse(BaseModel):
    """決策響應"""
    decision_id: int = Field(..., description="決策ID")
    article_id: int = Field(..., description="文章ID")
    proofreading_history_id: int = Field(..., description="校對歷史ID")
    suggestion_id: str = Field(..., description="建議ID")
    suggestion_type: str = Field(..., description="建議類型")
    original_text: str = Field(..., description="原始文本")
    suggested_text: str = Field(..., description="建議文本")
    decision: DecisionTypeEnum = Field(..., description="決策類型")
    custom_correction: Optional[str] = Field(default=None, description="自定義修正")
    decision_reason: Optional[str] = Field(default=None, description="決策原因")
    confidence_score: float = Field(..., ge=0, le=1, description="置信度分數")
    context_before: Optional[str] = Field(default=None, description="前文")
    context_after: Optional[str] = Field(default=None, description="後文")
    tags: List[str] = Field(default_factory=list, description="標籤")
    created_at: datetime = Field(..., description="創建時間")
    updated_at: datetime = Field(..., description="更新時間")

    class Config:
        orm_mode = True


class DecisionListResponse(BaseResponse):
    """決策列表響應"""
    data: List[DecisionResponse] = Field(..., description="決策列表")
    total: int = Field(..., ge=0, description="總數")
    page: int = Field(..., ge=1, description="當前頁碼")
    limit: int = Field(..., ge=1, description="每頁數量")


class BatchDecisionResponse(BaseResponse):
    """批量決策響應"""
    processed: int = Field(..., ge=0, description="處理數量")
    successful: int = Field(..., ge=0, description="成功數量")
    failed: int = Field(..., ge=0, description="失敗數量")
    decisions: List[DecisionResponse] = Field(..., description="決策結果")
    errors: Optional[List[Dict[str, str]]] = Field(default=None, description="錯誤信息")


# ============================================================================
# 模式分析相關模型
# ============================================================================

class PatternDetail(BaseModel):
    """模式詳情"""
    pattern_type: str = Field(..., description="模式類型")
    frequency: int = Field(..., ge=0, description="出現頻率")
    rate: float = Field(..., ge=0, le=1, description="比率")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    examples: List[str] = Field(default_factory=list, description="示例")


class CorrectionPattern(BaseModel):
    """修正模式"""
    id: str = Field(..., description="模式ID")
    original_pattern: str = Field(..., description="原始模式")
    correction_pattern: str = Field(..., description="修正模式")
    frequency: int = Field(..., ge=0, description="頻率")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文")


class TimePattern(BaseModel):
    """時間模式"""
    period: str = Field(..., description="時間段")
    trend: TrendType = Field(..., description="趨勢")
    metrics: Dict[str, float] = Field(..., description="指標")


class PatternAnalysisRequest(BaseModel):
    """模式分析請求"""
    start_date: Optional[datetime] = Field(default=None, description="開始日期")
    end_date: Optional[datetime] = Field(default=None, description="結束日期")
    min_occurrences: int = Field(default=5, ge=1, description="最小出現次數")


class PatternAnalysisResponse(BaseResponse):
    """模式分析響應"""
    common_acceptances: List[PatternDetail] = Field(..., description="常見接受模式")
    common_rejections: List[PatternDetail] = Field(..., description="常見拒絕模式")
    custom_corrections: List[CorrectionPattern] = Field(..., description="自定義修正模式")
    time_patterns: List[TimePattern] = Field(..., description="時間模式")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="置信度分數")


# ============================================================================
# 用戶偏好相關模型
# ============================================================================

class StylePreferences(BaseModel):
    """風格偏好"""
    formal_level: str = Field(default="neutral", description="正式程度")
    sentence_length: str = Field(default="medium", description="句子長度")
    complexity: str = Field(default="moderate", description="複雜度")


class UserPreferencesResponse(BaseResponse):
    """用戶偏好響應"""
    style_preferences: StylePreferences = Field(..., description="風格偏好")
    vocabulary_preferences: List[str] = Field(default_factory=list, description="詞彙偏好")
    grammar_rules: List[str] = Field(default_factory=list, description="語法規則")
    punctuation_habits: Dict[str, str] = Field(default_factory=dict, description="標點習慣")
    confidence_level: float = Field(..., ge=0, le=1, description="置信度")


# ============================================================================
# 規則學習相關模型
# ============================================================================

class LearningRule(BaseModel):
    """學習規則"""
    rule_id: str = Field(..., description="規則ID")
    rule_type: str = Field(..., description="規則類型")
    pattern: str = Field(..., description="模式")
    replacement: Optional[str] = Field(default=None, description="替換內容")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    context_conditions: Dict[str, Any] = Field(default_factory=dict, description="上下文條件")
    example_applications: List[str] = Field(default_factory=list, description="應用示例")


class GenerateRulesRequest(BaseModel):
    """生成規則請求"""
    confidence_threshold: float = Field(default=0.8, ge=0, le=1, description="置信度閾值")
    include_patterns: bool = Field(default=True, description="包含模式")
    include_preferences: bool = Field(default=True, description="包含偏好")


class GenerateRulesResponse(BaseResponse):
    """生成規則響應"""
    rules: List[LearningRule] = Field(..., description="規則列表")
    total_rules: int = Field(..., ge=0, description="規則總數")
    generation_timestamp: datetime = Field(..., description="生成時間")


class RuleApplication(BaseModel):
    """規則應用"""
    rule_id: str = Field(..., description="規則ID")
    original_text: str = Field(..., description="原始文本")
    modified_text: str = Field(..., description="修改後文本")
    position: List[int] = Field(..., min_items=2, max_items=2, description="位置")
    confidence: float = Field(..., ge=0, le=1, description="置信度")


class ApplyRulesRequest(BaseModel):
    """應用規則請求"""
    content: str = Field(..., min_length=1, description="內容")
    rule_ids: Optional[List[str]] = Field(default=None, description="規則ID列表")
    apply_all: bool = Field(default=False, description="應用所有規則")


class ApplyRulesResponse(BaseResponse):
    """應用規則響應"""
    original_content: str = Field(..., description="原始內容")
    modified_content: str = Field(..., description="修改後內容")
    applications: List[RuleApplication] = Field(..., description="應用記錄")
    total_changes: int = Field(..., ge=0, description="總修改數")


# ============================================================================
# 反饋聚合相關模型
# ============================================================================

class FeedbackStatsRequest(BaseModel):
    """反饋統計請求"""
    aggregation_period: AggregationPeriod = Field(default=AggregationPeriod.DAILY, description="聚合週期")
    date: Optional[datetime] = Field(default=None, description="指定日期")


class FeedbackStatsResponse(BaseResponse):
    """反饋統計響應"""
    total_decisions: int = Field(..., ge=0, description="總決策數")
    acceptance_rate: float = Field(..., ge=0, le=1, description="接受率")
    rejection_rate: float = Field(..., ge=0, le=1, description="拒絕率")
    modification_rate: float = Field(..., ge=0, le=1, description="修改率")
    suggestion_type_distribution: Dict[str, int] = Field(..., description="建議類型分布")
    user_activity: Dict[str, Any] = Field(..., description="用戶活動")
    time_period: str = Field(..., description="時間段")


class PrepareDatasetRequest(BaseModel):
    """準備數據集請求"""
    min_examples: int = Field(default=100, ge=1, description="最小樣本數")
    balance_dataset: bool = Field(default=True, description="平衡數據集")
    include_metadata: bool = Field(default=True, description="包含元數據")


class PrepareDatasetResponse(BaseResponse):
    """準備數據集響應"""
    dataset_id: str = Field(..., description="數據集ID")
    positive_examples: int = Field(..., ge=0, description="正例數量")
    negative_examples: int = Field(..., ge=0, description="負例數量")
    custom_examples: int = Field(..., ge=0, description="自定義例數量")
    metadata: Dict[str, Any] = Field(..., description="元數據")
    download_url: Optional[str] = Field(default=None, description="下載URL")


# ============================================================================
# 質量評估相關模型
# ============================================================================

class QualityEvaluationRequest(BaseModel):
    """質量評估請求"""
    start_date: Optional[datetime] = Field(default=None, description="開始日期")
    end_date: Optional[datetime] = Field(default=None, description="結束日期")


class QualityEvaluationResponse(BaseResponse):
    """質量評估響應"""
    accuracy: float = Field(..., ge=0, le=1, description="準確率")
    relevance: float = Field(..., ge=0, le=1, description="相關性")
    usefulness: float = Field(..., ge=0, le=1, description="有用性")
    trend: TrendType = Field(..., description="趨勢")
    details: Dict[str, Any] = Field(..., description="詳細信息")


class ImprovementArea(BaseModel):
    """改進領域"""
    area_name: str = Field(..., description="領域名稱")
    current_performance: float = Field(..., ge=0, le=1, description="當前性能")
    target_performance: float = Field(..., ge=0, le=1, description="目標性能")
    priority: PriorityLevel = Field(..., description="優先級")
    suggestions: List[str] = Field(..., description="建議")


class ImprovementAreasRequest(BaseModel):
    """改進領域請求"""
    target_accuracy: float = Field(default=0.85, ge=0, le=1, description="目標準確率")


class ImprovementAreasResponse(BaseResponse):
    """改進領域響應"""
    improvement_areas: List[ImprovementArea] = Field(..., description="改進領域")
    total_areas: int = Field(..., ge=0, description="總領域數")


# ============================================================================
# 錯誤響應模型
# ============================================================================

class ErrorDetail(BaseModel):
    """錯誤詳情"""
    code: str = Field(..., description="錯誤碼")
    message: str = Field(..., description="錯誤消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="詳細信息")


class ErrorResponse(BaseModel):
    """錯誤響應"""
    success: bool = Field(default=False, description="操作失敗")
    error: ErrorDetail = Field(..., description="錯誤信息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="時間戳")


# ============================================================================
# 規則審查模型
# ============================================================================

class DraftStatus(str, Enum):
    """草稿狀態"""
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"

class ReviewStatus(str, Enum):
    """審查狀態"""
    PENDING = "pending"
    APPROVED = "approved"
    MODIFIED = "modified"
    REJECTED = "rejected"

class ReviewAction(str, Enum):
    """審查動作"""
    APPROVE = "approve"
    MODIFY = "modify"
    REJECT = "reject"

class RuleSetStatus(str, Enum):
    """規則集狀態"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ACTIVE = "active"
    DEPRECATED = "deprecated"

class Example(BaseModel):
    """規則示例"""
    before: str = Field(..., description="應用規則前的文本")
    after: str = Field(..., description="應用規則後的文本")

class ReviewProgress(BaseModel):
    """審查進度"""
    total: int = Field(..., description="總規則數")
    reviewed: int = Field(..., description="已審查數")
    approved: int = Field(..., description="已批准數")
    modified: int = Field(..., description="已修改數")
    rejected: int = Field(..., description="已拒絕數")

class DraftRule(BaseModel):
    """草稿規則"""
    rule_id: str = Field(..., description="規則ID")
    rule_type: str = Field(..., description="規則類型")
    natural_language: str = Field(..., description="自然語言描述")
    pattern: Optional[str] = Field(default=None, description="匹配模式")
    replacement: Optional[str] = Field(default=None, description="替換文本")
    conditions: Optional[Dict[str, Any]] = Field(default=None, description="應用條件")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    examples: List[Example] = Field(default_factory=list, description="示例列表")
    review_status: ReviewStatus = Field(default=ReviewStatus.PENDING, description="審查狀態")
    user_feedback: Optional[str] = Field(default=None, description="用戶反饋")
    modified_at: Optional[datetime] = Field(default=None, description="修改時間")
    modified_by: Optional[str] = Field(default=None, description="修改者")

class RuleDraft(BaseModel):
    """規則草稿"""
    draft_id: str = Field(..., description="草稿ID")
    rules: List[DraftRule] = Field(..., description="規則列表")
    status: DraftStatus = Field(..., description="草稿狀態")
    description: Optional[str] = Field(default=None, description="描述")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元數據")
    created_at: datetime = Field(..., description="創建時間")
    created_by: str = Field(..., description="創建者")
    review_progress: ReviewProgress = Field(..., description="審查進度")

# 規則草稿請求/響應模型

class SaveDraftRequest(BaseModel):
    """保存草稿請求"""
    rules: List[LearningRule] = Field(..., description="規則列表")
    description: Optional[str] = Field(default=None, description="描述")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元數據")

class SaveDraftResponse(BaseModel):
    """保存草稿響應"""
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="響應數據")

class DraftListResponse(BaseModel):
    """草稿列表響應"""
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="響應數據")

class DraftDetailResponse(BaseModel):
    """草稿詳情響應"""
    success: bool = Field(..., description="是否成功")
    data: RuleDraft = Field(..., description="草稿數據")

class ModifyRuleRequest(BaseModel):
    """修改規則請求"""
    natural_language: str = Field(..., description="自然語言描述")
    examples: Optional[List[Example]] = Field(default=None, description="示例")
    conditions: Optional[Dict[str, Any]] = Field(default=None, description="條件")

class ModifyRuleResponse(BaseModel):
    """修改規則響應"""
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="響應數據")

class ReviewItem(BaseModel):
    """審查項目"""
    rule_id: str = Field(..., description="規則ID")
    action: ReviewAction = Field(..., description="審查動作")
    comment: Optional[str] = Field(default=None, description="評論")
    natural_language: Optional[str] = Field(default=None, description="修改後的自然語言描述")

class BatchReviewRequest(BaseModel):
    """批量審查請求"""
    reviews: List[ReviewItem] = Field(..., description="審查列表")

class BatchReviewResponse(BaseModel):
    """批量審查響應"""
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="響應數據")

class PublishRulesRequest(BaseModel):
    """發布規則請求"""
    name: str = Field(..., description="規則集名稱")
    description: Optional[str] = Field(default=None, description="描述")
    include_rejected: bool = Field(default=False, description="是否包含拒絕的規則")
    activation_date: Optional[datetime] = Field(default=None, description="激活日期")
    test_mode: bool = Field(default=False, description="測試模式")

class PublishRulesResponse(BaseModel):
    """發布規則響應"""
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="響應數據")

class TestRulesRequest(BaseModel):
    """測試規則請求"""
    ruleset_id: Optional[str] = Field(default=None, description="規則集ID")
    rules: Optional[List[DraftRule]] = Field(default=None, description="要測試的規則")
    test_content: str = Field(..., description="測試內容")
    options: Optional[Dict[str, bool]] = Field(default=None, description="測試選項")

class TestRulesResponse(BaseModel):
    """測試規則響應"""
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="測試結果")

# ============================================================================
# WebSocket 消息模型
# ============================================================================

class WSMessage(BaseModel):
    """WebSocket 消息"""
    type: str = Field(..., description="消息類型")
    data: Dict[str, Any] = Field(..., description="消息數據")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="時間戳")


class WSDecisionUpdate(BaseModel):
    """決策更新消息"""
    decision_id: int = Field(..., description="決策ID")
    action: str = Field(..., description="動作: created|updated|deleted")
    decision: Optional[DecisionResponse] = Field(default=None, description="決策數據")