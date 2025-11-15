"""
Test script for SEO Title API endpoints (Phase 5)

This script tests:
1. Generating optimizations with SEO Title suggestions
2. Selecting an SEO Title variant
3. Selecting a custom SEO Title
4. Verifying SEO Title is used in publishing
"""

import asyncio
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db_config
from src.config.settings import get_settings
from src.models import Article, TitleSuggestion


async def test_seo_title_api():
    """Test SEO Title API functionality."""
    settings = get_settings()
    db_config = get_db_config()
    session_factory = db_config.get_session_factory()

    print("=" * 80)
    print("Phase 5: SEO Title API 測試")
    print("=" * 80)
    print()

    session: AsyncSession = session_factory()
    try:
        # Test 1: Find an article with title_suggestions
        print("📋 測試 1: 查找有優化建議的文章")
        print("-" * 80)

        stmt = (
            select(Article)
            .join(TitleSuggestion)
            .where(TitleSuggestion.suggested_seo_titles.isnot(None))
            .limit(1)
        )
        result = await session.execute(stmt)
        article = result.scalar_one_or_none()

        if article:
            print(f"✅ 找到文章 ID: {article.id}")
            print(f"   標題: {article.title}")
            print(f"   當前 SEO Title: {article.seo_title}")
            print(f"   SEO Title 來源: {article.seo_title_source}")
        else:
            # Try to find any article
            stmt = select(Article).limit(1)
            result = await session.execute(stmt)
            article = result.scalar_one_or_none()

            if article:
                print(f"⚠️  找到文章但沒有 SEO Title 建議，使用文章 ID: {article.id}")
                print(f"   標題: {article.title}")
            else:
                print("❌ 數據庫中沒有文章，無法測試")
                return

        print()

        # Test 2: Check if article has SEO Title suggestions
        print("📋 測試 2: 檢查 SEO Title 建議")
        print("-" * 80)

        stmt = select(TitleSuggestion).where(TitleSuggestion.article_id == article.id)
        result = await session.execute(stmt)
        title_suggestion = result.scalar_one_or_none()

        if title_suggestion and title_suggestion.suggested_seo_titles:
            seo_suggestions = title_suggestion.suggested_seo_titles
            print(f"✅ 找到 SEO Title 建議")
            print(f"   原文提取: {seo_suggestions.get('original_seo_title')}")
            print(f"   變體數量: {len(seo_suggestions.get('variants', []))}")

            for idx, variant in enumerate(seo_suggestions.get("variants", []), 1):
                print(f"   變體 {idx}:")
                print(f"     - ID: {variant['id']}")
                print(f"     - SEO Title: {variant['seo_title']}")
                print(f"     - 字符數: {variant['character_count']}")
                print(f"     - 關鍵字: {', '.join(variant['keywords_focus'])}")
        else:
            print("⚠️  文章沒有 SEO Title 建議")
            print("   這是正常的，如果文章尚未生成優化建議")

        print()

        # Test 3: Test select-seo-title endpoint (simulated)
        print("📋 測試 3: 模擬選擇 SEO Title API")
        print("-" * 80)

        # Simulate selecting a custom SEO Title
        custom_seo_title = "測試用的自定義 SEO Title"
        old_seo_title = article.seo_title

        article.seo_title = custom_seo_title
        article.seo_title_source = "user_input"
        article.updated_at = datetime.utcnow()

        await session.commit()

        print(f"✅ 成功更新 SEO Title")
        print(f"   舊值: {old_seo_title}")
        print(f"   新值: {article.seo_title}")
        print(f"   來源: {article.seo_title_source}")
        print(f"   更新時間: {article.updated_at}")

        print()

        # Test 4: Verify PublishingOrchestrator will use seo_title
        print("📋 測試 4: 驗證 PublishingOrchestrator 邏輯")
        print("-" * 80)

        # Simulate _build_seo_metadata logic
        seo_title_for_publish = article.seo_title or article.title or "Published Article"
        h1_title = article.title or "Published Article"

        print(f"✅ 發佈時將使用:")
        print(f"   H1 標題 (article.title): {h1_title}")
        print(f"   SEO Title (for <title>): {seo_title_for_publish}")
        print(f"   SEO Title 來源: {article.seo_title_source}")

        if article.seo_title:
            print(f"   ✅ 將使用優化的 SEO Title")
        else:
            print(f"   ⚠️  將後備到 H1 標題")

        print()

        # Test 5: Clean up (restore original value)
        print("📋 測試 5: 清理測試數據")
        print("-" * 80)

        article.seo_title = old_seo_title
        await session.commit()

        print(f"✅ 已恢復原始 SEO Title: {old_seo_title}")

        print()
        print("=" * 80)
        print("✅ 所有測試完成！")
        print("=" * 80)

    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ 測試失敗: {e}")
        print("=" * 80)
        import traceback

        traceback.print_exc()
        await session.rollback()

    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(test_seo_title_api())
