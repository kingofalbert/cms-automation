# Tasks: SEO Optimization & Multi-Provider Computer Use Publishing

**Version**: 2.0.0
**Last Updated**: 2025-10-26
**Architecture**: Article Import → SEO Analysis (Messages API) → Multi-Provider Computer Use Publishing
**Input**: Design documents from `/specs/001-cms-automation/`
**Prerequisites**: plan.md v2.0, spec.md v2.0, data-model.md, contracts/api-spec.yaml

---

## Overview

This document provides a detailed breakdown of **48+ implementation tasks** organized across **5 phases** over **10.5 weeks**. Each task includes:
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

## Phase 1: Database Refactor & Article Import (2 weeks)

**Goal**: Extend database schema and implement article import from external sources
**Duration**: 2 weeks (Week 1-2)
**Estimated Hours**: 46 hours
**Status**: Not Started

---

### Week 1: Database Schema Design & Migration

#### T1.1 [P] Design New Database Schema

**Description**: Create ER diagram and detailed schema design for 4 core tables: articles (extended), seo_metadata, publish_tasks, execution_logs

**Dependencies**: None

**Estimated Hours**: 8 hours

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

#### T1.2 [P] Create Alembic Migration Scripts

**Description**: Write Alembic migration to extend articles table and create 3 new tables (seo_metadata, publish_tasks, execution_logs)

**Dependencies**: T1.1

**Estimated Hours**: 6 hours

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

#### T1.3 [P] Update SQLAlchemy Models

**Description**: Create/update SQLAlchemy ORM models to match new database schema

**Dependencies**: T1.2

**Estimated Hours**: 8 hours

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

#### T1.4 Run Migration & Verify

**Description**: Execute migration on dev database and verify all tables, constraints, and indexes created correctly

**Dependencies**: T1.3

**Estimated Hours**: 2 hours

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

## Phase 2: SEO Analysis Engine (1.5 weeks)

**Goal**: Implement intelligent SEO metadata generation using Claude Messages API
**Duration**: 1.5 weeks (Week 3-4)
**Estimated Hours**: 52 hours
**Status**: Not Started

---

### Week 3: SEO Analyzer Implementation

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

## Phase 3: Multi-Provider Computer Use Framework (3 weeks)

**Goal**: Implement abstract provider pattern for Computer Use with 3 providers (Anthropic, Gemini, Playwright)
**Duration**: 3 weeks (Week 4-6)
**Estimated Hours**: 94 hours
**Status**: Not Started

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

## Phase 4: Frontend & API Integration (2 weeks → **6 weeks revised**)

**⚠️ CRITICAL UPDATE (2025-10-27): UI Implementation Gap Identified**

**Original Estimate**: 2 weeks, 80 hours
**Revised Estimate**: **6 weeks, 312 hours**
**Current Status**: 🔴 **0% Complete** - No UI implementation exists
**Impact**: End-to-end user workflow is completely blocked

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

## Phase 5: Testing, Optimization & Deployment (2 weeks)

**Goal**: Comprehensive testing, performance optimization, and production deployment
**Duration**: 2 weeks (Week 9-10)
**Estimated Hours**: 72 hours
**Status**: Not Started

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

## Summary

**Total Tasks**: 58 tasks (48 core + 10 governance/deployment)
**Total Duration**: 10.5 weeks (~52 business days)
**Total Estimated Hours**: ~300 hours

### By Phase:
- **Phase 0**: Governance (continuous)
- **Phase 1**: Database & Import (2 weeks, 10 tasks, 46 hours)
- **Phase 2**: SEO Analysis (1.5 weeks, 9 tasks, 52 hours)
- **Phase 3**: Computer Use (3 weeks, 14 tasks, 94 hours)
- **Phase 4**: Frontend (2 weeks, 10 tasks, 80 hours)
- **Phase 5**: Testing & Deployment (2 weeks, 12 tasks, 72 hours)

### By User Story:
- **US1** (Article Import): T1.5-T1.10 (6 tasks)
- **US2** (SEO Analysis): T2.1-T2.9 (9 tasks)
- **US3** (Multi-Provider Publishing): T3.1-T3.14 (14 tasks)
- **US4** (Monitoring): T4.5-T4.7 (3 tasks)
- **US5** (Provider Comparison): T4.8 (1 task)

### Critical Path:
1. Database migration (T1.1-T1.4) → Blocks all data operations
2. Article import (T1.5-T1.10) → Blocks SEO testing
3. SEO analyzer (T2.1-T2.9) → Blocks publishing
4. Computer Use providers (T3.1-T3.14) → Blocks E2E tests
5. Integration tests (T5.1-T5.5) → Blocks production deployment

### Parallel Work Opportunities:
- Frontend (Phase 4) can start once Phase 3 APIs are defined
- Playwright provider (T3.5) can develop in parallel with Anthropic provider (T3.2)
- Performance testing (T5.6) can start during Phase 4
- All [P] marked tasks have no blocking dependencies

---

**End of Tasks Document - SEO Optimization & Multi-Provider Computer Use Publishing**
