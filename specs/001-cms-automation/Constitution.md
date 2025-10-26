# Project Constitution: CMS Automation Platform

**Feature**: 001-cms-automation
**Version**: 1.0.0 (Fusion Architecture)
**Status**: Active
**Last Updated**: 2025-10-25

---

## Purpose

This Constitution defines the **immutable principles and standards** that govern all development, testing, deployment, and operational decisions for the CMS Automation Platform. These principles ensure:

- **Quality**: Code meets professional standards for maintainability and reliability
- **Security**: User data and credentials are protected at all times
- **Performance**: System meets or exceeds SLAs under expected load
- **Compatibility**: Changes preserve backward compatibility whenever possible
- **Auditability**: All operations are logged and traceable

**All team members MUST adhere to these principles.** Deviations require formal justification and approval.

---

## I. General Principles

### I.1. API-First Design

**Principle**: All features are designed as APIs before implementation begins.

**Requirements**:
- OpenAPI 3.0 specification written BEFORE coding starts
- API contracts reviewed by at least 2 team members
- Contract tests validate implementation matches specification
- Breaking changes require major version bump (semantic versioning)

**Rationale**: API-first design ensures clear interfaces, enables parallel frontend/backend development, and prevents scope creep.

**Example**:
```yaml
# specs/001-cms-automation/contracts/api-spec.yaml MUST be updated BEFORE implementation
paths:
  /v1/articles/import:  # New endpoint requires OpenAPI spec update first
    post:
      summary: Import external articles
      # Full specification here...
```

---

### I.2. Documentation as Code

**Principle**: Documentation is maintained alongside code and treated as a first-class deliverable.

**Requirements**:
- README.md updated for user-facing changes
- Inline code documentation (docstrings, JSDoc) for all public APIs
- Architecture Decision Records (ADRs) for significant technical choices
- Changelog maintained (CHANGELOG.md) following Keep a Changelog format

**Rationale**: Documentation prevents knowledge silos and reduces onboarding time.

---

### I.3. Semantic Versioning

**Principle**: All releases follow Semantic Versioning 2.0.0 (MAJOR.MINOR.PATCH).

**Requirements**:
- MAJOR: Breaking changes to API or data models
- MINOR: New features (backward-compatible)
- PATCH: Bug fixes and performance improvements
- Pre-release tags for alpha/beta: `2.0.0-beta.1`

**Example**:
- v1.0.0 → v1.1.0: Added article import (NEW feature, backward-compatible)
- v1.1.0 → v2.0.0: Added `source` field to Article model (BREAKING change, requires migration)

---

### I.4. Principle of Least Surprise

**Principle**: System behavior should match user expectations; avoid unexpected side effects.

**Requirements**:
- GET requests MUST be idempotent and side-effect free
- Destructive operations (DELETE) require confirmation or soft-delete
- Async operations return 202 Accepted with status polling endpoint
- Error messages are clear and actionable

**Example**:
```python
# ✅ GOOD: Soft delete, preserves data
async def delete_article(id: int):
    await db.update("UPDATE articles SET status = 'deleted' WHERE id = $1", id)

# ❌ BAD: Hard delete, data loss
async def delete_article(id: int):
    await db.execute("DELETE FROM articles WHERE id = $1", id)
```

---

## II. Code Quality & Testing

### II.1. Test-Driven Development (TDD) Mandatory

**Principle**: All new features and bug fixes MUST follow TDD workflow.

**Requirements**:
1. Write failing test first (RED)
2. Implement minimum code to pass test (GREEN)
3. Refactor while keeping tests green (REFACTOR)
4. Commit only when tests pass

**Coverage Targets**:
- Unit tests: ≥ 80% code coverage
- Integration tests: All critical workflows
- E2E tests: Complete user journeys (AI generation, import, SEO, publishing)

