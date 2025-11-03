"""語義相似度檢測服務

使用 OpenAI embeddings 和 pgvector 實現文章的語義相似度檢測。
"""

import hashlib
import numpy as np
from typing import List, Optional, Tuple, Dict
from functools import lru_cache

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, and_
from sqlalchemy.orm import selectinload

from src.config.settings import get_settings
from src.models.article import Article
from src.models.topic_embedding import TopicEmbedding
from src.config.logging import get_logger

logger = get_logger(__name__)


class SemanticSimilarityService:
    """語義相似度檢測服務

    主要功能：
    1. 生成文本的向量嵌入
    2. 存儲和管理文章嵌入
    3. 查找相似文章
    4. 檢測重複內容
    5. 主題聚類
    """

    def __init__(self):
        """初始化服務"""
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.ANTHROPIC_API_KEY)
        self.embedding_model = "text-embedding-3-small"  # 1536 維度
        self.similarity_threshold = float(settings.SIMILARITY_THRESHOLD)  # 默認 0.85
        self._embedding_cache: Dict[str, List[float]] = {}

    def _get_text_hash(self, text: str) -> str:
        """生成文本的哈希值用於緩存"""
        return hashlib.md5(text.encode()).hexdigest()

    async def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """生成文本的向量嵌入

        Args:
            text: 要生成嵌入的文本
            use_cache: 是否使用緩存

        Returns:
            向量嵌入（1536 維度）
        """
        # 檢查緩存
        if use_cache:
            text_hash = self._get_text_hash(text)
            if text_hash in self._embedding_cache:
                logger.debug(f"使用緩存的嵌入: {text_hash[:8]}")
                return self._embedding_cache[text_hash]

        try:
            # 調用 OpenAI API
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            embedding = response.data[0].embedding

            # 存入緩存
            if use_cache:
                self._embedding_cache[text_hash] = embedding
                # 限制緩存大小
                if len(self._embedding_cache) > 1000:
                    # 移除最早的條目
                    first_key = next(iter(self._embedding_cache))
                    del self._embedding_cache[first_key]

            logger.info(f"成功生成嵌入，維度: {len(embedding)}")
            return embedding

        except Exception as e:
            logger.error(f"生成嵌入失敗: {e}")
            raise

    async def batch_generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """批量生成嵌入（優化 API 調用）

        Args:
            texts: 文本列表
            batch_size: 批次大小

        Returns:
            嵌入列表
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = await self.client.embeddings.create(
                    model=self.embedding_model,
                    input=batch
                )
                embeddings.extend([d.embedding for d in response.data])
                logger.info(f"批量生成嵌入: {i+1}-{min(i+batch_size, len(texts))}/{len(texts)}")

            except Exception as e:
                logger.error(f"批量生成嵌入失敗: {e}")
                # 降級為單個處理
                for text in batch:
                    try:
                        embedding = await self.generate_embedding(text)
                        embeddings.append(embedding)
                    except:
                        embeddings.append(None)

        return embeddings

    async def store_article_embedding(
        self,
        session: AsyncSession,
        article_id: int,
        topic_text: Optional[str] = None
    ) -> TopicEmbedding:
        """存儲文章的向量嵌入

        Args:
            session: 數據庫會話
            article_id: 文章 ID
            topic_text: 用於生成嵌入的文本（如果為空，自動從文章提取）

        Returns:
            TopicEmbedding 對象
        """
        # 獲取文章
        article = await session.get(Article, article_id)
        if not article:
            raise ValueError(f"文章不存在: {article_id}")

        # 準備嵌入文本
        if not topic_text:
            # 使用標題和內容前 1000 字符
            topic_text = f"{article.title}\n\n{article.body[:1000] if article.body else ''}"

        # 生成嵌入
        embedding = await self.generate_embedding(topic_text)

        # 檢查是否已存在
        existing = await session.execute(
            select(TopicEmbedding).where(TopicEmbedding.article_id == article_id)
        )
        topic_embedding = existing.scalar_one_or_none()

        if topic_embedding:
            # 更新現有嵌入
            topic_embedding.topic_text = topic_text
            topic_embedding.embedding = embedding
            logger.info(f"更新文章嵌入: {article_id}")
        else:
            # 創建新嵌入
            topic_embedding = TopicEmbedding(
                article_id=article_id,
                topic_text=topic_text,
                embedding=embedding
            )
            session.add(topic_embedding)
            logger.info(f"創建文章嵌入: {article_id}")

        await session.commit()
        return topic_embedding

    async def find_similar_articles(
        self,
        session: AsyncSession,
        query_text: str,
        limit: int = 10,
        threshold: Optional[float] = None,
        exclude_ids: Optional[List[int]] = None
    ) -> List[Tuple[Article, float]]:
        """查找相似文章

        Args:
            session: 數據庫會話
            query_text: 查詢文本
            limit: 返回數量限制
            threshold: 相似度閾值（0-1）
            exclude_ids: 要排除的文章 ID

        Returns:
            (文章, 相似度) 元組列表
        """
        # 生成查詢向量
        query_embedding = await self.generate_embedding(query_text)
        threshold = threshold or self.similarity_threshold
        exclude_ids = exclude_ids or []

        # 構建排除條件
        exclude_condition = ""
        if exclude_ids:
            exclude_ids_str = ",".join(map(str, exclude_ids))
            exclude_condition = f"AND a.id NOT IN ({exclude_ids_str})"

        # 使用 pgvector 進行相似度搜索
        # 注意：<=> 操作符返回餘弦距離（0-2），相似度 = 1 - (distance / 2)
        query = text(f"""
            SELECT
                a.id,
                a.title,
                a.body,
                a.status,
                a.word_count,
                a.quality_score,
                a.created_at,
                a.updated_at,
                te.topic_text,
                1 - (te.embedding <=> :query_embedding::vector) as similarity
            FROM topic_embeddings te
            JOIN articles a ON te.article_id = a.id
            WHERE 1 - (te.embedding <=> :query_embedding::vector) > :threshold
            {exclude_condition}
            ORDER BY te.embedding <=> :query_embedding::vector
            LIMIT :limit
        """)

        result = await session.execute(
            query,
            {
                "query_embedding": query_embedding,
                "threshold": threshold,
                "limit": limit
            }
        )

        similar_articles = []
        for row in result:
            article = Article(
                id=row.id,
                title=row.title,
                body=row.body,
                status=row.status,
                word_count=row.word_count,
                quality_score=row.quality_score,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            similarity = row.similarity
            similar_articles.append((article, similarity))

        logger.info(f"找到 {len(similar_articles)} 篇相似文章（閾值: {threshold}）")
        return similar_articles

    async def check_duplicate_content(
        self,
        session: AsyncSession,
        content: str,
        threshold: float = 0.95
    ) -> Optional[Article]:
        """檢查是否有重複內容

        Args:
            session: 數據庫會話
            content: 要檢查的內容
            threshold: 重複判定閾值（默認 0.95）

        Returns:
            如果找到重複，返回文章；否則返回 None
        """
        similar = await self.find_similar_articles(
            session,
            content,
            limit=1,
            threshold=threshold
        )

        if similar:
            article, similarity = similar[0]
            logger.warning(f"發現重複內容: {article.title} (相似度: {similarity:.2%})")
            return article

        return None

    async def find_articles_by_vector(
        self,
        session: AsyncSession,
        embedding_vector: List[float],
        limit: int = 10,
        threshold: float = 0.85
    ) -> List[Tuple[int, float]]:
        """直接使用向量查找相似文章

        Args:
            session: 數據庫會話
            embedding_vector: 查詢向量
            limit: 返回數量
            threshold: 相似度閾值

        Returns:
            (文章ID, 相似度) 列表
        """
        query = text("""
            SELECT
                article_id,
                1 - (embedding <=> :query_vector::vector) as similarity
            FROM topic_embeddings
            WHERE 1 - (embedding <=> :query_vector::vector) > :threshold
            ORDER BY embedding <=> :query_vector::vector
            LIMIT :limit
        """)

        result = await session.execute(
            query,
            {
                "query_vector": embedding_vector,
                "threshold": threshold,
                "limit": limit
            }
        )

        return [(row.article_id, row.similarity) for row in result]

    async def reindex_all_articles(
        self,
        session: AsyncSession,
        batch_size: int = 50
    ) -> int:
        """重新索引所有文章的嵌入

        Args:
            session: 數據庫會話
            batch_size: 批處理大小

        Returns:
            處理的文章數量
        """
        # 獲取所有文章
        result = await session.execute(
            select(Article).where(
                and_(
                    Article.body.isnot(None),
                    Article.body != ""
                )
            )
        )
        articles = result.scalars().all()

        if not articles:
            logger.info("沒有文章需要索引")
            return 0

        logger.info(f"開始重新索引 {len(articles)} 篇文章")

        # 批量處理
        processed = 0
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]

            # 準備文本
            texts = [
                f"{article.title}\n\n{article.body[:1000]}"
                for article in batch
            ]

            # 批量生成嵌入
            embeddings = await self.batch_generate_embeddings(texts)

            # 存儲嵌入
            for article, text, embedding in zip(batch, texts, embeddings):
                if embedding:  # 跳過失敗的嵌入
                    try:
                        await self.store_article_embedding(
                            session,
                            article.id,
                            text
                        )
                        processed += 1
                    except Exception as e:
                        logger.error(f"存儲嵌入失敗 (文章 {article.id}): {e}")

            logger.info(f"進度: {min(i + batch_size, len(articles))}/{len(articles)}")

        logger.info(f"重新索引完成，處理了 {processed} 篇文章")
        return processed

    async def get_article_clusters(
        self,
        session: AsyncSession,
        min_cluster_size: int = 2,
        similarity_threshold: float = 0.80
    ) -> Dict[int, List[int]]:
        """對文章進行主題聚類

        Args:
            session: 數據庫會話
            min_cluster_size: 最小聚類大小
            similarity_threshold: 相似度閾值

        Returns:
            聚類字典 {cluster_id: [article_ids]}
        """
        # 獲取所有嵌入
        result = await session.execute(
            select(TopicEmbedding)
        )
        embeddings = result.scalars().all()

        if len(embeddings) < min_cluster_size:
            return {}

        # 轉換為 numpy 數組
        vectors = np.array([e.embedding for e in embeddings])
        article_ids = [e.article_id for e in embeddings]

        # 使用 DBSCAN 聚類
        try:
            from sklearn.cluster import DBSCAN

            # 餘弦距離 = 1 - 餘弦相似度
            clustering = DBSCAN(
                eps=1 - similarity_threshold,
                min_samples=min_cluster_size,
                metric='cosine'
            )
            labels = clustering.fit_predict(vectors)

            # 組織聚類結果
            clusters = {}
            for article_id, label in zip(article_ids, labels):
                if label >= 0:  # -1 表示噪聲點
                    if label not in clusters:
                        clusters[label] = []
                    clusters[label].append(article_id)

            logger.info(f"聚類完成: {len(clusters)} 個聚類")
            return clusters

        except ImportError:
            logger.error("需要安裝 scikit-learn 來使用聚類功能")
            return {}

    async def clear_cache(self):
        """清除嵌入緩存"""
        self._embedding_cache.clear()
        logger.info("嵌入緩存已清除")


# 全局服務實例
_semantic_service = None


def get_semantic_service() -> SemanticSimilarityService:
    """獲取語義相似度服務的單例實例"""
    global _semantic_service
    if _semantic_service is None:
        _semantic_service = SemanticSimilarityService()
    return _semantic_service