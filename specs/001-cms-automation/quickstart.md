# Quickstart Guide: CMS Automation Platform (Fusion Architecture)

**Feature**: 001-cms-automation
**Version**: 2.0.0 (Fusion Architecture)
**Last Updated**: 2025-10-25
**Target Audience**: Developers new to the project

## Overview

This guide helps you set up a local development environment for the **AI-powered CMS automation platform with fusion architecture**. The system supports **dual-source article workflows**:

**Workflow 1: AI Generation** (Preserved)
- Submit topic descriptions
- AI generates complete articles
- Automatic tagging and categorization
- Review and approval workflows
- Scheduled publishing

**Workflow 2: Import + SEO + Publishing** (New in v2.0)
- Import existing articles from CSV/JSON/manual entry
- Unified SEO optimization for all articles (AI-generated or imported)
- Computer Use API browser automation for WordPress publishing
- Comprehensive execution logging and screenshot capture

You'll learn how to:

- Set up backend services (API + workers + Computer Use)
- Configure Claude API integration (Messages API + Computer Use API)
- Connect to a test WordPress instance
- Run the development stack
- Test **both** core workflows:
  - AI article generation → SEO → Publishing
  - Article import → SEO → Publishing

**Estimated Setup Time**: 45-60 minutes (includes Computer Use configuration)

---

## Prerequisites

### Required Software

- **Python**: 3.11 or higher (tested with 3.13.7)
- **PostgreSQL**: 15.0 or higher (with pgvector extension)
- **Redis**: 7.0 or higher
- **Node.js**: 18 LTS or higher (for frontend)
- **Docker & Docker Compose**: Latest stable (recommended for dependencies)
- **Chrome/Chromium**: Latest stable (for Computer Use API browser automation)

### Required Accounts

- **Anthropic API Key**: Sign up at https://console.anthropic.com/
  - Need access to both Claude Messages API and Computer Use API
- **Test WordPress Instance**: WordPress site with:
  - REST API enabled
  - Application Password configured
  - SEO plugin installed (Yoast SEO or Rank Math recommended)
  - Admin credentials for Computer Use automation

### System Requirements

- **RAM**: Minimum 16 GB (Computer Use requires additional headroom)
- **Disk**: 10 GB free space (includes Chrome browser)
- **OS**: macOS, Linux, or Windows WSL2
- **Network**: Stable connection for Computer Use browser automation

---

## Quick Setup (Docker Compose - Recommended)

### 1. Clone Repository

```bash
git clone <repository-url>
cd cms_automation
git checkout 001-cms-automation
```

### 2. Create Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# =============================================================================
# API KEYS
# =============================================================================
ANTHROPIC_API_KEY=sk-ant-...  # Your Claude API key (Messages + Computer Use)

# =============================================================================
# DATABASE
# =============================================================================
DATABASE_URL=postgresql://cms_user:cms_pass@localhost:5432/cms_automation
DATABASE_POOL_SIZE=20

# =============================================================================
# REDIS
# =============================================================================
REDIS_URL=redis://localhost:6379/0

# =============================================================================
# CMS INTEGRATION (WordPress)
# =============================================================================
CMS_TYPE=wordpress
CMS_BASE_URL=https://your-test-site.com
CMS_USERNAME=admin
CMS_APPLICATION_PASSWORD=xxxx xxxx xxxx xxxx

# Computer Use Publishing (NEW in v2.0)
CMS_ADMIN_LOGIN_URL=https://your-test-site.com/wp-admin
CMS_ADMIN_USERNAME=admin
CMS_ADMIN_PASSWORD=your-admin-password  # Plain password for Computer Use
CMS_SEO_PLUGIN=yoast  # or 'rankmath'

# Screenshot Storage (NEW in v2.0)
SCREENSHOT_STORAGE_TYPE=local  # or 's3'
SCREENSHOT_STORAGE_PATH=/app/storage/screenshots  # for local storage
# For S3 storage:
# S3_BUCKET_NAME=cms-automation-screenshots
# S3_ACCESS_KEY_ID=...
# S3_SECRET_ACCESS_KEY=...
# S3_REGION=us-east-1

# =============================================================================
# APPLICATION
# =============================================================================
API_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development