**Exemptions**:
- Configuration files (.env, docker-compose.yml)
- Database migrations (tested via integration tests)
- Prototypes (marked with `# PROTOTYPE:` comment)

**Verification**:
```bash
# CI/CD pipeline MUST run these checks
pytest --cov=src --cov-fail-under=80
pytest tests/integration/
pytest tests/e2e/
```

---

### II.2. Code Review Mandatory

**Principle**: No code is merged to main branch without peer review.

**Requirements**:
- Minimum 1 approval from another team member
- Automated checks must pass (linting, tests, security)
- No force-push to main or protected branches
- Review focuses on: correctness, clarity, test coverage, security

**Review Checklist**:
- [ ] Tests cover new functionality
- [ ] No hardcoded credentials or secrets
- [ ] Error handling is comprehensive
- [ ] Documentation updated (if user-facing change)
- [ ] Performance considerations addressed

---

### II.3. Static Analysis Mandatory

**Principle**: All code passes linting, type checking, and security scans before merge.

**Requirements** (Python):
- **Linting**: `ruff check src/` (no errors)
- **Type Checking**: `mypy src/` (strict mode)
- **Code Formatting**: `black src/` + `isort src/`
- **Security**: `bandit -r src/` + `safety check`

**Requirements** (TypeScript):
- **Linting**: `eslint src/`
- **Type Checking**: `tsc --noEmit`
- **Code Formatting**: `prettier --check src/`

**CI/CD Integration**:
```yaml
# .github/workflows/ci.yml
- name: Lint
  run: ruff check src/
- name: Type check
  run: mypy src/ --strict
- name: Security scan
  run: |
    bandit -r src/
    safety check
```

---

## III. Security & Privacy

### III.1. Credential Management

**Principle**: No credentials, API keys, or secrets in source code or version control.

**Requirements**:
- All secrets stored in environment variables or secrets manager (AWS Secrets Manager, HashiCorp Vault)
- `.env.example` provides template WITHOUT actual values
- `.gitignore` includes `.env`, `*.key`, `credentials.json`
- API keys masked in logs (show only first 8 characters)

**Example**:
```python
# ✅ GOOD: Load from environment
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# ❌ BAD: Hardcoded credential
ANTHROPIC_API_KEY = "sk-ant-api03-1234567890abcdef..."  # NEVER DO THIS
```

**Logging**:
```python
# Mask API keys in logs
logger.info(f"Using Anthropic API key: {api_key[:8]}...{api_key[-4:]}")
# Example output: "Using Anthropic API key: sk-ant-a...xyz"
```

---

### III.2. Input Validation and Sanitization

**Principle**: Never trust user input; validate and sanitize all external data.

**Requirements**:
- API endpoints validate request bodies using Pydantic models
- Imported HTML is sanitized (bleach library for XSS prevention)
- File uploads validated (MIME type, file size, extension)
- SQL queries use parameterized statements (prevent SQL injection)

**Example**:
```python
from pydantic import BaseModel, Field, validator

class ArticleImport(BaseModel):
    title: str = Field(..., min_length=10, max_length=500)
    body: str = Field(..., min_length=100)
    tags: List[str] = Field(default=[], max_items=20)

    @validator('body')
    def sanitize_html(cls, v):
        return bleach.clean(v, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
```

---

### III.3. Authentication and Authorization

**Principle**: All API endpoints require authentication; sensitive operations require authorization.

**Requirements**:
- JWT tokens for user authentication
- API keys for service-to-service authentication
- Role-based access control (RBAC) for administrative operations
- Token expiration: 1 hour (access tokens), 7 days (refresh tokens)

**Endpoint Protection**:
```python
from fastapi import Depends, HTTPException
from src.middleware.auth import verify_token

@app.post("/v1/articles/import")
async def import_articles(
    request: ImportRequest,
    user: User = Depends(verify_token)  # Authentication required
):
    if not user.has_permission("article:import"):  # Authorization check
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    # Implementation...
```

