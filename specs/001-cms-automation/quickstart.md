# Quickstart Guide: CMS Automation Platform

**Feature**: 001-cms-automation
**Version**: 1.0.0
**Last Updated**: 2025-10-26
**Target Audience**: Developers new to the project

## Overview

This guide helps you set up a local development environment for the **CMS automation platform with multi-provider Computer Use**. The system enables importing existing articles, optimizing them for SEO using Claude Messages API, and publishing to WordPress using flexible providers.

**Core Workflow**:
1. **Import** articles from CSV/JSON or manual entry
2. **Proofread & Optimize** via单一 Prompt（Claude Messages API）+ Deterministic Rule Engine 合并
3. **Publish** to WordPress using Computer Use (choose provider: Anthropic/Gemini/Playwright)

**Provider Options**:
- **Playwright** (default): Free, fast (30-60s), 99%+ reliability
- **Anthropic**: AI-driven ($1-1.50), slow (2-4 min), adaptive to UI changes
- **Gemini**: Future Google provider (not yet available)

**Estimated Setup Time**: 30-45 minutes

---

## Prerequisites

### Required Software

- **Python**: 3.13 or higher
- **PostgreSQL**: 15.0 or higher
- **Redis**: 7.0 or higher
- **Node.js**: 18 LTS or higher (for frontend)
- **Docker & Docker Compose**: Latest stable (recommended)
- **Chrome/Chromium**: Latest stable (for Playwright/Anthropic Computer Use)

### Required Accounts

- **Anthropic API Key** (optional for AI provider): Sign up at https://console.anthropic.com/
  - Required only if using Anthropic provider for SEO analysis or publishing
  - Claude Messages API for SEO optimization
  - Computer Use API for AI-driven publishing (optional)

- **Test WordPress Instance**:
  - WordPress 6.4+ (Gutenberg editor)
  - SEO plugin installed (Yoast SEO or Rank Math recommended)
  - Admin credentials for Computer Use automation

### System Requirements

- **RAM**: Minimum 8 GB (16 GB recommended for AI providers)
- **Disk**: 5 GB free space
- **OS**: macOS, Linux, or Windows WSL2
- **Network**: Stable connection for browser automation

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
# API KEYS (Optional - only if using Anthropic provider)
# =============================================================================
ANTHROPIC_API_KEY=sk-ant-...  # Required for SEO analysis and Anthropic Computer Use

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
CMS_ADMIN_USERNAME=admin
CMS_ADMIN_PASSWORD=your-admin-password  # For Computer Use automation

# =============================================================================
# COMPUTER USE PROVIDER SELECTION
# =============================================================================
# Default provider for publishing (playwright, anthropic, gemini)
COMPUTER_USE_PROVIDER=playwright  # Free, fast, reliable default

# Playwright Configuration (Default)
PLAYWRIGHT_HEADLESS=true  # Set false for debugging
PLAYWRIGHT_TIMEOUT=60000  # 60 seconds

# Anthropic Computer Use Configuration (Optional AI provider)
ANTHROPIC_COMPUTER_USE_ENABLED=false  # Set true to use Anthropic
ANTHROPIC_COMPUTER_USE_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_COST_PER_ARTICLE=1.50  # Cost limit per article

# Gemini Computer Use Configuration (Future)
GEMINI_COMPUTER_USE_ENABLED=false  # Not yet available

# =============================================================================
# SEO OPTIMIZATION
# =============================================================================
SEO_ANALYSIS_ENABLED=true
SEO_ANALYSIS_MODEL=claude-3-5-haiku-20241022  # Cheap model for SEO
SEO_TARGET_TITLE_LENGTH_MIN=50
SEO_TARGET_TITLE_LENGTH_MAX=60
SEO_TARGET_DESC_LENGTH_MIN=150
SEO_TARGET_DESC_LENGTH_MAX=160
SEO_MIN_READABILITY_SCORE=60.0  # Flesch Reading Ease

# =============================================================================
# SCREENSHOT STORAGE
# =============================================================================
SCREENSHOT_STORAGE_TYPE=local  # or 's3'
SCREENSHOT_STORAGE_PATH=/app/storage/screenshots

# For S3 storage (optional):
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
MAX_IMPORT_BATCH_SIZE=1000
IMPORT_HTML_SANITIZATION=true
COMPUTER_USE_MAX_RETRIES=3
COMPUTER_USE_SCREENSHOT_ENABLED=true
```

### 3. Install Chrome/Chromium (for Computer Use)

```bash
# macOS
brew install --cask google-chrome