# =============================================================================
# SECURITY
# =============================================================================
SECRET_KEY=<generate-random-string>  # python -c "import secrets; print(secrets.token_hex(32))"
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# =============================================================================
# FEATURE FLAGS
# =============================================================================
# AI Generation
ENABLE_SEMANTIC_SIMILARITY=true
SIMILARITY_THRESHOLD=0.85
MAX_CONCURRENT_GENERATIONS=10

# Import (NEW in v2.0)
MAX_IMPORT_BATCH_SIZE=1000
IMPORT_HTML_SANITIZATION=true

# SEO Optimization (NEW in v2.0)
SEO_ANALYSIS_ENABLED=true
SEO_MIN_KEYWORD_DENSITY=1.0
SEO_MAX_KEYWORD_DENSITY=3.5

# Computer Use Publishing (NEW in v2.0)
COMPUTER_USE_ENABLED=true
COMPUTER_USE_MAX_RETRIES=3
COMPUTER_USE_SCREENSHOT_ENABLED=true
COMPUTER_USE_BROWSER_HEADLESS=false  # Set true for production
COMPUTER_USE_TIMEOUT_SECONDS=300  # 5 minutes max per publish task
```

### 3. Install Chrome/Chromium (for Computer Use)

```bash
# macOS
brew install --cask google-chrome

# Ubuntu/Debian
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f

# Verify Chrome installation
google-chrome --version
```

### 4. Start Services with Docker Compose

```bash
# Start database and Redis
docker-compose up -d postgres redis

# Wait for database to be ready
docker-compose exec postgres pg_isready

# Run database migrations (includes Phase 5 fusion schema)
docker-compose run --rm backend poetry run alembic upgrade head

# Start all services
docker-compose up
```

**Services Started:**
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- Celery Worker: Background task processor
- Celery Beat: Scheduler for periodic tasks
- Flower: Task monitoring at http://localhost:5555

### 5. Verify Installation

```bash
# Check API health
curl http://localhost:8000/v1/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "2.0.0",
#   "dependencies": {
#     "database": "healthy",
#     "redis": "healthy",
#     "claude_api": "healthy",
#     "cms_api": "healthy"
#   }
# }

# Verify pgvector extension
docker-compose exec postgres psql -U cms_user -d cms_automation \
  -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Check Celery workers
docker-compose exec backend celery -A src.workers.celery_app inspect active

# Check frontend
open http://localhost:3000

# Verify Chrome for Computer Use
docker-compose exec backend which google-chrome
```

---

## Manual Setup (Local Development)

### 1. Set Up Python Backend

```bash
# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies (includes Phase 5 fusion dependencies)
cd backend
poetry install

# Activate shell
poetry shell
```

**New Phase 5 Dependencies**:
- `bleach` - HTML sanitization for imported articles
- `pandas` - CSV parsing for bulk import
- `anthropic[computer-use]` - Computer Use API support

### 2. Set Up Database

```bash
# Create database
createdb cms_automation

# Enable pgvector extension
psql cms_automation -c "CREATE EXTENSION vector;"

# Run migrations (includes Phase 5 tables: seo_metadata, publish_tasks, execution_logs)
poetry run alembic upgrade head

# Verify Phase 5 tables
psql cms_automation -c "\dt" | grep -E "(seo_metadata|publish_tasks|execution_logs)"
```

### 3. Set Up Redis

```bash
# macOS (Homebrew)
brew install redis
brew services start redis

# Linux (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis

# Verify Redis
redis-cli ping  # Should return PONG
```

### 4. Install Chrome/Chromium

```bash
# macOS
brew install --cask google-chrome

# Ubuntu/Debian
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb

# Verify installation
google-chrome --version
```

### 5. Start Backend Services

**Terminal 1 - API Server:**
```bash
cd backend
poetry run uvicorn src.main:app --reload --port 8000
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
poetry run celery -A src.workers.celery_app worker --loglevel=info --concurrency=4
```

**Terminal 3 - Celery Beat (Scheduler):**
```bash
cd backend
poetry run celery -A src.workers.celery_app beat --loglevel=info
```

**Terminal 4 - Flower (Optional Monitoring):**
```bash
cd backend
poetry run celery -A src.workers.celery_app flower --port=5555
```

### 6. Set Up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

---

## Workflow 1: AI Article Generation Pipeline (Preserved)

This is the original workflow for AI-powered article generation.

### 1.1. Submit Article Topic Request

```bash
# Using curl
curl -X POST http://localhost:8000/v1/topics \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "topic_description": "Write a beginner-friendly guide to setting up PostgreSQL on Ubuntu",
    "style_tone": "conversational",
    "target_word_count": 1500,
    "priority": "normal"
  }'

