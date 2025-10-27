# Article Import Service Guide

## Overview

The Article Import Service allows bulk import of articles from various file formats into the CMS system. All imports are processed asynchronously using Celery, making it suitable for large datasets.

## Supported Formats

- **CSV** (`.csv`) - Comma-separated values
- **JSON** (`.json`) - JSON format with article array
- **WordPress XML** (`.xml`, `.wxr`) - WordPress export files

## API Endpoints

### 1. Import Articles

**Endpoint**: `POST /v1/import`

**Request**: Multipart form data
- `file`: Upload file (required)
- `file_format`: Format override (optional: csv, json, wordpress)

**Response**: 202 Accepted
```json
{
  "task_id": "abc123...",
  "message": "Import task queued for articles.csv",
  "status_url": "/v1/import/status/abc123..."
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/v1/import \
  -F "file=@articles.csv" \
  -F "file_format=csv"
```

### 2. Check Import Status

**Endpoint**: `GET /v1/import/status/{task_id}`

**Response**:
```json
{
  "task_id": "abc123...",
  "status": "completed",
  "result": {
    "total_records": 100,
    "successful_imports": 98,
    "failed_imports": 2,
    "success_rate": 98.0,
    "imported_article_ids": [1, 2, 3, ...],
    "errors": [
      {
        "row_number": 15,
        "error_message": "Title is required",
        "raw_data": {...}
      }
    ]
  }
}
```

**Status Values**:
- `pending` - Task queued but not started
- `running` - Task is processing
- `completed` - Task finished successfully
- `failed` - Task failed

### 3. Cancel Import Task

**Endpoint**: `DELETE /v1/import/{task_id}`

**Response**:
```json
{
  "message": "Import task abc123... cancelled",
  "status": "cancelled"
}
```

## File Format Specifications

### CSV Format

**Required Fields**:
- `title` - Article title (1-500 chars)
- `body` - Article content
- `author_id` - Author identifier (will be prefixed)

**Optional Fields**:
- `status` - Article status (imported, draft, published, etc.)
- `featured_image_path` - Path to featured image
- `published_at` - Publication timestamp (YYYY-MM-DD HH:MM:SS)

**SEO Fields** (optional, with `seo_` prefix):
- `seo_meta_title` - SEO title (50-60 chars)
- `seo_meta_description` - SEO description (150-160 chars)
- `seo_focus_keyword` - Primary keyword
- `seo_primary_keywords` - Comma-separated (3-5 keywords)
- `seo_secondary_keywords` - Comma-separated (5-10 keywords)
- `seo_readability_score` - Score 0-100
- `seo_seo_score` - Score 0-100

**Example CSV**:
```csv
title,body,author_id,status,seo_meta_title,seo_meta_description,seo_focus_keyword,seo_primary_keywords,seo_secondary_keywords
"Article Title","Article content here...","user123","imported","SEO Title Here (50-60 chars)","SEO description must be between 150-160 characters long. This is a sample description that meets the length requirement for proper SEO optimization.","main keyword","keyword1,keyword2,keyword3","key1,key2,key3,key4,key5"
```

### JSON Format

**Structure**:
```json
{
  "articles": [
    {
      "title": "Article Title",
      "body": "Article content...",
      "author_id": "user123",
      "status": "imported",
      "featured_image_path": "/images/cover.jpg",
      "published_at": "2025-01-01 10:00:00",
      "seo": {
        "meta_title": "SEO Title (50-60 chars)",
        "meta_description": "SEO description between 150-160 characters. This is a sample that demonstrates the proper length for search engine optimization purposes.",
        "focus_keyword": "main keyword",
        "primary_keywords": ["keyword1", "keyword2", "keyword3"],
        "secondary_keywords": ["key1", "key2", "key3", "key4", "key5"],
        "readability_score": 75.0,
        "seo_score": 88.0
      }
    }
  ]
}
```

### WordPress XML Format

Standard WordPress eXtended RSS (WXR) export format. The importer automatically:
- Extracts posts (skips pages and attachments)
- Converts WordPress post status to article status
- Extracts Yoast/Rank Math SEO metadata if present
- Preserves original post IDs and URLs

**Note**: WordPress SEO metadata may not meet strict length requirements. SEO re-optimization is recommended after import.

## Author ID Handling

Author IDs from import files are **prefixed** to avoid conflicts with existing users:

- CSV imports: `csv_user123` → unique integer ID
- JSON imports: `json_user123` → unique integer ID
- WordPress imports: `wordpress_admin` → unique integer ID

The same source author ID always maps to the same internal ID consistently.

## Import Behavior

### Transaction Strategy

The import uses a **partial commit** strategy:
- ✅ Successful records are imported
- ❌ Failed records are logged but don't stop the import
- 📊 Import continues to completion
- 🔄 All successful imports are committed together

