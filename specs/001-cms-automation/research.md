# Research: AI-Powered CMS Automation

**Feature**: 001-cms-automation
**Date**: 2025-10-25
**Purpose**: Resolve technical clarifications from Technical Context before design phase

## Executive Summary

This research document consolidates decisions for the CMS automation platform's technology stack, integration patterns, and architectural choices. All decisions prioritize Claude Computer Use API integration, semantic content analysis, reliable scheduling, and seamless CMS platform compatibility.

---

## 1. Language and Runtime Selection

### Decision: Python 3.11+

### Rationale:
- **Anthropic SDK Support**: Official `anthropic` Python SDK provides first-class support for Claude API including Computer Use features
- **AI/ML Ecosystem**: Rich ecosystem for NLP, embeddings, and content analysis (transformers, sentence-transformers, spaCy)
- **Async Support**: Native async/await for handling concurrent article generation requests
- **CMS Integration**: Strong library support for major CMS platforms (WordPress REST API, Strapi SDK, Contentful Python client)
- **Task Processing**: Mature task queue systems (Celery) with robust scheduling capabilities

### Alternatives Considered:
- **Node.js/TypeScript**: Excellent async performance and growing AI ecosystem, but fewer mature NLP libraries and less robust Anthropic SDK at time of research
- **Go**: Superior performance for concurrent processing, but limited AI/ML library ecosystem and no official Anthropic SDK
- **Rust**: Best performance and safety, but steep learning curve and immature AI integration libraries

### Implementation Notes:
- Use Python 3.11+ for pattern matching and performance improvements
- Leverage type hints (PEP 484) for better IDE support and early error detection
- Use Poetry or uv for dependency management

---

## 2. CMS Platform Integration Strategy

### Decision: Platform-Agnostic Adapter Pattern with WordPress as Primary Target

### Rationale:
- **Market Reality**: WordPress powers 43% of all websites (W3Techs, 2024)
- **Extensibility**: Adapter pattern allows support for multiple CMS platforms without core logic changes
- **REST API Maturity**: WordPress REST API is production-ready and well-documented
- **Plugin Ecosystem**: Can be deployed as WordPress plugin or standalone service

### Architecture:
```python
# Abstract interface
class CMSAdapter(ABC):
    async def create_article(self, article: Article) -> str
    async def update_article(self, article_id: str, data: dict) -> bool
    async def publish_article(self, article_id: str) -> bool
    async def get_taxonomy(self) -> Taxonomy
    async def add_tags(self, article_id: str, tags: List[str]) -> bool

# Concrete implementations
class WordPressAdapter(CMSAdapter): ...
class StrapiAdapter(CMSAdapter): ...
class ContentfulAdapter(CMSAdapter): ...
```

### Alternatives Considered:
- **Headless CMS First** (Strapi/Contentful): Modern API-first design but smaller market share
- **Custom CMS Only**: Maximum flexibility but limits adoption to single platform
- **Ghost Platform**: Growing but niche market (under 2% market share)

### Implementation Notes:
- Start with WordPress REST API v2
- Use WordPress Application Passwords for authentication
- Support for custom post types and taxonomies
- Future adapters: Strapi, Ghost, Contentful (based on user demand)

---

## 3. Task Queue and Scheduling System

### Decision: Celery with Redis Backend

### Rationale:
- **Python Native**: Seamless integration with Python backend
- **Proven Scale**: Handles 100,000+ tasks/day in production environments
- **Scheduling**: Built-in periodic task support via Celery Beat
- **Reliability**: Retry logic, task expiration, and failure handling
- **Monitoring**: Integration with Flower for real-time task monitoring

### Architecture:
```
Article Generation Request → Celery Task → Redis Queue → Worker Pool
                                          ↓
                                    Claude API Call
                                          ↓
                                    CMS Publication
```

### Alternatives Considered:
- **AWS SQS + Lambda**: Serverless, highly scalable, but vendor lock-in and cold start latency
- **BullMQ (Node.js)**: Excellent for Node ecosystem but requires language switch
- **RabbitMQ + Celery**: More complex setup, overkill for current scale (100-500 articles/day)

### Implementation Notes:
- Use Celery 5.3+ with Redis 7+ as broker and result backend
- Configure task time limits (5 minutes for generation, 30 seconds for other tasks)
- Implement exponential backoff for API failures
- Use priority queues for urgent article generation requests

---

## 4. Semantic Similarity Engine

### Decision: Anthropic Claude Embeddings with pgvector Storage

### Rationale:
- **API Consolidation**: Single vendor (Anthropic) for both generation and embeddings
- **Cost Efficiency**: Leverages existing Claude API relationship, potentially better pricing
- **Quality**: Anthropic embeddings optimized for semantic understanding of long-form content
- **Simplicity**: No additional embedding service deployment required