# Response:
# {
#   "request_id": 1,
#   "status": "pending",
#   "estimated_completion": "2025-10-25T14:35:00Z",
#   "message": "Topic request accepted for processing"
# }
```

### 1.2. Monitor Article Generation

```bash
# Check topic request status
curl http://localhost:8000/v1/topics/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Watch Celery task logs
# (See Terminal 2 for real-time generation progress)

# Check Flower dashboard
open http://localhost:5555
```

### 1.3. Review Generated Article

```bash
# Get article details
curl http://localhost:8000/v1/articles/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Response includes:
# {
#   "id": 1,
#   "title": "PostgreSQL on Ubuntu: A Beginner's Guide",
#   "body": "...",
#   "source": "ai_generated",  # NEW in v2.0
#   "seo_optimized": false,     # NEW in v2.0
#   "status": "draft",
#   "tags": [...],
#   "metadata": {...}
# }
```

### 1.4. Trigger SEO Analysis (NEW in v2.0)

```bash
# Analyze article for SEO optimization
curl -X POST http://localhost:8000/v1/seo/analyze/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "focus_keyword_hint": "PostgreSQL Ubuntu"
  }'

# Response (for articles <2000 words, completes synchronously):
# {
#   "id": 1,
#   "article_id": 1,
#   "seo_title": "PostgreSQL on Ubuntu: Complete Installation Guide 2025",
#   "meta_description": "Learn how to install PostgreSQL on Ubuntu with step-by-step instructions, configuration tips, and troubleshooting. Complete guide for beginners.",
#   "focus_keyword": "PostgreSQL Ubuntu",
#   "primary_keywords": ["PostgreSQL", "Ubuntu installation", "database setup"],
#   "secondary_keywords": ["PostgreSQL configuration", "Ubuntu server", "database management", "SQL", "open source database"],
#   "keyword_density": {
#     "PostgreSQL": 2.3,
#     "Ubuntu": 1.8,
#     "installation": 1.5
#   },
#   "readability_score": 68.5,
#   "optimization_recommendations": [
#     "Increase focus keyword density to 2-3%",
#     "Add more internal links to related articles",
#     "Include images with alt text"
#   ]
# }

# Verify article is now marked as SEO optimized
curl http://localhost:8000/v1/articles/1 | jq '.seo_optimized'
# true
```

### 1.5. Approve and Publish with Computer Use (NEW in v2.0)

```bash
# Approve article
curl -X POST http://localhost:8000/v1/workflows/1/approve \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "Article looks great, approved for publishing"
  }'

# Submit for Computer Use publishing
curl -X POST http://localhost:8000/v1/publish/submit \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 1,
    "cms_type": "wordpress",
    "max_retries": 3
  }'

# Response:
# {
#   "task_id": 1,
#   "article_id": 1,
#   "status": "pending",
#   "estimated_completion": "2025-10-25T14:40:00Z",
#   "message": "Publishing task queued successfully"
# }
```

### 1.6. Monitor Publishing Progress (NEW in v2.0)

```bash
# Check publishing task status
curl http://localhost:8000/v1/publish/tasks/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Response (in-progress):
# {
#   "id": 1,
#   "article_id": 1,
#   "status": "in_progress",
#   "screenshots": [
#     {"step": "login_success", "url": "http://localhost:8000/screenshots/1/login_success.png", "timestamp": "2025-10-25T14:35:10Z"},
#     {"step": "editor_loaded", "url": "http://localhost:8000/screenshots/1/editor_loaded.png", "timestamp": "2025-10-25T14:35:15Z"}
#   ],
#   "created_at": "2025-10-25T14:35:00Z",
#   "started_at": "2025-10-25T14:35:05Z"
# }

# When completed:
# {
#   "id": 1,
#   "status": "completed",
#   "published_url": "https://your-test-site.com/postgresql-ubuntu-guide/",
#   "screenshots": [
#     {"step": "login_success", ...},
#     {"step": "editor_loaded", ...},
#     {"step": "content_filled", ...},
#     {"step": "seo_fields_filled", ...},
#     {"step": "taxonomy_set", ...},
#     {"step": "publish_clicked", ...},
#     {"step": "article_live", ...}
#   ],
#   "duration_seconds": 47.3
# }

