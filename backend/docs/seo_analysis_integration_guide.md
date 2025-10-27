# SEO Analysis Integration Guide

> **⚠️ 功能定位说明 | Feature Scope**
>
> 本文档描述的是**批量SEO分析功能**，专门用于为"外部导入的历史文章"生成SEO metadata。
>
> **This document describes the Batch SEO Analysis feature**, specifically for generating SEO metadata for externally imported historical articles.
>
> ---
>
> ### 🔍 与新文章校对工作流的区别
>
> 如果您要了解**新文章的校对+SEO优化工作流**，请参考以下文档：
> - 📄 [`article_proofreading_seo_workflow.md`](article_proofreading_seo_workflow.md) - 完整的新文章校对和优化工作流（v2.0 单一Prompt架构）
> - 📄 [`single_prompt_design.md`](single_prompt_design.md) - 单一Prompt综合分析架构设计
> - 📄 [`user_experience_workflow.md`](user_experience_workflow.md) - 新文章工作流的用户体验说明
>
> ### 📊 两个功能的对比
>
> | 功能 | SEO Analysis（本文档） | 校对+SEO工作流 |
> |------|----------------------|--------------|
> | **目标文章** | 导入的历史文章（IMPORTED状态） | 新建文章（用户撰写） |
> | **触发方式** | 手动API调用批量处理 | 用户提交新文章自动触发 |
> | **处理内容** | 仅SEO metadata生成 | 450条校对规则 + Meta + 关键词 + FAQ |
> | **用户交互** | 后台自动，无交互 | 用户审核、编辑、确认 |
> | **版本管理** | 无版本管理 | 三版本管理（原始/建议/最终） |
> | **工作流** | IMPORTED → SEO_OPTIMIZED | 原始 → 建议 → 最终 → 发布 |
> | **使用场景** | 迁移旧文章、批量优化 | 日常新闻发布流程 |
> | **AI架构** | 独立SEO分析调用 | 单一Prompt综合分析（v2.0） |
>
> **简单来说：**
> - **SEO Analysis**: 为已有的导入文章补充SEO信息
> - **校对工作流**: 新文章从撰写到发布的完整质量控制流程
>
> ---

## Overview

The SEO Analysis Integration automatically generates SEO metadata for imported articles using Claude AI. Articles with status `IMPORTED` can be batch-analyzed or individually optimized.

**Use Case**: This feature is designed for bulk processing of externally imported articles (e.g., migrating content from legacy systems) that need SEO metadata generation without the full proofreading workflow.

## Features

- 🤖 **AI-Powered Analysis**: Uses Claude to generate optimized SEO metadata
- 📊 **Batch Processing**: Analyze multiple articles asynchronously
- 🎯 **Auto-Optimization**: Generates meta titles, descriptions, and keywords
- 📈 **Scoring**: Provides SEO and readability scores
- 🔄 **Status Management**: Automatically updates article status to `SEO_OPTIMIZED`

## Workflow

```
IMPORTED → (SEO Analysis) → SEO_OPTIMIZED → READY_TO_PUBLISH
```

When SEO analysis completes:
1. Creates `SEOMetadata` record linked to article
2. Updates article status to `SEO_OPTIMIZED`
3. Returns SEO scores and focus keyword

## API Endpoints

### 1. Analyze Single Article

**Endpoint**: `POST /v1/seo/analyze/{article_id}`

**Description**: Queue SEO analysis for a specific article

**Response**: 202 Accepted
```json
{
  "task_id": "abc123...",
  "message": "SEO analysis task queued for article 42",
  "article_id": 42,
  "status_url": "/v1/seo/status/abc123..."
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/v1/seo/analyze/1
```

### 2. Analyze Batch (All Imported Articles)

**Endpoint**: `POST /v1/seo/analyze-batch?limit={limit}`

**Description**: Queue batch SEO analysis for all imported articles without SEO

**Parameters**:
- `limit` (optional): Maximum number of articles to process

**Response**: 202 Accepted
```json
{
  "task_id": "xyz789...",
  "message": "Batch SEO analysis task queued (limit: 10)",
  "limit": 10,
  "status_url": "/v1/seo/status/xyz789..."
}
```

**Examples**:
```bash
# Analyze all imported articles
curl -X POST http://localhost:8000/v1/seo/analyze-batch

# Analyze first 10 articles
curl -X POST "http://localhost:8000/v1/seo/analyze-batch?limit=10"
```

### 3. Check Task Status

**Endpoint**: `GET /v1/seo/status/{task_id}`

**Response**:

**Single Article Result**:
```json
{
  "task_id": "abc123...",
  "status": "completed",
  "result": {
    "article_id": 1,
    "seo_id": 5,
    "focus_keyword": "python fastapi tutorial",
    "seo_score": 92.3,
    "readability_score": 78.5,
    "status": "completed"
  }
}
```

