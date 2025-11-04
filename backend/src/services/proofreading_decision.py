"""校對決策服務

處理校對決策的記錄、分析、學習和優化。
實現 T7.2 的核心業務邏輯。
"""

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.logging import get_logger
from src.config.settings import get_settings
from src.models.article import Article
from src.models.proofreading import (
    DecisionType,
    FeedbackTuningJob,
    ProofreadingDecision,
    ProofreadingHistory,
    TuningJobStatus,
    TuningJobType,
)

# ============================================================================
# 數據模型定義
# ============================================================================

@dataclass
class DecisionInput:
    """決策輸入"""
    suggestion_id: str
    decision: DecisionType
    custom_correction: str | None = None
    reason: str | None = None
    tags: list[str] | None = None


@dataclass
class DateRange:
    """日期範圍"""
    start_date: datetime
    end_date: datetime


@dataclass
class PatternDetail:
    """模式詳情"""
    pattern_type: str
    frequency: int
    rate: float
    examples: list[str]
    confidence: float


@dataclass
class CorrectionPattern:
    """修正模式"""
    id: str
    original_pattern: str
    correction_pattern: str
    frequency: int
    confidence: float
    context: dict[str, Any]


@dataclass
class TimePattern:
    """時間模式"""
    period: str
    trend: str  # "increasing", "decreasing", "stable"
    metrics: dict[str, float]


@dataclass
class DecisionPatterns:
    """決策模式"""
    common_acceptances: list[PatternDetail]
    common_rejections: list[PatternDetail]
    custom_corrections: list[CorrectionPattern]
    time_patterns: list[TimePattern]
    confidence_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class UserPreferences:
    """用戶偏好"""
    style_preferences: dict[str, Any] = field(default_factory=dict)
    vocabulary_preferences: list[str] = field(default_factory=list)
    grammar_rules: list[str] = field(default_factory=list)
    punctuation_habits: dict[str, str] = field(default_factory=dict)
    confidence_level: float = 0.0


@dataclass
class LearningRule:
    """學習規則"""
    rule_id: str
    rule_type: str  # "replacement", "style", "grammar"
    pattern: str
    replacement: str | None = None
    context_conditions: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    example_applications: list[str] = field(default_factory=list)


@dataclass
class RuleApplication:
    """規則應用結果"""
    rule_id: str
    original_text: str
    modified_text: str
    position: tuple[int, int]
    confidence: float


@dataclass
class FeedbackAggregation:
    """反饋聚合數據"""
    total_decisions: int
    acceptance_rate: float
    rejection_rate: float
    modification_rate: float
    suggestion_type_distribution: dict[str, int]
    user_activity: dict[str, int]
    time_period: str


@dataclass
class TuningDataset:
    """模型調優數據集"""
    positive_examples: list[dict[str, str]]
    negative_examples: list[dict[str, str]]
    custom_examples: list[dict[str, str]]
    metadata: dict[str, Any]


@dataclass
class QualityMetrics:
    """質量指標"""
    accuracy: float
    relevance: float
    usefulness: float
    trend: str  # "improving", "declining", "stable"
    details: dict[str, float]


@dataclass
class ImprovementArea:
    """改進領域"""
    area_name: str
    current_performance: float
    target_performance: float
    suggestions: list[str]
    priority: str  # "high", "medium", "low"


# ============================================================================
# 異常定義
# ============================================================================

class DecisionServiceError(Exception):
    """決策服務基礎異常"""
    pass


class DuplicateDecisionError(DecisionServiceError):
    """重複決策異常"""
    pass


class InvalidDecisionError(DecisionServiceError):
    """無效決策異常"""
    pass


class PatternAnalysisError(DecisionServiceError):
    """模式分析異常"""
    pass


# ============================================================================
# 服務實現
# ============================================================================

