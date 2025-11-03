# 語義相似度檢測功能實施方案

## 1. 功能概述

語義相似度檢測功能用於：
- 防止重複內容生成
- 查找相似主題文章
- 內容推薦系統
- 主題聚類分析

## 2. 數據庫實現

### 2.1 表結構

```sql
-- topic_embeddings 表（已創建）
CREATE TABLE topic_embeddings (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    topic_text TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI embeddings 維度
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(article_id)
);

-- 向量索引（使用 pgvector）
CREATE INDEX idx_topic_embeddings_vector_hnsw
ON topic_embeddings USING hnsw (embedding vector_cosine_ops);
```

### 2.2 pgvector 擴展功能

```sql
-- 支持的操作符
<-> : 歐幾里得距離
<#> : 負內積
<=> : 餘弦距離（最常用於語義相似度）

-- 支持的索引類型
1. IVFFlat: 適合中等規模數據（< 100萬向量）
2. HNSW: 適合大規模數據，查詢速度更快
```

## 3. 功能實現方案

### 3.1 生成向量嵌入

```python
# src/services/semantic_similarity.py

import numpy as np
from typing import List, Optional, Tuple
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pgvector.sqlalchemy import Vector

from src.config.settings import get_settings
from src.models.article import Article
from src.models.topic_embedding import TopicEmbedding
from src.config.logging import get_logger

logger = get_logger(__name__)

class SemanticSimilarityService:
    """語義相似度檢測服務"""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.ANTHROPIC_API_KEY)
        self.embedding_model = "text-embedding-3-small"  # 1536 維度
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD  # 0.85

    async def generate_embedding(self, text: str) -> List[float]:
        """生成文本的向量嵌入"""
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"生成嵌入失敗: {e}")
            raise

    async def store_article_embedding(
        self,
        session: AsyncSession,
        article_id: int,
        topic_text: str
    ) -> TopicEmbedding:
        """存儲文章的向量嵌入"""

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
        else:
            # 創建新嵌入
            topic_embedding = TopicEmbedding(
                article_id=article_id,
                topic_text=topic_text,
                embedding=embedding
            )
            session.add(topic_embedding)

        await session.commit()
        return topic_embedding
```

### 3.2 相似度搜索

```python
    async def find_similar_articles(
        self,
        session: AsyncSession,
        query_text: str,
        limit: int = 10,
        threshold: Optional[float] = None
    ) -> List[Tuple[Article, float]]:
        """查找相似文章"""

        # 生成查詢向量
        query_embedding = await self.generate_embedding(query_text)
        threshold = threshold or self.similarity_threshold

        # 使用 pgvector 進行相似度搜索
        query = text("""
            SELECT
                a.id,
                a.title,
                a.body,
                a.status,
                a.created_at,
                te.topic_text,
                1 - (te.embedding <=> :query_embedding::vector) as similarity
            FROM topic_embeddings te
            JOIN articles a ON te.article_id = a.id
            WHERE 1 - (te.embedding <=> :query_embedding::vector) > :threshold
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
                created_at=row.created_at
            )
            similarity = row.similarity
            similar_articles.append((article, similarity))

        return similar_articles

    async def check_duplicate_content(
        self,
        session: AsyncSession,
        content: str,
        threshold: float = 0.95
    ) -> Optional[Article]:
        """檢查是否有重複內容"""

        similar = await self.find_similar_articles(
            session,
            content,
            limit=1,
            threshold=threshold
        )

        if similar:
            return similar[0][0]
        return None
```

### 3.3 批量處理和優化

```python
    async def batch_generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """批量生成嵌入（優化 API 調用）"""

        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=batch
            )
            embeddings.extend([d.embedding for d in response.data])

        return embeddings

    async def reindex_all_articles(self, session: AsyncSession):
        """重新索引所有文章的嵌入"""

        # 獲取所有文章
        result = await session.execute(
            select(Article).where(Article.body.isnot(None))
        )
        articles = result.scalars().all()

        # 批量生成嵌入
        texts = [f"{a.title}\n\n{a.body[:1000]}" for a in articles]
        embeddings = await self.batch_generate_embeddings(texts)

        # 批量更新
        for article, embedding in zip(articles, embeddings):
            await self.store_article_embedding(
                session,
                article.id,
                texts[articles.index(article)]
            )
```

## 4. API 端點實現

```python
# src/api/routes/semantic_search.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.config.database import get_session
from src.services.semantic_similarity import SemanticSimilarityService
from src.schemas.semantic import (
    SimilarArticleResponse,
    DuplicateCheckRequest,
    EmbeddingRequest
)

router = APIRouter(prefix="/v1/semantic", tags=["Semantic Search"])
service = SemanticSimilarityService()

@router.post("/embeddings")
async def create_embedding(
    request: EmbeddingRequest,
    session: AsyncSession = Depends(get_session)
):
    """為文章生成並存儲向量嵌入"""
    embedding = await service.store_article_embedding(
        session,
        request.article_id,
        request.text
    )
    return {"message": "Embedding created", "id": embedding.id}

@router.get("/similar")
async def find_similar(
    query: str = Query(..., description="搜索查詢"),
    limit: int = Query(10, ge=1, le=100),
    threshold: float = Query(0.85, ge=0, le=1),
    session: AsyncSession = Depends(get_session)
) -> List[SimilarArticleResponse]:
    """查找相似文章"""
    results = await service.find_similar_articles(
        session, query, limit, threshold
    )

    return [
        SimilarArticleResponse(
            article_id=article.id,
            title=article.title,
            similarity=similarity,
            excerpt=article.body[:200] + "..." if len(article.body) > 200 else article.body
        )
        for article, similarity in results
    ]

@router.post("/check-duplicate")
async def check_duplicate(
    request: DuplicateCheckRequest,
    session: AsyncSession = Depends(get_session)
):
    """檢查內容是否重複"""
    duplicate = await service.check_duplicate_content(
        session,
        request.content,
        request.threshold
    )

    if duplicate:
        return {
            "is_duplicate": True,
            "article_id": duplicate.id,
            "title": duplicate.title
        }

    return {"is_duplicate": False}

@router.post("/reindex")
async def reindex_articles(
    session: AsyncSession = Depends(get_session)
):
    """重新索引所有文章"""
    await service.reindex_all_articles(session)
    return {"message": "Reindexing completed"}
```

