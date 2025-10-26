# Tasks: AI-Powered CMS Automation with SEO Optimization (Fusion Architecture)

**Input**: Design documents from `/specs/001-cms-automation/`
**Prerequisites**: plan.md v2.0, spec.md (updated), research.md, data-model.md (fusion), contracts/api-spec.yaml
**Last Updated**: 2025-10-25
**Architecture**: Dual-Source (AI Generation + Import) → Unified SEO → Computer Use Publishing

**Tests**: Tests are OPTIONAL and not explicitly requested in the feature specification. This task list focuses on implementation only.

**Organization**: Tasks are grouped by phase and user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US7)
- **✅**: Completed tasks (Phases 1-4)
- **⏳**: In Progress (Phase 5)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md v2.0, this project uses web application structure:
- **Backend**: `backend/src/`, `backend/tests/`, `backend/migrations/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure) ✅ COMPLETE

**Purpose**: Project initialization and basic structure
**Duration**: 1 week
**Status**: Completed

- [x] T001 Create backend project structure (backend/src/{models,services,api,workers,config}) per plan.md
- [x] T002 Create frontend project structure (frontend/src/{components,services,hooks,utils}) per plan.md
- [x] T003 [P] Initialize Python 3.13.7 project with Poetry 2.2.0 in backend/
- [x] T004 [P] Initialize React 18.3.1 TypeScript project with Vite in frontend/
- [x] T005 [P] Install backend dependencies: anthropic 0.71.0+, fastapi, sqlalchemy 2.0, celery 5.5.3, redis, psycopg2, alembic, bleach ★NEW, pandas ★NEW
- [x] T006 [P] Install frontend dependencies: react, react-query, react-hook-form, tailwind, date-fns
- [x] T007 [P] Configure linting (ruff, mypy) and formatting (black, isort) for backend
- [x] T008 [P] Configure linting (eslint, typescript) and formatting (prettier) for frontend
- [x] T009 Create Docker Compose configuration in docker-compose.yml for postgres, redis, backend, frontend, workers
- [x] T010 [P] Create .env.example template with required environment variables (including CMS_USERNAME, CMS_PASSWORD for Computer Use) ★UPDATED
- [x] T011 [P] Setup README.md with project overview and setup instructions

---

## Phase 2: Foundational Infrastructure ✅ COMPLETE

**Purpose**: Core infrastructure for all user stories
**Duration**: 2 weeks
**Status**: Completed

### Database Foundation
- [x] T012 Install and enable pgvector extension in PostgreSQL 15 database
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

### Configuration & Logging
- [x] T027 [P] Implement configuration management in backend/src/config/settings.py
- [x] T028 [P] Setup structured logging with JSON output in backend/src/config/logging.py
- [x] T029 [P] Create environment-specific configs (dev, staging, prod) in backend/src/config/

### Frontend Foundation
- [x] T030 Setup React Router with route definitions in frontend/src/routes.tsx
- [x] T031 [P] Configure React Query client in frontend/src/services/query-client.ts
- [x] T032 [P] Create API client with authentication in frontend/src/services/api-client.ts
- [x] T033 [P] Implement Tailwind theme configuration in frontend/tailwind.config.js
- [x] T034 [P] Create base UI components (Button, Input, Card) in frontend/src/components/ui/

**Checkpoint**: ✅ Foundation ready

---

## Phase 3: User Story 1 - AI Article Generation (Priority: P1) ✅ COMPLETE

**Goal**: Content managers can submit topics and receive fully formatted articles within 5 minutes
**Duration**: 2 weeks
**Status**: Completed - 6/6 E2E tests passing, 91.7% faster than SLA

### Data Models
- [x] T035 [P] [US1] Create TopicRequest model in backend/src/models/topic_request.py
- [x] T036 [P] [US1] Create Article model with status enum in backend/src/models/article.py
- [x] T037 [US1] Create database migration for topic_requests and articles tables

### Claude API Integration
- [x] T038 [P] [US1] Implement Claude Messages API client wrapper in backend/src/services/article_generator/claude_client.py
- [x] T039 [US1] Implement ArticleGeneratorService with retry logic in backend/src/services/article_generator/generator.py
- [x] T040 [US1] Implement cost tracking for Claude API usage in backend/src/services/article_generator/cost_tracker.py

### Celery Tasks
- [x] T041 [US1] Create article generation Celery task in backend/src/workers/tasks/generate_article.py
- [x] T042 [US1] Add task progress tracking and status updates
- [x] T043 [US1] Implement error handling and retry logic for API failures

### API Endpoints
- [x] T044 [P] [US1] Create TopicRequest schemas in backend/src/api/schemas/topic_request.py
- [x] T045 [P] [US1] Create Article schemas in backend/src/api/schemas/article.py
- [x] T046 [US1] Implement POST /v1/topics endpoint in backend/src/api/routes/topics.py
- [x] T047 [US1] Implement GET /v1/topics/{requestId} endpoint
- [x] T048 [US1] Implement GET /v1/articles/{articleId} endpoint in backend/src/api/routes/articles.py

### Frontend UI
- [x] T049 [P] [US1] Create TopicSubmissionForm component in frontend/src/components/ArticleGenerator/TopicSubmissionForm.tsx
- [x] T050 [P] [US1] Create ArticlePreview component in frontend/src/components/ArticleGenerator/ArticlePreview.tsx
- [x] T051 [US1] Implement topic submission page in frontend/src/pages/ArticleGeneratorPage.tsx
- [x] T052 [US1] Create React Query hooks for topic/article operations in frontend/src/hooks/

**Checkpoint**: ✅ US1 complete - AI generation functional

---

## Phase 4: Testing & Validation ✅ COMPLETE

**Duration**: 1 week
**Status**: Completed - 6/6 E2E tests passed (100%)

### E2E Tests
- [x] T053 E2E Test 1: Topic Submission workflow
- [x] T054 E2E Test 2: Article Generation Pipeline (25s average, 91.7% faster than 300s SLA)
- [x] T055 E2E Test 3: Article Display & Retrieval
- [x] T056 E2E Test 4: Error Handling (100% coverage)
- [x] T057 E2E Test 5: Concurrent Requests (3+ simultaneous)
- [x] T058 E2E Test 6: SLA Compliance validation

### Production Deployment
- [x] T059 Create production Docker configurations
- [x] T060 Create deployment documentation (DEPLOYMENT.md)

**Checkpoint**: ✅ System production-ready

---

## Phase 5: Fusion Architecture Extensions (In Progress ⏳)

**Purpose**: Add external article import, unified SEO optimization, and Computer Use publishing while preserving AI generation
**Duration**: 8-9 weeks
**Status**: In Progress

---

### Week 1-2: Database Extensions + Article Import (10 tasks)

#### Database Migration (T301-T306)

- [ ] T301 [P] [Phase 5] ⏳ **Extend articles table** with new columns in backend/migrations/versions/xxx_fusion_extensions.py:
  - Add `source VARCHAR(20) NOT NULL DEFAULT 'ai_generated'` CHECK (source IN ('ai_generated', 'imported'))
  - Add `seo_optimized BOOLEAN NOT NULL DEFAULT FALSE`
  - Add indexes: `idx_articles_source`, `idx_articles_seo_optimized`
  - **Dependencies**: None
  - **Est**: 2 hours
  - **Acceptance**: Migration runs successfully, existing articles have source='ai_generated', new columns indexed

- [ ] T302 [P] [Phase 5] ⏳ **Create seo_metadata table** in same migration:
  - Columns: id, article_id (FK), seo_title VARCHAR(60), meta_description VARCHAR(160), focus_keyword, primary_keywords TEXT[], secondary_keywords TEXT[], keyword_density JSONB, optimization_recommendations TEXT[], manual_overrides JSONB, readability_score DECIMAL(4,2), generated_at, updated_at
  - Constraints: CHECK seo_title length 50-60, CHECK meta_description length 150-160, CHECK primary_keywords array length 3-5, CHECK secondary_keywords array length 5-10
  - Indexes: `idx_seo_metadata_article`, `idx_seo_metadata_focus_keyword`
  - **Dependencies**: T301
  - **Est**: 2 hours
  - **Acceptance**: Table created with all constraints, foreign keys working

- [ ] T303 [P] [Phase 5] ⏳ **Create publish_tasks table** in same migration:
  - Columns: id, article_id (FK), cms_type VARCHAR(50) DEFAULT 'wordpress', status VARCHAR(20) DEFAULT 'pending', screenshots JSONB DEFAULT '[]', retry_count INT DEFAULT 0, max_retries INT DEFAULT 3, error_message TEXT, started_at, completed_at, duration_seconds INT, created_at
  - Constraints: CHECK max_retries > 0, CHECK retry_count <= max_retries, CHECK status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')
  - Indexes: `idx_publish_tasks_article`, `idx_publish_tasks_status`, `idx_publish_tasks_pending`
  - **Dependencies**: T301
  - **Est**: 2 hours
  - **Acceptance**: Table created with all constraints

- [ ] T304 [Phase 5] ⏳ **Create execution_logs table with partitioning** in same migration:
  - Partitioned table by timestamp (monthly)
  - Columns: id BIGSERIAL, publish_task_id (FK), action VARCHAR(50), target_element TEXT, payload JSONB, result VARCHAR(20), error_details TEXT, timestamp
  - Constraints: CHECK action IN ('navigate', 'click', 'type', 'upload', 'screenshot', 'verify', 'wait', 'scroll'), CHECK result IN ('success', 'failure', 'retry')
  - Indexes: `idx_execution_logs_task`, `idx_execution_logs_timestamp`, `idx_execution_logs_action`
  - Create first partition: execution_logs_2025_10
  - **Dependencies**: T303
  - **Est**: 3 hours
  - **Acceptance**: Partitioned table created, can insert logs to current month partition

- [ ] T305 [Phase 5] ⏳ **Deploy database triggers** for SEO and audit logging:
  - Trigger: `update_seo_optimized_status` on INSERT seo_metadata → UPDATE articles SET seo_optimized=TRUE
  - Trigger: `update_updated_at` on UPDATE seo_metadata → SET updated_at=NOW()
  - Trigger: `log_article_changes` on INSERT/UPDATE/DELETE articles → INSERT audit_logs
  - **Dependencies**: T302
  - **Est**: 2 hours
  - **Acceptance**: All triggers fire correctly, tested with sample data

- [ ] T306 [Phase 5] ⏳ **Backfill existing data** and validate migration:
  - Update all existing articles: SET source='ai_generated', seo_optimized=FALSE
  - Verify all foreign keys and constraints
  - Run ANALYZE on all new tables/indexes
  - **Dependencies**: T301-T305
  - **Est**: 1 hour
  - **Acceptance**: All existing data migrated correctly, performance benchmarks met

#### Article Importer Service (T307-T310)

- [ ] T307 [P] [US2] ⏳ **Implement CSV parser with validation** in backend/src/services/article_importer/csv_parser.py:
  - Use pandas for CSV parsing
  - Required columns: title, body
  - Optional columns: images (comma-separated URLs), excerpt, metadata
  - Validate: title 10-500 chars, body min 100 words
  - Return list of validated article dictionaries
  - **Dependencies**: None (can start parallel with T301)
  - **Est**: 4 hours
  - **Acceptance**: Parse CSV with 100 articles in < 30 seconds, validation catches all errors

- [ ] T308 [P] [US2] ⏳ **Implement HTML sanitization** in backend/src/services/article_importer/sanitizer.py:
  - Use bleach library for XSS prevention
  - Allowed tags: p, h1-h6, ul, ol, li, a, strong, em, code, pre, blockquote, img
  - Allowed attributes: href (for a), src/alt (for img), class
  - Strip all scripts, iframes, and dangerous tags
  - **Dependencies**: None
  - **Est**: 3 hours
  - **Acceptance**: 100% XSS prevention (tested with OWASP XSS vectors), preserves safe formatting

- [ ] T309 [US2] ⏳ **Implement ArticleImporterService** in backend/src/services/article_importer/importer.py:
  - Method: `import_csv(file_path, user_id) -> List[Article]`
  - Method: `import_json(data, user_id) -> List[Article]`
  - Method: `import_single(title, body, images, user_id) -> Article`
  - For each article: sanitize HTML, validate images URLs, set source='imported', store to DB
  - Batch insert for performance (100 articles in one transaction)
  - Return list of created article IDs
  - **Dependencies**: T306 (DB ready), T307 (CSV parser), T308 (sanitizer)
  - **Est**: 6 hours
  - **Acceptance**: Import 100 articles from CSV in < 5 minutes, 100% data integrity, transaction rollback on errors

- [ ] T310 [US2] ⏳ **Implement import API endpoints**:
  - POST /v1/articles/import endpoint in backend/src/api/routes/articles.py
  - Request schema: multipart/form-data with CSV file OR JSON array
  - Response schema: {article_ids: List[int], imported_count: int, failed_count: int, errors: List}
  - Add progress tracking for large batches (return task_id if > 50 articles)
  - **Dependencies**: T309
  - **Est**: 4 hours
  - **Acceptance**: API accepts CSV/JSON, returns correct counts, handles errors gracefully

**Week 1-2 Checkpoint**: Database extended, import functionality working, can import 100 articles in < 5 minutes

---

### Week 3-4: SEO Optimization Engine (15 tasks)

#### SEO Analyzer Service (T311-T318)

- [ ] T311 [P] [US3] ⏳ **Implement keyword extraction** in backend/src/services/seo_analyzer/keyword_extractor.py:
  - Use Claude Messages API with specialized SEO prompt
  - Extract: 1 focus keyword, 3-5 primary keywords, 5-10 secondary keywords
  - Calculate keyword density for each (count / total_words * 100)
  - Store in JSONB format: {"keyword": {"count": N, "density": X.X}}
  - **Dependencies**: None (can start parallel)
  - **Est**: 6 hours
  - **Acceptance**: Extract keywords from 1500-word article in < 20 seconds, 85%+ accuracy vs expert baseline (tested on 20 articles)

- [ ] T312 [P] [US3] ⏳ **Implement SEO metadata generation** in backend/src/services/seo_analyzer/metadata_generator.py:
  - Use Claude Messages API to generate SEO title (50-60 chars) and meta description (150-160 chars)
  - Include focus keyword in title and description
  - Follow Google Search Console best practices
  - Auto-truncate if exceeds length limits
  - **Dependencies**: T311 (needs focus keyword)
  - **Est**: 4 hours
  - **Acceptance**: Generated titles 100% within 50-60 chars, descriptions 100% within 150-160 chars, include focus keyword

- [ ] T313 [P] [US3] ⏳ **Implement readability scoring** in backend/src/services/seo_analyzer/readability_scorer.py:
  - Calculate Flesch-Kincaid Grade Level
  - Formula: 0.39 * (total_words / total_sentences) + 11.8 * (total_syllables / total_words) - 15.59
  - Use pyphen library for syllable counting
  - Target grade level: 8-12 (readable but professional)
  - **Dependencies**: None
  - **Est**: 3 hours
  - **Acceptance**: Score 1500-word article in < 1 second, scores match manual calculations

- [ ] T314 [US3] ⏳ **Implement optimization recommendations generator** in backend/src/services/seo_analyzer/recommendations_generator.py:
  - Check title length (warn if > 60 chars)
  - Check description length (warn if > 160 chars)
  - Check keyword density (warn if focus keyword < 0.5% or > 3%)
  - Check readability (warn if grade level < 8 or > 14)
  - Check image alt tags (if article has images)
  - Return array of actionable recommendations
  - **Dependencies**: T311-T313
  - **Est**: 4 hours
  - **Acceptance**: Generate 3-7 relevant recommendations per article, tested on 20 diverse articles

- [ ] T315 [US3] ⏳ **Implement SEO Analyzer orchestrator** in backend/src/services/seo_analyzer/analyzer.py:
  - Method: `analyze_article(article_id) -> SEOMetadata`
  - Orchestrate: keyword extraction → metadata generation → readability scoring → recommendations
  - Create SEOMetadata record in database
  - Update article.seo_optimized = TRUE
  - Return complete SEO metadata object
  - **Dependencies**: T311-T314, T306 (DB ready)
  - **Est**: 5 hours
  - **Acceptance**: Complete analysis of 1500-word article in < 30 seconds, all fields populated correctly

- [ ] T316 [US3] ⏳ **Implement batch SEO analysis** in backend/src/services/seo_analyzer/batch_analyzer.py:
  - Method: `analyze_batch(article_ids: List[int]) -> BatchResult`
  - Process articles in parallel (using Celery tasks)
  - Track progress for each article
  - Return summary: {total, completed, failed, errors}
  - **Dependencies**: T315
  - **Est**: 4 hours
  - **Acceptance**: Analyze 100 articles in < 50 minutes (30s each), handle failures gracefully

- [ ] T317 [P] [US3] ⏳ **Implement manual override tracking** in backend/src/services/seo_analyzer/override_tracker.py:
  - Method: `record_override(seo_metadata_id, field, old_value, new_value, editor_id, reason)`
  - Append to manual_overrides JSONB array with timestamp
  - Update seo_metadata.updated_at
  - Track which fields were edited by humans
  - **Dependencies**: T306 (DB ready)
  - **Est**: 3 hours
  - **Acceptance**: Override records stored correctly, history preserved

- [ ] T318 [US3] ⏳ **Create Celery task for async SEO analysis** in backend/src/workers/tasks/analyze_seo.py:
  - Wrapper for SEO Analyzer
  - Progress tracking (update task status)
  - Error handling with retry (max 3 attempts)
  - Update article status: draft → seo_optimizing → seo_complete
  - **Dependencies**: T315
  - **Est**: 3 hours
  - **Acceptance**: Task completes successfully, retries on transient errors, updates article status

#### SEO API Endpoints (T319-T323)

- [ ] T319 [P] [US3] ⏳ **Create SEOMetadata schemas** in backend/src/api/schemas/seo_metadata.py:
  - Schema: SEOMetadataCreate, SEOMetadataUpdate, SEOMetadataResponse
  - Include all fields: seo_title, meta_description, keywords, density, recommendations
  - Validation: title 50-60 chars, description 150-160 chars
  - **Dependencies**: None
  - **Est**: 2 hours
  - **Acceptance**: Schemas validate correctly, match DB model

- [ ] T320 [US3] ⏳ **Implement POST /v1/seo/analyze/{article_id}** endpoint in backend/src/api/routes/seo.py:
  - Trigger SEO analysis for specific article
  - Return task_id for async tracking OR immediate result if sync
  - Check article exists and is not already seo_optimized (or allow re-analysis)
  - **Dependencies**: T318 (Celery task), T319 (schemas)
  - **Est**: 3 hours
  - **Acceptance**: Endpoint triggers analysis, returns task_id, handles errors (article not found, etc.)

- [ ] T321 [US3] ⏳ **Implement GET /v1/seo/metadata/{article_id}** endpoint in backend/src/api/routes/seo.py:
  - Retrieve SEO metadata for article
  - Return 404 if not analyzed yet
  - Include manual_overrides in response
  - **Dependencies**: T319 (schemas)
  - **Est**: 2 hours
  - **Acceptance**: Returns metadata correctly, handles missing data

- [ ] T322 [US3] ⏳ **Implement PUT /v1/seo/metadata/{article_id}** endpoint in backend/src/api/routes/seo.py:
  - Allow manual editing of SEO fields
  - Accept: seo_title, meta_description, focus_keyword (only these editable)
  - Record override using T317 override tracker
  - **Dependencies**: T317 (override tracker), T319 (schemas)
  - **Est**: 3 hours
  - **Acceptance**: Updates saved, overrides tracked, validation enforced

- [ ] T323 [US3] ⏳ **Implement POST /v1/seo/analyze/batch** endpoint in backend/src/api/routes/seo.py:
  - Accept list of article_ids OR filter (e.g., all articles with seo_optimized=FALSE)
  - Trigger batch analysis using T316
  - Return batch_task_id for progress tracking
  - **Dependencies**: T316 (batch analyzer)
  - **Est**: 3 hours
  - **Acceptance**: Triggers batch analysis, returns task_id, limits batch size to 1000

#### SEO Testing (T324-T325)

- [ ] T324 [US3] ⏳ **Create SEO accuracy benchmark test** in backend/tests/services/seo_analyzer/test_accuracy.py:
  - Collect 20 test articles with expert-written SEO metadata (baseline)
  - Run SEO analyzer on each article
  - Compare keywords: count matches / total * 100 (target: 85%+)
  - Report accuracy metrics
  - **Dependencies**: T315 (analyzer ready)
  - **Est**: 6 hours
  - **Acceptance**: Accuracy report generated, 85%+ keyword match vs expert baseline

- [ ] T325 [US3] ⏳ **Create SEO performance test** in backend/tests/services/seo_analyzer/test_performance.py:
  - Test analysis duration for various article lengths (500, 1000, 1500, 2000 words)
  - Verify 95% of articles analyzed in < 30 seconds
  - Test batch processing (100 articles in < 50 minutes)
  - **Dependencies**: T315 (analyzer), T316 (batch)
  - **Est**: 4 hours
  - **Acceptance**: Performance SLA met, no degradation with load

**Week 3-4 Checkpoint**: SEO analysis working, 85%+ accuracy, < 30s per article, batch processing functional

---

### Week 5-7: Computer Use Integration (17 tasks)

#### Computer Use Publisher Service (T326-T335)

- [ ] T326 [P] [US4] ⏳ **Setup Chrome/Chromium environment** for Computer Use:
  - Install Chrome/Chromium in Docker container
  - Configure headless mode
  - Setup sandbox environment (isolated from host)
  - Test basic Claude Computer Use API connectivity
  - **Dependencies**: None
  - **Est**: 4 hours
  - **Acceptance**: Chrome launches in container, Computer Use API can control it

- [ ] T327 [P] [US4] ⏳ **Implement WordPress login automation** in backend/src/services/computer_use_publisher/wordpress_login.py:
  - Method: `login(url, username, password) -> Session`
  - Navigate to /wp-admin
  - Fill username and password fields
  - Click login button
  - Verify success (check for dashboard URL or welcome message)
  - Capture screenshot: login_success.png
  - Handle failures: wrong credentials (retry 3 times), CAPTCHA (fail and alert)
  - **Dependencies**: T326 (Chrome ready)
  - **Est**: 6 hours
  - **Acceptance**: Successfully logs into test WordPress, captures screenshot, handles login failures

- [ ] T328 [US4] ⏳ **Implement post creation workflow** in backend/src/services/computer_use_publisher/post_creator.py:
  - Method: `create_post(session) -> PostEditor`
  - Navigate to /wp-admin/post-new.php
  - Wait for editor to load (Gutenberg or Classic)
  - Detect editor type (check for .block-editor vs .wp-editor)
  - Return editor context
  - Capture screenshot: editor_loaded.png
  - **Dependencies**: T327 (logged in session)
  - **Est**: 4 hours
  - **Acceptance**: Navigates to new post, detects editor type, screenshot captured

- [ ] T329 [US4] ⏳ **Implement content filling** in backend/src/services/computer_use_publisher/content_filler.py:
  - Method: `fill_content(editor, title, body) -> None`
  - Fill title field (usually #post-title-0 or .editor-post-title__input)
  - Fill body content (Gutenberg: add paragraph blocks, Classic: paste into editor)
  - Handle HTML formatting (preserve headings, lists, bold, italic)
  - Verify content filled (check field values)
  - Capture screenshot: content_filled.png
  - **Dependencies**: T328 (post created)
  - **Est**: 6 hours
  - **Acceptance**: Title and body filled correctly, HTML formatting preserved, screenshot shows filled content

- [ ] T330 [US4] ⏳ **Implement image upload automation** in backend/src/services/computer_use_publisher/image_uploader.py:
  - Method: `upload_featured_image(session, image_url) -> ImageID`
  - Click "Set featured image" button
  - Navigate to Upload tab
  - Download image from URL to temp file
  - Upload file via file input
  - Wait for upload complete
  - Select uploaded image
  - Set as featured image
  - Capture screenshot: image_uploaded.png
  - **Dependencies**: T328 (post created)
  - **Est**: 8 hours
  - **Acceptance**: Featured image uploaded and set, handles multiple images, screenshot verification

- [ ] T331 [US4] ⏳ **Implement SEO plugin field population** in backend/src/services/computer_use_publisher/seo_plugin_filler.py:
  - Method: `fill_yoast_seo(seo_metadata) -> None` (for Yoast SEO)
  - Method: `fill_rankmath_seo(seo_metadata) -> None` (for Rank Math)
  - Detect installed SEO plugin (check for plugin meta boxes)
  - Fill SEO title field
  - Fill meta description field
  - Fill focus keyword field
  - Add primary keywords (tags or separate field depending on plugin)
  - Capture screenshot: seo_fields_filled.png
  - **Dependencies**: T328 (post created)
  - **Est**: 8 hours (most critical and complex)
  - **Acceptance**: SEO fields populated correctly for both Yoast and Rank Math, screenshot shows filled fields

- [ ] T332 [US4] ⏳ **Implement category and tag assignment** in backend/src/services/computer_use_publisher/taxonomy_setter.py:
  - Method: `set_categories(categories: List[str]) -> None`
  - Method: `set_tags(tags: List[str]) -> None`
  - Open category panel (usually in sidebar)
  - Check existing categories or create new
  - Open tag panel
  - Type tags (comma-separated) or add individually
  - Capture screenshot: taxonomy_set.png
  - **Dependencies**: T328 (post created)
  - **Est**: 5 hours
  - **Acceptance**: Categories and tags assigned, new ones created if needed, screenshot verification

- [ ] T333 [US4] ⏳ **Implement publish action** in backend/src/services/computer_use_publisher/publisher.py:
  - Method: `publish_post(session) -> PostURL`
  - Click "Publish" button (may require 2 clicks in Gutenberg)
  - Wait for success notification
  - Extract post ID from URL or response
  - Navigate to live post URL
  - Verify post is published (check for content visibility)
  - Capture screenshots: publish_clicked.png, article_live.png
  - **Dependencies**: T329-T332 (all content filled)
  - **Est**: 5 hours
  - **Acceptance**: Post published successfully, post ID retrieved, live URL verified, screenshots captured

- [ ] T334 [US4] ⏳ **Implement retry logic with exponential backoff** in backend/src/services/computer_use_publisher/retry_handler.py:
  - Detect transient failures: network timeout, element not found (temporary), slow loading
  - Retry strategy: 10s delay → 30s delay → 90s delay (max 3 retries)
  - Track retry count in publish_tasks table
  - Log each retry attempt to execution_logs
  - Stop retrying on permanent failures: login failure after 3 attempts, post already published
  - **Dependencies**: None (used by all previous tasks)
  - **Est**: 4 hours
  - **Acceptance**: Retries transient errors correctly, exponential backoff working, permanent errors fail fast

- [ ] T335 [US4] ⏳ **Implement Computer Use Publisher orchestrator** in backend/src/services/computer_use_publisher/publisher_service.py:
  - Method: `publish_article(article_id) -> PublishResult`
  - Orchestrate full workflow:
    1. Login (T327)
    2. Create post (T328)
    3. Fill content (T329)
    4. Upload images if present (T330)
    5. Fill SEO fields (T331)
    6. Set categories/tags (T332)
    7. Publish (T333)
  - Log each step to execution_logs table
  - Capture all 8 screenshots
  - Store screenshots to S3/local storage
  - Update publish_tasks status throughout
  - Handle errors at each step with retry logic (T334)
  - Return: {success: bool, post_id: str, post_url: str, duration_seconds: int, screenshots: List}
  - **Dependencies**: T327-T334
  - **Est**: 8 hours
  - **Acceptance**: Complete workflow executes successfully, all screenshots captured, errors handled gracefully

#### Execution Logging & Storage (T336-T338)

- [ ] T336 [P] [US4] ⏳ **Implement execution logging service** in backend/src/services/computer_use_publisher/execution_logger.py:
  - Method: `log_action(task_id, action, target_element, payload, result) -> LogID`
  - Insert into execution_logs table (automatically partitioned by month)
  - Include timestamp, action type, target element, payload (JSONB), result (success/failure/retry)
  - Never log WordPress credentials (sanitize payload)
  - **Dependencies**: T304 (execution_logs table ready)
  - **Est**: 3 hours
  - **Acceptance**: Logs inserted correctly into current month partition, credentials never logged

- [ ] T337 [P] [US4] ⏳ **Implement screenshot storage service** in backend/src/services/computer_use_publisher/screenshot_storage.py:
  - Method: `store_screenshot(task_id, step_name, screenshot_data) -> URL`
  - Support local filesystem storage (default for dev)
  - Support S3-compatible storage (MinIO or AWS S3 for production)
  - Filename format: `screenshots/task_{task_id}/{step_name}_{timestamp}.png`
  - Store URLs in publish_tasks.screenshots JSONB
  - **Dependencies**: None
  - **Est**: 4 hours
  - **Acceptance**: Screenshots stored to configured backend, URLs returned correctly, accessible via HTTP

- [ ] T338 [US4] ⏳ **Implement credential sanitization** in backend/src/services/computer_use_publisher/credential_sanitizer.py:
  - Method: `sanitize_payload(payload: dict) -> dict`
  - Remove keys: password, secret, token, api_key, credential
  - Redact values: replace with "***REDACTED***"
  - Never log CMS_PASSWORD in any logs or screenshots
  - **Dependencies**: None
  - **Est**: 2 hours
  - **Acceptance**: All credential fields removed from logs, tested with various payloads

#### Publishing API Endpoints (T339-T342)

- [ ] T339 [P] [US4] ⏳ **Create PublishTask schemas** in backend/src/api/schemas/publish_task.py:
  - Schema: PublishTaskCreate, PublishTaskResponse, PublishTaskUpdate
  - Include: task_id, article_id, status, screenshots, retry_count, error_message, duration_seconds
  - **Dependencies**: None
  - **Est**: 2 hours
  - **Acceptance**: Schemas match DB model, validation working

- [ ] T340 [US4] ⏳ **Implement POST /v1/publish/submit** endpoint in backend/src/api/routes/publish.py:
  - Accept article_id in request body
  - Validate article exists and has SEO metadata
  - Create publish_task in database (status='pending')
  - Trigger Computer Use Publisher Celery task (T342)
  - Return task_id for tracking
  - **Dependencies**: T339 (schemas), T303 (publish_tasks table)
  - **Est**: 3 hours
  - **Acceptance**: Creates task, triggers async publishing, returns task_id

- [ ] T341 [US4] ⏳ **Implement GET /v1/publish/tasks/{task_id}** endpoint in backend/src/api/routes/publish.py:
  - Retrieve publish task by ID
  - Return status, progress, error_message if failed
  - Include screenshot URLs
  - Include duration_seconds if completed
  - **Dependencies**: T339 (schemas)
  - **Est**: 2 hours
  - **Acceptance**: Returns task details, handles missing tasks (404)

- [ ] T342 [US4] ⏳ **Create Celery task for async publishing** in backend/src/workers/tasks/publish_article.py:
  - Wrapper for Computer Use Publisher (T335)
  - Update publish_task status: pending → in_progress → completed/failed
  - Track progress for each step
  - Store screenshots to S3/local
  - Log all actions to execution_logs
  - Update article.cms_article_id with WordPress post ID
  - Update article.published_at timestamp
  - Send notification on completion/failure
  - **Dependencies**: T335 (publisher ready), T336 (logging), T337 (storage)
  - **Est**: 5 hours
  - **Acceptance**: Task completes successfully, updates all fields, handles failures with retry

**Week 5-7 Checkpoint**: Computer Use publishing working, 8 screenshots captured, success rate 95%+

---

### Week 8: Integration Testing & Optimization (4 tasks)

#### E2E Fusion Workflow Tests (T343-T346)

- [ ] T343 [Phase 5] ⏳ **E2E Test 1: AI Generation → SEO → Publishing** in backend/tests/e2e/test_fusion_ai_workflow.py:
  - Step 1: Submit topic via POST /v1/topics
  - Step 2: Wait for article generation (poll GET /v1/topics/{id})
  - Step 3: Trigger SEO analysis POST /v1/seo/analyze/{article_id}
  - Step 4: Verify SEO metadata GET /v1/seo/metadata/{article_id}
  - Step 5: Submit publish task POST /v1/publish/submit
  - Step 6: Wait for publishing (poll GET /v1/publish/tasks/{task_id})
  - Step 7: Verify WordPress post published (check post URL)
  - Step 8: Verify all 8 screenshots captured
  - **Dependencies**: T310 (import), T323 (SEO API), T342 (publish task)
  - **Est**: 6 hours
  - **Acceptance**: Complete workflow passes, article published to WordPress, all steps verified

- [ ] T344 [Phase 5] ⏳ **E2E Test 2: Import → SEO → Publishing** in backend/tests/e2e/test_fusion_import_workflow.py:
  - Step 1: Import article from CSV POST /v1/articles/import
  - Step 2: Verify article imported with source='imported'
  - Step 3-8: Same as T343 (SEO → Publishing)
  - Verify imported articles work through full pipeline
  - **Dependencies**: T310 (import), T323 (SEO API), T342 (publish task)
  - **Est**: 5 hours
  - **Acceptance**: Imported article published successfully, no errors specific to imported content

- [ ] T345 [Phase 5] ⏳ **E2E Test 3: Concurrent publishing (3+ tasks)** in backend/tests/e2e/test_concurrent_publishing.py:
  - Create 3 articles (AI-generated or imported)
  - Trigger SEO analysis for all 3 in parallel
  - Submit all 3 for publishing simultaneously
  - Verify all 3 publish successfully
  - Check for race conditions, resource conflicts
  - **Dependencies**: T342 (publish task)
  - **Est**: 5 hours
  - **Acceptance**: All 3 articles publish successfully, no conflicts, screenshots for all tasks

- [ ] T346 [Phase 5] ⏳ **Performance optimization and benchmarking** in backend/tests/performance/:
  - Database query optimization: EXPLAIN ANALYZE all SEO and publishing queries
  - API response time tuning: p95 < 500ms for all endpoints
  - Celery worker scaling: test with 10 concurrent tasks
  - Screenshot storage optimization: test S3 upload speeds
  - Generate performance report
  - **Dependencies**: All Phase 5 tasks
  - **Est**: 8 hours (includes optimization work)
  - **Acceptance**: All SLAs met (SEO < 30s, publishing < 5min, API < 500ms), performance report generated

**Week 8 Checkpoint**: All E2E tests passing, performance optimized, system ready for production

---

### Week 9: Production Deployment (2 tasks)

#### Production Deployment (T347-T348)

- [ ] T347 [Phase 5] ⏳ **Production deployment execution**:
  - Build production Docker images
  - Run database migration (Phase 5 schema) on production DB
  - Deploy backend services (API, Celery workers with Computer Use)
  - Deploy frontend build
  - Configure Nginx reverse proxy
  - Setup S3/MinIO for screenshot storage
  - Run smoke tests in production
  - Verify all services healthy
  - **Dependencies**: T301-T346 (all Phase 5 tasks complete)
  - **Est**: 8 hours
  - **Acceptance**: Zero downtime deployment, all services healthy, smoke tests pass

- [ ] T348 [Phase 5] ⏳ **Monitoring and alerting setup**:
  - Setup Grafana dashboards:
    - Import throughput (articles/hour)
    - SEO analysis throughput (articles/hour)
    - Publishing success rate (%)
    - Screenshot storage size (GB)
    - API latency (p50, p95, p99)
    - Celery queue depth
  - Configure alerts (PagerDuty + Slack):
    - Critical: Computer Use credential exposure detected, publishing success < 80%, API error rate > 5%
    - Warning: SEO accuracy < 85%, screenshot storage > 400GB, queue depth > 50
  - Setup log aggregation (CloudWatch or ELK)
  - Create runbook for common operations
  - **Dependencies**: T347 (deployed)
  - **Est**: 6 hours
  - **Acceptance**: Dashboards operational, alerts firing correctly (test with simulated failures), runbook validated

**Week 9 Checkpoint**: Production deployment complete, monitoring active, system operational

---

## Summary: Phase 5 Tasks

**Total Tasks**: 48 (T301-T348)
**Duration**: 8-9 weeks
**Estimated Hours**: ~220 hours

### By Week:
- **Week 1-2** (T301-T310): Database + Import - 10 tasks, 32 hours
- **Week 3-4** (T311-T325): SEO Engine - 15 tasks, 58 hours
- **Week 5-7** (T326-T342): Computer Use - 17 tasks, 83 hours
- **Week 8** (T343-T346): Integration Testing - 4 tasks, 24 hours
- **Week 9** (T347-T348): Deployment - 2 tasks, 14 hours

### By User Story:
- **US2** (External Import): T307-T310 (4 tasks)
- **US3** (SEO Optimization): T311-T325 (15 tasks)
- **US4** (Computer Use Publishing): T326-T342 (17 tasks)
- **Infrastructure**: T301-T306 (6 tasks)
- **Integration**: T343-T346 (4 tasks)
- **Deployment**: T347-T348 (2 tasks)

### Critical Path:
1. Database migration (T301-T306) → Blocks everything
2. Import service (T307-T310) → Blocks import workflow tests
3. SEO analyzer (T311-T318) → Blocks publishing
4. Computer Use publisher (T326-T335) → Blocks publishing
5. Integration tests (T343-T346) → Blocks production deployment

### Parallel Work Opportunities:
- CSV parser (T307-T308) can start before DB migration complete
- SEO keyword extraction (T311) can start in parallel with import work
- Chrome setup (T326) can start early
- All [P] marked tasks can run in parallel

---

## Dependencies Summary

**External Dependencies**:
- Anthropic Claude API (Messages API + Computer Use API)
- WordPress test instance (for integration testing)
- Chrome/Chromium browser (for Computer Use)
- S3-compatible storage (for screenshot storage)

**Internal Dependencies**:
- Phase 1-4 must be complete before Phase 5 starts
- Database migration (T301-T306) must complete before most Phase 5 work
- SEO analysis must complete before publishing can include SEO fields
- Computer Use environment setup before any publishing tests

---

## Acceptance Criteria Summary

**Phase 5 Complete When**:
- ✅ Database extended with source, seo_optimized fields and 3 new tables
- ✅ Can import 100 articles from CSV in < 5 minutes
- ✅ SEO analysis achieves 85%+ keyword accuracy vs expert baseline
- ✅ SEO metadata generation completes in < 30 seconds
- ✅ Computer Use publishes to WordPress in < 5 minutes with 95%+ success rate
- ✅ All 8 screenshots captured per publishing task
- ✅ Zero WordPress credentials exposed in logs/screenshots
- ✅ 3 E2E fusion workflow tests passing
- ✅ Performance benchmarks met (all SLAs)
- ✅ Production deployment successful with zero downtime
- ✅ Monitoring dashboards operational

---

*End of Tasks Document - AI-Powered CMS Automation with SEO Optimization (Fusion Architecture)*
