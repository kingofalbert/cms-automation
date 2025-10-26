# Data Model: AI-Powered CMS Automation with SEO Optimization

**Feature**: 001-cms-automation
**Date**: 2025-10-25
**Last Updated**: 2025-10-25
**Database**: PostgreSQL 15+ with pgvector extension
**Architecture**: Fusion Model (Dual Source + Unified Processing)

## Overview

This document defines the database schema for the dual-source CMS automation platform. The model supports:

1. **AI Generation Path** (Preserved): Topic requests → Article generation
2. **Import Path** (New): External article imports
3. **Unified Processing** (New): SEO optimization + Computer Use publishing

All entities are derived from the feature specification's Key Entities section and support both content sources through a unified data model.

---

## Entity Relationship Diagram

```
                    ┌──────────────────┐
                    │  TopicRequest    │
                    │  (AI Generation) │
                    │                  │
                    │ - id             │
                    │ - topic          │
                    │ - outline        │
                    │ - style_tone     │
                    │ - word_count     │
                    │ - submitted_at   │
                    │ - article_id ────┼──┐
                    └──────────────────┘  │
                                          │ 1:1
                                          ↓
                    ┌─────────────────────────────┐       ┌──────────────────┐
                    │       Article               │       │   SEOMetadata    │
                    │  (Unified Content Store)    │       │  (New - Unified  │
                    │                             │       │   SEO Analysis)  │
                    │ - id                        │──1:1──│                  │
                    │ - title                     │       │ - id             │
                    │ - body                      │       │ - article_id (FK)│
                    │ - source ★NEW★              │       │ - seo_title      │
                    │   ('ai_generated','imported')│      │ - meta_desc      │
                    │ - seo_optimized ★NEW★       │       │ - focus_keyword  │
                    │ - status                    │       │ - keywords[]     │
                    │ - author_id                 │       │ - keyword_density│
                    │ - cms_article_id            │       │ - recommendations│
                    │ - published_at              │       │ - manual_overrides│
                    │ - metadata (images, etc)    │       │ - generated_at   │
                    └─────────────────────────────┘       └──────────────────┘
                              │
                              │ M:N
                              ↓
                    ┌─────────────────┐
                    │      Tag        │
                    │                 │
                    │ - id            │
                    │ - name          │
                    │ - category      │
                    │ - usage_count   │
                    │ - source        │
                    └─────────────────┘

                              │
                              │ 1:N
                              ↓
                    ┌─────────────────────────┐       ┌──────────────────┐
                    │    PublishTask          │──1:N──│  ExecutionLog    │
                    │  (New - Computer Use)   │       │  (New - Detailed │
                    │                         │       │   Action Log)    │
                    │ - id                    │       │                  │
                    │ - article_id (FK)       │       │ - id             │
                    │ - cms_type              │       │ - task_id (FK)   │
                    │ - status                │       │ - action         │
                    │ - screenshots (JSONB)   │       │ - target_element │
                    │ - retry_count           │       │ - payload        │
                    │ - error_message         │       │ - result         │
                    │ - started_at            │       │ - timestamp      │
                    │ - completed_at          │       └──────────────────┘
                    │ - duration_seconds      │
                    └─────────────────────────┘

                    ┌─────────────────────────┐
                    │   TopicEmbedding        │
                    │   (Semantic Similarity) │
                    │                         │
                    │ - id                    │
                    │ - article_id            │
                    │ - topic_text            │
                    │ - embedding (vector)    │
                    │ - created_at            │
                    └─────────────────────────┘

                    ┌─────────────────────────┐
                    │     AuditLog            │
                    │   (Compliance Trail)    │
                    │                         │
                    │ - id                    │
                    │ - entity_type           │
                    │ - entity_id             │
                    │ - action                │
                    │ - user_id               │
                    │ - changes               │
                    │ - timestamp             │
                    └─────────────────────────┘

                    ┌─────────────────────────┐
                    │     Schedule            │
                    │   (Time-based Publish)  │
                    │                         │
                    │ - id                    │
                    │ - article_id (FK)       │
                    │ - scheduled_time        │
                    │ - status                │
                    │ - retry_config          │
                    └─────────────────────────┘

                    ┌─────────────────────────┐
                    │   WorkflowState         │
                    │   (Review Process)      │
                    │                         │
                    │ - id                    │
                    │ - article_id (FK)       │
                    │ - current_status        │
                    │ - reviewers             │
                    │ - approval_history      │
                    └─────────────────────────┘
```

