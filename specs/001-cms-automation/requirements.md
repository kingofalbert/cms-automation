# Requirements Checklist: CMS Automation Platform

**Feature**: 001-cms-automation
**Version**: 1.0.0
**Last Updated**: 2025-10-26

---

## Overview

This document provides a comprehensive checklist of all functional and non-functional requirements for the CMS Automation Platform. Use this checklist to verify completeness during implementation and testing.

**Architecture**: Multi-provider Computer Use (Anthropic / Gemini / Playwright) + AI Proofreading Guard Rails
**Core Workflow**: Import → Proofread & SEO（单一 Prompt + 脚本合并）→ Publish

---

## Functional Requirements (45 Total)

### 1. Article Import (Requirements: FR-001 to FR-010)

- [ ] **FR-001**: System accepts CSV files for batch article import
  - Required columns: `title`, `body`
  - Optional columns: `source`, `featured_image_url`, `additional_images`, `metadata`

- [ ] **FR-002**: System accepts JSON files for batch article import
  - Array of article objects with same schema as CSV

- [ ] **FR-003**: System accepts single article import via API
  - POST /v1/articles/import with JSON body

- [ ] **FR-004**: HTML content is sanitized to prevent XSS attacks
  - Uses bleach library with whitelist of safe tags
  - Removes script, iframe, object, embed, form tags
  - Removes dangerous attributes (onclick, onerror, etc.)

- [ ] **FR-005**: Imported articles are validated before saving
  - Title: 10-500 characters
  - Body: non-empty
  - Source: string identifier
  - Report validation errors with row numbers

- [ ] **FR-006**: Batch import creates async job for 10+ articles
  - Returns job_id for status polling
  - Processes articles in background via Celery

- [ ] **FR-007**: Batch import completes within performance SLA
  - 100 articles < 5 minutes
  - 1000 articles < 30 minutes

- [ ] **FR-008**: Featured images are downloaded and stored locally
  - From featured_image_url if provided
  - Stored in /storage/articles/{article_id}/featured.{ext}

- [ ] **FR-009**: Articles have `source` field to track origin
  - Values: "csv_import", "json_import", "manual", "wordpress_export"

- [ ] **FR-010**: Import results include summary statistics
  - imported_count, skipped_count, failed_count
  - List of validation errors with details

### 2. SEO Optimization (Requirements: FR-011 to FR-020)

- [ ] **FR-011**: System运行单一 Prompt 的 ProofreadingAnalysisService，输出统一校对+SEO结果
  - 使用 Claude Messages API (claude-3-5-sonnet-20241022)
  - 返回结构包含：`issues[]`, `suggested_content`, `seo_metadata`, `processing_metadata`
  - `issues[]` 遵循 schema：`rule_id`, `category`, `severity`, `confidence`, `source (ai|script|merged)`, `blocks_publish`, `suggestion`
  - `statistics` 需包含 `total_issues`, `blocking_issue_count`, `source_breakdown`
  - `processing_metadata` 记录 `prompt_hash`, `ai_model`, `latency_ms`, `rule_manifest_version`, `script_engine_version`
  - AI 无法输出 JSON 时需返回错误并记录日志

- [ ] **FR-011a**: DeterministicRuleEngine 补强 F 类发布合规与高置信度规则
  - 必须覆盖：B2-002 半角逗号、F1-002 特色图横向、F2-001 标题层级
  - 命中 F 类规则时 `blocks_publish=true` 并写入 `articles.critical_issues_count`
  - Rule Engine 版本号记录在 `processing_metadata.script_engine_version`
  - 支持后续扩展更多规则（配置化 / 插件化）

- [ ] **FR-012**: SEO metadata includes meta title (50-60 characters)
  - Focus keyword appears near beginning
  - Includes brand name or year for freshness

- [ ] **FR-013**: SEO metadata includes meta description (150-160 characters)
  - Contains focus keyword
  - Includes call-to-action verb

- [ ] **FR-014**: SEO metadata includes focus keyword
  - 1-3 words representing main topic
  - Must appear in title and first paragraph

- [ ] **FR-015**: SEO metadata includes 3-5 primary keywords
  - Main topics covered in article
  - Semantic analysis via Claude

- [ ] **FR-016**: SEO metadata includes 5-10 secondary keywords
  - Supporting topics and related terms

- [ ] **FR-017**: Keyword density is calculated and stored
  - JSONB field with keyword → {count, density} mapping
  - Target density: 1-3%

- [ ] **FR-018**: Readability score is calculated
  - Flesch Reading Ease formula
  - Target: 60-70 (8th-9th grade level)