## 5. 使用場景示例

### 5.1 新文章生成前的重複檢查

```python
# 在生成新文章前檢查
async def generate_article_with_duplicate_check(topic: str):
    # 1. 先檢查是否有相似內容
    duplicate = await semantic_service.check_duplicate_content(
        session, topic, threshold=0.90
    )

    if duplicate:
        logger.warning(f"發現重複內容: {duplicate.title}")
        return duplicate

    # 2. 生成新文章
    article = await article_service.generate_article(topic)

    # 3. 存儲向量嵌入
    await semantic_service.store_article_embedding(
        session, article.id, f"{article.title}\n\n{article.body[:1000]}"
    )

    return article
```

### 5.2 內容推薦系統

```python
# 基於當前文章推薦相關內容
async def recommend_related_articles(article_id: int):
    # 獲取當前文章
    article = await session.get(Article, article_id)

    # 查找相似文章
    similar = await semantic_service.find_similar_articles(
        session,
        query_text=f"{article.title}\n{article.body[:500]}",
        limit=5,
        threshold=0.75
    )

    # 過濾掉自己
    recommendations = [
        (a, score) for a, score in similar
        if a.id != article_id
    ]

    return recommendations
```

### 5.3 主題聚類

```python
# 將文章按主題聚類
async def cluster_articles_by_topic(threshold: float = 0.80):
    # 獲取所有嵌入
    embeddings = await session.execute(
        select(TopicEmbedding)
    )
    all_embeddings = embeddings.scalars().all()

    # 使用 DBSCAN 或 K-means 進行聚類
    from sklearn.cluster import DBSCAN
    import numpy as np

    vectors = np.array([e.embedding for e in all_embeddings])
    clustering = DBSCAN(eps=1-threshold, min_samples=2, metric='cosine')
    labels = clustering.fit_predict(vectors)

    # 組織聚類結果
    clusters = {}
    for embedding, label in zip(all_embeddings, labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(embedding.article_id)

    return clusters
```

## 6. 性能優化建議

### 6.1 索引優化

```sql
-- 使用 HNSW 索引（更快的查詢）
CREATE INDEX idx_embeddings_hnsw ON topic_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 調整索引參數
ALTER INDEX idx_embeddings_hnsw SET (ef = 40);
```

### 6.2 查詢優化

```python
# 使用近似最近鄰搜索
async def fast_similarity_search(query_vector, k=10):
    # 設置 pgvector 的搜索參數
    await session.execute(text("SET hnsw.ef = 100"))

    # 執行查詢
    result = await session.execute(
        text("""
            SELECT *, embedding <=> :vector as distance
            FROM topic_embeddings
            ORDER BY embedding <=> :vector
            LIMIT :k
        """),
        {"vector": query_vector, "k": k}
    )

    return result.all()
```

### 6.3 緩存策略

```python
from functools import lru_cache
import hashlib

# 緩存嵌入生成結果
@lru_cache(maxsize=1000)
def get_cached_embedding(text_hash: str):
    return embeddings_cache.get(text_hash)

async def generate_embedding_with_cache(text: str):
    text_hash = hashlib.md5(text.encode()).hexdigest()

    # 檢查緩存
    cached = get_cached_embedding(text_hash)
    if cached:
        return cached

    # 生成新嵌入
    embedding = await generate_embedding(text)
    embeddings_cache[text_hash] = embedding

    return embedding
```

## 7. 監控和維護

### 7.1 性能監控

```python
# 監控查詢性能
async def monitor_query_performance():
    await session.execute(text("""
        SELECT
            query,
            calls,
            total_time,
            mean_time,
            max_time
        FROM pg_stat_statements
        WHERE query LIKE '%topic_embeddings%'
        ORDER BY total_time DESC
        LIMIT 10
    """))
```

### 7.2 數據質量檢查

```python
# 檢查嵌入完整性
async def check_embedding_integrity():
    # 查找缺失嵌入的文章
    missing = await session.execute(text("""
        SELECT a.id, a.title
        FROM articles a
        LEFT JOIN topic_embeddings te ON a.id = te.article_id
        WHERE te.id IS NULL
        AND a.body IS NOT NULL
    """))

    return missing.all()
```

## 8. 成本估算

### OpenAI Embedding API 成本
- text-embedding-3-small: $0.00002 / 1K tokens
- 平均文章（1000 字）≈ 750 tokens
- 成本: $0.000015 / 文章

### 存儲成本
- 每個向量: 1536 * 4 bytes = 6KB
- 10,000 篇文章: 60MB
- Supabase 存儲成本: 可忽略

### 查詢成本
- pgvector 查詢: < 10ms（使用 HNSW 索引）
- API 調用成本: 僅計算資源