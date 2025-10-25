# Quickstart Guide: CMS Automation Platform

**Feature**: 001-cms-automation
**Last Updated**: 2025-10-25
**Target Audience**: Developers new to the project

## Overview

This guide helps you set up a local development environment for the AI-powered CMS automation platform. You'll learn how to:

- Set up backend services (API + workers)
- Configure Claude API integration
- Connect to a test CMS instance
- Run the development stack
- Test core workflows (article generation, tagging, scheduling)

**Estimated Setup Time**: 30-45 minutes

---

## Prerequisites

### Required Software

- **Python**: 3.11 or higher
- **PostgreSQL**: 15.0 or higher
- **Redis**: 7.0 or higher
- **Node.js**: 18 LTS or higher (for frontend)
- **Docker & Docker Compose**: Latest stable (recommended for dependencies)

### Required Accounts

- **Anthropic API Key**: Sign up at https://console.anthropic.com/
- **Test CMS Instance**: WordPress site with REST API enabled (or local test instance)

### System Requirements

- **RAM**: Minimum 8 GB (16 GB recommended)
- **Disk**: 5 GB free space
- **OS**: macOS, Linux, or Windows WSL2

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
# API Keys
ANTHROPIC_API_KEY=sk-ant-...  # Your Claude API key

# Database
DATABASE_URL=postgresql://cms_user:cms_pass@localhost:5432/cms_automation
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://localhost:6379/0

# CMS Integration (WordPress example)
CMS_TYPE=wordpress
CMS_BASE_URL=https://your-test-site.com
CMS_USERNAME=admin
CMS_APPLICATION_PASSWORD=xxxx xxxx xxxx xxxx

# Application
API_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development

# Security
SECRET_KEY=<generate-random-string>  # python -c "import secrets; print(secrets.token_hex(32))"
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Feature Flags
ENABLE_SEMANTIC_SIMILARITY=true
SIMILARITY_THRESHOLD=0.85
MAX_CONCURRENT_GENERATIONS=10
```

### 3. Start Services with Docker Compose

```bash
# Start database and Redis
docker-compose up -d postgres redis

# Wait for database to be ready
docker-compose exec postgres pg_isready

# Run database migrations
docker-compose run --rm backend python -m alembic upgrade head

# Start all services
docker-compose up
```

**Services Started:**
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- Celery Worker: Background task processor
- Celery Beat: Scheduler for periodic tasks
- Flower: Task monitoring at http://localhost:5555

### 4. Verify Installation

```bash
# Check API health
curl http://localhost:8000/v1/health

# Expected response:
# {
#   "status": "healthy",
#   "dependencies": {
#     "database": "healthy",
#     "redis": "healthy",
#     "claude_api": "healthy",
#     "cms_api": "healthy"
#   }
# }

# Check Celery workers
docker-compose exec backend celery -A app.workers inspect active

# Check frontend
open http://localhost:3000
```

---

## Manual Setup (Local Development)

### 1. Set Up Python Backend

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"  # Installs with dev dependencies

# Alternative with Poetry
poetry install
poetry shell
```

### 2. Set Up Database

```bash
# Create database
createdb cms_automation

# Enable pgvector extension
psql cms_automation -c "CREATE EXTENSION vector;"

# Run migrations
alembic upgrade head

# Verify tables
psql cms_automation -c "\dt"
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

### 4. Start Backend Services

**Terminal 1 - API Server:**
```bash
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Celery Worker:**
```bash
celery -A app.workers worker --loglevel=info --concurrency=4
```

**Terminal 3 - Celery Beat (Scheduler):**
```bash
celery -A app.workers beat --loglevel=info
```

**Terminal 4 - Flower (Optional Monitoring):**
```bash
celery -A app.workers flower --port=5555
```

### 5. Set Up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

---

## Testing Core Workflows

### 1. Submit Article Topic Request

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

### 2. Monitor Article Generation

```bash
# Check topic request status
curl http://localhost:8000/v1/topics/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Watch Celery task logs
# (See Terminal 2 for real-time generation progress)

# Check Flower dashboard
open http://localhost:5555
```

### 3. Review Generated Article

