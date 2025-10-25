# AI-Powered CMS Automation

Automate content management workflows using Claude Computer Use API for article generation, intelligent tagging, scheduling, and publishing.

## Features

- **Automated Article Generation**: Generate complete, formatted articles from topics using Claude AI (3-5 min)
- **Intelligent Tagging**: Automatic content categorization with 85%+ accuracy
- **Scheduled Publishing**: Time-based article publishing with 1-minute precision
- **Review Workflows**: Content approval and modification workflows
- **Semantic Duplicate Detection**: Prevent redundant article creation
- **CMS Integration**: WordPress adapter (extensible to other platforms)

## Tech Stack

**Backend**:
- Python 3.11+
- FastAPI (REST API)
- SQLAlchemy + PostgreSQL + pgvector
- Celery + Redis (task queue)
- Anthropic Claude API

**Frontend**:
- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- React Query (data fetching)
- React Hook Form (forms)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Anthropic API Key

### Setup with Docker (Recommended)

1. **Clone and Configure**
   ```bash
   git clone <repository-url>
   cd cms_automation
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials**
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   CMS_BASE_URL=https://your-wordpress-site.com
   CMS_USERNAME=admin
   CMS_APPLICATION_PASSWORD=your-app-password
   SECRET_KEY=$(openssl rand -hex 32)
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   ```

4. **Run Migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Access Applications**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Flower (Task Monitor): http://localhost:5555

### Local Development Setup

#### Backend

```bash
cd backend

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Create .env file
cp ../.env.example ../.env
# Edit .env with your configuration

# Run migrations
poetry run alembic upgrade head

# Start API server
poetry run uvicorn src.main:app --reload --port 8000

# Start Celery worker (separate terminal)
poetry run celery -A src.workers.celery_app worker --loglevel=info

# Start Celery Beat scheduler (separate terminal)
poetry run celery -A src.workers.celery_app beat --loglevel=info
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Project Structure

```
cms_automation/
├── backend/
│   ├── src/
│   │   ├── models/              # SQLAlchemy models
│   │   ├── services/
│   │   │   ├── article_generator/  # Claude API integration
│   │   │   ├── content_analyzer/   # Tagging & categorization
│   │   │   ├── scheduler/          # Publishing scheduler
│   │   │   ├── cms_adapter/        # CMS platform adapters
│   │   │   └── similarity/         # Duplicate detection
│   │   ├── api/
│   │   │   ├── routes/          # REST endpoints
│   │   │   ├── middleware/      # Auth, logging, errors
│   │   │   └── schemas/         # Pydantic models
│   │   ├── workers/             # Celery tasks
│   │   └── config/              # Configuration
│   ├── tests/
│   ├── migrations/              # Alembic migrations
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ArticleGenerator/
│   │   │   ├── ReviewWorkflow/
│   │   │   ├── ScheduleManager/
│   │   │   └── Tags/
│   │   ├── services/            # API client
│   │   ├── hooks/               # React hooks
│   │   └── utils/
│   ├── tests/
│   └── package.json
│
├── specs/                        # Feature specifications & planning
├── docker-compose.yml
└── .env.example
```

## API Usage

### Submit Article Topic

```bash
curl -X POST http://localhost:8000/v1/topics \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "topic_description": "Write a guide on setting up PostgreSQL with pgvector",
    "style_tone": "professional",
    "target_word_count": 1500
  }'
```

### Check Generation Status

```bash
curl http://localhost:8000/v1/topics/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Generated Article

```bash
curl http://localhost:8000/v1/articles/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Development

### Run Tests

```bash
# Backend
cd backend
poetry run pytest

# Frontend
cd frontend
npm run test
```

### Code Quality

```bash
# Backend linting
cd backend
poetry run ruff check src/
poetry run mypy src/
poetry run black --check src/

# Frontend linting
cd frontend
npm run lint
npm run format:check
```

### Database Migrations

```bash
# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Run migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1
```

## Configuration

Key environment variables:

- `ANTHROPIC_API_KEY`: Claude API key (required)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `CMS_TYPE`: CMS platform (wordpress, strapi, etc.)
- `CMS_BASE_URL`: CMS instance URL
- `SIMILARITY_THRESHOLD`: Duplicate detection threshold (0.0-1.0, default: 0.85)
- `MAX_CONCURRENT_GENERATIONS`: Concurrent article generation limit (default: 10)

See `.env.example` for full configuration options.

## Architecture

- **Web Application**: Separate backend API and frontend UI
- **Task Queue**: Celery with Redis for async article generation
- **Database**: PostgreSQL with pgvector for semantic similarity
- **CMS Adapter Pattern**: Extensible to multiple CMS platforms
- **API-First Design**: RESTful API with OpenAPI documentation

## Performance

- Article generation: 3-5 minutes (95th percentile)
- Concurrent requests: 50+ simultaneous generations
- Scheduling accuracy: ±1 minute
- API response time: <500ms (non-generation endpoints)
- Tagging analysis: <10 seconds per article

## Success Metrics

- 70% reduction in content creation time
- 85%+ automated tagging accuracy
- 99% scheduled publishing success rate
- 90% of articles require minimal editing

## Documentation

- [Feature Specification](specs/001-cms-automation/spec.md)
- [Implementation Plan](specs/001-cms-automation/plan.md)
- [Database Schema](specs/001-cms-automation/data-model.md)
- [API Documentation](specs/001-cms-automation/contracts/api-spec.yaml)
- [Quickstart Guide](specs/001-cms-automation/quickstart.md)
- [Implementation Tasks](specs/001-cms-automation/tasks.md)

## Implementation Status

**Phase 1: Setup** - ✅ Complete
- Project structure created
- Python 3.11+ backend initialized with Poetry
- React 18+ frontend initialized with Vite
- Docker Compose configuration ready
- Environment templates configured
- Linting and formatting tools configured

**Next Steps**: Phase 2 - Foundational infrastructure (database, API, task queue)

## License

MIT License - See LICENSE file for details

## Support

- Issues: https://github.com/your-org/cms-automation/issues
- Documentation: See `/specs` directory
- API Reference: http://localhost:8000/docs (when running)