---

## Core Entities

### 1. Article (EXTENDED)

Represents a content piece from either AI generation or external import, ready for unified SEO and publishing.

**Table**: `articles`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique article identifier |
| title | VARCHAR(500) | NOT NULL | Article headline |
| body | TEXT | NOT NULL | Full article content (Markdown or HTML) |
| **source** ★NEW★ | VARCHAR(20) | NOT NULL, DEFAULT 'ai_generated' | Content source (see enum below) |
| **seo_optimized** ★NEW★ | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether SEO analysis has been performed |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'draft' | Workflow status (see enum below) |
| author_id | INTEGER | NOT NULL | User who created/imported the article |
| cms_article_id | VARCHAR(255) | NULLABLE, UNIQUE | CMS platform's article ID (WordPress post ID) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Article creation timestamp |
| published_at | TIMESTAMP | NULLABLE | Actual publication timestamp |
| metadata | JSONB | NOT NULL, DEFAULT '{}' | CMS-specific metadata (images, featured image, excerpt, etc.) |
| formatting | JSONB | NOT NULL, DEFAULT '{}' | Formatting preferences (headings, lists, code blocks) |

**Source Enum** ★NEW★: `ai_generated`, `imported`

**Status Enum** (UPDATED): `draft`, `seo_optimizing`, `seo_complete`, `publishing`, `published`, `failed`

**Indexes**:
```sql
CREATE INDEX idx_articles_status ON articles(status);
CREATE INDEX idx_articles_author ON articles(author_id);
CREATE INDEX idx_articles_published ON articles(published_at) WHERE published_at IS NOT NULL;
CREATE INDEX idx_articles_metadata ON articles USING GIN(metadata);
CREATE INDEX idx_articles_source ON articles(source);  -- NEW
CREATE INDEX idx_articles_seo_optimized ON articles(seo_optimized) WHERE seo_optimized = FALSE;  -- NEW
```

**Validation Rules**:
- Title length: 10-500 characters
- Body length: minimum 100 words
- Source must be 'ai_generated' or 'imported'
- Status transitions: `draft → seo_optimizing → seo_complete → publishing → published` (or → failed at any step)

**State Transitions** (UPDATED):
```
draft ──────────→ seo_optimizing ──────→ seo_complete ──────→ publishing ──────→ published
  ↓                      ↓                      ↓                  ↓
  └──────────────────────┴──────────────────────┴──────────────> failed
                                                                   ↓
                                                             (rollback)
                                                                   ↓
                                                                 draft
```

**metadata JSONB Schema** (UPDATED):
```json
{
  "images": [
    {"url": "https://cdn.example.com/image1.jpg", "alt": "Image description", "position": 0},
    {"url": "https://cdn.example.com/image2.jpg", "alt": "Another image", "position": 1}
  ],
  "featured_image": "https://cdn.example.com/featured.jpg",
  "excerpt": "Brief article summary...",
  "import_source": "outsourced_writer_batch_2025_10",  // For imported articles
  "original_url": "https://external-site.com/original"  // For imported articles
}
```

---

### 2. SEOMetadata (NEW)

Stores SEO analysis results for all articles regardless of source.

**Table**: `seo_metadata`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique SEO metadata identifier |
| article_id | INTEGER | NOT NULL, UNIQUE | Article reference |
| seo_title | VARCHAR(60) | NOT NULL | Optimized SEO title (50-60 chars) |
| meta_description | VARCHAR(160) | NOT NULL | Meta description (150-160 chars) |
| focus_keyword | VARCHAR(100) | NOT NULL | Primary target keyword |
| primary_keywords | TEXT[] | NOT NULL, DEFAULT '{}' | 3-5 main keywords |
| secondary_keywords | TEXT[] | NOT NULL, DEFAULT '{}' | 5-10 supporting keywords |
| keyword_density | JSONB | NOT NULL, DEFAULT '{}' | Keyword frequency analysis |
| optimization_recommendations | TEXT[] | NOT NULL, DEFAULT '{}' | Actionable SEO suggestions |
| manual_overrides | JSONB | DEFAULT '{}' | User edits with timestamps |
| readability_score | DECIMAL(4,2) | NULLABLE | Flesch-Kincaid grade level |
| generated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Initial analysis timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last modification timestamp |

