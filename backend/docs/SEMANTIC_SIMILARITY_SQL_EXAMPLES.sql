-- ============================================================================
-- 語義相似度檢測 - SQL 查詢範例
-- 使用 pgvector 擴展進行向量搜索
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. 基礎設置
-- ----------------------------------------------------------------------------

-- 確認 pgvector 擴展已安裝
SELECT * FROM pg_extension WHERE extname = 'vector';

-- 查看 vector 類型支持的操作符
SELECT
    oprname AS operator,
    oprcode::regproc AS function,
    oprleft::regtype AS left_type,
    oprright::regtype AS right_type
FROM pg_operator
WHERE oprname IN ('<->', '<#>', '<=>')
AND oprleft = 'vector'::regtype;

-- ----------------------------------------------------------------------------
-- 2. 基本向量操作
-- ----------------------------------------------------------------------------

-- 計算兩個向量的餘弦相似度
-- 注意：<=> 返回餘弦距離（0-2），相似度 = 1 - (distance / 2)
SELECT
    1 - ('[1,2,3]'::vector <=> '[1,2,3]'::vector) AS similarity;  -- 結果: 1 (完全相同)

-- 計算兩個向量的歐幾里得距離
SELECT
    '[1,2,3]'::vector <-> '[4,5,6]'::vector AS euclidean_distance;

-- 計算兩個向量的負內積
SELECT
    '[1,2,3]'::vector <#> '[4,5,6]'::vector AS negative_inner_product;

-- ----------------------------------------------------------------------------
-- 3. 查找相似文章
-- ----------------------------------------------------------------------------

-- 3.1 基本相似度搜索
WITH query_embedding AS (
    -- 假設這是查詢文本的嵌入向量（實際應用中由 API 生成）
    SELECT embedding
    FROM topic_embeddings
    WHERE article_id = 1  -- 使用某篇文章的嵌入作為查詢
)
SELECT
    a.id,
    a.title,
    SUBSTRING(a.body, 1, 100) AS excerpt,
    1 - (te.embedding <=> q.embedding) AS similarity,
    te.embedding <=> q.embedding AS cosine_distance
FROM topic_embeddings te
CROSS JOIN query_embedding q
JOIN articles a ON te.article_id = a.id
WHERE te.article_id != 1  -- 排除查詢文章本身
ORDER BY te.embedding <=> q.embedding  -- 按距離排序（越小越相似）
LIMIT 10;

-- 3.2 設置相似度閾值
-- 找出相似度大於 0.85 的文章
WITH query_embedding AS (
    SELECT embedding FROM topic_embeddings WHERE article_id = 1
)
SELECT
    a.id,
    a.title,
    1 - (te.embedding <=> q.embedding) AS similarity
FROM topic_embeddings te
CROSS JOIN query_embedding q
JOIN articles a ON te.article_id = a.id
WHERE 1 - (te.embedding <=> q.embedding) > 0.85  -- 相似度閾值
    AND te.article_id != 1
ORDER BY similarity DESC;

-- ----------------------------------------------------------------------------
-- 4. 批量相似度計算
-- ----------------------------------------------------------------------------

-- 4.1 計算所有文章對的相似度矩陣
SELECT
    a1.title AS article_1,
    a2.title AS article_2,
    1 - (te1.embedding <=> te2.embedding) AS similarity
FROM topic_embeddings te1
JOIN topic_embeddings te2 ON te1.article_id < te2.article_id
JOIN articles a1 ON te1.article_id = a1.id
JOIN articles a2 ON te2.article_id = a2.id
WHERE 1 - (te1.embedding <=> te2.embedding) > 0.8  -- 只顯示高相似度對
ORDER BY similarity DESC;

-- 4.2 找出潛在的重複內容
-- 相似度超過 0.95 的文章對可能是重複內容
SELECT
    a1.id AS article_1_id,
    a1.title AS article_1_title,
    a2.id AS article_2_id,
    a2.title AS article_2_title,
    1 - (te1.embedding <=> te2.embedding) AS similarity,
    a1.created_at AS article_1_created,
    a2.created_at AS article_2_created
FROM topic_embeddings te1
JOIN topic_embeddings te2 ON te1.article_id < te2.article_id
JOIN articles a1 ON te1.article_id = a1.id
JOIN articles a2 ON te2.article_id = a2.id
WHERE 1 - (te1.embedding <=> te2.embedding) > 0.95
ORDER BY similarity DESC;

-- ----------------------------------------------------------------------------
-- 5. 使用索引優化查詢
-- ----------------------------------------------------------------------------

-- 5.1 創建 IVFFlat 索引（適合中等規模數據）
CREATE INDEX idx_embeddings_ivfflat ON topic_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 5.2 創建 HNSW 索引（適合大規模數據，查詢更快）
CREATE INDEX idx_embeddings_hnsw ON topic_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 5.3 設置搜索參數以優化性能
-- 對於 IVFFlat
SET ivfflat.probes = 10;  -- 增加探測數量以提高精度

-- 對於 HNSW
SET hnsw.ef = 100;  -- 增加 ef 值以提高召回率

-- 5.4 查看索引使用情況
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM topic_embeddings
ORDER BY embedding <=> '[1,2,3,...,1536]'::vector
LIMIT 10;

-- ----------------------------------------------------------------------------
-- 6. 主題聚類分析
-- ----------------------------------------------------------------------------

