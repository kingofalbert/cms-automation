#!/usr/bin/env python3
"""
Test script for independent title generation service

Tests the new Option 2 implementation - dedicated title generation API.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from src.services.title_generator import TitleGeneratorService, TitleGenerationResult


async def test_title_generation():
    """Test the title generation service independently"""

    print("=" * 60)
    print("Testing Independent Title Generation Service (Option 2)")
    print("=" * 60)

    # Get API key from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not set in environment")
        return

    # Initialize service
    service = TitleGeneratorService(api_key=api_key)

    # Test article content
    test_title = "人工智能在医疗领域的应用"
    test_content = """
    人工智能（AI）技术正在彻底改变医疗行业。从疾病诊断到药物开发，
    从个性化治疗到健康管理，AI的应用无处不在。本文将深入探讨AI在
    医疗领域的最新进展，包括机器学习在医学影像分析中的应用、深度
    学习在疾病预测中的作用，以及自然语言处理在电子病历管理中的价值。

    通过分析真实案例和最新研究成果，我们将展示AI如何帮助医生提高
    诊断准确率、缩短治疗时间、降低医疗成本。同时，我们也将讨论AI
    在医疗应用中面临的挑战，包括数据隐私、算法可解释性和监管合规等问题。
    """

    print(f"\n📝 Original Title: {test_title}")
    print(f"📄 Content Preview: {test_content[:100]}...")

    # Test 1: Claude generation
    print("\n🤖 Test 1: Claude AI Generation")
    print("-" * 40)

    try:
        result: TitleGenerationResult = await service.generate_titles(
            article_title=test_title,
            article_content=test_content
        )

        if result.success:
            print(f"✅ Success! Generated {len(result.suggested_titles)} titles:")
            for i, title in enumerate(result.suggested_titles, 1):
                prefix = title.get("prefix", "")
                main = title.get("main", "")
                suffix = title.get("suffix", "")
                score = title.get("score", 0)
                reason = title.get("reason", "")

                full_title = f"{prefix}{main}{suffix}" if prefix or suffix else main
                print(f"\n  {i}. {full_title}")
                print(f"     Score: {score:.2f}")
                print(f"     Reason: {reason}")
        else:
            print(f"⚠️  Generation failed: {result.error}")

    except Exception as e:
        print(f"❌ Error during Claude generation: {e}")

    # Test 2: Fallback generation (simulate failure)
    print("\n\n🛡️ Test 2: Fallback Generation (Simulated Failure)")
    print("-" * 40)

    # Force fallback by using invalid API key
    fallback_service = TitleGeneratorService(api_key="invalid-key")

    try:
        result: TitleGenerationResult = service._generate_fallback_titles(test_title)

        if result.success:
            print(f"✅ Fallback successful! Generated {len(result.suggested_titles)} titles:")
            for i, title in enumerate(result.suggested_titles, 1):
                prefix = title.get("prefix", "")
                main = title.get("main", "")
                suffix = title.get("suffix", "")
                score = title.get("score", 0)
                reason = title.get("reason", "")

                full_title = f"{prefix}{main}{suffix}" if prefix or suffix else main
                print(f"\n  {i}. {full_title}")
                print(f"     Score: {score:.2f}")
                print(f"     Reason: {reason}")

        if result.error:
            print(f"\n  ℹ️ Note: {result.error}")

    except Exception as e:
        print(f"❌ Error during fallback generation: {e}")

    print("\n" + "=" * 60)
    print("✅ Title Generation Service Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_title_generation())