**Indexes**:
```sql
CREATE INDEX idx_seo_metadata_article ON seo_metadata(article_id);
CREATE INDEX idx_seo_metadata_focus_keyword ON seo_metadata(focus_keyword);
CREATE INDEX idx_seo_metadata_generated ON seo_metadata(generated_at DESC);
```

**Foreign Keys**:
```sql
ALTER TABLE seo_metadata
ADD CONSTRAINT fk_seo_metadata_article
FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE;
```

**Constraints**:
```sql
ALTER TABLE seo_metadata ADD CONSTRAINT check_seo_title_length
CHECK (char_length(seo_title) BETWEEN 50 AND 60);

ALTER TABLE seo_metadata ADD CONSTRAINT check_meta_description_length
CHECK (char_length(meta_description) BETWEEN 150 AND 160);

ALTER TABLE seo_metadata ADD CONSTRAINT check_primary_keywords_count
CHECK (array_length(primary_keywords, 1) BETWEEN 3 AND 5);

ALTER TABLE seo_metadata ADD CONSTRAINT check_secondary_keywords_count
CHECK (array_length(secondary_keywords, 1) BETWEEN 5 AND 10);
```

**keyword_density JSONB Schema**:
```json
{
  "OEM": {"count": 15, "density": 2.1},
  "supply chain": {"count": 12, "density": 1.7},
  "manufacturing": {"count": 10, "density": 1.4}
}
```

**manual_overrides JSONB Schema**:
```json
[
  {
    "field": "seo_title",
    "original_value": "OEM Supply Chain Trends in North America 2025",
    "new_value": "North America OEM Supply Chain Trends | 2025 Guide",
    "editor_id": 42,
    "edited_at": "2025-10-25T14:30:00Z",
    "reason": "Brand keyword placement"
  }
]
```

---

### 3. PublishTask (NEW)

Represents a Computer Use publishing operation to WordPress.

**Table**: `publish_tasks`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique task identifier |
| article_id | INTEGER | NOT NULL | Article to publish |
| cms_type | VARCHAR(50) | NOT NULL, DEFAULT 'wordpress' | Target CMS platform |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | Task execution status |
| screenshots | JSONB | DEFAULT '[]' | Screenshot URLs with timestamps |
| retry_count | INTEGER | NOT NULL, DEFAULT 0 | Number of retry attempts |
| max_retries | INTEGER | NOT NULL, DEFAULT 3 | Maximum retry limit |
| error_message | TEXT | NULLABLE | Failure reason if applicable |
| started_at | TIMESTAMP | NULLABLE | Task start time |
| completed_at | TIMESTAMP | NULLABLE | Task completion time |
| duration_seconds | INTEGER | NULLABLE | Total execution time |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Task creation time |

**Status Enum**: `pending`, `in_progress`, `completed`, `failed`, `cancelled`

**Indexes**:
```sql
CREATE INDEX idx_publish_tasks_article ON publish_tasks(article_id);
CREATE INDEX idx_publish_tasks_status ON publish_tasks(status);
CREATE INDEX idx_publish_tasks_created ON publish_tasks(created_at DESC);
CREATE INDEX idx_publish_tasks_pending ON publish_tasks(status) WHERE status = 'pending';
```

**Foreign Keys**:
```sql
ALTER TABLE publish_tasks
ADD CONSTRAINT fk_publish_tasks_article
FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE;
```

**Constraints**:
```sql
ALTER TABLE publish_tasks ADD CONSTRAINT check_max_retries_positive
CHECK (max_retries > 0);

ALTER TABLE publish_tasks ADD CONSTRAINT check_retry_count_within_max
CHECK (retry_count <= max_retries);
```

**screenshots JSONB Schema**:
```json
[
  {
    "step": "login_success",
    "url": "s3://bucket/screenshots/task_123/01_login_success.png",
    "timestamp": "2025-10-25T14:25:30Z",
    "description": "WordPress login successful"
  },
  {
    "step": "editor_loaded",
    "url": "s3://bucket/screenshots/task_123/02_editor_loaded.png",
    "timestamp": "2025-10-25T14:25:45Z",
    "description": "Post editor interface loaded"
  },
  {
    "step": "content_filled",
    "url": "s3://bucket/screenshots/task_123/03_content_filled.png",
    "timestamp": "2025-10-25T14:26:10Z",
    "description": "Title and body content populated"
  },
  {
    "step": "seo_fields_filled",
    "url": "s3://bucket/screenshots/task_123/04_seo_fields.png",
    "timestamp": "2025-10-25T14:26:45Z",
    "description": "Yoast SEO fields configured"
  },
  {
    "step": "published_success",
    "url": "s3://bucket/screenshots/task_123/05_published.png",
    "timestamp": "2025-10-25T14:27:20Z",
    "description": "Article published successfully"
  }
]
```

