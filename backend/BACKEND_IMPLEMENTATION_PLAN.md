# Backend Implementation Plan

**Status**: 🚧 In Progress (10% complete)
**Estimated Total Time**: 90 hours
**Current Phase**: Phase 1 - Publishing API

---

## Progress Summary

### ✅ Completed (10%)

**Model Updates** (2h):
- ✅ Updated `Provider` enum to match frontend:
  - `PLAYWRIGHT`, `COMPUTER_USE`, `HYBRID`
- ✅ Updated `TaskStatus` enum with detailed workflow steps:
  - `IDLE`, `PENDING`, `INITIALIZING`, `LOGGING_IN`, `CREATING_POST`, `UPLOADING_IMAGES`, `CONFIGURING_SEO`, `PUBLISHING`, `COMPLETED`, `FAILED`
- ✅ Added progress tracking fields to `PublishTask`:
  - `progress` (0-100)
  - `current_step`
  - `total_steps`
  - `completed_steps`

### 🚧 In Progress

**Phase 1: Publishing API** (14h remaining):
1. Add helper methods to `PublishTask` model for progress updates
2. Create Pydantic schemas for API requests/responses
3. Create Publishing API routes (`/api/v1/publish/...`)
4. Implement async publishing service with Celery
5. Implement provider orchestration (Playwright/Computer Use/Hybrid)

---

## Detailed Implementation Plan

### Phase 1: Publishing API (16h total, 2h done)

**Remaining Tasks** (14h):

#### 1.1 Complete Model Updates (2h)
- [ ] Add helper method `update_progress(step_name, completed_steps, progress)`
- [ ] Add property `article_title` (computed from relationship)
- [ ] Update `mark_started()` to set initial progress
- [ ] Update constraints for progress fields

#### 1.2 Create Pydantic Schemas (3h)
**File**: `backend/src/api/schemas/publishing.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PublishOptions(BaseModel):
    """Publishing options."""
    seo_optimization: bool = True
    publish_immediately: bool = True
    tags: Optional[List[str]] = []
    categories: Optional[List[str]] = []

class PublishRequest(BaseModel):
    """Request to submit publishing task."""
    provider: str = Field(..., pattern="^(playwright|computer_use|hybrid)$")
    options: PublishOptions

class PublishResult(BaseModel):
    """Result of publishing submission."""
    task_id: str
    status: str
    message: str

class Screenshot(BaseModel):
    """Screenshot metadata."""
    step: str
    timestamp: str
    image_url: str

class PublishTaskResponse(BaseModel):
    """Publishing task response."""
    id: str
    article_id: str
    article_title: str
    provider: str
    status: str
    progress: int
    current_step: str
    total_steps: int
    completed_steps: int
    screenshots: List[Screenshot]
    error_message: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    duration: Optional[int] = None
    cost: Optional[float] = None
```

#### 1.3 Create Publishing Routes (5h)
**File**: `backend/src/api/routes/publish_routes.py`

**Endpoints to implement**:

1. **POST /api/v1/publish/submit/{article_id}**
   - Submit new publishing task
   - Validate article exists
   - Create PublishTask record
   - Dispatch Celery task
   - Return task_id

2. **GET /api/v1/publish/tasks/{task_id}/status**
   - Get single task status
   - Include screenshots array
   - Calculate duration if running

3. **GET /api/v1/publish/tasks**
   - List all tasks with filters
   - Query params: `status`, `provider`, `limit`, `offset`
   - Return paginated results

4. **POST /api/v1/publish/tasks/{task_id}/retry**
   - Retry failed task
   - Check `can_retry` property
   - Increment retry_count
   - Dispatch new Celery task

#### 1.4 Create Publishing Service (4h)
**File**: `backend/src/services/publishing/orchestrator.py`

```python
class PublishingOrchestrator:
    """Orchestrates publishing across different providers."""

    async def publish_article(
        self,
        task_id: int,
        article_id: int,
        provider: Provider,
        options: dict
    ) -> PublishTask:
        """Execute publishing workflow."""
        # 1. Load article
        # 2. Select provider (Playwright/Computer Use/Hybrid)
        # 3. Execute publishing steps with progress updates
        # 4. Handle screenshots
        # 5. Track cost
        # 6. Mark completed/failed
```

**Provider Implementations**:
- `PlaywrightPublisher` - Use existing Playwright provider
- `ComputerUsePublisher` - New Computer Use implementation
- `HybridPublisher` - Orchestrate with fallback logic

---

### Phase 2: Task Monitoring API (12h)

#### 2.1 Create Monitoring Schemas (2h)
**File**: `backend/src/api/schemas/monitoring.py`

```python
class TaskFilters(BaseModel):
    status: Optional[str] = None
    provider: Optional[str] = None
    limit: int = 50
    offset: int = 0

class TaskStatistics(BaseModel):
    total: int
    completed: int
    failed: int
    in_progress: int
```