-- 6.1 找出每篇文章的最相似文章（構建相似度圖）
WITH similarity_pairs AS (
    SELECT
        te1.article_id AS article_id,
        te2.article_id AS similar_article_id,
        1 - (te1.embedding <=> te2.embedding) AS similarity,
        ROW_NUMBER() OVER (PARTITION BY te1.article_id ORDER BY te1.embedding <=> te2.embedding) AS rank
    FROM topic_embeddings te1
    JOIN topic_embeddings te2 ON te1.article_id != te2.article_id
)
SELECT
    a1.title AS article,
    a2.title AS most_similar,
    sp.similarity
FROM similarity_pairs sp
JOIN articles a1 ON sp.article_id = a1.id
JOIN articles a2 ON sp.similar_article_id = a2.id
WHERE sp.rank = 1  -- 只取最相似的一篇
ORDER BY sp.similarity DESC;

-- 6.2 識別主題群組（基於傳遞相似性）
WITH RECURSIVE topic_clusters AS (
    -- 初始節點：選擇未分類的文章作為種子
    SELECT
        article_id,
        article_id AS cluster_id,
        0 AS depth
    FROM topic_embeddings

    UNION ALL

    -- 遞歸添加相似文章到群組
    SELECT
        te.article_id,
        tc.cluster_id,
        tc.depth + 1
    FROM topic_clusters tc
    JOIN topic_embeddings te1 ON tc.article_id = te1.article_id
    JOIN topic_embeddings te ON
        te.article_id NOT IN (SELECT article_id FROM topic_clusters)
        AND 1 - (te1.embedding <=> te.embedding) > 0.85
    WHERE tc.depth < 3  -- 限制遞歸深度
)
SELECT
    cluster_id,
    COUNT(*) AS cluster_size,
    STRING_AGG(a.title, ', ' ORDER BY a.id) AS articles
FROM topic_clusters tc
JOIN articles a ON tc.article_id = a.id
GROUP BY cluster_id
HAVING COUNT(*) > 1
ORDER BY cluster_size DESC;

-- ----------------------------------------------------------------------------
-- 7. 性能監控查詢
-- ----------------------------------------------------------------------------

-- 7.1 檢查嵌入覆蓋率
SELECT
    COUNT(DISTINCT a.id) AS total_articles,
    COUNT(DISTINCT te.article_id) AS articles_with_embeddings,
    ROUND(COUNT(DISTINCT te.article_id)::NUMERIC / COUNT(DISTINCT a.id) * 100, 2) AS coverage_percent
FROM articles a
LEFT JOIN topic_embeddings te ON a.id = te.article_id;

-- 7.2 檢查嵌入維度一致性
SELECT
    array_length(embedding::float[], 1) AS dimensions,
    COUNT(*) AS count
FROM topic_embeddings
GROUP BY dimensions;

-- 7.3 找出缺失嵌入的文章
SELECT
    a.id,
    a.title,
    a.created_at,
    LENGTH(a.body) AS body_length
FROM articles a
LEFT JOIN topic_embeddings te ON a.id = te.article_id
WHERE te.id IS NULL
    AND a.body IS NOT NULL
    AND LENGTH(a.body) > 100
ORDER BY a.created_at DESC;

-- ----------------------------------------------------------------------------
-- 8. 實用函數
-- ----------------------------------------------------------------------------

-- 8.1 創建函數：計算兩篇文章的相似度
CREATE OR REPLACE FUNCTION calculate_article_similarity(article1_id INT, article2_id INT)
RETURNS FLOAT AS $$
DECLARE
    similarity FLOAT;
BEGIN
    SELECT 1 - (te1.embedding <=> te2.embedding)
    INTO similarity
    FROM topic_embeddings te1
    JOIN topic_embeddings te2 ON te2.article_id = article2_id
    WHERE te1.article_id = article1_id;

    RETURN COALESCE(similarity, 0);
END;
$$ LANGUAGE plpgsql;

-- 使用函數
SELECT calculate_article_similarity(1, 2);

-- 8.2 創建函數：找出最相似的 N 篇文章
CREATE OR REPLACE FUNCTION find_similar_articles(
    query_article_id INT,
    limit_count INT DEFAULT 10,
    min_similarity FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    article_id INT,
    title VARCHAR,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH query_embedding AS (
        SELECT embedding FROM topic_embeddings WHERE article_id = query_article_id
    )
    SELECT
        a.id,
        a.title,
        1 - (te.embedding <=> q.embedding)::FLOAT AS similarity
    FROM topic_embeddings te
    CROSS JOIN query_embedding q
    JOIN articles a ON te.article_id = a.id
    WHERE te.article_id != query_article_id
        AND 1 - (te.embedding <=> q.embedding) > min_similarity
    ORDER BY te.embedding <=> q.embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- 使用函數
SELECT * FROM find_similar_articles(1, 5, 0.8);

-- ----------------------------------------------------------------------------
-- 9. 維護和優化
-- ----------------------------------------------------------------------------

-- 9.1 更新統計信息
ANALYZE topic_embeddings;

-- 9.2 重建索引（如果性能下降）
REINDEX INDEX idx_embeddings_hnsw;

-- 9.3 清理無效的嵌入（對應文章已刪除）
DELETE FROM topic_embeddings te
WHERE NOT EXISTS (
    SELECT 1 FROM articles a WHERE a.id = te.article_id
);

-- 9.4 檢查索引大小
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE tablename = 'topic_embeddings'
ORDER BY pg_relation_size(indexrelid) DESC;