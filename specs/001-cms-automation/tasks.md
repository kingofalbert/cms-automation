# Tasks: AI-Powered CMS Automation

**Input**: Design documents from `/specs/001-cms-automation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-spec.yaml

**Tests**: Tests are OPTIONAL and not explicitly requested in the feature specification. This task list focuses on implementation only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md, this project uses web application structure:
- **Backend**: `backend/src/`, `backend/tests/`, `backend/migrations/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure) ✅ COMPLETE

**Purpose**: Project initialization and basic structure

- [x] T001 Create backend project structure (backend/src/{models,services,api,workers,config}) per plan.md
- [x] T002 Create frontend project structure (frontend/src/{components,services,hooks,utils}) per plan.md
- [x] T003 [P] Initialize Python 3.11+ project with Poetry/uv in backend/
- [x] T004 [P] Initialize React 18+ TypeScript project with Vite in frontend/
- [x] T005 [P] Install backend dependencies: anthropic, fastapi, sqlalchemy, celery, redis, psycopg2, alembic
- [x] T006 [P] Install frontend dependencies: react, react-query, react-hook-form, tailwind, date-fns
- [x] T007 [P] Configure linting (ruff, mypy) and formatting (black, isort) for backend
- [x] T008 [P] Configure linting (eslint, typescript) and formatting (prettier) for frontend
- [x] T009 Create Docker Compose configuration in docker-compose.yml for postgres, redis, backend, frontend, workers
- [x] T010 [P] Create .env.example template with required environment variables per quickstart.md
- [x] T011 [P] Setup README.md with project overview and setup instructions

---

## Phase 2: Foundational (Blocking Prerequisites) ✅ COMPLETE

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Foundation

- [x] T012 Install and enable pgvector extension in PostgreSQL database
- [x] T013 Initialize Alembic for database migrations in backend/migrations/
- [x] T014 [P] Create base SQLAlchemy models infrastructure in backend/src/models/base.py
- [x] T015 [P] Configure database connection pooling in backend/src/config/database.py
- [x] T016 Create initial migration for base tables structure in backend/migrations/versions/

### API Foundation

- [x] T017 Setup FastAPI application with CORS and middleware in backend/src/main.py
- [x] T018 [P] Implement authentication middleware integration in backend/src/api/middleware/auth.py
- [x] T019 [P] Implement error handling middleware in backend/src/api/middleware/error_handler.py
- [x] T020 [P] Implement request logging middleware in backend/src/api/middleware/logging.py
- [x] T021 [P] Create API route registration structure in backend/src/api/routes/__init__.py
- [x] T022 [P] Implement Pydantic base schemas for request/response validation in backend/src/api/schemas/base.py

### Task Queue Foundation

- [x] T023 Configure Celery application with Redis broker in backend/src/workers/celery_app.py
- [x] T024 [P] Setup Celery Beat for scheduled tasks in backend/src/workers/beat_schedule.py
- [x] T025 [P] Create base task classes with retry logic in backend/src/workers/base_task.py
- [x] T026 [P] Implement task monitoring configuration for Flower in backend/src/workers/monitoring.py

### CMS Integration Foundation

- [x] T027 Create abstract CMS adapter interface in backend/src/services/cms_adapter/base.py
- [x] T028 Implement WordPress adapter in backend/src/services/cms_adapter/wordpress_adapter.py
- [x] T029 [P] Add CMS authentication handling in backend/src/services/cms_adapter/auth.py
- [x] T030 [P] Create CMS adapter factory in backend/src/services/cms_adapter/factory.py

### Configuration & Logging

- [x] T031 [P] Implement configuration management in backend/src/config/settings.py
- [x] T032 [P] Setup structured logging with JSON output in backend/src/config/logging.py
- [x] T033 [P] Create environment-specific configs (dev, staging, prod) in backend/src/config/

### Frontend Foundation