#### 2.2 Create Monitoring Routes (6h)
**File**: `backend/src/api/routes/monitoring_routes.py`

**Endpoints**:
1. GET /api/v1/monitoring/tasks - List tasks with advanced filters
2. GET /api/v1/monitoring/statistics - Get aggregated statistics
3. GET /api/v1/monitoring/tasks/{id}/logs - Get execution logs

#### 2.3 Create Monitoring Service (4h)
**File**: `backend/src/services/monitoring/service.py`

- Implement efficient task queries with pagination
- Calculate statistics (success rate, avg duration, etc.)
- Fetch execution logs with partitioning

---

### Phase 3: Analytics & Comparison API (14h)

#### 3.1 Create Analytics Models (3h)
**File**: `backend/src/models/analytics.py`

```python
class ProviderMetrics(Base):
    """Aggregated provider performance metrics."""
    __tablename__ = "provider_metrics"

    provider: Mapped[Provider]
    date: Mapped[datetime]  # Partition key
    total_tasks: Mapped[int]
    successful_tasks: Mapped[int]
    failed_tasks: Mapped[int]
    success_rate: Mapped[float]
    avg_duration: Mapped[float]
    avg_cost: Mapped[float]
    total_cost: Mapped[float]
```

#### 3.2 Create Analytics Routes (6h)
**File**: `backend/src/api/routes/analytics_routes.py`

**Endpoints**:
1. GET /api/v1/analytics/provider-comparison?time_range={7d|30d|90d|all}
2. GET /api/v1/analytics/cost-usage
3. GET /api/v1/analytics/storage-usage
4. GET /api/v1/analytics/recommendations

#### 3.3 Create Analytics Service (5h)
**File**: `backend/src/services/analytics/service.py`

- Aggregate metrics by provider and time range
- Calculate task distribution
- Generate AI-powered recommendations
- Track cost usage (daily/monthly)

---

### Phase 4: Settings Management API (10h)

#### 4.1 Create Settings Models (2h)
**File**: `backend/src/models/settings.py`

```python
class AppSettings(Base):
    """Application settings (singleton pattern)."""
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    provider_config: Mapped[dict] = mapped_column(JSONB)
    cms_config: Mapped[dict] = mapped_column(JSONB)
    cost_limits: Mapped[dict] = mapped_column(JSONB)
    screenshot_retention: Mapped[dict] = mapped_column(JSONB)
    updated_at: Mapped[datetime]
```

#### 4.2 Create Settings Routes (4h)
**File**: `backend/src/api/routes/settings_routes.py`

**Endpoints**:
1. GET /api/v1/settings - Get current settings
2. PUT /api/v1/settings - Update settings (partial updates)
3. POST /api/v1/settings/test-connection - Test WordPress connection

#### 4.3 Create Settings Service (4h)
**File**: `backend/src/services/settings/service.py`

- Load settings (with defaults)
- Validate settings updates
- Test WordPress connection
- Encrypt sensitive data (passwords)

---

### Phase 5: Worklist & Google Drive API (18h)

#### 5.1 Create Worklist Models (3h)
**File**: `backend/src/models/worklist.py`

```python
class WorklistStatus(str, PyEnum):
    TO_EVALUATE = "to_evaluate"
    TO_CONFIRM = "to_confirm"
    TO_REVIEW = "to_review"
    TO_REVISE = "to_revise"
    TO_REREVIEW = "to_rereview"
    READY_TO_PUBLISH = "ready_to_publish"
    PUBLISHED = "published"

class WorklistItem(Base):
    """Worklist item from Google Drive."""
    __tablename__ = "worklist_items"

    drive_file_id: Mapped[str] = mapped_column(unique=True)
    title: Mapped[str]
    status: Mapped[WorklistStatus]
    content: Mapped[str] = mapped_column(Text)
    author: Mapped[str]
    metadata: Mapped[dict] = mapped_column(JSONB)
    notes: Mapped[List] = mapped_column(JSONB)
```

#### 5.2 Create Worklist Routes (6h)
**File**: `backend/src/api/routes/worklist_routes.py`

**Endpoints**:
1. GET /api/v1/worklist - List worklist items with filters
2. GET /api/v1/worklist/statistics - Get statistics
3. GET /api/v1/worklist/sync-status - Get sync status
4. POST /api/v1/worklist/sync - Trigger sync
5. POST /api/v1/worklist/{id}/status - Change status
6. POST /api/v1/worklist/{id}/publish - Publish to WordPress

#### 5.3 Google Drive Integration (9h)
**File**: `backend/src/services/google_drive/sync_service.py`

