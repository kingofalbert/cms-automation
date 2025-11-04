#!/usr/bin/env python3
"""測試校對決策服務

測試 T7.2 ProofreadingDecisionService 的完整功能。
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db_config
from src.config.logging import get_logger
from src.models.article import Article
from src.models.proofreading import DecisionType, ProofreadingDecision, ProofreadingHistory
from src.services.proofreading_decision import (
    DateRange,
    DecisionInput,
    DecisionPatterns,
    ProofreadingDecisionService,
    get_decision_service,
)

logger = get_logger(__name__)


async def create_test_data(session: AsyncSession) -> dict:
    """創建測試數據"""
    print("\n📝 創建測試數據...")

    # 1. 創建測試文章
    article = Article(
        title="T7.2 測試文章",
        body="這是一篇用於測試校對決策服務的文章。文章包含了各種需要校對的內容，例如錯別字、語法錯誤、標點符號問題等。這樣我們可以測試決策服務的各種功能。",
        status="draft"
    )
    session.add(article)
    await session.commit()
    print(f"  ✅ 創建文章: ID={article.id}, Title={article.title}")

    # 2. 創建校對歷史
    proofreading_history = ProofreadingHistory(
        article_id=article.id,
        original_content=article.body,
        corrected_content=article.body.replace("錯別字", "錯誤字"),
        suggestions=[
            {
                "id": "sug_001",
                "type": "spelling",
                "original": "錯別字",
                "suggested": "錯誤字",
                "confidence": 0.9,
                "context_before": "各種需要校對的內容，例如",
                "context_after": "、語法錯誤、標點符號問題"
            },
            {
                "id": "sug_002",
                "type": "grammar",
                "original": "這樣我們可以",
                "suggested": "這樣，我們可以",
                "confidence": 0.85,
                "context_before": "標點符號問題等。",
                "context_after": "測試決策服務的各種功能"
            },
            {
                "id": "sug_003",
                "type": "punctuation",
                "original": "功能。",
                "suggested": "功能！",
                "confidence": 0.7,
                "context_before": "測試決策服務的各種",
                "context_after": ""
            },
            {
                "id": "sug_004",
                "type": "style",
                "original": "文章包含了",
                "suggested": "文章含有",
                "confidence": 0.6,
                "context_before": "測試校對決策服務的文章。",
                "context_after": "各種需要校對的內容"
            },
            {
                "id": "sug_005",
                "type": "vocabulary",
                "original": "例如",
                "suggested": "比如",
                "confidence": 0.75,
                "context_before": "各種需要校對的內容，",
                "context_after": "錯別字、語法錯誤"
            }
        ],
        changes_made=1,
        ai_provider="test_provider",
        processing_time_ms=500,
        quality_score=0.85
    )
    session.add(proofreading_history)
    await session.commit()
    print(f"  ✅ 創建校對歷史: ID={proofreading_history.id}, 建議數={len(proofreading_history.suggestions)}")

    return {
        "article": article,
        "proofreading_history": proofreading_history
    }


async def test_decision_recording(
    service: ProofreadingDecisionService,
    session: AsyncSession,
    test_data: dict
) -> list[ProofreadingDecision]:
    """測試決策記錄功能"""
    print("\n🧪 測試 1: 決策記錄")
    print("-" * 40)

    article = test_data["article"]
    history = test_data["proofreading_history"]

    decisions_made = []

    # 1. 接受第一個建議（拼寫）
    print("\n1️⃣ 記錄接受決策...")
    decision1 = await service.record_decision(
        session=session,
        article_id=article.id,
        proofreading_history_id=history.id,
        suggestion_id="sug_001",
        decision=DecisionType.ACCEPT,
        decision_reason="拼寫錯誤確實需要修正",
        tags=["spelling", "accepted"]
    )
    decisions_made.append(decision1)
    print(f"  ✅ 決策記錄: {decision1.suggestion_id} -> {decision1.decision}")

    # 2. 拒絕第二個建議（語法）
    print("\n2️⃣ 記錄拒絕決策...")
    decision2 = await service.record_decision(
        session=session,
        article_id=article.id,
        proofreading_history_id=history.id,
        suggestion_id="sug_002",
        decision=DecisionType.REJECT,
        decision_reason="原文語法沒有問題",
        tags=["grammar", "rejected"]
    )
    decisions_made.append(decision2)
    print(f"  ✅ 決策記錄: {decision2.suggestion_id} -> {decision2.decision}")

    # 3. 修改第三個建議（標點）
    print("\n3️⃣ 記錄修改決策...")
    decision3 = await service.record_decision(
        session=session,
        article_id=article.id,
        proofreading_history_id=history.id,
        suggestion_id="sug_003",
        decision=DecisionType.MODIFY,
        custom_correction="功能。",  # 保持原樣
        decision_reason="保持句號，不需要感嘆號",
        tags=["punctuation", "modified"]
    )
    decisions_made.append(decision3)
    print(f"  ✅ 決策記錄: {decision3.suggestion_id} -> {decision3.decision} (自定義: {decision3.custom_correction})")

    # 4. 測試批量記錄
    print("\n4️⃣ 批量記錄決策...")
    batch_decisions = [
        DecisionInput(
            suggestion_id="sug_004",
            decision=DecisionType.ACCEPT,
            reason="風格改進合理",
            tags=["style"]
        ),
        DecisionInput(
            suggestion_id="sug_005",
            decision=DecisionType.REJECT,
            reason="保持原詞彙",
            tags=["vocabulary"]
        )
    ]

    batch_results = await service.record_batch_decisions(
        session=session,
        article_id=article.id,
        proofreading_history_id=history.id,
        decisions=batch_decisions
    )
    decisions_made.extend(batch_results)
    print(f"  ✅ 批量記錄 {len(batch_results)} 個決策")

    return decisions_made


async def test_decision_retrieval(
    service: ProofreadingDecisionService,
    session: AsyncSession,
    test_data: dict
):
    """測試決策查詢功能"""
    print("\n🧪 測試 2: 決策查詢")
    print("-" * 40)

    article = test_data["article"]

    # 1. 查詢文章的所有決策
    print("\n1️⃣ 查詢文章決策...")
    decisions = await service.get_article_decisions(
        session=session,
        article_id=article.id,
        include_history=True
    )

    print(f"  找到 {len(decisions)} 個決策:")
    for d in decisions:
        print(f"    - {d.suggestion_id}: {d.decision} ({d.suggestion_type})")

    # 2. 查詢決策歷史
    print("\n2️⃣ 查詢決策歷史...")
    history = await service.get_user_decision_history(
        session=session,
        limit=10,
        offset=0
    )

    print(f"  找到 {len(history)} 條歷史記錄")

    # 3. 查詢特定時間範圍的決策
    print("\n3️⃣ 查詢今日決策...")
    today = datetime.utcnow()
    time_range = DateRange(
        start_date=today.replace(hour=0, minute=0, second=0),
        end_date=today + timedelta(days=1)
    )

    today_decisions = await service.get_user_decision_history(
        session=session,
        time_range=time_range
    )

    print(f"  今日決策數: {len(today_decisions)}")


async def test_pattern_analysis(
    service: ProofreadingDecisionService,
    session: AsyncSession
):
    """測試模式分析功能"""
    print("\n🧪 測試 3: 模式分析")
    print("-" * 40)

    # 1. 分析決策模式
    print("\n1️⃣ 分析決策模式...")
    patterns = await service.analyze_decision_patterns(
        session=session,
        min_occurrences=1  # 測試環境降低閾值
    )

    print(f"  常接受的模式: {len(patterns.common_acceptances)}")
    for pattern in patterns.common_acceptances:
        print(f"    - {pattern.pattern_type}: {pattern.rate:.2%} (n={pattern.frequency})")

    print(f"  常拒絕的模式: {len(patterns.common_rejections)}")
    for pattern in patterns.common_rejections:
        print(f"    - {pattern.pattern_type}: {pattern.rate:.2%} (n={pattern.frequency})")

    print(f"  自定義修正: {len(patterns.custom_corrections)}")
    for pattern in patterns.custom_corrections:
        print(f"    - {pattern.original_pattern} → {pattern.correction_pattern}")

    # 2. 提取用戶偏好
    print("\n2️⃣ 提取用戶偏好...")
    preferences = await service.extract_user_preferences(
        session=session,
        min_decisions=1  # 測試環境降低閾值
    )

    print(f"  置信度: {preferences.confidence_level:.2%}")
    print(f"  風格偏好: {preferences.style_preferences}")
    print(f"  詞彙偏好: {len(preferences.vocabulary_preferences)} 個詞")

    return patterns


async def test_rule_generation(
    service: ProofreadingDecisionService,
    session: AsyncSession,
    patterns: DecisionPatterns
):
    """測試規則生成功能"""
    print("\n🧪 測試 4: 規則生成")
    print("-" * 40)

    # 1. 生成學習規則
    print("\n1️⃣ 生成學習規則...")
    rules = await service.generate_learning_rules(
        session=session,
        patterns=patterns,
        confidence_threshold=0.5  # 測試環境降低閾值
    )

    print(f"  生成 {len(rules)} 條規則:")
    for rule in rules:
        print(f"    - {rule.rule_id}: {rule.rule_type} (置信度: {rule.confidence:.2f})")
        if rule.pattern:
            print(f"      模式: {rule.pattern}")
        if rule.replacement:
            print(f"      替換: {rule.replacement}")

    # 2. 應用規則到新內容
    if rules:
        print("\n2️⃣ 應用規則到新內容...")
        test_content = "這是測試內容，包含錯別字和其他問題。"

        modified, applications = await service.apply_learning_rules(
            content=test_content,
            rules=rules
        )

        print(f"  原始: {test_content}")
        print(f"  修改: {modified}")
        print(f"  應用 {len(applications)} 條規則")

        for app in applications:
            print(f"    - {app.rule_id}: {app.original_text} → {app.modified_text}")

    return rules


async def test_feedback_aggregation(
    service: ProofreadingDecisionService,
    session: AsyncSession
):
    """測試反饋聚合功能"""
    print("\n🧪 測試 5: 反饋聚合")
    print("-" * 40)

    # 1. 日度聚合
    print("\n1️⃣ 日度反饋聚合...")
    daily_feedback = await service.aggregate_feedback_data(
        session=session,
        aggregation_period="daily"
    )

    print(f"  總決策數: {daily_feedback.total_decisions}")
    print(f"  接受率: {daily_feedback.acceptance_rate:.2%}")
    print(f"  拒絕率: {daily_feedback.rejection_rate:.2%}")
    print(f"  修改率: {daily_feedback.modification_rate:.2%}")
    print(f"  建議類型分布: {daily_feedback.suggestion_type_distribution}")

    # 2. 準備調優數據集
    print("\n2️⃣ 準備調優數據集...")
    dataset = await service.prepare_tuning_dataset(
        session=session,
        min_examples=5,  # 測試環境降低閾值
        balance_dataset=True
    )

    print(f"  正例: {len(dataset.positive_examples)}")
    print(f"  負例: {len(dataset.negative_examples)}")
    print(f"  自定義例: {len(dataset.custom_examples)}")
    print(f"  元數據: {dataset.metadata}")

    return daily_feedback


async def test_quality_evaluation(
    service: ProofreadingDecisionService,
    session: AsyncSession
):
    """測試質量評估功能"""
    print("\n🧪 測試 6: 質量評估")
    print("-" * 40)

    # 1. 評估建議質量
    print("\n1️⃣ 評估建議質量...")
    quality = await service.evaluate_suggestion_quality(
        session=session
    )

    print(f"  準確率: {quality.accuracy:.2%}")
    print(f"  相關性: {quality.relevance:.2%}")
    print(f"  有用性: {quality.usefulness:.2%}")
    print(f"  趨勢: {quality.trend}")
    print(f"  詳情: {quality.details}")

    # 2. 識別改進領域
    print("\n2️⃣ 識別改進領域...")
    improvements = await service.identify_improvement_areas(
        session=session,
        quality_metrics=quality,
        target_accuracy=0.85
    )

    print(f"  需改進領域: {len(improvements)}")
    for area in improvements:
        print(f"    - {area.area_name} ({area.priority})")
        print(f"      當前: {area.current_performance:.2%}")
        print(f"      目標: {area.target_performance:.2%}")
        print(f"      建議: {', '.join(area.suggestions[:2])}")

    return quality


async def create_more_test_decisions(
    service: ProofreadingDecisionService,
    session: AsyncSession
):
    """創建更多測試決策數據以便更好地測試模式分析"""
    print("\n📝 創建額外測試數據...")

    # 創建多篇文章和決策以形成模式
    for i in range(5):
        # 創建文章
        article = Article(
            title=f"測試文章 {i+2}",
            body=f"這是第 {i+2} 篇測試文章的內容。",
            status="draft"
        )
        session.add(article)
        await session.commit()

        # 創建校對歷史
        history = ProofreadingHistory(
            article_id=article.id,
            original_content=article.body,
            corrected_content=article.body,
            suggestions=[
                {
                    "id": f"art{i+2}_sug1",
                    "type": "spelling",
                    "original": "測試",
                    "suggested": "測驗",
                    "confidence": 0.9
                },
                {
                    "id": f"art{i+2}_sug2",
                    "type": "grammar",
                    "original": "內容",
                    "suggested": "內容。",
                    "confidence": 0.8
                }
            ],
            changes_made=0,
            ai_provider="test_provider",
            processing_time_ms=300,
            quality_score=0.8
        )
        session.add(history)
        await session.commit()

        # 創建決策（形成模式）
        # 總是接受拼寫建議
        await service.record_decision(
            session=session,
            article_id=article.id,
            proofreading_history_id=history.id,
            suggestion_id=f"art{i+2}_sug1",
            decision=DecisionType.ACCEPT,
            decision_reason="拼寫修正",
            tags=["spelling"]
        )

        # 總是拒絕語法建議
        await service.record_decision(
            session=session,
            article_id=article.id,
            proofreading_history_id=history.id,
            suggestion_id=f"art{i+2}_sug2",
            decision=DecisionType.REJECT,
            decision_reason="語法正確",
            tags=["grammar"]
        )

    print("  ✅ 創建了 5 篇額外文章和 10 個決策")


async def cleanup_test_data(session: AsyncSession):
    """清理測試數據"""
    print("\n🧹 清理測試數據...")

    # 刪除測試創建的數據
    await session.execute(text(
        "DELETE FROM proofreading_decisions WHERE article_id IN (SELECT id FROM articles WHERE title LIKE 'T7.2 測試文章%' OR title LIKE '測試文章%')"
    ))
    await session.execute(text(
        "DELETE FROM proofreading_history WHERE article_id IN (SELECT id FROM articles WHERE title LIKE 'T7.2 測試文章%' OR title LIKE '測試文章%')"
    ))
    await session.execute(text(
        "DELETE FROM articles WHERE title LIKE 'T7.2 測試文章%' OR title LIKE '測試文章%'"
    ))

    await session.commit()
    print("  ✅ 測試數據已清理")


async def main():
    """主測試函數"""
    print("=" * 60)
    print("🚀 T7.2 校對決策服務測試")
    print("=" * 60)

    # 獲取服務實例
    service = get_decision_service()
    db_config = get_db_config()

    try:
        async with db_config.session() as session:
            # 清理之前的測試數據
            await cleanup_test_data(session)

            # 創建測試數據
            test_data = await create_test_data(session)

            # 執行測試

            # 1. 測試決策記錄
            decisions = await test_decision_recording(service, session, test_data)

            # 2. 測試決策查詢
            await test_decision_retrieval(service, session, test_data)

            # 創建更多測試數據以形成模式
            await create_more_test_decisions(service, session)

            # 3. 測試模式分析
            patterns = await test_pattern_analysis(service, session)

            # 4. 測試規則生成
            rules = await test_rule_generation(service, session, patterns)

            # 5. 測試反饋聚合
            feedback = await test_feedback_aggregation(service, session)

            # 6. 測試質量評估
            quality = await test_quality_evaluation(service, session)

            print("\n" + "=" * 60)
            print("✅ 所有測試完成！")
            print("=" * 60)

            print("\n📊 測試總結:")
            print(f"  • 記錄決策: {len(decisions)} 個")
            print(f"  • 識別模式: {len(patterns.common_acceptances) + len(patterns.common_rejections)} 個")
            print(f"  • 生成規則: {len(rules) if 'rules' in locals() else 0} 條")
            print(f"  • 聚合數據: {feedback.total_decisions} 個決策")
            print(f"  • 質量評估: 準確率 {quality.accuracy:.2%}")

            # 清理測試數據
            await cleanup_test_data(session)

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