---

### III.4. Data Privacy and Retention

**Principle**: User data is collected only when necessary and retained per policy.

**Requirements**:
- Collect minimum data required for functionality
- Retention policy: 7 years (tiered storage)
- Support for data export (GDPR Article 20)
- Support for data deletion (GDPR Article 17, "Right to be Forgotten")
- Personal data encrypted at rest (database encryption)

**Audit Logging**:
```python
# Log all data access for audit trail
await audit_log.record(
    action="article_accessed",
    user_id=user.id,
    resource_id=article_id,
    ip_address=request.client.host,
    timestamp=datetime.now(UTC)
)
```

---

### III.5. CMS Credential Management (NEW - Phase 5)

**Principle**: WordPress admin credentials for Computer Use are handled with extreme care.

**Requirements**:
- **Storage**: WordPress admin passwords stored in AWS Secrets Manager (never in .env or database)
- **Rotation**: Passwords rotated every 90 days
- **Sanitization**: Credentials MUST be sanitized from execution logs and screenshots
- **Scope**: Computer Use credentials limited to publishing scope (no admin access)

**Credential Sanitization**:
```python
def sanitize_credentials(payload: dict) -> dict:
    """Remove sensitive fields from execution logs."""
    sensitive_fields = ['password', 'secret', 'token', 'api_key', 'access_key']

    sanitized = payload.copy()
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = '***REDACTED***'

    return sanitized

# Usage in execution logging:
await execution_log.create(
    publish_task_id=task_id,
    action='login',
    payload=sanitize_credentials(login_payload)  # ALWAYS sanitize
)
```

**Screenshot Protection**:
- Password fields MUST NOT be visible in screenshots
- If password field captured accidentally, screenshot deleted immediately
- Login screenshot taken AFTER password field is cleared

**Verification**:
```bash
# CI/CD check: No credentials in logs
grep -r "password\|secret\|api_key" backend/logs/*.log
# Expected: 0 matches (all sanitized)

# Database check: No credentials in execution_logs
psql cms_automation -c "SELECT * FROM execution_logs WHERE payload::text ~ '(password|secret|token)';"
# Expected: 0 rows
```

---

## IV. Testing Strategy

### IV.1. Unit Testing

**Principle**: All business logic has isolated unit tests with mocked dependencies.

**Requirements**:
- Test one function/method per test case
- Mock external dependencies (API calls, database, file system)
- Test success cases AND error cases
- Use fixtures for common test data

**Example**:
```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_claude_api():
    with patch('src.services.article_generator.claude_client') as mock:
        mock.messages.create.return_value = Mock(
            content=[Mock(text='Generated article body...')]
        )
        yield mock

def test_generate_article_success(mock_claude_api):
    """Test successful article generation."""
    generator = ArticleGenerator()
    result = generator.generate(topic="Test topic")

    assert result.title is not None
    assert len(result.body) > 100
    mock_claude_api.messages.create.assert_called_once()

def test_generate_article_api_failure(mock_claude_api):
    """Test article generation handles API errors gracefully."""
    mock_claude_api.messages.create.side_effect = AnthropicError("API unavailable")

    generator = ArticleGenerator()
    with pytest.raises(ArticleGenerationError):
        generator.generate(topic="Test topic")
```

---

### IV.2. Integration Testing

**Principle**: Critical workflows are tested with real dependencies in isolated environment.

**Requirements**:
- Use Docker containers for database, Redis (docker-compose.test.yml)
- Test actual API calls with rate limiting and retry logic
- Clean up test data after each test (fixtures with cleanup)
- Separate test database from development database

**Example**:
```python
@pytest.mark.integration
async def test_article_generation_workflow():
    """Test complete article generation workflow with real database and queue."""
    # Setup
    async with TestDatabase() as db:
        # Submit topic request
        request_id = await submit_topic(topic="Test article")

        # Wait for Celery task to complete
        await wait_for_task_completion(request_id, timeout=60)

        # Verify article created in database
        article = await db.query("SELECT * FROM articles WHERE request_id = $1", request_id)
        assert article is not None
        assert article.status == 'draft'
```