**Batch Result**:
```json
{
  "task_id": "xyz789...",
  "status": "completed",
  "result": {
    "successful_count": 18,
    "failed_count": 2,
    "total_count": 20,
    "errors": [
      "Article 5 (Some Title...): Article already has SEO metadata",
      "Article 12 (Another Title...): API rate limit exceeded"
    ],
    "status": "completed"
  }
}
```

### 4. Cancel Task

**Endpoint**: `DELETE /v1/seo/task/{task_id}`

**Response**:
```json
{
  "message": "SEO analysis task abc123... cancelled",
  "status": "cancelled"
}
```

## Generated SEO Metadata

For each article, the following SEO metadata is generated:

### Core Fields
- **meta_title** (50-60 characters): SEO-optimized title for search engines
- **meta_description** (150-160 characters): Compelling description for SERP
- **focus_keyword**: Primary keyword the article should rank for

### Keywords
- **primary_keywords** (3-5): Main keywords extracted from content
- **secondary_keywords** (5-10): Supporting and LSI keywords

### Scores
- **seo_score** (0-100): Overall SEO optimization score
- **readability_score** (0-100): Flesch Reading Ease score

### Additional Data (JSONB)
- **open_graph_data**: Social media optimization
  - `og_title`: Social title (up to 70 chars)
  - `og_description`: Social description (up to 200 chars)
  - `og_image`: Featured image URL
- **schema_markup**: Structured data type (e.g., "Article")

## Database Changes

### SEOMetadata Table

After analysis, a record is created in `seo_metadata`:

```sql
SELECT
    a.id,
    a.title,
    a.status,
    s.meta_title,
    s.focus_keyword,
    s.seo_score
FROM articles a
JOIN seo_metadata s ON a.id = s.article_id
WHERE a.status = 'seo_optimized';
```

### Status Update Trigger

The `sync_article_status_on_seo_insert` trigger automatically updates article status:

```sql
-- Before: status = 'imported'
-- After SEO analysis: status = 'seo_optimized'
```

## Complete Workflow Example

### 1. Import Articles

```bash
# Import 20 articles from CSV
IMPORT_TASK=$(curl -X POST http://localhost:8000/v1/import \
  -F "file=@articles_full_sample.csv" \
  | jq -r '.task_id')

echo "Import task: $IMPORT_TASK"
```

### 2. Wait for Import to Complete

```bash
while true; do
  STATUS=$(curl -s http://localhost:8000/v1/import/status/$IMPORT_TASK \
    | jq -r '.status')

  echo "Import status: $STATUS"

  if [[ "$STATUS" == "completed" ]]; then
    break
  fi

  sleep 5
done
```

### 3. Check Imported Articles

```bash
# Count articles by status
docker compose exec postgres psql -U cms_user -d cms_automation \
  -c "SELECT status, COUNT(*) FROM articles GROUP BY status;"

# Output:
#    status   | count
# ------------+-------
#  imported   |    20
```

### 4. Run Batch SEO Analysis

```bash
# Analyze all imported articles
SEO_TASK=$(curl -X POST http://localhost:8000/v1/seo/analyze-batch \
  | jq -r '.task_id')

echo "SEO analysis task: $SEO_TASK"
```

### 5. Monitor SEO Analysis Progress

```bash
while true; do
  RESULT=$(curl -s http://localhost:8000/v1/seo/status/$SEO_TASK)
  STATUS=$(echo $RESULT | jq -r '.status')

  echo "SEO analysis status: $STATUS"

  if [[ "$STATUS" == "completed" ]]; then
    echo "Results:"
    echo $RESULT | jq '.result'
    break
  fi

  sleep 10
done
```

### 6. Verify SEO Optimization

```bash
# Check article statuses after SEO
docker compose exec postgres psql -U cms_user -d cms_automation \
  -c "SELECT status, COUNT(*) FROM articles GROUP BY status;"

# Output:
#       status      | count
# ------------------+-------
#  seo_optimized    |    18
#  imported         |     2

# View SEO metadata
docker compose exec postgres psql -U cms_user -d cms_automation \
  -c "SELECT a.title, s.focus_keyword, s.seo_score, s.readability_score
      FROM articles a
      JOIN seo_metadata s ON a.id = s.article_id
      LIMIT 5;"
```

## Error Handling

### Common Errors

1. **Article already has SEO metadata**
   - Error: `Article {id} already has SEO metadata`
   - Solution: Skip this article or delete existing SEO first

2. **Article not found**
   - Error: `Article {id} not found`
   - Solution: Verify article ID exists

3. **Claude API rate limit**
   - Error: `API rate limit exceeded`
   - Solution: Wait and retry, or reduce batch size

4. **Invalid Claude API response**
   - Error: `Invalid JSON response`
   - Solution: Retry analysis, check article content quality

### Retry Failed Articles