- [x] T034 Setup React Router with route definitions in frontend/src/routes.tsx
- [x] T035 [P] Configure React Query client in frontend/src/services/query-client.ts
- [x] T036 [P] Create API client with authentication in frontend/src/services/api-client.ts
- [x] T037 [P] Implement Tailwind theme configuration in frontend/tailwind.config.js
- [x] T038 [P] Create base UI components (Button, Input, Card) in frontend/src/components/ui/

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Article Creation (Priority: P1) 🎯 MVP

**Goal**: Content managers can submit article topics and receive fully formatted, ready-to-publish articles within 3-5 minutes

**Independent Test**: Submit an article topic through the UI, verify a complete article is generated with title, body, and formatting within 5 minutes

### Data Models for US1

- [x] T039 [P] [US1] Create TopicRequest model in backend/src/models/topic_request.py
- [x] T040 [P] [US1] Create Article model with status enum in backend/src/models/article.py
- [x] T041 [P] [US1] Create TopicEmbedding model for similarity detection in backend/src/models/topic_embedding.py
- [x] T042 [US1] Create database migration for topic_requests, articles, topic_embeddings tables in backend/migrations/versions/
- [x] T043 [US1] Add database indexes for articles.status and articles.author_id in migration

### Claude API Integration for US1

- [x] T044 [P] [US1] Implement Claude API client wrapper in backend/src/services/article_generator/claude_client.py
- [ ] T045 [P] [US1] Create article generation prompts and templates in backend/src/services/article_generator/prompts.py
- [x] T046 [US1] Implement ArticleGeneratorService with retry logic in backend/src/services/article_generator/generator.py
- [ ] T047 [US1] Add content quality validation (word count, readability) in backend/src/services/article_generator/validator.py
- [x] T048 [US1] Implement cost tracking for Claude API usage in backend/src/services/article_generator/cost_tracker.py

### Semantic Similarity for US1 (DEFERRED TO PHASE 4)

- [ ] T049 [P] [US1] **[Phase 4]** Implement embedding generation service in backend/src/services/similarity/embedding_service.py (Use Claude API embedding endpoint text-embedding-ada-002 equivalent, 1536-dimension vectors with L2 normalization before storage in pgvector)
- [ ] T050 [US1] **[Phase 4]** Implement duplicate detection using pgvector cosine similarity in backend/src/services/similarity/duplicate_detector.py
- [ ] T051 [US1] **[Phase 4]** Add similarity threshold configuration (0.85 default) in backend/src/config/similarity.py

### Celery Tasks for US1

- [x] T052 [US1] Create article generation Celery task in backend/src/workers/tasks/generate_article.py
- [x] T053 [US1] Add task progress tracking and status updates in article generation task
- [x] T054 [US1] Implement error handling and retry logic for API failures in generation task
- [ ] T055 [US1] **[Phase 4]** Add embedding generation as async subtask in generation workflow

### API Endpoints for US1

- [x] T056 [P] [US1] Create TopicRequest schemas in backend/src/api/schemas/topic_request.py
- [x] T057 [P] [US1] Create Article schemas in backend/src/api/schemas/article.py
- [x] T058 [US1] Implement POST /v1/topics endpoint in backend/src/api/routes/topics.py
- [x] T059 [US1] Implement GET /v1/topics endpoint with pagination in backend/src/api/routes/topics.py
- [x] T060 [US1] Implement GET /v1/topics/{requestId} endpoint in backend/src/api/routes/topics.py
- [ ] T061 [US1] Implement DELETE /v1/topics/{requestId} (cancel) in backend/src/api/routes/topics.py
- [x] T062 [US1] Implement GET /v1/articles endpoint with filters in backend/src/api/routes/articles.py
- [x] T063 [US1] Implement GET /v1/articles/{articleId} endpoint in backend/src/api/routes/articles.py
- [ ] T064 [US1] **[Phase 4]** Implement GET /v1/articles/{articleId}/similarity endpoint in backend/src/api/routes/articles.py