---

### IV.3. Contract Testing

**Principle**: API implementations match OpenAPI specification exactly.

**Requirements**:
- Use `schemathesis` or `dredd` to validate API against OpenAPI spec
- Run contract tests in CI/CD pipeline
- Block merge if contract tests fail

**Example**:
```bash
# Validate all API endpoints against spec
schemathesis run http://localhost:8000/openapi.json --base-url http://localhost:8000

# Expected: All endpoints return responses matching OpenAPI spec
```

---

### IV.4. E2E Testing

**Principle**: Complete user workflows are tested from UI to database.

**Requirements**:
- Test real user journeys (submit topic → generate article → approve → publish)
- Use Playwright for frontend E2E tests
- Run E2E tests before each release (not on every commit)

**Example E2E Test**:
```typescript
test('AI Article Generation → SEO → Publishing workflow', async ({ page }) => {
  // Submit topic
  await page.goto('http://localhost:3000/topics/new');
  await page.fill('#topic-description', 'Test article topic');
  await page.click('button[type="submit"]');

  // Wait for generation
  await page.waitForSelector('.article-status:has-text("draft")', { timeout: 300000 });

  // Approve article
  await page.click('button:has-text("Approve")');

  // Verify published
  await page.waitForSelector('.article-status:has-text("published")');
});
```

---

### IV.5. Computer Use Testing Strategy (NEW - Phase 5)

**Principle**: Computer Use browser automation is tested in isolated, reproducible environments.

**Requirements**:
- **Test Environment**: Dedicated WordPress instance (docker container) for each test run
- **Headless Mode**: Tests run in headless browser (Xvfb for CI/CD)
- **Screenshot Validation**: Verify screenshots captured at each step
- **Retry Logic**: Test retry behavior (simulate failures, verify exponential backoff)
- **Credential Isolation**: Use test credentials (never production credentials)

**Test Workflow**:
```python
@pytest.mark.computer_use
async def test_computer_use_publishing_workflow():
    """Test Computer Use publishing with screenshot validation."""
    # Setup: Start test WordPress instance
    async with TestWordPressInstance() as wp:
        # Create test article with SEO metadata
        article = await create_test_article(seo_optimized=True)

        # Submit publishing task
        task_id = await publish_task.submit(article_id=article.id)

        # Wait for completion
        result = await wait_for_publish_task(task_id, timeout=300)

        # Assertions
        assert result.status == 'completed'
        assert result.published_url is not None
        assert len(result.screenshots) == 8  # All 8 steps captured

        # Verify screenshots exist
        for step in ['login_success', 'editor_loaded', 'content_filled', 'seo_fields_filled', 'publish_clicked']:
            screenshot = await get_screenshot(task_id, step)
            assert screenshot is not None
            assert len(screenshot) > 1000  # At least 1KB (valid PNG)

        # Verify article published on WordPress
        wp_article = await wp.get_post(result.post_id)
        assert wp_article.title == article.title
        assert wp_article.status == 'publish'
```

**Flaky Test Mitigation**:
- **Timeouts**: Generous timeouts (5 min per task) for Computer Use operations
- **Retries**: Auto-retry failed tests 3x before marking as failure
- **Idempotency**: Tests clean up after themselves (delete test articles)
- **Isolation**: Each test uses unique test data (no shared state)

**Mock Strategy**:
```python
# For unit tests, mock Computer Use API
@patch('src.services.computer_use_publisher.computer_use_client')
def test_computer_use_login_logic(mock_client):
    """Test login logic without actual browser."""
    mock_client.click.return_value = True
    mock_client.type.return_value = True

    publisher = ComputerUsePublisher()
    result = publisher.login(username='test', password='test')

    assert result == True
    mock_client.click.assert_called_with(selector='#wp-submit')
```