# Download all screenshots
curl http://localhost:8000/v1/publish/tasks/1/screenshots \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Workflow 2: Import + SEO + Publishing Pipeline (NEW in v2.0)

This is the new fusion architecture workflow for importing existing articles.

### 2.1. Prepare Import CSV File

Create `articles.csv` with your existing content:

```csv
title,body,author,tags,featured_image_url,excerpt
"Understanding Docker Containers","<p>Docker is a platform for developing...</p>",John Doe,"docker,containers,devops",https://example.com/docker.jpg,"Learn Docker basics"
"Kubernetes Deployment Guide","<p>Kubernetes orchestrates containerized applications...</p>",Jane Smith,"kubernetes,devops,cloud",https://example.com/k8s.jpg,"Deploy apps with K8s"
```

**Required Columns**: `title`, `body`
**Optional Columns**: `author`, `tags` (comma-separated), `metadata` (JSON string), `featured_image_url`, `excerpt`, `publish_date`

### 2.2. Import Articles

```bash
# Import via multipart/form-data (for CSV/JSON files)
curl -X POST http://localhost:8000/v1/articles/import \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@articles.csv" \
  -F "skip_duplicates=true" \
  -F "similarity_threshold=0.85"

# For small batches (<10 articles), response is synchronous:
# {
#   "imported_count": 2,
#   "skipped_count": 0,
#   "failed_count": 0,
#   "article_ids": [10, 11],
#   "validation_errors": [],
#   "duplicates": [],
#   "duration_seconds": 12.5
# }

# For large batches (≥10 articles), response is async:
# {
#   "import_id": "550e8400-e29b-41d4-a716-446655440000",
#   "status": "queued",
#   "total_articles": 100,
#   "estimated_completion": "2025-10-25T14:45:00Z"
# }

# Check async import status
curl http://localhost:8000/v1/articles/import/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2.3. Verify Imported Articles

```bash
# List imported articles
curl "http://localhost:8000/v1/articles?source=imported&page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get specific imported article
curl http://localhost:8000/v1/articles/10 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Response shows:
# {
#   "id": 10,
#   "title": "Understanding Docker Containers",
#   "body": "<p>Docker is a platform for developing...</p>",
#   "source": "imported",        # Marked as imported
#   "seo_optimized": false,      # Not yet optimized
#   "status": "draft"
# }
```

### 2.4. Batch SEO Analysis for Imported Articles

```bash
# Analyze multiple imported articles at once
curl -X POST http://localhost:8000/v1/seo/batch-analyze \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": [10, 11]
  }'

# Response:
# {
#   "batch_id": "660e8400-e29b-41d4-a716-446655440001",
#   "total_articles": 2,
#   "estimated_completion": "2025-10-25T14:38:00Z"
# }

# Individual SEO analysis is also available
curl -X POST http://localhost:8000/v1/seo/analyze/10 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2.5. Review and Update SEO Metadata

```bash
# Get SEO metadata
curl http://localhost:8000/v1/seo/metadata/10 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Manually override SEO fields if needed
curl -X PUT http://localhost:8000/v1/seo/metadata/10 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "seo_title": "Docker Containers Explained: Complete Beginner Guide 2025",
    "meta_description": "Master Docker containers with this comprehensive guide. Learn installation, commands, best practices, and real-world examples for developers.",
    "focus_keyword": "Docker containers",
    "primary_keywords": ["Docker", "containers", "containerization"],
    "secondary_keywords": ["Docker tutorial", "DevOps", "microservices", "Docker commands", "container management"]
  }'

# Manual overrides are tracked with timestamps in the manual_overrides JSONB field
```

### 2.6. Publish Imported Articles with Computer Use

```bash
# Approve imported article
curl -X POST http://localhost:8000/v1/workflows/10/approve \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comment": "Imported article reviewed and approved"}'

# Submit for Computer Use publishing
curl -X POST http://localhost:8000/v1/publish/submit \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 10,
    "cms_type": "wordpress",
    "max_retries": 3
  }'

# Monitor progress (same as Workflow 1.6)
curl http://localhost:8000/v1/publish/tasks/2 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Test Semantic Similarity (Works for Both Workflows)

```bash
# Submit similar topic to test duplicate detection
curl -X POST http://localhost:8000/v1/topics \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "topic_description": "Guide for installing PostgreSQL database on Ubuntu Linux",
    "target_word_count": 1500
  }'