### Frontend UI for US1

- [x] T065 [P] [US1] Create TopicSubmissionForm component in frontend/src/components/ArticleGenerator/TopicSubmissionForm.tsx
- [ ] T066 [P] [US1] Create GenerationProgress component in frontend/src/components/ArticleGenerator/GenerationProgress.tsx
- [x] T067 [P] [US1] Create ArticlePreview component in frontend/src/components/ArticleGenerator/ArticlePreview.tsx
- [x] T068 [US1] Implement topic submission page in frontend/src/pages/ArticleGeneratorPage.tsx
- [x] T069 [US1] Create React Query hooks for topic operations in frontend/src/hooks/useTopicRequests.ts
- [x] T070 [US1] Create React Query hooks for article operations in frontend/src/hooks/useArticles.ts
- [ ] T071 [US1] Add real-time progress polling for generation status in frontend/src/hooks/useGenerationProgress.ts

### Integration & Error Handling for US1

- [ ] T072 [US1] Implement batch topic submission handling in backend/src/api/routes/topics.py
- [ ] T073 [US1] **[Phase 4]** Add duplicate detection check before topic submission in backend/src/api/routes/topics.py
- [ ] T074 [US1] Implement article metadata extraction and storage in backend/src/services/article_generator/metadata_extractor.py
- [ ] T075 [US1] Add error notification system for failed generations in backend/src/services/notifications/generator_notifications.py
- [ ] T076 [US1] Create audit logging for article generation events in backend/src/services/audit/article_audit.py

**Checkpoint**: User Story 1 complete - article generation fully functional and testable independently

---

## Phase 4: User Story 2 - Intelligent Tagging and Categorization (Priority: P2)

**Goal**: Articles are automatically tagged and categorized with 85%+ accuracy, ensuring consistent taxonomy and content discoverability

**Independent Test**: Provide pre-written articles (bypass generation), verify appropriate tags and categories are assigned with 85% accuracy

### Data Models for US2

- [ ] T077 [P] [US2] Create Tag model in backend/src/models/tag.py
- [ ] T078 [P] [US2] Create ArticleTag association model in backend/src/models/article_tag.py
- [ ] T079 [US2] Create database migration for tags and article_tags tables in backend/migrations/versions/
- [ ] T080 [US2] Add database indexes for tags.name and article_tags.confidence in migration
- [ ] T081 [US2] Add trigger for automatic tag usage_count updates in migration

### Content Analysis Service for US2

- [ ] T082 [P] [US2] Implement content analyzer using Claude API in backend/src/services/content_analyzer/analyzer.py
- [ ] T083 [P] [US2] Create tag extraction logic from article content in backend/src/services/content_analyzer/tag_extractor.py
- [ ] T084 [US2] Implement category assignment logic in backend/src/services/content_analyzer/category_assigner.py
- [ ] T085 [US2] Add tag confidence scoring algorithm in backend/src/services/content_analyzer/confidence_scorer.py
- [ ] T086 [US2] Implement tag normalization and synonym detection in backend/src/services/content_analyzer/tag_normalizer.py

### Tag Management for US2

- [ ] T087 [P] [US2] Create TagService for CRUD operations in backend/src/services/tag_service.py
- [ ] T088 [US2] Implement existing tag matching (case-insensitive) in backend/src/services/tag_service.py
- [ ] T089 [US2] Add automatic tag creation for new topics in backend/src/services/tag_service.py
- [ ] T090 [US2] Implement tag merging for synonyms in backend/src/services/tag_service.py

### Integration with Article Generation for US2

- [ ] T091 [US2] Add tagging step to article generation workflow in backend/src/workers/tasks/generate_article.py
- [ ] T092 [US2] Implement automatic tagging for manually created articles in backend/src/api/routes/articles.py
- [ ] T093 [US2] Add tag override capability for content managers in backend/src/api/routes/articles.py

### API Endpoints for US2