### Error Handling

Errors are collected and returned in the result:
```json
{
  "errors": [
    {
      "row_number": 15,
      "error_message": "SEO meta_description must be 150-160 characters (got 169)",
      "raw_data": {
        "title": "Article Title",
        "body": "..."
      }
    }
  ]
}
```

### Article Status

All imported articles default to `IMPORTED` status unless explicitly specified in the import file. This allows review before publishing.

## Best Practices

### 1. Validate Data Before Import

- Check title and body are not empty
- Verify SEO field lengths match requirements
- Ensure author IDs are consistent

### 2. Use Test Imports

Test with small datasets (10-50 records) before bulk import.

### 3. Monitor Import Progress

Poll the status endpoint to track progress:
```bash
# Check every 5 seconds
watch -n 5 curl http://localhost:8000/v1/import/status/{task_id}
```

### 4. Handle Errors

Review error logs and fix source data for failed records, then re-import.

### 5. SEO Optimization

SEO metadata is optional during import. You can:
- Import with SEO data (strict validation)
- Import without SEO (optimize later)
- Import partial SEO (re-optimize)

## Workflow Example

### Complete Import Workflow

```bash
# 1. Prepare data file
cat > articles.csv << 'EOF'
title,body,author_id,status
"Test Article","Content here","user1","imported"
EOF

# 2. Import articles
TASK_ID=$(curl -X POST http://localhost:8000/v1/import \
  -F "file=@articles.csv" \
  | jq -r '.task_id')

echo "Task ID: $TASK_ID"

# 3. Check status
while true; do
  STATUS=$(curl http://localhost:8000/v1/import/status/$TASK_ID \
    | jq -r '.status')

  echo "Status: $STATUS"

  if [[ "$STATUS" == "completed" ]] || [[ "$STATUS" == "failed" ]]; then
    break
  fi

  sleep 5
done

# 4. Get final result
curl http://localhost:8000/v1/import/status/$TASK_ID | jq

# 5. Verify imported articles
curl http://localhost:8000/v1/articles | jq
```

## Integration with Publishing Workflow

After import, articles follow the standard workflow:

```
IMPORTED → (SEO optimization) → SEO_OPTIMIZED → READY_TO_PUBLISH → PUBLISHING → PUBLISHED
```

1. **Import**: Articles enter with `IMPORTED` status
2. **SEO Analysis**: Run SEO analyzer on imported articles
3. **Review**: Manual review if needed
4. **Publishing**: Use Computer Use service to publish to WordPress

## Performance

- **CSV/JSON**: ~100-500 articles/second (parsing)
- **WordPress XML**: ~50-100 articles/second (XML parsing overhead)
- **Database insertion**: ~10-50 articles/second
- **Async processing**: Non-blocking API response

Large imports (1000+ articles) are handled efficiently through Celery task queue.

## Troubleshooting

### Import Task Stuck

Check Celery worker status:
```bash
docker compose exec backend celery -A src.workers.celery_app inspect active
```

### High Failure Rate

- Validate SEO field lengths
- Check required fields are present
- Review error messages in result

### Temporary Files

Import files are stored in `/tmp/cms_imports/`. They are not automatically cleaned up. Consider adding a cleanup cron job:

```bash
# Clean files older than 7 days
find /tmp/cms_imports -type f -mtime +7 -delete
```

## API Integration Examples

### Python

```python
import requests

# Upload and import
with open('articles.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/v1/import',
        files={'file': f},
        data={'file_format': 'csv'}
    )

task_id = response.json()['task_id']

# Check status
import time
while True:
    status = requests.get(f'http://localhost:8000/v1/import/status/{task_id}').json()

    if status['status'] in ['completed', 'failed']:
        print(status)
        break

    time.sleep(5)
```

### JavaScript

```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('file_format', 'csv');

const response = await fetch('/v1/import', {
  method: 'POST',
  body: formData
});

const { task_id } = await response.json();

// Poll status
const checkStatus = async () => {
  const status = await fetch(`/v1/import/status/${task_id}`).then(r => r.json());

  if (status.status === 'completed' || status.status === 'failed') {
    console.log(status);
    return;
  }

  setTimeout(checkStatus, 5000);
};

checkStatus();
```

## Testing

Run import service tests:
```bash
# All tests
docker compose exec backend poetry run pytest tests/services/article_importer/ -v

# CSV tests only
docker compose exec backend poetry run pytest tests/services/article_importer/test_csv_importer.py -v

# JSON tests only
docker compose exec backend poetry run pytest tests/services/article_importer/test_json_importer.py -v
```

## See Also

- [SEO Analyzer Guide](seo_analyzer_guide.md)
- [Publishing Service Guide](publishing_service_guide.md)
- [API Documentation](http://localhost:8000/docs)