# System should detect similarity to article 1 and alert:
# {
#   "error": {
#     "code": "DUPLICATE_TOPIC_DETECTED",
#     "message": "Similar article already exists",
#     "details": {
#       "similar_articles": [
#         {
#           "id": 1,
#           "title": "PostgreSQL on Ubuntu: A Beginner's Guide",
#           "similarity_score": 0.92,
#           "source": "ai_generated"
#         }
#       ]
#     }
#   }
# }

# Find similar articles for imported content
curl "http://localhost:8000/v1/articles/10/similarity?threshold=0.85&limit=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Development Tools

### API Documentation

- **Swagger UI**: http://localhost:8000/docs (now shows v2.0 endpoints)
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

### Database Tools

```bash
# Connect to database
psql cms_automation

# Useful queries for Phase 5
SELECT id, title, source, seo_optimized, status FROM articles ORDER BY created_at DESC LIMIT 10;
SELECT article_id, seo_title, focus_keyword FROM seo_metadata ORDER BY generated_at DESC LIMIT 10;
SELECT id, article_id, status, published_url FROM publish_tasks ORDER BY created_at DESC LIMIT 10;
SELECT COUNT(*) FROM execution_logs WHERE result = 'failure';

# Check vector similarity index
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'topic_embeddings';

# Check partitioned execution_logs
SELECT schemaname, tablename FROM pg_tables WHERE tablename LIKE 'execution_logs%';
```

### Celery Monitoring

```bash
# List active tasks (includes import, SEO, and publish tasks)
celery -A src.workers.celery_app inspect active

# List scheduled tasks
celery -A src.workers.celery_app inspect scheduled

# Purge all tasks (careful!)
celery -A src.workers.celery_app purge

# Monitor task execution
celery -A src.workers.celery_app events
```

### Computer Use Debugging (NEW in v2.0)

```bash
# Watch Computer Use logs in real-time
tail -f logs/worker.log | jq 'select(.service == "computer_use_publisher")'

# Check screenshot storage
ls -lh storage/screenshots/

# View execution logs for a specific publish task
psql cms_automation -c "SELECT action, target_element, result FROM execution_logs WHERE publish_task_id = 1 ORDER BY timestamp;"

# Test WordPress admin login manually
google-chrome --headless=false $CMS_ADMIN_LOGIN_URL
```

### Logs

```bash
# API logs (structured JSON)
tail -f logs/api.log | jq .

# Worker logs (includes import, SEO, and Computer Use tasks)
tail -f logs/worker.log | jq .

# Filter by log level
tail -f logs/api.log | jq 'select(.level == "ERROR")'

# Watch article generation events
tail -f logs/worker.log | jq 'select(.event == "article_generation_started")'

# Watch import events (NEW in v2.0)
tail -f logs/worker.log | jq 'select(.event == "article_import_started")'

# Watch SEO analysis events (NEW in v2.0)
tail -f logs/worker.log | jq 'select(.event == "seo_analysis_started")'

# Watch Computer Use publishing events (NEW in v2.0)
tail -f logs/worker.log | jq 'select(.event == "publish_task_started")'
```

---

## Common Issues & Troubleshooting

### Issue: "Database connection failed"

**Solution:**
```bash
# Check PostgreSQL is running
pg_isready

# Verify connection string in .env
# Ensure database exists
psql -l | grep cms_automation

# Check pgvector extension
psql cms_automation -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Verify Phase 5 tables exist
psql cms_automation -c "\dt" | grep -E "(seo_metadata|publish_tasks|execution_logs)"
```

### Issue: "Anthropic API error: Invalid API key"

**Solution:**
```bash
# Verify API key format (starts with sk-ant-)
echo $ANTHROPIC_API_KEY

# Test Messages API
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-haiku-20240307","max_tokens":10,"messages":[{"role":"user","content":"test"}]}'

# Test Computer Use API access (NEW in v2.0)
# Computer Use requires beta access - contact Anthropic support if errors occur
```

### Issue: "Celery worker not processing tasks"

**Solution:**
```bash
# Check Redis connection
redis-cli ping

# Restart worker
celery -A src.workers.celery_app worker --loglevel=debug

# Check task queue
redis-cli LLEN celery

# Clear stuck tasks
celery -A src.workers.celery_app purge
```

### Issue: "CMS API connection failed"