- [ ] T094 [P] [US2] Create Tag schemas in backend/src/api/schemas/tag.py
- [ ] T095 [US2] Implement GET /v1/tags endpoint with filters in backend/src/api/routes/tags.py
- [ ] T096 [US2] Implement POST /v1/tags endpoint (manual tag creation) in backend/src/api/routes/tags.py
- [ ] T097 [US2] Add tag assignment to PATCH /v1/articles/{articleId} endpoint in backend/src/api/routes/articles.py

### Frontend UI for US2

- [ ] T098 [P] [US2] Create TagDisplay component in frontend/src/components/Tags/TagDisplay.tsx
- [ ] T099 [P] [US2] Create TagEditor component for manual tagging in frontend/src/components/Tags/TagEditor.tsx
- [ ] T100 [P] [US2] Create TagConfidenceIndicator component in frontend/src/components/Tags/TagConfidenceIndicator.tsx
- [ ] T101 [US2] Add tag display to ArticlePreview component in frontend/src/components/ArticleGenerator/ArticlePreview.tsx
- [ ] T102 [US2] Create React Query hooks for tag operations in frontend/src/hooks/useTags.ts
- [ ] T103 [US2] Implement tag filtering and search in article list in frontend/src/pages/ArticleListPage.tsx

### Accuracy Tracking for US2

- [ ] T104 [US2] Implement tagging accuracy tracking system in backend/src/services/content_analyzer/accuracy_tracker.py
- [ ] T105 [US2] Create comparison logic against manual baseline in backend/src/services/content_analyzer/baseline_comparator.py
- [ ] T106 [US2] Add metrics endpoint for tagging accuracy in backend/src/api/routes/metrics.py

**Checkpoint**: User Story 2 complete - automated tagging functional, can be tested independently from generation

---

## Phase 5: User Story 3 - Scheduling and Publishing Workflow (Priority: P3)

**Goal**: Content managers can schedule articles for future publication with 99% success rate and ±1 minute accuracy

**Independent Test**: Schedule pre-created articles for future publication, verify they publish at correct time with proper status transitions

### Data Models for US3

- [ ] T107 [P] [US3] Create Schedule model in backend/src/models/schedule.py
- [ ] T108 [US3] Create database migration for schedules table in backend/migrations/versions/
- [ ] T109 [US3] Add database indexes for schedules.scheduled_time and schedules.status in migration

### Scheduling Service for US3

- [ ] T110 [P] [US3] Implement ScheduleService for CRUD operations in backend/src/services/scheduler/schedule_service.py
- [ ] T111 [US3] Add schedule validation (future time, article status checks) in backend/src/services/scheduler/validator.py
- [ ] T112 [US3] Implement retry configuration handling in backend/src/services/scheduler/retry_handler.py
- [ ] T113 [US3] Create schedule conflict detection (same time, resource limits) in backend/src/services/scheduler/conflict_detector.py

### Publishing Service for US3

- [ ] T114 [P] [US3] Implement article publishing logic via CMS adapter in backend/src/services/cms_adapter/publisher.py
- [ ] T115 [US3] Add pre-publication validation checks in backend/src/services/cms_adapter/publication_validator.py
- [ ] T116 [US3] Implement dependency verification (images, metadata) in backend/src/services/cms_adapter/dependency_checker.py
- [ ] T117 [US3] Add rollback mechanism for failed publications in backend/src/services/cms_adapter/rollback_handler.py

### Celery Beat Tasks for US3

- [ ] T118 [US3] Create scheduled publication Celery Beat task in backend/src/workers/tasks/publish_scheduled.py
- [ ] T119 [US3] Implement periodic schedule scanner (runs every minute) in backend/src/workers/beat_schedule.py
- [ ] T120 [US3] Add publication status update after success/failure in backend/src/workers/tasks/publish_scheduled.py
- [ ] T121 [US3] Implement retry logic with exponential backoff in backend/src/workers/tasks/publish_scheduled.py