---

## V. Performance & Scalability

### V.1. SLA Compliance Mandatory

**Principle**: All operations meet defined Service Level Agreements (SLAs).

**SLAs**:
- AI Article Generation: < 5 minutes (95th percentile)
- SEO Analysis: < 30 seconds (1500-word article)
- Article Import: < 5 minutes (100 articles)
- Computer Use Publishing: < 5 minutes (95th percentile)
- API Response Time: < 500ms (non-generation endpoints)

**Monitoring**:
```python
# Measure and log operation duration
import time

@log_duration
async def generate_article(topic: str) -> Article:
    start = time.time()
    try:
        article = await _generate_article(topic)
        duration = time.time() - start

        # Alert if SLA violated
        if duration > 300:  # 5 minutes
            await alert_sla_violation(operation='article_generation', duration=duration)

        return article
    except Exception as e:
        duration = time.time() - start
        logger.error(f"Article generation failed after {duration}s", exc_info=e)
        raise
```

---

### V.2. Database Query Optimization

**Principle**: All database queries are optimized for performance.

**Requirements**:
- Use indexes on frequently queried columns (status, created_at, author_id)
- Avoid N+1 queries (use eager loading)
- Use database connection pooling (20 connections)
- Monitor slow queries (log queries > 1 second)

**Example**:
```python
# ✅ GOOD: Eager load tags (1 query)
articles = await db.query("""
    SELECT a.*, json_agg(t.*) AS tags
    FROM articles a
    LEFT JOIN article_tags at ON a.id = at.article_id
    LEFT JOIN tags t ON at.tag_id = t.id
    WHERE a.status = 'published'
    GROUP BY a.id
""")

# ❌ BAD: N+1 query problem (1 + N queries)
articles = await db.query("SELECT * FROM articles WHERE status = 'published'")
for article in articles:
    article.tags = await db.query("SELECT * FROM tags WHERE article_id = $1", article.id)
```

---

### V.3. Concurrency Limits

**Principle**: System enforces limits to prevent resource exhaustion.

**Limits**:
- Max concurrent article generation: 50 requests
- Max concurrent SEO analysis: 100 requests
- Max concurrent Computer Use publishing: 10 tasks
- Max API requests per user: 100/minute (rate limiting)

**Implementation**:
```python
from asyncio import Semaphore

# Limit concurrent Computer Use tasks
computer_use_semaphore = Semaphore(10)

async def publish_with_computer_use(article_id: int):
    async with computer_use_semaphore:  # Blocks if 10 tasks already running
        return await _publish_article(article_id)
```

---

## VI. Deployment & Operations

### VI.1. Blue-Green Deployment

**Principle**: All production deployments use blue-green strategy for zero-downtime.

**Requirements**:
- Deploy new version to "green" environment
- Run smoke tests on green environment
- Switch traffic from blue to green (load balancer)
- Keep blue environment ready for rollback (24 hours)

**Rollback Trigger**:
- Error rate > 5% (compared to baseline)
- Response time > 2x baseline
- Critical functionality broken (health check fails)

---

### VI.2. Database Migrations

**Principle**: All schema changes are reversible and tested before production.

**Requirements**:
- Use Alembic for migrations (Python) or db-migrate (Node.js)
- Every migration has `upgrade()` and `downgrade()` functions
- Test migrations on staging environment first
- Run migrations during maintenance window (low-traffic period)

**Example**:
```python
# backend/migrations/versions/xxx_add_seo_metadata_table.py

def upgrade():
    op.create_table(
        'seo_metadata',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('article_id', sa.Integer, sa.ForeignKey('articles.id'), unique=True),
        # ... other columns
    )
    op.create_index('idx_seo_metadata_article_id', 'seo_metadata', ['article_id'])

def downgrade():
    op.drop_index('idx_seo_metadata_article_id')
    op.drop_table('seo_metadata')
```

