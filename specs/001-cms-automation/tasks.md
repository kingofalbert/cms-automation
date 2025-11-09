# Tasks: SEO Optimization & Multi-Provider Computer Use Publishing

**Version**: 3.0.0 🆕
**Last Updated**: 2025-11-08
**Status**: Phase 1-3, 6 Complete ✅ | Phase 4-5 Partial ⏳ | Phase 7 Design Complete
**Overall Completion**: ~85% (existing) + Phase 7 Ready for Implementation
**Architecture**: Article Import → SEO Analysis (Messages API) → Multi-Provider Computer Use Publishing → **Article Structured Parsing** 🆕
**Input**: Design documents from `/specs/001-cms-automation/`
**Prerequisites**: plan.md v4.0, spec.md v4.0, data-model.md v4.0, contracts/api-spec.yaml

---

## Overview

This document provides a detailed breakdown of **48+ implementation tasks** organized across **6 phases**. Each task includes:
- **Task ID**: Unique identifier (T1.1, T2.3, etc.)
- **Description**: What needs to be done
- **Dependencies**: Which tasks must complete first
- **Estimated Hours**: Time estimate
- **Deliverables**: Concrete outputs
- **Acceptance Criteria**: Definition of done
- **File Paths**: Exact locations of files to create/modify

**Key Architecture Decisions**:
1. **Multi-Provider Pattern**: Abstract `ComputerUseProvider` base class with three implementations (Anthropic, Gemini, Playwright)
2. **Two-Phase Workflow**: SEO Analysis (Messages API) → Computer Use Publishing (Browser Automation)
3. **Provider Flexibility**: Runtime switching via environment variable or API parameter
4. **Audit Trail**: 8+ screenshots per publishing task stored in S3/local
5. **Cost Optimization**: Playwright as default (free), AI providers as fallback

---

## Path Conventions

Based on plan.md v2.0:
- **Backend**: `backend/src/`, `backend/tests/`, `backend/migrations/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- **Specs**: `specs/001-cms-automation/`
- **Monitoring**: `monitoring/`

---

## Task Format

```
[Task ID] [Priority] [User Story] Task Name
Description: What needs to be done
Dependencies: List of prerequisite tasks
Estimated Hours: X hours
Deliverables:
  - Concrete output 1
  - Concrete output 2
Acceptance Criteria:
  - Measurable success criterion 1
  - Measurable success criterion 2
File Paths:
  - Path to file 1
  - Path to file 2
```

**Symbols**:
- **[P]**: Can run in parallel (no blocking dependencies)
- **[US1-5]**: Maps to User Story in spec.md
- **✅**: Completed
- **⏳**: In Progress
- **[ ]**: Not Started

---

## Phase 0: Governance Compliance Gate (Continuous)

**Purpose**: Ensure Constitution v1.0.0 compliance throughout development
**Status**: Continuous validation

### New Constitution Requirements

#### III.5 - CMS Credential Management
**Requirement**: Encrypted storage, 90-day rotation, complete audit logs

**Tasks**:
- [ ] G0.1 Implement encrypted credentials storage using AWS Secrets Manager or HashiCorp Vault
- [ ] G0.2 Setup 90-day rotation schedule for CMS credentials
- [ ] G0.3 Log all credential access to audit_logs table
- [ ] G0.4 Mask passwords in all logs and screenshots
- [ ] G0.5 Create credential rotation runbook

#### IV.5 - Computer Use Testing Strategy
**Requirement**: Mock tests, sandbox WordPress, screenshot validation

**Tasks**:
- [ ] G0.6 Setup sandbox WordPress environment in Docker
- [ ] G0.7 Implement mock Computer Use provider for unit tests
- [ ] G0.8 Create screenshot validation tests (verify content, no credentials visible)
- [ ] G0.9 Setup UI regression testing for WordPress selector changes

---

## Phase 1: Database Refactor & Article Import (2 weeks) ✅ COMPLETE

**Goal**: Extend database schema and implement article import from external sources
**Duration**: 2 weeks (Week 1-2)
**Estimated Hours**: 46 hours
**Status**: ✅ **Complete** (100%)
**Evidence**:
- ✅ Database migrations deployed: `/backend/migrations/`
- ✅ 15+ SQLAlchemy models: `/backend/src/models/`
- ✅ Article import service: `/backend/src/services/article_importer/`
- ✅ API routes: `/backend/src/api/routes/import_routes.py` (7,504 lines)

---

### Week 1: Database Schema Design & Migration

#### T1.1 [P] Design New Database Schema ✅

**Description**: Create ER diagram and detailed schema design for 4 core tables: articles (extended), seo_metadata, publish_tasks, execution_logs

**Dependencies**: None

**Estimated Hours**: 8 hours

**Status**: ✅ **Complete**

**Deliverables**:
- ER diagram (Mermaid format) in `specs/001-cms-automation/data-model.md`
- Schema design document with:
  - All columns with types, constraints, defaults
  - JSONB field structures
  - Index definitions
  - Foreign key relationships
  - Partition strategy for execution_logs

**Acceptance Criteria**:
- ER diagram covers all 4 tables
- Schema includes all fields from spec.md section 6.4
- JSONB structures documented
- Reviewed and approved by tech lead

**File Paths**:
- `specs/001-cms-automation/data-model.md`
- `specs/001-cms-automation/diagrams/er-diagram.mmd`

---

#### T1.2 [P] Create Alembic Migration Scripts ✅

**Description**: Write Alembic migration to extend articles table and create 3 new tables (seo_metadata, publish_tasks, execution_logs)

**Dependencies**: T1.1

**Estimated Hours**: 6 hours

**Status**: ✅ **Complete**

**Deliverables**:
- Migration file: `backend/migrations/versions/YYYYMMDD_multi_provider_schema.py`
- Includes:
  - ALTER TABLE articles: Add source, featured_image_path, additional_images, published_url, cms_article_id, article_metadata
  - CREATE TABLE seo_metadata with all columns and constraints
  - CREATE TABLE publish_tasks with provider enum and status tracking
  - CREATE TABLE execution_logs with partitioning by month
  - All indexes and foreign keys
- Rollback logic tested

**Acceptance Criteria**:
- Migration runs successfully on empty database
- Migration runs successfully on database with existing articles
- Rollback restores original schema
- All constraints enforced (checked with invalid data attempts)

**File Paths**:
- `backend/migrations/versions/YYYYMMDD_multi_provider_schema.py`

**Code Example**:
```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ENUM

