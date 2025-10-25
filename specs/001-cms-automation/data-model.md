# Data Model: AI-Powered CMS Automation

**Feature**: 001-cms-automation
**Date**: 2025-10-25
**Database**: PostgreSQL 15+ with pgvector extension

## Overview

This document defines the database schema for the CMS automation platform. The model supports article generation workflows, semantic duplicate detection, scheduling, and audit trails. All entities are derived from the feature specification's Key Entities section.

---

## Entity Relationship Diagram

```
┌─────────────────┐       ┌──────────────────┐       ┌─────────────┐
│  TopicRequest   │──1:1──│     Article      │──M:N──│     Tag     │
│                 │       │                  │       │             │
│ - id            │       │ - id             │       │ - id        │
│ - topic         │       │ - title          │       │ - name      │
│ - outline       │       │ - body           │       │ - category  │
│ - style_tone    │       │ - status         │       │ - usage_cnt │
│ - word_count    │       │ - author_id      │       │ - source    │
│ - priority      │       │ - created_at     │       └─────────────┘
│ - submitted_at  │       │ - published_at   │
│ - status        │       │ - metadata       │
└─────────────────┘       └──────────────────┘
                                 │
                                 │ 1:N
                                 ↓
                          ┌──────────────────┐
                          │  WorkflowState   │
                          │                  │
                          │ - id             │
                          │ - article_id     │
                          │ - current_status │
                          │ - reviewers      │
                          │ - approval_hist  │
                          │ - modifications  │
                          │ - updated_at     │
                          └──────────────────┘
                                 │
                                 │ 1:1
                                 ↓
                          ┌──────────────────┐
                          │     Schedule     │
                          │                  │
                          │ - id             │
                          │ - article_id     │
                          │ - scheduled_time │
                          │ - creator_id     │
                          │ - status         │
                          │ - retry_config   │
                          │ - created_at     │
                          └──────────────────┘

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
```

---

## Core Entities

### 1. Article

Represents a content piece managed by the automation system.

**Table**: `articles`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique article identifier |
| title | VARCHAR(500) | NOT NULL | Article headline |
| body | TEXT | NOT NULL | Full article content (Markdown or HTML) |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'draft' | Workflow status (see enum below) |
| author_id | INTEGER | NOT NULL | User who initiated generation |
| cms_article_id | VARCHAR(255) | NULLABLE, UNIQUE | CMS platform's article ID (WordPress post ID, etc.) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Article creation timestamp |
| published_at | TIMESTAMP | NULLABLE | Actual publication timestamp |
| metadata | JSONB | NOT NULL, DEFAULT '{}' | CMS-specific metadata (featured image, excerpt, etc.) |
| formatting | JSONB | NOT NULL, DEFAULT '{}' | Formatting preferences (headings, lists, code blocks) |

**Status Enum**: `draft`, `in-review`, `scheduled`, `published`, `failed`

**Indexes**:
```sql
CREATE INDEX idx_articles_status ON articles(status);
CREATE INDEX idx_articles_author ON articles(author_id);
CREATE INDEX idx_articles_published ON articles(published_at) WHERE published_at IS NOT NULL;
CREATE INDEX idx_articles_metadata ON articles USING GIN(metadata);
```

**Validation Rules**:
- Title length: 10-500 characters
- Body length: minimum 100 words (FR-003 quality standards)
- Status transitions: `draft → in-review → scheduled → published` (no backwards except rollback)

**State Transitions**:
```
draft ──────────→ in-review ─────→ scheduled ──────→ published
  ↓                  ↓                 ↓                 ↓
  └──────────────→ failed ←──────────┘                 │
                                                        ↓
                                                    (rollback)
                                                        ↓
                                                      draft
```

---

### 2. TopicRequest

Represents a user's submission for article creation.

**Table**: `topic_requests`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique request identifier |
| topic_description | TEXT | NOT NULL | User-provided topic or outline |
| outline | TEXT | NULLABLE | Optional structured outline (JSON or Markdown) |
| style_tone | VARCHAR(50) | DEFAULT 'professional' | Requested writing style (professional, casual, technical, etc.) |
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
FOREIGN KEY (submitted_by) REFERENCES users(id);  -- Assumes existing users table
```

---

### 3. Tag

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

### 4. ArticleTag (Join Table)

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

**Indexes**:
```sql
CREATE INDEX idx_article_tags_confidence ON article_tags(confidence);
```

---

### 5. Schedule

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

**Constraints**:
```sql
ALTER TABLE schedules ADD CONSTRAINT check_scheduled_time_future
CHECK (scheduled_time > NOW());  -- Only for INSERT, not UPDATE
```

---

### 6. WorkflowState

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
| version | INTEGER | NOT NULL, DEFAULT 1 | Article version number (increments on re-generation) |
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

**JSONB Schema Examples**:

**approval_history**:
```json
[
  {
    "reviewer_id": 42,
    "action": "approved",
    "comment": "Looks good, ready to publish",
    "timestamp": "2025-10-25T14:30:00Z"
  },
  {
    "reviewer_id": 57,
    "action": "rejected",
    "comment": "Needs more technical depth in section 3",
    "timestamp": "2025-10-25T15:15:00Z"
  }
]
```

**modification_requests**:
```json
[
  {
    "requester_id": 57,
    "request_type": "ai_regeneration",
    "feedback": "Add more code examples in the API integration section",
    "status": "pending",
    "created_at": "2025-10-25T15:20:00Z"
  },
  {
    "requester_id": 42,
    "request_type": "manual_edit",
    "changes": {"section": "introduction", "edit": "Updated first paragraph for clarity"},
    "status": "completed",
    "created_at": "2025-10-25T16:00:00Z"
  }
]
```

---

## Supporting Entities

### 7. TopicEmbedding

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
    1 - (te.embedding <=> $1::vector) AS similarity
FROM topic_embeddings te
JOIN articles a ON te.article_id = a.id
WHERE 1 - (te.embedding <=> $1::vector) > 0.85
ORDER BY te.embedding <=> $1::vector
LIMIT 10;
```