- [ ] **FR-019**: SEO analysis completes within SLA
  - 1500-word article: < 30 seconds
  - 5000-word article: < 60 seconds

- [ ] **FR-020**: Manual SEO overrides are supported
  - PUT /v1/seo/metadata/{article_id}
  - Changes tracked in manual_overrides JSONB field

### 3. Multi-Provider Publishing (Requirements: FR-021 to FR-035)

- [ ] **FR-021**: System supports 3 publishing providers
  - Playwright (default, free)
  - Anthropic Computer Use (AI-driven)
  - Gemini Computer Use (future support)

- [ ] **FR-022**: Provider selection is configurable
  - Via environment variable COMPUTER_USE_PROVIDER
  - Via API request body "provider" field

- [ ] **FR-023**: Playwright provider implements browser automation
  - Uses Playwright library for Chrome/Chromium
  - Deterministic script-based automation

- [ ] **FR-024**: Anthropic provider uses Computer Use API
  - Uses claude-3-5-sonnet-20241022 model
  - AI-driven adaptive automation

- [ ] **FR-025**: Publishing workflow includes 8 core steps
  - Login to WordPress admin
  - Create new post
  - Fill title and body
  - Upload featured image
  - Populate SEO fields (Yoast/Rank Math)
  - Set categories and tags
  - Publish article
  - Verify article is live

- [ ] **FR-026**: Screenshots are captured for all major steps
  - Minimum 8 screenshots per task
  - Stored with step name, URL, timestamp, description

- [ ] **FR-027**: Screenshots are stored durably
  - Local storage: /storage/screenshots/{task_id}/{step}.png
  - S3 storage: s3://{bucket}/{year}/{month}/{day}/task_{id}/{step}.png

- [ ] **FR-028**: Execution logs record all actions
  - Log level, step name, message, action type, target, result, timestamp
  - Partitioned by month for performance

- [ ] **FR-029**: Publishing completes within provider SLA
  - Playwright: < 2 minutes
  - Anthropic: < 5 minutes

- [ ] **FR-030**: Publishing success rate meets SLA
  - Playwright: ≥ 99%
  - Anthropic: ≥ 95%

- [ ] **FR-031**: Cost is tracked per publishing task
  - Playwright: $0.00
  - Anthropic: $1.00-$1.50 (tracked via cost_usd field)

- [ ] **FR-032**: Failed tasks can be retried
  - Max 3 retries by default
  - Exponential backoff: 1min, 2min, 4min

- [ ] **FR-033**: Provider fallback logic is implemented
  - If Anthropic fails 3 consecutive times → fallback to Playwright
  - Fallback logged with reason

- [ ] **FR-034**: Published articles include live URL
  - published_url field populated on success
  - Verified via HTTP GET request (200 OK)

- [ ] **FR-035**: WordPress SEO plugin detection
  - Auto-detect Yoast SEO, Rank Math, All in One SEO
  - Use appropriate selectors for each plugin

### 4. API Endpoints (Requirements: FR-036 to FR-045)

- [ ] **FR-036**: POST /v1/articles/import - Single article import

- [ ] **FR-037**: POST /v1/articles/import/batch - Batch CSV/JSON import

- [ ] **FR-038**: GET /v1/articles - List articles with pagination
  - Filters: status, source
  - Pagination: page, limit (default 20, max 100)

- [ ] **FR-039**: GET /v1/articles/{article_id} - Get article details

- [ ] **FR-040**: POST /v1/seo/analyze/{article_id} - Generate SEO metadata

- [ ] **FR-041**: GET /v1/seo/metadata/{article_id} - Get SEO metadata

- [ ] **FR-042**: PUT /v1/seo/metadata/{article_id} - Update SEO metadata (manual override)

- [ ] **FR-043**: POST /v1/publish/submit - Submit publishing task
  - Request body: article_id, provider, cms_config, post_config

- [ ] **FR-044**: GET /v1/publish/tasks/{task_id} - Get task status
  - Returns: status, screenshots, cost, duration

- [ ] **FR-045**: GET /v1/publish/tasks/{task_id}/logs - Get execution logs
  - Filters: log_level
  - Pagination: limit (default 100, max 1000)

---

## Non-Functional Requirements (15 Total)

### 1. Performance (NFR-001 to NFR-005)

- [ ] **NFR-001**: Article import throughput
  - 100 articles in < 5 minutes
  - 1000 articles in < 30 minutes

- [ ] **NFR-002**: SEO analysis latency
  - 1500-word article: < 30 seconds
  - 5000-word article: < 60 seconds