**Solution:**
```bash
# Test WordPress REST API manually
curl https://your-test-site.com/wp-json/wp/v2/posts

# Verify Application Password
curl -u admin:xxxx-xxxx-xxxx-xxxx https://your-test-site.com/wp-json/wp/v2/users/me

# Check CORS settings if using remote CMS
```

### Issue: "Computer Use publishing failed" (NEW in v2.0)

**Solution:**
```bash
# Check Chrome installation
google-chrome --version

# Verify WordPress admin credentials
curl -X POST https://your-test-site.com/wp-login.php \
  -d "log=$CMS_ADMIN_USERNAME&pwd=$CMS_ADMIN_PASSWORD"

# Check screenshots for error details
ls -lh storage/screenshots/1/

# Review execution logs
psql cms_automation -c "SELECT * FROM execution_logs WHERE publish_task_id = 1 AND result = 'failure';"

# Retry failed task
curl -X POST http://localhost:8000/v1/publish/tasks/1/retry \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Run Computer Use in non-headless mode for debugging
# Set in .env: COMPUTER_USE_BROWSER_HEADLESS=false
```

### Issue: "Import CSV validation errors"

**Solution:**
```bash
# Check CSV format
head -5 articles.csv

# Ensure required columns exist: title, body
# Validate HTML in body column is well-formed

# Check import response for specific validation errors
curl -X POST http://localhost:8000/v1/articles/import \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@articles.csv" | jq '.validation_errors'

# Common issues:
# - Missing required fields (title, body)
# - Invalid HTML in body
# - Malformed tags field (should be comma-separated)
# - Invalid date format in publish_date
```

### Issue: "SEO analysis timeout"

**Solution:**
```bash
# Check Claude API rate limits
# Large articles (>2000 words) are processed async

# Check article word count
curl http://localhost:8000/v1/articles/1 | jq '.body | split(" ") | length'

# For large articles, poll for completion
curl http://localhost:8000/v1/seo/metadata/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Check Celery worker logs for SEO tasks
tail -f logs/worker.log | jq 'select(.task == "seo_analyze_article")'
```

### Issue: "Screenshot storage S3 upload failed" (NEW in v2.0)

**Solution:**
```bash
# Verify S3 credentials
aws s3 ls s3://$S3_BUCKET_NAME --profile cms-automation

# Check S3 configuration in .env
echo $SCREENSHOT_STORAGE_TYPE
echo $S3_BUCKET_NAME
echo $S3_REGION

# Fall back to local storage temporarily
# Update .env: SCREENSHOT_STORAGE_TYPE=local

# Verify local storage directory exists and is writable
mkdir -p storage/screenshots
chmod 755 storage/screenshots
```

### Issue: "Frontend not connecting to backend"

**Solution:**
```bash
# Check ALLOWED_ORIGINS in .env
ALLOWED_ORIGINS=http://localhost:3000

# Verify API is accessible
curl http://localhost:8000/v1/health

# Check browser console for CORS errors
# If CORS error, add frontend origin to backend config
```

---

## Running Tests

### Backend Tests

```bash
# Run all tests (includes Phase 5 fusion tests)
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/

# Run Phase 5 specific tests (NEW in v2.0)
pytest tests/unit/test_article_importer.py
pytest tests/unit/test_seo_analyzer.py
pytest tests/unit/test_computer_use_publisher.py

# Run E2E fusion workflow tests (NEW in v2.0)
pytest tests/e2e/test_fusion_ai_workflow.py
pytest tests/e2e/test_fusion_import_workflow.py
pytest tests/e2e/test_fusion_concurrent_workflow.py

# Run single test file
pytest tests/unit/test_article_generator.py

# Run with verbose output
pytest -v -s
```

### Frontend Tests

```bash
cd frontend

# Unit tests
npm run test

# E2E tests (requires backend running)
npm run test:e2e

# Coverage report
npm run test:coverage
```

### E2E Fusion Workflow Tests (NEW in v2.0)

```bash
# Test complete AI generation → SEO → Publishing workflow
pytest tests/e2e/test_fusion_ai_workflow.py -v

# Test complete Import → SEO → Publishing workflow
pytest tests/e2e/test_fusion_import_workflow.py -v

# Test concurrent publishing (3+ simultaneous tasks)
pytest tests/e2e/test_fusion_concurrent_workflow.py -v

# Expected output:
# ✅ E2E Test 1: AI Generation → SEO → Publishing PASSED
# ✅ E2E Test 2: Import → SEO → Publishing PASSED
# ✅ E2E Test 3: Concurrent Publishing (3 tasks) PASSED
```