### Technical Approach:
1. Generate embeddings for article topics using Claude API
2. Store embeddings in PostgreSQL with pgvector extension
3. Use cosine similarity for duplicate detection
4. Set threshold at 0.85 similarity score (configurable)

### Alternatives Considered:
- **Sentence-Transformers (self-hosted)**: No API costs but requires GPU infrastructure and maintenance
- **OpenAI Embeddings**: Mature and well-documented but introduces second vendor dependency
- **Pinecone/Weaviate**: Specialized vector databases with excellent performance but adds infrastructure complexity

### Implementation Notes:
```sql
-- Enable pgvector extension
CREATE EXTENSION vector;

-- Store topic embeddings
CREATE TABLE topic_embeddings (
    id SERIAL PRIMARY KEY,
    article_id INT REFERENCES articles(id),
    topic_text TEXT,
    embedding vector(1536),  -- Anthropic embedding dimension
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for similarity search
CREATE INDEX ON topic_embeddings USING ivfflat (embedding vector_cosine_ops);
```

---

## 5. Primary Database Selection

### Decision: PostgreSQL 15+

### Rationale:
- **Vector Support**: pgvector extension for semantic similarity (no separate vector DB needed)
- **JSON Support**: Native JSONB for storing article metadata and flexible schema evolution
- **Reliability**: ACID compliance for audit trails and workflow state management
- **Performance**: Excellent performance for 100-500 articles/day scale
- **Ecosystem**: Strong Python support via asyncpg and SQLAlchemy

### Schema Design Principles:
- Separate tables for core entities (Articles, TopicRequests, Tags, Schedules, WorkflowStates)
- JSONB columns for CMS-specific metadata to support multiple platforms
- Audit table with triggers for all state changes
- Indexes on status fields and scheduled publication times

### Alternatives Considered:
- **MongoDB**: Flexible schema but lacks ACID guarantees needed for workflow state
- **MySQL**: Widely used but weaker JSON support and no native vector capabilities
- **Dedicated Vector DB (Qdrant/Pinecone)**: Better vector search but adds complexity for current scale

### Implementation Notes:
- Use asyncpg for async database operations
- Implement connection pooling (10-20 connections for 50 concurrent requests)
- Enable PostgreSQL statement logging for debugging
- Set up read replicas if query load exceeds write load

---

## 6. Testing Strategy and Frameworks

### Decision: pytest with pytest-asyncio for Backend, Playwright for Frontend

### Rationale:
- **Async Support**: pytest-asyncio handles async service testing naturally
- **Mocking**: pytest-mock and responses library for API mocking
- **Coverage**: pytest-cov for code coverage tracking (target: 80%+)
- **E2E Testing**: Playwright for cross-browser frontend automation tests

### Test Structure:
```
tests/
├── unit/                          # Fast, isolated tests (pytest)
│   ├── test_article_generator.py  # Mock Claude API calls
│   ├── test_content_analyzer.py   # Tag extraction logic
│   └── test_similarity.py         # Duplicate detection
│
├── integration/                    # Service integration tests
│   ├── test_cms_workflow.py       # End-to-end article creation
│   ├── test_scheduling.py         # Celery task execution
│   └── test_database.py           # PostgreSQL operations
│
├── contract/                       # API contract tests
│   ├── test_wordpress_api.py      # WordPress REST API contract
│   └── test_claude_api.py         # Claude API response schemas
│
└── e2e/                            # Frontend E2E tests (Playwright)
    ├── test_article_submission.py
    └── test_approval_workflow.py
```

### Implementation Notes:
- Run unit tests in CI/CD on every commit (< 30 seconds)
- Run integration tests on pre-merge (< 5 minutes)
- Run E2E tests nightly or pre-release
- Use VCR.py to record/replay HTTP interactions for deterministic tests

---

## 7. Deployment Target and Infrastructure

### Decision: AWS ECS (Fargate) with RDS PostgreSQL and ElastiCache Redis

### Rationale:
- **Managed Services**: RDS and ElastiCache reduce operational overhead
- **Scalability**: ECS Fargate auto-scales based on queue depth and CPU usage
- **Cost-Effective**: Pay-per-use pricing suitable for 100-500 articles/day
- **Monitoring**: Native CloudWatch integration for logs and metrics
- **Security**: VPC isolation, IAM roles, and Secrets Manager for credentials

### Architecture:
```
Internet → ALB → ECS Service (Backend API)
                      ↓
              ECS Service (Celery Workers)
                      ↓
         Redis (ElastiCache) ← Celery Beat (Scheduler)
                      ↓
        PostgreSQL (RDS) + pgvector
```

### Scaling Configuration:
- **API Service**: 2-10 tasks (CPU-based scaling)
- **Worker Service**: 5-20 tasks (queue depth scaling)
- **RDS**: db.t3.medium (2 vCPU, 4 GB) with read replica
- **ElastiCache**: cache.t3.small (1.5 GB memory)

