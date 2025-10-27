# Article Import Test Samples

This directory contains sample article files for testing the import functionality.

## Available Samples

### 1. CSV Format

**File**: `articles_full_sample.csv`
- **Records**: 20 articles
- **Features**:
  - Complete SEO metadata (all fields)
  - Mix of imported/draft statuses
  - Featured images
  - Published timestamps
  - Various technical topics

**Usage**:
```bash
curl -X POST http://localhost:8000/v1/import \
  -F "file=@articles_full_sample.csv" \
  -F "file_format=csv"
```

### 2. JSON Format

**File**: `articles_full_sample.json`
- **Records**: 12 articles
- **Features**:
  - Structured SEO objects
  - Full article metadata
  - Featured images
  - Mix of statuses
  - Technical content

**Usage**:
```bash
curl -X POST http://localhost:8000/v1/import \
  -F "file=@articles_full_sample.json" \
  -F "file_format=json"
```

### 3. WordPress XML Format

**File**: `wordpress_export_sample.xml`
- **Records**: 5 articles (posts only)
- **Features**:
  - Standard WXR format
  - Yoast SEO metadata
  - Rank Math SEO metadata
  - HTML content with formatting
  - Post IDs and permalinks

**Usage**:
```bash
curl -X POST http://localhost:8000/v1/import \
  -F "file=@wordpress_export_sample.xml" \
  -F "file_format=wordpress"
```

## Article Topics Covered

The sample data includes technical articles on:

- **Backend**: Python FastAPI, Django REST, Node.js/Express, Rust
- **Frontend**: React, Vue.js, Next.js, Svelte, Angular, Flutter
- **DevOps**: Docker, Kubernetes, CI/CD, Terraform, Nginx
- **Databases**: PostgreSQL, MongoDB, Elasticsearch, Redis
- **Architecture**: Microservices, Message Queues (RabbitMQ, Kafka), Service Mesh (Istio)
- **Monitoring**: Prometheus, Grafana

## SEO Metadata Quality

All samples include properly formatted SEO metadata:
- ✅ meta_title: 50-60 characters
- ✅ meta_description: 150-160 characters
- ✅ focus_keyword: Present
- ✅ primary_keywords: 3-5 keywords
- ✅ secondary_keywords: 5-10 keywords
- ✅ readability_score: 70-80 range
- ✅ seo_score: 84-92 range

## Expected Import Results

### CSV Import
```json
{
  "total_records": 20,
  "successful_imports": 20,
  "failed_imports": 0,
  "success_rate": 100.0
}
```

### JSON Import
```json
{
  "total_records": 12,
  "successful_imports": 12,
  "failed_imports": 0,
  "success_rate": 100.0
}
```

### WordPress XML Import
```json
{
  "total_records": 5,
  "successful_imports": 5,
  "failed_imports": 0,
  "success_rate": 100.0
}
```

## Testing Workflow

1. **Import articles**:
```bash
TASK_ID=$(curl -X POST http://localhost:8000/v1/import \
  -F "file=@articles_full_sample.csv" \
  | jq -r '.task_id')
```

2. **Check status**:
```bash
curl http://localhost:8000/v1/import/status/$TASK_ID | jq
```

3. **Verify imported articles**:
```bash
curl http://localhost:8000/v1/articles | jq
```

4. **Count articles by status**:
```bash
docker compose exec postgres psql -U cms_user -d cms_automation \
  -c "SELECT status, COUNT(*) FROM articles GROUP BY status;"
```

5. **View articles with SEO**:
```bash
docker compose exec postgres psql -U cms_user -d cms_automation \
  -c "SELECT a.title, s.focus_keyword, s.seo_score
      FROM articles a
      JOIN seo_metadata s ON a.id = s.article_id
      LIMIT 10;"
```

## Sample Data Characteristics

- **Author IDs**: Prefixed during import (e.g., `csv_dev001`, `json_python_expert_01`, `wordpress_admin`)
- **Statuses**: Mix of `imported` (default) and `draft`
- **Publication Dates**: Range from Jan 15-29, 2025
- **Image Paths**: Sample paths (images not included)
- **Content Length**: 200-500 words per article
- **SEO Quality**: Production-ready metadata

## Notes

- These are **test fixtures** for unit/integration testing
- Images referenced in `featured_image_path` do not exist (paths only)
- All content is AI-generated for testing purposes
- Author IDs are fictional and will be normalized during import