# Ubuntu/Debian
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f

# Verify installation
google-chrome --version
# Google Chrome 119.0.6045.105
```

### 4. Start Services with Docker Compose

```bash
# Start database and Redis
docker-compose up -d postgres redis

# Wait for database to be ready
docker-compose exec postgres pg_isready

# Run database migrations
docker-compose run --rm backend poetry run alembic upgrade head

# Start all services
docker-compose up
```

**Services Started:**
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- Celery Worker: Background task processor
- Flower: Task monitoring at http://localhost:5555

### 5. Verify Installation

```bash
# Check API health
curl http://localhost:8000/v1/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "checks": {
#     "database": "ok",
#     "redis": "ok"
#   }
# }

# Check Celery workers
docker-compose exec backend celery -A src.workers.celery_app inspect active

# Open frontend
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

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
cd backend
poetry install

# Activate shell
poetry shell
```

**Key Dependencies**:
- `fastapi` - API framework
- `sqlalchemy[asyncio]` - Async ORM
- `anthropic` - Claude API SDK
- `playwright` - Browser automation (default provider)
- `celery` - Task queue
- `bleach` - HTML sanitization

### 2. Set Up Database

```bash
# Create database
createdb cms_automation

# Run migrations
poetry run alembic upgrade head

# Verify tables
psql cms_automation -c "\dt"
# articles, seo_metadata, publish_tasks, execution_logs
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

# Verify
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

**Terminal 3 - Flower (Optional Monitoring):**
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

## Core Workflow: Import → Proofread & SEO → Publish

### Step 1: Import Articles

**1.1. Prepare CSV File**

Create `articles.csv` with your existing content:

```csv
title,body,source,featured_image_url
"Docker Complete Guide","<h2>Introduction</h2><p>Docker is a platform...</p>",wordpress_export,https://example.com/docker.jpg
"Kubernetes Basics","<h2>What is Kubernetes?</h2><p>Kubernetes orchestrates...</p>",manual,https://example.com/k8s.jpg
```

**Required Columns**: `title`, `body`
**Optional Columns**: `source`, `featured_image_url`, `additional_images`, `metadata`

**1.2. Import via API**

```bash
# Single article import
curl -X POST http://localhost:8000/v1/articles/import \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Docker Complete Guide",
    "body": "<h2>Introduction</h2><p>Docker is...</p>",
    "source": "wordpress_export",
    "featured_image_url": "https://example.com/docker.jpg"
  }'

# Response:
# {
#   "id": 1,
#   "title": "Docker Complete Guide",
#   "source": "wordpress_export",
#   "status": "imported",
#   "created_at": "2025-10-26T14:30:00Z"
# }

# Batch import from CSV
curl -X POST http://localhost:8000/v1/articles/import/batch \
  -F "file=@articles.csv" \
  -F "format=csv"

# Response:
# {
#   "job_id": "batch_import_20251026_143000",
#   "status": "processing",
#   "total_rows": 50,
#   "estimated_completion": "2025-10-26T14:45:00Z"
# }
```

### Step 2: Proofreading + SEO (Single Prompt + Scripts)

**2.1. Run ProofreadingAnalysisService**

```bash
curl -X POST http://localhost:8000/v1/articles/1/proofread \
  -H "Authorization: Bearer $TOKEN"

# Response (truncated):
# {
#   "article_id": 1,
#   "issues": [
#     {"rule_id": "B2-002", "message": "中文段落使用半角逗号", "severity": "warning", "source": "script"},
#     {"rule_id": "F1-002", "message": "特色图片宽高比不足", "severity": "critical", "blocks_publish": true, "source": "script"},
#     {"rule_id": "A4-014", "message": "出现网络流行语“土豪”", "severity": "warning", "source": "ai", "confidence": 0.68}
#   ],
#   "statistics": {
#     "total_issues": 5,
#     "blocking_issue_count": 1,
#     "source_breakdown": {"script": 2, "ai": 2, "merged": 1}
#   },
#   "suggested_content": "<h2>Docker 简介...</h2>",
#   "seo_metadata": {
#     "meta_title": "Docker 完整指南：安装、部署与最佳实践 2025",
#     "meta_description": "掌握最新 Docker 技巧，从安装、命令到生产部署完整解析。立即开始容器化应用！",
#     "focus_keyword": "Docker 指南",
#     "keywords": ["Docker 教學", "Docker 指令", "容器部署"]
#   },
#   "processing_metadata": {
#     "ai_model": "claude-3-5-sonnet-20241022",
#     "prompt_hash": "c13c8e5...",
#     "rule_manifest_version": "2025.02.05",
#     "script_engine_version": "0.1.0"
#   }
# }
```