---

### VI.3. Monitoring and Alerting

**Principle**: All critical metrics are monitored with automated alerting.

**Monitored Metrics**:
- API latency (p50, p95, p99)
- Error rate (4xx, 5xx responses)
- Queue depth (Celery tasks pending)
- Database connection pool usage
- Computer Use task success rate

**Alerting Thresholds**:
- Error rate > 5% → Page on-call engineer
- API latency p95 > 2 seconds → Slack alert
- Queue depth > 1000 tasks → Slack alert
- Database connections > 18/20 → Slack alert

**Tools**:
- Metrics: Prometheus + Grafana
- Logs: CloudWatch Logs (AWS) or ELK Stack
- Errors: Sentry
- Uptime: Pingdom or StatusCake

---

### VI.4. Incident Response

**Principle**: All production incidents follow defined response protocol.

**Severity Levels**:
- **SEV1** (Critical): System down, data loss, security breach → Page on-call, immediate response
- **SEV2** (High): Major feature broken, significant performance degradation → Slack alert, 1-hour SLA
- **SEV3** (Medium): Minor feature broken, minor performance issue → Slack alert, 24-hour SLA
- **SEV4** (Low): Cosmetic issue, no user impact → Create ticket, next sprint

**Incident Response Steps**:
1. **Acknowledge**: Confirm incident within 15 minutes
2. **Assess**: Determine severity and impact
3. **Mitigate**: Stop bleeding (rollback, disable feature, scale up)
4. **Communicate**: Update status page, notify stakeholders
5. **Resolve**: Fix root cause
6. **Postmortem**: Write incident report (within 5 days), identify preventative measures

---

## VII. Amendment Process

### VII.1. Proposing Changes

**Principle**: This Constitution can be amended through formal proposal process.

**Requirements**:
1. Create proposal document (ADR format)
2. Present to team for discussion
3. Require 75% team approval
4. Update Constitution with version bump
5. Communicate changes to all stakeholders

**Example Proposal**:
```markdown
# ADR-XXX: Amend Constitution IV.5 - Computer Use Testing Strategy

## Status
Proposed

## Context
Current testing strategy requires dedicated WordPress instance per test, which is slow (5 min setup per test).

## Proposed Amendment
Allow shared WordPress instance for Computer Use tests with test data isolation.

## Consequences
- Faster test execution (30s vs 5min setup)
- Risk: Flaky tests if shared instance has issues
- Mitigation: Reset instance daily, monitor flakiness

## Vote
- For: 4/5 team members
- Against: 1/5
- Result: APPROVED (80% > 75% threshold)
```

---

## VIII. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-25 | Initial Constitution for fusion architecture (includes Phase 5 principles) |

---

## Appendix: Quick Reference Checklist

Before merging code to main:

- [ ] All tests pass (unit, integration, E2E)
- [ ] Code coverage ≥ 80%
- [ ] Linting and type checking pass
- [ ] Security scans pass (no vulnerabilities)
- [ ] API specification updated (if API change)
- [ ] Documentation updated (if user-facing change)
- [ ] Peer review approved (≥ 1 approval)
- [ ] No credentials in code or logs
- [ ] SLA compliance verified (if performance-sensitive change)
- [ ] Database migration tested (if schema change)

Before deploying to production:

- [ ] Smoke tests pass on staging
- [ ] Blue-green deployment configured
- [ ] Rollback plan documented
- [ ] Monitoring and alerting configured
- [ ] Stakeholders notified of deployment window
- [ ] Database backups verified
- [ ] Incident response team on standby

---

**This Constitution is binding for all contributors to the CMS Automation Platform.**

**Violations of these principles may result in code rejection, rollback, or incident postmortem actions.**

**When in doubt, ask: "Does this decision align with our Constitution?"**