---

### 4. ExecutionLog (NEW)

Detailed operation log for Computer Use actions during publishing.

**Table**: `execution_logs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Unique log entry identifier |
| publish_task_id | INTEGER | NOT NULL | Associated publish task |
| action | VARCHAR(50) | NOT NULL | Action type (click, type, screenshot, verify, etc.) |
| target_element | TEXT | NULLABLE | CSS selector or element description |
| payload | JSONB | DEFAULT '{}' | Action-specific data (text typed, coordinates, etc.) |
| result | VARCHAR(20) | NOT NULL | Execution result (success, failure, retry) |
| error_details | TEXT | NULLABLE | Error message if result is failure |
| timestamp | TIMESTAMP | NOT NULL, DEFAULT NOW() | Action execution time |

**Action Enum**: `navigate`, `click`, `type`, `upload`, `screenshot`, `verify`, `wait`, `scroll`

**Result Enum**: `success`, `failure`, `retry`

**Indexes**:
```sql
CREATE INDEX idx_execution_logs_task ON execution_logs(publish_task_id);
CREATE INDEX idx_execution_logs_timestamp ON execution_logs(timestamp DESC);
CREATE INDEX idx_execution_logs_action ON execution_logs(action);
CREATE INDEX idx_execution_logs_result ON execution_logs(result) WHERE result = 'failure';
```

**Foreign Keys**:
```sql
ALTER TABLE execution_logs
ADD CONSTRAINT fk_execution_logs_task
FOREIGN KEY (publish_task_id) REFERENCES publish_tasks(id) ON DELETE CASCADE;
```

**Partitioning** (for high-volume logging):
```sql
-- Partition by month for efficient archival
CREATE TABLE execution_logs_2025_10 PARTITION OF execution_logs
FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
```

**payload JSONB Examples**:

**Type action**:
```json
{
  "element": "#post-title-0",
  "text": "OEM Supply Chain Trends in North America",
  "duration_ms": 250
}
```

**Click action**:
```json
{
  "element": "#publish-button",
  "coordinates": {"x": 1234, "y": 567}
}
```

**Upload action**:
```json
{
  "element": "#featured-image-upload",
  "file_path": "/tmp/featured_image_123.jpg",
  "file_size_bytes": 245678
}
```

**Verify action**:
```json
{
  "check": "element_visible",
  "element": ".notice-success",
  "expected": true,
  "actual": true
}
```

---

### 5. TopicRequest (PRESERVED)

Represents a user's submission for AI article creation.

**Table**: `topic_requests`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique request identifier |
| topic_description | TEXT | NOT NULL | User-provided topic or outline |
| outline | TEXT | NULLABLE | Optional structured outline (JSON or Markdown) |
| style_tone | VARCHAR(50) | DEFAULT 'professional' | Requested writing style |
| target_word_count | INTEGER | DEFAULT 1000 | Desired article length |
| priority | VARCHAR(10) | DEFAULT 'normal' | Processing priority (urgent, normal, low) |
| submitted_by | INTEGER | NOT NULL | User ID who submitted request |
| submitted_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Submission timestamp |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | Request processing status |
| article_id | INTEGER | NULLABLE, UNIQUE | Foreign key to generated article |
| error_message | TEXT | NULLABLE | Error details if generation fails |

**Status Enum**: `pending`, `processing`, `completed`, `failed`, `cancelled`

**Indexes**:
```sql
CREATE INDEX idx_topic_requests_status ON topic_requests(status);
CREATE INDEX idx_topic_requests_submitted ON topic_requests(submitted_at);
CREATE INDEX idx_topic_requests_priority ON topic_requests(priority, submitted_at);
```

**Foreign Keys**:
```sql
ALTER TABLE topic_requests
ADD CONSTRAINT fk_topic_requests_article
FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE SET NULL;