**2.2. Manual SEO Override (Optional)**

```bash
curl -X PUT http://localhost:8000/v1/seo/metadata/1 \
  -H "Content-Type: application/json" \
  -d '{
    "meta_title": "Docker Guide 2025: Complete Beginner to Advanced Tutorial",
    "meta_description": "Learn Docker from scratch with hands-on examples. Installation, commands, best practices & production deployment. Perfect for beginners!",
    "focus_keyword": "Docker tutorial"
  }'
```

### Step 3: Publish to WordPress

**3.1. Choose Provider and Submit**

```bash
# Option 1: Use Playwright (default, free, fast)
curl -X POST http://localhost:8000/v1/publish/submit \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 1,
    "provider": "playwright",
    "cms_type": "wordpress",
    "cms_config": {
      "url": "https://your-site.com/wp-admin",
      "username": "admin",
      "password": "your-password"
    },
    "post_config": {
      "categories": ["DevOps", "Tutorials"],
      "tags": ["docker", "containers"],
      "post_status": "publish"
    }
  }'

# Option 2: Use Anthropic Computer Use (AI-driven, adaptive)
curl -X POST http://localhost:8000/v1/publish/submit \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 1,
    "provider": "anthropic",
    "cms_type": "wordpress",
    "cms_config": {
      "url": "https://your-site.com/wp-admin",
      "username": "admin",
      "password": "your-password"
    }
  }'

# Response:
# {
#   "id": 1,
#   "task_id": "pub_20251026_143500_abc123",
#   "article_id": 1,
#   "provider": "playwright",
#   "status": "pending",
#   "estimated_completion": "2025-10-26T14:36:00Z"
# }
```

**3.2. Monitor Publishing Progress**

```bash
# Poll task status
curl http://localhost:8000/v1/publish/tasks/pub_20251026_143500_abc123

# Response (running):
# {
#   "id": 1,
#   "task_id": "pub_20251026_143500_abc123",
#   "article_id": 1,
#   "provider": "playwright",
#   "status": "running",
#   "screenshots": [
#     {
#       "step": "01_login_success",
#       "url": "http://localhost:8000/screenshots/1/01_login_success.png",
#       "timestamp": "2025-10-26T14:35:10Z",
#       "description": "WordPress admin login successful"
#     },
#     {
#       "step": "02_new_post_page",
#       "url": "http://localhost:8000/screenshots/1/02_new_post.png",
#       "timestamp": "2025-10-26T14:35:15Z"
#     }
#   ],
#   "started_at": "2025-10-26T14:35:05Z"
# }

# Response (completed):
# {
#   "id": 1,
#   "task_id": "pub_20251026_143500_abc123",
#   "status": "completed",
#   "published_url": "https://your-site.com/docker-complete-guide/",
#   "cost_usd": 0.0,  # Free for Playwright
#   "duration_seconds": 45,
#   "screenshots": [
#     {"step": "01_login_success", ...},
#     {"step": "02_new_post_page", ...},
#     {"step": "03_title_filled", ...},
#     {"step": "04_content_filled", ...},
#     {"step": "05_seo_fields_filled", ...},
#     {"step": "06_taxonomy_set", ...},
#     {"step": "07_publish_clicked", ...},
#     {"step": "08_article_live", ...}
#   ],
#   "completed_at": "2025-10-26T14:35:50Z"
# }
```

**3.3. View Screenshots**

```bash
# Get all screenshots for task
curl http://localhost:8000/v1/publish/tasks/pub_20251026_143500_abc123/screenshots

# Download specific screenshot
curl -O http://localhost:8000/screenshots/1/05_seo_fields_filled.png
```

**3.4. View Execution Logs**

```bash
# Get detailed execution logs
curl http://localhost:8000/v1/publish/tasks/pub_20251026_143500_abc123/logs

# Response:
# {
#   "task_id": "pub_20251026_143500_abc123",
#   "logs": [
#     {
#       "id": 1,
#       "log_level": "INFO",
#       "step_name": "login",
#       "message": "Navigating to WordPress login page",
#       "action_type": "navigate",
#       "action_target": "https://your-site.com/wp-login.php",
#       "action_result": "success",
#       "created_at": "2025-10-26T14:35:05Z"
#     },
#     {
#       "id": 2,
#       "log_level": "INFO",
#       "step_name": "login",
#       "message": "Entering username",
#       "action_type": "type",
#       "action_target": "#user_login",
#       "action_result": "success",
#       "created_at": "2025-10-26T14:35:07Z"
#     }
#   ]
# }
```