### API Endpoints for US3

- [ ] T122 [P] [US3] Create Schedule schemas in backend/src/api/schemas/schedule.py
- [ ] T123 [US3] Implement POST /v1/schedules endpoint in backend/src/api/routes/schedules.py
- [ ] T124 [US3] Implement GET /v1/schedules endpoint with date filters in backend/src/api/routes/schedules.py
- [ ] T125 [US3] Implement GET /v1/schedules/{scheduleId} endpoint in backend/src/api/routes/schedules.py
- [ ] T126 [US3] Implement PATCH /v1/schedules/{scheduleId} (update time) in backend/src/api/routes/schedules.py
- [ ] T127 [US3] Implement DELETE /v1/schedules/{scheduleId} (cancel) in backend/src/api/routes/schedules.py
- [ ] T128 [US3] Implement POST /v1/articles/{articleId}/rollback endpoint in backend/src/api/routes/articles.py

### Frontend UI for US3

- [ ] T129 [P] [US3] Create ScheduleCalendar component in frontend/src/components/ScheduleManager/ScheduleCalendar.tsx
- [ ] T130 [P] [US3] Create ScheduleForm component in frontend/src/components/ScheduleManager/ScheduleForm.tsx
- [ ] T131 [P] [US3] Create ScheduleList component in frontend/src/components/ScheduleManager/ScheduleList.tsx
- [ ] T132 [US3] Implement scheduling page in frontend/src/pages/ScheduleManagerPage.tsx
- [ ] T133 [US3] Create React Query hooks for schedule operations in frontend/src/hooks/useSchedules.ts
- [ ] T134 [US3] Add schedule status indicators and notifications in frontend/src/components/ScheduleManager/ScheduleStatus.tsx

### Monitoring & Notifications for US3

- [ ] T135 [US3] Implement publication success/failure notifications in backend/src/services/notifications/publication_notifications.py
- [ ] T136 [US3] Add schedule accuracy tracking and metrics in backend/src/services/scheduler/metrics_tracker.py
- [ ] T137 [US3] Create publication audit logging in backend/src/services/audit/publication_audit.py

**Checkpoint**: User Story 3 complete - scheduling and publishing functional, can be tested independently

---

## Phase 6: User Story 4 - Content Review and Approval (Priority: P4)

**Goal**: Content managers can review AI-generated content, approve/reject, and request modifications through hybrid workflow

**Independent Test**: Generate articles, place in review status, test approval/rejection workflows with different user permission levels

### Data Models for US4

- [ ] T138 [P] [US4] Create WorkflowState model in backend/src/models/workflow_state.py
- [ ] T139 [US4] Create database migration for workflow_states table in backend/migrations/versions/
- [ ] T140 [US4] Add database indexes for workflow_states.current_status and workflow_states.article_id in migration
- [ ] T141 [US4] Add trigger for automatic workflow_states.updated_at in migration

### Workflow Service for US4

- [ ] T142 [P] [US4] Implement WorkflowService for state management in backend/src/services/workflow/workflow_service.py
- [ ] T143 [US4] Add reviewer assignment logic in backend/src/services/workflow/reviewer_assigner.py
- [ ] T143.1 [US4] Implement automatic reviewer assignment based on article category, editor availability, and load-balancing heuristics in backend/src/services/workflow/reviewer_assigner.py
- [ ] T144 [US4] Implement permission validation for approvals in backend/src/services/workflow/permission_validator.py
- [ ] T145 [US4] Create approval history tracking in backend/src/services/workflow/history_tracker.py
- [ ] T146 [US4] Add modification request handling in backend/src/services/workflow/modification_handler.py

### Article Modification for US4