- [ ] **NFR-003**: Publishing latency
  - Playwright: < 2 minutes per article
  - Anthropic: < 5 minutes per article

- [ ] **NFR-004**: Concurrent request handling
  - 10+ concurrent imports
  - 20+ concurrent SEO analyses
  - 20+ concurrent Playwright publishes
  - 10+ concurrent Anthropic publishes

- [ ] **NFR-005**: API response time
  - GET endpoints: < 200ms (p95)
  - POST endpoints: < 500ms (p95)

### 2. Reliability (NFR-006 to NFR-008)

- [ ] **NFR-006**: Publishing success rate
  - Playwright: ≥ 99%
  - Anthropic: ≥ 95%

- [ ] **NFR-007**: Database availability
  - PostgreSQL uptime: ≥ 99.9%
  - Connection pool: 20 connections, no exhaustion

- [ ] **NFR-008**: Task queue reliability
  - Redis uptime: ≥ 99.9%
  - Celery workers: auto-restart on failure

### 3. Security (NFR-009 to NFR-012)

- [ ] **NFR-009**: Credential protection
  - WordPress passwords not logged in plain text
  - Screenshots do not capture password fields
  - Execution logs sanitize sensitive fields
  - API keys masked in logs (show first 8 chars only)

- [ ] **NFR-010**: HTML sanitization
  - Imported HTML sanitized via bleach library
  - XSS prevention: no script, iframe, onclick, onerror

- [ ] **NFR-011**: Database connection security
  - Connection strings use environment variables
  - TLS/SSL encryption for production connections

- [ ] **NFR-012**: API authentication (future)
  - JWT-based authentication
  - Role-based access control (RBAC)

### 4. Observability (NFR-013 to NFR-015)

- [ ] **NFR-013**: Structured logging
  - JSON format for all logs
  - Log levels: DEBUG, INFO, WARNING, ERROR
  - Contextual fields: task_id, article_id, provider, cost

- [ ] **NFR-014**: Monitoring dashboards
  - Flower dashboard for Celery tasks
  - Prometheus + Grafana for metrics (future)

- [ ] **NFR-015**: Screenshot retention
  - Local storage: 90 days
  - S3 storage: 90 days → Glacier (30 days) → delete (90 days)
  - Execution logs: 6 months retention

---

## Database Schema Requirements (8 Total)

- [ ] **DB-001**: articles table with required fields
  - id, title, body, source, status, featured_image_path, created_at, updated_at

- [ ] **DB-002**: seo_metadata table with constraints
  - meta_title: 50-60 chars
  - meta_description: 150-160 chars
  - primary_keywords: 3-5 items
  - secondary_keywords: 5-10 items

- [ ] **DB-003**: publish_tasks table with provider enum
  - provider: enum('anthropic', 'gemini', 'playwright')
  - status: enum('pending', 'running', 'completed', 'failed')

- [ ] **DB-004**: execution_logs table partitioned by month
  - Partition by created_at for efficient pruning
  - Auto-create partitions via cron job

- [ ] **DB-005**: JSONB fields for flexible metadata
  - articles.article_metadata
  - seo_metadata.keyword_density
  - publish_tasks.screenshots
  - execution_logs.details

- [ ] **DB-006**: Indexes for query optimization
  - articles(status), articles(source), articles(created_at)
  - seo_metadata(article_id)
  - publish_tasks(article_id), publish_tasks(provider), publish_tasks(status)
  - execution_logs(task_id, created_at)

- [ ] **DB-007**: Foreign key constraints
  - seo_metadata.article_id → articles.id (ON DELETE CASCADE)
  - publish_tasks.article_id → articles.id (ON DELETE CASCADE)
  - execution_logs.task_id → publish_tasks.id (ON DELETE CASCADE)

- [ ] **DB-008**: Database triggers for auto-updates
  - update_updated_at() on articles, seo_metadata
  - update_article_status_on_seo() when SEO metadata created
  - update_article_status_on_publish() when publish task completed

---

## Testing Requirements (10 Total)

- [ ] **TEST-001**: Unit tests with ≥ 80% code coverage
  - Test all service methods
  - Test all API endpoints
  - Test all database models

- [ ] **TEST-002**: Integration tests for critical paths
  - Import → Database
  - SEO Analysis → Database
  - Publish → WordPress

- [ ] **TEST-003**: E2E test: Import → SEO → Publish (Playwright)
  - Full workflow end-to-end
  - Verify article published to WordPress

- [ ] **TEST-004**: E2E test: Import → SEO → Publish (Anthropic)
  - Test AI-driven publishing
  - Verify cost tracking