---

## Next Steps

### For Backend Development

1. **Review Fusion Architecture**: Read `specs/001-cms-automation/plan.md` (Phase 5 section)
2. **Study Data Model**: Review `specs/001-cms-automation/data-model.md` (new tables)
3. **Study API Contracts**: Review `specs/001-cms-automation/contracts/api-spec.yaml` (v2.0)
4. **Understand Workflows**: Read feature specification user stories (v2.0)
5. **Explore Code**:
   - AI Generation: `backend/src/services/article_generator/`
   - Article Import: `backend/src/services/article_importer/` (NEW)
   - SEO Analysis: `backend/src/services/seo_analyzer/` (NEW)
   - Computer Use Publishing: `backend/src/services/computer_use_publisher/` (NEW)

### For Frontend Development

1. **Component Documentation**: Check `frontend/src/components/README.md`
2. **State Management**: Review React Query setup in `frontend/src/services/`
3. **Design System**: Explore Tailwind configuration and theme
4. **API Integration**: Study `frontend/src/services/api-client.ts` (updated for v2.0)
5. **New Features**:
   - Article import UI components
   - SEO metadata editor
   - Publishing task monitor with screenshot viewer

### For Testing

1. **Write Tests First**: Follow TDD workflow (Constitution mandates)
2. **Mock External APIs**: Use VCR.py for HTTP mocking
3. **Contract Tests**: Ensure API matches OpenAPI spec (v2.0)
4. **Load Testing**: Use Locust for performance validation
5. **Computer Use Testing**: Test browser automation in isolated environment

---

## Useful Commands Reference

```bash
# Development
make dev              # Start all services
make logs             # Tail all logs
make shell            # Open Python shell with app context
make db-shell         # Open database shell

# Database
make db-migrate       # Create new migration
make db-upgrade       # Run migrations (includes Phase 5)
make db-downgrade     # Rollback migration
make db-reset         # Drop and recreate database (destructive!)

# Testing
make test             # Run all tests (includes fusion tests)
make test-unit        # Unit tests only
make test-integration # Integration tests only
make test-e2e         # E2E fusion workflow tests (NEW)
make test-coverage    # Generate coverage report

# Code Quality
make lint             # Run linters (ruff, mypy)
make format           # Format code (black, isort)
make type-check       # Type checking with mypy
make security-check   # Security audit (bandit, safety)

# Deployment
make build            # Build Docker images
make deploy-staging   # Deploy to staging
make deploy-prod      # Deploy to production

# Phase 5 Specific (NEW)
make import-sample    # Import sample CSV articles
make test-seo         # Test SEO analysis on sample articles
make test-publish     # Test Computer Use publishing (requires WordPress)
make clean-screenshots # Clean up old screenshots
```

---

## Performance Benchmarks (v2.0)

Based on E2E test results:

| Metric | Target (SLA) | Actual | Status |
|--------|--------------|--------|--------|
| AI Article Generation | < 5 min (300s) | ~25s | ✅ 91.7% faster |
| SEO Analysis (1500 words) | < 30s | ~18s | ✅ 40% faster |
| Article Import (100 articles) | < 5 min | ~4m 15s | ✅ 15% faster |
| Computer Use Publishing | < 5 min | ~47s | ✅ 84% faster |
| Concurrent Publishing (3 tasks) | < 5 min each | ~52s avg | ✅ 82.7% faster |

**System Capacity**:
- Concurrent article generation: 50+ simultaneous
- Concurrent SEO analysis: 100+ simultaneous
- Concurrent publishing: 10+ simultaneous (limited by Computer Use API)

---

## Getting Help

- **Documentation**: `docs/` directory
- **API Reference**: http://localhost:8000/docs (v2.0 with fusion endpoints)
- **Architecture Diagrams**: `specs/001-cms-automation/diagrams/`
- **Troubleshooting**: `docs/troubleshooting.md`
- **Team Chat**: Slack #cms-automation channel

**Version-Specific Resources**:
- **v1.0 (AI Generation Only)**: `specs/001-cms-automation/README.md`
- **v2.0 (Fusion Architecture)**: `specs/001-cms-automation/plan.md` (Phase 5 section)

---

## License

MIT License - See LICENSE file for details