ALTER TABLE topic_requests
ADD CONSTRAINT fk_topic_requests_user
FOREIGN KEY (submitted_by) REFERENCES users(id);
```

---

### 6. Tag (PRESERVED)

Represents a content classification keyword.

**Table**: `tags`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique tag identifier |
| name | VARCHAR(100) | NOT NULL, UNIQUE | Tag display name (case-insensitive) |
| slug | VARCHAR(120) | NOT NULL, UNIQUE | URL-friendly version |
| category | VARCHAR(50) | NULLABLE | Tag grouping (topic, industry, format, etc.) |
| usage_count | INTEGER | NOT NULL, DEFAULT 0 | Number of articles with this tag |
| source | VARCHAR(20) | NOT NULL, DEFAULT 'automated' | Creation method (automated, manual) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Tag creation timestamp |
| cms_tag_id | VARCHAR(255) | NULLABLE | CMS platform's tag ID |

**Indexes**:
```sql
CREATE INDEX idx_tags_name ON tags(LOWER(name));
CREATE INDEX idx_tags_category ON tags(category) WHERE category IS NOT NULL;
CREATE INDEX idx_tags_usage ON tags(usage_count DESC);
```

**Constraints**:
```sql
ALTER TABLE tags ADD CONSTRAINT check_tag_name_length
CHECK (char_length(name) BETWEEN 2 AND 100);

ALTER TABLE tags ADD CONSTRAINT check_tag_source
CHECK (source IN ('automated', 'manual'));
```

---

### 7. ArticleTag (PRESERVED)

Many-to-many relationship between articles and tags.

**Table**: `article_tags`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| article_id | INTEGER | NOT NULL | Article reference |
| tag_id | INTEGER | NOT NULL | Tag reference |
| confidence | DECIMAL(3,2) | DEFAULT 1.0 | Tagging confidence (0.0-1.0) for automated tags |
| assigned_by | VARCHAR(20) | NOT NULL | Source (ai, manual, hybrid) |
| assigned_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Assignment timestamp |

**Primary Key**:
```sql
ALTER TABLE article_tags
ADD CONSTRAINT pk_article_tags PRIMARY KEY (article_id, tag_id);
```

**Foreign Keys**:
```sql
ALTER TABLE article_tags
ADD CONSTRAINT fk_article_tags_article
FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE;

ALTER TABLE article_tags
ADD CONSTRAINT fk_article_tags_tag
FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE;
```

---

### 8. Schedule (PRESERVED)

Represents a publishing schedule for articles.

**Table**: `schedules`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique schedule identifier |
| article_id | INTEGER | NOT NULL, UNIQUE | Article to be published |
| scheduled_time | TIMESTAMP | NOT NULL | Target publication time (UTC) |
| creator_id | INTEGER | NOT NULL | User who created schedule |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | Execution status |
| retry_count | INTEGER | NOT NULL, DEFAULT 0 | Number of retry attempts |
| max_retries | INTEGER | NOT NULL, DEFAULT 3 | Maximum retry limit |
| retry_delay | INTEGER | NOT NULL, DEFAULT 300 | Delay between retries (seconds) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Schedule creation time |
| executed_at | TIMESTAMP | NULLABLE | Actual publication time |
| error_message | TEXT | NULLABLE | Failure reason if applicable |

**Status Enum**: `pending`, `published`, `failed`, `cancelled`

**Indexes**:
```sql
CREATE INDEX idx_schedules_time ON schedules(scheduled_time) WHERE status = 'pending';
CREATE INDEX idx_schedules_status ON schedules(status);
```

**Foreign Keys**:
```sql
ALTER TABLE schedules
ADD CONSTRAINT fk_schedules_article
FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE;