- [ ] **TEST-005**: E2E test: Concurrent publishing (5+ tasks)
  - Verify no timeouts or race conditions
  - Verify all tasks complete within SLA

- [ ] **TEST-006**: E2E test: Provider fallback
  - Simulate Anthropic failure
  - Verify automatic fallback to Playwright

- [ ] **TEST-007**: Contract tests for API
  - Verify API matches OpenAPI spec (api-spec.yaml)
  - Validate request/response schemas

- [ ] **TEST-008**: Security tests
  - Verify XSS prevention (HTML sanitization)
  - Verify credential protection (no passwords in logs)
  - Verify no SQL injection vulnerabilities

- [ ] **TEST-009**: Performance tests
  - Load testing with 100+ concurrent requests
  - Verify database connection pool does not exhaust
  - Verify Redis queue handles load

- [ ] **TEST-010**: Provider-specific tests
  - Playwright: Test on WordPress 6.4, 6.5, 6.6
  - Anthropic: Test on custom WordPress themes
  - Test SEO plugin detection (Yoast, Rank Math)

---

## Deployment Requirements (5 Total)

- [ ] **DEPLOY-001**: Docker Compose setup for development
  - Services: postgres, redis, backend, frontend, celery, flower
  - All services start and communicate correctly

- [ ] **DEPLOY-002**: Database migrations
  - Alembic migrations for all schema changes
  - Migrations execute without errors
  - Rollback capability

- [ ] **DEPLOY-003**: Environment configuration
  - .env.example provided with all required variables
  - Secrets not committed to repository
  - Validation of required environment variables on startup

- [ ] **DEPLOY-004**: Production deployment (AWS ECS Fargate)
  - ECS service definitions for API and workers
  - RDS PostgreSQL 15
  - ElastiCache Redis 7
  - S3 for screenshot storage
  - ALB for API load balancing

- [ ] **DEPLOY-005**: CI/CD pipeline (GitHub Actions)
  - Automated testing on pull requests
  - Automated deployment to staging on merge to main
  - Manual approval for production deployment

---

## Documentation Requirements (5 Total)

- [ ] **DOC-001**: API documentation (Swagger UI)
  - All endpoints documented
  - Request/response examples
  - Authentication requirements

- [ ] **DOC-002**: Quickstart guide (quickstart.md)
  - Local development setup
  - Docker Compose setup
  - Example workflows for all 3 providers

- [ ] **DOC-003**: Architecture documentation (plan.md)
  - Multi-provider architecture diagrams
  - Database schema diagrams
  - Workflow sequence diagrams

- [ ] **DOC-004**: MVP verification (mvp-verification.md)
  - Acceptance criteria for all features
  - E2E test scripts
  - Performance benchmarks

- [ ] **DOC-005**: Requirements checklist (requirements.md)
  - This document
  - Updated as requirements change

---

## Summary

**Total Requirements**: 88

### By Category:
- Functional Requirements: 45
- Non-Functional Requirements: 15
- Database Schema: 8
- Testing: 10
- Deployment: 5
- Documentation: 5

### Completion Status:
- [ ] All 45 functional requirements implemented
- [ ] All 15 non-functional requirements met
- [ ] All 8 database schema requirements satisfied
- [ ] All 10 testing requirements passed
- [ ] All 5 deployment requirements completed
- [ ] All 5 documentation requirements delivered

---

## Verification

### Phase 1: Implementation (Weeks 1-8)
- Review functional requirements FR-001 to FR-045 weekly
- Ensure test coverage for each completed requirement

### Phase 2: Testing (Weeks 9-10)
- Execute all E2E tests (TEST-003 to TEST-006)
- Verify non-functional requirements (NFR-001 to NFR-015)
- Performance benchmarking

### Phase 3: Deployment (Week 11)
- Deploy to staging environment
- Execute smoke tests
- Deploy to production with monitoring

---

## Traceability Matrix

| Requirement ID | User Story | Implementation | Test Coverage |
|----------------|------------|----------------|---------------|
| FR-001 to FR-010 | US-001: Article Import | `src/services/article_importer/` | `tests/unit/test_article_importer.py` |
| FR-011 to FR-020 | US-002: SEO Optimization | `src/services/seo_analyzer/` | `tests/unit/test_seo_analyzer.py` |
| FR-021 to FR-035 | US-003: Multi-Provider Publishing | `src/services/providers/` | `tests/unit/test_providers.py` |
| FR-036 to FR-045 | US-004: API Endpoints | `src/api/v1/` | `tests/integration/test_api.py` |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-26 | Initial requirements checklist for multi-provider architecture |

---

## License

MIT License - See LICENSE file for details