- OAuth 2.0 authentication
- List files from Drive folder
- Parse Google Docs content
- Sync worklist items (create/update)
- Track sync status and errors
- Handle rate limiting

---

### Phase 6: Database Schema & Migrations (12h)

#### 6.1 Create Migration Scripts (4h)
- Alembic migrations for new models
- Add indexes for performance
- Create partitions for execution_logs

#### 6.2 Database Optimizations (4h)
- Add composite indexes
- Configure connection pooling
- Set up read replicas (if needed)

#### 6.3 Data Validation (4h)
- Add database constraints
- Create triggers for audit trails
- Set up cascading deletes

---

### Phase 7: Integration Testing (8h)

#### 7.1 Unit Tests (3h)
- Test all API endpoints
- Test model methods
- Test service logic

#### 7.2 Integration Tests (3h)
- Test publishing workflow end-to-end
- Test Google Drive sync
- Test provider failover (Hybrid)

#### 7.3 Performance Testing (2h)
- Load testing with locust
- Database query optimization
- API response time benchmarks

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 14+ with partitioning
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic 2.0
- **Task Queue**: Celery + Redis
- **Testing**: pytest, pytest-asyncio

### Services
- **Playwright**: Browser automation
- **Computer Use**: Anthropic API (claude-3-5-sonnet)
- **Google Drive**: Google Drive API v3
- **WordPress**: REST API / XML-RPC

---

## API Endpoint Summary

### Publishing (4 endpoints)
- POST /api/v1/publish/submit/{article_id}
- GET /api/v1/publish/tasks/{task_id}/status
- GET /api/v1/publish/tasks
- POST /api/v1/publish/tasks/{task_id}/retry

### Monitoring (3 endpoints)
- GET /api/v1/monitoring/tasks
- GET /api/v1/monitoring/statistics
- GET /api/v1/monitoring/tasks/{id}/logs

### Analytics (4 endpoints)
- GET /api/v1/analytics/provider-comparison
- GET /api/v1/analytics/cost-usage
- GET /api/v1/analytics/storage-usage
- GET /api/v1/analytics/recommendations

### Settings (3 endpoints)
- GET /api/v1/settings
- PUT /api/v1/settings
- POST /api/v1/settings/test-connection

### Worklist (6 endpoints)
- GET /api/v1/worklist
- GET /api/v1/worklist/statistics
- GET /api/v1/worklist/sync-status
- POST /api/v1/worklist/sync
- POST /api/v1/worklist/{id}/status
- POST /api/v1/worklist/{id}/publish

**Total**: 20 API endpoints

---

## Database Schema

### Core Tables
1. `articles` - Article content and metadata (existing)
2. `publish_tasks` - Publishing task records (updated)
3. `execution_logs` - Detailed execution logs (partitioned)

### New Tables
4. `provider_metrics` - Aggregated provider performance (partitioned by date)
5. `app_settings` - Application settings (singleton)
6. `worklist_items` - Google Drive worklist items
7. `worklist_notes` - Comments/notes on worklist items
8. `cost_records` - Detailed cost tracking (partitioned by date)
9. `screenshot_storage` - Screenshot metadata and retention

---

## Next Steps

### Immediate (Today)
1. Complete `PublishTask` model updates with helper methods
2. Create `publishing.py` Pydantic schemas
3. Start implementing `publish_routes.py`

### This Week
1. Complete Publishing API (Phase 1)
2. Implement PublishingOrchestrator
3. Test publishing workflow with Playwright

### Next Week
1. Complete Task Monitoring API (Phase 2)
2. Start Analytics API (Phase 3)
3. Begin Google Drive integration research

---

## Dependencies

### Python Packages (to add)
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install anthropic  # For Computer Use
pip install celery[redis]
pip install alembic
```

### Environment Variables (to configure)
```env
# Google Drive
GOOGLE_DRIVE_CREDENTIALS_PATH=/path/to/credentials.json
GOOGLE_DRIVE_FOLDER_ID=xxx

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxx

# WordPress
DEFAULT_WP_URL=https://example.com
DEFAULT_WP_USERNAME=admin
DEFAULT_WP_PASSWORD=xxx

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## Progress Tracking

- [x] Phase 1: Publishing API - 10% (2h/16h)
- [ ] Phase 2: Task Monitoring API - 0% (0h/12h)
- [ ] Phase 3: Analytics API - 0% (0h/14h)
- [ ] Phase 4: Settings API - 0% (0h/10h)
- [ ] Phase 5: Worklist & Drive API - 0% (0h/18h)
- [ ] Phase 6: Database & Migrations - 0% (0h/12h)
- [ ] Phase 7: Integration Testing - 0% (0h/8h)

**Overall Progress**: 10% (9h/90h)

---

**Last Updated**: 2025-10-31
**Status**: Model updates in progress
**Next Milestone**: Complete Publishing API endpoints