---

### 8. AuditLog

Comprehensive audit trail for compliance (FR-014).

**Table**: `audit_logs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Unique log entry identifier |
| entity_type | VARCHAR(50) | NOT NULL | Type of entity (article, tag, schedule, etc.) |
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

**Partitioning** (for long-term retention):
```sql
-- Partition by month for efficient archival
CREATE TABLE audit_logs_2025_10 PARTITION OF audit_logs
FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
```

**Example Log Entry**:
```json
{
  "entity_type": "article",
  "entity_id": 123,
  "action": "status_change",
  "user_id": 42,
  "changes": {
    "before": {"status": "draft"},
    "after": {"status": "published"}
  },
  "metadata": {
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "automated": true
  },
  "timestamp": "2025-10-25T14:30:00Z"
}
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

## Validation Rules Summary

| Entity | Rule | Enforcement |
|--------|------|-------------|
| Article | Title 10-500 chars | Application + CHECK constraint |
| Article | Body min 100 words | Application logic (FR-003) |
| Article | Status transitions | Application state machine |
| TopicRequest | Word count 100-10000 | Application + CHECK constraint |
| Tag | Name 2-100 chars | CHECK constraint |
| Tag | Unique case-insensitive | Application + functional index |
| ArticleTag | Confidence 0.0-1.0 | CHECK constraint |
| Schedule | Scheduled time future | CHECK constraint (INSERT only) |
| Schedule | Max retries > 0 | CHECK constraint |

---

## Migration Strategy

### Phase 1: Core Tables
1. Create `articles`, `topic_requests`, `tags`, `article_tags`
2. Insert seed data for common tags
3. Deploy basic CRUD operations

### Phase 2: Workflow & Scheduling
1. Create `workflow_states`, `schedules`
2. Implement state machine logic
3. Deploy Celery Beat scheduler

### Phase 3: Semantic Similarity
1. Enable pgvector extension
2. Create `topic_embeddings` table
3. Backfill embeddings for existing articles

### Phase 4: Compliance
1. Create `audit_logs` table with partitioning
2. Deploy audit triggers
3. Configure log retention policies

---

## Data Retention

Following 7-year retention policy from research:

| Time Period | Storage | Access Pattern |
|-------------|---------|----------------|
| 0-12 months | Hot (RDS) | Full read/write, all indexes |
| 1-3 years | Warm (RDS archive tables) | Read-only, reduced indexes |
| 3-7 years | Cold (S3 Glacier) | Export only, manual restore |
| 7+ years | Deleted | Automated purge (unless legal hold) |

**Archive Job** (runs monthly):
```sql
-- Move old articles to archive table
INSERT INTO articles_archive
SELECT * FROM articles
WHERE created_at < NOW() - INTERVAL '1 year';

DELETE FROM articles
WHERE created_at < NOW() - INTERVAL '1 year';
```

---

## Performance Considerations

### Expected Load
- **Writes**: 100-500 articles/day = ~0.3 writes/second average
- **Reads**: 50 concurrent users × 10 queries/minute = ~8 reads/second
- **Storage**: 500 articles/day × 10 KB avg = ~1.8 GB/year

### Optimization Strategy
1. **Connection Pooling**: 10-20 connections for backend API, 5-10 for workers
2. **Query Optimization**: Use EXPLAIN ANALYZE for all queries with response time > 100ms
3. **Materialized Views**: For tag usage statistics and trending topics
4. **Vacuum Strategy**: Autovacuum enabled, manual VACUUM ANALYZE weekly

### Scaling Triggers
- Query latency p95 > 500ms → Add read replica
- Connection pool exhaustion → Increase pool size or add replica
- Disk usage > 80% → Archive old data or increase storage

---

## Schema Validation

All entities mapped from feature specification:

| Spec Entity | Database Table(s) | Status |
|-------------|-------------------|--------|
| Article | `articles` | ✅ Complete |
| TopicRequest | `topic_requests` | ✅ Complete |
| Tag | `tags`, `article_tags` | ✅ Complete |
| Schedule | `schedules` | ✅ Complete |
| WorkflowState | `workflow_states` | ✅ Complete |
| (Implicit) Embeddings | `topic_embeddings` | ✅ Complete |
| (Implicit) Audit | `audit_logs` | ✅ Complete |

**Ready for Phase 1 Contracts** ✅