---

## Provider Selection Guide

### When to Use Playwright (Default)

**Best For:**
- Standard WordPress installations
- Bulk publishing (100+ articles)
- Cost-sensitive projects
- Fast turnaround required

**Pros:**
- **Free**: No API costs
- **Fast**: 30-60 seconds per article
- **Reliable**: 99%+ success rate
- **Predictable**: Deterministic behavior

**Cons:**
- **Brittle**: Breaks if WordPress UI changes significantly
- **Limited**: Cannot adapt to custom themes without code changes

**Example:**
```bash
curl -X POST http://localhost:8000/v1/publish/submit \
  -d '{"article_id": 1, "provider": "playwright"}'
```

### When to Use Anthropic Computer Use

**Best For:**
- Custom WordPress themes
- Non-standard editor configurations
- Dynamic UI elements
- Complex multi-step workflows

**Pros:**
- **Adaptive**: AI reasoning handles UI changes
- **Flexible**: Works with custom themes
- **Visual**: Natural language instructions

**Cons:**
- **Expensive**: $1.00-$1.50 per article
- **Slow**: 2-4 minutes per article
- **Variable**: 95-98% success rate

**Example:**
```bash
curl -X POST http://localhost:8000/v1/publish/submit \
  -d '{"article_id": 1, "provider": "anthropic"}'
```

### Cost Comparison (500 articles/month)

| Provider | Cost/Article | Total Cost | Time/Article | Total Time |
|----------|--------------|------------|--------------|------------|
| **Playwright** | $0.00 | **$0.00** | 45s | 6.25 hours |
| **Anthropic** | $1.15 | **$575.00** | 3 min | 25 hours |

**Recommendation**: Start with Playwright. Upgrade to Anthropic only when:
- Publishing fails repeatedly due to UI changes
- Custom theme requires AI reasoning
- Budget allows for AI automation

---

## Development Tools

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

### Database Tools

```bash
# Connect to database
psql cms_automation

# Useful queries
SELECT id, title, source, status FROM articles ORDER BY created_at DESC LIMIT 10;

SELECT article_id, meta_title, focus_keyword FROM seo_metadata ORDER BY created_at DESC LIMIT 10;

SELECT id, article_id, provider, status, cost_usd, duration_seconds
FROM publish_tasks ORDER BY created_at DESC LIMIT 10;

# Execution logs for failed tasks
SELECT task_id, step_name, message, action_result
FROM execution_logs
WHERE action_result = 'failed'
ORDER BY created_at DESC LIMIT 20;
```

### Celery Monitoring

```bash
# List active tasks
celery -A src.workers.celery_app inspect active

# List scheduled tasks
celery -A src.workers.celery_app inspect scheduled

# Open Flower dashboard
open http://localhost:5555
```

### Logs

```bash
# API logs (structured JSON)
tail -f logs/api.log | jq .

# Worker logs
tail -f logs/worker.log | jq .

# Filter by log level
tail -f logs/api.log | jq 'select(.level == "ERROR")'

# Watch import events
tail -f logs/worker.log | jq 'select(.event == "article_import_started")'

# Watch SEO analysis events
tail -f logs/worker.log | jq 'select(.event == "seo_analysis_started")'

# Watch publishing events
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
echo $DATABASE_URL

# Ensure database exists
psql -l | grep cms_automation

# Verify tables exist
psql cms_automation -c "\dt"
```

### Issue: "Redis connection failed"

**Solution:**
```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Verify Redis URL in .env
echo $REDIS_URL

# Check Celery can connect
celery -A src.workers.celery_app inspect ping
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
  -d '{"model":"claude-3-5-haiku-20241022","max_tokens":10,"messages":[{"role":"user","content":"test"}]}'

# Expected: {"id":"msg_...", "type":"message", ...}
```

### Issue: "Publishing failed with Playwright"

**Solution:**
```bash
# Check Chrome installation
google-chrome --version

# Verify WordPress admin credentials
curl -I https://your-site.com/wp-login.php

# Check screenshots for error details
ls -lh storage/screenshots/1/

# Review execution logs
psql cms_automation -c "
  SELECT step_name, message, action_result
  FROM execution_logs
  WHERE task_id = 1
  ORDER BY created_at;
"

# Retry failed task
curl -X POST http://localhost:8000/v1/publish/tasks/1/retry

# Run in non-headless mode for debugging
# Set in .env: PLAYWRIGHT_HEADLESS=false
```