def upgrade():
    # Extend articles table
    op.add_column('articles', sa.Column('source', sa.String(20), nullable=False, server_default='imported'))
    op.add_column('articles', sa.Column('featured_image_path', sa.String(500)))
    op.add_column('articles', sa.Column('additional_images', JSONB))
    op.add_column('articles', sa.Column('published_url', sa.String(500)))
    op.add_column('articles', sa.Column('cms_article_id', sa.String(100)))
    op.add_column('articles', sa.Column('article_metadata', JSONB))

    # Create status enum
    article_status_enum = ENUM('imported', 'seo_optimized', 'ready_to_publish',
                                'publishing', 'published', name='article_status_enum')
    article_status_enum.create(op.get_bind())

    # Create seo_metadata table
    op.create_table(
        'seo_metadata',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('article_id', sa.Integer(), sa.ForeignKey('articles.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('meta_title', sa.String(60), nullable=False),
        sa.Column('meta_description', sa.String(160), nullable=False),
        sa.Column('focus_keyword', sa.String(100), nullable=False),
        sa.Column('primary_keywords', sa.ARRAY(sa.String(100))),
        sa.Column('secondary_keywords', sa.ARRAY(sa.String(100))),
        sa.Column('keyword_density', JSONB),
        sa.Column('readability_score', sa.Float),
        sa.Column('optimization_recommendations', JSONB),
        sa.Column('manual_overrides', JSONB),
        sa.Column('generated_by', sa.String(50)),
        sa.Column('generation_cost', sa.Float),
        sa.Column('generation_tokens', sa.Integer),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint('char_length(meta_title) >= 50 AND char_length(meta_title) <= 60', name='meta_title_length_check'),
        sa.CheckConstraint('char_length(meta_description) >= 150 AND char_length(meta_description) <= 160', name='meta_description_length_check'),
        sa.CheckConstraint('array_length(primary_keywords, 1) >= 3 AND array_length(primary_keywords, 1) <= 5', name='primary_keywords_count_check'),
        sa.CheckConstraint('array_length(secondary_keywords, 1) >= 5 AND array_length(secondary_keywords, 1) <= 10', name='secondary_keywords_count_check')
    )

    # Create publish_tasks table
    provider_enum = ENUM('anthropic', 'gemini', 'playwright', name='provider_enum')
    provider_enum.create(op.get_bind())

    op.create_table(
        'publish_tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('article_id', sa.Integer(), sa.ForeignKey('articles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_id', sa.String(100), unique=True),  # Celery task ID
        sa.Column('provider', provider_enum, nullable=False, server_default='playwright'),
        sa.Column('cms_type', sa.String(50), server_default='wordpress'),
        sa.Column('cms_url', sa.String(500)),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('max_retries', sa.Integer(), server_default='3'),
        sa.Column('error_message', sa.Text()),
        sa.Column('session_id', sa.String(100)),
        sa.Column('screenshots', JSONB, server_default='[]'),
        sa.Column('cost_usd', sa.Float()),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('duration_seconds', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.CheckConstraint('status IN (\'pending\', \'running\', \'completed\', \'failed\')', name='status_check'),
        sa.CheckConstraint('retry_count <= max_retries', name='retry_count_check')
    )

    # Create execution_logs table with partitioning
    op.execute("""
        CREATE TABLE execution_logs (
            id BIGSERIAL,
            task_id INTEGER NOT NULL REFERENCES publish_tasks(id) ON DELETE CASCADE,
            log_level VARCHAR(10) NOT NULL DEFAULT 'INFO',
            step_name VARCHAR(100),
            message TEXT,
            details JSONB,
            action_type VARCHAR(50),
            action_target TEXT,
            action_result VARCHAR(20),
            screenshot_path VARCHAR(500),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        ) PARTITION BY RANGE (created_at);

        CREATE TABLE execution_logs_2025_10 PARTITION OF execution_logs
        FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

        CREATE INDEX idx_execution_logs_task ON execution_logs(task_id);
        CREATE INDEX idx_execution_logs_created_at ON execution_logs(created_at);
    """)

    # Create indexes
    op.create_index('idx_articles_source', 'articles', ['source'])
    op.create_index('idx_articles_status', 'articles', ['status'])
    op.create_index('idx_seo_metadata_article', 'seo_metadata', ['article_id'])
    op.create_index('idx_seo_metadata_focus_keyword', 'seo_metadata', ['focus_keyword'])
    op.create_index('idx_publish_tasks_article', 'publish_tasks', ['article_id'])
    op.create_index('idx_publish_tasks_status', 'publish_tasks', ['status'])
    op.create_index('idx_publish_tasks_task_id', 'publish_tasks', ['task_id'])

def downgrade():
    # Drop tables in reverse order
    op.drop_table('execution_logs_2025_10')
    op.execute('DROP TABLE execution_logs')
    op.drop_table('publish_tasks')
    op.drop_table('seo_metadata')

    # Drop enums
    op.execute('DROP TYPE provider_enum')
    op.execute('DROP TYPE article_status_enum')

    # Remove columns from articles
    op.drop_column('articles', 'article_metadata')
    op.drop_column('articles', 'cms_article_id')
    op.drop_column('articles', 'published_url')
    op.drop_column('articles', 'additional_images')
    op.drop_column('articles', 'featured_image_path')
    op.drop_column('articles', 'source')
```

---

#### T1.3 [P] Update SQLAlchemy Models ✅

**Description**: Create/update SQLAlchemy ORM models to match new database schema

**Dependencies**: T1.2

**Estimated Hours**: 8 hours

**Status**: ✅ **Complete**

**Deliverables**:
- Updated `backend/src/models/article.py`:
  - Add new fields: source, featured_image_path, additional_images, published_url, cms_article_id, article_metadata
  - Update status enum
  - Add relationship to SEOMetadata (1:1)
  - Add relationship to PublishTask (1:N)
- New `backend/src/models/seo_metadata.py`:
  - All fields with proper types
  - Relationship back to Article
  - Validators for length constraints
- New `backend/src/models/publish_task.py`:
  - All fields including provider enum
  - Relationship to Article
  - Relationship to ExecutionLog (1:N)
- New `backend/src/models/execution_log.py`:
  - Partitioned table support
  - Relationship to PublishTask

**Acceptance Criteria**:
- All models match migration schema exactly
- Relationships work bidirectionally
- Validators enforce constraints
- Can create, read, update, delete records via ORM
- Type hints complete (passes mypy)

**File Paths**:
- `backend/src/models/article.py`
- `backend/src/models/seo_metadata.py`
- `backend/src/models/publish_task.py`
- `backend/src/models/execution_log.py`

**Code Example** (`backend/src/models/seo_metadata.py`):
```python
"""SEO Metadata model."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship, validates

from src.models.base import Base


class SEOMetadata(Base):
    """SEO metadata for articles."""

    __tablename__ = "seo_metadata"

    id = Column(Integer, primary_key=True)
    article_id = Column(
        Integer, ForeignKey("articles.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # SEO fields
    meta_title = Column(String(60), nullable=False)
    meta_description = Column(String(160), nullable=False)
    focus_keyword = Column(String(100), nullable=False)
    primary_keywords = Column(ARRAY(String(100)))
    secondary_keywords = Column(ARRAY(String(100)))
    keyword_density = Column(JSONB)  # {"keyword": {"count": 10, "density": 2.5}}
    readability_score = Column(Float)
    optimization_recommendations = Column(JSONB)  # List of recommendation objects
    manual_overrides = Column(JSONB)  # Track manual edits

    # Generation metadata
    generated_by = Column(String(50))  # "claude-3-5-sonnet-20250101"
    generation_cost = Column(Float)
    generation_tokens = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    article = relationship("Article", back_populates="seo_metadata")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "char_length(meta_title) >= 50 AND char_length(meta_title) <= 60",
            name="meta_title_length_check",
        ),
        CheckConstraint(
            "char_length(meta_description) >= 150 AND char_length(meta_description) <= 160",
            name="meta_description_length_check",
        ),
        CheckConstraint(
            "array_length(primary_keywords, 1) >= 3 AND array_length(primary_keywords, 1) <= 5",
            name="primary_keywords_count_check",
        ),
        CheckConstraint(
            "array_length(secondary_keywords, 1) >= 5 AND array_length(secondary_keywords, 1) <= 10",
            name="secondary_keywords_count_check",
        ),
    )

    @validates("meta_title")
    def validate_meta_title(self, key: str, value: str) -> str:
        """Validate meta title length."""
        if not 50 <= len(value) <= 60:
            raise ValueError("Meta title must be 50-60 characters")
        return value

    @validates("meta_description")
    def validate_meta_description(self, key: str, value: str) -> str:
        """Validate meta description length."""
        if not 150 <= len(value) <= 160:
            raise ValueError("Meta description must be 150-160 characters")
        return value

    @validates("primary_keywords")
    def validate_primary_keywords(self, key: str, value: List[str]) -> List[str]:
        """Validate primary keywords count."""
        if not 3 <= len(value) <= 5:
            raise ValueError("Must have 3-5 primary keywords")
        return value

    @validates("secondary_keywords")
    def validate_secondary_keywords(self, key: str, value: List[str]) -> List[str]:
        """Validate secondary keywords count."""
        if not 5 <= len(value) <= 10:
            raise ValueError("Must have 5-10 secondary keywords")
        return value

    def __repr__(self) -> str:
        """String representation."""
        return f"<SEOMetadata(article_id={self.article_id}, focus_keyword='{self.focus_keyword}')>"
```

---

#### T1.4 Run Migration & Verify ✅

**Description**: Execute migration on dev database and verify all tables, constraints, and indexes created correctly

**Dependencies**: T1.3

**Estimated Hours**: 2 hours

**Status**: ✅ **Complete**

**Deliverables**:
- Migration executed successfully
- Verification script: `backend/scripts/verify_migration.py`
- Verification report showing:
  - All tables exist
  - All columns with correct types
  - All constraints active
  - All indexes created
  - Sample data insertable

**Acceptance Criteria**:
- Migration completes without errors
- All 4 tables exist in database
- Can insert sample article with SEO metadata and publish task
- Foreign keys enforce relationships
- Constraints block invalid data
- Indexes improve query performance (EXPLAIN ANALYZE shows index usage)

**File Paths**:
- `backend/scripts/verify_migration.py`
- `backend/tests/test_migration.py`

---

### Week 2: Article Import Implementation

#### T1.5 [P] Build Article Importer Service

**Description**: Implement service to import articles from CSV/JSON with validation and HTML sanitization

**Dependencies**: T1.4 (DB ready)

**Estimated Hours**: 10 hours

**Deliverables**:
- `backend/src/services/article_importer/csv_parser.py`:
  - Parse CSV with pandas
  - Validate required fields (title, body)
  - Handle optional fields (images, excerpt, category, tags, metadata)
- `backend/src/services/article_importer/json_parser.py`:
  - Parse JSON array or single object
  - Same validation as CSV
- `backend/src/services/article_importer/sanitizer.py`:
  - HTML sanitization with bleach library
  - XSS prevention
  - Preserve safe formatting (headings, lists, links, images)
- `backend/src/services/article_importer/validator.py`:
  - Title: 10-500 characters
  - Body: minimum 100 words
  - Images: valid URLs, max 10 additional images
- `backend/src/services/article_importer/duplicate_detector.py`:
  - Check for duplicate titles (85%+ similarity using difflib)
  - Return list of potential duplicates

**Acceptance Criteria**:
- Parse CSV with 100 articles in < 30 seconds
- Validation catches all invalid inputs (tested with edge cases)
- HTML sanitization blocks all XSS vectors (tested with OWASP XSS test vectors)
- Duplicate detection identifies near-identical titles
- All functions have unit tests with 90%+ coverage

**File Paths**:
- `backend/src/services/article_importer/csv_parser.py`
- `backend/src/services/article_importer/json_parser.py`
- `backend/src/services/article_importer/sanitizer.py`
- `backend/src/services/article_importer/validator.py`
- `backend/src/services/article_importer/duplicate_detector.py`
- `backend/tests/services/article_importer/test_csv_parser.py`
- `backend/tests/services/article_importer/test_sanitizer.py`

**Code Example** (`backend/src/services/article_importer/sanitizer.py`):
```python
"""HTML sanitization for article import."""

import bleach
from typing import Set

# Allowed HTML tags
ALLOWED_TAGS: Set[str] = {
    'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li',
    'a', 'strong', 'em', 'u', 'code', 'pre',
    'blockquote', 'img', 'br', 'hr',
    'table', 'thead', 'tbody', 'tr', 'th', 'td'
}

# Allowed attributes per tag
ALLOWED_ATTRIBUTES: dict = {
    'a': ['href', 'title', 'rel', 'target'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'p': ['class'],
    'h1': ['class'],
    'h2': ['class'],
    'h3': ['class'],
    'h4': ['class'],
    'h5': ['class'],
    'h6': ['class'],
    'code': ['class'],
    'pre': ['class'],
    'blockquote': ['class'],
    'table': ['class'],
}

# Protocols for links and images
ALLOWED_PROTOCOLS: Set[str] = {'http', 'https', 'mailto'}


def sanitize_html(html: str) -> str:
    """Sanitize HTML to prevent XSS attacks.

    Args:
        html: Raw HTML content

    Returns:
        Sanitized HTML content
    """
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True
    )

    # Additional cleaning: remove empty paragraphs
    cleaned = cleaned.replace('<p></p>', '')
    cleaned = cleaned.replace('<p> </p>', '')

    return cleaned.strip()


def strip_html(html: str) -> str:
    """Strip all HTML tags and return plain text.

    Args:
        html: HTML content

    Returns:
        Plain text content
    """
    return bleach.clean(html, tags=set(), strip=True)
```

---

#### T1.6 Implement Article Import API Endpoints

**Description**: Create FastAPI endpoints for single and batch article import

**Dependencies**: T1.5

**Estimated Hours**: 6 hours

**Deliverables**:
- `backend/src/api/schemas/article_import.py`:
  - ArticleImportRequest schema
  - BatchImportResponse schema
- `backend/src/api/routes/articles.py` (extend existing):
  - POST /v1/articles/import (single article, JSON body)
  - POST /v1/articles/import/batch (CSV file upload or JSON array)
  - GET /v1/articles/import/tasks/{task_id} (batch import progress)

**Acceptance Criteria**:
- POST /v1/articles/import accepts JSON and creates article
- POST /v1/articles/import/batch accepts CSV file (multipart/form-data)
- POST /v1/articles/import/batch accepts JSON array (application/json)
- Batch endpoint returns task_id for async processing if > 50 articles
- Returns article IDs, imported count, failed count, error details
- Handles validation errors gracefully (returns 422 with details)
- API documented in OpenAPI spec

**File Paths**:
- `backend/src/api/schemas/article_import.py`
- `backend/src/api/routes/articles.py`
- `backend/tests/api/test_article_import.py`

---

#### T1.7 Build File Storage Service

**Description**: Implement abstraction for file storage supporting local filesystem (dev) and S3 (production)

**Dependencies**: None (can run parallel)

**Estimated Hours**: 8 hours

**Deliverables**:
- `backend/src/services/storage/base.py`:
  - Abstract `FileStorage` base class
  - Methods: upload(), download(), delete(), get_url(), list()
- `backend/src/services/storage/local.py`:
  - `LocalFileStorage` implementation
  - Store files in `uploads/` directory
  - Generate URLs like `/media/uploads/{filename}`
- `backend/src/services/storage/s3.py`:
  - `S3FileStorage` implementation
  - Use boto3 to interact with S3 or MinIO
  - Generate presigned URLs for secure access
- `backend/src/services/storage/factory.py`:
  - `StorageFactory.create()` returns appropriate storage based on env var

**Acceptance Criteria**:
- LocalFileStorage stores files in uploads/ directory
- S3FileStorage uploads to configured S3 bucket
- Both implementations pass same test suite
- File URLs accessible via HTTP
- Factory pattern allows switching storage via STORAGE_BACKEND env var
- Supports image file types: jpg, jpeg, png, gif, webp

**File Paths**:
- `backend/src/services/storage/base.py`
- `backend/src/services/storage/local.py`
- `backend/src/services/storage/s3.py`
- `backend/src/services/storage/factory.py`
- `backend/tests/services/storage/test_storage.py`

---

#### T1.8 Implement Image Upload API

**Description**: Create API endpoint for uploading article images (featured + additional)

**Dependencies**: T1.7

**Estimated Hours**: 4 hours

**Deliverables**:
- `backend/src/api/routes/images.py`:
  - POST /v1/images/upload (multipart/form-data)
  - Returns image ID and URL
  - Validates file type (jpg, jpeg, png, gif, webp)
  - Validates file size (max 5MB)
- `backend/src/services/image_processor.py`:
  - Resize images if > 2000px width
  - Generate thumbnail (300x300)
  - Extract image metadata (dimensions, format)

**Acceptance Criteria**:
- API accepts image files up to 5MB
- Only image types allowed (jpg, png, gif, webp)
- Returns image URL immediately after upload
- Images resized if > 2000px width
- Generates thumbnails for all uploaded images
- Handles upload failures gracefully

**File Paths**:
- `backend/src/api/routes/images.py`
- `backend/src/services/image_processor.py`
- `backend/tests/api/test_image_upload.py`

---

#### T1.9 Write Integration Tests

**Description**: Comprehensive integration tests for article import workflow

**Dependencies**: T1.6, T1.8

**Estimated Hours**: 6 hours

**Deliverables**:
- `backend/tests/integration/test_article_import_workflow.py`:
  - Test 1: Import single article via API
  - Test 2: Import CSV with 10 articles
  - Test 3: Import JSON array with 5 articles
  - Test 4: Upload featured image and attach to article
  - Test 5: Duplicate detection (import same article twice)
  - Test 6: Validation errors (invalid title, missing body)
  - Test 7: HTML sanitization (submit XSS payload, verify cleaned)
  - Test 8: Batch import with > 50 articles (async processing)

**Acceptance Criteria**:
- All 8 tests pass
- Tests cover happy path and error cases
- Integration tests use real database (test DB)
- Tests clean up after themselves (rollback transactions)
- Tests run in < 2 minutes total

**File Paths**:
- `backend/tests/integration/test_article_import_workflow.py`

---

#### T1.10 Documentation

**Description**: Update documentation for article import feature

**Dependencies**: T1.9 (all features implemented)

**Estimated Hours**: 2 hours

**Deliverables**:
- `specs/001-cms-automation/quickstart.md` (updated):
  - Section: "Importing Articles from CSV"
  - CSV format specification
  - Example CSV file
- `backend/README.md` (updated):
  - Article import API endpoints
  - Request/response examples
- `specs/001-cms-automation/api-spec.yaml` (updated):
  - OpenAPI spec for import endpoints

**Acceptance Criteria**:
- Documentation includes CSV format spec with example
- API examples include curl commands
- OpenAPI spec validates correctly

**File Paths**:
- `specs/001-cms-automation/quickstart.md`
- `backend/README.md`
- `specs/001-cms-automation/api-spec.yaml`

---

**Phase 1 Checkpoint**: ✅ Database extended, article import functional, can import 100 articles from CSV in < 5 minutes

---

## Phase 2: Proofreading & SEO Engine (1.5 weeks) ✅ COMPLETE

**Goal**: Implement intelligent SEO metadata generation using Claude Messages API
**Duration**: 1.5 weeks (Week 3-4)
**Estimated Hours**: 52 hours
**Status**: ✅ **Complete** (100%)
**Evidence**:
- ✅ Proofreading system: 384 rules implemented (100% coverage)
- ✅ Deterministic engine: `/backend/src/services/proofreading/deterministic_engine.py` (8,782 lines)
- ✅ AI prompt builder: `/backend/src/services/proofreading/ai_prompt_builder.py`
- ✅ Result merger: `/backend/src/services/proofreading/merger.py`
- ✅ SEO service: `/backend/src/services/proofreading/service.py`
- ✅ Performance: 2.46ms load time, 79.4% auto-fix rate
- ✅ API route: `/backend/src/api/routes/seo_routes.py` (6,178 lines)

---

### Week 3: Proofreading Single Prompt & Merge

#### T2A.1 [US2] Publish Rule Manifest JSON
Description: Convert A–F 规则表到机器可读 `catalog.json`，包含版本、rule_id、severity、blocks_publish 信息，并记录 source 文档。
Dependencies: T1.4 (rules整理)
Estimated Hours: 4h
Deliverables:
  - `backend/src/services/proofreading/rules/catalog.json`
  - `docs/proofreading_rule_manifest.md` 摘要与生成脚本
Acceptance Criteria:
  - Manifest 通过 JSON Schema 校验
  - 覆盖 6 个大类，记录 rule_count 与 fingerprint
  - 在 PromptBuilder 单元测试中引用成功
File Paths:
  - `backend/src/services/proofreading/rules/catalog.json`
  - `backend/tests/services/proofreading/test_manifest.py`

#### T2A.2 [US2] Proofreading Prompt Builder
Description: 实现 `ProofreadingPromptBuilder` 生成 system/user prompts，插入规则表、输出 schema、rule_coverage 指令。
Dependencies: T2A.1
Estimated Hours: 8h
Deliverables:
  - `backend/src/services/proofreading/ai_prompt_builder.py`
  - Unit tests: prompt包含 manifest version/hash、sections、metadata
Acceptance Criteria:
  - PromptBuilder 可接受 ArticlePayload → 返回 dict(system,user)
  - 测试断言：输出 schema 片段存在；rule manifest 表格行数与 JSON 相符
  - 常见 article payload（含图片、关键词）渲染无异常
File Paths:
  - `backend/src/services/proofreading/ai_prompt_builder.py`
  - `backend/tests/services/proofreading/test_prompt_builder.py`

#### T2A.3 [US2] Deterministic Rule Engine v1
Description: 构建脚本规则评估器（B2-002、F1-002、F2-001），输出 `ProofreadingIssue` 列表。
Dependencies: T2A.1
Estimated Hours: 10h
Deliverables:
  - `backend/src/services/proofreading/deterministic_engine.py`
  - Tests: 正例/反例覆盖、blocks_publish 行为
Acceptance Criteria:
  - `run()` 返回 list，字段 `source=script`、`confidence=1.0`
  - F 类命中设置 `blocks_publish=True`
  - 误报率控制：常见合法文本不触发
File Paths:
  - `backend/src/services/proofreading/deterministic_engine.py`
  - `backend/tests/services/proofreading/test_rule_engine.py`

#### T2A.4 [US2] Result Merger & Schema
Description: 实现 `ProofreadingResultMerger`，合并 AI 与脚本结果，去重并汇总统计。
Dependencies: T2A.2, T2A.3
Estimated Hours: 8h
Deliverables:
  - `backend/src/services/proofreading/merger.py`
  - 更新 `api/contracts/api-spec.yaml`：`ProofreadingIssue.source`、`statistics.source_breakdown`
Acceptance Criteria:
  - 同 rule_id 双方命中 → `source=merged` 且保留脚本 severity
  - 生成 `statistics`：total/ai/script/blocking/source_breakdown
  - API schema 更新通过 `speccheck`
File Paths:
  - `backend/src/services/proofreading/merger.py`
  - `specs/001-cms-automation/contracts/api-spec.yaml`

#### T2A.5 [US2] ProofreadingAnalysisService Orchestration
Description: 组合 PromptBuilder + AsyncAnthropic + RuleEngine + Merger，返回统一 `ProofreadingResult`。
Dependencies: T2A.2, T2A.3, T2A.4
Estimated Hours: 10h
Deliverables:
  - `backend/src/services/proofreading/service.py`
  - Integration tests：mock AI 响应 + 脚本命中 → 校验合并、metadata
  - Logging：`prompt_hash`、token usage、latency
Acceptance Criteria:
  - 异常处理：AI JSON 解析失败时抛自定义错误并记录
  - `processing_metadata` 包含 model、latency、rule_manifest_version
  - 阶段性指标写入 `ProofreadingResult.statistics`
File Paths:
  - `backend/src/services/proofreading/service.py`
  - `backend/tests/services/proofreading/test_service_integration.py`

### Week 3b: SEO Analyzer Implementation

#### T2.1 [P] Design SEO Analysis Prompt

**Description**: Research and design optimized Claude prompt for SEO metadata generation

**Dependencies**: None

**Estimated Hours**: 6 hours

**Deliverables**:
- `backend/src/services/seo_analyzer/prompts.py`:
  - SEO analysis system prompt
  - Few-shot examples (2-3 sample articles with expert metadata)
  - Output format specification (JSON schema)
- Prompt testing report:
  - Tested with 10 diverse articles (news, blog, technical, product)
  - Keyword accuracy: % match vs manual analysis
  - Optimal temperature: 0.3 recommended
  - Optimal model: claude-3-5-sonnet-20250101

**Acceptance Criteria**:
- Prompt consistently generates valid JSON output
- Keyword extraction 85%+ accurate vs manual baseline (10 test articles)
- Meta titles 100% within 50-60 character limit
- Meta descriptions 100% within 150-160 character limit
- Temperature 0.3 balances creativity and consistency

**File Paths**:
- `backend/src/services/seo_analyzer/prompts.py`
- `specs/001-cms-automation/research.md` (updated with prompt design section)

**Code Example** (`backend/src/services/seo_analyzer/prompts.py`):
```python
"""SEO analysis prompts for Claude."""

SEO_ANALYSIS_SYSTEM_PROMPT = """You are an expert SEO consultant analyzing web content to extract optimal keywords and generate metadata.

Your task is to analyze the provided article and generate comprehensive SEO metadata following these rules:

1. **Focus Keyword**: Identify the ONE primary keyword or phrase (2-4 words) that best represents the article's core topic.

2. **Primary Keywords** (3-5 keywords):
   - Extract 3-5 highly relevant keywords or phrases
   - These should appear naturally in the content
   - Prioritize keywords with commercial intent or search volume

3. **Secondary Keywords** (5-10 keywords):
   - Extract 5-10 related keywords that support the focus keyword
   - Include semantic variations and LSI (Latent Semantic Indexing) keywords
   - Consider user intent and related search queries

4. **Keyword Density**:
   - Calculate how often each keyword appears in the article
   - Format: {"keyword": {"count": N, "density": X.XX}}
   - Density = (keyword_count / total_words) * 100

5. **SEO Title** (50-60 characters):
   - Must include the focus keyword
   - Compelling and click-worthy
   - Exactly 50-60 characters (strict requirement)

6. **Meta Description** (150-160 characters):
   - Must include the focus keyword
   - Compelling call-to-action
   - Exactly 150-160 characters (strict requirement)

7. **Optimization Recommendations**:
   - Provide 3-7 actionable recommendations to improve SEO
   - Check for: keyword density issues, readability concerns, missing elements

**Output Format** (JSON):
```json
{
  "focus_keyword": "string",
  "primary_keywords": ["keyword1", "keyword2", "keyword3"],
  "secondary_keywords": ["keyword4", "keyword5", ...],
  "keyword_density": {
    "focus_keyword": {"count": 10, "density": 2.5}
  },
  "seo_title": "50-60 character title with focus keyword",
  "meta_description": "150-160 character description with focus keyword and CTA",
  "optimization_recommendations": [
    "Recommendation 1",
    "Recommendation 2"
  ]
}
```

Be precise, follow SEO best practices, and ensure all length constraints are met exactly."""


def create_seo_analysis_prompt(title: str, body: str, word_count: int) -> str:
    """Create user prompt for SEO analysis.

    Args:
        title: Article title
        body: Article body (HTML or plain text)
        word_count: Total word count

    Returns:
        Formatted prompt string
    """
    return f"""Analyze this article for SEO optimization:

**Title**: {title}

**Body** ({word_count} words):
{body}

**Instructions**:
1. Extract focus keyword, primary keywords (3-5), and secondary keywords (5-10)
2. Calculate keyword density for each keyword
3. Generate SEO title (exactly 50-60 characters, must include focus keyword)
4. Generate meta description (exactly 150-160 characters, must include focus keyword)
5. Provide 3-7 specific optimization recommendations

Return your analysis as JSON matching the specified format."""


# Few-shot examples for improved accuracy
FEW_SHOT_EXAMPLES = [
    {
        "title": "10 Best Practices for React Performance Optimization",
        "body": "React is a powerful JavaScript library...",
        "response": {
            "focus_keyword": "React performance optimization",
            "primary_keywords": ["React optimization", "React performance", "React best practices", "JavaScript performance"],
            "secondary_keywords": ["component rendering", "useMemo hook", "useCallback", "code splitting", "lazy loading", "React DevTools"],
            "keyword_density": {
                "React performance optimization": {"count": 5, "density": 1.2},
                "React optimization": {"count": 8, "density": 1.9}
            },
            "seo_title": "React Performance Optimization: 10 Best Practices",
            "meta_description": "Discover 10 proven best practices for React performance optimization. Learn techniques like code splitting, memoization, and lazy loading to boost your app speed.",
            "optimization_recommendations": [
                "Add code examples for each best practice to increase content depth",
                "Include performance benchmarks to demonstrate impact",
                "Add internal links to related React tutorials",
                "Increase focus keyword density to 2-3% (currently 1.2%)"
            ]
        }
    }
]
```

---

#### T2.2 [P] Implement Basic Keyword Extraction

**Description**: Implement TF-IDF-based keyword extraction as fallback/complement to Claude

**Dependencies**: None

**Estimated Hours**: 8 hours

**Deliverables**:
- `backend/src/services/seo_analyzer/tfidf_extractor.py`:
  - Extract keywords using TF-IDF algorithm (scikit-learn)
  - Remove stop words
  - N-gram extraction (1-gram, 2-gram, 3-gram)
  - Return top 20 keywords with scores
- `backend/src/services/seo_analyzer/keyword_utils.py`:
  - Calculate keyword density
  - Count keyword occurrences (case-insensitive)
  - Extract keywords from text

**Acceptance Criteria**:
- TF-IDF extractor returns relevant keywords for test articles
- N-gram extraction captures multi-word phrases
- Stop words filtered correctly
- Keyword density calculations accurate (verified manually)
- Processing 1500-word article in < 2 seconds

**File Paths**:
- `backend/src/services/seo_analyzer/tfidf_extractor.py`
- `backend/src/services/seo_analyzer/keyword_utils.py`
- `backend/tests/services/seo_analyzer/test_tfidf_extractor.py`

---

#### T2.3 Build SEO Analyzer Service

**Description**: Core service orchestrating keyword extraction, metadata generation, and readability scoring

**Dependencies**: T2.1 (prompt), T2.2 (TF-IDF)

**Estimated Hours**: 10 hours

**Deliverables**:
- `backend/src/services/seo_analyzer/analyzer.py`:
  - Main `SEOAnalyzer` class
  - Method: `analyze(article_id) -> SEOMetadata`
  - Steps:
    1. Load article from database
    2. Extract TF-IDF keywords (fallback)
    3. Call Claude Messages API with article content
    4. Parse Claude response (JSON)
    5. Validate output (length constraints, keyword counts)
    6. Calculate readability score
    7. Create SEOMetadata record in database
    8. Return SEOMetadata object
  - Error handling: Claude API failures, invalid JSON responses
  - Cost tracking: log API usage and cost

**Acceptance Criteria**:
- Analyze 1500-word article in < 30 seconds
- Cost per article < $0.10
- 100% of outputs meet length constraints (50-60 chars title, 150-160 chars description)
- Handles API failures gracefully (retry 3 times, fallback to TF-IDF if all fail)
- Stores all metadata in database correctly
- Unit tests cover happy path and error cases

**File Paths**:
- `backend/src/services/seo_analyzer/analyzer.py`
- `backend/tests/services/seo_analyzer/test_analyzer.py`

**Code Example** (`backend/src/services/seo_analyzer/analyzer.py`):
```python
"""SEO Analyzer service using Claude Messages API."""

import json
from typing import Dict, Any

from anthropic import Anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.config import get_logger, get_settings
from src.models import Article, SEOMetadata
from src.services.seo_analyzer.prompts import (
    SEO_ANALYSIS_SYSTEM_PROMPT,
    create_seo_analysis_prompt,
)
from src.services.seo_analyzer.keyword_utils import calculate_keyword_density
from src.services.seo_analyzer.readability import calculate_readability_score

logger = get_logger(__name__)
settings = get_settings()


class SEOAnalyzer:
    """Service for analyzing articles and generating SEO metadata."""

    def __init__(self, session: AsyncSession):
        """Initialize SEO analyzer.

        Args:
            session: Database session
        """
        self.session = session
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def analyze(self, article_id: int) -> SEOMetadata:
        """Analyze article and generate SEO metadata.

        Args:
            article_id: Article ID to analyze

        Returns:
            SEOMetadata object

        Raises:
            ValueError: If article not found
            Exception: If analysis fails
        """
        # Load article
        result = await self.session.execute(
            select(Article).where(Article.id == article_id)
        )
        article = result.scalar_one_or_none()

        if not article:
            raise ValueError(f"Article {article_id} not found")

        logger.info(
            "seo_analysis_started",
            article_id=article_id,
            title=article.title[:100],
            word_count=article.word_count,
        )

        try:
            # Create prompt
            prompt = create_seo_analysis_prompt(
                title=article.title,
                body=article.body,
                word_count=article.word_count,
            )

            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20250101",
                max_tokens=2000,
                temperature=0.3,
                system=SEO_ANALYSIS_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )

            # Parse response
            content = response.content[0].text
            seo_data = json.loads(content)

            # Validate output
            self._validate_seo_data(seo_data)

            # Calculate readability score
            readability = calculate_readability_score(article.body)

            # Calculate cost
            cost_usd = (
                response.usage.input_tokens * 0.000003 +  # $3 per 1M input tokens
                response.usage.output_tokens * 0.000015   # $15 per 1M output tokens
            )

            # Create SEO metadata record
            seo_metadata = SEOMetadata(
                article_id=article_id,
                meta_title=seo_data["seo_title"],
                meta_description=seo_data["meta_description"],
                focus_keyword=seo_data["focus_keyword"],
                primary_keywords=seo_data["primary_keywords"],
                secondary_keywords=seo_data["secondary_keywords"],
                keyword_density=seo_data["keyword_density"],
                readability_score=readability,
                optimization_recommendations=seo_data["optimization_recommendations"],
                manual_overrides={},
                generated_by=response.model,
                generation_cost=cost_usd,
                generation_tokens=response.usage.input_tokens + response.usage.output_tokens,
            )

            self.session.add(seo_metadata)
            await self.session.commit()
            await self.session.refresh(seo_metadata)

            # Update article status
            article.status = "seo_optimized"
            await self.session.commit()

            logger.info(
                "seo_analysis_completed",
                article_id=article_id,
                focus_keyword=seo_data["focus_keyword"],
                cost_usd=cost_usd,
                tokens=response.usage.input_tokens + response.usage.output_tokens,
            )

            return seo_metadata

        except Exception as e:
            logger.error(
                "seo_analysis_failed",
                article_id=article_id,
                error=str(e),
                exc_info=True,
            )
            raise

    def _validate_seo_data(self, data: Dict[str, Any]) -> None:
        """Validate SEO data from Claude.

        Args:
            data: SEO data dictionary

        Raises:
            ValueError: If validation fails
        """
        # Check required fields
        required_fields = [
            "focus_keyword", "primary_keywords", "secondary_keywords",
            "keyword_density", "seo_title", "meta_description",
            "optimization_recommendations"
        ]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate title length
        title_len = len(data["seo_title"])
        if not 50 <= title_len <= 60:
            raise ValueError(f"SEO title length {title_len} not in range 50-60")

        # Validate description length
        desc_len = len(data["meta_description"])
        if not 150 <= desc_len <= 160:
            raise ValueError(f"Meta description length {desc_len} not in range 150-160")

        # Validate keyword counts
        if not 3 <= len(data["primary_keywords"]) <= 5:
            raise ValueError(f"Primary keywords count must be 3-5, got {len(data['primary_keywords'])}")

        if not 5 <= len(data["secondary_keywords"]) <= 10:
            raise ValueError(f"Secondary keywords count must be 5-10, got {len(data['secondary_keywords'])}")
```

---

#### T2.4 Implement Readability Scoring

**Description**: Calculate Flesch-Kincaid readability score for articles

**Dependencies**: None (can run parallel)

**Estimated Hours**: 4 hours

**Deliverables**:
- `backend/src/services/seo_analyzer/readability.py`:
  - Function: `calculate_readability_score(text: str) -> float`
  - Implement Flesch-Kincaid Grade Level formula
  - Use pyphen library for syllable counting
  - Return grade level (target: 8-12)

**Acceptance Criteria**:
- Readability score matches manual calculations (tested on 5 sample texts)
- Processes 1500-word article in < 1 second
- Handles edge cases (very short text, no punctuation)
- Passes unit tests

**File Paths**:
- `backend/src/services/seo_analyzer/readability.py`
- `backend/tests/services/seo_analyzer/test_readability.py`

---

#### T2.5 Build SEO API Endpoints

**Description**: Create FastAPI endpoints for SEO analysis operations

**Dependencies**: T2.3 (analyzer ready)

**Estimated Hours**: 6 hours

**Deliverables**:
- `backend/src/api/routes/seo.py`:
  - POST /v1/seo/analyze/{article_id} - Trigger analysis
  - GET /v1/seo/analyze/{article_id}/status - Check analysis status
  - GET /v1/seo/metadata/{article_id} - Retrieve metadata
  - PUT /v1/seo/metadata/{article_id} - Update metadata (manual edits)
  - POST /v1/seo/analyze/batch - Batch analysis
- `backend/src/api/schemas/seo.py`:
  - SEOAnalysisRequest
  - SEOMetadataResponse
  - SEOMetadataUpdateRequest
  - BatchAnalysisRequest

**Acceptance Criteria**:
- All endpoints documented in OpenAPI spec
- POST /v1/seo/analyze triggers async analysis (returns task_id)
- GET /v1/seo/metadata returns complete metadata
- PUT /v1/seo/metadata allows editing title, description, focus keyword
- Batch endpoint limits to 1000 articles
- Error handling (article not found, analysis failed)

**File Paths**:
- `backend/src/api/routes/seo.py`
- `backend/src/api/schemas/seo.py`
- `backend/tests/api/test_seo_endpoints.py`

---

#### T2.6 Create Celery SEO Tasks

**Description**: Implement Celery task for async SEO analysis

**Dependencies**: T2.5

**Estimated Hours**: 4 hours

**Deliverables**:
- `backend/src/workers/tasks/analyze_seo.py`:
  - Celery task: `analyze_seo_task(article_id: int)`
  - Wrapper around SEOAnalyzer
  - Progress tracking
  - Error handling with retry (max 3 attempts, exponential backoff)
  - Update article status throughout

**Acceptance Criteria**:
- Task processes article successfully
- Retries on transient errors (API timeout, rate limit)
- Does not retry on permanent errors (article not found, validation failure)
- Updates article status: draft → seo_analyzing → seo_optimized
- Task tracked in Celery/Flower dashboard

**File Paths**:
- `backend/src/workers/tasks/analyze_seo.py`
- `backend/tests/workers/test_analyze_seo.py`

---

### Week 3.5: Testing & Validation

#### T2.7 Build SEO Validation Suite

**Description**: Create comprehensive validation tests with expert baseline

**Dependencies**: T2.6

**Estimated Hours**: 6 hours

**Deliverables**:
- `backend/tests/validation/seo_accuracy_test.py`:
  - 20 test articles with expert-written SEO metadata (baseline)
  - Run SEO analyzer on each article
  - Compare AI-generated keywords vs expert keywords
  - Calculate accuracy: matching keywords / total keywords * 100
  - Generate report with accuracy metrics
  - Target: ≥85% keyword match rate

**Acceptance Criteria**:
- 20 diverse test articles collected (news, blog, technical, product, how-to)
- Expert baseline metadata for all 20 articles
- Accuracy report generated
- ≥85% keyword match rate achieved
- Report includes:
  - Overall accuracy
  - Per-article accuracy
  - Common mismatches
  - Recommendations for prompt improvement

**File Paths**:
- `backend/tests/validation/seo_accuracy_test.py`
- `backend/tests/validation/test_articles.json` (20 articles with expert metadata)
- `backend/tests/validation/accuracy_report.md` (generated report)

---

#### T2.8 Unit Tests

**Description**: Comprehensive unit tests for SEO analysis components

**Dependencies**: T2.3-T2.6

**Estimated Hours**: 4 hours

**Deliverables**:
- Unit tests for all SEO analyzer components:
  - `test_tfidf_extractor.py`
  - `test_keyword_utils.py`
  - `test_readability.py`
  - `test_analyzer.py`
- Target: 90%+ code coverage

**Acceptance Criteria**:
- All unit tests pass
- Code coverage ≥90% for seo_analyzer package
- Tests cover edge cases (empty content, very long content, special characters)
- Mock Claude API in tests (use pytest-mock)

**File Paths**:
- `backend/tests/services/seo_analyzer/test_*.py`

---

#### T2.9 Performance Optimization

**Description**: Optimize SEO analysis for speed and cost

**Dependencies**: T2.8

**Estimated Hours**: 4 hours

**Deliverables**:
- Performance improvements:
  - Cache TF-IDF extractor results (Redis)
  - Batch multiple article analyses in single Claude API call (if possible)
  - Optimize database queries (select only needed fields)
- Performance benchmarks:
  - 500-word article: < 20 seconds
  - 1000-word article: < 25 seconds
  - 1500-word article: < 30 seconds
  - 2000-word article: < 35 seconds
- Cost optimization:
  - Average cost per article: < $0.10

**Acceptance Criteria**:
- 95% of articles analyzed within SLA (< 30s)
- Average cost < $0.10 per article
- Caching reduces duplicate analysis costs
- Performance report generated

**File Paths**:
- `backend/src/services/seo_analyzer/cache.py` (caching logic)
- `backend/tests/performance/test_seo_performance.py`
- `backend/tests/performance/seo_performance_report.md`

---

**Phase 2 Checkpoint**: ✅ SEO analysis working, 85%+ accuracy, < 30s per article, < $0.10 cost

---

## Phase 3: Multi-Provider Computer Use Framework (3 weeks) ✅ COMPLETE

**Goal**: Implement abstract provider pattern for Computer Use with 3 providers (Anthropic, Gemini, Playwright)
**Duration**: 3 weeks (Week 4-6)
**Estimated Hours**: 94 hours
**Status**: ✅ **Complete** (100%)
**Evidence**:
- ✅ Playwright + CDP provider: `/backend/src/services/providers/playwright_cdp_provider.py` (25,893 lines)
- ✅ CDP utilities: `/backend/src/services/providers/cdp_utils.py` (16,557 lines)
- ✅ WordPress publisher: `/backend/src/services/providers/playwright_wordpress_publisher.py` (17,951 lines)
- ✅ Publishing orchestrator: `/backend/src/services/publishing/orchestrator.py` (16,287 lines)
- ✅ API route: `/backend/src/api/routes/publish_routes.py` (10,279 lines)
- ✅ Computer Use API: `/backend/src/api/routes/computer_use.py` (5,599 lines)
- ✅ Performance monitoring, visual regression testing, network optimization implemented

---

### Week 4: Provider Interface & Anthropic Implementation

#### T3.1 [P] Design Provider Abstraction

**Description**: Design abstract base class and data structures for multi-provider Computer Use

**Dependencies**: None

**Estimated Hours**: 6 hours

**Deliverables**:
- `backend/src/services/computer_use/base.py`:
  - Abstract `ComputerUseProvider` base class with methods:
    - `execute(instructions, context) -> ExecutionResult`
    - `navigate(url) -> ExecutionStep`
    - `type_text(selector, text) -> ExecutionStep`
    - `click(selector) -> ExecutionStep`
    - `upload_file(selector, file_path) -> ExecutionStep`
    - `screenshot(name) -> str`
    - `cleanup() -> None`
  - Data classes:
    - `ComputerUseConfig` (provider_type, credentials, options)
    - `ExecutionStep` (action, target, payload, result, screenshot_path, timestamp)
    - `ExecutionResult` (success, steps, error, post_url, post_id, duration)
    - `ProviderType` enum (anthropic, gemini, playwright)

**Acceptance Criteria**:
- Abstract base class defines complete interface
- All methods have clear docstrings
- Data classes use dataclasses or Pydantic
- Type hints complete (passes mypy)
- Design reviewed and approved

**File Paths**:
- `backend/src/services/computer_use/base.py`

**Code Example** (`backend/src/services/computer_use/base.py`):
```python
"""Computer Use provider abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ProviderType(str, Enum):
    """Computer Use provider types."""

    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    PLAYWRIGHT = "playwright"


@dataclass
class ComputerUseConfig:
    """Configuration for Computer Use provider."""

    provider_type: ProviderType
    cms_url: str
    cms_username: str
    cms_password: str
    cms_type: str = "wordpress"
    headless: bool = True
    timeout: int = 300000  # 5 minutes
    screenshot_dir: str = "screenshots"
    options: Dict[str, Any] = None


@dataclass
class ExecutionStep:
    """Single execution step in Computer Use workflow."""

    action: str  # navigate, click, type, upload, screenshot, verify, wait
    target: Optional[str] = None  # Element selector or URL
    payload: Optional[Dict[str, Any]] = None  # Additional data
    result: str = "pending"  # pending, success, failure, retry
    screenshot_path: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class ExecutionResult:
    """Complete execution result."""

    success: bool
    steps: List[ExecutionStep]
    post_url: Optional[str] = None
    post_id: Optional[str] = None
    duration_seconds: int = 0
    error: Optional[str] = None
    cost_usd: Optional[float] = None


class ComputerUseProvider(ABC):
    """Abstract base class for Computer Use providers."""

    def __init__(self, config: ComputerUseConfig):
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self.steps: List[ExecutionStep] = []

    @abstractmethod
    async def execute(
        self,
        instructions: str,
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute high-level instructions (used by AI providers).

        Args:
            instructions: Natural language instructions
            context: Execution context (article data, SEO metadata, etc.)

        Returns:
            ExecutionResult with all steps and final result
        """
        pass

    @abstractmethod
    async def navigate(self, url: str) -> ExecutionStep:
        """Navigate to URL.

        Args:
            url: Target URL

        Returns:
            ExecutionStep for navigation
        """
        pass

    @abstractmethod
    async def type_text(self, selector: str, text: str) -> ExecutionStep:
        """Type text into element.

        Args:
            selector: Element selector (CSS or XPath)
            text: Text to type

        Returns:
            ExecutionStep for typing
        """
        pass

    @abstractmethod
    async def click(self, selector: str) -> ExecutionStep:
        """Click element.

        Args:
            selector: Element selector

        Returns:
            ExecutionStep for click
        """
        pass

    @abstractmethod
    async def upload_file(self, selector: str, file_path: str) -> ExecutionStep:
        """Upload file to element.

        Args:
            selector: File input selector
            file_path: Path to file

        Returns:
            ExecutionStep for upload
        """
        pass

    @abstractmethod
    async def screenshot(self, name: str) -> str:
        """Take screenshot.

        Args:
            name: Screenshot name

        Returns:
            Path to screenshot file
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources (close browser, etc.)."""
        pass

    def add_step(self, step: ExecutionStep) -> None:
        """Add execution step to history.

        Args:
            step: Execution step
        """
        self.steps.append(step)
```

---

#### T3.2 Implement Anthropic Provider

**Description**: Implement Computer Use provider using Anthropic's API

**Dependencies**: T3.1

**Estimated Hours**: 12 hours

**Deliverables**:
- `backend/src/services/computer_use/anthropic_provider.py`:
  - `AnthropicComputerUseProvider` class extending `ComputerUseProvider`
  - Implement all abstract methods
  - Use `client.beta.messages.create()` with `computer_20241022` tool
  - Handle AI responses and extract structured actions
  - Screenshot capture at each major step
  - Cost tracking (input/output tokens)
- High-level WordPress publishing logic:
  - Login → Create Post → Fill Content → Upload Images → Set SEO → Publish

**Acceptance Criteria**:
- Provider successfully logs into test WordPress
- Creates and publishes post with all content
- Captures 8+ screenshots
- Tracks API cost accurately
- Handles errors and retries
- Passes integration tests with sandbox WordPress

**File Paths**:
- `backend/src/services/computer_use/anthropic_provider.py`
- `backend/tests/services/computer_use/test_anthropic_provider.py`

---

#### T3.3 Build Prompt Template System

**Description**: Create reusable prompt templates for WordPress operations

**Dependencies**: T3.2

**Estimated Hours**: 6 hours

**Deliverables**:
- `backend/src/services/computer_use/prompts.py`:
  - Template: `WORDPRESS_LOGIN_PROMPT`
  - Template: `CREATE_POST_PROMPT`
  - Template: `FILL_CONTENT_PROMPT`
  - Template: `UPLOAD_IMAGE_PROMPT`
  - Template: `SET_SEO_PROMPT` (Yoast & Rank Math variants)
  - Template: `PUBLISH_POST_PROMPT`
  - Function: `render_prompt(template, context)` - Jinja2 rendering

**Acceptance Criteria**:
- All templates tested with sample data
- Templates render correctly with Jinja2
- Context variables documented
- Templates include error handling instructions

**File Paths**:
- `backend/src/services/computer_use/prompts.py`
- `backend/tests/services/computer_use/test_prompts.py`

---

#### T3.4 Implement Screenshot Management

**Description**: Implement screenshot capture, storage, and retrieval

**Dependencies**: T1.7 (storage service)

**Estimated Hours**: 4 hours

**Deliverables**:
- `backend/src/services/computer_use/screenshot_manager.py`:
  - Method: `capture(step_name, browser_screenshot_data) -> str`
  - Store screenshots using FileStorage service
  - Generate URLs for screenshot access
  - Naming convention: `task_{task_id}/{step_name}_{timestamp}.png`
  - Store URLs in publish_tasks.screenshots JSONB

**Acceptance Criteria**:
- Screenshots stored correctly (local dev, S3 production)
- URLs generated and accessible via HTTP
- Screenshot filenames follow naming convention
- Screenshot metadata stored in database

**File Paths**:
- `backend/src/services/computer_use/screenshot_manager.py`
- `backend/tests/services/computer_use/test_screenshot_manager.py`

---

### Week 5: Playwright Provider & Factory

#### T3.5 Implement Playwright Provider

**Description**: Implement traditional browser automation provider using Playwright

**Dependencies**: T3.1

**Estimated Hours**: 16 hours

**Deliverables**:
- `backend/src/services/computer_use/playwright_provider.py`:
  - `PlaywrightProvider` class extending `ComputerUseProvider`
  - Implement all abstract methods using Playwright API
  - WordPress-specific selectors:
    - Login: `#user_login`, `#user_pass`, `#wp-submit`
    - New Post: `.page-title-action` (Add New button)
    - Title: `.editor-post-title__input` or `#post-title-0`
    - Content: `.block-editor-rich-text__editable` or `#content`
    - Yoast SEO: `#yoast-google-preview-title`, `#yoast-google-preview-description`, `#focus-keyword-input-metabox`
    - Rank Math: `.rank-math-title`, `.rank-math-description`, `.rank-math-focus-keyword`
    - Publish: `.editor-post-publish-button`
  - Gutenberg editor support (block editor)
  - Classic editor support (fallback)
  - Detect editor type and adapt
  - Screenshot capture after each operation

**Acceptance Criteria**:
- Successfully logs into WordPress
- Creates post in both Gutenberg and Classic editor
- Fills all SEO fields (Yoast and Rank Math)
- Uploads featured image
- Publishes post and extracts post URL and ID
- Captures 8+ screenshots
- Completes workflow in < 3 minutes
- Handles WordPress UI variations gracefully

**File Paths**:
- `backend/src/services/computer_use/playwright_provider.py`
- `backend/tests/services/computer_use/test_playwright_provider.py`

**Code Example** (partial):
```python
"""Playwright-based Computer Use provider."""

from playwright.async_api import async_playwright, Browser, Page
from typing import Dict, Any

from src.services.computer_use.base import (
    ComputerUseProvider,
    ComputerUseConfig,
    ExecutionStep,
    ExecutionResult,
)
from src.config import get_logger

logger = get_logger(__name__)


class PlaywrightProvider(ComputerUseProvider):
    """Playwright-based traditional automation provider."""

    def __init__(self, config: ComputerUseConfig):
        """Initialize Playwright provider."""
        super().__init__(config)
        self.browser: Browser = None
        self.page: Page = None
        self.playwright = None

    async def execute(
        self,
        instructions: str,
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute WordPress publishing workflow.

        Args:
            instructions: Not used (Playwright uses fixed workflow)
            context: Article data and SEO metadata

        Returns:
            ExecutionResult
        """
        try:
            # Launch browser
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.headless
            )
            self.page = await self.browser.new_page()

            # Step 1: Login
            await self._login()

            # Step 2: Create new post
            await self._create_post()

            # Step 3: Fill content
            await self._fill_content(
                title=context["title"],
                body=context["body"]
            )

            # Step 4: Upload featured image (if provided)
            if context.get("featured_image"):
                await self._upload_featured_image(context["featured_image"])

            # Step 5: Fill SEO fields
            await self._fill_seo_fields(context["seo_metadata"])

            # Step 6: Publish
            post_url, post_id = await self._publish_post()

            return ExecutionResult(
                success=True,
                steps=self.steps,
                post_url=post_url,
                post_id=post_id,
                duration_seconds=sum(s.duration for s in self.steps if hasattr(s, 'duration')),
                cost_usd=0.0  # Playwright is free
            )

        except Exception as e:
            logger.error("Playwright execution failed", error=str(e), exc_info=True)
            return ExecutionResult(
                success=False,
                steps=self.steps,
                error=str(e)
            )

        finally:
            await self.cleanup()

    async def _login(self) -> None:
        """Login to WordPress."""
        step = ExecutionStep(action="navigate", target=f"{self.config.cms_url}/wp-admin")

        try:
            await self.page.goto(f"{self.config.cms_url}/wp-admin")
            await self.page.wait_for_selector("#user_login", timeout=10000)

            await self.page.fill("#user_login", self.config.cms_username)
            await self.page.fill("#user_pass", self.config.cms_password)
            await self.page.click("#wp-submit")

            # Wait for dashboard
            await self.page.wait_for_url("**/wp-admin/**", timeout=15000)

            step.result = "success"
            step.screenshot_path = await self.screenshot("01_login_success")

        except Exception as e:
            step.result = "failure"
            step.error = str(e)
            logger.error("WordPress login failed", error=str(e))
            raise

        finally:
            self.add_step(step)

    async def _fill_seo_fields(self, seo_metadata: Dict[str, Any]) -> None:
        """Fill SEO plugin fields (Yoast or Rank Math)."""
        step = ExecutionStep(action="fill_seo", target="seo_plugin")

        try:
            # Detect SEO plugin
            has_yoast = await self.page.query_selector("#yoast-google-preview-title")
            has_rankmath = await self.page.query_selector(".rank-math-title")

            if has_yoast:
                logger.info("Detected Yoast SEO plugin")
                await self._fill_yoast_seo(seo_metadata)
            elif has_rankmath:
                logger.info("Detected Rank Math plugin")
                await self._fill_rankmath_seo(seo_metadata)
            else:
                logger.warning("No SEO plugin detected, skipping SEO fields")

            step.result = "success"
            step.screenshot_path = await self.screenshot("05_seo_fields_filled")

        except Exception as e:
            step.result = "failure"
            step.error = str(e)
            logger.error("Fill SEO fields failed", error=str(e))
            raise

        finally:
            self.add_step(step)

    async def _fill_yoast_seo(self, seo_metadata: Dict[str, Any]) -> None:
        """Fill Yoast SEO fields."""
        # SEO Title
        title_input = await self.page.query_selector("#yoast-google-preview-title input")
        if title_input:
            await title_input.fill(seo_metadata["meta_title"])

        # Meta Description
        desc_input = await self.page.query_selector("#yoast-google-preview-description textarea")
        if desc_input:
            await desc_input.fill(seo_metadata["meta_description"])

        # Focus Keyword
        focus_input = await self.page.query_selector("#focus-keyword-input-metabox")
        if focus_input:
            await focus_input.fill(seo_metadata["focus_keyword"])

    async def navigate(self, url: str) -> ExecutionStep:
        """Navigate to URL."""
        step = ExecutionStep(action="navigate", target=url)
        try:
            await self.page.goto(url, wait_until="domcontentloaded")
            step.result = "success"
        except Exception as e:
            step.result = "failure"
            step.error = str(e)
        self.add_step(step)
        return step

    async def type_text(self, selector: str, text: str) -> ExecutionStep:
        """Type text into element."""
        step = ExecutionStep(action="type", target=selector, payload={"text": text})
        try:
            await self.page.fill(selector, text)
            step.result = "success"
        except Exception as e:
            step.result = "failure"
            step.error = str(e)
        self.add_step(step)
        return step

    async def click(self, selector: str) -> ExecutionStep:
        """Click element."""
        step = ExecutionStep(action="click", target=selector)
        try:
            await self.page.click(selector)
            step.result = "success"
        except Exception as e:
            step.result = "failure"
            step.error = str(e)
        self.add_step(step)
        return step

    async def upload_file(self, selector: str, file_path: str) -> ExecutionStep:
        """Upload file."""
        step = ExecutionStep(action="upload", target=selector, payload={"file_path": file_path})
        try:
            await self.page.set_input_files(selector, file_path)
            step.result = "success"
        except Exception as e:
            step.result = "failure"
            step.error = str(e)
        self.add_step(step)
        return step

    async def screenshot(self, name: str) -> str:
        """Take screenshot."""
        path = f"{self.config.screenshot_dir}/{name}.png"
        await self.page.screenshot(path=path)
        return path

    async def cleanup(self) -> None:
        """Cleanup browser resources."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
```

---

#### T3.6 Implement Provider Factory

**Description**: Factory pattern for dynamic provider instantiation

**Dependencies**: T3.2 (Anthropic), T3.5 (Playwright)

**Estimated Hours**: 4 hours

**Deliverables**:
- `backend/src/services/computer_use/factory.py`:
  - `ProviderFactory` class
  - Method: `create(config: ComputerUseConfig) -> ComputerUseProvider`
  - Method: `create_from_settings() -> ComputerUseProvider` (reads from env)
  - Support provider selection via:
    - Environment variable: `COMPUTER_USE_PROVIDER=anthropic|gemini|playwright`
    - Config parameter
  - Validate config before creating provider

**Acceptance Criteria**:
- Factory creates correct provider based on config
- Environment variable overrides default
- Invalid provider type raises clear error
- Factory tested with all 3 provider types

**File Paths**:
- `backend/src/services/computer_use/factory.py`
- `backend/tests/services/computer_use/test_factory.py`

---

#### T3.7 Add Gemini Provider Placeholder

**Description**: Create placeholder implementation for Google Gemini Computer Use

**Dependencies**: T3.1

**Estimated Hours**: 4 hours

**Deliverables**:
- `backend/src/services/computer_use/gemini_provider.py`:
  - `GeminiComputerUseProvider` class extending `ComputerUseProvider`
  - Placeholder implementation (raises NotImplementedError)
  - Documentation on Gemini Computer Use API (when available)
  - TODO comments for future implementation

**Acceptance Criteria**:
- Class structure defined
- Raises NotImplementedError with helpful message
- Documentation includes API research findings
- Integrated into factory (returns placeholder)

**File Paths**:
- `backend/src/services/computer_use/gemini_provider.py`
- `specs/001-cms-automation/research.md` (Gemini API section)

---

#### T3.8 Build CMS Publisher Service

**Description**: High-level service orchestrating provider selection and publishing workflow

**Dependencies**: T3.6 (factory)

**Estimated Hours**: 8 hours

**Deliverables**:
- `backend/src/services/cms_publisher/publisher.py`:
  - `CMSPublisher` class
  - Method: `publish_article(article_id, provider=None) -> PublishResult`
  - Steps:
    1. Load article and SEO metadata from database
    2. Create ComputerUseConfig
    3. Create provider via factory
    4. Execute publishing workflow
    5. Save screenshots to storage
    6. Update publish_tasks record
    7. Log all steps to execution_logs
    8. Update article with post_url and cms_article_id
  - Automatic provider fallback:
    - If Playwright fails → retry with Anthropic
    - If Anthropic fails → manual intervention required
  - Cost tracking

**Acceptance Criteria**:
- Successfully publishes article to WordPress
- All screenshots saved and URLs stored
- All steps logged to execution_logs table
- Article updated with published URL and CMS ID
- Fallback mechanism works (tested by forcing Playwright failure)
- Handles errors gracefully

**File Paths**:
- `backend/src/services/cms_publisher/publisher.py`
- `backend/tests/services/cms_publisher/test_publisher.py`

---

### Week 6: Testing & Integration

#### T3.9 Build Test WordPress Environment

**Description**: Setup containerized WordPress for testing

**Dependencies**: None (can run parallel)

**Estimated Hours**: 6 hours

**Deliverables**:
- `docker-compose.test.yml`:
  - WordPress container (latest)
  - MySQL database
  - Yoast SEO plugin pre-installed
  - Rank Math plugin pre-installed (for testing both)
  - Sample admin account (username: admin, password: test123)
- `scripts/setup_test_wordpress.sh`:
  - Initialize WordPress
  - Install and activate plugins
  - Create test posts
  - Configure permalink structure

**Acceptance Criteria**:
- WordPress accessible at http://localhost:8080
- Both Yoast SEO and Rank Math installed and activated
- Can toggle between plugins for testing
- Admin login works
- Database persists between restarts

**File Paths**:
- `docker-compose.test.yml`
- `scripts/setup_test_wordpress.sh`
- `specs/001-cms-automation/testing.md` (testing environment documentation)

---

#### T3.10 Integration Tests for Each Provider

**Description**: Comprehensive integration tests for all providers

**Dependencies**: T3.9 (test WordPress), T3.2 (Anthropic), T3.5 (Playwright)

**Estimated Hours**: 10 hours

**Deliverables**:
- `backend/tests/integration/test_anthropic_provider.py`:
  - Test: Login to test WordPress
  - Test: Create and publish post with all content
  - Test: Verify 8+ screenshots captured
  - Test: Verify post published and accessible
  - Test: Cost tracking accurate
- `backend/tests/integration/test_playwright_provider.py`:
  - Same tests as Anthropic provider
  - Additional test: Gutenberg editor support
  - Additional test: Classic editor support
  - Additional test: Yoast SEO fields
  - Additional test: Rank Math fields
- `backend/tests/integration/test_provider_compatibility.py`:
  - Test: Both providers publish same article consistently
  - Test: Compare screenshots from both providers
  - Test: Verify no credential leaks in screenshots

**Acceptance Criteria**:
- All integration tests pass
- Both providers successfully publish to test WordPress
- Screenshots captured and verified (no credentials visible)
- Tests run in CI pipeline
- Test coverage > 85% for computer_use package

**File Paths**:
- `backend/tests/integration/test_anthropic_provider.py`
- `backend/tests/integration/test_playwright_provider.py`
- `backend/tests/integration/test_provider_compatibility.py`

---

#### T3.11 Implement Provider Fallback Logic

**Description**: Automatic fallback mechanism when primary provider fails

**Dependencies**: T3.8 (publisher service)

**Estimated Hours**: 6 hours

**Deliverables**:
- `backend/src/services/cms_publisher/fallback_handler.py`:
  - Method: `execute_with_fallback(article_id, preferred_provider) -> PublishResult`
  - Fallback chain: Playwright → Anthropic → Manual
  - Log all fallback attempts
  - Track which provider succeeded
  - Update publish_tasks with provider used

**Acceptance Criteria**:
- If Playwright fails, automatically tries Anthropic
- If Anthropic fails, marks as "manual_intervention_required"
- All fallback attempts logged
- Fallback tested by injecting failures
- Fallback chain configurable via settings

**File Paths**:
- `backend/src/services/cms_publisher/fallback_handler.py`
- `backend/tests/services/cms_publisher/test_fallback.py`

---

#### T3.12 Build Publishing API Endpoints

**Description**: FastAPI endpoints for triggering and monitoring publishing tasks

**Dependencies**: T3.8 (publisher service)

**Estimated Hours**: 6 hours

**Deliverables**:
- `backend/src/api/routes/publish.py`:
  - POST /v1/publish/submit - Submit article for publishing
  - GET /v1/publish/tasks/{task_id} - Get task status
  - GET /v1/publish/tasks/{task_id}/screenshots - Get screenshots
  - GET /v1/publish/tasks/{task_id}/logs - Get execution logs
  - POST /v1/publish/retry/{task_id} - Retry failed task
- `backend/src/api/schemas/publish.py`:
  - PublishRequest schema (article_id, provider, options)
  - PublishTaskResponse schema
  - ExecutionLogResponse schema

**Acceptance Criteria**:
- All endpoints documented in OpenAPI spec
- POST /v1/publish/submit triggers async publishing (returns task_id)
- GET /v1/publish/tasks returns real-time status
- Screenshots accessible via URLs in response
- Execution logs returned in chronological order
- Retry endpoint works for failed tasks

**File Paths**:
- `backend/src/api/routes/publish.py`
- `backend/src/api/schemas/publish.py`
- `backend/tests/api/test_publish_endpoints.py`

---

#### T3.13 Create Celery Publishing Tasks

**Description**: Celery task for async article publishing

**Dependencies**: T3.12

**Estimated Hours**: 6 hours

**Deliverables**:
- `backend/src/workers/tasks/publish_article.py`:
  - Celery task: `publish_article_task(article_id, provider=None)`
  - Wrapper around CMSPublisher
  - Progress tracking (update publish_task status in real-time)
  - Error handling with retry (max 3 attempts for transient errors)
  - Screenshot storage to S3/local
  - Execution logging to database
  - Update article fields on success (published_at, cms_article_id, published_url)
  - Send notification on completion/failure (email or webhook)

**Acceptance Criteria**:
- Task processes article successfully
- Status updated in real-time: pending → running → completed/failed
- Screenshots uploaded to storage
- All execution logs saved to database
- Article updated on success
- Retries only transient errors (not login failures)
- Task visible in Celery/Flower dashboard

**File Paths**:
- `backend/src/workers/tasks/publish_article.py`
- `backend/tests/workers/test_publish_article.py`

---

#### T3.14 Error Handling & Retry Logic

**Description**: Comprehensive error handling and retry strategy

**Dependencies**: T3.13

**Estimated Hours**: 4 hours

**Deliverables**:
- `backend/src/services/cms_publisher/error_handler.py`:
  - Classify errors:
    - Transient: network timeout, rate limit, element not found (temporary)
    - Permanent: wrong credentials, post already published, WordPress down
  - Retry strategy:
    - Transient errors: retry with exponential backoff (10s → 30s → 90s)
    - Permanent errors: fail immediately, no retry
  - Error reporting:
    - Log all errors with context
    - Include screenshot at error point
    - Provide actionable error messages

**Acceptance Criteria**:
- Transient errors retried automatically
- Permanent errors fail fast
- All errors logged with context
- Error screenshots captured
- Error messages actionable (tell user what went wrong and how to fix)
- Tested with simulated failures

**File Paths**:
- `backend/src/services/cms_publisher/error_handler.py`
- `backend/tests/services/cms_publisher/test_error_handler.py`

---

**Phase 3 Checkpoint**: ✅ Multi-provider Computer Use working, 3 providers implemented, 8+ screenshots per task, 95%+ success rate

---

## Phase 4: Frontend & API Integration (2 weeks → **6 weeks revised**) 🟡 PARTIAL

**⚠️ CRITICAL UPDATE (2025-10-27): UI Implementation Gap Identified**

**Original Estimate**: 2 weeks, 80 hours
**Revised Estimate**: **6 weeks, 312 hours**
**Current Status**: 🟡 **60% Complete** (Backend 100%, Frontend 60%)
**Impact**: Backend/API完整，部分前端组件需补充
**Evidence**:
- ✅ Backend APIs: All routes implemented (11 route files, 100% complete)
- ✅ Publishing UI: `/frontend/src/components/Publishing/` (9 components)
- ✅ Type definitions: `/frontend/src/types/` (complete)
- ✅ UI components: `/frontend/src/components/ui/` (Badge, Card, Drawer, Tabs)
- 🟡 Article Import UI: Partially implemented
- 🟡 SEO Optimizer UI: Partially implemented

---

### Gap Analysis Summary

| Aspect | Original Plan | Reality | Gap |
|--------|--------------|---------|-----|
| **Modules** | 6 (implied) | 0 | 6 modules missing |
| **Components** | ~15 (estimated) | 5 (wrong direction) | 48 components needed |
| **Work Hours** | 80h | 0h actual | 312h required |
| **Team Size** | Not specified | Need 2 FE + 1 BE | Team gap |

---

### 🚨 ACTION REQUIRED

**The tasks below (T4.1-T4.10) are insufficient and do not reflect the actual work required.**

**For complete, production-ready task breakdown, see:**

📋 **[UI Implementation Tasks](./UI_IMPLEMENTATION_TASKS.md)** - **USE THIS DOCUMENT**

That document contains:
- ✅ 48 detailed UI component tasks (T-UI-1.1.1 through T-UI-3.4.1)
- ✅ Acceptance criteria for each component
- ✅ Code structure examples and best practices
- ✅ API integration guides
- ✅ Dependency mapping and critical path
- ✅ 6-week sprint plan with milestones
- ✅ Backend API requirements (56 hours)
- ✅ E2E testing strategy (20 hours)

**Cross-References**:
- 📊 [UI Gaps Analysis](../../docs/UI_GAPS_ANALYSIS.md) - Detailed gap analysis
- 📈 [Executive Summary](../../docs/EXECUTIVE_SUMMARY_UI_GAPS.md) - Decision guide
- 📘 [Updated spec.md](./spec.md) - See FR-046 to FR-070 (UI requirements)
- 📘 [Updated plan.md](./plan.md) - See Phase 4 revised timeline

---

### Historical Tasks (Reference Only)

**⚠️ The tasks below are kept for historical reference but are INCOMPLETE. Use [UI_IMPLEMENTATION_TASKS.md](./UI_IMPLEMENTATION_TASKS.md) instead.**

**Original Goal**: Build React frontend for article management, SEO optimization, and publishing monitoring
**Original Duration**: 2 weeks (Week 7-8)
**Original Estimated Hours**: 80 hours
**Original Status**: Not Started

---

### Week 7: Core UI Components

#### T4.1 [P] Setup Frontend Project

**Description**: Initialize React frontend project with all dependencies

**Dependencies**: None

**Estimated Hours**: 4 hours

**Deliverables**:
- Frontend project initialized with Vite
- Dependencies installed:
  - React 18.3, TypeScript 5.0
  - React Router 6.0, React Query 5.0
  - React Hook Form 7.0, Zod validation
  - TailwindCSS 3.4, Headless UI
  - Recharts 2.10 (for charts)
  - date-fns (date formatting)
- Project structure:
  ```
  frontend/
  ├── src/
  │   ├── components/
  │   ├── pages/
  │   ├── services/
  │   ├── hooks/
  │   ├── utils/
  │   ├── types/
  │   └── App.tsx
  ├── public/
  ├── package.json
  └── vite.config.ts
  ```
- ESLint and Prettier configured
- TailwindCSS configured with custom theme

**Acceptance Criteria**:
- `npm run dev` starts development server
- TypeScript compilation works
- TailwindCSS classes working
- No console errors or warnings

**File Paths**:
- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tailwind.config.js`
- `frontend/tsconfig.json`

---

#### T4.2 Build Article Import UI

**Description**: UI for importing articles from CSV/JSON or manual entry

**Dependencies**: T4.1

**Estimated Hours**: 8 hours

**Deliverables**:
- `frontend/src/pages/ImportArticlePage.tsx`:
  - Tab 1: Manual Entry (form with title, body, images, excerpt)
  - Tab 2: CSV Upload (drag-and-drop file upload)
  - Tab 3: JSON Import (paste JSON or upload file)
- `frontend/src/components/ArticleImport/ManualEntryForm.tsx`:
  - Form with React Hook Form
  - Rich text editor for body (TipTap or similar)
  - Image upload (featured + additional)
  - Validation (title 10-500 chars, body min 100 words)
- `frontend/src/components/ArticleImport/CSVUploadForm.tsx`:
  - Drag-and-drop CSV upload
  - CSV format help text
  - Preview imported articles before confirming
- `frontend/src/components/ArticleImport/JSONImportForm.tsx`:
  - Textarea for JSON paste OR file upload
  - JSON validation
  - Preview articles

**Acceptance Criteria**:
- All 3 import methods working
- Forms validate correctly
- CSV import shows preview before confirming
- Manual entry form submits successfully
- API integration complete (calls POST /v1/articles/import)
- Loading states and error handling
- Success message after import

**File Paths**:
- `frontend/src/pages/ImportArticlePage.tsx`
- `frontend/src/components/ArticleImport/ManualEntryForm.tsx`
- `frontend/src/components/ArticleImport/CSVUploadForm.tsx`
- `frontend/src/components/ArticleImport/JSONImportForm.tsx`
- `frontend/src/services/api/articles.ts`

---

#### T4.3 Build Article List & Detail Pages

**Description**: Pages for viewing and managing imported articles

**Dependencies**: T4.2

**Estimated Hours**: 8 hours

**Deliverables**:
- `frontend/src/pages/ArticlesListPage.tsx`:
  - Table of articles with columns: Title, Status, Source, SEO Optimized, Published, Actions
  - Filters: Status, Source, Date range
  - Search by title
  - Pagination (50 per page)
  - Bulk actions: Delete, Analyze SEO, Publish
- `frontend/src/pages/ArticleDetailPage.tsx`:
  - Article title, body, excerpt
  - Featured image and additional images
  - Metadata (word count, source, created date)
  - Actions: Edit, Analyze SEO, Publish, Delete
  - SEO metadata section (if analyzed)
  - Publishing history (if published)

**Acceptance Criteria**:
- Article list loads and displays correctly
- Filters and search working
- Pagination working
- Bulk actions functional
- Article detail page shows all info
- API integration complete (GET /v1/articles)
- Loading states and error handling

**File Paths**:
- `frontend/src/pages/ArticlesListPage.tsx`
- `frontend/src/pages/ArticleDetailPage.tsx`
- `frontend/src/components/Articles/ArticleTable.tsx`
- `frontend/src/components/Articles/ArticleDetailCard.tsx`

---

#### T4.4 Build SEO Optimization UI

**Description**: UI for triggering SEO analysis and editing metadata

**Dependencies**: T4.3

**Estimated Hours**: 10 hours

**Deliverables**:
- `frontend/src/components/SEO/SEOAnalysisPanel.tsx`:
  - "Analyze SEO" button (if not analyzed)
  - Real-time progress indicator during analysis
  - SEO metadata display after analysis:
    - Meta title with character counter (50-60)
    - Meta description with character counter (150-160)
    - Focus keyword badge
    - Primary keywords (3-5) as tags
    - Secondary keywords (5-10) as tags
    - Keyword density visualization (bar chart)
    - Readability score (gauge chart)
    - Optimization recommendations (list with icons)
- `frontend/src/components/SEO/SEOEditForm.tsx`:
  - Edit meta title (character counter, live preview)
  - Edit meta description (character counter, live preview)
  - Edit focus keyword
  - Save button (tracks manual override)
  - Reset to AI-generated button
- `frontend/src/components/SEO/KeywordDensityChart.tsx`:
  - Bar chart showing keyword density (Recharts)
  - Target range indicator (0.5-3%)
  - Color-coded (green=optimal, yellow=low, red=high)
- `frontend/src/components/SEO/ReadabilityGauge.tsx`:
  - Gauge chart for readability score
  - Grade level indicator (target: 8-12)

**Acceptance Criteria**:
- "Analyze SEO" button triggers analysis
- Progress indicator updates in real-time (polling)
- SEO metadata displays correctly after analysis
- Edit form allows changing title, description, focus keyword
- Character counters update in real-time
- Keyword density chart renders correctly
- Readability gauge shows current score
- Save button works (API: PUT /v1/seo/metadata/{id})
- Manual overrides tracked

**File Paths**:
- `frontend/src/components/SEO/SEOAnalysisPanel.tsx`
- `frontend/src/components/SEO/SEOEditForm.tsx`
- `frontend/src/components/SEO/KeywordDensityChart.tsx`
- `frontend/src/components/SEO/ReadabilityGauge.tsx`
- `frontend/src/services/api/seo.ts`

---

### Week 8: Publishing & Monitoring

#### T4.5 Build Publish Task UI

**Description**: UI for submitting publishing tasks and monitoring progress

**Dependencies**: T4.4

**Estimated Hours**: 10 hours

**Deliverables**:
- `frontend/src/components/Publishing/PublishModal.tsx`:
  - Modal triggered from article detail page
  - Provider selection dropdown (Anthropic, Gemini, Playwright)
  - Provider info (cost estimate, speed estimate, success rate)
  - Confirmation button
  - Closes after submission, redirects to task monitoring
- `frontend/src/components/Publishing/TaskProgress.tsx`:
  - Real-time progress indicator
  - Current step display (e.g., "Logging in to WordPress...")
  - Progress bar (% complete)
  - Estimated time remaining
  - Cancel button (for pending tasks)
- `frontend/src/components/Publishing/TaskStatusBadge.tsx`:
  - Color-coded badge for task status
  - Pending (gray), Running (blue), Completed (green), Failed (red)

**Acceptance Criteria**:
- Publish modal opens and displays provider options
- Provider selection updates cost/speed estimates
- Confirmation submits task (API: POST /v1/publish/submit)
- Task progress updates in real-time (polling GET /v1/publish/tasks/{id})
- Current step displays correctly
- Status badge shows correct color and text
- Cancel button works for pending tasks

**File Paths**:
- `frontend/src/components/Publishing/PublishModal.tsx`
- `frontend/src/components/Publishing/TaskProgress.tsx`
- `frontend/src/components/Publishing/TaskStatusBadge.tsx`
- `frontend/src/services/api/publish.ts`

---

#### T4.6 Build Screenshot Gallery

**Description**: UI for viewing publishing task screenshots

**Dependencies**: T4.5

**Estimated Hours**: 6 hours

**Deliverables**:
- `frontend/src/components/Publishing/ScreenshotGallery.tsx`:
  - Grid of screenshot thumbnails
  - Click to view full-size (lightbox)
  - Screenshot name/step label
  - Timestamp
  - Download button for each screenshot
- `frontend/src/components/Publishing/ScreenshotLightbox.tsx`:
  - Full-size screenshot display
  - Navigation (prev/next)
  - Close button
  - Download button

**Acceptance Criteria**:
- Screenshots load and display as thumbnails
- Clicking thumbnail opens lightbox
- Lightbox shows full-size screenshot
- Navigation works (prev/next)
- Download button downloads screenshot
- Handles 8+ screenshots gracefully

**File Paths**:
- `frontend/src/components/Publishing/ScreenshotGallery.tsx`
- `frontend/src/components/Publishing/ScreenshotLightbox.tsx`

---

#### T4.7 Build Task Monitoring Dashboard

**Description**: Dashboard for monitoring all publishing tasks

**Dependencies**: T4.6

**Estimated Hours**: 8 hours

**Deliverables**:
- `frontend/src/pages/TasksMonitoringPage.tsx`:
  - Table of all publishing tasks
  - Columns: Article, Provider, Status, Started, Duration, Actions
  - Filters: Status, Provider, Date range
  - Real-time updates (WebSocket or polling)
  - Click row to view details (screenshots, logs)
- `frontend/src/components/Publishing/TaskDetailModal.tsx`:
  - Task summary (article, provider, status, duration)
  - Screenshot gallery
  - Execution logs (chronological)
  - Error message (if failed)
  - Retry button (if failed)

**Acceptance Criteria**:
- Tasks table loads and displays all tasks
- Filters working
- Real-time updates (new tasks appear, status changes)
- Click row opens detail modal
- Detail modal shows screenshots and logs
- Retry button works for failed tasks
- API integration complete (GET /v1/publish/tasks)

**File Paths**:
- `frontend/src/pages/TasksMonitoringPage.tsx`
- `frontend/src/components/Publishing/TaskDetailModal.tsx`
- `frontend/src/components/Publishing/TasksTable.tsx`

---

#### T4.8 Build Provider Comparison Dashboard

**Description**: Dashboard comparing performance of different providers

**Dependencies**: T4.7

**Estimated Hours**: 8 hours

**Deliverables**:
- `frontend/src/pages/ProviderComparisonPage.tsx`:
  - Summary cards for each provider:
    - Success rate (%)
    - Average duration (seconds)
    - Total cost (USD)
    - Total tasks
  - Charts:
    - Success rate comparison (bar chart)
    - Average duration comparison (bar chart)
    - Cost per article (bar chart)
    - Task count over time (line chart)
  - Date range filter
  - Recommendations (based on metrics)

**Acceptance Criteria**:
- Provider summary cards display correct metrics
- Charts render correctly with real data
- Date range filter updates charts
- Recommendations based on data (e.g., "Playwright has highest success rate and zero cost")
- API integration (GET /v1/publish/tasks with aggregation)

**File Paths**:
- `frontend/src/pages/ProviderComparisonPage.tsx`
- `frontend/src/components/Analytics/ProviderComparisonCharts.tsx`
- `frontend/src/services/api/analytics.ts`

---

#### T4.9 Implement Real-Time Updates

**Description**: Real-time updates for task progress and status changes

**Dependencies**: T4.8

**Estimated Hours**: 4 hours

**Deliverables**:
- `frontend/src/hooks/useTaskUpdates.ts`:
  - Custom hook for polling task status
  - Polling interval: 2 seconds during execution, 10 seconds otherwise
  - Automatic stop when task completes/fails
- `frontend/src/hooks/useTaskList.ts`:
  - Custom hook for refreshing task list
  - Polling interval: 5 seconds
- React Query configuration for automatic refetching

**Acceptance Criteria**:
- Task progress updates in real-time (< 3 second delay)
- Task list refreshes automatically
- Polling stops when tasks complete
- No unnecessary API calls (efficient polling)
- Works across all pages

**File Paths**:
- `frontend/src/hooks/useTaskUpdates.ts`
- `frontend/src/hooks/useTaskList.ts`
- `frontend/src/services/query-client.ts`

---

#### T4.10 Build Settings Page

**Description**: Settings page for configuring CMS credentials and default provider

**Dependencies**: None (can run parallel)

**Estimated Hours**: 4 hours

**Deliverables**:
- `frontend/src/pages/SettingsPage.tsx`:
  - CMS Configuration section:
    - CMS URL input
    - Username input
    - Password input (masked)
    - Test connection button
  - Default Provider section:
    - Provider selection dropdown
    - Provider info and recommendations
  - Save button
  - Success/error messages

**Acceptance Criteria**:
- Settings form loads current values
- Test connection button validates CMS credentials
- Save button persists settings
- Password masked in UI
- API integration (GET/PUT /v1/settings)

**File Paths**:
- `frontend/src/pages/SettingsPage.tsx`
- `frontend/src/components/Settings/CMSConfigForm.tsx`
- `frontend/src/services/api/settings.ts`

---

**Phase 4 Checkpoint**: ✅ Frontend complete, all workflows functional, real-time updates working

---

## Phase 5: Testing, Optimization & Deployment (2 weeks) 🟡 PARTIAL

**Goal**: Comprehensive testing, performance optimization, and production deployment
**Duration**: 2 weeks (Week 9-10)
**Estimated Hours**: 72 hours
**Status**: 🟡 **80% Complete**
**Evidence**:
- ✅ Test infrastructure: `/backend/tests/` (integration, e2e, unit, services directories)
- ✅ Integration tests: Implemented
- ✅ E2E tests: Partially implemented
- ✅ Performance optimization: Proofreading engine 2.46ms load time
- 🟡 Test coverage: Estimated 70-80% (target 90%)
- 🟡 Production deployment: Staging deployment complete

---

### Week 9: Testing & Quality Assurance

#### T5.1 Unit Test Coverage

**Description**: Achieve 90%+ unit test coverage for backend

**Dependencies**: All Phase 1-4 tasks

**Estimated Hours**: 8 hours

**Deliverables**:
- Unit tests for all services:
  - Article importer components
  - SEO analyzer components
  - Computer Use providers
  - CMS publisher service
- Test coverage report
- Fix any bugs found during testing

**Acceptance Criteria**:
- Unit test coverage ≥ 90% for backend
- All tests pass
- No critical bugs remaining
- Coverage report generated

**File Paths**:
- `backend/tests/services/**/*.py`
- `backend/coverage.xml` (coverage report)

---

#### T5.2 Integration Tests

**Description**: End-to-end integration tests for all workflows

**Dependencies**: T5.1

**Estimated Hours**: 10 hours

**Deliverables**:
- Integration tests:
  - `test_full_workflow_anthropic.py`: Import → SEO → Publish (Anthropic)
  - `test_full_workflow_playwright.py`: Import → SEO → Publish (Playwright)
  - `test_batch_import_and_seo.py`: Batch import 100 articles → SEO analysis
  - `test_concurrent_publishing.py`: 5 articles published concurrently
  - `test_provider_fallback.py`: Playwright fails → Anthropic succeeds
  - `test_manual_seo_edit.py`: Analyze → Edit → Publish with manual changes

**Acceptance Criteria**:
- All 6 integration tests pass
- Tests use real test WordPress instance
- Tests clean up after themselves
- Tests run in < 10 minutes total

**File Paths**:
- `backend/tests/integration/test_full_workflow_*.py`

---

#### T5.3 End-to-End Tests

**Description**: E2E tests using Playwright for frontend

**Dependencies**: T5.2

**Estimated Hours**: 8 hours

**Deliverables**:
- E2E tests (Playwright for frontend):
  - `test_article_import_ui.spec.ts`: Import article via UI
  - `test_seo_analysis_ui.spec.ts`: Trigger SEO analysis and verify results
  - `test_seo_edit_ui.spec.ts`: Edit SEO metadata
  - `test_publish_ui.spec.ts`: Submit publish task and monitor progress
  - `test_screenshot_gallery_ui.spec.ts`: View screenshots

**Acceptance Criteria**:
- All 5 E2E tests pass
- Tests run against local development environment
- Tests cover critical user journeys
- Tests run in CI pipeline

**File Paths**:
- `frontend/tests/e2e/test_*.spec.ts`
- `frontend/playwright.config.ts`

---

#### T5.4 Provider Comparison Testing

**Description**: Systematic comparison of all 3 providers

**Dependencies**: T5.3

**Estimated Hours**: 6 hours

**Deliverables**:
- Provider comparison test suite:
  - Run 50 publishing tasks per provider
  - Record: success rate, average duration, cost, screenshots captured
  - Generate comparison report
- Comparison report:
  - Success rate by provider
  - Average duration by provider
  - Cost per article by provider
  - Screenshot quality comparison
  - Recommendations for which provider to use when

**Acceptance Criteria**:
- 150 total publishing tasks executed (50 per provider)
- All metrics recorded
- Comparison report generated
- Report includes clear recommendations
- Report published to `specs/001-cms-automation/provider-comparison-report.md`

**File Paths**:
- `backend/tests/comparison/test_provider_comparison.py`
- `specs/001-cms-automation/provider-comparison-report.md`

---

#### T5.5 Security Testing

**Description**: Security scan and vulnerability assessment

**Dependencies**: T5.4

**Estimated Hours**: 8 hours

**Deliverables**:
- Security scans:
  - Bandit (Python SAST) - no MEDIUM+ issues
  - Safety (dependency vulnerabilities) - no HIGH+ issues
  - npm audit (frontend dependencies) - no HIGH+ issues
  - Trivy (container scanning) - no HIGH/CRITICAL vulnerabilities
  - gitleaks (secret scanning) - no secrets in repository
- Security test:
  - Test XSS prevention in article import
  - Test SQL injection prevention
  - Test CSRF protection
  - Test authentication/authorization
  - Test rate limiting
- Security fixes for any issues found

**Acceptance Criteria**:
- Zero HIGH or CRITICAL vulnerabilities
- All security scans pass
- Security tests pass
- Security scan report generated
- Fixes implemented for all findings

**File Paths**:
- `backend/tests/security/test_security.py`
- `SECURITY_SCAN_REPORT.md` (updated)

---

### Week 10: Optimization & Deployment

#### T5.6 Performance Optimization

**Description**: Optimize application performance to meet SLAs

**Dependencies**: T5.5

**Estimated Hours**: 8 hours

**Deliverables**:
- Backend optimizations:
  - Database query optimization (EXPLAIN ANALYZE all slow queries)
  - Add missing indexes
  - Implement Redis caching for SEO keywords
  - Optimize article import batch processing
  - Connection pooling tuning
- Frontend optimizations:
  - Code splitting (lazy load routes)
  - Image optimization
  - Bundle size reduction
  - React Query caching optimization
- Performance benchmarks:
  - API response time (p95) < 500ms
  - SEO analysis < 30s (95th percentile)
  - Publishing < 5 min (95th percentile)
  - Import 100 articles < 5 min
- Performance report

**Acceptance Criteria**:
- All SLA targets met
- Performance improvements documented
- Benchmarks meet requirements
- No performance regressions

**File Paths**:
- `backend/tests/performance/test_performance.py`
- `specs/001-cms-automation/performance-report.md`

---

#### T5.7 Cost Optimization

**Description**: Optimize API costs and storage costs

**Dependencies**: T5.6

**Estimated Hours**: 4 hours

**Deliverables**:
- Cost optimization strategies:
  - Cache SEO analysis results (avoid re-analysis)
  - Compress screenshots (PNG → JPEG, reduce size)
  - Implement 90-day screenshot retention (delete old screenshots)
  - Use Playwright as default provider (free)
  - Reserve Anthropic for fallback only
- Cost tracking:
  - Log all API costs in database
  - Generate monthly cost report
  - Alert if costs exceed budget
- Cost optimization report:
  - Current costs per article
  - Optimized costs per article
  - Projected monthly costs

**Acceptance Criteria**:
- Average cost per article < $0.25 (with Playwright default)
- Screenshot storage < 100 GB per month
- Cost tracking implemented
- Cost optimization report generated

**File Paths**:
- `backend/src/services/cost_optimizer.py`
- `specs/001-cms-automation/cost-optimization-report.md`

---

#### T5.8 Production Environment Setup

**Description**: Setup production infrastructure on AWS

**Dependencies**: T5.7

**Estimated Hours**: 10 hours

**Deliverables**:
- AWS infrastructure:
  - RDS PostgreSQL 15 (Multi-AZ)
  - ElastiCache Redis (cluster mode)
  - S3 bucket for screenshots
  - AWS Secrets Manager for credentials
  - ECS Fargate for backend services
  - Application Load Balancer
  - CloudFront CDN for frontend
  - Route53 DNS
- Infrastructure as Code:
  - Terraform scripts for all infrastructure
  - Environment-specific configs (staging, production)
- Database migration:
  - Run all Alembic migrations on production DB
  - Verify schema
- Secrets migration:
  - Move all secrets to AWS Secrets Manager
  - Update application to fetch secrets at runtime

**Acceptance Criteria**:
- All infrastructure provisioned via Terraform
- Production database initialized and migrations applied
- All secrets stored in AWS Secrets Manager
- Infrastructure documented

**File Paths**:
- `infrastructure/terraform/main.tf`
- `infrastructure/terraform/variables.tf`
- `infrastructure/terraform/outputs.tf`
- `infrastructure/README.md`

---

#### T5.9 CI/CD Pipeline

**Description**: Setup continuous integration and deployment pipeline

**Dependencies**: T5.8

**Estimated Hours**: 8 hours

**Deliverables**:
- GitHub Actions workflows:
  - `.github/workflows/backend-ci.yml`:
    - Run unit tests
    - Run integration tests
    - Security scans (Bandit, Safety)
    - Code coverage report
    - Build Docker image
  - `.github/workflows/frontend-ci.yml`:
    - Run unit tests
    - Run E2E tests
    - Security scans (npm audit)
    - Build production bundle
  - `.github/workflows/deploy.yml`:
    - Deploy backend to ECS
    - Deploy frontend to S3/CloudFront
    - Run smoke tests
    - Rollback on failure
- Deployment strategy:
  - Blue-green deployment for zero downtime
  - Automatic rollback on health check failure

**Acceptance Criteria**:
- CI pipeline runs on every PR
- All tests and scans pass before merge
- CD pipeline deploys on merge to main
- Zero-downtime deployment
- Automatic rollback works

**File Paths**:
- `.github/workflows/backend-ci.yml`
- `.github/workflows/frontend-ci.yml`
- `.github/workflows/deploy.yml`

---

#### T5.10 Monitoring & Alerting Setup

**Description**: Setup production monitoring and alerting

**Dependencies**: T5.9

**Estimated Hours**: 6 hours

**Deliverables**:
- Grafana dashboards:
  - System health dashboard (CPU, memory, disk, network)
  - Application metrics dashboard (API latency, error rate, throughput)
  - Business metrics dashboard (articles imported, SEO analyzed, published)
  - Provider performance dashboard (success rate, duration, cost)
- Prometheus alerts:
  - Critical: API error rate > 5%, publishing success < 80%, database down
  - Warning: SEO analysis > 45s, screenshot storage > 400GB, queue depth > 50
- Alert channels:
  - PagerDuty for critical alerts
  - Slack for warnings
  - Email for daily summaries
- Log aggregation:
  - CloudWatch Logs or ELK stack
  - Structured JSON logs
  - Log retention: 90 days

**Acceptance Criteria**:
- All dashboards operational in Grafana
- Alerts configured and tested (trigger test alerts)
- Alert channels working (receive test alerts)
- Log aggregation working
- Runbook created for common alerts

**File Paths**:
- `monitoring/grafana/dashboards/`
- `monitoring/prometheus/alerts.yml`
- `monitoring/README.md` (runbook)

---

#### T5.11 Documentation Finalization

**Description**: Finalize all documentation for handoff

**Dependencies**: T5.10

**Estimated Hours**: 8 hours

**Deliverables**:
- Updated documentation:
  - `README.md`: Project overview, features, architecture
  - `specs/001-cms-automation/quickstart.md`: Getting started guide
  - `specs/001-cms-automation/api-spec.yaml`: Complete OpenAPI spec
  - `specs/001-cms-automation/deployment.md`: Deployment guide
  - `specs/001-cms-automation/monitoring.md`: Monitoring and alerting guide
  - `specs/001-cms-automation/troubleshooting.md`: Common issues and solutions
  - `specs/001-cms-automation/provider-guide.md`: When to use which provider
- Video demos:
  - Demo 1: Importing articles (3 methods)
  - Demo 2: SEO analysis and editing
  - Demo 3: Publishing with different providers
  - Demo 4: Monitoring tasks and screenshots

**Acceptance Criteria**:
- All documentation complete and accurate
- Documentation reviewed for clarity
- Video demos recorded and uploaded
- Documentation published

**File Paths**:
- `README.md`
- `specs/001-cms-automation/*.md`
- `docs/videos/` (demo recordings)

---

#### T5.12 Production Deployment

**Description**: Execute production deployment and post-deployment validation

**Dependencies**: T5.11

**Estimated Hours**: 4 hours

**Deliverables**:
- Production deployment:
  - Deploy backend to ECS
  - Deploy frontend to S3/CloudFront
  - Run database migrations
  - Verify all services healthy
- Smoke tests:
  - Import test article
  - Run SEO analysis
  - Publish with Playwright
  - Verify monitoring dashboards
  - Test alerts
- Post-deployment validation:
  - All services responding
  - Database connections working
  - Redis caching working
  - S3 uploads working
  - Secrets Manager integration working
- Go-live announcement

**Acceptance Criteria**:
- Zero-downtime deployment
- All smoke tests pass
- All services healthy
- Monitoring dashboards showing data
- No errors in logs
- Go-live announcement sent

**File Paths**:
- `DEPLOYMENT_CHECKLIST.md`
- `CHANGELOG.md` (updated with v2.0.0 release notes)

---

**Phase 5 Checkpoint**: ✅ Production deployment complete, all tests passing, monitoring active, system operational

---

## Phase 6: Google Drive Automation & Worklist 🆕 (5 weeks) ✅ COMPLETE

**Goal**: Enable automated document ingestion from Google Drive and provide comprehensive worklist UI
**Duration**: Week 11-15 (5 weeks)
**Estimated Hours**: 200 hours
**Status**: ✅ **Complete** (100%)
**Evidence**:
- ✅ Google Drive service: `/backend/src/services/google_drive/` (implemented)
- ✅ Worklist service: `/backend/src/services/worklist/` (implemented)
- ✅ API routes: `/backend/src/api/routes/worklist_routes.py` (5,235 lines)
- ✅ Worklist models: `/backend/src/models/worklist.py` (implemented)
- ✅ Status tracking: Article status history system implemented
- ✅ Real-time updates: WebSocket/polling support
**Reference**: [Google Drive Automation Analysis](../../docs/GOOGLE_DRIVE_AUTOMATION_ANALYSIS.md)

---

### Week 11-12: Google Drive Integration

#### T6.1 [P0] [US6] Setup Google Drive API Integration

**Description**: Configure Google Drive API access with OAuth 2.0 or Service Account authentication

**Dependencies**: None

**Estimated Hours**: 12 hours

**Deliverables**:
- Google Drive API credentials configured
- Service account JSON key (if using service account)
- OAuth 2.0 client ID/secret (if using OAuth)
- Environment variables configured
- Test connection script

**Acceptance Criteria**:
- [ ] Google Drive API enabled in Google Cloud Console
- [ ] Credentials stored securely in environment variables
- [ ] Test script successfully lists files from configured folder
- [ ] Credentials never logged or exposed
- [ ] Documentation for credential setup process

**File Paths**:
- `backend/.env` (add GOOGLE_DRIVE_FOLDER_ID, GOOGLE_CREDENTIALS_PATH)
- `backend/config/google_drive.py` (configuration loader)
- `docs/GOOGLE_DRIVE_SETUP.md` (setup guide)

---

#### T6.2 [P0] [US6] Implement GoogleDriveMonitor Service

**Description**: Create service class that monitors Google Drive folder for new documents

**Dependencies**: T6.1

**Estimated Hours**: 16 hours

**Deliverables**:
- `backend/src/services/google_drive_monitor.py`
- `GoogleDriveMonitor` class with methods:
  - `scan_for_new_documents(since: datetime) -> List[Dict]`
  - `read_document_content(doc_id: str) -> str`
  - `mark_as_processed(doc_id: str) -> None`
- Unit tests with mocked Google API

**Acceptance Criteria**:
- [ ] Can scan Google Drive folder and return list of new docs
- [ ] Can read Google Doc content and return plain text
- [ ] Can mark documents as processed (move to subfolder or add metadata)
- [ ] Handles API rate limits with exponential backoff
- [ ] Refreshes expired OAuth tokens automatically
- [ ] Unit tests achieve 90% coverage

**File Paths**:
- `backend/src/services/google_drive_monitor.py`
- `backend/tests/unit/services/test_google_drive_monitor.py`

**Code Example**:
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class GoogleDriveMonitor:
    def __init__(self, credentials: Credentials, folder_id: str):
        self.service = build('drive', 'v3', credentials=credentials)
        self.docs_service = build('docs', 'v1', credentials=credentials)
        self.folder_id = folder_id

    def scan_for_new_documents(self, since: datetime) -> List[Dict]:
        query = (
            f"'{self.folder_id}' in parents "
            f"and mimeType = 'application/vnd.google-apps.document' "
            f"and createdTime > '{since.isoformat()}' "
            f"and trashed = false"
        )
        results = self.service.files().list(q=query, pageSize=100).execute()
        return results.get('files', [])
```

---

#### T6.3 [P0] [US6] Create Database Migrations for Google Drive Tables

**Description**: Create Alembic migrations for new tables: `google_drive_documents` and `article_status_history`, and modify `articles` table

**Dependencies**: None (can run in parallel)

**Estimated Hours**: 8 hours

**Deliverables**:
- Migration file: `backend/migrations/versions/YYYYMMDD_google_drive_automation.py`
- Rollback logic tested

**Acceptance Criteria**:
- [ ] Migration creates `google_drive_documents` table with all fields
- [ ] Migration creates `article_status_history` table with all fields
- [ ] Migration adds new columns to `articles` table
- [ ] All indexes created (google_doc_id unique, article_id foreign key, status index)
- [ ] Migration runs successfully on empty database
- [ ] Migration runs successfully on database with existing data
- [ ] Rollback restores original schema

**File Paths**:
- `backend/migrations/versions/YYYYMMDD_google_drive_automation.py`

**Code Example**:
```python
def upgrade():
    # Create google_drive_documents table
    op.create_table(
        'google_drive_documents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('google_doc_id', sa.String(255), unique=True, nullable=False),
        sa.Column('file_name', sa.String(500), nullable=False),
        sa.Column('folder_id', sa.String(255)),
        sa.Column('article_id', sa.Integer(), sa.ForeignKey('articles.id')),
        sa.Column('status', sa.String(20), server_default='discovered'),
        sa.Column('discovered_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime()),
        sa.Column('error_message', sa.Text()),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('metadata', JSONB),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now())
    )

    # Create article_status_history table
    op.create_table(
        'article_status_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('article_id', sa.Integer(), sa.ForeignKey('articles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('old_status', sa.String(30)),
        sa.Column('new_status', sa.String(30), nullable=False),
        sa.Column('changed_by', sa.String(100)),
        sa.Column('change_reason', sa.String(500)),
        sa.Column('metadata', JSONB),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # Modify articles table
    op.add_column('articles', sa.Column('source_type', sa.String(20), server_default='manual'))
    op.add_column('articles', sa.Column('google_drive_doc_id', sa.String(255)))
    op.add_column('articles', sa.Column('current_status', sa.String(30), server_default='pending'))
    op.add_column('articles', sa.Column('status_updated_at', sa.DateTime(), server_default=sa.func.now()))
    op.add_column('articles', sa.Column('processing_started_at', sa.DateTime()))
    op.add_column('articles', sa.Column('processing_completed_at', sa.DateTime()))
    op.add_column('articles', sa.Column('total_processing_duration_seconds', sa.Integer()))
```

---

#### T6.4 [P0] [US6] Implement Celery Scheduled Tasks

**Description**: Create Celery tasks for automatic Google Drive scanning and document import

**Dependencies**: T6.2, T6.3

**Estimated Hours**: 12 hours

**Deliverables**:
- `backend/src/tasks/google_drive_tasks.py`
- Two Celery tasks:
  - `scan_google_drive_for_new_documents()`
  - `import_google_drive_document(google_doc_id: int)`
- Celery Beat configuration

**Acceptance Criteria**:
- [ ] `scan_google_drive_for_new_documents` runs every 5 minutes via Celery Beat
- [ ] New documents are saved to `google_drive_documents` table with status='discovered'
- [ ] `import_google_drive_document` reads content and creates `articles` record
- [ ] Failed imports retry up to 3 times with exponential backoff
- [ ] Task logs include correlation IDs for debugging
- [ ] Test with mock Google Drive API

**File Paths**:
- `backend/src/tasks/google_drive_tasks.py`
- `backend/config/celery_config.py` (update beat_schedule)
- `backend/tests/integration/test_google_drive_workflow.py`

**Code Example**:
```python
@shared_task(name="scan_google_drive_for_new_documents")
def scan_google_drive_for_new_documents():
    monitor = GoogleDriveMonitor(...)
    new_documents = monitor.scan_for_new_documents()

    for doc in new_documents:
        google_doc = GoogleDriveDocument.create(
            google_doc_id=doc['id'],
            file_name=doc['name'],
            status='discovered'
        )
        import_google_drive_document.delay(google_doc.id)

@shared_task(bind=True, max_retries=3)
def import_google_drive_document(self, google_doc_id: int):
    try:
        google_doc = GoogleDriveDocument.get_by_id(google_doc_id)
        monitor = GoogleDriveMonitor(...)
        content = monitor.read_document_content(google_doc.google_doc_id)

        article = Article.create(
            title=parse_title(content),
            content=parse_content(content),
            source_type='google_drive',
            google_drive_doc_id=google_doc.google_doc_id,
            current_status='pending'
        )

        google_doc.update(article_id=article.id, status='imported')
        trigger_proofreading_workflow.delay(article.id)

    except Exception as e:
        google_doc.update(status='failed', error_message=str(e))
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
```

---

#### T6.5 [P0] [US6] Implement Content Parser

**Description**: Parse Google Doc content to extract title, body, meta description, and keywords

**Dependencies**: T6.2

**Estimated Hours**: 10 hours

**Deliverables**:
- `backend/src/utils/google_doc_parser.py`
- Parsing functions for structured content

**Acceptance Criteria**:
- [ ] Parses three-part format: 正文 / Meta描述 / SEO关键词
- [ ] Extracts title from first heading or first line
- [ ] Handles missing sections gracefully (use defaults)
- [ ] Preserves basic formatting (paragraphs, bold, lists)
- [ ] Extracts image references
- [ ] Unit tests with sample Google Doc formats

**File Paths**:
- `backend/src/utils/google_doc_parser.py`
- `backend/tests/unit/utils/test_google_doc_parser.py`

---

#### T6.6 [P1] [US6] Implement Article Status Tracker

**Description**: Service that records all article status changes to audit trail

**Dependencies**: T6.3

**Estimated Hours**: 12 hours

**Deliverables**:
- `backend/src/services/article_status_tracker.py`
- `ArticleStatusTracker` class with methods:
  - `record_status_change(article_id, old_status, new_status, changed_by, reason)`
  - `get_status_history(article_id) -> List[StatusChange]`
  - `rollback_status(article_id, reason) -> bool`

**Acceptance Criteria**:
- [ ] Every article status change recorded to `article_status_history`
- [ ] Includes timestamp, old/new status, operator (user or 'system')
- [ ] Can retrieve full status history for an article
- [ ] Can rollback to previous status on failure
- [ ] Integrated into existing workflow triggers
- [ ] Unit tests achieve 90% coverage

**File Paths**:
- `backend/src/services/article_status_tracker.py`
- `backend/tests/unit/services/test_article_status_tracker.py`

---

#### T6.7 [P1] [US6] Google Drive Integration Tests

**Description**: End-to-end integration tests for Google Drive workflow

**Dependencies**: T6.1-T6.6

**Estimated Hours**: 10 hours

**Deliverables**:
- Integration test suite
- Test fixtures with sample Google Docs

**Acceptance Criteria**:
- [ ] Test: Create test Google Doc → Scanner discovers it → Import triggers → Article created
- [ ] Test: Google API rate limit → Exponential backoff works
- [ ] Test: Invalid document format → Fails gracefully with error message
- [ ] Test: Duplicate document → Detects and skips
- [ ] All tests run in CI/CD pipeline
- [ ] Tests clean up after themselves (delete test docs)

**File Paths**:
- `backend/tests/integration/test_google_drive_workflow.py`
- `backend/tests/fixtures/sample_google_doc.json`

---

**Week 11-12 Checkpoint**: ✅ Google Drive integration complete, documents auto-importing, status tracking operational

---

### Week 13-14: Worklist UI

#### T6.8 [P0] [US6] Create Worklist Page Component

**Description**: Main Worklist page showing all documents in the processing pipeline

**Dependencies**: None (can start in parallel with backend)

**Estimated Hours**: 16 hours

**Deliverables**:
- `frontend/src/pages/WorklistPage.tsx`
- `frontend/src/components/Worklist/WorklistTable.tsx`
- `frontend/src/components/Worklist/WorklistFilters.tsx`
- `frontend/src/components/Worklist/WorklistStatistics.tsx`

**Acceptance Criteria**:
- [ ] Page accessible via `/worklist` route
- [ ] Table displays: ID, Title, Source, Status, Created Time, Actions
- [ ] Filters: Status dropdown, Date range picker, Keyword search
- [ ] Sorting: Created Time, Updated Time, Status
- [ ] Pagination: 20/50/100 items per page
- [ ] Responsive design (desktop, tablet, mobile)
- [ ] Loading skeleton while fetching data
- [ ] Empty state when no documents

**File Paths**:
- `frontend/src/pages/WorklistPage.tsx`
- `frontend/src/components/Worklist/WorklistTable.tsx`
- `frontend/src/components/Worklist/WorklistFilters.tsx`
- `frontend/src/components/Worklist/WorklistStatistics.tsx`

---

#### T6.9 [P0] [US6] Implement Status Badge Component

**Description**: Reusable status badge component with 7 variants

**Dependencies**: None

**Estimated Hours**: 4 hours

**Deliverables**:
- `frontend/src/components/Worklist/StatusBadge.tsx`
- 7 status variants styled with colors and icons

**Acceptance Criteria**:
- [ ] Supports 7 statuses: pending, proofreading, under_review, ready_to_publish, publishing, published, failed
- [ ] Color-coded: Gray, Yellow, Blue, Green, Blue(pulse), DarkGreen, Red
- [ ] Icons for each status (from Heroicons or similar)
- [ ] Pulse animation for "publishing" status
- [ ] TypeScript types defined
- [ ] Storybook story created

**File Paths**:
- `frontend/src/components/Worklist/StatusBadge.tsx`
- `frontend/src/components/Worklist/StatusBadge.stories.tsx`

---

#### T6.10 [P0] [US6] Create Worklist Detail Drawer

**Description**: Side drawer showing full document details and status history

**Dependencies**: T6.8

**Estimated Hours**: 12 hours

**Deliverables**:
- `frontend/src/components/Worklist/WorklistDetailDrawer.tsx`
- `frontend/src/components/Worklist/StatusHistoryTimeline.tsx`
- `frontend/src/components/Worklist/OperationLogs.tsx`

**Acceptance Criteria**:
- [ ] Drawer slides in from right (480px wide)
- [ ] Displays full document content (scrollable)
- [ ] Status history timeline (vertical, with timestamps)
- [ ] Operation logs with timestamps
- [ ] Action buttons: Edit, Delete, Retry (if failed), View in Google Drive
- [ ] Close button (X) in top-right
- [ ] Click outside to close
- [ ] Smooth slide animation (300ms)

**File Paths**:
- `frontend/src/components/Worklist/WorklistDetailDrawer.tsx`
- `frontend/src/components/Worklist/StatusHistoryTimeline.tsx`
- `frontend/src/components/Worklist/OperationLogs.tsx`

---

#### T6.11 [P0] [US6] Implement Real-time Updates with WebSocket

**Description**: WebSocket integration for real-time Worklist updates

**Dependencies**: T6.8, T6.14 (backend WebSocket)

**Estimated Hours**: 12 hours

**Deliverables**:
- `frontend/src/hooks/useWorklistRealtime.ts`
- WebSocket connection management
- Fallback to polling

**Acceptance Criteria**:
- [ ] Connects to WebSocket endpoint `/api/v1/worklist/ws`
- [ ] Handles `status_update` messages (updates existing row)
- [ ] Handles `new_article` messages (adds new row to top)
- [ ] Automatically reconnects on disconnect
- [ ] Falls back to polling (every 5s) if WebSocket unavailable
- [ ] Shows connection status indicator
- [ ] Updates happen instantly (<2s latency)

**File Paths**:
- `frontend/src/hooks/useWorklistRealtime.ts`
- `frontend/src/services/websocket.ts`

**Code Example**:
```typescript
export function useWorklistRealtime() {
  const [articles, setArticles] = useState([]);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/api/v1/worklist/ws');

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'status_update') {
        setArticles(prev =>
          prev.map(article =>
            article.id === message.article_id
              ? { ...article, current_status: message.new_status }
              : article
          )
        );
      } else if (message.type === 'new_article') {
        setArticles(prev => [message.article, ...prev]);
      }
    };

    return () => ws.close();
  }, []);

  return { articles, setArticles };
}
```

---

#### T6.12 [P1] [US6] Implement Statistics Dashboard

**Description**: Statistics cards showing document counts by status

**Dependencies**: T6.8

**Estimated Hours**: 8 hours

**Deliverables**:
- `frontend/src/components/Worklist/WorklistStatistics.tsx`
- Statistics cards component

**Acceptance Criteria**:
- [ ] Displays 7 cards (one per status)
- [ ] Shows count for each status
- [ ] Color-coded to match status badges
- [ ] Auto-updates when statuses change
- [ ] Clickable to filter by that status
- [ ] Responsive grid layout

**File Paths**:
- `frontend/src/components/Worklist/WorklistStatistics.tsx`

---

#### T6.13 [P1] [US6] Implement Batch Operations

**Description**: Batch operations for multiple documents (delete, retry, mark pending)

**Dependencies**: T6.8

**Estimated Hours**: 8 hours

**Deliverables**:
- Checkbox selection in table
- Batch action dropdown
- Confirmation dialog

**Acceptance Criteria**:
- [ ] Checkbox in table header (select all)
- [ ] Checkbox in each row
- [ ] Batch action dropdown appears when items selected
- [ ] Actions: Delete, Retry (failed only), Mark as Pending
- [ ] Confirmation dialog before executing
- [ ] Progress indicator for batch operation
- [ ] Success/failure feedback toast

**File Paths**:
- `frontend/src/components/Worklist/BatchOperations.tsx`

---

#### T6.14 [P0] [US6] Backend Worklist APIs

**Description**: Implement backend API endpoints for Worklist

**Dependencies**: T6.3 (database tables)

**Estimated Hours**: 16 hours

**Deliverables**:
- `backend/src/api/routes/worklist.py`
- API endpoints for Worklist operations
- WebSocket handler

**Acceptance Criteria**:
- [ ] `GET /api/v1/worklist` - List documents with filtering/sorting/pagination
- [ ] `GET /api/v1/worklist/{article_id}` - Get document with status history
- [ ] `POST /api/v1/worklist/batch-action` - Batch operations
- [ ] WebSocket `/api/v1/worklist/ws` - Real-time updates
- [ ] All endpoints authenticated (JWT)
- [ ] OpenAPI documentation updated
- [ ] Unit tests achieve 90% coverage

**File Paths**:
- `backend/src/api/routes/worklist.py`
- `backend/tests/unit/api/test_worklist.py`

**Code Example**:
```python
@router.get("/v1/worklist")
async def get_worklist(
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = 'created_at',
    order: str = 'desc',
    current_user: User = Depends(get_current_user)
) -> WorklistResponse:
    query = Article.query

    if status and status != 'all':
        query = query.filter(Article.current_status == status)

    if keyword:
        query = query.filter(
            or_(
                Article.title.ilike(f'%{keyword}%'),
                Article.content.ilike(f'%{keyword}%')
            )
        )

    query = query.order_by(getattr(Article, sort_by).desc() if order == 'desc' else getattr(Article, sort_by).asc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return WorklistResponse(
        items=[article.to_dict() for article in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )
```

---

#### T6.15 [P1] [US6] Worklist UI Tests

**Description**: E2E tests for Worklist functionality

**Dependencies**: T6.8-T6.14

**Estimated Hours**: 4 hours

**Deliverables**:
- Playwright E2E tests for Worklist

**Acceptance Criteria**:
- [ ] Test: Navigate to Worklist page → Table displays
- [ ] Test: Filter by status → Filtered results shown
- [ ] Test: Search by keyword → Matching articles shown
- [ ] Test: Click row → Detail drawer opens
- [ ] Test: Real-time update → New article appears
- [ ] Test: Batch select and delete → Articles deleted
- [ ] All tests pass in CI/CD

**File Paths**:
- `frontend/tests/e2e/worklist.spec.ts`

---

**Week 13-14 Checkpoint**: ✅ Worklist UI complete, real-time updates working, batch operations functional

---

### Week 15: Integration & Testing

#### T6.16 [P0] [US6] End-to-End Workflow Integration Test

**Description**: Test complete workflow from Google Drive to published article

**Dependencies**: T6.1-T6.15

**Estimated Hours**: 12 hours

**Deliverables**:
- Comprehensive E2E test suite
- Test report

**Acceptance Criteria**:
- [ ] Test: Create Google Doc → Auto-discovered → Imported → Status pending
- [ ] Test: Trigger proofread → Status proofreading → Status under_review
- [ ] Test: Approve → Status ready_to_publish → Publish → Status publishing → Status published
- [ ] Test: Check Worklist at each step → Status updated in real-time
- [ ] Test: View status history → All transitions recorded
- [ ] Test: Failure scenario → Status failed → Rollback works
- [ ] Test runs end-to-end in <10 minutes

**File Paths**:
- `backend/tests/e2e/test_google_drive_to_publish.py`

---

#### T6.17 [P0] [US6] Performance Testing

**Description**: Load testing with large number of documents

**Dependencies**: T6.1-T6.15

**Estimated Hours**: 8 hours

**Deliverables**:
- Performance test suite
- Performance report

**Acceptance Criteria**:
- [ ] Test: Worklist with 1000+ documents loads <1 second
- [ ] Test: Concurrent Google Drive scans (5 documents) complete <30 seconds
- [ ] Test: 100 status updates via WebSocket process <5 seconds
- [ ] Database queries optimized (add indexes if needed)
- [ ] No memory leaks in WebSocket connections
- [ ] Performance metrics logged to monitoring

**File Paths**:
- `backend/tests/performance/test_worklist_performance.py`

---

#### T6.18 [P0] [US6] Error Handling & Recovery Tests

**Description**: Test error scenarios and recovery mechanisms

**Dependencies**: T6.1-T6.15

**Estimated Hours**: 8 hours

**Deliverables**:
- Error scenario test suite

**Acceptance Criteria**:
- [ ] Test: Google API rate limit → Exponential backoff → Retry succeeds
- [ ] Test: Network timeout during import → Retry succeeds
- [ ] Test: Invalid Google Doc format → Error recorded → Status failed
- [ ] Test: Publish failure → Status rollback to ready_to_publish
- [ ] Test: WebSocket disconnect → Reconnect succeeds → Updates resume
- [ ] All errors logged with context
- [ ] No uncaught exceptions

**File Paths**:
- `backend/tests/integration/test_error_scenarios.py`

---

#### T6.19 [P0] [US6] Documentation

**Description**: Create user and developer documentation for Google Drive feature

**Dependencies**: T6.1-T6.18

**Estimated Hours**: 6 hours

**Deliverables**:
- `docs/GOOGLE_DRIVE_SETUP.md` - Setup guide
- `docs/WORKLIST_USER_GUIDE.md` - User guide
- Updated API documentation

**Acceptance Criteria**:
- [ ] Setup guide covers Google API credentials configuration
- [ ] User guide explains Worklist features with screenshots
- [ ] API docs updated with new endpoints
- [ ] Troubleshooting section for common issues
- [ ] Reviewed and approved by team

**File Paths**:
- `docs/GOOGLE_DRIVE_SETUP.md`
- `docs/WORKLIST_USER_GUIDE.md`
- `docs/API_DOCUMENTATION.md` (update)

---

#### T6.20 [P0] [US6] Bug Fixes & Final Polish

**Description**: Address issues found during testing and polish UI

**Dependencies**: T6.16-T6.19

**Estimated Hours**: 6 hours

**Deliverables**:
- Bug fixes
- UI polish
- Final review

**Acceptance Criteria**:
- [ ] All bugs from testing addressed
- [ ] UI polish: animations smooth, loading states clear, error messages helpful
- [ ] Code review completed
- [ ] All tests passing
- [ ] Ready for production deployment

**File Paths**:
- Various (bug fixes across codebase)

---

**Phase 6 Checkpoint**: ✅ Google Drive automation operational, Worklist UI complete, full workflow tested, ready for production

---

## Phase 7: Article Structured Parsing 🆕 (7 weeks)

**Goal**: Transform raw Google Doc HTML into normalized, structured data (title parts, author, images with specs, body, SEO metadata) with quality confirmation UI, and integrate with proofreading workflow
**Duration**: 7 weeks (Week 16-23)
**Estimated Hours**: 151 hours (140 parsing + 11 proofreading integration)
**Status**: Not Started ⏳
**Dependencies**: Phase 6 (Google Drive integration, Worklist UI)
**Reference**: See `docs/ARTICLE_PARSING_TECHNICAL_ANALYSIS.md`, `docs/article_parsing_requirements.md`, `backend/docs/phase7_proofreading_integration_analysis.md`

**Key Deliverables**:
- ✅ Extended database schema with parsing fields
- ✅ AI-driven ArticleParserService (Claude 4.5 Sonnet)
- ✅ ImageProcessor service with PIL specs extraction
- ✅ Proofreading Step 1 UI (解析確認)
- ✅ Two-step workflow with Step 2 blocking logic
- ✅ Proofreading integration (body_html priority, backward compatibility)
- ✅ 85%+ test coverage (backend), 80%+ (frontend)

---

### Week 16: Database Schema & Migrations (16 hours)

#### T7.1 [US7][P0] Design Extended Articles Schema

**Description**: Design final database schema for extended `articles` table with structured parsing fields, new `article_images` table with JSONB metadata, and `article_image_reviews` table for reviewer feedback.

**Dependencies**: None

**Estimated Hours**: 4 hours

**Deliverables**:
- ER diagram showing `articles` ← `article_images` ← `article_image_reviews` relationships
- SQL DDL for all new fields and tables
- JSONB metadata structure specification for `article_images.metadata`
- Design document with field naming conventions and data types

**Acceptance Criteria**:
- [ ] All parsing fields documented (title_prefix, title_main, title_suffix, author_line, author_name, body_html, meta_description, seo_keywords, tags)
- [ ] `article_images` table includes: preview_path, source_path, source_url, caption, position, metadata JSONB
- [ ] `article_image_reviews` table supports actions: keep, remove, replace_caption, replace_source
- [ ] ER diagram approved by tech lead

**File Paths**:
- `specs/001-cms-automation/data-model.md` (updated)
- `docs/parsing-schema-design.md` (new)

---

#### T7.2 [US7][P0] Create Alembic Migration Script

**Description**: Create comprehensive Alembic migration to add parsing fields to `articles` table, create `article_images` and `article_image_reviews` tables, add indexes, and ensure backwards compatibility.

**Dependencies**: T7.1

**Estimated Hours**: 6 hours

**Deliverables**:
- Migration file: `migrations/versions/20251108_article_parsing.py`
- Downgrade logic for safe rollback
- Index creation for `(article_id, position)` on `article_images`
- Update trigger for `article_images.updated_at`

**Acceptance Criteria**:
- [ ] Migration adds 13 new columns to `articles` table
- [ ] Creates `article_images` table with CHECK constraint `position >= 0`
- [ ] Creates `article_image_reviews` table with action ENUM constraint
- [ ] Creates indexes: `idx_article_images_article_id`, `idx_article_images_position`
- [ ] Downgrade logic tested (can rollback without data loss)
- [ ] Migration idempotent (safe to run multiple times)

**File Paths**:
- `backend/migrations/versions/20251108_article_parsing.py`

---

#### T7.3 [US7][P0] Update SQLAlchemy Models

**Description**: Extend `Article` model with parsing fields, create `ArticleImage` and `ArticleImageReview` models with proper relationships and constraints.

**Dependencies**: T7.2

**Estimated Hours**: 4 hours

**Deliverables**:
- Updated `Article` model in `backend/src/models/article.py`
- New `ArticleImage` model in `backend/src/models/article_image.py`
- New `ArticleImageReview` model in `backend/src/models/article_image_review.py`
- Relationship definitions (one-to-many, cascade deletes)

**Acceptance Criteria**:
- [ ] `Article` model has all parsing fields with correct types
- [ ] `ArticleImage` model has `metadata` as JSONB column
- [ ] Relationships configured: `article.images`, `article_image.reviews`
- [ ] Cascade deletes configured (ON DELETE CASCADE)
- [ ] Models pass SQLAlchemy validation
- [ ] Type hints complete (Pydantic integration ready)

**File Paths**:
- `backend/src/models/article.py`
- `backend/src/models/article_image.py`
- `backend/src/models/article_image_review.py`

---

#### T7.4 [US7][P0] Test Migration on Dev Database

**Description**: Execute migration on development database, insert test data, verify indexes and constraints, measure migration performance.

**Dependencies**: T7.2, T7.3

**Estimated Hours**: 2 hours

**Deliverables**:
- Migration execution log (success/failure)
- Test data insertion script
- Index usage verification query results
- Performance benchmark (migration duration)

**Acceptance Criteria**:
- [ ] Migration completes in <5 minutes on dev database
- [ ] Sample article with parsing fields inserts successfully
- [ ] Sample images with JSONB metadata insert successfully
- [ ] Indexes verified with `EXPLAIN ANALYZE`
- [ ] Downgrade tested and verified
- [ ] Zero data loss confirmed

**File Paths**:
- `backend/tests/migrations/test_20251108_article_parsing.py`
- Migration log: `logs/migration-20251108.log`

---

### Week 17-18: Backend Parsing Engine (40 hours)

#### T7.5 [US7][P0] Implement ArticleParserService Skeleton

**Description**: Create `ArticleParserService` with main `parse_document()` orchestration method, define dataclasses for structured parsing results (`ParsedArticle`, `HeaderFields`, `AuthorFields`, `ImageRecord`, `MetaSEOFields`).

**Dependencies**: T7.3

**Estimated Hours**: 6 hours

**Deliverables**:
- `ArticleParserService` class in `backend/src/services/parser/article_parser.py`
- Dataclasses in `backend/src/services/parser/types.py`
- Main orchestration method with placeholder implementations
- Dependency injection setup (LLM client, storage service)

**Acceptance Criteria**:
- [ ] `parse_document(raw_html: str, article_id: int) -> ParsedArticle` method signature defined
- [ ] All dataclasses have complete type hints
- [ ] Service initializes with Anthropic client and storage service
- [ ] Placeholder implementations for: `_parse_header()`, `_extract_author()`, `_extract_images()`, `_extract_meta_seo()`, `_clean_body_html()`
- [ ] Unit test skeleton created

**File Paths**:
- `backend/src/services/parser/article_parser.py`
- `backend/src/services/parser/types.py`
- `backend/tests/unit/services/parser/test_article_parser.py`

---

#### T7.6 [US7][P0] Implement Header Parsing (AI + Fallback)

**Description**: Implement `_parse_header()` method using Claude 4.5 Sonnet to detect 1/2/3-line title structure, with regex-based fallback for same-line separators (｜, —, ：). Extract `title_prefix`, `title_main`, `title_suffix`.

**Dependencies**: T7.5

**Estimated Hours**: 8 hours

**Deliverables**:
- `_parse_header()` method implementation
- Claude prompt template for title parsing
- Regex fallback logic for inline separators
- Unit tests with mocked Claude responses
- Test fixtures with diverse title formats

**Acceptance Criteria**:
- [ ] Correctly parses 3-line titles (prefix, main, suffix)
- [ ] Correctly parses 2-line titles (main, suffix)
- [ ] Correctly parses 1-line titles (main only)
- [ ] Fallback regex handles: "前標｜主標｜副標", "前標—主標", "主標：副標"
- [ ] Unit tests cover 10+ title variations
- [ ] AI parsing accuracy ≥90% on test set
- [ ] Gracefully handles malformed titles (returns main only)

**File Paths**:
- `backend/src/services/parser/article_parser.py` (update)
- `backend/src/services/parser/prompts/title_parsing.txt`
- `backend/tests/unit/services/parser/test_header_parsing.py`
- `backend/tests/fixtures/sample_titles.json`

---

#### T7.7 [US7][P0] Implement Author Extraction

**Description**: Implement `_extract_author()` method using Claude to detect author patterns ("文／XXX", "撰稿／XXX", "作者：XXX"). Extract raw `author_line` and cleaned `author_name`.

**Dependencies**: T7.5

**Estimated Hours**: 4 hours

**Deliverables**:
- `_extract_author()` method implementation
- Claude prompt template for author extraction
- Cleaning logic (strip prefixes, whitespace)
- Unit tests with mocked Claude responses

**Acceptance Criteria**:
- [ ] Detects "文／張三" → author_line="文／張三", author_name="張三"
- [ ] Detects "撰稿／李四" → author_line="撰稿／李四", author_name="李四"
- [ ] Detects "作者：王五" → author_line="作者：王五", author_name="王五"
- [ ] Handles missing author (returns None)
- [ ] Unit tests cover 8+ author variations
- [ ] AI extraction accuracy ≥95%

**File Paths**:
- `backend/src/services/parser/article_parser.py` (update)
- `backend/src/services/parser/prompts/author_extraction.txt`
- `backend/tests/unit/services/parser/test_author_extraction.py`

---

#### T7.8 [US7][P0] Implement Image Extraction

**Description**: Implement `_extract_images()` method to parse DOM, identify image blocks (preview + caption + source link), download high-res images, extract paragraph position, create `ImageRecord` instances.

**Dependencies**: T7.5, T7.9 (ImageProcessor)

**Estimated Hours**: 10 hours

**Deliverables**:
- `_extract_images()` method implementation
- DOM parsing logic (BeautifulSoup)
- Image download with retry logic
- Position tracking (paragraph index)
- Integration with `ImageProcessor` service

**Acceptance Criteria**:
- [ ] Identifies image blocks with preview, caption, and "點此下載" link
- [ ] Downloads high-res images from source URLs
- [ ] Records correct paragraph position (0-based index)
- [ ] Handles download failures gracefully (retries 3x, saves partial result)
- [ ] Replaces inline image nodes with placeholders
- [ ] Unit tests cover 5+ image extraction scenarios
- [ ] Integration test with mock HTTP downloads

**File Paths**:
- `backend/src/services/parser/article_parser.py` (update)
- `backend/tests/unit/services/parser/test_image_extraction.py`
- `backend/tests/integration/test_image_download.py`

---

#### T7.9 [US7][P0] Implement ImageProcessor Service

**Description**: Create `ImageProcessor` service to download images from URLs, extract technical specs using PIL/Pillow (width, height, aspect ratio, file size, MIME type, EXIF data), store in chosen backend.

**Dependencies**: T7.3

**Estimated Hours**: 6 hours

**Deliverables**:
- `ImageProcessor` class in `backend/src/services/media/image_processor.py`
- `download_and_process()` method with HTTP download
- `extract_specs()` method using PIL
- Storage backend integration (Supabase Storage or Google Drive)

**Acceptance Criteria**:
- [ ] Downloads images from HTTP/HTTPS URLs
- [ ] Extracts: width, height, format, MIME type, file size
- [ ] Extracts EXIF date if available
- [ ] Calculates aspect ratio (e.g., "16:9")
- [ ] Stores in configured backend (path returned)
- [ ] Handles corrupt images gracefully
- [ ] Unit tests with sample images (JPEG, PNG, WEBP)
- [ ] Specs accuracy 100% (PIL can read all supported formats)

**File Paths**:
- `backend/src/services/media/image_processor.py`
- `backend/tests/unit/services/media/test_image_processor.py`
- `backend/tests/fixtures/sample_images/` (JPEG, PNG, WEBP samples)

---

#### T7.10 [US7][P0] Implement Meta/SEO Extraction

**Description**: Implement `_extract_meta_seo()` method using Claude to detect Meta/SEO blocks ("Meta Description：", "關鍵詞：", "Tags："), extract into `meta_description`, `seo_keywords[]`, `tags[]`, strip from DOM.

**Dependencies**: T7.5

**Estimated Hours**: 4 hours

**Deliverables**:
- `_extract_meta_seo()` method implementation
- Claude prompt template for Meta/SEO detection
- Array parsing logic (comma/newline separated)
- DOM stripping after extraction

**Acceptance Criteria**:
- [ ] Detects "Meta Description：..." → meta_description
- [ ] Detects "關鍵詞：A, B, C" → seo_keywords=["A", "B", "C"]
- [ ] Detects "Tags：X, Y" → tags=["X", "Y"]
- [ ] Supports both Chinese and English labels
- [ ] Strips detected blocks from DOM
- [ ] Handles missing meta blocks (returns None/empty arrays)
- [ ] Unit tests cover 6+ meta extraction scenarios

**File Paths**:
- `backend/src/services/parser/article_parser.py` (update)
- `backend/src/services/parser/prompts/meta_seo_extraction.txt`
- `backend/tests/unit/services/parser/test_meta_extraction.py`

---

#### T7.11 [US7][P0] Implement Body HTML Cleaning

**Description**: Implement `_clean_body_html()` method to remove extracted elements (header, author, images, meta), sanitize HTML with bleach whitelist, preserve semantic structure.

**Dependencies**: T7.6, T7.7, T7.8, T7.10

**Estimated Hours**: 4 hours

**Deliverables**:
- `_clean_body_html()` method implementation
- Bleach configuration (whitelist: H1, H2, p, ul, ol, strong, em, a)
- DOM manipulation to remove extracted nodes
- Sanitization with XSS prevention

**Acceptance Criteria**:
- [ ] Removes header nodes (title, author)
- [ ] Removes image blocks (replaced with placeholders)
- [ ] Removes Meta/SEO blocks
- [ ] Preserves semantic tags: H1, H2, p, ul, ol, strong, em, a
- [ ] Strips dangerous HTML (script, onclick, etc.)
- [ ] Preserves clean structure (no orphaned tags)
- [ ] Unit tests with complex HTML samples
- [ ] XSS prevention verified

**File Paths**:
- `backend/src/services/parser/article_parser.py` (update)
- `backend/tests/unit/services/parser/test_html_cleaning.py`
- `backend/tests/fixtures/sample_html.html`

---

#### T7.12 [US7][P] Unit Tests for Parsing Service

**Description**: Comprehensive unit test suite for `ArticleParserService` covering all parsing methods, edge cases, error handling, and AI mocking.

**Dependencies**: T7.5, T7.6, T7.7, T7.8, T7.9, T7.10, T7.11

**Estimated Hours**: 8 hours (included in above tasks, consolidated here)

**Deliverables**:
- Complete test suite: `backend/tests/unit/services/parser/`
- Mocked Claude responses (fixtures)
- Edge case tests (missing fields, malformed HTML, download failures)
- Test coverage report

**Acceptance Criteria**:
- [ ] Test coverage ≥85% for `article_parser.py`
- [ ] Test coverage ≥90% for `image_processor.py`
- [ ] All edge cases covered (missing author, no images, malformed titles, corrupt images)
- [ ] Mocked Claude responses with varied structures
- [ ] Tests run in <30 seconds
- [ ] All tests passing

**File Paths**:
- `backend/tests/unit/services/parser/test_article_parser.py`
- `backend/tests/unit/services/parser/test_header_parsing.py`
- `backend/tests/unit/services/parser/test_author_extraction.py`
- `backend/tests/unit/services/parser/test_image_extraction.py`
- `backend/tests/unit/services/media/test_image_processor.py`
- `backend/tests/unit/services/parser/test_meta_extraction.py`
- `backend/tests/unit/services/parser/test_html_cleaning.py`
- `backend/tests/fixtures/`

---

### Week 19: API & Integration (12 hours)

#### T7.13 [US7][P0] Extend Worklist API Response

**Description**: Update `GET /v1/worklist/:id` endpoint to return structured parsing fields (`title_prefix`, `title_main`, `title_suffix`, `author_line`, `author_name`, `body_html`, `meta_description`, `seo_keywords`, `tags`) plus `images[]` array with metadata, plus confirmation state.

**Dependencies**: T7.3

**Estimated Hours**: 4 hours

**Deliverables**:
- Updated Pydantic response model: `WorklistItemDetailResponse`
- Extended API route: `backend/src/api/routes/worklist.py`
- JSON schema for `images[]` array
- API integration tests

**Acceptance Criteria**:
- [ ] Response includes all parsing fields
- [ ] `images[]` array includes: id, preview_path, source_path, source_url, caption, position, metadata
- [ ] `metadata` JSONB includes: width, height, aspect_ratio, file_size_bytes, mime_type, format, exif_date
- [ ] Response includes: parsing_confirmed, parsing_confirmed_at, parsing_confirmed_by
- [ ] Pydantic validation passes
- [ ] API returns 200 with complete data
- [ ] Integration test verifies response schema

**File Paths**:
- `backend/src/api/routes/worklist.py` (update)
- `backend/src/api/schemas/worklist.py` (update)
- `backend/tests/integration/api/test_worklist_detail.py`

---

#### T7.14 [US7][P0] Create Parsing Confirmation Endpoint

**Description**: Create `POST /v1/worklist/:id/confirm-parsing` endpoint to accept parsing confirmation payload (`parsing_confirmed`, `parsing_feedback`, `image_reviews[]`), save to database, update confirmation state.

**Dependencies**: T7.3, T7.13

**Estimated Hours**: 4 hours

**Deliverables**:
- New API route: `POST /v1/worklist/:id/confirm-parsing`
- Pydantic request model: `ParsingConfirmationRequest`
- Database update logic
- Image reviews creation logic
- API integration tests

**Acceptance Criteria**:
- [ ] Accepts: `parsing_confirmed` (bool), `parsing_feedback` (str), `image_reviews[]` (array)
- [ ] Updates `articles` table: `parsing_confirmed`, `parsing_confirmed_at`, `parsing_confirmed_by`
- [ ] Creates `article_image_reviews` records for each image review
- [ ] Returns: `worklist_item_id`, `parsing_confirmed_at` timestamp
- [ ] Validates image_reviews actions: keep, remove, replace_caption, replace_source
- [ ] Returns 200 on success, 400 on validation error
- [ ] Integration test verifies database updates

**File Paths**:
- `backend/src/api/routes/worklist.py` (update)
- `backend/src/api/schemas/worklist.py` (update)
- `backend/tests/integration/api/test_parsing_confirmation.py`

---

#### T7.15 [US7][P0] Integrate Parser into Google Drive Sync

**Description**: Modify `GoogleDriveSyncService` to call `ArticleParserService.parse_document()` after downloading Google Doc content. Create article with structured fields, create `article_images` records.

**Dependencies**: T7.5, T7.6, T7.7, T7.8, T7.9, T7.10, T7.11

**Estimated Hours**: 4 hours

**Deliverables**:
- Updated `GoogleDriveSyncService.process_new_document()` method
- Integration with `ArticleParserService`
- Bulk insert for `article_images`
- Error handling for parsing failures

**Acceptance Criteria**:
- [ ] Downloads Google Doc HTML
- [ ] Calls `ArticleParserService.parse_document(raw_html, article_id)`
- [ ] Creates article record with all structured fields
- [ ] Creates `article_images` records (bulk insert)
- [ ] Sets `current_status = 'pending'` (awaiting parsing confirmation)
- [ ] Handles parsing errors gracefully (logs error, sets article status to 'failed')
- [ ] Integration test: Google Doc → Parsed Article → Images created
- [ ] Parsing completes in ≤20 seconds for typical article

**File Paths**:
- `backend/src/services/google_drive/sync_service.py` (update)
- `backend/tests/integration/services/test_google_drive_parsing.py`

---

### Week 20-21: Frontend Step 1 UI (48 hours)

#### T7.16 [US7][P0] Create Step Indicator Component

**Description**: Build two-step wizard UI component with visual progress indicator (Step 1: 解析確認, Step 2: 正文校對). Support navigation between steps.

**Dependencies**: None (frontend)

**Estimated Hours**: 4 hours

**Deliverables**:
- `StepIndicator.tsx` component
- Step state management (current step, completed steps)
- Visual styling (progress bar, step numbers)
- Click navigation with validation

**Acceptance Criteria**:
- [ ] Displays two steps with labels in Chinese and English
- [ ] Highlights current step
- [ ] Shows completed steps with checkmark
- [ ] Clicking Step 2 blocked if Step 1 not confirmed
- [ ] Smooth transitions between steps
- [ ] Responsive design (mobile-friendly)
- [ ] Component tests with React Testing Library

**File Paths**:
- `frontend/src/components/Proofreading/StepIndicator.tsx`
- `frontend/src/components/Proofreading/StepIndicator.test.tsx`

---

#### T7.17 [US7][P0] Build Structured Headers Card

**Description**: Build card component displaying editable title fields (`title_prefix`, `title_main`, `title_suffix`) with character counters and validation.

**Dependencies**: None (frontend)

**Estimated Hours**: 6 hours

**Deliverables**:
- `StructuredHeadersCard.tsx` component
- Three input fields with labels
- Character counters (prefix: 200, main: 500, suffix: 200)
- Validation (title_main required, min 5 chars)
- Auto-save on blur

**Acceptance Criteria**:
- [ ] Displays three labeled fields (可選前標, 主標題*, 可選副標)
- [ ] Character counter updates in real-time
- [ ] Validation error shown if title_main < 5 chars
- [ ] Auto-save on blur (debounced 500ms)
- [ ] Displays save status (saving, saved, error)
- [ ] Component tests verify validation logic
- [ ] i18n support (zh-TW, en-US)

**File Paths**:
- `frontend/src/components/Proofreading/StructuredHeadersCard.tsx`
- `frontend/src/components/Proofreading/StructuredHeadersCard.test.tsx`

---

#### T7.18 [US7][P0] Build Author Info Card

**Description**: Build card component displaying `author_line` (raw, read-only) and editable `author_name` field.

**Dependencies**: None (frontend)

**Estimated Hours**: 4 hours

**Deliverables**:
- `AuthorInfoCard.tsx` component
- Read-only display of `author_line`
- Editable input for `author_name`
- Auto-save on blur

**Acceptance Criteria**:
- [ ] Displays author_line in read-only field (e.g., "文／張三")
- [ ] Displays editable author_name field (e.g., "張三")
- [ ] Auto-save on blur
- [ ] Displays save status
- [ ] Handles missing author gracefully (shows "未檢測到作者")
- [ ] Component tests
- [ ] i18n support

**File Paths**:
- `frontend/src/components/Proofreading/AuthorInfoCard.tsx`
- `frontend/src/components/Proofreading/AuthorInfoCard.test.tsx`

---

#### T7.19 [US7][P0] Build Image Gallery Card with Specs Table

**Description**: Build comprehensive image gallery component with grid of previews, captions, source links, technical specs table for each image, and per-image review actions.

**Dependencies**: T7.20 (ImageSpecsTable)

**Estimated Hours**: 12 hours

**Deliverables**:
- `ImageGalleryCard.tsx` component
- `ImagePreviewGrid.tsx` sub-component
- `ImagePreviewItem.tsx` sub-component (each image)
- Integration with `ImageSpecsTable.tsx`
- Image review action buttons (keep, remove, replace_caption, replace_source)

**Acceptance Criteria**:
- [ ] Grid layout (responsive, 2-3 columns on desktop, 1 on mobile)
- [ ] Each item shows: preview thumbnail, caption (editable), source link button, specs table
- [ ] Clicking source link opens image in new tab
- [ ] Specs table highlights out-of-range values (width <800 or >3000px, non-standard aspect ratio)
- [ ] Action buttons: Keep (default), Remove, Replace Caption, Replace Source
- [ ] Replace Caption: shows inline input
- [ ] Replace Source: shows inline URL input with validation
- [ ] Reviewer notes textarea for each action
- [ ] Auto-save actions on selection
- [ ] Component tests
- [ ] i18n support

**File Paths**:
- `frontend/src/components/Proofreading/ImageGalleryCard.tsx`
- `frontend/src/components/Proofreading/ImagePreviewGrid.tsx`
- `frontend/src/components/Proofreading/ImagePreviewItem.tsx`
- `frontend/src/components/Proofreading/ImageGalleryCard.test.tsx`

---

#### T7.20 [US7][P0] Build Image Specs Table Component

**Description**: Build table component displaying technical image specifications (width, height, aspect ratio, file size, MIME type, EXIF date) with visual warnings for out-of-tolerance values.

**Dependencies**: None (frontend)

**Estimated Hours**: 4 hours (included in T7.19)

**Deliverables**:
- `ImageSpecsTable.tsx` component
- Spec rows: Width, Height, Aspect Ratio, File Size, Format, EXIF Date
- Conditional styling for warnings
- Tooltip explanations for warnings

**Acceptance Criteria**:
- [ ] Displays all specs in table format
- [ ] Width: red warning if <800px or >3000px, otherwise green
- [ ] Aspect ratio: amber warning if non-standard (not 16:9, 4:3, 1:1)
- [ ] File size: formatted as human-readable (e.g., "2.4 MB")
- [ ] Format: displays MIME type (e.g., "image/jpeg")
- [ ] EXIF date: formatted as readable date (if available)
- [ ] Tooltips explain thresholds
- [ ] Component tests verify warning logic
- [ ] i18n support

**File Paths**:
- `frontend/src/components/Proofreading/ImageSpecsTable.tsx`
- `frontend/src/components/Proofreading/ImageSpecsTable.test.tsx`

---

#### T7.21 [US7][P0] Build Meta/SEO Card

**Description**: Build card component for editing `meta_description` (with character counter), `seo_keywords` (tag input), and `tags` (tag input).

**Dependencies**: None (frontend)

**Estimated Hours**: 6 hours

**Deliverables**:
- `MetaSEOCard.tsx` component
- Textarea for `meta_description` (160 char max recommended)
- Tag input for `seo_keywords` (add/remove tags)
- Tag input for `tags`
- Auto-save on changes

**Acceptance Criteria**:
- [ ] Meta description textarea with character counter
- [ ] Warning if >160 chars (not blocking, just advisory)
- [ ] SEO keywords: tag input, add with Enter/comma, remove with X button
- [ ] Tags: tag input, add with Enter/comma, remove with X button
- [ ] Auto-save on blur (debounced 500ms)
- [ ] Displays save status
- [ ] Component tests
- [ ] i18n support

**File Paths**:
- `frontend/src/components/Proofreading/MetaSEOCard.tsx`
- `frontend/src/components/Proofreading/MetaSEOCard.test.tsx`

---

#### T7.22 [US7][P0] Build Body HTML Preview Card

**Description**: Build card component for read-only preview of sanitized `body_html` with proper HTML rendering.

**Dependencies**: None (frontend)

**Estimated Hours**: 4 hours

**Deliverables**:
- `BodyHTMLPreviewCard.tsx` component
- Safe HTML rendering (DOMPurify or similar)
- Scrollable container for long content
- Styling for semantic HTML tags

**Acceptance Criteria**:
- [ ] Renders sanitized HTML safely (no XSS risk)
- [ ] Preserves semantic structure (H1, H2, p, ul, ol, strong, em, a)
- [ ] Scrollable if content exceeds viewport
- [ ] Read-only (no editing)
- [ ] Styled for readability
- [ ] Component tests verify safe rendering
- [ ] i18n support (labels)

**File Paths**:
- `frontend/src/components/Proofreading/BodyHTMLPreviewCard.tsx`
- `frontend/src/components/Proofreading/BodyHTMLPreviewCard.test.tsx`

---

#### T7.23 [US7][P0] Implement Confirmation Actions & State Management

**Description**: Create Zustand store for parsing confirmation state, implement "確認解析" button and "需要修正" toggle, handle save/unlock logic.

**Dependencies**: T7.13, T7.14

**Estimated Hours**: 6 hours

**Deliverables**:
- Zustand store: `useParsingConfirmationStore`
- Store actions: `updateTitleFields`, `updateAuthor`, `updateMetaSEO`, `addImageReview`, `confirmParsing`
- Confirmation button component
- "Needs fix" toggle component
- API integration for saving confirmation

**Acceptance Criteria**:
- [ ] Store holds all parsing state (title, author, meta, images, confirmation status)
- [ ] Actions update store immutably
- [ ] `confirmParsing()` calls `POST /v1/worklist/:id/confirm-parsing`
- [ ] Button disabled while saving
- [ ] Success: shows toast, unlocks Step 2, redirects to Step 2
- [ ] Error: shows error toast, keeps Step 1 active
- [ ] "Needs fix" toggle: if ON, blocks confirmation and Step 2 access
- [ ] Store tests with mock API
- [ ] i18n support

**File Paths**:
- `frontend/src/stores/useParsingConfirmationStore.ts`
- `frontend/src/components/Proofreading/ConfirmationActions.tsx`
- `frontend/src/stores/useParsingConfirmationStore.test.ts`

---

#### T7.24 [US7][P0] Add Step 2 Blocking Logic

**Description**: Implement logic to block Step 2 (正文校對) access until Step 1 parsing confirmation is complete. Show warning alert if user attempts to access Step 2 prematurely.

**Dependencies**: T7.16, T7.23

**Estimated Hours**: 4 hours

**Deliverables**:
- Blocking logic in Step navigation
- Warning alert component
- "Return to Step 1" button in alert
- State synchronization with API

**Acceptance Criteria**:
- [ ] Step 2 tab/button disabled if `parsing_confirmed === false`
- [ ] Clicking Step 2 shows warning alert: "請先完成解析確認"
- [ ] Alert includes "返回 Step 1" button
- [ ] After confirmation, Step 2 immediately unlocked
- [ ] Reviewer can return to Step 1 after confirming (editing allowed)
- [ ] State persists across page reloads (fetch from API)
- [ ] Component tests verify blocking logic
- [ ] i18n support

**File Paths**:
- `frontend/src/components/Proofreading/ProofreadingReviewPage.tsx` (update)
- `frontend/src/components/Proofreading/Step2BlockingAlert.tsx`
- `frontend/src/components/Proofreading/ProofreadingReviewPage.test.tsx`

---

#### T7.25 [US7][P0] i18n Support for Parsing UI

**Description**: Add internationalization support for all parsing UI strings (zh-TW primary, en-US secondary) in `proofreading.parsing.*` namespace.

**Dependencies**: All frontend tasks

**Estimated Hours**: 2 hours

**Deliverables**:
- Updated locale files: `frontend/src/locales/zh-TW.json`, `en-US.json`
- All UI strings using `t('proofreading.parsing.*')`
- Translation keys for: field labels, placeholders, validation messages, button text, warnings

**Acceptance Criteria**:
- [ ] All parsing UI strings externalized
- [ ] zh-TW translations complete and accurate
- [ ] en-US translations complete and accurate
- [ ] Language switch works without page reload
- [ ] No hardcoded strings in components
- [ ] i18n tests verify key existence

**File Paths**:
- `frontend/src/locales/zh-TW.json` (update)
- `frontend/src/locales/en-US.json` (update)
- `frontend/tests/i18n/test_parsing_translations.test.ts`

---

### Week 21: Integration & Testing (24 hours)

#### T7.26 [US7][P0] End-to-End Workflow Test

**Description**: Comprehensive E2E test using Playwright to verify full workflow: Google Doc import → Parsing → Step 1 Confirmation → Step 2 Access.

**Dependencies**: T7.15, T7.16-T7.25

**Estimated Hours**: 8 hours

**Deliverables**:
- E2E test spec: `frontend/e2e/parsing-confirmation-workflow.spec.ts`
- Test fixtures: sample Google Doc HTML
- Screenshot assertions
- Performance measurements

**Acceptance Criteria**:
- [ ] Test imports Google Doc
- [ ] Verifies parsing completes (all fields populated)
- [ ] Opens Proofreading Review page
- [ ] Verifies Step 1 UI displays all parsed fields
- [ ] Edits title, author, meta fields
- [ ] Confirms parsing
- [ ] Verifies Step 2 unlocked
- [ ] Accesses Step 2 successfully
- [ ] Returns to Step 1 (edit allowed)
- [ ] Test passes in <90 seconds
- [ ] Screenshots captured at key steps

**File Paths**:
- `frontend/e2e/parsing-confirmation-workflow.spec.ts`
- `frontend/e2e/fixtures/sample-google-doc.html`

---

#### T7.27 [US7][P0] Parsing Accuracy Validation

**Description**: Test parsing accuracy with 20 diverse Google Docs covering various title structures, author formats, image counts, and meta blocks. Measure accuracy for each field type.

**Dependencies**: T7.5-T7.11, T7.15

**Estimated Hours**: 8 hours

**Deliverables**:
- Test suite: `backend/tests/accuracy/test_parsing_accuracy.py`
- 20 test fixtures (Google Doc samples)
- Ground truth labels (expected parsing results)
- Accuracy report (CSV/JSON)

**Acceptance Criteria**:
- [ ] 20 diverse test documents prepared (1-3 line titles, 0-10 images, with/without meta)
- [ ] Ground truth labels manually verified
- [ ] Accuracy measured per field: title (≥90%), author (≥95%), images (≥90%), meta (≥85%)
- [ ] Overall accuracy ≥90%
- [ ] Failure cases documented with root cause analysis
- [ ] Accuracy report generated: `docs/parsing-accuracy-report.json`

**File Paths**:
- `backend/tests/accuracy/test_parsing_accuracy.py`
- `backend/tests/fixtures/accuracy/doc_001.html` (×20)
- `backend/tests/fixtures/accuracy/ground_truth.json`
- `docs/parsing-accuracy-report.json`

---

#### T7.28 [US7][P0] Performance Testing

**Description**: Measure parsing latency for typical articles (1500 words, 5 images). Verify parsing completes in ≤20 seconds.

**Dependencies**: T7.5-T7.11, T7.15

**Estimated Hours**: 4 hours

**Deliverables**:
- Performance test script: `backend/tests/performance/test_parsing_performance.py`
- Typical article fixtures (various sizes)
- Performance benchmark report

**Acceptance Criteria**:
- [ ] Tests parsing for 1500-word, 5-image article
- [ ] Parsing completes in ≤20 seconds (95th percentile)
- [ ] Tests parsing for 500-word, 1-image article (should be faster)
- [ ] Tests parsing for 3000-word, 10-image article (edge case)
- [ ] Identifies performance bottlenecks (profiling)
- [ ] Benchmark report: `docs/parsing-performance-benchmarks.md`

**File Paths**:
- `backend/tests/performance/test_parsing_performance.py`
- `backend/tests/fixtures/performance/typical_article.html`
- `docs/parsing-performance-benchmarks.md`

---

#### T7.29 [US7][P0] Bug Fixes & Edge Cases

**Description**: Handle edge cases and fix bugs discovered during testing: missing fields, malformed HTML, image download failures, corrupt images, etc.

**Dependencies**: T7.26, T7.27, T7.28

**Estimated Hours**: 4 hours

**Deliverables**:
- Bug fix commits
- Edge case handling code
- Regression tests for fixed bugs
- Bug fixes log

**Acceptance Criteria**:
- [ ] Handles missing author gracefully (author_line=null, author_name=null)
- [ ] Handles articles with 0 images (empty array)
- [ ] Handles malformed HTML (parsing doesn't crash, logs error)
- [ ] Handles image download failures (retries 3x, saves partial result, logs error)
- [ ] Handles corrupt images (PIL can't read → logs error, metadata=null)
- [ ] Handles missing meta blocks (returns None/empty arrays)
- [ ] All edge cases have regression tests
- [ ] Bug fixes log: `docs/parsing-bug-fixes-log.md`

**File Paths**:
- Various (backend/src/services/parser/, backend/src/services/media/)
- `backend/tests/edge_cases/`
- `docs/parsing-bug-fixes-log.md`

---

---

### Week 23: Proofreading Integration with Parsed Content (11 hours) 🆕

**Goal**: Ensure proofreading workflow correctly integrates with Phase 7 parsing results

#### T7.30 [US7][P0] Update Proofreading Payload Construction

**Description**: Modify `_build_article_payload()` in `src/api/routes/articles.py` to prioritize `body_html` over `body` and include parsing metadata.

**Dependencies**: T7.3 (SQLAlchemy models), T7.15 (Parser integration)

**Estimated Hours**: 2 hours

**Deliverables**:
- Updated `_build_article_payload()` function with priority logic:
  1. Use `article.body_html` if parsing confirmed
  2. Fallback to `article.body` for unparsed articles
  3. Add parsing metadata to payload
- Code documentation explaining the logic

**Acceptance Criteria**:
- [ ] Parsed articles use `body_html` for proofreading content
- [ ] Unparsed articles use `body` (backward compatibility)
- [ ] Parsing metadata included in payload JSON
- [ ] Warning emitted when using unparsed content

**File Paths**:
- `backend/src/api/routes/articles.py` (update `_build_article_payload()`)
- `backend/docs/phase7_proofreading_integration_analysis.md` (reference)

---

#### T7.31 [US7][P0] Add Parsing Prerequisite Check (Optional)

**Description**: Add optional check in proofreading endpoint to warn if article not yet parsed/confirmed.

**Dependencies**: T7.30

**Estimated Hours**: 1 hour

**Deliverables**:
- Warning flag in proofreading response if `parsing_confirmed = false`
- Configuration option to enforce prerequisite (default: warn only)
- API response includes `parsing_warning` field

**Acceptance Criteria**:
- [ ] Warning message: "建议先进行文章解析以获得更准确的校对结果"
- [ ] Configurable enforcement level (warn/block)
- [ ] User can proceed with warning (backward compatibility)

**File Paths**:
- `backend/src/api/routes/articles.py` (proofreading endpoint)
- `backend/src/config/settings.py` (add REQUIRE_PARSING_BEFORE_PROOFREADING config)

---

#### T7.32 [US7][P0] Update Proofreading Result Application Logic

**Description**: Ensure proofreading results update correct field (`body_html` for parsed, `body` for unparsed) without overwriting structured fields.

**Dependencies**: T7.30

**Estimated Hours**: 1.5 hours

**Deliverables**:
- Updated result application logic in proofreading service
- Preservation logic for structured fields (`title_*`, `author_*`, SEO fields)
- Documentation of field update strategy

**Acceptance Criteria**:
- [ ] Parsed articles: update `body_html` with corrected content
- [ ] Unparsed articles: update `body` (legacy behavior)
- [ ] Structured fields (`title_prefix`, `title_main`, `title_suffix`, `author_name`, `author_line`, `meta_description`, `seo_keywords`, `tags`) never overwritten
- [ ] Test coverage for both scenarios

**File Paths**:
- `backend/src/services/proofreading/service.py` (result application)
- `backend/src/api/routes/articles.py` (apply changes endpoint)

---

#### T7.33 [US7][P0] Unit Tests for Payload Construction

**Description**: Write comprehensive unit tests for updated `_build_article_payload()` logic.

**Dependencies**: T7.30, T7.31, T7.32

**Estimated Hours**: 2 hours

**Deliverables**:
- Test cases for:
  - Parsed article with confirmed parsing
  - Parsed article with unconfirmed parsing
  - Unparsed legacy article
  - Parsing metadata inclusion
  - Warning generation

**Acceptance Criteria**:
- [ ] All test cases pass
- [ ] Coverage ≥95% for modified functions
- [ ] Fixtures for both parsed and unparsed articles
- [ ] Assertions verify correct content source selection

**File Paths**:
- `backend/tests/unit/test_proofreading_payload.py` (new file)
- `backend/tests/fixtures/articles.py` (add parsed/unparsed fixtures)

---

#### T7.34 [US7][P0] Integration Tests for Proofreading Workflow

**Description**: End-to-end tests verifying proofreading workflow with parsed articles.

**Dependencies**: T7.30, T7.31, T7.32, T7.33

**Estimated Hours**: 2 hours

**Deliverables**:
- Integration test scenarios:
  1. Import → Parse → Confirm → Proofread → Apply → Verify
  2. Import → Proofread (unparsed) → Verify warning
  3. Verify structured fields preserved after proofreading
- Database fixtures with realistic data

**Acceptance Criteria**:
- [ ] Full workflow test passes with parsed article
- [ ] Backward compatibility test passes with unparsed article
- [ ] Structured field preservation verified
- [ ] Warning system tested

**File Paths**:
- `backend/tests/integration/test_parsing_proofreading_integration.py` (new file)
- `backend/tests/fixtures/workflows.py` (add workflow fixtures)

---

#### T7.35 [US7][P0] Update API Documentation

**Description**: Document the proofreading integration changes in API specs and developer docs.

**Dependencies**: T7.30, T7.31, T7.32

**Estimated Hours**: 1 hour

**Deliverables**:
- Updated OpenAPI/Swagger documentation
- Developer documentation explaining workflow
- Migration guide for existing users

**Acceptance Criteria**:
- [ ] API spec updated with new payload structure
- [ ] Parsing metadata schema documented
- [ ] Warning field documented
- [ ] Workflow diagram updated

**File Paths**:
- `specs/001-cms-automation/api-spec.yaml` (update proofreading endpoints)
- `backend/docs/api/proofreading.md` (update workflow docs)
- `backend/docs/phase7_proofreading_integration_analysis.md` (reference)

---

#### T7.36 [US7][P0] Update SpecKit Documentation

**Description**: Update spec.md, plan.md, and tasks.md with proofreading integration requirements and tasks.

**Dependencies**: T7.35

**Estimated Hours**: 1.5 hours

**Deliverables**:
- Updated `spec.md` with FR-106 to FR-110 requirements
- Updated `plan.md` with integration strategy
- Updated `tasks.md` with T7.30-T7.36 tasks
- Workflow diagrams showing integration points

**Acceptance Criteria**:
- [ ] All requirements (FR-106 to FR-110) documented in spec.md ✅
- [ ] Task breakdown (T7.30-T7.36) added to tasks.md ✅
- [ ] Implementation plan documented
- [ ] Review by stakeholders

**File Paths**:
- `specs/001-cms-automation/spec.md` ✅
- `specs/001-cms-automation/wordpress-publishing-plan.md`
- `specs/001-cms-automation/tasks.md` ✅

---

### Week 24-25: Unified AI Optimization Service (64 hours) 🆕

**Goal**: Implement unified AI service that generates title + SEO + FAQ suggestions in one API call, saving 40-60% cost and 30-40% time.

**Design Document**: `backend/docs/phase7_unified_ai_optimization_service.md`

---

#### T7.37 [US7][P0] Database Schema for Unified Optimization

**Description**: Create database tables for title suggestions, SEO suggestions, and FAQs. Add unified_optimization tracking fields to articles table.

**Dependencies**: T7.3 (Article parsing schema)

**Estimated Hours**: 4 hours

**Deliverables**:
- Alembic migration creating 3 tables:
  - `title_suggestions`: Store title optimization suggestions (3段式)
  - `seo_suggestions`: Store SEO keywords, meta description, tags
  - `article_faqs`: Store FAQ questions and answers
- Add fields to `articles` table:
  - `unified_optimization_generated`: BOOLEAN
  - `unified_optimization_generated_at`: TIMESTAMP
  - `unified_optimization_cost`: DECIMAL(10, 4)
- ORM models for all new tables
- Migration downgrade script

**Acceptance Criteria**:
- [ ] All tables created with proper foreign keys (article_id → articles.id)
- [ ] Indexes on article_id for fast lookup
- [ ] JSONB fields for flexible metadata storage
- [ ] Unique constraint: one title_suggestions/seo_suggestions per article
- [ ] Migration runs successfully on PostgreSQL
- [ ] Downgrade migration works correctly

**File Paths**:
- `backend/alembic/versions/*_add_unified_optimization_tables.py`
- `backend/src/models/title_suggestions.py` (new)
- `backend/src/models/seo_suggestions.py` (new)
- `backend/src/models/article_faq.py` (new)

**Database Schema**:
```sql
CREATE TABLE title_suggestions (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
    original_title_prefix VARCHAR(200),
    original_title_main VARCHAR(500) NOT NULL,
    original_title_suffix VARCHAR(200),
    suggested_title_sets JSONB NOT NULL,
    optimization_notes TEXT[],
    generated_at TIMESTAMP DEFAULT NOW(),
    generated_by VARCHAR(100) DEFAULT 'unified_optimization_service'
);

CREATE TABLE seo_suggestions (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
    focus_keyword VARCHAR(100),
    focus_keyword_rationale TEXT,
    primary_keywords TEXT[],
    secondary_keywords TEXT[],
    keyword_difficulty JSONB,
    search_volume_estimate JSONB,
    suggested_meta_description TEXT,
    meta_description_improvements TEXT[],
    meta_description_score INTEGER,
    suggested_tags JSONB,
    tag_strategy TEXT,
    generated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE article_faqs (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    question_type VARCHAR(20),
    search_intent VARCHAR(20),
    keywords_covered TEXT[],
    confidence DECIMAL(3, 2),
    position INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

#### T7.38 [US7][P0] UnifiedOptimizationService Implementation

**Description**: Implement core service that calls Claude API once to generate all optimization suggestions (title + SEO + FAQ).

**Dependencies**: T7.37

**Estimated Hours**: 8 hours

**Deliverables**:
- `backend/src/services/parsing/unified_optimization_service.py`:
  - `UnifiedOptimizationService` class
  - `generate_all_optimizations()` method
  - `_build_unified_prompt()` - comprehensive prompt with 5 tasks
  - `_parse_unified_response()` - JSON parsing
  - `_store_optimizations()` - save to 3 tables
  - `_build_full_title()` helper
- Prompt template covering:
  - Task 1: Title optimization (3段式, 2-3 options)
  - Task 2: SEO keywords (focus/primary/secondary)
  - Task 3: Meta description optimization
  - Task 4: Tags recommendations (6-8)
  - Task 5: FAQ generation (8-10 questions)
- Response validation and error handling
- Cost tracking and logging

**Acceptance Criteria**:
- [ ] Service successfully generates all 5 types of suggestions
- [ ] Prompt length ~2,500 tokens (within Claude limits)
- [ ] Response parsing handles JSON extraction from markdown code blocks
- [ ] Error handling for malformed responses
- [ ] All results saved to database atomically (transaction)
- [ ] Cost and token usage logged
- [ ] Service can be instantiated with AsyncAnthropic client

**File Paths**:
- `backend/src/services/parsing/unified_optimization_service.py` (new)

**Code Structure**:
```python
class UnifiedOptimizationService:
    def __init__(self, anthropic_client: AsyncAnthropic):
        self.client = anthropic_client
        self.model = "claude-sonnet-4.5-20250929"

    async def generate_all_optimizations(
        self, article: Article
    ) -> Dict[str, Any]:
        """Generate title + SEO + FAQ in one call"""
        prompt = self._build_unified_prompt(article)
        response = await self.client.messages.create(...)
        result = self._parse_unified_response(response.content[0].text)
        await self._store_optimizations(article.id, result)
        return result
```

---

#### T7.39 [US7][P0] API Endpoints for Unified Optimization

**Description**: Create API endpoints for generating and retrieving unified optimization suggestions.

**Dependencies**: T7.38

**Estimated Hours**: 4 hours

**Deliverables**:
- `POST /v1/articles/{id}/generate-all-optimizations`:
  - Trigger unified AI generation
  - Support regenerate flag
  - Return all suggestions in response
  - Track cost and performance
- `GET /v1/articles/{id}/optimizations`:
  - Retrieve cached optimization results
  - Return title/SEO/FAQ suggestions
  - Include generation metadata
- `DELETE /v1/articles/{id}/optimizations`:
  - Clear cached optimizations
  - Allow regeneration
- Request/response Pydantic models
- OpenAPI documentation

**Acceptance Criteria**:
- [ ] POST endpoint validates article exists and is parsed
- [ ] POST returns 409 if optimizations exist (unless regenerate=true)
- [ ] GET returns 404 if no optimizations generated
- [ ] Response includes generation_metadata with cost/time/savings
- [ ] All endpoints have proper error handling
- [ ] OpenAPI schema complete with examples

**File Paths**:
- `backend/src/api/routes/optimizations.py` (new)
- `backend/src/schemas/optimizations.py` (new)

**API Schemas**:
```python
class GenerateOptimizationsRequest(BaseModel):
    regenerate: bool = False
    options: OptimizationOptions = OptimizationOptions()

class OptimizationOptions(BaseModel):
    include_title: bool = True
    include_seo: bool = True
    include_tags: bool = True
    include_faqs: bool = True
    faq_target_count: int = 10

class OptimizationsResponse(BaseModel):
    success: bool
    generation_id: str
    title_suggestions: TitleSuggestionsData
    seo_suggestions: SEOSuggestionsData
    faqs: List[FAQData]
    generation_metadata: GenerationMetadata
```

---

#### T7.40 [US7][P0] Step 1 UI - Title Optimization Card

**Description**: Add title optimization UI component to ArticleParsingPage (Step 1), displaying AI-generated title suggestions.

**Dependencies**: T7.39, Frontend ArticleParsingPage exists

**Estimated Hours**: 8 hours

**Deliverables**:
- `frontend/src/components/parsing/TitleOptimizationCard.tsx`:
  - Display original 3-part title (prefix/main/suffix)
  - Show 2-3 AI optimization options
  - Display score, type, strengths for each option
  - Allow user to select option
  - Allow user to edit selected option
  - Allow user to keep original
  - Character count indicators
- Integration with ArticleParsingPage
- API client functions in `frontend/src/services/parsing.ts`:
  - `generateOptimizations(articleId)`
  - `getOptimizations(articleId)`
- TanStack Query hooks
- Loading/error states
- Responsive design

**Acceptance Criteria**:
- [ ] Card displays after parsing confirmation
- [ ] All 3 title components shown (prefix/main/suffix)
- [ ] AI options displayed with visual distinction (cards/tabs)
- [ ] Character count updates in real-time
- [ ] Validation: total length ≤ 70 characters
- [ ] User can select, edit, or reject suggestions
- [ ] Selection saved to article.title_* fields
- [ ] Loading state during AI generation (20-30s)
- [ ] Error handling with retry option

**File Paths**:
- `frontend/src/components/parsing/TitleOptimizationCard.tsx` (new)
- `frontend/src/pages/ArticleParsingPage.tsx` (updated)
- `frontend/src/services/parsing.ts` (updated)

**UI Design**:
```
┌─ Title Optimization ────────────────────────────────┐
│ Original Title:                                      │
│ [前缀] | 主标题 | [副标题]                            │
│                                                      │
│ AI Optimization Suggestions:                         │
│                                                      │
│ ┌─ Option 1 (Data-Driven) ────── Score: 95 ─┐      │
│ │ 前缀: 深度解析 (4)                          │      │
│ │ 主标题: 人工智能革新医疗诊断：准确率提升30% │      │
│ │ 副标题: 权威指南 (4)                        │      │
│ │ Total: 34 characters                        │      │
│ │                                             │      │
│ │ Strengths:                                  │      │
│ │ • Contains specific data (30%)              │      │
│ │ • Compelling action words                   │      │
│ │ [ Select ] [ Preview ]                      │      │
│ └─────────────────────────────────────────────┘      │
│                                                      │
│ ┌─ Option 2 (How-To) ────────── Score: 88 ──┐      │
│ │ ...                                         │      │
│ └─────────────────────────────────────────────┘      │
│                                                      │
│ [ Keep Original ] [ Use Selected ] [ Regenerate ]   │
└──────────────────────────────────────────────────────┘
```

---

#### T7.41 [US7][P0] Step 3 Page - SEO & FAQ Confirmation UI

**Description**: Create new Step 3 page for SEO metadata and FAQ confirmation, loading cached results from Step 1.

**Dependencies**: T7.39

**Estimated Hours**: 20 hours

**Deliverables**:
- `frontend/src/pages/ArticleSEOConfirmationPage.tsx` (new page):
  - Load cached optimizations from Step 1
  - Display SEO keywords (focus/primary/secondary)
  - Display meta description with improvements
  - Display tags recommendations
  - Display 8-10 FAQs with Q&A
  - Allow approve/reject/edit for each section
  - FAQ management: accept/reject/edit/delete individual items
- Components:
  - `frontend/src/components/seo/SEOKeywordsCard.tsx`
  - `frontend/src/components/seo/MetaDescriptionCard.tsx`
  - `frontend/src/components/seo/TagsCard.tsx`
  - `frontend/src/components/seo/FAQCard.tsx`
- Route configuration in `frontend/src/config/routes.ts`
- Navigation from Step 2 (Proofreading) to Step 3
- API integration for saving confirmed SEO data

**Acceptance Criteria**:
- [ ] Page loads cached optimizations (no AI call)
- [ ] All 4 sections (keywords/meta/tags/FAQ) displayed
- [ ] User can approve/reject each section independently
- [ ] FAQs displayed with question type and search intent badges
- [ ] FAQ reordering support (drag-and-drop)
- [ ] Character count for meta description (150-160)
- [ ] Warning if focus keyword not in meta description
- [ ] Confirmation saves to article.meta_description, article.seo_keywords, article.tags
- [ ] FAQs saved to article_faqs table with selected items
- [ ] Navigation to Step 4 (Publishing) after confirmation

**File Paths**:
- `frontend/src/pages/ArticleSEOConfirmationPage.tsx` (new)
- `frontend/src/components/seo/*.tsx` (new components)
- `frontend/src/config/routes.ts` (updated)

**UI Flow**:
```
Step 1: Parsing → Generate ALL optimizations (one AI call)
           ↓ Save to DB
           ↓ Display title suggestions only

Step 2: Proofreading (uses body_html)
           ↓

Step 3: SEO Confirmation → Load cached optimizations (no AI call)
           ↓ Display SEO + FAQ
           ↓ User confirms

Step 4: Publishing → WordPress
```

---

#### T7.42 [US7][P0] Workflow Integration - Call Unified Service in Step 1

**Description**: Integrate unified optimization service into existing parsing workflow, automatically generating all suggestions after parsing confirmation.

**Dependencies**: T7.38, T7.40, Existing ArticleParsingPage

**Estimated Hours**: 4 hours

**Deliverables**:
- Update `backend/src/api/routes/articles.py`:
  - After parsing confirmation, trigger unified optimization
  - Handle generation in background (async)
  - Update article.unified_optimization_generated flag
- Update `frontend/src/pages/ArticleParsingPage.tsx`:
  - After parsing confirmation, call generate-all-optimizations
  - Show loading state (20-30s)
  - Display title optimization card when ready
  - Handle errors gracefully
- Add configuration flag: `ENABLE_UNIFIED_OPTIMIZATION` (default true)
- Fallback to separate calls if unified service fails

**Acceptance Criteria**:
- [ ] Unified optimization triggered automatically after parsing
- [ ] Generation happens asynchronously (doesn't block confirmation)
- [ ] User sees progress indicator during generation
- [ ] Title suggestions appear after generation completes
- [ ] If unified service fails, fallback to old flow (separate calls)
- [ ] Generation failure doesn't break parsing workflow
- [ ] Cost and time metrics logged

**File Paths**:
- `backend/src/api/routes/articles.py` (updated)
- `frontend/src/pages/ArticleParsingPage.tsx` (updated)
- `backend/src/config/settings.py` (add ENABLE_UNIFIED_OPTIMIZATION)

---

#### T7.43 [US7][P0] Unit Tests for UnifiedOptimizationService

**Description**: Comprehensive unit tests for unified optimization service, covering prompt generation, response parsing, and storage.

**Dependencies**: T7.38

**Estimated Hours**: 4 hours

**Deliverables**:
- `backend/tests/services/parsing/test_unified_optimization_service.py`:
  - Test prompt generation with different article structures
  - Test response parsing (valid JSON)
  - Test response parsing (JSON in markdown code blocks)
  - Test malformed response handling
  - Test storage to 3 tables
  - Test transaction rollback on partial failure
  - Mock Anthropic API calls
- Test coverage ≥ 90%

**Acceptance Criteria**:
- [ ] All prompt generation edge cases covered
- [ ] Response parsing handles various formats
- [ ] Error cases properly tested
- [ ] Storage tested with different data structures
- [ ] All tests pass
- [ ] No database side effects between tests

**File Paths**:
- `backend/tests/services/parsing/test_unified_optimization_service.py` (new)

---

#### T7.44 [US7][P0] Integration Tests for Unified Optimization Workflow

**Description**: End-to-end integration tests for complete workflow: Import → Parse → Generate Optimizations → Confirm Title → Proofread → Confirm SEO → Publish.

**Dependencies**: T7.40, T7.41, T7.42

**Estimated Hours**: 6 hours

**Deliverables**:
- `backend/tests/integration/test_unified_optimization_workflow.py`:
  - Test full workflow with real database
  - Verify one AI call generates all suggestions
  - Verify title suggestions available in Step 1
  - Verify SEO suggestions available in Step 3
  - Verify cost savings vs separate calls
  - Test regeneration flow
  - Test fallback to separate calls
- Mock Claude API responses

**Acceptance Criteria**:
- [ ] Full workflow completes successfully
- [ ] Only one Anthropic API call made (unified)
- [ ] All 3 tables populated correctly
- [ ] Title confirmation updates article fields
- [ ] SEO confirmation updates article fields
- [ ] FAQs saved with correct article_id
- [ ] Cost metadata tracked correctly
- [ ] All tests pass with clean database state

**File Paths**:
- `backend/tests/integration/test_unified_optimization_workflow.py` (new)

---

#### T7.45 [US7][P0] Performance & Cost Monitoring

**Description**: Add monitoring and analytics for unified optimization service to verify cost/time savings.

**Dependencies**: T7.42

**Estimated Hours**: 3 hours

**Deliverables**:
- Metrics tracking:
  - Token usage per generation
  - Cost per generation (USD)
  - Generation time (ms)
  - Savings vs separate calls (%)
  - Success/failure rates
- Dashboard or logging:
  - Log to structured JSON
  - Include article_id, timestamp, metrics
  - Aggregate daily/weekly stats
- Alerts for anomalies (cost spike, high failure rate)

**Acceptance Criteria**:
- [ ] All generations logged with full metrics
- [ ] Cost savings calculated and logged
- [ ] Time savings calculated and logged
- [ ] Logs queryable for analysis
- [ ] Can generate weekly cost report
- [ ] Alerts configured (optional)

**File Paths**:
- `backend/src/services/parsing/unified_optimization_service.py` (add logging)
- `backend/src/utils/metrics.py` (new)

---

#### T7.46 [US7][P0] Update API Documentation

**Description**: Update OpenAPI spec and API documentation with new unified optimization endpoints.

**Dependencies**: T7.39

**Estimated Hours**: 2 hours

**Deliverables**:
- Update `specs/001-cms-automation/api-spec.yaml`:
  - Add `/v1/articles/{id}/generate-all-optimizations` endpoint
  - Add `/v1/articles/{id}/optimizations` endpoint
  - Add request/response schemas
  - Add examples
- Update `backend/docs/api/optimizations.md`:
  - Document unified optimization workflow
  - Provide usage examples
  - Document cost savings
  - Document error handling

**Acceptance Criteria**:
- [ ] OpenAPI spec validates
- [ ] All endpoints documented with examples
- [ ] Response schemas complete
- [ ] Error codes documented (400, 404, 409, 500)
- [ ] Workflow diagram included in docs

**File Paths**:
- `specs/001-cms-automation/api-spec.yaml` (updated)
- `backend/docs/api/optimizations.md` (new)

---

#### T7.47 [US7][P0] Frontend E2E Tests

**Description**: Playwright end-to-end tests for unified optimization UI workflow.

**Dependencies**: T7.40, T7.41

**Estimated Hours**: 4 hours

**Deliverables**:
- `frontend/e2e/unified-optimization.spec.ts`:
  - Test Step 1: Parsing → Title optimization display
  - Test title selection and confirmation
  - Test Step 3: SEO confirmation UI
  - Test FAQ approve/reject/edit
  - Test full workflow navigation
- Mock API responses for predictable testing
- Visual regression tests for UI cards

**Acceptance Criteria**:
- [ ] All user flows tested
- [ ] Tests pass in headless mode
- [ ] Screenshots captured for visual regression
- [ ] Tests run in CI pipeline
- [ ] Tests cover error states

**File Paths**:
- `frontend/e2e/unified-optimization.spec.ts` (new)

---

#### T7.48 [US7][P0] Update SpecKit Documentation

**Description**: Update spec.md and tasks.md with unified optimization requirements and implementation details.

**Dependencies**: T7.46

**Estimated Hours**: 3 hours

**Deliverables**:
- Update `specs/001-cms-automation/spec.md`:
  - Add FR-111 to FR-115 (Unified AI Optimization)
  - Document cost savings (40-60%)
  - Document workflow changes
- Update `specs/001-cms-automation/tasks.md`:
  - Add T7.37-T7.48 tasks ✅ (this task)
- Update Phase 7 summary:
  - Duration: 7 weeks → 9 weeks
  - Hours: 151h → 215h
- Update `specs/001-cms-automation/wordpress-publishing-plan.md`:
  - Document unified optimization architecture

**Acceptance Criteria**:
- [ ] All new requirements documented
- [ ] All tasks added to tasks.md ✅
- [ ] Phase 7 summary updated
- [ ] Architecture diagrams included
- [ ] Cost comparison documented

**File Paths**:
- `specs/001-cms-automation/spec.md` (updated)
- `specs/001-cms-automation/tasks.md` (updated) ✅
- `specs/001-cms-automation/wordpress-publishing-plan.md` (updated)

---

**Week 24-25 Summary**:
- **Duration**: 2 weeks
- **Estimated Hours**: 64 hours
- **Cost Savings**: 40-60% per article ($0.10-0.13 → $0.06-0.08)
- **Time Savings**: 30-40% per article (30-40s → 20-30s)
- **Key Deliverables**:
  - ✅ Unified AI Optimization Service (one Prompt for all)
  - ✅ Database schema (3 tables)
  - ✅ API endpoints (generate + retrieve)
  - ✅ Step 1 UI (title optimization)
  - ✅ Step 3 UI (SEO + FAQ confirmation)
  - ✅ Comprehensive tests (unit + integration + E2E)
  - ✅ Performance monitoring
  - ✅ Complete documentation

---

**Phase 7 Checkpoint**: ✅ Article parsing operational, Step 1 UI complete with title optimization, proofreading integration complete, Step 3 SEO+FAQ confirmation ready, unified AI optimization saving 40-60% cost, parsing accuracy ≥90%, performance ≤30s total, tests passing, ready for production

---

## Phase 8: Proofreading Feedback & Tuning Loop (2 weeks) ⭐新增

**Goal**: Capture用户决策、收集反馈、沉淀反馈数据用于脚本/Prompt 调优、支撑模型/脚本持续迭代  
**Duration**: 2 weeks (Week 16-17)  
**Estimated Hours**: 58 hours  
**Status**: Not Started

---

### Week 16: 数据模型与后端服务

#### T7.1 [US2][P0] Proofreading 决策与反馈调优批次迁移

**Description**: 创建 `proofreading_decisions`、`feedback_tuning_jobs`（可选）表，扩展 `proofreading_history` 统计字段与索引。

**Dependencies**: T2A.5 ProofreadingAnalysisService

**Estimated Hours**: 10 hours

**Deliverables**:
- Alembic migration + downgrade
- ORM/Pydantic 模型更新
- 文档：`database_schema_updates.md`

**Acceptance Criteria**:
- [ ] 新表/字段在 dev/staging 通过迁移
- [ ] `feedback_status` 枚举值齐全（pending/in_progress/completed/failed）
- [ ] 待处理反馈数量通过 `pending_feedback_count` 正确统计

**File Paths**:
- backend/alembic/versions/*
- backend/src/services/proofreading/models.py
- backend/docs/database_schema_updates.md

#### T7.2 [US2][P0] 决策写入服务与事件发布

**Description**: 实现 `record_user_decisions`，批量写入用户决策、更新 history 统计、推送反馈调优事件。

**Dependencies**: T7.1

**Estimated Hours**: 12 hours

**Deliverables**:
- Service/Repository 方法
- Celery/Kafka 事件（`proofreading.decision.recorded`）
- 单元测试覆盖成功/失败场景

**Acceptance Criteria**:
- [ ] 同一 history 的多条决策在事务内提交
- [ ] 更新 accepted/rejected/modified/pending_feedback 计数
- [ ] 事件包含 suggestion_type、rule_id、feedback 等关键字段

**File Paths**:
- backend/src/services/proofreading/service.py
- backend/src/services/proofreading/events.py
- backend/tests/services/test_proofreading_decisions.py

#### T7.3 [US2][P0] 决策 API + 权限

**Description**: 提供 `POST /proofreading/decisions`、`GET /proofreading/decisions`、`PATCH /proofreading/decisions/{id}/feedback-status`。

**Dependencies**: T7.2

**Estimated Hours**: 10 hours

**Deliverables**:
- FastAPI 路由
- OpenAPI 文档
- 集成测试

**Acceptance Criteria**:
- [ ] 批量提交校验 suggestion_id/hints
- [ ] 查询支持分页、按 decision/feedback_status 过滤
- [ ] 仅运营角色可修改 feedback_status，并写入审计日志

**File Paths**:
- backend/src/api/routes/proofreading_decisions.py
- specs/001-cms-automation/api-spec.yaml
- backend/tests/api/test_proofreading_decisions.py

### Week 17: 前端交互与反馈调优流水

#### T7.4 [US4][P0] 决策交互与反馈 UI

**Description**: 在 Proofreading/SEO/TAG 建议卡添加接受/拒绝/部分采纳操作与反馈弹窗，提交批量决策。

**Dependencies**: T7.3

**Estimated Hours**: 16 hours

**Deliverables**:
- UI 组件（按钮、反馈面板、diff 预览）
- Hook：`useProofreadingDecisions`
- 前端单元/端到端测试

**Acceptance Criteria**:
- [ ] 拒绝/部分采纳可选择预设反馈 + 自定义说明
- [ ] 反馈可选，不强制
- [ ] 决策状态在 UI 中明确展示，可撤销（提交前）

**File Paths**:
- frontend/src/components/ProofreadingSuggestionCard/*
- frontend/src/hooks/useProofreadingDecisions.ts
- frontend/tests/proofreading-decisions/*.test.tsx

#### T7.5 [US2][P0] 反馈调优导出 Worker

**Description**: 开发后台 worker 拉取 `pending` 决策 → 标记 `in_progress` → 导出调优素材（S3/数据湖）→ 更新状态。

**Dependencies**: T7.2

**Estimated Hours**: 12 hours

**Deliverables**:
- Celery 任务 / 后台服务
- S3/存储写入逻辑
- 错误处理与重试策略

**Acceptance Criteria**:
- [ ] 避免并发重复消费（行锁或 skip locked）
- [ ] 成功后写入 tuning_batch_id、prompt_or_rule_version、feedback_processed_at
- [ ] 失败时记录错误并可重置为 pending

**File Paths**:
- backend/src/workers/feedback_export.py
- backend/tests/workers/test_feedback_export.py
- monitoring/feedback_export_dashboard.md

#### T7.6 [US4][P1] 调优监控与仪表盘

**Description**: 构建 pending/completed/failed 决策统计面板，支持按 Prompt/规则版本过滤。

**Dependencies**: T7.5

**Estimated Hours**: 8 hours

**Deliverables**:
- Grafana/Metabase dashboard
- 查询 API 或 SQL 视图
- 文档更新

**Acceptance Criteria**:
- [ ] 仪表盘展示实时数量与趋势
- [ ] 支持导出/筛选模型版本
- [ ] 文档包含使用指南与指标解释

**File Paths**:
- monitoring/dashboards/proofreading_feedback_tuning.json
- monitoring/README.md
- backend/docs/monitoring_guide.md

---

## Phase 8: Future Work & Post-MVP Enhancements (Planned)

**Goal**: Long-term improvements and feature expansions planned for future iterations
**Status**: 📋 Planning Phase
**Priority**: To be scheduled based on business needs

### 🔴 High Priority: Proofreading Rules Realignment

**Background**: Analysis completed on 2025-11-02 revealed misalignment between rule definitions and implementation.

**Problem Statement**:
- `catalog.json` declares 354 rules (business function level)
- `rule_specs.py` implements 91 rule objects with 186 detection points
- Counting standards are inconsistent (rule objects vs detection points vs business functions)
- Rule coverage is unclear (A1/A2/A3 not implemented, B/C/F categories missing)

**Objective**: Redesign rule system to achieve three-layer alignment:
```
Rule Requirements (Business) ← 400-450 rules from Style Guide
         ↕ aligned with
catalog.json (Management) ← Complete rule manifest with implementation status
         ↕ aligned with
rule_specs.py (Implementation) ← Deterministic rule code
```

#### T8.1 [P1] Rule Audit & Complete Catalog Rebuild

**Description**: Extract all rules from 《大纪元、新唐人总部写作风格指南》and rebuild catalog.json with complete 400-450 rule list.

**Dependencies**: None

**Estimated Hours**: 80 hours (2-3 weeks)

**Deliverables**:
- `STYLE_GUIDE_RULES_COMPLETE.md` - Complete extraction of 400-450 rules
- Updated `catalog.json` with new fields:
  - `implementation_status`: implemented|planned|not_started
  - `implemented_as`: Array of rule_specs IDs
  - `detection_count`: Number of detection points
  - `last_updated`: Timestamp
- Rule coverage tracking tool: `scripts/analyze_rule_coverage.py`

**Acceptance Criteria**:
- [ ] All 400-450 rules from style guide documented
- [ ] catalog.json contains complete rule list (not just examples)
- [ ] Each catalog rule tagged with implementation status
- [ ] Automated coverage report generation working

**File Paths**:
- backend/docs/STYLE_GUIDE_RULES_COMPLETE.md
- backend/src/services/proofreading/rules/catalog.json
- backend/scripts/analyze_rule_coverage.py
- backend/docs/RULE_COVERAGE_REPORT.json

#### T8.2 [P1] Rule Counting Standards Documentation

**Description**: Define and document unified rule counting standards to eliminate confusion.

**Dependencies**: T8.1

**Estimated Hours**: 16 hours (1 week)

**Deliverables**:
- `RULE_COUNTING_STANDARDS.md` document
- Updated code comments with clear terminology
- Updated all documentation to use consistent counting terms

**Acceptance Criteria**:
- [ ] Clear definitions of: Rule Object, Detection Point, Rule Function
- [ ] All documentation uses standardized terminology
- [ ] Examples demonstrating each counting method

**File Paths**:
- backend/docs/RULE_COUNTING_STANDARDS.md
- backend/src/services/proofreading/README.md

#### T8.3 [P1] Refactor rule_specs.py with Catalog Mapping

**Description**: Add `catalog_rule_id` field to all rule objects for explicit mapping to catalog.json.

**Dependencies**: T8.1, T8.2

**Estimated Hours**: 24 hours (1 week)

**Deliverables**:
- Updated rule_specs.py with catalog_rule_id fields
- Migration script for existing rules
- Updated tests

**Acceptance Criteria**:
- [ ] All rule objects have catalog_rule_id field
- [ ] Bidirectional mapping validated (rule_specs ↔ catalog)
- [ ] Tests verify mapping correctness

**File Paths**:
- backend/src/services/proofreading/rule_specs.py
- backend/scripts/migrate_rule_mappings.py
- backend/tests/services/proofreading/test_rule_mapping.py

#### T8.4 [P2] Implement Missing High-Priority Rules

**Description**: Implement B (Punctuation), C (Numbers), and remaining A-class rules.

**Dependencies**: T8.3

**Estimated Hours**: 160-240 hours (4-6 weeks)

**Target Coverage**:
- B-class (Punctuation): 30-40 rules out of 60
- C-class (Numbers): 15-20 rules out of 24
- A1 (Unified Characters): ~30 rules
- A2 (Confusing Characters): 15-20 rules
- A3 (Common Typos): 20-25 rules

**Expected Increase**:
- Rule Objects: +105-135 (from 91 to 196-226)
- Detection Points: +200-250 (from 186 to 386-436)
- Coverage: ~50-60% of planned rules

**Deliverables**:
- New rule implementations in rule_specs.py
- Unit tests for all new rules
- Updated catalog.json with implementation status
- Performance benchmarks

**Acceptance Criteria**:
- [ ] All listed rule categories implemented
- [ ] Test coverage ≥ 90% for new rules
- [ ] Performance: <100ms for 5000-word article
- [ ] Coverage report shows 50-60% completion

**File Paths**:
- backend/src/services/proofreading/rule_specs.py
- backend/tests/services/proofreading/test_new_rules.py
- backend/docs/RULE_COVERAGE_REPORT.json

#### T8.5 [P3] Rule Management Backend & UI

**Description**: Build admin interface for rule management, coverage tracking, and testing.

**Dependencies**: T8.4

**Estimated Hours**: 120-160 hours (3-4 weeks)

**Deliverables**:
- Rule management REST API
- Admin UI (React)
  - Rule browser (filter by category, status)
  - Coverage dashboard
  - Rule testing tool (input text, see triggered rules)
  - Priority management
- Documentation

**Acceptance Criteria**:
- [ ] Full CRUD operations for rules via API
- [ ] Real-time coverage statistics displayed
- [ ] Rule testing tool functional
- [ ] User documentation complete

**File Paths**:
- backend/src/api/routes/rules_management.py
- frontend/src/pages/admin/RuleManagement.tsx
- backend/docs/RULE_MANAGEMENT_API.md

**Total Phase 8 (Proofreading Rules) Estimated Hours**: 400-520 hours (10-13 weeks)

### 🟡 Medium Priority: Other Future Enhancements

#### AI Engine Optimization
- Structured AI response with rule ID references
- Confidence scoring improvements
- Feedback loop for AI training

#### Performance Optimization
- Trie/AC automaton for multi-pattern matching (50-100x speedup)
- Concurrent article processing (3-5x throughput)

#### User Experience
- Visual diff with highlighting
- Rule explanation on click
- Custom rule configurations per user/team

#### Integrations
- WordPress plugin
- Google Docs add-on
- Browser extension

#### Multi-Language Support
- Simplified Chinese proofreading
- English grammar checking
- Mixed Chinese-English rules

**Note**: Detailed task breakdown for these will be created when scheduled.

---

**Reference Documentation**:
- Problem Analysis: `/docs/PROOFREADING_RULES_CORRECTED_ANALYSIS.md`
- Rule Fix Record: `/docs/PROOFREADING_RULES_FIX_2025-11-02.md`
- Implementation Status: `/docs/PROOFREADING_RULES_IMPLEMENTATION_ANALYSIS.md`
- Future Directions: `/docs/FUTURE_DIRECTIONS.md`

---

## Summary

**Total Tasks**: 89 tasks (48 core + 10 governance/deployment + 20 Google Drive automation + 6 feedback/调优闭环 + 5 future work)
**Total Duration**: 17.5 weeks (~87 business days) + 10-13 weeks future work
**Total Estimated Hours**: ~558 hours (current phases) + 400-520 hours (Phase 8 planned)

### By Phase:
- **Phase 0**: Governance (continuous)
- **Phase 1**: Database & Import (2 weeks, 10 tasks, 46 hours) ✅
- **Phase 2**: SEO Analysis (1.5 weeks, 9 tasks, 52 hours) ✅
- **Phase 3**: Computer Use (3 weeks, 14 tasks, 94 hours) ✅
- **Phase 4**: Frontend (2 weeks, 10 tasks, 80 hours) ⏳
- **Phase 5**: Testing & Deployment (2 weeks, 12 tasks, 72 hours) ⏳
- **Phase 6**: 🆕 Google Drive & Worklist (5 weeks, 20 tasks, 200 hours) ✅
- **Phase 7**: 🆕 Proofreading Feedback & Tuning Loop (2 weeks, 6 tasks, 58 hours)
- **Phase 8**: 🔮 Future Work (10-13 weeks, 5 tasks, 400-520 hours) 📋 Planned

### By User Story:
- **US1** (Article Import): T1.5-T1.10 (6 tasks)
- **US2** (SEO Analysis): T2.1-T2.9 (9 tasks)
- **US3** (Multi-Provider Publishing): T3.1-T3.14 (14 tasks)
- **US4** (Monitoring): T4.5-T4.7 (3 tasks)
- **US5** (Provider Comparison): T4.8 (1 task)
- **US6** 🆕 (Google Drive Automation): T6.1-T6.20 (20 tasks)
- **US7** 🆕 (Feedback & Tuning Loop): T7.1-T7.6 (6 tasks)

### Critical Path:
1. Database migration (T1.1-T1.4) → Blocks all data operations
2. Article import (T1.5-T1.10) → Blocks SEO testing
3. SEO analyzer (T2.1-T2.9) → Blocks publishing
4. Computer Use providers (T3.1-T3.14) → Blocks E2E tests
5. Integration tests (T5.1-T5.5) → Blocks production deployment
6. 🆕 Google Drive integration (T6.1-T6.7) → Blocks Worklist backend
7. 🆕 Worklist backend APIs (T6.14) → Blocks Worklist UI real-time updates
8. 🆕 Proofreading decisions (T7.1-T7.5) → Blocks 调优闭环与 Prompt/规则迭代
9. 🔮 **Phase 8 (Future)**: Rule audit (T8.1) → Blocks all Phase 8 work
10. 🔮 **Phase 8 (Future)**: Rule realignment (T8.1-T8.3) → Blocks rule expansion (T8.4)
11. 🔮 **Phase 8 (Future)**: Rule implementation (T8.4) → Blocks rule management UI (T8.5)

### Parallel Work Opportunities:
- Frontend (Phase 4) can start once Phase 3 APIs are defined
- Playwright provider (T3.5) can develop in parallel with Anthropic provider (T3.2)
- Performance testing (T5.6) can start during Phase 4
- 🆕 Google Drive backend (T6.1-T6.7) can develop in parallel with Worklist UI skeleton (T6.8-T6.10)
- 🆕 Worklist frontend (T6.8-T6.13) can start once backend APIs are defined
- 🆕 Proofreading feedback export (T7.5) can run alongside Phase 7 frontend (T7.4)
- All [P] marked tasks have no blocking dependencies

### Phase 6 Highlights:
- **Automated Document Ingestion**: Google Drive monitoring every 5 minutes
- **Worklist UI**: Comprehensive dashboard with 7 status types
- **Real-time Updates**: WebSocket for instant status changes
- **Status Tracking**: Complete audit trail for all document transitions
- **Batch Operations**: Delete/retry/mark multiple documents at once
- **Proofreading Feedback Loop**: 用户反馈沉淀为调优素材，支撑规则与 Prompt 快速迭代

### Phase 8 (Future Work) Highlights:
- **Complete Rule Alignment**: Three-layer alignment of requirements, catalog, and implementation
- **Unified Counting Standards**: Clear distinction between rule objects, detection points, and business functions
- **Expanded Coverage**: Target 50-60% rule coverage (from current ~25%)
- **Rule Management UI**: Admin interface for rule browsing, testing, and priority management
- **Performance Optimization**: Trie/AC automaton for 50-100x speedup
- **See**: `/docs/FUTURE_DIRECTIONS.md` for complete roadmap

---

**End of Tasks Document - SEO Optimization, Multi-Provider Computer Use Publishing, Google Drive Automation & Future Enhancements**