ALTER TABLE schedules
ADD CONSTRAINT fk_schedules_creator
FOREIGN KEY (creator_id) REFERENCES users(id);
```

---

### 9. WorkflowState (PRESERVED)

Represents the approval and review state for articles.

**Table**: `workflow_states`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique workflow state identifier |
| article_id | INTEGER | NOT NULL, UNIQUE | Article under review |
| current_status | VARCHAR(20) | NOT NULL | Current workflow stage |
| assigned_reviewers | INTEGER[] | DEFAULT '{}' | User IDs of assigned reviewers |
| approval_history | JSONB | DEFAULT '[]' | Array of approval/rejection events |
| modification_requests | JSONB | DEFAULT '[]' | Array of requested changes |
| version | INTEGER | NOT NULL, DEFAULT 1 | Article version number |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Initial workflow creation |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last workflow update |

**Current Status Enum**: `pending_review`, `approved`, `rejected`, `revision_requested`

**Indexes**:
```sql
CREATE INDEX idx_workflow_states_status ON workflow_states(current_status);
CREATE INDEX idx_workflow_states_reviewers ON workflow_states USING GIN(assigned_reviewers);
```

**Foreign Keys**:
```sql
ALTER TABLE workflow_states
ADD CONSTRAINT fk_workflow_states_article
FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE;
```

---

### 10. TopicEmbedding (PRESERVED)

Stores vector embeddings for semantic duplicate detection.

**Table**: `topic_embeddings`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique embedding identifier |
| article_id | INTEGER | NULLABLE | Associated article (null for pending requests) |
| topic_request_id | INTEGER | NULLABLE | Associated topic request |
| topic_text | TEXT | NOT NULL | Original topic description |
| embedding | vector(1536) | NOT NULL | Claude embedding vector |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Embedding generation time |

**Indexes**:
```sql
-- Vector similarity index (IVFFlat algorithm)
CREATE INDEX idx_topic_embeddings_vector
ON topic_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX idx_topic_embeddings_article ON topic_embeddings(article_id);
```

**Foreign Keys**:
```sql
ALTER TABLE topic_embeddings
ADD CONSTRAINT fk_topic_embeddings_article
FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE;

ALTER TABLE topic_embeddings
ADD CONSTRAINT fk_topic_embeddings_request
FOREIGN KEY (topic_request_id) REFERENCES topic_requests(id) ON DELETE CASCADE;
```

**Similarity Query**:
```sql
-- Find similar topics (cosine similarity > 0.85)
SELECT
    te.article_id,
    a.title,
    a.source,
    1 - (te.embedding <=> $1::vector) AS similarity
FROM topic_embeddings te
JOIN articles a ON te.article_id = a.id
WHERE 1 - (te.embedding <=> $1::vector) > 0.85
ORDER BY te.embedding <=> $1::vector
LIMIT 10;
```

---

### 11. AuditLog (PRESERVED)

Comprehensive audit trail for compliance.

**Table**: `audit_logs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Unique log entry identifier |
| entity_type | VARCHAR(50) | NOT NULL | Type of entity (article, seo_metadata, publish_task, etc.) |
| entity_id | INTEGER | NOT NULL | ID of the affected entity |
| action | VARCHAR(50) | NOT NULL | Action performed (create, update, delete, publish, etc.) |
| user_id | INTEGER | NULLABLE | User who performed action (null for system actions) |
| changes | JSONB | DEFAULT '{}' | Before/after values for updates |
| metadata | JSONB | DEFAULT '{}' | Additional context (IP address, user agent, etc.) |
| timestamp | TIMESTAMP | NOT NULL, DEFAULT NOW() | When action occurred |

**Indexes**:
```sql
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
```

**Partitioning**:
```sql
-- Partition by month for efficient archival
CREATE TABLE audit_logs_2025_10 PARTITION OF audit_logs
FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
```

---

## Database Triggers

### Auto-Update Timestamps

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_workflow_states_updated_at
BEFORE UPDATE ON workflow_states
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_seo_metadata_updated_at
BEFORE UPDATE ON seo_metadata
FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### Audit Trail Trigger

```sql
CREATE OR REPLACE FUNCTION log_article_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (entity_type, entity_id, action, user_id, changes)
    VALUES (
        'article',
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        current_setting('app.current_user_id', true)::INTEGER,
        jsonb_build_object(
            'before', to_jsonb(OLD),
            'after', to_jsonb(NEW)
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_article_audit
AFTER INSERT OR UPDATE OR DELETE ON articles
FOR EACH ROW EXECUTE FUNCTION log_article_changes();
```

### SEO Optimization Status Trigger

```sql
CREATE OR REPLACE FUNCTION update_seo_optimized_status()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE articles
    SET seo_optimized = TRUE
    WHERE id = NEW.article_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_seo_metadata_created
AFTER INSERT ON seo_metadata
FOR EACH ROW EXECUTE FUNCTION update_seo_optimized_status();
```

### Tag Usage Counter