```bash
# Get article details
curl http://localhost:8000/v1/articles/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Response includes:
# - Generated title and body
# - Automatically assigned tags
# - Workflow state (in-review)
# - Metadata
```

### 4. Approve and Schedule Article

```bash
# Approve article
curl -X POST http://localhost:8000/v1/workflows/1/approve \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "Article looks great, approved for publishing"
  }'

# Schedule publication for 1 hour from now
curl -X POST http://localhost:8000/v1/schedules \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 1,
    "scheduled_time": "2025-10-25T15:30:00Z"
  }'
```

### 5. Test Semantic Similarity

```bash
# Submit similar topic to test duplicate detection
curl -X POST http://localhost:8000/v1/topics \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "topic_description": "Guide for installing PostgreSQL database on Ubuntu Linux",
    "target_word_count": 1500
  }'

# System should detect similarity and alert:
# {
#   "error": {
#     "code": "DUPLICATE_TOPIC_DETECTED",
#     "message": "Similar article already exists",
#     "details": {
#       "similar_articles": [
#         {
#           "id": 1,
#           "title": "...",
#           "similarity_score": 0.92
#         }
#       ]
#     }
#   }
# }
```

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
SELECT id, title, status FROM articles ORDER BY created_at DESC LIMIT 10;
SELECT name, usage_count FROM tags ORDER BY usage_count DESC LIMIT 20;
SELECT * FROM schedules WHERE status = 'pending' ORDER BY scheduled_time;

# Check vector similarity index
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'topic_embeddings';
```

### Celery Monitoring

```bash
# List active tasks
celery -A app.workers inspect active

# List scheduled tasks
celery -A app.workers inspect scheduled

# Purge all tasks (careful!)
celery -A app.workers purge

# Monitor task execution
celery -A app.workers events
```

### Logs

```bash
# API logs (structured JSON)
tail -f logs/api.log | jq .

# Worker logs
tail -f logs/worker.log | jq .

# Filter by log level
tail -f logs/api.log | jq 'select(.level == "ERROR")'

# Watch article generation events
tail -f logs/worker.log | jq 'select(.event == "article_generation_started")'
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
```

### Issue: "Anthropic API error: Invalid API key"

**Solution:**
```bash
# Verify API key format (starts with sk-ant-)
echo $ANTHROPIC_API_KEY

# Test API key directly
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-haiku-20240307","max_tokens":10,"messages":[{"role":"user","content":"test"}]}'
```

### Issue: "Celery worker not processing tasks"

**Solution:**
```bash
# Check Redis connection
redis-cli ping

# Restart worker
celery -A app.workers worker --loglevel=debug

# Check task queue
redis-cli LLEN celery

# Clear stuck tasks
celery -A app.workers purge
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
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/

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

---

## Next Steps

### For Backend Development

1. **Review Architecture**: Read `specs/001-cms-automation/data-model.md`
2. **Study API Contracts**: Review `specs/001-cms-automation/contracts/api-spec.yaml`
3. **Understand Workflows**: Read feature specification user stories
4. **Explore Code**: Start with `backend/src/services/article_generator/`

### For Frontend Development

1. **Component Documentation**: Check `frontend/src/components/README.md`
2. **State Management**: Review React Query setup in `frontend/src/services/`
3. **Design System**: Explore Tailwind configuration and theme
4. **API Integration**: Study `frontend/src/services/api-client.ts`

### For Testing

1. **Write Tests First**: Follow TDD workflow (if constitution mandates)
2. **Mock External APIs**: Use VCR.py for HTTP mocking
3. **Contract Tests**: Ensure API matches OpenAPI spec
4. **Load Testing**: Use Locust for performance validation

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
make db-upgrade       # Run migrations
make db-downgrade     # Rollback migration
make db-reset         # Drop and recreate database (destructive!)

# Testing
make test             # Run all tests
make test-unit        # Unit tests only
make test-integration # Integration tests only
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
```

---

## Getting Help

- **Documentation**: `docs/` directory
- **API Reference**: http://localhost:8000/docs
- **Architecture Diagrams**: `specs/001-cms-automation/diagrams/`
- **Troubleshooting**: `docs/troubleshooting.md`
- **Team Chat**: Slack #cms-automation channel

---

## License

MIT License - See LICENSE file for details