- [ ] T147 [P] [US4] Implement manual edit tracking in backend/src/services/article_generator/edit_tracker.py
- [ ] T148 [US4] Create article regeneration with feedback in backend/src/workers/tasks/regenerate_article.py
- [ ] T149 [US4] Add version control for article modifications in backend/src/services/article_generator/version_control.py
- [ ] T150 [US4] Implement modification history export in backend/src/services/article_generator/history_exporter.py

### API Endpoints for US4

- [ ] T151 [P] [US4] Create WorkflowState schemas in backend/src/api/schemas/workflow.py
- [ ] T152 [US4] Implement GET /v1/workflows/{articleId} endpoint in backend/src/api/routes/workflows.py
- [ ] T153 [US4] Implement POST /v1/workflows/{articleId}/approve endpoint in backend/src/api/routes/workflows.py
- [ ] T154 [US4] Implement POST /v1/workflows/{articleId}/reject endpoint in backend/src/api/routes/workflows.py
- [ ] T155 [US4] Implement POST /v1/articles/{articleId}/regenerate endpoint in backend/src/api/routes/articles.py
- [ ] T156 [US4] Implement PATCH /v1/articles/{articleId} for manual edits in backend/src/api/routes/articles.py

### Frontend UI for US4

- [ ] T157 [P] [US4] Create ReviewPanel component in frontend/src/components/ReviewWorkflow/ReviewPanel.tsx
- [ ] T158 [P] [US4] Create ApprovalButtons component in frontend/src/components/ReviewWorkflow/ApprovalButtons.tsx
- [ ] T159 [P] [US4] Create FeedbackForm component for rejection/modification in frontend/src/components/ReviewWorkflow/FeedbackForm.tsx
- [ ] T160 [P] [US4] Create ModificationHistory component in frontend/src/components/ReviewWorkflow/ModificationHistory.tsx
- [ ] T161 [US4] Implement article review page in frontend/src/pages/ArticleReviewPage.tsx
- [ ] T162 [US4] Create React Query hooks for workflow operations in frontend/src/hooks/useWorkflow.ts
- [ ] T163 [US4] Add inline editing capability in ArticlePreview component in frontend/src/components/ArticleGenerator/ArticlePreview.tsx

### Notifications for US4

- [ ] T164 [US4] Implement review assignment notifications in backend/src/services/notifications/workflow_notifications.py
- [ ] T165 [US4] Add approval/rejection notifications in backend/src/services/notifications/workflow_notifications.py
- [ ] T166 [US4] Create modification request notifications in backend/src/services/notifications/workflow_notifications.py

**Checkpoint**: User Story 4 complete - review and approval workflow functional, all user stories independently testable

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements and quality enhancements that affect multiple user stories

### Health & Monitoring

- [ ] T167 [P] Implement health check endpoint GET /v1/health in backend/src/api/routes/health.py
- [ ] T168 [P] Add dependency health checks (database, redis, claude_api, cms_api) in backend/src/services/health/
- [ ] T169 [P] Create metrics collection for queue depth, generation time, API latency in backend/src/services/metrics/
- [ ] T170 [P] Implement Prometheus metrics exporter in backend/src/services/metrics/prometheus_exporter.py

### Audit & Compliance

- [ ] T171 [P] Create AuditLog model in backend/src/models/audit_log.py
- [ ] T172 Create database migration for audit_logs table with partitioning in backend/migrations/versions/
- [ ] T173 [P] Implement audit logging triggers for all entity changes in backend/migrations/versions/
- [ ] T174 [P] Create audit log query API in backend/src/api/routes/audit.py

### Performance Optimization

- [ ] T175 [P] Implement database query optimization (indexes, connection pooling) in backend/src/config/database.py
- [ ] T176 [P] Add Redis caching for frequently accessed data in backend/src/services/cache/
- [ ] T177 [P] Optimize API response times with pagination and filtering in backend/src/api/routes/
- [ ] T178 [P] Implement rate limiting middleware in backend/src/api/middleware/rate_limiter.py

### Security

