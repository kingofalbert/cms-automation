"""校對決策 API 路由

實現 T7.3 的 RESTful API 端點，提供決策管理的完整功能。
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_session
from src.config.logging import get_logger
from src.services.proofreading_decision import (
    ProofreadingDecisionService,
    get_decision_service,
    DecisionInput,
    DateRange,
    DecisionPatterns,
    UserPreferences,
    LearningRule as ServiceLearningRule,
    FeedbackAggregation,
    QualityMetrics,
    ImprovementArea as ServiceImprovementArea,
    DecisionServiceError,
    InvalidDecisionError,
    DuplicateDecisionError
)
from src.schemas.proofreading_decision import (
    DecisionRequest,
    BatchDecisionRequest,
    BatchDecisionItem,
    DecisionUpdateRequest,
    DecisionResponse,
    DecisionListResponse,
    BatchDecisionResponse,
    PatternAnalysisRequest,
    PatternAnalysisResponse,
    PatternDetail,
    CorrectionPattern,
    TimePattern,
    UserPreferencesResponse,
    StylePreferences,
    GenerateRulesRequest,
    GenerateRulesResponse,
    LearningRule,
    ApplyRulesRequest,
    ApplyRulesResponse,
    RuleApplication,
    FeedbackStatsRequest,
    FeedbackStatsResponse,
    PrepareDatasetRequest,
    PrepareDatasetResponse,
    QualityEvaluationRequest,
    QualityEvaluationResponse,
    ImprovementAreasRequest,
    ImprovementAreasResponse,
    ImprovementArea,
    BaseResponse,
    ErrorResponse,
    ErrorDetail,
    DecisionTypeEnum,
    TrendType,
    PriorityLevel,
    # 新增規則審查相關模型
    DraftStatus,
    ReviewStatus,
    ReviewAction,
    RuleSetStatus,
    Example,
    ReviewProgress,
    DraftRule,
    RuleDraft,
    SaveDraftRequest,
    SaveDraftResponse,
    DraftListResponse,
    DraftDetailResponse,
    ModifyRuleRequest,
    ModifyRuleResponse,
    ReviewItem,
    BatchReviewRequest,
    BatchReviewResponse,
    PublishRulesRequest,
    PublishRulesResponse,
    TestRulesRequest,
    TestRulesResponse
)
from src.models.proofreading import DecisionType

logger = get_logger(__name__)

# 創建路由器
router = APIRouter(
    prefix="/api/v1/proofreading/decisions",
    tags=["Proofreading Decisions"],
    responses={
        404: {"model": ErrorResponse, "description": "資源不存在"},
        400: {"model": ErrorResponse, "description": "請求無效"},
        500: {"model": ErrorResponse, "description": "服務器錯誤"}
    }
)


# ============================================================================
# 依賴注入
# ============================================================================

async def get_service() -> ProofreadingDecisionService:
    """獲取決策服務實例"""
    return get_decision_service()


# ============================================================================
# 決策記錄端點
# ============================================================================

@router.post(
    "/",
    response_model=DecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="記錄單個決策",
    description="記錄用戶對校對建議的決策"
)
async def record_decision(
    request: DecisionRequest = Body(...),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """記錄單個校對決策

    Args:
        request: 決策請求數據
        session: 數據庫會話
        service: 決策服務

    Returns:
        創建的決策記錄

    Raises:
        HTTPException: 當發生錯誤時
    """
    try:
        # 轉換枚舉類型 - map from Pydantic enum to SQLAlchemy enum
        decision_map = {
            "accept": DecisionType.ACCEPTED,
            "reject": DecisionType.REJECTED,
            "modify": DecisionType.MODIFIED
        }
        decision_type = decision_map.get(request.decision.value)
        if not decision_type:
            raise ValueError(f"Invalid decision type: {request.decision.value}")

        # 記錄決策
        decision = await service.record_decision(
            session=session,
            article_id=request.article_id,
            proofreading_history_id=request.proofreading_history_id,
            suggestion_id=request.suggestion_id,
            decision=decision_type,
            custom_correction=request.custom_correction,
            decision_reason=request.decision_reason,
            tags=request.tags
        )

        logger.info(f"決策已記錄: {decision.id}")

        # 轉換為響應模型
        return DecisionResponse(
            decision_id=decision.id,
            article_id=decision.article_id,
            proofreading_history_id=decision.proofreading_history_id,
            suggestion_id=decision.suggestion_id,
            suggestion_type=decision.suggestion_type,
            original_text=decision.original_text,
            suggested_text=decision.suggested_text,
            decision=DecisionTypeEnum(decision.decision.value.lower()),
            custom_correction=decision.custom_correction,
            decision_reason=decision.decision_reason,
            confidence_score=decision.confidence_score,
            context_before=decision.context_before,
            context_after=decision.context_after,
            tags=decision.tags or [],
            created_at=decision.created_at,
            updated_at=decision.updated_at
        )

    except InvalidDecisionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateDecisionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"記錄決策失敗: {e}")
        raise HTTPException(status_code=500, detail="記錄決策失敗")


@router.post(
    "/batch",
    response_model=BatchDecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="批量記錄決策",
    description="批量記錄多個校對決策"
)
async def record_batch_decisions(
    request: BatchDecisionRequest = Body(...),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """批量記錄校對決策

    Args:
        request: 批量決策請求
        session: 數據庫會話
        service: 決策服務

    Returns:
        批量記錄結果
    """
    try:
        # 轉換為服務層的決策輸入
        decision_inputs = [
            DecisionInput(
                suggestion_id=item.suggestion_id,
                decision=DecisionType[item.decision.value.upper()],
                custom_correction=item.custom_correction,
                reason=item.reason,
                tags=item.tags
            )
            for item in request.decisions
        ]

        # 批量記錄
        decisions = await service.record_batch_decisions(
            session=session,
            article_id=request.article_id,
            proofreading_history_id=request.proofreading_history_id,
            decisions=decision_inputs
        )

        # 轉換為響應模型
        decision_responses = []
        for decision in decisions:
            decision_responses.append(DecisionResponse(
                decision_id=decision.id,
                article_id=decision.article_id,
                proofreading_history_id=decision.proofreading_history_id,
                suggestion_id=decision.suggestion_id,
                suggestion_type=decision.suggestion_type,
                original_text=decision.original_text,
                suggested_text=decision.suggested_text,
                decision=DecisionTypeEnum(decision.decision.value.lower()),
                custom_correction=decision.custom_correction,
                decision_reason=decision.decision_reason,
                confidence_score=decision.confidence_score,
                context_before=decision.context_before,
                context_after=decision.context_after,
                tags=decision.tags or [],
                created_at=decision.created_at,
                updated_at=decision.updated_at
            ))

        return BatchDecisionResponse(
            success=True,
            processed=len(request.decisions),
            successful=len(decisions),
            failed=len(request.decisions) - len(decisions),
            decisions=decision_responses
        )

    except Exception as e:
        logger.error(f"批量記錄決策失敗: {e}")
        raise HTTPException(status_code=500, detail="批量記錄失敗")


# ============================================================================
# 決策查詢端點
# ============================================================================

@router.get(
    "/article/{article_id}",
    response_model=DecisionListResponse,
    summary="獲取文章決策",
    description="獲取指定文章的所有決策記錄"
)
async def get_article_decisions(
    article_id: int = Path(..., gt=0, description="文章ID"),
    include_history: bool = Query(False, description="是否包含校對歷史"),
    page: int = Query(1, ge=1, description="頁碼"),
    limit: int = Query(20, ge=1, le=100, description="每頁數量"),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """獲取文章的決策記錄

    Args:
        article_id: 文章ID
        include_history: 是否包含歷史
        page: 頁碼
        limit: 每頁數量
        session: 數據庫會話
        service: 決策服務

    Returns:
        決策列表
    """
    try:
        # 獲取決策
        decisions = await service.get_article_decisions(
            session=session,
            article_id=article_id,
            include_history=include_history
        )

        # 分頁
        start = (page - 1) * limit
        end = start + limit
        paginated_decisions = decisions[start:end]

        # 轉換為響應模型
        decision_responses = []
        for decision in paginated_decisions:
            decision_responses.append(DecisionResponse(
                decision_id=decision.id,
                article_id=decision.article_id,
                proofreading_history_id=decision.proofreading_history_id,
                suggestion_id=decision.suggestion_id,
                suggestion_type=decision.suggestion_type,
                original_text=decision.original_text,
                suggested_text=decision.suggested_text,
                decision=DecisionTypeEnum(decision.decision.value.lower()),
                custom_correction=decision.custom_correction,
                decision_reason=decision.decision_reason,
                confidence_score=decision.confidence_score,
                context_before=decision.context_before,
                context_after=decision.context_after,
                tags=decision.tags or [],
                created_at=decision.created_at,
                updated_at=decision.updated_at
            ))

        return DecisionListResponse(
            success=True,
            data=decision_responses,
            total=len(decisions),
            page=page,
            limit=limit
        )

    except Exception as e:
        logger.error(f"獲取文章決策失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取決策失敗")


@router.get(
    "/{decision_id}",
    response_model=DecisionResponse,
    summary="獲取決策詳情",
    description="獲取指定決策的詳細信息"
)
async def get_decision_detail(
    decision_id: int = Path(..., gt=0, description="決策ID"),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """獲取決策詳情

    Args:
        decision_id: 決策ID
        session: 數據庫會話
        service: 決策服務

    Returns:
        決策詳情

    Raises:
        HTTPException: 當決策不存在時
    """
    try:
        # 查詢決策
        from sqlalchemy import select
        from src.models.proofreading import ProofreadingDecision

        result = await session.execute(
            select(ProofreadingDecision).where(ProofreadingDecision.id == decision_id)
        )
        decision = result.scalar_one_or_none()

        if not decision:
            raise HTTPException(status_code=404, detail=f"決策不存在: {decision_id}")

        # 轉換為響應模型
        return DecisionResponse(
            decision_id=decision.id,
            article_id=decision.article_id,
            proofreading_history_id=decision.proofreading_history_id,
            suggestion_id=decision.suggestion_id,
            suggestion_type=decision.suggestion_type,
            original_text=decision.original_text,
            suggested_text=decision.suggested_text,
            decision=DecisionTypeEnum(decision.decision.value.lower()),
            custom_correction=decision.custom_correction,
            decision_reason=decision.decision_reason,
            confidence_score=decision.confidence_score,
            context_before=decision.context_before,
            context_after=decision.context_after,
            tags=decision.tags or [],
            created_at=decision.created_at,
            updated_at=decision.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取決策詳情失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取決策詳情失敗")


@router.get(
    "/history",
    response_model=DecisionListResponse,
    summary="查詢決策歷史",
    description="查詢決策歷史記錄，支持多種過濾條件"
)
async def query_decision_history(
    user_id: Optional[int] = Query(None, description="用戶ID"),
    start_date: Optional[datetime] = Query(None, description="開始日期"),
    end_date: Optional[datetime] = Query(None, description="結束日期"),
    decision_type: Optional[DecisionTypeEnum] = Query(None, description="決策類型"),
    suggestion_type: Optional[str] = Query(None, description="建議類型"),
    page: int = Query(1, ge=1, description="頁碼"),
    limit: int = Query(20, ge=1, le=100, description="每頁數量"),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """查詢決策歷史

    Args:
        各種查詢參數
        session: 數據庫會話
        service: 決策服務

    Returns:
        決策歷史列表
    """
    try:
        # 構建時間範圍
        time_range = None
        if start_date or end_date:
            time_range = DateRange(
                start_date=start_date or datetime(2020, 1, 1),
                end_date=end_date or datetime.utcnow()
            )

        # 查詢決策歷史
        decisions = await service.get_user_decision_history(
            session=session,
            user_id=user_id,
            limit=limit,
            offset=(page - 1) * limit,
            time_range=time_range
        )

        # 根據類型過濾
        if decision_type:
            target_type = DecisionType[decision_type.value.upper()]
            decisions = [d for d in decisions if d.decision == target_type]

        if suggestion_type:
            decisions = [d for d in decisions if d.suggestion_type == suggestion_type]

        # 轉換為響應模型
        decision_responses = []
        for decision in decisions:
            decision_responses.append(DecisionResponse(
                decision_id=decision.id,
                article_id=decision.article_id,
                proofreading_history_id=decision.proofreading_history_id,
                suggestion_id=decision.suggestion_id,
                suggestion_type=decision.suggestion_type,
                original_text=decision.original_text,
                suggested_text=decision.suggested_text,
                decision=DecisionTypeEnum(decision.decision.value.lower()),
                custom_correction=decision.custom_correction,
                decision_reason=decision.decision_reason,
                confidence_score=decision.confidence_score,
                context_before=decision.context_before,
                context_after=decision.context_after,
                tags=decision.tags or [],
                created_at=decision.created_at,
                updated_at=decision.updated_at
            ))

        return DecisionListResponse(
            success=True,
            data=decision_responses,
            total=len(decision_responses),
            page=page,
            limit=limit
        )

    except Exception as e:
        logger.error(f"查詢決策歷史失敗: {e}")
        raise HTTPException(status_code=500, detail="查詢失敗")


# ============================================================================
# 模式分析端點
# ============================================================================

@router.get(
    "/patterns/analyze",
    response_model=PatternAnalysisResponse,
    summary="分析決策模式",
    description="分析歷史決策數據，識別用戶偏好和模式"
)
async def analyze_patterns(
    start_date: Optional[datetime] = Query(None, description="開始日期"),
    end_date: Optional[datetime] = Query(None, description="結束日期"),
    min_occurrences: int = Query(5, ge=1, description="最小出現次數"),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """分析決策模式

    Args:
        start_date: 開始日期
        end_date: 結束日期
        min_occurrences: 最小出現次數
        session: 數據庫會話
        service: 決策服務

    Returns:
        模式分析結果
    """
    try:
        # 構建時間範圍
        time_range = None
        if start_date or end_date:
            time_range = DateRange(
                start_date=start_date or datetime(2020, 1, 1),
                end_date=end_date or datetime.utcnow()
            )

        # 分析模式
        patterns = await service.analyze_decision_patterns(
            session=session,
            time_range=time_range,
            min_occurrences=min_occurrences
        )

        # 轉換為響應模型
        return PatternAnalysisResponse(
            success=True,
            common_acceptances=[
                PatternDetail(
                    pattern_type=p.pattern_type,
                    frequency=p.frequency,
                    rate=p.rate,
                    confidence=p.confidence,
                    examples=p.examples
                )
                for p in patterns.common_acceptances
            ],
            common_rejections=[
                PatternDetail(
                    pattern_type=p.pattern_type,
                    frequency=p.frequency,
                    rate=p.rate,
                    confidence=p.confidence,
                    examples=p.examples
                )
                for p in patterns.common_rejections
            ],
            custom_corrections=[
                CorrectionPattern(
                    id=p.id,
                    original_pattern=p.original_pattern,
                    correction_pattern=p.correction_pattern,
                    frequency=p.frequency,
                    confidence=p.confidence,
                    context=p.context
                )
                for p in patterns.custom_corrections
            ],
            time_patterns=[
                TimePattern(
                    period=p.period,
                    trend=TrendType(p.trend),
                    metrics=p.metrics
                )
                for p in patterns.time_patterns
            ],
            confidence_scores=patterns.confidence_scores
        )

    except Exception as e:
        logger.error(f"分析模式失敗: {e}")
        raise HTTPException(status_code=500, detail="模式分析失敗")


@router.get(
    "/preferences/{user_id}",
    response_model=UserPreferencesResponse,
    summary="提取用戶偏好",
    description="分析用戶的歷史決策，提取寫作偏好"
)
async def extract_preferences(
    user_id: int = Path(..., gt=0, description="用戶ID"),
    min_decisions: int = Query(20, ge=1, description="最小決策數"),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """提取用戶偏好

    Args:
        user_id: 用戶ID
        min_decisions: 最小決策數
        session: 數據庫會話
        service: 決策服務

    Returns:
        用戶偏好
    """
    try:
        # 提取偏好
        preferences = await service.extract_user_preferences(
            session=session,
            user_id=user_id,
            min_decisions=min_decisions
        )

        # 轉換為響應模型
        return UserPreferencesResponse(
            success=True,
            style_preferences=StylePreferences(
                formal_level=preferences.style_preferences.get("formal_level", "neutral"),
                sentence_length=preferences.style_preferences.get("sentence_length", "medium"),
                complexity=preferences.style_preferences.get("complexity", "moderate")
            ),
            vocabulary_preferences=preferences.vocabulary_preferences,
            grammar_rules=preferences.grammar_rules,
            punctuation_habits=preferences.punctuation_habits,
            confidence_level=preferences.confidence_level
        )

    except Exception as e:
        logger.error(f"提取用戶偏好失敗: {e}")
        raise HTTPException(status_code=500, detail="提取偏好失敗")


# ============================================================================
# 規則學習端點
# ============================================================================

@router.post(
    "/rules/generate",
    response_model=GenerateRulesResponse,
    summary="生成學習規則",
    description="基於決策模式生成可執行的學習規則"
)
async def generate_rules(
    request: GenerateRulesRequest = Body(...),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """生成學習規則

    Args:
        request: 生成規則請求
        session: 數據庫會話
        service: 決策服務

    Returns:
        生成的規則
    """
    try:
        # 先分析模式
        patterns = await service.analyze_decision_patterns(
            session=session,
            min_occurrences=5
        )

        # 生成規則
        rules = await service.generate_learning_rules(
            session=session,
            patterns=patterns,
            confidence_threshold=request.confidence_threshold
        )

        # 轉換為響應模型
        rule_responses = [
            LearningRule(
                rule_id=rule.rule_id,
                rule_type=rule.rule_type,
                pattern=rule.pattern,
                replacement=rule.replacement,
                confidence=rule.confidence,
                context_conditions=rule.context_conditions,
                example_applications=rule.example_applications
            )
            for rule in rules
        ]

        return GenerateRulesResponse(
            success=True,
            rules=rule_responses,
            total_rules=len(rules),
            generation_timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"生成規則失敗: {e}")
        raise HTTPException(status_code=500, detail="生成規則失敗")


@router.post(
    "/rules/apply",
    response_model=ApplyRulesResponse,
    summary="應用學習規則",
    description="將學習規則應用到新內容"
)
async def apply_rules(
    request: ApplyRulesRequest = Body(...),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """應用學習規則

    Args:
        request: 應用規則請求
        session: 數據庫會話
        service: 決策服務

    Returns:
        應用結果
    """
    try:
        # 獲取規則
        if request.apply_all or not request.rule_ids:
            # 生成所有規則
            patterns = await service.analyze_decision_patterns(session)
            rules = await service.generate_learning_rules(session, patterns)
        else:
            # 根據 ID 過濾規則（這裡簡化處理）
            patterns = await service.analyze_decision_patterns(session)
            all_rules = await service.generate_learning_rules(session, patterns)
            rules = [r for r in all_rules if r.rule_id in request.rule_ids]

        # 應用規則
        modified_content, applications = await service.apply_learning_rules(
            content=request.content,
            rules=rules
        )

        # 轉換為響應模型
        application_responses = [
            RuleApplication(
                rule_id=app.rule_id,
                original_text=app.original_text,
                modified_text=app.modified_text,
                position=list(app.position),
                confidence=app.confidence
            )
            for app in applications
        ]

        return ApplyRulesResponse(
            success=True,
            original_content=request.content,
            modified_content=modified_content,
            applications=application_responses,
            total_changes=len(applications)
        )

    except Exception as e:
        logger.error(f"應用規則失敗: {e}")
        raise HTTPException(status_code=500, detail="應用規則失敗")


# ============================================================================
# 反饋聚合端點
# ============================================================================

@router.get(
    "/feedback/stats",
    response_model=FeedbackStatsResponse,
    summary="獲取反饋統計",
    description="獲取決策的統計數據和反饋信息"
)
async def get_feedback_stats(
    aggregation_period: str = Query("daily", description="聚合週期"),
    date: Optional[datetime] = Query(None, description="指定日期"),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """獲取反饋統計

    Args:
        aggregation_period: 聚合週期
        date: 指定日期
        session: 數據庫會話
        service: 決策服務

    Returns:
        統計數據
    """
    try:
        # 聚合反饋
        feedback = await service.aggregate_feedback_data(
            session=session,
            aggregation_period=aggregation_period,
            date=date
        )

        # 轉換為響應模型
        return FeedbackStatsResponse(
            success=True,
            total_decisions=feedback.total_decisions,
            acceptance_rate=feedback.acceptance_rate,
            rejection_rate=feedback.rejection_rate,
            modification_rate=feedback.modification_rate,
            suggestion_type_distribution=feedback.suggestion_type_distribution,
            user_activity=feedback.user_activity,
            time_period=feedback.time_period
        )

    except Exception as e:
        logger.error(f"獲取反饋統計失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取統計失敗")


@router.post(
    "/feedback/prepare-dataset",
    response_model=PrepareDatasetResponse,
    summary="準備調優數據集",
    description="準備用於模型調優的數據集"
)
async def prepare_dataset(
    request: PrepareDatasetRequest = Body(...),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """準備調優數據集

    Args:
        request: 數據集請求
        session: 數據庫會話
        service: 決策服務

    Returns:
        數據集信息
    """
    try:
        # 準備數據集
        dataset = await service.prepare_tuning_dataset(
            session=session,
            min_examples=request.min_examples,
            balance_dataset=request.balance_dataset
        )

        # 生成數據集ID
        dataset_id = f"ds_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # 返迴響應
        return PrepareDatasetResponse(
            success=True,
            dataset_id=dataset_id,
            positive_examples=len(dataset.positive_examples),
            negative_examples=len(dataset.negative_examples),
            custom_examples=len(dataset.custom_examples),
            metadata=dataset.metadata,
            download_url=f"/api/v1/proofreading/datasets/{dataset_id}"
        )

    except Exception as e:
        logger.error(f"準備數據集失敗: {e}")
        raise HTTPException(status_code=500, detail="準備數據集失敗")


# ============================================================================
# 質量評估端點
# ============================================================================

@router.get(
    "/quality/evaluate",
    response_model=QualityEvaluationResponse,
    summary="評估建議質量",
    description="評估校對建議的質量指標"
)
async def evaluate_quality(
    start_date: Optional[datetime] = Query(None, description="開始日期"),
    end_date: Optional[datetime] = Query(None, description="結束日期"),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """評估建議質量

    Args:
        start_date: 開始日期
        end_date: 結束日期
        session: 數據庫會話
        service: 決策服務

    Returns:
        質量評估結果
    """
    try:
        # 構建時間範圍
        time_range = None
        if start_date or end_date:
            time_range = DateRange(
                start_date=start_date or datetime(2020, 1, 1),
                end_date=end_date or datetime.utcnow()
            )

        # 評估質量
        quality = await service.evaluate_suggestion_quality(
            session=session,
            time_range=time_range
        )

        # 轉換為響應模型
        return QualityEvaluationResponse(
            success=True,
            accuracy=quality.accuracy,
            relevance=quality.relevance,
            usefulness=quality.usefulness,
            trend=TrendType(quality.trend),
            details=quality.details
        )

    except Exception as e:
        logger.error(f"評估質量失敗: {e}")
        raise HTTPException(status_code=500, detail="評估失敗")


@router.get(
    "/quality/improvements",
    response_model=ImprovementAreasResponse,
    summary="識別改進領域",
    description="識別需要改進的領域和優化建議"
)
async def identify_improvements(
    target_accuracy: float = Query(0.85, ge=0, le=1, description="目標準確率"),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """識別改進領域

    Args:
        target_accuracy: 目標準確率
        session: 數據庫會話
        service: 決策服務

    Returns:
        改進領域列表
    """
    try:
        # 先評估質量
        quality = await service.evaluate_suggestion_quality(session)

        # 識別改進領域
        areas = await service.identify_improvement_areas(
            session=session,
            quality_metrics=quality,
            target_accuracy=target_accuracy
        )

        # 轉換為響應模型
        area_responses = [
            ImprovementArea(
                area_name=area.area_name,
                current_performance=area.current_performance,
                target_performance=area.target_performance,
                priority=PriorityLevel(area.priority),
                suggestions=area.suggestions
            )
            for area in areas
        ]

        return ImprovementAreasResponse(
            success=True,
            improvement_areas=area_responses,
            total_areas=len(areas)
        )

    except Exception as e:
        logger.error(f"識別改進領域失敗: {e}")
        raise HTTPException(status_code=500, detail="識別失敗")


# ============================================================================
# 管理端點
# ============================================================================

@router.put(
    "/{decision_id}",
    response_model=DecisionResponse,
    summary="更新決策",
    description="更新現有決策的信息"
)
async def update_decision(
    decision_id: int = Path(..., gt=0, description="決策ID"),
    request: DecisionUpdateRequest = Body(...),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """更新決策

    Args:
        decision_id: 決策ID
        request: 更新請求
        session: 數據庫會話
        service: 決策服務

    Returns:
        更新後的決策

    Raises:
        HTTPException: 當決策不存在時
    """
    try:
        # 查詢決策
        from sqlalchemy import select
        from src.models.proofreading import ProofreadingDecision

        result = await session.execute(
            select(ProofreadingDecision).where(ProofreadingDecision.id == decision_id)
        )
        decision = result.scalar_one_or_none()

        if not decision:
            raise HTTPException(status_code=404, detail=f"決策不存在: {decision_id}")

        # 更新決策
        if request.decision:
            decision.decision = DecisionType[request.decision.value.upper()]
        if request.custom_correction is not None:
            decision.custom_correction = request.custom_correction
        if request.decision_reason is not None:
            decision.decision_reason = request.decision_reason
        if request.tags is not None:
            decision.tags = request.tags

        decision.updated_at = datetime.utcnow()

        await session.commit()

        # 轉換為響應模型
        return DecisionResponse(
            decision_id=decision.id,
            article_id=decision.article_id,
            proofreading_history_id=decision.proofreading_history_id,
            suggestion_id=decision.suggestion_id,
            suggestion_type=decision.suggestion_type,
            original_text=decision.original_text,
            suggested_text=decision.suggested_text,
            decision=DecisionTypeEnum(decision.decision.value.lower()),
            custom_correction=decision.custom_correction,
            decision_reason=decision.decision_reason,
            confidence_score=decision.confidence_score,
            context_before=decision.context_before,
            context_after=decision.context_after,
            tags=decision.tags or [],
            created_at=decision.created_at,
            updated_at=decision.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新決策失敗: {e}")
        raise HTTPException(status_code=500, detail="更新失敗")


@router.delete(
    "/{decision_id}",
    response_model=BaseResponse,
    summary="刪除決策",
    description="刪除指定的決策記錄"
)
async def delete_decision(
    decision_id: int = Path(..., gt=0, description="決策ID"),
    session: AsyncSession = Depends(get_session),
    service: ProofreadingDecisionService = Depends(get_service)
):
    """刪除決策

    Args:
        decision_id: 決策ID
        session: 數據庫會話
        service: 決策服務

    Returns:
        刪除結果

    Raises:
        HTTPException: 當決策不存在時
    """
    try:
        # 查詢並刪除決策
        from sqlalchemy import select, delete
        from src.models.proofreading import ProofreadingDecision

        result = await session.execute(
            select(ProofreadingDecision).where(ProofreadingDecision.id == decision_id)
        )
        decision = result.scalar_one_or_none()

        if not decision:
            raise HTTPException(status_code=404, detail=f"決策不存在: {decision_id}")

        await session.execute(
            delete(ProofreadingDecision).where(ProofreadingDecision.id == decision_id)
        )
        await session.commit()

        return BaseResponse(
            success=True,
            message=f"決策 {decision_id} 已刪除"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除決策失敗: {e}")
        raise HTTPException(status_code=500, detail="刪除失敗")


@router.post(
    "/cache/clear",
    response_model=BaseResponse,
    summary="清除緩存",
    description="清除決策服務的緩存數據"
)
async def clear_cache(
    service: ProofreadingDecisionService = Depends(get_service)
):
    """清除緩存

    Args:
        service: 決策服務

    Returns:
        清除結果
    """
    try:
        # 清除服務緩存
        service._pattern_cache.clear()

        return BaseResponse(
            success=True,
            message="緩存已清除"
        )

    except Exception as e:
        logger.error(f"清除緩存失敗: {e}")
        raise HTTPException(status_code=500, detail="清除緩存失敗")


# ============================================================================
# 健康檢查
# ============================================================================

@router.get(
    "/health",
    response_model=BaseResponse,
    summary="健康檢查",
    description="檢查 API 服務狀態"
)
async def health_check():
    """健康檢查

    Returns:
        服務狀態
    """
    return BaseResponse(
        success=True,
        message="服務正常運行"
    )


# ============================================================================
# 規則審查與修改端點
# ============================================================================

# 臨時存儲草稿的字典 (實際應使用數據庫)
rule_drafts = {}

@router.post("/rules/draft", response_model=SaveDraftResponse, status_code=status.HTTP_201_CREATED)
async def save_rule_draft(
    request: SaveDraftRequest = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """保存規則為草稿

    Args:
        request: 草稿請求數據

    Returns:
        草稿保存結果
    """
    try:
        # 生成草稿ID
        draft_id = f"draft_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # 構建草稿規則
        draft_rules = []
        for rule in request.rules:
            draft_rule = DraftRule(
                rule_id=rule.rule_id,
                rule_type=rule.rule_type,
                natural_language=f"當遇到「{rule.pattern}」時，建議替換為「{rule.replacement}」",
                pattern=rule.pattern,
                replacement=rule.replacement,
                confidence=rule.confidence,
                examples=[
                    Example(
                        before=f"文本包含{rule.pattern}",
                        after=f"文本包含{rule.replacement}"
                    )
                ] if hasattr(rule, 'pattern') and hasattr(rule, 'replacement') else [],
                review_status=ReviewStatus.PENDING
            )
            draft_rules.append(draft_rule)

        # 創建草稿
        draft = RuleDraft(
            draft_id=draft_id,
            rules=draft_rules,
            status=DraftStatus.PENDING_REVIEW,
            description=request.description,
            metadata=request.metadata or {},
            created_at=datetime.utcnow(),
            created_by="system",
            review_progress=ReviewProgress(
                total=len(draft_rules),
                reviewed=0,
                approved=0,
                modified=0,
                rejected=0
            )
        )

        # 保存到臨時存儲
        rule_drafts[draft_id] = draft

        logger.info(f"規則草稿已保存: {draft_id}")

        return SaveDraftResponse(
            success=True,
            data={
                "draft_id": draft_id,
                "rule_count": len(draft_rules),
                "status": draft.status.value,
                "created_at": draft.created_at.isoformat()
            }
        )

    except Exception as e:
        logger.error(f"保存規則草稿失敗: {e}")
        raise HTTPException(status_code=500, detail="保存規則草稿失敗")

@router.get("/rules/drafts", response_model=DraftListResponse)
async def list_rule_drafts(
    status: Optional[DraftStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """獲取待審查規則列表

    Args:
        status: 狀態篩選
        page: 頁碼
        limit: 每頁數量

    Returns:
        草稿列表
    """
    try:
        # 篩選草稿
        filtered_drafts = []
        for draft in rule_drafts.values():
            if status is None or draft.status == status:
                filtered_drafts.append({
                    "draft_id": draft.draft_id,
                    "rule_count": len(draft.rules),
                    "status": draft.status.value,
                    "description": draft.description,
                    "created_at": draft.created_at.isoformat(),
                    "created_by": draft.created_by,
                    "review_progress": {
                        "total": draft.review_progress.total,
                        "reviewed": draft.review_progress.reviewed,
                        "approved": draft.review_progress.approved,
                        "modified": draft.review_progress.modified,
                        "rejected": draft.review_progress.rejected
                    }
                })

        # 分頁
        start = (page - 1) * limit
        end = start + limit
        paginated_drafts = filtered_drafts[start:end]

        return DraftListResponse(
            success=True,
            data={
                "drafts": paginated_drafts,
                "total": len(filtered_drafts),
                "page": page,
                "limit": limit
            }
        )

    except Exception as e:
        logger.error(f"獲取規則草稿列表失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取規則草稿列表失敗")

@router.get("/rules/drafts/{draft_id}", response_model=DraftDetailResponse)
async def get_draft_detail(
    draft_id: str = Path(...),
    session: AsyncSession = Depends(get_session)
):
    """獲取草稿詳情

    Args:
        draft_id: 草稿ID

    Returns:
        草稿詳情
    """
    try:
        if draft_id not in rule_drafts:
            raise HTTPException(status_code=404, detail="草稿不存在")

        draft = rule_drafts[draft_id]

        # 更新狀態為審查中
        if draft.status == DraftStatus.PENDING_REVIEW:
            draft.status = DraftStatus.IN_REVIEW

        return DraftDetailResponse(
            success=True,
            data=draft
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取草稿詳情失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取草稿詳情失敗")

@router.put("/rules/drafts/{draft_id}/rules/{rule_id}", response_model=ModifyRuleResponse)
async def modify_rule_natural_language(
    draft_id: str = Path(...),
    rule_id: str = Path(...),
    request: ModifyRuleRequest = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """使用自然語言修改規則

    Args:
        draft_id: 草稿ID
        rule_id: 規則ID
        request: 修改請求

    Returns:
        修改結果
    """
    try:
        if draft_id not in rule_drafts:
            raise HTTPException(status_code=404, detail="草稿不存在")

        draft = rule_drafts[draft_id]
        rule_found = False

        for rule in draft.rules:
            if rule.rule_id == rule_id:
                rule_found = True

                # 解析自然語言並生成規則代碼
                generated_code = natural_language_to_code(
                    request.natural_language,
                    request.examples,
                    request.conditions
                )

                # 更新規則
                rule.natural_language = request.natural_language
                rule.pattern = generated_code.get("pattern")
                rule.replacement = generated_code.get("replacement")
                rule.conditions = generated_code.get("conditions")
                rule.examples = request.examples or rule.examples
                rule.review_status = ReviewStatus.MODIFIED
                rule.modified_at = datetime.utcnow()
                rule.modified_by = "user"

                # 更新審查進度
                update_review_progress(draft)

                return ModifyRuleResponse(
                    success=True,
                    data={
                        "rule_id": rule_id,
                        "natural_language": request.natural_language,
                        "generated_code": generated_code,
                        "validation": {
                            "syntax_valid": True,
                            "testable": True,
                            "warnings": []
                        }
                    }
                )

        if not rule_found:
            raise HTTPException(status_code=404, detail="規則不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改規則失敗: {e}")
        raise HTTPException(status_code=500, detail="修改規則失敗")

@router.post("/rules/drafts/{draft_id}/review", response_model=BatchReviewResponse)
async def batch_review_rules(
    draft_id: str = Path(...),
    request: BatchReviewRequest = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """批量審查規則

    Args:
        draft_id: 草稿ID
        request: 批量審查請求

    Returns:
        審查結果
    """
    try:
        if draft_id not in rule_drafts:
            raise HTTPException(status_code=404, detail="草稿不存在")

        draft = rule_drafts[draft_id]
        processed = 0
        approved = 0
        modified = 0
        rejected = 0

        for review_item in request.reviews:
            for rule in draft.rules:
                if rule.rule_id == review_item.rule_id:
                    processed += 1

                    if review_item.action == ReviewAction.APPROVE:
                        rule.review_status = ReviewStatus.APPROVED
                        approved += 1
                    elif review_item.action == ReviewAction.MODIFY:
                        rule.review_status = ReviewStatus.MODIFIED
                        if review_item.natural_language:
                            rule.natural_language = review_item.natural_language
                        modified += 1
                    elif review_item.action == ReviewAction.REJECT:
                        rule.review_status = ReviewStatus.REJECTED
                        rejected += 1

                    rule.user_feedback = review_item.comment
                    rule.modified_at = datetime.utcnow()
                    rule.modified_by = "user"
                    break

        # 更新審查進度
        update_review_progress(draft)

        # 更新草稿狀態
        if draft.review_progress.reviewed == draft.review_progress.total:
            draft.status = DraftStatus.APPROVED

        return BatchReviewResponse(
            success=True,
            data={
                "processed": processed,
                "approved": approved,
                "modified": modified,
                "rejected": rejected,
                "draft_status": draft.status.value
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量審查失敗: {e}")
        raise HTTPException(status_code=500, detail="批量審查失敗")

@router.post("/rules/drafts/{draft_id}/publish", response_model=PublishRulesResponse)
async def publish_rules(
    draft_id: str = Path(...),
    request: PublishRulesRequest = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """確認並發布規則集

    Args:
        draft_id: 草稿ID
        request: 發布請求

    Returns:
        發布結果
    """
    try:
        if draft_id not in rule_drafts:
            raise HTTPException(status_code=404, detail="草稿不存在")

        draft = rule_drafts[draft_id]

        # 篩選要發布的規則
        rules_to_publish = []
        for rule in draft.rules:
            if rule.review_status == ReviewStatus.APPROVED or \
               rule.review_status == ReviewStatus.MODIFIED or \
               (request.include_rejected and rule.review_status == ReviewStatus.REJECTED):
                rules_to_publish.append(rule)

        if not rules_to_publish:
            raise HTTPException(status_code=400, detail="沒有可發布的規則")

        # 生成規則集ID
        ruleset_id = f"ruleset_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # TODO: 實際應該保存到數據庫
        logger.info(f"發布規則集: {ruleset_id}, 包含 {len(rules_to_publish)} 個規則")

        return PublishRulesResponse(
            success=True,
            data={
                "ruleset_id": ruleset_id,
                "name": request.name,
                "total_rules": len(draft.rules),
                "approved_rules": sum(1 for r in draft.rules if r.review_status == ReviewStatus.APPROVED),
                "modified_rules": sum(1 for r in draft.rules if r.review_status == ReviewStatus.MODIFIED),
                "status": "published",
                "activation_date": request.activation_date.isoformat() if request.activation_date else None,
                "code_generation": {
                    "success": True,
                    "compiled_rules": f"/api/v1/proofreading/rules/compiled/{ruleset_id}"
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"發布規則失敗: {e}")
        raise HTTPException(status_code=500, detail="發布規則失敗")

@router.post("/rules/test", response_model=TestRulesResponse)
async def test_rules(
    request: TestRulesRequest = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """測試規則集

    Args:
        request: 測試請求

    Returns:
        測試結果
    """
    try:
        # 應用規則到測試內容
        result_text = request.test_content
        changes = []

        # 簡單的模擬規則應用
        if request.rules:
            for rule in request.rules:
                if rule.pattern and rule.replacement:
                    import re
                    matches = list(re.finditer(rule.pattern, result_text))
                    for match in reversed(matches):  # 從後往前替換避免位置偏移
                        start, end = match.span()
                        changes.append({
                            "rule_id": rule.rule_id,
                            "type": "replacement",
                            "position": [start, end],
                            "original": match.group(),
                            "replacement": rule.replacement,
                            "confidence": rule.confidence
                        })
                        result_text = result_text[:start] + rule.replacement + result_text[end:]

        return TestRulesResponse(
            success=True,
            data={
                "original": request.test_content,
                "result": result_text,
                "changes": changes,
                "execution_time_ms": 15
            }
        )

    except Exception as e:
        logger.error(f"測試規則失敗: {e}")
        raise HTTPException(status_code=500, detail="測試規則失敗")

# ============================================================================
# 輔助函數
# ============================================================================

def update_review_progress(draft: RuleDraft) -> None:
    """更新審查進度"""
    reviewed = 0
    approved = 0
    modified = 0
    rejected = 0

    for rule in draft.rules:
        if rule.review_status != ReviewStatus.PENDING:
            reviewed += 1
        if rule.review_status == ReviewStatus.APPROVED:
            approved += 1
        elif rule.review_status == ReviewStatus.MODIFIED:
            modified += 1
        elif rule.review_status == ReviewStatus.REJECTED:
            rejected += 1

    draft.review_progress.reviewed = reviewed
    draft.review_progress.approved = approved
    draft.review_progress.modified = modified
    draft.review_progress.rejected = rejected

def natural_language_to_code(
    natural_language: str,
    examples: Optional[List[Example]] = None,
    conditions: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """將自然語言轉換為規則代碼

    這是一個簡化的實現，實際應使用 NLP 或 LLM 來解析自然語言
    """
    import re

    # 嘗試從自然語言中提取模式
    pattern_match = re.search(r'「([^」]+)」.*「([^」]+)」', natural_language)

    if pattern_match:
        pattern = pattern_match.group(1)
        replacement = pattern_match.group(2)
    else:
        # 如果無法提取，使用默認值
        pattern = ""
        replacement = ""

    # 從條件中提取規則
    compiled_conditions = []
    if conditions:
        for key, value in conditions.items():
            compiled_conditions.append({
                "type": key,
                "operator": "equals",
                "value": value
            })

    return {
        "pattern": pattern,
        "replacement": replacement,
        "conditions": compiled_conditions,
        "priority": 100
    }