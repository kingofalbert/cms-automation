#!/usr/bin/env python3
"""
測試語義相似度檢測功能

演示如何使用語義相似度服務進行：
1. 生成和存儲向量嵌入
2. 查找相似文章
3. 檢測重複內容
4. 執行相似度搜索
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select  # noqa: E402

from src.config.database import get_db_config  # noqa: E402
from src.models.article import Article  # noqa: E402
from src.services.semantic_similarity import get_semantic_service  # noqa: E402


async def test_basic_embedding():
    """測試基本的嵌入生成功能"""
    print("\n" + "="*60)
    print("📝 測試 1: 生成文本嵌入")
    print("="*60)

    service = get_semantic_service()

    # 測試文本
    test_texts = [
        "人工智能正在改變世界，機器學習技術不斷進步",
        "AI and machine learning are transforming the world",
        "今天天氣很好，適合出去散步",
        "深度學習是機器學習的一個分支，使用神經網絡"
    ]

    embeddings = []
    for text in test_texts:
        print(f"\n生成嵌入: {text[:50]}...")
        try:
            embedding = await service.generate_embedding(text)
            embeddings.append(embedding)
            print(f"✅ 成功！維度: {len(embedding)}")
        except Exception as e:
            print(f"❌ 失敗: {e}")
            embeddings.append(None)

    # 計算相似度
    if all(embeddings):
        print("\n📊 文本相似度矩陣:")
        print("-" * 40)

        from sklearn.metrics.pairwise import cosine_similarity

        similarity_matrix = cosine_similarity(embeddings)

        for i, text1 in enumerate(test_texts):
            print(f"\n文本 {i+1}: {text1[:30]}...")
            for j, _text2 in enumerate(test_texts):
                if i != j:
                    similarity = similarity_matrix[i][j]
                    print(f"  與文本 {j+1} 相似度: {similarity:.2%}")

    return embeddings[0] if embeddings else None


async def test_article_operations():
    """測試文章相關操作"""
    print("\n" + "="*60)
    print("📚 測試 2: 文章嵌入存儲和搜索")
    print("="*60)

    db_config = get_db_config()
    service = get_semantic_service()

    async with db_config.session() as session:
        # 1. 創建測試文章
        print("\n1️⃣ 創建測試文章...")

        test_articles = [
            {
                "title": "深度學習在計算機視覺中的應用",
                "body": "深度學習技術，特別是卷積神經網絡（CNN），已經徹底改變了計算機視覺領域。從圖像分類到目標檢測，從語義分割到人臉識別，深度學習模型在各種視覺任務中都取得了突破性進展。本文將探討深度學習在計算機視覺中的主要應用，包括醫療影像分析、自動駕駛、安防監控等領域的實際案例。"
            },
            {
                "title": "自然語言處理的最新進展",
                "body": "近年來，自然語言處理（NLP）領域經歷了革命性的變化。Transformer 架構的出現，以及 BERT、GPT 等預訓練模型的成功，使得機器理解和生成人類語言的能力大幅提升。本文將介紹 NLP 的最新技術進展，包括大語言模型、零樣本學習、多語言理解等方面的突破。"
            },
            {
                "title": "量子計算的未來展望",
                "body": "量子計算作為下一代計算技術，有望在某些特定問題上實現指數級的加速。與傳統計算機使用比特不同，量子計算機使用量子比特（qubit），可以同時處於多個狀態的疊加。本文探討量子計算的基本原理、當前挑戰以及在密碼學、藥物研發、金融建模等領域的潛在應用。"
            },
            {
                "title": "計算機視覺與深度學習的融合",
                "body": "計算機視覺和深度學習的結合創造了許多令人驚嘆的應用。深度卷積神經網絡能夠自動學習圖像特徵，無需人工設計。這種方法在圖像識別、物體檢測、圖像生成等任務上都取得了超越人類的性能。本文深入探討這種融合帶來的技術革新。"
            }
        ]

        created_articles = []
        for article_data in test_articles:
            # 檢查是否已存在
            existing = await session.execute(
                select(Article).where(Article.title == article_data["title"])
            )
            article = existing.scalar_one_or_none()

            if not article:
                article = Article(**article_data, status="published")
                session.add(article)
                await session.commit()
                print(f"✅ 創建文章: {article.title}")
            else:
                print(f"ℹ️  文章已存在: {article.title}")

            created_articles.append(article)

        # 2. 生成並存儲嵌入
        print("\n2️⃣ 生成並存儲文章嵌入...")

        for article in created_articles:
            try:
                await service.store_article_embedding(session, article.id)
                print(f"✅ 存儲嵌入: 文章 {article.id} - {article.title[:30]}...")
            except Exception as e:
                print(f"❌ 失敗: {e}")

        # 3. 查找相似文章
        print("\n3️⃣ 查找相似文章...")

        query = "深度學習和計算機視覺的最新應用"
        print(f"\n查詢: {query}")

        similar = await service.find_similar_articles(
            session,
            query,
            limit=5,
            threshold=0.7
        )

        if similar:
            print(f"\n找到 {len(similar)} 篇相似文章:")
            for i, (article, similarity) in enumerate(similar, 1):
                print(f"{i}. {article.title}")
                print(f"   相似度: {similarity:.2%}")
                print(f"   摘要: {article.body[:100]}...")
                print()
        else:
            print("未找到相似文章")

        # 4. 檢測重複內容
        print("\n4️⃣ 檢測重複內容...")

        # 測試幾乎相同的內容
        duplicate_text = "深度學習技術，尤其是卷積神經網絡（CNN），已經徹底改變了計算機視覺領域。從圖像分類到目標檢測，深度學習在各種視覺任務中都取得了突破。"

        print(f"\n檢查文本: {duplicate_text[:50]}...")

        duplicate = await service.check_duplicate_content(
            session,
            duplicate_text,
            threshold=0.90
        )

        if duplicate:
            print("⚠️  發現重複內容!")
            print(f"   文章: {duplicate.title}")
            print(f"   ID: {duplicate.id}")
        else:
            print("✅ 未發現重複內容")

        return created_articles


async def test_batch_operations():
    """測試批量操作"""
    print("\n" + "="*60)
    print("⚡ 測試 3: 批量嵌入生成")
    print("="*60)

    service = get_semantic_service()

    # 準備批量文本
    batch_texts = [
        f"這是第 {i} 篇關於 {topic} 的文章內容"
        for i in range(1, 11)
        for topic in ["AI", "機器學習", "數據科學"]
    ]

    print(f"\n生成 {len(batch_texts)} 個文本的嵌入...")

    start_time = datetime.now()
    embeddings = await service.batch_generate_embeddings(batch_texts, batch_size=10)
    end_time = datetime.now()

    success_count = sum(1 for e in embeddings if e is not None)

    print(f"✅ 完成！成功: {success_count}/{len(batch_texts)}")
    print(f"⏱️  耗時: {(end_time - start_time).total_seconds():.2f} 秒")


async def test_similarity_search():
    """測試相似度搜索的高級功能"""
    print("\n" + "="*60)
    print("🔍 測試 4: 高級相似度搜索")
    print("="*60)

    db_config = get_db_config()
    service = get_semantic_service()

    async with db_config.session() as session:
        # 1. 測試排除特定文章
        print("\n1️⃣ 搜索時排除特定文章...")

        # 獲取一篇文章作為查詢
        result = await session.execute(
            select(Article).limit(1)
        )
        sample_article = result.scalar_one_or_none()

        if sample_article:
            query_text = f"{sample_article.title} {sample_article.body[:200]}"

            # 搜索但排除自己
            similar = await service.find_similar_articles(
                session,
                query_text,
                limit=3,
                threshold=0.5,
                exclude_ids=[sample_article.id]
            )

            print(f"查詢文章: {sample_article.title}")
            print(f"排除 ID: {sample_article.id}")

            if similar:
                print(f"\n找到 {len(similar)} 篇相似文章（排除自己）:")
                for article, similarity in similar:
                    print(f"  - {article.title[:50]}... (相似度: {similarity:.2%})")
            else:
                print("未找到其他相似文章")

        # 2. 測試不同的相似度閾值
        print("\n2️⃣ 測試不同相似度閾值...")

        query = "人工智能和機器學習"
        thresholds = [0.9, 0.8, 0.7, 0.6, 0.5]

        for threshold in thresholds:
            similar = await service.find_similar_articles(
                session,
                query,
                limit=100,
                threshold=threshold
            )
            print(f"  閾值 {threshold}: 找到 {len(similar)} 篇文章")


async def test_performance():
    """測試性能"""
    print("\n" + "="*60)
    print("⚡ 測試 5: 性能測試")
    print("="*60)

    service = get_semantic_service()

    # 1. 測試緩存效果
    print("\n1️⃣ 測試緩存效果...")

    test_text = "這是一段用於測試緩存的文本內容"

    # 第一次生成（無緩存）
    start = datetime.now()
    embedding1 = await service.generate_embedding(test_text)
    time1 = (datetime.now() - start).total_seconds()

    # 第二次生成（有緩存）
    start = datetime.now()
    embedding2 = await service.generate_embedding(test_text)
    time2 = (datetime.now() - start).total_seconds()

    print(f"第一次生成: {time1:.3f} 秒")
    print(f"第二次生成: {time2:.3f} 秒（緩存）")
    print(f"加速比: {time1/time2:.1f}x" if time2 > 0 else "無限大")

    # 驗證結果一致
    import numpy as np
    if np.array_equal(embedding1, embedding2):
        print("✅ 緩存結果一致")
    else:
        print("❌ 緩存結果不一致")

    # 2. 清除緩存
    print("\n2️⃣ 清除緩存...")
    await service.clear_cache()
    print("✅ 緩存已清除")


async def main():
    """主測試函數"""
    print("="*60)
    print("🧪 語義相似度檢測功能測試")
    print("="*60)

    try:
        # 運行各項測試
        embedding = await test_basic_embedding()

        if embedding:
            await test_article_operations()
            await test_batch_operations()
            await test_similarity_search()
            await test_performance()
        else:
            print("\n⚠️  嵌入生成失敗，跳過後續測試")
            print("請檢查 OpenAI API 密鑰配置")

        print("\n" + "="*60)
        print("✅ 所有測試完成！")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 運行測試
    asyncio.run(main())