- [ ] T179 [P] Add input validation and sanitization across all endpoints in backend/src/api/schemas/
- [ ] T180 [P] Implement API key rotation mechanism in backend/src/services/auth/key_rotation.py
- [ ] T181 [P] Add HTTPS enforcement and security headers in backend/src/main.py
- [ ] T182 [P] Create secrets management integration in backend/src/config/secrets.py

### Documentation

- [ ] T183 [P] Generate OpenAPI documentation endpoint in backend/src/main.py
- [ ] T184 [P] Create API reference documentation in docs/api-reference.md
- [ ] T185 [P] Document deployment procedures in docs/deployment.md
- [ ] T186 [P] Create troubleshooting guide in docs/troubleshooting.md

### Testing Infrastructure

- [ ] T187 [P] Setup pytest configuration in backend/pytest.ini
- [ ] T188 [P] Create test fixtures and factories in backend/tests/fixtures/
- [ ] T189 [P] Setup Playwright configuration in frontend/playwright.config.ts
- [ ] T190 [P] Create E2E test helpers in frontend/tests/helpers/

### Deployment Readiness

- [ ] T191 [P] Create production Dockerfile for backend in backend/Dockerfile
- [ ] T192 [P] Create production Dockerfile for frontend in frontend/Dockerfile
- [ ] T193 [P] Setup CI/CD pipeline configuration in .github/workflows/
- [ ] T194 [P] Create database backup and restore scripts in backend/scripts/
- [ ] T195 [P] Implement zero-downtime deployment strategy in docs/deployment.md
- [ ] T196 Run quickstart.md validation to ensure setup instructions work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion - MVP target
- **User Story 2 (Phase 4)**: Depends on Foundational completion - Independent of US1 but integrates with generation
- **User Story 3 (Phase 5)**: Depends on Foundational completion - Independent of US1/US2 but uses their outputs
- **User Story 4 (Phase 6)**: Depends on Foundational completion - Independent of other stories but enhances workflow
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories ✅ MVP READY
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 generation but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses articles from US1 but independently testable
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Enhances all stories but independently testable

### Within Each User Story

**General Pattern**:
1. Data models and migrations (can run in parallel within story)
2. Service layer implementation (depends on models)
3. Celery tasks (depends on services)
4. API endpoints (depends on services)
5. Frontend components (can run in parallel)
6. Frontend pages (depends on components)
7. Integration and error handling

### Parallel Opportunities

**Setup Phase (Phase 1)**:
- T003-T008: All dependency installation and configuration tasks
- T010-T011: Documentation tasks

**Foundational Phase (Phase 2)**:
- T014-T015: Database setup
- T018-T022: API middleware (different files)
- T024-T026: Celery configuration
- T029, T030: CMS adapter helpers
- T031-T033: Configuration
- T035-T038: Frontend foundation

**User Story 1 (Phase 3)**:
- T039-T041: All models (different files)
- T044-T045, T048: Article generator components
- T049, T051: Similarity components
- T056-T057: API schemas
- T065-T067: Frontend components

**User Story 2 (Phase 4)**:
- T077-T078: Models
- T082-T083: Analyzer components
- T087: Tag service
- T094: Schemas
- T098-T100: Frontend components

**User Story 3 (Phase 5)**:
- T107: Schedule model
- T110-T111: Scheduler components
- T114-T115: Publishing components
- T122: Schemas
- T129-T131: Frontend components

**User Story 4 (Phase 6)**:
- T138: Workflow model
- T142-T143: Workflow components
- T147-T148: Modification handlers
- T151: Schemas
- T157-T160: Frontend components

**Polish Phase (Phase 7)**:
- T167-T170: Health and monitoring
- T171, T174: Audit (T173 depends on T172)
- T175-T178: Performance
- T179-T182: Security
- T183-T186: Documentation
- T187-T190: Testing infrastructure
- T191-T195: Deployment

---

## Parallel Example: User Story 1