class ProofreadingDecisionService:
    """校對決策服務

    處理校對決策的完整生命週期：
    1. 記錄決策
    2. 分析模式
    3. 提取規則
    4. 優化建議
    """

    def __init__(self):
        """初始化服務"""
        self.logger = get_logger(__name__)
        self.settings = get_settings()
        self.min_pattern_threshold = 5  # 形成模式的最小決策數
        self.confidence_threshold = 0.8  # 規則置信度閾值
        self.cache_ttl = 3600  # 緩存時間（秒）
        self._pattern_cache: dict[str, DecisionPatterns] = {}

    # ========================================================================
    # 決策記錄方法
    # ========================================================================

    async def record_decision(
        self,
        session: AsyncSession,
        article_id: int,
        proofreading_history_id: int,
        suggestion_id: str,
        decision: DecisionType,
        custom_correction: str | None = None,
        decision_reason: str | None = None,
        tags: list[str] | None = None
    ) -> ProofreadingDecision:
        """記錄單個校對決策

        Args:
            session: 數據庫會話
            article_id: 文章ID
            proofreading_history_id: 校對歷史ID
            suggestion_id: 建議ID
            decision: 決策類型
            custom_correction: 自定義修正
            decision_reason: 決策原因
            tags: 標籤列表

        Returns:
            創建的決策記錄
        """
        try:
            # 1. 驗證輸入
            await self._validate_decision_input(
                session, article_id, proofreading_history_id, suggestion_id
            )

            # 2. 檢查重複
            existing = await self._check_existing_decision(
                session, article_id, suggestion_id
            )
            if existing:
                # 更新現有決策
                existing.decision = decision
                existing.custom_correction = custom_correction
                existing.decision_reason = decision_reason
                existing.updated_at = datetime.utcnow()
                await session.commit()
                self.logger.info(f"更新決策: article={article_id}, suggestion={suggestion_id}")
                return existing

            # 3. 獲取建議詳情
            suggestion_detail = await self._get_suggestion_detail(
                session, proofreading_history_id, suggestion_id
            )

            # 4. 創建決策記錄
            new_decision = ProofreadingDecision(
                article_id=article_id,
                proofreading_history_id=proofreading_history_id,
                suggestion_id=suggestion_id,
                suggestion_type=suggestion_detail.get("type", "unknown"),
                original_text=suggestion_detail.get("original", ""),
                suggested_text=suggestion_detail.get("suggested", ""),
                decision=decision,
                custom_correction=custom_correction,
                decision_reason=decision_reason,
                confidence_score=await self._calculate_confidence(
                    session, decision, suggestion_detail
                ),
                context_before=suggestion_detail.get("context_before", ""),
                context_after=suggestion_detail.get("context_after", ""),
                tags=tags or []
            )

            # 5. 保存到數據庫
            session.add(new_decision)
            await session.commit()

            self.logger.info(
                f"記錄決策: article={article_id}, suggestion={suggestion_id}, "
                f"decision={decision}"
            )

            # 6. 觸發異步學習（如果達到閾值）
            if await self._should_trigger_learning(session, article_id):
                await self._trigger_async_learning(session, article_id)

            return new_decision

        except Exception as e:
            self.logger.error(f"記錄決策失敗: {e}")
            await session.rollback()
            raise DecisionServiceError(f"記錄決策失敗: {str(e)}")

    async def record_batch_decisions(
        self,
        session: AsyncSession,
        article_id: int,
        proofreading_history_id: int,
        decisions: list[DecisionInput]
    ) -> list[ProofreadingDecision]:
        """批量記錄多個決策

        Args:
            session: 數據庫會話
            article_id: 文章ID
            proofreading_history_id: 校對歷史ID
            decisions: 決策輸入列表

        Returns:
            創建的決策記錄列表
        """
        created_decisions = []

        try:
            # 開始事務
            async with session.begin_nested():
                for decision_input in decisions:
                    decision = await self.record_decision(
                        session=session,
                        article_id=article_id,
                        proofreading_history_id=proofreading_history_id,
                        suggestion_id=decision_input.suggestion_id,
                        decision=decision_input.decision,
                        custom_correction=decision_input.custom_correction,
                        decision_reason=decision_input.reason,
                        tags=decision_input.tags
                    )
                    created_decisions.append(decision)

            await session.commit()
            self.logger.info(f"批量記錄 {len(created_decisions)} 個決策")
            return created_decisions

        except Exception as e:
            self.logger.error(f"批量記錄決策失敗: {e}")
            await session.rollback()
            raise DecisionServiceError(f"批量記錄失敗: {str(e)}")

    # ========================================================================
    # 決策查詢方法
    # ========================================================================

    async def get_article_decisions(
        self,
        session: AsyncSession,
        article_id: int,
        include_history: bool = False
    ) -> list[ProofreadingDecision]:
        """獲取文章的所有決策記錄

        Args:
            session: 數據庫會話
            article_id: 文章ID
            include_history: 是否包含校對歷史

        Returns:
            決策記錄列表
        """
        query = select(ProofreadingDecision).where(
            ProofreadingDecision.article_id == article_id
        ).order_by(ProofreadingDecision.created_at.desc())

        if include_history:
            query = query.options(selectinload(ProofreadingDecision.proofreading_history))

        result = await session.execute(query)
        return result.scalars().all()

    async def get_user_decision_history(
        self,
        session: AsyncSession,
        user_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
        time_range: DateRange | None = None
    ) -> list[ProofreadingDecision]:
        """獲取用戶的決策歷史

        Args:
            session: 數據庫會話
            user_id: 用戶ID（可選）
            limit: 返回數量限制
            offset: 偏移量
            time_range: 時間範圍

        Returns:
            決策記錄列表
        """
        query = select(ProofreadingDecision)

        # 添加時間範圍過濾
        if time_range:
            query = query.where(
                and_(
                    ProofreadingDecision.created_at >= time_range.start_date,
                    ProofreadingDecision.created_at <= time_range.end_date
                )
            )

        # TODO: 添加用戶ID過濾（需要關聯用戶表）

        query = query.order_by(
            ProofreadingDecision.created_at.desc()
        ).limit(limit).offset(offset)

        result = await session.execute(query)
        return result.scalars().all()

    # ========================================================================
    # 模式分析方法
    # ========================================================================

    async def analyze_decision_patterns(
        self,
        session: AsyncSession,
        time_range: DateRange | None = None,
        min_occurrences: int = 5
    ) -> DecisionPatterns:
        """分析決策模式

        Args:
            session: 數據庫會話
            time_range: 時間範圍
            min_occurrences: 最小出現次數

        Returns:
            決策模式分析結果
        """
        try:
            # 檢查緩存
            cache_key = self._get_cache_key("patterns", time_range)
            if cache_key in self._pattern_cache:
                return self._pattern_cache[cache_key]

            # 1. 收集決策數據
            decisions = await self._collect_decisions(session, time_range)

            if not decisions:
                return DecisionPatterns(
                    common_acceptances=[],
                    common_rejections=[],
                    custom_corrections=[],
                    time_patterns=[]
                )

            # 2. 按建議類型分組
            grouped = self._group_by_suggestion_type(decisions)

            # 3. 計算統計指標
            statistics = {}
            for suggestion_type, group_decisions in grouped.items():
                total = len(group_decisions)
                if total < min_occurrences:
                    continue

                accepted = sum(1 for d in group_decisions if d.decision == DecisionType.ACCEPT)
                rejected = sum(1 for d in group_decisions if d.decision == DecisionType.REJECT)
                modified = sum(1 for d in group_decisions if d.decision == DecisionType.MODIFY)

                statistics[suggestion_type] = {
                    'total': total,
                    'accepted': accepted,
                    'rejected': rejected,
                    'modified': modified,
                    'acceptance_rate': accepted / total,
                    'rejection_rate': rejected / total,
                    'modification_rate': modified / total,
                    'examples': [d.original_text for d in group_decisions[:5]]
                }

            # 4. 識別顯著模式
            patterns = self._identify_significant_patterns(
                statistics, min_occurrences=min_occurrences
            )

            # 5. 提取自定義修正模式
            custom_patterns = await self._extract_custom_patterns(
                [d for d in decisions if d.custom_correction]
            )

            # 6. 分析時間模式
            time_patterns = self._analyze_time_patterns(decisions)

            result = DecisionPatterns(
                common_acceptances=patterns['acceptances'],
                common_rejections=patterns['rejections'],
                custom_corrections=custom_patterns,
                time_patterns=time_patterns,
                confidence_scores=self._calculate_pattern_confidence(statistics)
            )

            # 緩存結果
            self._pattern_cache[cache_key] = result

            return result

        except Exception as e:
            self.logger.error(f"分析決策模式失敗: {e}")
            raise PatternAnalysisError(f"模式分析失敗: {str(e)}")

    async def extract_user_preferences(
        self,
        session: AsyncSession,
        user_id: int | None = None,
        min_decisions: int = 20
    ) -> UserPreferences:
        """提取用戶偏好

        Args:
            session: 數據庫會話
            user_id: 用戶ID
            min_decisions: 最小決策數

        Returns:
            用戶偏好分析結果
        """
        # 獲取用戶決策歷史
        decisions = await self.get_user_decision_history(
            session, user_id, limit=1000
        )

        if len(decisions) < min_decisions:
            self.logger.warning(f"決策數量不足: {len(decisions)} < {min_decisions}")
            return UserPreferences(confidence_level=0.0)

        preferences = UserPreferences()

        # 1. 分析寫作風格偏好
        style_prefs = self._analyze_style_preferences(decisions)
        preferences.style_preferences = style_prefs

        # 2. 提取詞彙使用偏好
        vocab_prefs = self._extract_vocabulary_preferences(decisions)
        preferences.vocabulary_preferences = vocab_prefs

        # 3. 識別語法規則偏好
        grammar_rules = self._identify_grammar_preferences(decisions)
        preferences.grammar_rules = grammar_rules

        # 4. 分析標點符號習慣
        punctuation = self._analyze_punctuation_habits(decisions)
        preferences.punctuation_habits = punctuation

        # 5. 計算置信度
        preferences.confidence_level = min(len(decisions) / 100, 1.0)

        return preferences

    # ========================================================================
    # 規則學習方法
    # ========================================================================

    async def generate_learning_rules(
        self,
        session: AsyncSession,
        patterns: DecisionPatterns,
        confidence_threshold: float = 0.8
    ) -> list[LearningRule]:
        """從模式生成學習規則

        Args:
            session: 數據庫會話
            patterns: 決策模式
            confidence_threshold: 置信度閾值

        Returns:
            學習規則列表
        """
        rules = []

        # 1. 生成替換規則
        for pattern in patterns.custom_corrections:
            if pattern.frequency >= self.min_pattern_threshold:
                rule = LearningRule(
                    rule_id=f"replace_{pattern.id}",
                    rule_type="replacement",
                    pattern=pattern.original_pattern,
                    replacement=pattern.correction_pattern,
                    confidence=pattern.confidence,
                    context_conditions=pattern.context,
                    example_applications=[
                        f"{pattern.original_pattern} → {pattern.correction_pattern}"
                    ]
                )
                rules.append(rule)

        # 2. 生成風格規則
        for acceptance in patterns.common_acceptances:
            if acceptance.rate >= confidence_threshold:
                rule = self._create_style_rule(acceptance)
                if rule:
                    rules.append(rule)

        # 3. 生成否定規則（不應該做的修改）
        for rejection in patterns.common_rejections:
            if rejection.rate >= confidence_threshold:
                rule = self._create_negative_rule(rejection)
                if rule:
                    rules.append(rule)

        # 4. 驗證規則一致性
        rules = self._validate_rule_consistency(rules)

        self.logger.info(f"生成 {len(rules)} 條學習規則")
        return rules

    async def apply_learning_rules(
        self,
        content: str,
        rules: list[LearningRule]
    ) -> tuple[str, list[RuleApplication]]:
        """應用學習規則到新內容

        Args:
            content: 原始內容
            rules: 學習規則列表

        Returns:
            (修改後內容, 應用記錄列表)
        """
        applications = []
        modified_content = content

        for rule in sorted(rules, key=lambda r: r.confidence, reverse=True):
            if rule.rule_type == "replacement" and rule.replacement:
                # 查找所有匹配
                import re
                matches = list(re.finditer(rule.pattern, modified_content))

                for match in reversed(matches):  # 從後向前替換避免位置錯亂
                    start, end = match.span()
                    original = modified_content[start:end]

                    # 應用替換
                    modified_content = (
                        modified_content[:start] +
                        rule.replacement +
                        modified_content[end:]
                    )

                    applications.append(RuleApplication(
                        rule_id=rule.rule_id,
                        original_text=original,
                        modified_text=rule.replacement,
                        position=(start, end),
                        confidence=rule.confidence
                    ))

        return modified_content, applications

    # ========================================================================
    # 反饋聚合方法
    # ========================================================================

    async def aggregate_feedback_data(
        self,
        session: AsyncSession,
        aggregation_period: str = "daily",
        date: datetime | None = None
    ) -> FeedbackAggregation:
        """聚合反饋數據

        Args:
            session: 數據庫會話
            aggregation_period: 聚合週期
            date: 指定日期

        Returns:
            反饋聚合結果
        """
        # 確定時間範圍
        if not date:
            date = datetime.utcnow()

        if aggregation_period == "daily":
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        elif aggregation_period == "weekly":
            start_date = date - timedelta(days=date.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=7)
        else:  # monthly
            start_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if date.month == 12:
                end_date = date.replace(year=date.year + 1, month=1, day=1)
            else:
                end_date = date.replace(month=date.month + 1, day=1)

        # 查詢統計數據
        query = select(
            func.count(ProofreadingDecision.id).label('total'),
            func.sum(case((ProofreadingDecision.decision == DecisionType.ACCEPT, 1), else_=0)).label('accepted'),
            func.sum(case((ProofreadingDecision.decision == DecisionType.REJECT, 1), else_=0)).label('rejected'),
            func.sum(case((ProofreadingDecision.decision == DecisionType.MODIFY, 1), else_=0)).label('modified'),
            ProofreadingDecision.suggestion_type,
            func.count(distinct(ProofreadingDecision.article_id)).label('unique_articles')
        ).where(
            and_(
                ProofreadingDecision.created_at >= start_date,
                ProofreadingDecision.created_at < end_date
            )
        ).group_by(ProofreadingDecision.suggestion_type)

        result = await session.execute(query)
        stats = result.all()

        # 聚合結果
        total = sum(row.total for row in stats)
        accepted = sum(row.accepted or 0 for row in stats)
        rejected = sum(row.rejected or 0 for row in stats)
        modified = sum(row.modified or 0 for row in stats)

        return FeedbackAggregation(
            total_decisions=total,
            acceptance_rate=accepted / total if total > 0 else 0,
            rejection_rate=rejected / total if total > 0 else 0,
            modification_rate=modified / total if total > 0 else 0,
            suggestion_type_distribution={
                row.suggestion_type: row.total for row in stats
            },
            user_activity={
                'unique_articles': sum(row.unique_articles for row in stats),
                'avg_decisions_per_article': total / sum(row.unique_articles for row in stats) if stats else 0
            },
            time_period=f"{aggregation_period}_{start_date.date()}"
        )

    async def prepare_tuning_dataset(
        self,
        session: AsyncSession,
        min_examples: int = 100,
        balance_dataset: bool = True
    ) -> TuningDataset:
        """準備模型微調數據集

        Args:
            session: 數據庫會話
            min_examples: 最小樣本數
            balance_dataset: 是否平衡數據集

        Returns:
            調優數據集
        """
        # 獲取決策數據
        decisions = await self._collect_decisions(session, limit=min_examples * 3)

        # 分類樣本
        positive_examples = []
        negative_examples = []
        custom_examples = []

        for decision in decisions:
            example = {
                'input': decision.original_text,
                'context_before': decision.context_before,
                'context_after': decision.context_after,
                'suggestion_type': decision.suggestion_type
            }

            if decision.decision == DecisionType.ACCEPT:
                example['output'] = decision.suggested_text
                positive_examples.append(example)
            elif decision.decision == DecisionType.REJECT:
                example['output'] = decision.original_text
                negative_examples.append(example)
            elif decision.decision == DecisionType.MODIFY and decision.custom_correction:
                example['output'] = decision.custom_correction
                custom_examples.append(example)

        # 平衡數據集
        if balance_dataset:
            min_size = min(len(positive_examples), len(negative_examples))
            positive_examples = positive_examples[:min_size]
            negative_examples = negative_examples[:min_size]

        return TuningDataset(
            positive_examples=positive_examples,
            negative_examples=negative_examples,
            custom_examples=custom_examples,
            metadata={
                'total_decisions': len(decisions),
                'creation_date': datetime.utcnow().isoformat(),
                'balance_applied': balance_dataset
            }
        )

    # ========================================================================
    # 質量評估方法
    # ========================================================================

    async def evaluate_suggestion_quality(
        self,
        session: AsyncSession,
        time_range: DateRange | None = None
    ) -> QualityMetrics:
        """評估校對建議質量

        Args:
            session: 數據庫會話
            time_range: 時間範圍

        Returns:
            質量指標
        """
        # 獲取決策數據
        decisions = await self._collect_decisions(session, time_range)

        if not decisions:
            return QualityMetrics(
                accuracy=0, relevance=0, usefulness=0,
                trend="stable", details={}
            )

        total = len(decisions)
        accepted = sum(1 for d in decisions if d.decision == DecisionType.ACCEPT)
        modified = sum(1 for d in decisions if d.decision == DecisionType.MODIFY)

        # 計算指標
        accuracy = accepted / total
        usefulness = (accepted + modified) / total

        # 計算相關性（基於置信度分數）
        relevance = sum(d.confidence_score or 0 for d in decisions) / total

        # 分析趨勢
        trend = await self._analyze_quality_trend(session, time_range)

        return QualityMetrics(
            accuracy=accuracy,
            relevance=relevance,
            usefulness=usefulness,
            trend=trend,
            details={
                'total_decisions': total,
                'accepted': accepted,
                'rejected': total - accepted - modified,
                'modified': modified,
                'avg_confidence': relevance
            }
        )

    async def identify_improvement_areas(
        self,
        session: AsyncSession,
        quality_metrics: QualityMetrics,
        target_accuracy: float = 0.85
    ) -> list[ImprovementArea]:
        """識別需要改進的領域

        Args:
            session: 數據庫會話
            quality_metrics: 質量指標
            target_accuracy: 目標準確率

        Returns:
            改進領域列表
        """
        areas = []

        # 1. 檢查準確率
        if quality_metrics.accuracy < target_accuracy:
            areas.append(ImprovementArea(
                area_name="建議準確率",
                current_performance=quality_metrics.accuracy,
                target_performance=target_accuracy,
                suggestions=[
                    "分析被拒絕的建議模式",
                    "調整建議生成算法",
                    "增加上下文考慮",
                    "收集更多訓練數據"
                ],
                priority="high"
            ))

        # 2. 檢查相關性
        if quality_metrics.relevance < 0.7:
            areas.append(ImprovementArea(
                area_name="建議相關性",
                current_performance=quality_metrics.relevance,
                target_performance=0.7,
                suggestions=[
                    "改進上下文理解",
                    "優化建議匹配算法",
                    "增加領域特定規則"
                ],
                priority="medium"
            ))

        # 3. 檢查有用性
        if quality_metrics.usefulness < 0.8:
            areas.append(ImprovementArea(
                area_name="建議有用性",
                current_performance=quality_metrics.usefulness,
                target_performance=0.8,
                suggestions=[
                    "分析修改模式",
                    "提供更多樣化的建議",
                    "考慮用戶偏好"
                ],
                priority="medium"
            ))

        return areas

    # ========================================================================
    # 私有輔助方法
    # ========================================================================

    async def _validate_decision_input(
        self,
        session: AsyncSession,
        article_id: int,
        proofreading_history_id: int,
        suggestion_id: str
    ) -> None:
        """驗證決策輸入"""
        # 檢查文章是否存在
        article = await session.get(Article, article_id)
        if not article:
            raise InvalidDecisionError(f"文章不存在: {article_id}")

        # 檢查校對歷史是否存在
        history = await session.get(ProofreadingHistory, proofreading_history_id)
        if not history or history.article_id != article_id:
            raise InvalidDecisionError(f"校對歷史不匹配: {proofreading_history_id}")

    async def _check_existing_decision(
        self,
        session: AsyncSession,
        article_id: int,
        suggestion_id: str
    ) -> ProofreadingDecision | None:
        """檢查是否已存在決策"""
        query = select(ProofreadingDecision).where(
            and_(
                ProofreadingDecision.article_id == article_id,
                ProofreadingDecision.suggestion_id == suggestion_id
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def _get_suggestion_detail(
        self,
        session: AsyncSession,
        proofreading_history_id: int,
        suggestion_id: str
    ) -> dict[str, Any]:
        """獲取建議詳情"""
        history = await session.get(ProofreadingHistory, proofreading_history_id)
        if not history or not history.suggestions:
            return {}

        for suggestion in history.suggestions:
            if suggestion.get("id") == suggestion_id:
                return suggestion

        return {}

    async def _calculate_confidence(
        self,
        session: AsyncSession,
        decision: DecisionType,
        suggestion_detail: dict[str, Any]
    ) -> float:
        """計算決策置信度"""
        base_confidence = 0.5

        # 基於決策類型調整
        if decision == DecisionType.ACCEPT:
            base_confidence += 0.2
        elif decision == DecisionType.REJECT:
            base_confidence -= 0.1

        # 基於建議置信度調整
        if "confidence" in suggestion_detail:
            base_confidence = (base_confidence + suggestion_detail["confidence"]) / 2

        return min(max(base_confidence, 0.0), 1.0)

    async def _should_trigger_learning(
        self,
        session: AsyncSession,
        article_id: int
    ) -> bool:
        """判斷是否應觸發學習"""
        # 統計該文章的決策數
        query = select(func.count(ProofreadingDecision.id)).where(
            ProofreadingDecision.article_id == article_id
        )
        result = await session.execute(query)
        count = result.scalar() or 0

        # 每10個決策觸發一次學習
        return count > 0 and count % 10 == 0

    async def _trigger_async_learning(
        self,
        session: AsyncSession,
        article_id: int
    ) -> None:
        """觸發異步學習任務"""
        # 創建調優任務記錄
        tuning_job = FeedbackTuningJob(
            job_type=TuningJobType.INCREMENTAL,
            status=TuningJobStatus.PENDING,
            config={
                "article_id": article_id,
                "triggered_at": datetime.utcnow().isoformat(),
                "auto_triggered": True
            }
        )
        session.add(tuning_job)
        await session.commit()

        self.logger.info(f"觸發異步學習任務: article={article_id}")

        # TODO: 實際觸發 Celery 任務或其他異步處理

    async def _collect_decisions(
        self,
        session: AsyncSession,
        time_range: DateRange | None = None,
        limit: int | None = None
    ) -> list[ProofreadingDecision]:
        """收集決策數據"""
        query = select(ProofreadingDecision)

        if time_range:
            query = query.where(
                and_(
                    ProofreadingDecision.created_at >= time_range.start_date,
                    ProofreadingDecision.created_at <= time_range.end_date
                )
            )

        if limit:
            query = query.limit(limit)

        query = query.order_by(ProofreadingDecision.created_at.desc())

        result = await session.execute(query)
        return result.scalars().all()

    def _group_by_suggestion_type(
        self,
        decisions: list[ProofreadingDecision]
    ) -> dict[str, list[ProofreadingDecision]]:
        """按建議類型分組"""
        grouped = defaultdict(list)
        for decision in decisions:
            grouped[decision.suggestion_type].append(decision)
        return dict(grouped)

    def _identify_significant_patterns(
        self,
        statistics: dict[str, dict],
        min_occurrences: int = 5
    ) -> dict[str, list[PatternDetail]]:
        """識別顯著模式"""
        acceptances = []
        rejections = []

        for suggestion_type, stats in statistics.items():
            if stats['total'] < min_occurrences:
                continue

            # 高接受率模式
            if stats['acceptance_rate'] > 0.8:
                acceptances.append(PatternDetail(
                    pattern_type=suggestion_type,
                    frequency=stats['total'],
                    rate=stats['acceptance_rate'],
                    examples=stats.get('examples', []),
                    confidence=self._calculate_confidence_score(stats)
                ))

            # 高拒絕率模式
            if stats['rejection_rate'] > 0.8:
                rejections.append(PatternDetail(
                    pattern_type=suggestion_type,
                    frequency=stats['total'],
                    rate=stats['rejection_rate'],
                    examples=stats.get('examples', []),
                    confidence=self._calculate_confidence_score(stats)
                ))

        return {
            'acceptances': sorted(acceptances, key=lambda x: x.rate, reverse=True),
            'rejections': sorted(rejections, key=lambda x: x.rate, reverse=True)
        }

    async def _extract_custom_patterns(
        self,
        decisions_with_custom: list[ProofreadingDecision]
    ) -> list[CorrectionPattern]:
        """提取自定義修正模式"""
        patterns = []
        pattern_counter = Counter()

        for decision in decisions_with_custom:
            if not decision.custom_correction:
                continue

            # 創建模式標識
            pattern_key = (
                decision.suggestion_type,
                decision.original_text[:50],  # 截取前50字符
                decision.custom_correction[:50]
            )
            pattern_counter[pattern_key] += 1

        # 提取頻繁模式
        for (suggestion_type, original, correction), count in pattern_counter.items():
            if count >= 3:  # 至少出現3次
                patterns.append(CorrectionPattern(
                    id=hashlib.md5(f"{original}_{correction}".encode()).hexdigest()[:8],
                    original_pattern=original,
                    correction_pattern=correction,
                    frequency=count,
                    confidence=min(count / 10, 1.0),  # 簡單的置信度計算
                    context={'suggestion_type': suggestion_type}
                ))

        return sorted(patterns, key=lambda x: x.frequency, reverse=True)

    def _analyze_time_patterns(
        self,
        decisions: list[ProofreadingDecision]
    ) -> list[TimePattern]:
        """分析時間模式"""
        if not decisions:
            return []

        # 按日期分組
        daily_groups = defaultdict(list)
        for decision in decisions:
            date_key = decision.created_at.date()
            daily_groups[date_key].append(decision)

        # 分析趨勢
        dates = sorted(daily_groups.keys())
        if len(dates) < 2:
            return []

        daily_counts = [len(daily_groups[date]) for date in dates]

        # 簡單的趨勢判斷
        trend = "stable"
        if len(daily_counts) >= 3:
            recent_avg = sum(daily_counts[-3:]) / 3
            earlier_avg = sum(daily_counts[:-3]) / max(len(daily_counts) - 3, 1)

            if recent_avg > earlier_avg * 1.2:
                trend = "increasing"
            elif recent_avg < earlier_avg * 0.8:
                trend = "decreasing"

        return [
            TimePattern(
                period="daily",
                trend=trend,
                metrics={
                    'avg_daily_decisions': sum(daily_counts) / len(daily_counts),
                    'max_daily_decisions': max(daily_counts),
                    'min_daily_decisions': min(daily_counts)
                }
            )
        ]

    def _calculate_pattern_confidence(
        self,
        statistics: dict[str, dict]
    ) -> dict[str, float]:
        """計算模式置信度"""
        confidence_scores = {}

        for suggestion_type, stats in statistics.items():
            # 基於樣本量和一致性計算置信度
            sample_factor = min(stats['total'] / 100, 1.0)

            # 計算決策一致性
            rates = [
                stats.get('acceptance_rate', 0),
                stats.get('rejection_rate', 0),
                stats.get('modification_rate', 0)
            ]
            max_rate = max(rates)

            consistency_factor = max_rate  # 最高比率作為一致性指標

            confidence_scores[suggestion_type] = (
                sample_factor * 0.3 + consistency_factor * 0.7
            )

        return confidence_scores

    def _calculate_confidence_score(self, stats: dict) -> float:
        """計算單個統計的置信度分數"""
        sample_size = stats.get('total', 0)

        # 基於樣本量的置信度
        if sample_size < 10:
            return 0.5
        elif sample_size < 50:
            return 0.7
        elif sample_size < 100:
            return 0.85
        else:
            return 0.95

    def _analyze_style_preferences(
        self,
        decisions: list[ProofreadingDecision]
    ) -> dict[str, Any]:
        """分析寫作風格偏好"""
        preferences = {
            'formal_level': 'neutral',  # formal, neutral, casual
            'sentence_length': 'medium',  # short, medium, long
            'complexity': 'moderate'  # simple, moderate, complex
        }

        # TODO: 實現詳細的風格分析邏輯

        return preferences

    def _extract_vocabulary_preferences(
        self,
        decisions: list[ProofreadingDecision]
    ) -> list[str]:
        """提取詞彙使用偏好"""
        preferred_words = []

        # 分析接受的詞彙修改
        for decision in decisions:
            if decision.decision == DecisionType.ACCEPT and decision.suggestion_type == "vocabulary":
                # 提取偏好的詞彙
                if decision.suggested_text:
                    preferred_words.append(decision.suggested_text)

        return list(set(preferred_words))[:50]  # 返回前50個

    def _identify_grammar_preferences(
        self,
        decisions: list[ProofreadingDecision]
    ) -> list[str]:
        """識別語法規則偏好"""
        grammar_rules = []

        # 分析語法相關的決策
        for decision in decisions:
            if decision.suggestion_type in ["grammar", "syntax"]:
                if decision.decision == DecisionType.ACCEPT:
                    # 記錄接受的語法規則
                    if decision.decision_reason:
                        grammar_rules.append(decision.decision_reason)

        return list(set(grammar_rules))[:20]  # 返回前20條

    def _analyze_punctuation_habits(
        self,
        decisions: list[ProofreadingDecision]
    ) -> dict[str, str]:
        """分析標點符號習慣"""
        habits = {}

        # 分析標點相關的決策
        for decision in decisions:
            if decision.suggestion_type == "punctuation":
                if decision.decision == DecisionType.ACCEPT:
                    # 記錄接受的標點使用
                    habits[decision.original_text] = decision.suggested_text

        return habits

    def _create_style_rule(self, pattern: PatternDetail) -> LearningRule | None:
        """創建風格規則"""
        if pattern.frequency < self.min_pattern_threshold:
            return None

        return LearningRule(
            rule_id=f"style_{pattern.pattern_type}_{hash(pattern.pattern_type) % 1000}",
            rule_type="style",
            pattern=pattern.pattern_type,
            confidence=pattern.confidence,
            context_conditions={
                'acceptance_rate': pattern.rate,
                'frequency': pattern.frequency
            },
            example_applications=pattern.examples[:3]
        )

    def _create_negative_rule(self, pattern: PatternDetail) -> LearningRule | None:
        """創建否定規則"""
        if pattern.frequency < self.min_pattern_threshold:
            return None

        return LearningRule(
            rule_id=f"negative_{pattern.pattern_type}_{hash(pattern.pattern_type) % 1000}",
            rule_type="negative",
            pattern=pattern.pattern_type,
            confidence=pattern.confidence,
            context_conditions={
                'rejection_rate': pattern.rate,
                'frequency': pattern.frequency,
                'action': 'do_not_suggest'
            },
            example_applications=pattern.examples[:3]
        )

    def _validate_rule_consistency(self, rules: list[LearningRule]) -> list[LearningRule]:
        """驗證規則一致性"""
        # 檢查衝突規則
        validated_rules = []
        rule_patterns = set()

        for rule in rules:
            if rule.pattern not in rule_patterns:
                validated_rules.append(rule)
                rule_patterns.add(rule.pattern)
            else:
                # 如果有衝突，選擇置信度更高的
                existing_rule = next(
                    r for r in validated_rules if r.pattern == rule.pattern
                )
                if rule.confidence > existing_rule.confidence:
                    validated_rules.remove(existing_rule)
                    validated_rules.append(rule)

        return validated_rules

    async def _analyze_quality_trend(
        self,
        session: AsyncSession,
        time_range: DateRange | None
    ) -> str:
        """分析質量趨勢"""
        # 獲取歷史數據進行比較
        if not time_range:
            return "stable"

        # 計算前期和後期的質量指標
        mid_point = time_range.start_date + (time_range.end_date - time_range.start_date) / 2

        earlier_range = DateRange(time_range.start_date, mid_point)
        later_range = DateRange(mid_point, time_range.end_date)

        earlier_metrics = await self.evaluate_suggestion_quality(session, earlier_range)
        later_metrics = await self.evaluate_suggestion_quality(session, later_range)

        # 比較準確率
        if later_metrics.accuracy > earlier_metrics.accuracy * 1.1:
            return "improving"
        elif later_metrics.accuracy < earlier_metrics.accuracy * 0.9:
            return "declining"
        else:
            return "stable"

    def _get_cache_key(self, prefix: str, time_range: DateRange | None) -> str:
        """生成緩存鍵"""
        if time_range:
            return f"{prefix}_{time_range.start_date.date()}_{time_range.end_date.date()}"
        return f"{prefix}_all"


# ============================================================================
# 服務單例
# ============================================================================

_decision_service = None


def get_decision_service() -> ProofreadingDecisionService:
    """獲取決策服務單例"""
    global _decision_service
    if _decision_service is None:
        _decision_service = ProofreadingDecisionService()
    return _decision_service