```bash
# Get failed article IDs from batch result
FAILED_IDS=$(curl -s http://localhost:8000/v1/seo/status/$SEO_TASK \
  | jq -r '.result.errors[]' \
  | grep -oP 'Article \K\d+')

# Retry each failed article
for ID in $FAILED_IDS; do
  echo "Retrying article $ID..."
  curl -X POST http://localhost:8000/v1/seo/analyze/$ID
  sleep 2
done
```

## Performance Considerations

### Claude API Costs

Each SEO analysis makes 1 API call to Claude:
- **Model**: claude-3-5-sonnet (or configured model)
- **Input tokens**: ~1000-2000 (article content)
- **Output tokens**: ~500-800 (SEO metadata)
- **Estimated cost**: $0.01-0.02 per article

For 100 articles: ~$1-2 USD

### Processing Time

- **Single article**: 3-5 seconds (Claude API latency)
- **Batch of 20 articles**: 1-2 minutes (sequential processing)
- **Batch of 100 articles**: 5-10 minutes

### Optimization Tips

1. **Use batch processing** for multiple articles
2. **Set reasonable limits** (e.g., 50 articles per batch)
3. **Process during off-peak hours** to avoid rate limits
4. **Monitor Celery queue** for task backlog

## Integration with Publishing Workflow

After SEO optimization, articles are ready for the next phase:

```
1. Import      → status: IMPORTED
2. SEO Analysis → status: SEO_OPTIMIZED
3. Review       → status: READY_TO_PUBLISH
4. Computer Use → status: PUBLISHING
5. Published    → status: PUBLISHED
```

### Auto-Trigger SEO After Import

You can create a webhook or scheduled task to automatically trigger SEO analysis after import completes:

```python
# In import_articles_task after completion
if result['successful_imports'] > 0:
    # Queue batch SEO analysis
    analyze_seo_batch_task.delay(limit=None)
```

## Monitoring and Observability

### Check SEO Queue Status

```bash
# View Celery task queue
docker compose exec backend celery -A src.workers.celery_app inspect active

# Check queue length
docker compose exec backend celery -A src.workers.celery_app inspect stats
```

### View SEO Analysis Logs

```bash
# View recent SEO analysis logs
docker compose logs backend | grep seo_analysis

# Filter for completed analyses
docker compose logs backend | grep seo_analysis_completed
```

### Database Metrics

```sql
-- SEO metadata statistics
SELECT
    COUNT(*) as total_with_seo,
    AVG(seo_score) as avg_seo_score,
    AVG(readability_score) as avg_readability,
    MIN(seo_score) as min_score,
    MAX(seo_score) as max_score
FROM seo_metadata;

-- Articles by status
SELECT
    status,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
FROM articles
GROUP BY status
ORDER BY count DESC;
```

## Best Practices

1. **Import first, then analyze**: Complete import before running SEO analysis
2. **Use batch processing**: More efficient than individual requests
3. **Set reasonable limits**: Avoid overwhelming Claude API
4. **Monitor costs**: Track API usage and spending
5. **Review generated SEO**: Spot-check AI-generated metadata
6. **Handle errors gracefully**: Retry failed analyses separately
7. **Update article content**: Re-analyze if content changes significantly

## Troubleshooting

### SEO analysis stuck in "pending"

Check Celery worker:
```bash
docker compose ps backend
docker compose logs backend | tail -50
```

Restart worker if needed:
```bash
docker compose restart backend
```

### Low SEO scores

- Review article content quality
- Ensure adequate word count (500+ words recommended)
- Check keyword usage and relevance
- Improve readability (shorter sentences, simpler words)

### Inconsistent metadata

- Claude may generate slightly different results for same input
- Use `temperature=0.3` for more consistent output (already configured)
- Review and manually adjust if needed

## API Integration Examples

### Python

```python
import requests
import time

# Analyze single article
response = requests.post('http://localhost:8000/v1/seo/analyze/1')
task_id = response.json()['task_id']

# Poll status
while True:
    status = requests.get(f'http://localhost:8000/v1/seo/status/{task_id}').json()

    if status['status'] == 'completed':
        print(f"SEO Score: {status['result']['seo_score']}")
        print(f"Focus Keyword: {status['result']['focus_keyword']}")
        break

    time.sleep(5)
```

### JavaScript

```javascript
// Batch analysis
const response = await fetch('/v1/seo/analyze-batch?limit=10', {
  method: 'POST'
});

const { task_id } = await response.json();

// Poll status
const checkStatus = async () => {
  const status = await fetch(`/v1/seo/status/${task_id}`).then(r => r.json());

  if (status.status === 'completed') {
    console.log(`Successful: ${status.result.successful_count}`);
    console.log(`Failed: ${status.result.failed_count}`);
    return;
  }

  setTimeout(checkStatus, 5000);
};

checkStatus();
```

## See Also

- [Article Import Guide](article_import_guide.md)
- [SEO Metadata Schema](../src/models/seo.py)
- [SEO Analyzer Service](../src/services/seo_analyzer.py)
- [API Documentation](http://localhost:8000/docs)