```sql
CREATE OR REPLACE FUNCTION update_tag_usage_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE tags SET usage_count = usage_count + 1 WHERE id = NEW.tag_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE tags SET usage_count = usage_count - 1 WHERE id = OLD.tag_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_article_tags_usage
AFTER INSERT OR DELETE ON article_tags
FOR EACH ROW EXECUTE FUNCTION update_tag_usage_count();
```

---

## Migration Strategy

### Phase 1: Core Tables (Completed)
1. ✅ Create `articles`, `topic_requests`, `tags`, `article_tags`
2. ✅ Insert seed data for common tags
3. ✅ Deploy basic CRUD operations

### Phase 2: Workflow & Scheduling (Completed)
1. ✅ Create `workflow_states`, `schedules`
2. ✅ Implement state machine logic
3. ✅ Deploy Celery Beat scheduler

### Phase 3: Semantic Similarity (Completed)
1. ✅ Enable pgvector extension
2. ✅ Create `topic_embeddings` table
3. ✅ Backfill embeddings for existing articles

### Phase 4: Compliance (Completed)
1. ✅ Create `audit_logs` table with partitioning
2. ✅ Deploy audit triggers
3. ✅ Configure log retention policies

### Phase 5: Fusion Architecture Extensions (NEW - In Progress)
1. ⏳ Extend `articles` table with `source` and `seo_optimized` columns
2. ⏳ Create `seo_metadata` table with FK to articles
3. ⏳ Create `publish_tasks` table with screenshot storage
4. ⏳ Create `execution_logs` table with partitioning
5. ⏳ Deploy new triggers for SEO status updates
6. ⏳ Backfill `source='ai_generated'` for existing articles

**Migration Script for Phase 5**:
```sql
-- Step 1: Extend articles table
ALTER TABLE articles
ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'ai_generated'
CHECK (source IN ('ai_generated', 'imported'));

ALTER TABLE articles
ADD COLUMN seo_optimized BOOLEAN NOT NULL DEFAULT FALSE;

-- Step 2: Create seo_metadata table
CREATE TABLE seo_metadata (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
    seo_title VARCHAR(60) NOT NULL CHECK (char_length(seo_title) BETWEEN 50 AND 60),
    meta_description VARCHAR(160) NOT NULL CHECK (char_length(meta_description) BETWEEN 150 AND 160),
    focus_keyword VARCHAR(100) NOT NULL,
    primary_keywords TEXT[] NOT NULL DEFAULT '{}' CHECK (array_length(primary_keywords, 1) BETWEEN 3 AND 5),
    secondary_keywords TEXT[] NOT NULL DEFAULT '{}' CHECK (array_length(secondary_keywords, 1) BETWEEN 5 AND 10),
    keyword_density JSONB NOT NULL DEFAULT '{}',
    optimization_recommendations TEXT[] NOT NULL DEFAULT '{}',
    manual_overrides JSONB DEFAULT '{}',
    readability_score DECIMAL(4,2),
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Step 3: Create publish_tasks table
CREATE TABLE publish_tasks (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    cms_type VARCHAR(50) NOT NULL DEFAULT 'wordpress',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')),
    screenshots JSONB DEFAULT '[]',
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count <= max_retries),
    max_retries INTEGER NOT NULL DEFAULT 3 CHECK (max_retries > 0),
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Step 4: Create execution_logs table with partitioning
CREATE TABLE execution_logs (
    id BIGSERIAL PRIMARY KEY,
    publish_task_id INTEGER NOT NULL REFERENCES publish_tasks(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL CHECK (action IN ('navigate', 'click', 'type', 'upload', 'screenshot', 'verify', 'wait', 'scroll')),
    target_element TEXT,
    payload JSONB DEFAULT '{}',
    result VARCHAR(20) NOT NULL CHECK (result IN ('success', 'failure', 'retry')),
    error_details TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (timestamp);

-- Step 5: Create indexes
CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_articles_seo_optimized ON articles(seo_optimized) WHERE seo_optimized = FALSE;
CREATE INDEX idx_seo_metadata_article ON seo_metadata(article_id);
CREATE INDEX idx_publish_tasks_article ON publish_tasks(article_id);
CREATE INDEX idx_publish_tasks_status ON publish_tasks(status);
CREATE INDEX idx_execution_logs_task ON execution_logs(publish_task_id);

-- Step 6: Deploy triggers
CREATE TRIGGER trigger_seo_metadata_updated_at
BEFORE UPDATE ON seo_metadata
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_seo_metadata_created
AFTER INSERT ON seo_metadata
FOR EACH ROW EXECUTE FUNCTION update_seo_optimized_status();
```