### Alternatives Considered:
- **GCP Cloud Run + Cloud SQL**: Simpler serverless but less Celery ecosystem maturity
- **Azure Container Apps**: Competitive but team has less experience
- **On-Premise Docker Swarm**: Full control but requires infrastructure team
- **Kubernetes (EKS)**: Over-engineered for current scale; adds complexity

### Implementation Notes:
- Use Terraform for infrastructure as code
- Store secrets in AWS Secrets Manager (API keys, database passwords)
- Enable CloudWatch Logs for all containers
- Set up CloudWatch alarms for queue depth, error rates, API latency

---

## 8. Data Retention and Compliance

### Decision: 7-Year Retention with Tiered Storage

### Rationale:
- **Compliance**: Aligns with common industry standards (SOX, GDPR art. 17)
- **Audit Trail**: Sufficient for regulatory audits and dispute resolution
- **Cost Optimization**: Move older data to cheaper storage after 1 year

### Retention Policy:
- **Hot Storage** (0-12 months): PostgreSQL RDS, full access
- **Warm Storage** (1-3 years): RDS, archived tables with reduced indexes
- **Cold Storage** (3-7 years): S3 Glacier, exported JSON + metadata
- **Deletion**: Automated purge after 7 years unless legal hold applies

### Implementation:
```python
# Automated archival job (runs monthly)
async def archive_old_articles():
    # Move articles older than 12 months to archive table
    cutoff_date = datetime.now() - timedelta(days=365)
    old_articles = await db.query(
        "SELECT * FROM articles WHERE created_at < $1", cutoff_date
    )

    # Export to S3 for articles older than 3 years
    glacier_cutoff = datetime.now() - timedelta(days=365 * 3)
    archive_to_s3(old_articles, glacier_cutoff)
```

### Alternatives Considered:
- **Indefinite Retention**: Unnecessary cost burden for historical data
- **3-Year Retention**: Too short for some compliance requirements
- **10-Year Retention**: Excessive for non-financial content

---

## 9. Frontend Framework Selection

### Decision: React 18+ with TypeScript and Tailwind CSS

### Rationale:
- **CMS Integration**: Can be embedded in WordPress admin or served standalone
- **Type Safety**: TypeScript prevents runtime errors in complex approval workflows
- **Component Reusability**: React hooks simplify state management for multi-step forms
- **Styling**: Tailwind CSS enables rapid UI development matching CMS themes

### Key Libraries:
- **React Query**: Server state management and caching for API calls
- **React Hook Form**: Form validation for article submission and editing
- **React Router**: Client-side routing if deployed as standalone app
- **date-fns**: Date handling for scheduling interface

### Alternatives Considered:
- **Vue.js**: Simpler learning curve but smaller ecosystem for TypeScript
- **Svelte**: Excellent performance but less mature ecosystem
- **Vanilla JS**: Faster initial load but harder to maintain complex state

---

## 10. Monitoring and Observability

### Decision: Structured Logging (JSON) + Sentry for Errors + Prometheus Metrics

### Rationale:
- **Structured Logs**: JSON format enables log aggregation and searching (CloudWatch Insights)
- **Error Tracking**: Sentry provides context-rich error reports and alerting
- **Metrics**: Prometheus metrics exported for Grafana dashboards (queue depth, generation time, API latency)

### Logging Strategy:
```python
import structlog

logger = structlog.get_logger()

# Log article generation events
logger.info(
    "article_generation_started",
    topic_request_id=request.id,
    user_id=user.id,
    word_count_target=request.word_count
)

# Log errors with full context
logger.error(
    "article_generation_failed",
    topic_request_id=request.id,
    error=str(e),
    retry_count=retry_count,
    exc_info=True
)
```

### Key Metrics:
- Article generation time (p50, p95, p99)
- Tagging accuracy (compared to manual baseline)
- Scheduling precision (deviation from target time)
- API error rates (Claude API, CMS API)
- Queue depth and worker utilization

---

## Research Validation

All "NEEDS CLARIFICATION" items from Technical Context have been resolved:

| Item | Resolution |
|------|------------|
| Language/Version | Python 3.11+ |
| CMS Platform | WordPress (adapter pattern for future platforms) |
| Task Queue | Celery with Redis backend |
| Semantic Similarity | Anthropic Claude embeddings + pgvector |
| Primary Database | PostgreSQL 15+ |
| Vector Storage | pgvector extension (no separate DB) |
| Testing Framework | pytest + pytest-asyncio |
| Deployment Target | AWS ECS Fargate + RDS + ElastiCache |
| Data Retention | 7-year tiered retention policy |

**Phase 0 Complete** - Ready to proceed to Phase 1: Design & Contracts