### Issue: "SEO analysis timeout"

**Solution:**
```bash
# Check Claude API rate limits
# Large articles (>3000 words) may take longer

# Check article word count
curl http://localhost:8000/v1/articles/1 | jq '.body | split(" ") | length'

# Check Celery worker logs for SEO tasks
tail -f logs/worker.log | jq 'select(.task == "seo_analyze_article")'

# Reduce article size if too large (>5000 words)
```

### Issue: "Import CSV validation errors"

**Solution:**
```bash
# Check CSV format
head -5 articles.csv

# Ensure required columns: title, body
# Validate HTML is well-formed

# Check specific validation errors
curl -X POST http://localhost:8000/v1/articles/import/batch \
  -F "file=@articles.csv" | jq '.errors'

# Common issues:
# - Missing title or body
# - Invalid HTML in body
# - Malformed metadata JSON
```

### Issue: "Screenshot storage S3 upload failed"

**Solution:**
```bash
# Verify S3 credentials
aws s3 ls s3://$S3_BUCKET_NAME

# Check S3 configuration in .env
echo $SCREENSHOT_STORAGE_TYPE
echo $S3_BUCKET_NAME

# Fall back to local storage temporarily
# Update .env: SCREENSHOT_STORAGE_TYPE=local

# Verify local storage directory
mkdir -p storage/screenshots
chmod 755 storage/screenshots
```

---

## Running Tests

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test files
pytest tests/unit/test_import.py
pytest tests/unit/test_seo_analyzer.py
pytest tests/unit/test_providers.py

# Run integration tests
pytest tests/integration/

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

---

## Next Steps

### For Backend Development

1. **Review Architecture**: Read `specs/001-cms-automation/plan.md`
2. **Study Data Model**: Review `specs/001-cms-automation/data-model.md`
3. **Study API Spec**: Review `specs/001-cms-automation/api-spec.yaml`
4. **Explore Code**:
   - Article Import: `backend/src/services/article_importer/`
   - SEO Analysis: `backend/src/services/seo_analyzer/`
   - Providers: `backend/src/services/providers/`

### For Frontend Development

1. **Component Documentation**: Check `frontend/src/components/README.md`
2. **State Management**: Review React Query setup
3. **API Integration**: Study `frontend/src/services/api-client.ts`
4. **Key Features**:
   - Article import UI
   - SEO metadata editor
   - Publishing task monitor with screenshots

### For Testing

1. **Write Tests First**: Follow TDD workflow
2. **Mock External APIs**: Use pytest fixtures
3. **Provider Testing**: Test Playwright and Anthropic providers separately
4. **Contract Tests**: Ensure API matches OpenAPI spec

---

## Useful Commands Reference

```bash
# Development
make dev              # Start all services
make logs             # Tail all logs
make shell            # Open Python shell
make db-shell         # Open database shell

# Database
make db-migrate       # Create new migration
make db-upgrade       # Run migrations
make db-downgrade     # Rollback migration
make db-reset         # Drop and recreate database

# Testing
make test             # Run all tests
make test-unit        # Unit tests only
make test-integration # Integration tests
make test-coverage    # Generate coverage report

# Code Quality
make lint             # Run linters (ruff, mypy)
make format           # Format code (black, isort)
make type-check       # Type checking
make security-check   # Security audit

# Deployment
make build            # Build Docker images
make deploy-staging   # Deploy to staging
make deploy-prod      # Deploy to production
```

---

## Performance Benchmarks

Based on test results (500 articles):

| Metric | Playwright | Anthropic |
|--------|-----------|-----------|
| Import (100 articles) | 2 min | 2 min |
| SEO Analysis (per article) | 8s | 8s |
| Publishing (per article) | 45s | 3 min |
| Cost (500 articles) | $15 (SEO only) | $590 (SEO + publishing) |
| Total Time (500 articles) | 8 hours | 30 hours |

**System Capacity**:
- Concurrent imports: 10 parallel workers
- Concurrent SEO analysis: 20 parallel tasks
- Concurrent publishing (Playwright): 20 parallel tasks
- Concurrent publishing (Anthropic): 10 parallel tasks (API limit)

---

## Getting Help

- **Documentation**: `docs/` directory
- **API Reference**: http://localhost:8000/docs
- **Architecture Diagrams**: `specs/001-cms-automation/diagrams/`
- **Troubleshooting**: `docs/troubleshooting.md`

---

## License

MIT License - See LICENSE file for details