---

## Data Retention

Following 7-year retention policy:

| Time Period | Storage | Access Pattern | Tables |
|-------------|---------|----------------|--------|
| 0-12 months | Hot (RDS) | Full read/write, all indexes | All tables |
| 1-3 years | Warm (RDS archive tables) | Read-only, reduced indexes | articles, seo_metadata, publish_tasks |
| 3-7 years | Cold (S3 Glacier) | Export only, manual restore | Archived JSON exports |
| 7+ years | Deleted | Automated purge (unless legal hold) | N/A |

**Archive Job** (runs monthly):
```sql
-- Move old articles and related data to archive tables
INSERT INTO articles_archive
SELECT * FROM articles
WHERE created_at < NOW() - INTERVAL '1 year';

INSERT INTO seo_metadata_archive
SELECT sm.* FROM seo_metadata sm
JOIN articles a ON sm.article_id = a.id
WHERE a.created_at < NOW() - INTERVAL '1 year';

DELETE FROM articles
WHERE created_at < NOW() - INTERVAL '1 year';
```

**Screenshot Cleanup** (runs weekly):
```sql
-- Delete screenshots from publish_tasks older than 90 days
UPDATE publish_tasks
SET screenshots = '[]'
WHERE completed_at < NOW() - INTERVAL '90 days'
AND screenshots IS NOT NULL;
```

---

## Performance Considerations

### Expected Load (UPDATED)

- **Writes**:
  - AI generation: 50-100 articles/day
  - Imports: 200-500 articles/day
  - SEO analysis: 250-600 articles/day
  - Publishing: 100-200 tasks/day
  - Total: ~0.5-1 writes/second average
- **Reads**: 100 concurrent users × 15 queries/minute = ~25 reads/second
- **Storage**:
  - Articles: 600 articles/day × 10 KB avg = ~2.2 GB/year
  - Screenshots: 150 tasks/day × 8 screenshots × 200 KB = ~220 GB/year
  - Execution logs: 150 tasks/day × 50 actions × 500 bytes = ~1.4 GB/year

### Optimization Strategy

1. **Connection Pooling**: 15-25 connections for backend API, 10-15 for workers
2. **Query Optimization**: Use EXPLAIN ANALYZE for queries with response time > 100ms
3. **Materialized Views**:
   - Tag usage statistics
   - SEO metadata quality metrics
   - Publishing success rates by time period
4. **Vacuum Strategy**: Autovacuum enabled, manual VACUUM ANALYZE weekly
5. **Screenshot Storage**: S3-compatible object storage with lifecycle policies (delete after 90 days)

### Scaling Triggers

- Query latency p95 > 500ms → Add read replica
- Connection pool exhaustion → Increase pool size or add replica
- Disk usage > 80% → Archive old data or increase storage
- Screenshot storage > 500 GB → Review retention policy or upgrade storage tier

---

## Schema Validation

All entities mapped from feature specification:

| Spec Entity | Database Table(s) | Status |
|-------------|-------------------|--------|
| Article (Extended) | `articles` | ✅ Extended with `source`, `seo_optimized` |
| TopicRequest | `topic_requests` | ✅ Preserved |
| **SEOMetadata (New)** | `seo_metadata` | ⏳ **Phase 5 - To be created** |
| **PublishTask (New)** | `publish_tasks` | ⏳ **Phase 5 - To be created** |
| **ExecutionLog (New)** | `execution_logs` | ⏳ **Phase 5 - To be created** |
| Tag | `tags`, `article_tags` | ✅ Preserved |
| Schedule | `schedules` | ✅ Preserved |
| WorkflowState | `workflow_states` | ✅ Preserved |
| TopicEmbedding | `topic_embeddings` | ✅ Preserved |
| AuditLog | `audit_logs` | ✅ Preserved |

**Status**: Ready for Phase 5 Implementation (Fusion Architecture Extensions)

---

## Appendix: Complete SQL Schema

See `/specs/001-cms-automation/scripts/schema_fusion.sql` for the complete SQL migration script including all table definitions, indexes, foreign keys, constraints, and triggers for the fusion architecture.