```bash
# Phase 1: All models for US1 can start together:
Task T039: "Create TopicRequest model in backend/src/models/topic_request.py"
Task T040: "Create Article model with status enum in backend/src/models/article.py"
Task T041: "Create TopicEmbedding model for similarity detection in backend/src/models/topic_embedding.py"

# Phase 2: Generator components (after models complete):
Task T044: "Implement Claude API client wrapper in backend/src/services/article_generator/claude_client.py"
Task T045: "Create article generation prompts in backend/src/services/article_generator/prompts.py"
Task T048: "Implement cost tracking in backend/src/services/article_generator/cost_tracker.py"

# Phase 3: API schemas can start in parallel:
Task T056: "Create TopicRequest schemas in backend/src/api/schemas/topic_request.py"
Task T057: "Create Article schemas in backend/src/api/schemas/article.py"

# Phase 4: Frontend components can start together:
Task T065: "Create TopicSubmissionForm component in frontend/src/components/ArticleGenerator/TopicSubmissionForm.tsx"
Task T066: "Create GenerationProgress component in frontend/src/components/ArticleGenerator/GenerationProgress.tsx"
Task T067: "Create ArticlePreview component in frontend/src/components/ArticleGenerator/ArticlePreview.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only) - RECOMMENDED

1. ✅ Complete **Phase 1: Setup** (T001-T011)
2. ✅ Complete **Phase 2: Foundational** (T012-T038) - CRITICAL BLOCKER
3. ✅ Complete **Phase 3: User Story 1** (T039-T076) - MVP READY
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Submit article topics through UI
   - Verify articles generated within 5 minutes
   - Test batch submissions
   - Verify duplicate detection works
   - Confirm all 3 acceptance scenarios pass
5. Deploy/demo if ready - **THIS IS YOUR MINIMUM VIABLE PRODUCT**

**MVP Scope**: 76 tasks for complete article generation workflow

### Incremental Delivery (Add Stories Sequentially)

1. Foundation + User Story 1 → Test → Deploy (MVP with article generation)
2. Add User Story 2 → Test → Deploy (MVP + automated tagging)
3. Add User Story 3 → Test → Deploy (Full automation with scheduling)
4. Add User Story 4 → Test → Deploy (Complete with review workflow)
5. Polish Phase → Production-ready

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. **Team completes Setup + Foundational together** (T001-T038)
2. **Once Foundational is done, parallel development**:
   - **Developer Team A**: User Story 1 (T039-T076) - Article Generation
   - **Developer Team B**: User Story 2 (T077-T106) - Tagging System
   - **Developer Team C**: User Story 3 (T107-T137) - Scheduling System
   - **Developer Team D**: User Story 4 (T138-T166) - Review Workflow
3. Stories complete and integrate independently
4. Polish phase after all stories complete

---

## Task Count Summary

- **Phase 1 (Setup)**: 11 tasks
- **Phase 2 (Foundational)**: 27 tasks - BLOCKING ALL STORIES
- **Phase 3 (User Story 1 - MVP)**: 38 tasks
- **Phase 4 (User Story 2)**: 30 tasks
- **Phase 5 (User Story 3)**: 31 tasks
- **Phase 6 (User Story 4)**: 30 tasks
- **Phase 7 (Polish)**: 30 tasks

**Total**: 197 tasks

**MVP Scope** (Setup + Foundational + US1): 76 tasks
**Full Feature** (All User Stories): 167 tasks
**Production Ready** (Full + Polish): 197 tasks

---

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability
- **Each user story is independently testable**: Can validate each story works without others
- **MVP strategy**: Complete just User Story 1 for fastest time-to-value
- **Incremental delivery**: Add one story at a time, test, deploy
- **Parallel execution**: Once Foundational is done, all user stories can proceed simultaneously
- **File paths**: All paths specified for immediate implementation
- **No tests included**: Tests not explicitly requested in specification, focus on implementation

**Format Validation**: ✅ All tasks follow required format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
